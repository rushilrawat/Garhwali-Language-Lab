import unittest

from compare_hf_release_metrics import compare_reports, render_markdown


def preflight(release_id, *, configs=None, records=10, status="passed", errors=None):
    return {
        "release_id": release_id,
        "status": status,
        "errors": errors or [],
        "record_schema_version": "1.0.0",
        "validation_contract_version": "1.0.0",
        "validator_sha256": "a" * 64,
        "metric_definitions": {"records": "rows in config/split views"},
        "configs": configs or {"text/train": {"records": records}},
        "totals": {"records": records},
        "records_deleted_or_mutated": 0,
    }


class HuggingFaceReleaseMetricComparisonTests(unittest.TestCase):
    def test_report_pins_comparator_code_hash(self):
        comparison = compare_reports(
            preflight("v0.2.5"), preflight("v0.2.6"),
            comparison_script_sha256="c" * 64,
        )

        self.assertEqual(comparison["comparison_script_sha256"], "c" * 64)
        self.assertIn("Comparison script SHA-256", render_markdown(comparison))

    def test_added_view_row_count_is_preserved_and_rendered(self):
        previous = preflight("v0.2.5", configs={"text/train": {"records": 10}})
        candidate = preflight("v0.2.6", configs={
            "text/train": {"records": 10},
            "text_resources/source_overlap": {"records": 7},
        }, records=17)

        comparison = compare_reports(previous, candidate)
        rendered = render_markdown(comparison)

        self.assertEqual(comparison["summary"]["added_config_splits"], [
            "text_resources/source_overlap",
        ])
        self.assertIn("| `text_resources/source_overlap` | — | 7 | +7 |", rendered)
        self.assertIn("overlapping views", rendered)

    def test_comparison_rejects_incompatible_validation_contract(self):
        previous = preflight("v0.2.5")
        candidate = preflight("v0.2.6")
        candidate["validator_sha256"] = "b" * 64

        with self.assertRaisesRegex(ValueError, "incompatible validator_sha256"):
            compare_reports(previous, candidate)

    def test_comparison_rejects_failed_preflight(self):
        previous = preflight("v0.2.5")
        candidate = preflight("v0.2.6", status="failed", errors=["bad row"])

        with self.assertRaisesRegex(ValueError, "candidate preflight must have passed"):
            compare_reports(previous, candidate)

    def test_comparison_rejects_changed_metric_definitions(self):
        previous = preflight("v0.2.5")
        candidate = preflight("v0.2.6")
        candidate["metric_definitions"]["records"] = "different unit"

        with self.assertRaisesRegex(ValueError, "different metric definitions"):
            compare_reports(previous, candidate)


if __name__ == "__main__":
    unittest.main()
