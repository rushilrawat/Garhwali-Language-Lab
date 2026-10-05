import unittest

from audit_upstream_split_overlap import build_report


class UpstreamSplitOverlapAuditTests(unittest.TestCase):
    def test_finds_direct_meta_eval_ids_and_community_text_matches(self):
        report = build_report(
            [
                {"record_id": "meta:test:1", "split": "test", "text_original": "परीक्षण वाक्य"},
                {"record_id": "meta:train:1", "split": "train", "text_original": "परीक्षण वाक्य"},
                {"record_id": "meta:dev:2", "split": "dev", "text_original": "दूसरू वाक्य"},
            ],
            [
                {"row_idx": 1, "split": "test", "transcript": "तीसरू वाक्य", "canonical_transcript": "तीसरू वाक्य"},
            ],
            [
                {"source": "facebook/omnilingual-asr-corpus", "sentence": "परीक्षण वाक्य"},
                {"source": "facebook/omnilingual-asr-corpus", "sentence": "दूसरू वाक्य"},
                {"source": "Vaani/Uttarakhand_TehriGarhwal", "sentence": "तीसरू वाक्य"},
                {"source": "unknown", "sentence": "अन्य वाक्य"},
            ],
        )

        self.assertEqual(
            report["meta_upstream_eval_record_ids"], ["meta:dev:2", "meta:test:1"]
        )
        matches = report["community_rows_with_eval_split_text_matches"]
        self.assertEqual(len(matches), 3)
        self.assertEqual(matches[0]["record_id"], "indic_dialect_asr_gbm:0")
        self.assertEqual(matches[0]["candidate_splits"], ["test", "train"])
        self.assertEqual(matches[0]["match_resolution"], "ambiguous_repeated_text_match")
        self.assertEqual(matches[1]["candidate_splits"], ["dev"])
        self.assertEqual(matches[2]["candidate_splits"], ["test"])

    def test_source_ids_are_content_free_and_row_order_is_explicit(self):
        report = build_report(
            [{"record_id": "m:1", "split": "train", "text_original": "अ"}],
            [],
            [{"source": "facebook/omnilingual-asr-corpus", "sentence": "अ"}],
        )

        self.assertEqual(report["community_rows_with_eval_split_text_matches"], [])
        self.assertEqual(report["source_row_counts"]["indic_dialect_asr_gbm"], 1)
        self.assertIn("not audio identity", report["matching_method"])


if __name__ == "__main__":
    unittest.main()
