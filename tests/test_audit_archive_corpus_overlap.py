import json
import tempfile
import unittest
from pathlib import Path

from audit_archive_corpus_overlap import audit_overlap, read_archive_rows


class ArchiveCorpusOverlapTests(unittest.TestCase):
    def test_archive_reader_prefers_complete_source_linked_candidate_view(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "data/extracted/research/internet_archive_candidate_views_2026-10-04/text_review_candidates.jsonl"
            candidate.parent.mkdir(parents=True)
            candidate.write_text(json.dumps({
                "record_id": "ia:supplement:1",
                "source_id": "ia-supplement",
                "text": "supplemental OCR page",
            }) + "\n", encoding="utf-8")

            rows = read_archive_rows(root)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["record_id"], "ia:supplement:1")
        self.assertEqual(rows[0]["text"], "supplemental OCR page")

    def test_exact_normalized_matches_are_reported_without_text(self):
        archive = [{
            "record_id": "ia:page:1",
            "source_id": "ia-book",
            "text": "गढ़वाली भाषा और लोकगीत",
        }]
        corpus = [{"text_clean": "गढ़वाली भाषा और लोकगीत", "split": "train"}]

        report = audit_overlap(archive, corpus, min_chars=3, ngram_size=2)

        self.assertEqual(report["exact"]["normalized_match_rows"], 1)
        self.assertEqual(report["exact"]["archive_rows_with_match"], 1)
        self.assertNotIn("text", report["exact"]["matches"][0]["archive"])
        self.assertNotIn("text", report["exact"]["matches"][0]["corpus"])

    def test_exact_match_carries_source_rights_provenance_without_copying_text(self):
        archive = [{"record_id": "ia:page:1", "source_id": "ia-book", "text": "a sufficiently long source page"}]
        corpus = [{
            "text_clean": "a sufficiently long source page",
            "provenance": [{
                "record_id": "old-book:page-1",
                "source_id": "old-book",
                "rights_status": "public_domain_india_government_work_term_expired",
            }],
        }]

        report = audit_overlap(archive, corpus, min_chars=3, ngram_size=2)

        match = report["exact"]["matches"][0]["corpus"]
        self.assertEqual(match["source_record_ids"], ["old-book:page-1"])
        self.assertEqual(match["source_ids"], ["old-book"])
        self.assertEqual(match["rights_statuses"], ["public_domain_india_government_work_term_expired"])
        self.assertNotIn("text", match)

    def test_near_match_is_reported_as_unadjudicated_candidate(self):
        text = "garhwali language folk music archive reference page"
        archive = [{"record_id": "ia:page:2", "source_id": "ia-book", "text": text}]
        corpus = [{"text_clean": text + " corrected", "split": "train"}]

        report = audit_overlap(
            archive, corpus, ngram_size=3, min_chars=10, min_jaccard=0.5,
        )

        self.assertEqual(report["near_duplicate"]["threshold_pairs"], 1)
        self.assertEqual(
            report["near_duplicate"]["matches"][0]["review_state"],
            "candidate_only_unadjudicated",
        )

    def test_short_text_is_exact_checked_but_not_near_checked(self):
        archive = [{"record_id": "ia:page:3", "source_id": "ia-book", "text": "राम"}]
        corpus = [{"text_clean": "राम", "split": "train"}]

        report = audit_overlap(archive, corpus)

        self.assertEqual(report["exact"]["normalized_match_rows"], 1)
        self.assertEqual(report["near_duplicate"]["candidate_pairs_scored"], 0)
        self.assertEqual(report["near_duplicate"]["threshold_pairs"], 0)


if __name__ == "__main__":
    unittest.main()
