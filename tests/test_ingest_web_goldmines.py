import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import ingest_web_goldmines as module


class WebGoldmineIngestionTests(unittest.TestCase):
    def test_candidate_filter_keeps_language_and_folk_titles_but_skips_regional_history(self):
        self.assertTrue(module.is_garhwali_candidate("गढ़वाली कविता", "https://example.org/a"))
        self.assertTrue(module.is_garhwali_candidate("Folk Songs of Garhwal", "https://example.org/a"))
        self.assertFalse(module.is_garhwali_candidate("Quit India movement in Garhwal", "https://example.org/a"))
        self.assertFalse(module.is_garhwali_candidate("History of Garhwal", "https://example.org/a"))

    def test_extracts_blogger_article_text_and_skips_non_garhwali_entries(self):
        feed = {
            "feed": {
                "openSearch$totalResults": {"$t": "2"},
                "entry": [
                    {
                        "id": {"$t": "post-1"},
                        "title": {"$t": "A Garhwali folk story"},
                        "published": {"$t": "2020-01-01T00:00:00Z"},
                        "content": {"$t": "<p>गढ़वाली कथा का यह एक नमूना है जिसे स्थानीय भाषा सामग्री के रूप में जाँचना है।</p><script>tracking()</script>"},
                        "link": [{"rel": "alternate", "href": "https://blog.example/story"}],
                        "author": [{"name": {"$t": "Author"}}],
                    },
                    {
                        "id": {"$t": "post-2"},
                        "title": {"$t": "Unrelated regional news"},
                        "content": {"$t": "<p>Not a Garhwali item.</p>"},
                        "link": [{"rel": "alternate", "href": "https://blog.example/news"}],
                    },
                ],
            }
        }

        records = module.records_from_blogger_feed(
            feed, feed_url="https://blog.example/feed", feed_sha256="feed-hash"
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "A Garhwali folk story")
        self.assertTrue(records[0]["text_normalized"].startswith("गढ़वाली कथा"))
        self.assertNotIn("tracking", records[0]["text_normalized"])

    def test_rights_pending_records_stay_local_experimental_only(self):
        feed = {
            "feed": {
                "entry": [{
                    "id": {"$t": "post-1"},
                    "title": {"$t": "Garhwali story"},
                    "content": {"$t": "<p>गरhwali कथा सामग्री का यह पर्याप्त लंबा नमूना है जिसे स्थानीय प्रायोगिक corpus में रखा जाएगा।</p>"},
                    "link": [{"rel": "alternate", "href": "https://blog.example/story"}],
                }]
            }
        }

        row = module.records_from_blogger_feed(
            feed, feed_url="https://blog.example/feed", feed_sha256="feed-hash"
        )[0]

        self.assertFalse(row["training_eligible"])
        self.assertTrue(row["experimental_training_eligible"])
        self.assertEqual(row["rights_status"], "rights_unassessed")
        self.assertEqual(row["corpus_layer"], "experimental")
        self.assertNotIn("iso_639_3", row)
        self.assertIn("gbm", row["language_candidates"])

    def test_khabarsaar_parser_keeps_article_body_and_drops_site_navigation(self):
        url = "https://uttarakhandkhabarsaar.in/jani-mayedi-tani-jayedi-a-garhwali-short-story/"
        html = (
            "<html><head><title>Garhwali story</title></head><body><nav>Navigation noise</nav>"
            "<article><div class='entry-content'><p>यह गढ़वाली कथा का पर्याप्त लंबा पाठ है। "
            "इसे भाषा पहचान और स्रोत के लिए प्रायोगिक परत में रखा गया है।</p></div></article></body></html>"
        )

        row = module.record_from_khabarsaar_page(url, html.encode(), {
            "raw_path": "data/downloads/page.html", "sha256": "page-hash",
            "bytes": len(html), "retrieved_at": "2026-09-30T00:00:00Z",
        })

        self.assertIsNotNone(row)
        self.assertNotIn("Navigation noise", row["text_normalized"])
        self.assertIn("गढ़वाली कथा", row["text_normalized"])

    def test_exact_dedup_keeps_one_source_record_and_reports_overlap(self):
        rows = [
            {"record_id": "a", "text_normalized": "one  text"},
            {"record_id": "b", "text_normalized": "one text"},
            {"record_id": "c", "text_normalized": "new text"},
        ]

        unique, duplicate_hashes = module.deduplicate_records(rows, {module.text_hash("one text")})

        self.assertEqual([row["record_id"] for row in unique], ["c"])
        self.assertEqual(duplicate_hashes, [module.text_hash("one text")])

    def test_feed_completeness_check_rejects_missing_entries(self):
        payload = {"feed": {"entry": [{"id": {"$t": "one"}}]}}
        with self.assertRaisesRegex(RuntimeError, "incomplete or overlapping"):
            module.verify_feed_complete([payload], expected_total=2)

    def test_large_feed_response_is_bisected_and_reassembled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []

            def fetcher(url):
                from urllib.parse import parse_qs, urlparse
                query = parse_qs(urlparse(url).query)
                start = int(query["start-index"][0])
                size = int(query["max-results"][0])
                calls.append((start, size))
                returned = size if size <= 2 else size - 2
                return json.dumps({"feed": {"entry": [
                    {"id": {"$t": str(index)}}
                    for index in range(start, start + returned)
                ]}}).encode()

            with patch.object(module, "ROOT", root), patch.object(
                module, "RAW", root / "data/downloads/web_goldmines"
            ):
                pages = module._acquire_feed_span(
                    1, 4, blog_rules="User-agent: *\nAllow: /", changed=True,
                    fetcher=fetcher, sleeper=lambda _seconds: None,
                )

        self.assertEqual([(start, size) for start, size, _data, _info in pages], [(1, 2), (3, 2)])
        self.assertEqual(calls, [(1, 4), (1, 2), (3, 2)])

    def test_robots_rules_are_respected(self):
        rules = "User-agent: *\nDisallow: /private\nAllow: /"

        self.assertTrue(module.robots_allows(rules, "https://blog.example/entry"))
        self.assertFalse(module.robots_allows(rules, "https://blog.example/private/entry"))


if __name__ == "__main__":
    unittest.main()
