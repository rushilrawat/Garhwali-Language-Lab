import json
import unittest
from urllib.parse import parse_qs, urlparse

from scripts.export_licensed_sources import (
    build_attribution_overlays,
    build_benchmark_exports,
    build_exports,
)


class LicensedSourceExportTests(unittest.TestCase):
    def test_tatoeba_uses_recovered_page_author_and_preserves_orphan_status(self):
        raw = {
            "record_id": "tatoeba:42",
            "source_id": "tatoeba",
            "text_original": "गढ़वळी वाक्य",
            "text_normalized": "गढ़वळी वाक्य",
            "iso_639_3": "gbm",
            "license_id": "CC-BY-2.0-FR",
            "license_url": "https://creativecommons.org/licenses/by/2.0/fr/",
            "item_url": "https://tatoeba.org/en/sentences/show/42",
            "attribution": "contributor unavailable",
            "quality_flags": ["missing_contributor"],
            "quality_status": "unreviewed",
            "native_reviewed": False,
            "training_eligible": False,
        }
        evidence = {
            "records": [{
                "sentence_id": "42",
                "lang": "gbm",
                "license": "CC BY 2.0 FR",
                "owner": None,
                "is_unapproved": False,
                "item_url": raw["item_url"],
                "contributor_username": "sabretou",
                "contributor_profile_url": "https://tatoeba.org/en/user/profile/sabretou",
                "added_date_label": "October 27, 2015",
                "sentence_page_retrieved_at": "2026-10-05T18:24:42Z",
                "sentence_page_sha256": "a" * 64,
                "page_has_sentence_id": True,
                "attribution_status": "creator_attributed_from_sentence_page",
            }],
        }

        exports = build_exports([raw], [], [], [], evidence)
        record = exports["tatoeba_cc_by_2_0_fr"][0]

        self.assertEqual(record["attribution_name"], "sabretou")
        self.assertEqual(record["source_url"], raw["item_url"])
        self.assertIsNone(record["upstream_owner"])
        self.assertTrue(record["upstream_orphaned"])
        self.assertEqual(record["quality_status"], "unreviewed")
        self.assertFalse(record["training_eligible"])
        self.assertNotIn("missing_contributor", record["quality_flags"])

    def test_wiktionary_export_has_immutable_revision_and_history_urls(self):
        raw = {
            "record_id": "wiktionary_en:99:lemma",
            "source_id": "wiktionary_en",
            "text_original": "शब्द",
            "text_normalized": "शब्द",
            "iso_639_3": "gbm",
            "license_id": "CC-BY-SA-4.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "revision_id": 12345,
            "source_url": "https://en.wiktionary.org/w/index.php?oldid=12345",
            "attribution": "English Wiktionary contributors; https://en.wiktionary.org/w/index.php?title=%E0%A4%B6%E0%A4%AC%E0%A5%8D%E0%A4%A6&action=history",
            "quality_status": "unreviewed",
            "native_reviewed": False,
            "training_eligible": False,
        }

        exports = build_exports([], [], [raw], [], {"records": []})
        record = exports["wiktionary_cc_by_sa_4_0"][0]

        self.assertEqual(record["source_revision"], 12345)
        self.assertIn("oldid=12345", record["source_url"])
        self.assertIn("action=history", record["source_history_url"])
        self.assertIn("%E0%A4%B6", record["source_url"])

    def test_swadesh_export_builds_revision_links_from_recorded_revision(self):
        raw = {
            "record_id": "wiktionary_swadesh_thematic:1:1",
            "source_id": "wiktionary_swadesh_thematic",
            "text_original": "मि",
            "text_normalized": "मि",
            "iso_639_3": "gbm",
            "license_id": "CC-BY-SA-4.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "source_revision": 87247279,
            "attribution": "English Wiktionary contributors",
            "provenance": {"retrieved_at": "2026-09-09T14:48:48Z", "sha256": "b" * 64},
            "quality_status": "unreviewed",
            "native_reviewed": False,
            "training_eligible": False,
        }

        exports = build_exports([], [], [], [raw], {"records": []})
        record = exports["wiktionary_cc_by_sa_4_0"][0]

        self.assertEqual(record["source_revision"], 87247279)
        self.assertIn("oldid=87247279", record["source_url"])
        self.assertEqual(
            parse_qs(urlparse(record["source_history_url"]).query)["title"],
            ["Appendix:Garhwali Swadesh list"],
        )

    def test_attribution_overlay_is_content_free_and_keeps_record_lineage(self):
        exports = {
            "tatoeba_cc_by_2_0_fr": [{
                "record_id": "tatoeba:42",
                "source_id": "tatoeba",
                "text_normalized": "must not be copied",
                "attribution_name": "sabretou",
                "attribution": "Sentence #42 contributed by sabretou",
                "source_url": "https://tatoeba.org/en/sentences/show/42",
                "source_revision": None,
                "source_history_url": None,
                "license_id": "CC-BY-2.0-FR",
                "license_url": "https://creativecommons.org/licenses/by/2.0/fr/",
                "quality_flags": ["upstream_sentence_orphaned"],
                "attribution_evidence_sha256": "a" * 64,
            }],
            "wiktionary_cc_by_sa_4_0": [{
                "record_id": "wiktionary_en:99:lemma",
                "source_id": "wiktionary_en",
                "text_normalized": "also must not be copied",
                "attribution_name": "English Wiktionary contributors",
                "attribution": "English Wiktionary contributors; revision 123",
                "source_title": "शब्द",
                "source_url": "https://en.wiktionary.org/w/index.php?oldid=123",
                "source_revision": 123,
                "source_history_url": "https://en.wiktionary.org/w/index.php?action=history",
                "license_id": "CC-BY-SA-4.0",
                "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
                "quality_flags": ["needs_native_review"],
            }],
        }

        overlay = build_attribution_overlays(exports)

        self.assertEqual(set(overlay["records"]), {
            "tatoeba:42", "wiktionary_en:99:lemma",
        })
        self.assertEqual(overlay["records"]["tatoeba:42"]["attribution_name"], "sabretou")
        self.assertEqual(overlay["records"]["wiktionary_en:99:lemma"]["source_revision"], 123)
        serialized = json.dumps(overlay, ensure_ascii=False)
        self.assertNotIn("must not be copied", serialized)
        self.assertNotIn("text_normalized", serialized)

    def test_attribution_overlay_rejects_duplicate_source_record_ids(self):
        duplicate = {
            "record_id": "wiktionary_en:99:lemma",
            "source_id": "wiktionary_en",
        }
        with self.assertRaisesRegex(ValueError, "duplicate attribution overlay"):
            build_attribution_overlays({
                "wiktionary_cc_by_sa_4_0": [duplicate, duplicate],
            })

    def test_benchmark_exports_only_compatible_sources_and_keep_split_lineage(self):
        rows = [{
            "benchmark_id": "garhwali-bench-v0.2-draft",
            "example_id": "example-1",
            "language": "gbm",
            "split": "train",
            "task": "language_modeling",
            "payload": {"text": "गढ़वळी वाक्य"},
            "rights": {"public_rights_basis_as_recorded": [{
                "source_id": "obs_tlf_gbm_v1",
                "record_id": "obs_tlf_gbm_v1:001",
                "rights_status": "rights_assessed_compatible",
                "license_id": "CC-BY-SA-4.0",
                "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
                "attribution": "The Love Fellowship, Garhwali Open Bible Stories (TLF), version 1",
                "source_url": "https://git.door43.org/OBS-TLF/gbm_obs",
                "source_snapshot_sha256": "c" * 64,
                "modifications": "Unicode NFC",
                "quality_flags": ["translation_quality_unreviewed"],
                "script": "Deva",
                "title": "शीर्षक",
            }]},
            "legacy_record": {"provenance": [{
                "source_id": "obs_tlf_gbm_v1",
                "record_id": "obs_tlf_gbm_v1:001",
                "source_revision": "f" * 40,
                "source_file": "gbm_obs/content/001.md",
            }]},
        }, {
            "example_id": "unresolved-example",
            "split": "train",
            "payload": {"text": "इनको बाहर रखें"},
            "rights": {"public_rights_basis_as_recorded": [{
                "source_id": "meta_omni",
                "rights_status": "not_recorded",
            }]},
        }]

        exports = build_benchmark_exports(rows)
        record = exports["obs_tlf_gbm_v1_cc_by_sa_4_0"][0]

        self.assertEqual(len(exports["obs_tlf_gbm_v1_cc_by_sa_4_0"]), 1)
        self.assertEqual(exports["lsi_1916_public_domain"], [])
        self.assertEqual(record["source_record_id"], "obs_tlf_gbm_v1:001")
        self.assertEqual(record["record_id"], "obs_tlf_gbm_v1:001#example-1")
        self.assertEqual(record["benchmark_split"], "train")
        self.assertEqual(record["source_revision"], "f" * 40)
        self.assertFalse(record["training_eligible"])


if __name__ == "__main__":
    unittest.main()
