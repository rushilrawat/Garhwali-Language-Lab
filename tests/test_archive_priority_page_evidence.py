import unittest

from audit_archive_priority_page_evidence import summarize_rows


class ArchivePriorityPageEvidenceTests(unittest.TestCase):
    def test_reports_duplicate_ids_without_exporting_page_text(self):
        text = "Repeated OCR footer"
        rows = [
            {
                "source_id": "ia_gunanand_juyal_madhya_pahadi_1967",
                "archive_review_candidate_group": "priority_language_study_review",
                "record_id": "source:page:0002",
                "text": text,
                "text_normalized": text,
                "automated_page_triage": {"script_profile": "mostly_latin", "warning_flags": []},
                "rights_status": "unverified_uploader_license_claim",
            },
            {
                "source_id": "ia_gunanand_juyal_madhya_pahadi_1967",
                "archive_review_candidate_group": "priority_language_study_review",
                "record_id": "source:page:0203",
                "text": text,
                "text_normalized": text,
                "automated_page_triage": {"script_profile": "mostly_latin", "warning_flags": []},
                "rights_status": "unverified_uploader_license_claim",
            },
        ]

        result = summarize_rows(rows)

        summary = result["sources"]["ia_gunanand_juyal_madhya_pahadi_1967"]
        self.assertEqual(summary["normalized_duplicate_groups"], [["source:page:0002", "source:page:0203"]])
        self.assertEqual(result["groups"]["priority_language_study_review"]["page_objects"], 2)
        self.assertNotIn("\"text\"", str(result))

    def test_ignores_sources_outside_the_scoped_phase_six_candidates(self):
        result = summarize_rows([{
            "source_id": "unrelated_source",
            "archive_review_candidate_group": "regional_context_not_verified_garhwali",
            "record_id": "unrelated:1",
            "text": "not included",
        }])

        self.assertNotIn("unrelated_source", result["sources"])
        self.assertTrue(all(item["page_objects"] == 0 for item in result["sources"].values()))
        self.assertEqual(result["groups"], {})


if __name__ == "__main__":
    unittest.main()
