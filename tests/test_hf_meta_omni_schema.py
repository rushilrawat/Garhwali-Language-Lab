import unittest

from build_hf_meta_omni_speech import make_release_record


class MetaOmnilingualSchemaTests(unittest.TestCase):
    def test_meta_record_includes_common_rights_and_quality_envelope(self):
        record = make_release_record({
            "record_id": "meta-1",
            "audio_sha256": "a" * 64,
            "text_sha256": "b" * 64,
            "duration_seconds": 2.5,
            "transcript": "पाठ",
            "elicitation_prompt": "prompt",
            "source_file": "source.tsv",
            "source_file_sha256": "c" * 64,
            "upstream_row_index": 3,
            "source_split": "dev",
            "split": "validation",
        }, {
            "duplicate_audio_count": 1,
            "duplicate_text_count": 1,
            "split_safe_for_training": True,
            "split_safe_for_evaluation": True,
        })

        self.assertEqual(record["rights_status"], "source_terms_recorded; inspect provenance")
        self.assertEqual(record["reuse_scope"], "attribution required under source license")
        self.assertEqual(record["license_labels"], ["CC-BY-4.0"])
        self.assertEqual(record["quality_status"], "unreviewed")
        self.assertEqual(record["record_quality_flags"], [])


if __name__ == "__main__":
    unittest.main()
