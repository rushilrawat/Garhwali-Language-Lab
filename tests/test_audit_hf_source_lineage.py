import unittest

from audit_hf_source_lineage import build_report


class HuggingFaceSourceLineageAuditTests(unittest.TestCase):
    def test_uses_text_hash_as_id_for_cleaned_parent_view_rows(self):
        source_rows = [
            {
                "source_id": "source-a",
                "record_id": "source-a:1",
                "upstream_source": "provider-one",
                "license_id": "CC-BY-4.0",
            }
        ]
        view_rows = [
            {
                "text_sha256": "abc123",
                "provenance": [{"source_id": "source-a", "record_id": "source-a:1"}],
            }
        ]

        report = build_report("source-a", source_rows, view_rows)

        self.assertEqual(report["view_rows_with_source"], 1)
        self.assertEqual(report["distinct_source_record_ids_linked"], 1)
        self.assertEqual(report["unlinked_source_record_count"], 0)

    def test_counts_source_rows_separately_from_segment_fanout(self):
        source_rows = [
            {
                "source_id": "source-a",
                "record_id": "source-a:1",
                "upstream_source": "provider-one",
                "license_id": "CC-BY-4.0",
            },
            {
                "source_id": "source-a",
                "record_id": "source-a:2",
                "upstream_source": "provider-two",
                "license_id": "CC-BY-4.0",
            },
            {
                "source_id": "source-a",
                "record_id": "source-a:3",
                "upstream_source": "provider-two",
                "license_id": "CC-BY-4.0",
            },
        ]
        view_rows = [
            {
                "id": "segment-a",
                "split": "train",
                "provenance": [{"source_id": "source-a", "record_id": "source-a:1"}],
            },
            {
                "id": "segment-b",
                "split": "train",
                "provenance": [
                    {"source_id": "source-a", "record_id": "source-a:1"},
                    {"source_id": "source-a", "record_id": "source-a:2"},
                    {"source_id": "source-a", "record_id": "source-a:1"},
                ],
            },
            {
                "id": "segment-c",
                "split": "validation",
                "provenance": [{"source_id": "source-a", "record_id": "source-a:2"}],
            },
        ]

        report = build_report("source-a", source_rows, view_rows)

        self.assertEqual(report["upstream_source_rows"], 3)
        self.assertEqual(report["view_rows_with_source"], 3)
        self.assertEqual(report["distinct_source_record_ids_linked"], 2)
        self.assertEqual(report["distinct_source_record_links"], 4)
        self.assertEqual(report["view_rows_with_multiple_source_records"], 1)
        self.assertEqual(report["source_records_with_fanout"], 2)
        self.assertEqual(report["source_record_fanout_histogram"], {"0": 1, "1": 0, "2": 2})
        self.assertEqual(report["unlinked_source_record_ids"], ["source-a:3"])
        self.assertEqual(report["unknown_view_source_record_ids"], [])
        self.assertEqual(report["view_rows_by_split"], {"train": 2, "validation": 1})


if __name__ == "__main__":
    unittest.main()
