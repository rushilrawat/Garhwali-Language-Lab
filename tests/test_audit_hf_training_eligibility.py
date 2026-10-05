import unittest

import audit_hf_training_eligibility as audit


class HuggingFaceTrainingEligibilityAuditTests(unittest.TestCase):
    def setUp(self):
        self.licensed_source = {
            "source_id": "source-a",
            "record_id": "source-a:1",
            "source_url": "https://example.org/source",
            "rights_status": "licensed",
            "license_id": "CC-BY-4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "attribution": "Example source contributors",
            "training_eligible": False,
            "experimental_training_eligible": True,
            "quality_flags": [],
        }
        self.row = {
            "id": "record-a",
            "language": "gbm",
            "source_languages": ["gbm"],
            "language_buckets": ["garhwali_candidate"],
            "quality_tiers": ["strict_gold_candidate"],
            "quality_flags": [],
            "record_quality_flags": [],
            "split": "train",
            "recommended_for_training": False,
            "provenance": [dict(self.licensed_source)],
            "public_rights_basis": [dict(self.licensed_source)],
        }

    def test_counterfactual_is_diagnostic_only_and_preserves_quality_blocks(self):
        original = dict(self.row["provenance"][0])
        report = audit.summarize_config([self.row])
        self.assertEqual(report["recomputed_recommended_for_training"], 0)
        self.assertEqual(
            report["diagnostic_recommended_if_false_source_flags_resolved"], 1
        )
        self.assertEqual(self.row["provenance"][0], original)

        flagged = dict(self.row)
        flagged["provenance"] = [{**original, "quality_flags": ["unreviewed"]}]
        flagged["public_rights_basis"] = [{**original, "quality_flags": ["unreviewed"]}]
        flagged_report = audit.summarize_config([flagged])
        self.assertEqual(
            flagged_report["diagnostic_recommended_if_false_source_flags_resolved"], 0
        )

    def test_source_counts_are_unique_per_record_and_do_not_use_experimental_flag(self):
        report = audit.summarize_config([self.row])
        source = report["source_records"][0]
        self.assertEqual(source["source_id"], "source-a")
        self.assertEqual(source["records"], 1)
        self.assertEqual(source["records_with_explicit_training_false"], 1)
        self.assertEqual(report["explicit_source_training_false"], 1)
        self.assertEqual(report["stored_recommendation_mismatches"], 0)


if __name__ == "__main__":
    unittest.main()
