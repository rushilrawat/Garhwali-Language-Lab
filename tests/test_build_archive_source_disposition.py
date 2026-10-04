import unittest

from build_archive_source_disposition import _license_class, classify_page_candidate, triage_page_text


class ArchiveSourceDispositionTests(unittest.TestCase):
    def test_reports_license_metadata_mismatch_without_selecting_a_license(self):
        claim, uri, conflict = _license_class({
            "licenseurl": "https://creativecommons.org/licenses/by/4.0/",
            "rights": "© 2021. CC-BY-SA 4.0.",
        })

        self.assertEqual(claim, "cc_by_claim")
        self.assertEqual(uri, "https://creativecommons.org/licenses/by/4.0/")
        self.assertTrue(conflict)

    def test_keeps_archive_public_domain_mark_as_a_claim_class(self):
        claim, _, conflict = _license_class({
            "licenseurl": "https://creativecommons.org/publicdomain/mark/1.0/",
        })

        self.assertEqual(claim, "public_domain_mark_claim")
        self.assertFalse(conflict)

    def test_language_scope_is_only_a_review_priority(self):
        group, reason = classify_page_candidate(
            "multilingual Garhwali-focused research source", None, "पृष्ठ OCR",
        )

        self.assertEqual(group, "priority_language_study_review")
        self.assertIn("does not verify", reason)

    def test_empty_ocr_pages_remain_visible_for_scan_followup(self):
        group, reason = classify_page_candidate("English OCR", None, " ")

        self.assertEqual(group, "empty_ocr_page_pending_visual_check")
        self.assertIn("retain the source scan", reason)

    def test_alternate_scan_is_labeled_but_not_removed(self):
        group, reason = classify_page_candidate("multilingual Garhwali-focused research source", "existing-book", "page")

        self.assertEqual(group, "known_alternate_scan_of_existing_work")
        self.assertIn("Retain the page", reason)

    def test_page_triage_reports_script_and_warnings_without_language_claim(self):
        result = triage_page_text("गढ़वाली भाषा 12345")

        self.assertEqual(result["script_profile"], "mostly_devanagari")
        self.assertIn("high_digit_ratio", result["warning_flags"])
        self.assertEqual(result["language_identification"], "not_performed")


if __name__ == "__main__":
    unittest.main()
