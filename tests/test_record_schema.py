import unittest

from record_schema import COMMON_RECORD_FIELDS, normalize_record


class CommonRecordSchemaTests(unittest.TestCase):
    def test_lexicon_keeps_source_rights_and_unreviewed_quality_signals(self):
        row = normalize_record({
            "form": "example",
            "public_rights_basis": [{
                "license_id": "CC-BY-4.0",
                "rights_status": "licensed",
                "quality_flags": ["deferred_native_check"],
            }],
            "quality_flags": ["native_review_deferred"],
        }, family="lexicon")

        self.assertEqual(row["rights_status"], "licensed")
        self.assertEqual(row["reuse_scope"], "attribution required under source license")
        self.assertEqual(row["license_labels"], ["CC-BY-4.0"])
        self.assertIn("native_review_deferred", row["record_quality_flags"])
        self.assertIn("deferred_native_check", row["record_quality_flags"])
        self.assertIn("not linguistically reviewed", row["quality_status"])
        self.assertTrue(set(COMMON_RECORD_FIELDS).issubset(row))

    def test_pending_catalog_text_is_explicit_and_keeps_source_specific_fields(self):
        row = normalize_record({
            "redistribution_status": "rights_pending",
            "commercial_use_status": "not_cleared",
            "text_publicly_available": False,
            "quality_flags": ["ocr_unreviewed"],
        }, family="catalog")

        self.assertEqual(row["rights_status"], "rights_pending")
        self.assertEqual(row["reuse_scope"], "not_cleared")
        self.assertIn("source_text_not_publicly_redistributable", row["record_quality_flags"])
        self.assertEqual(row["redistribution_status"], "rights_pending")

    def test_mit_scope_is_useful_but_keeps_notice_condition(self):
        row = normalize_record({"license_id": "MIT"}, family="lexicon")
        self.assertEqual(row["reuse_scope"], "MIT terms; preserve copyright and license notice")

    def test_metadata_projection_does_not_assert_rights_to_underlying_work(self):
        row = normalize_record({
            "record_scope": "factual_bibliographic_metadata_only",
            "rights_status": "metadata_only; no license asserted for underlying work",
            "quality_metadata": {"review_status": "not_reviewed", "native_reviewed": False},
        }, family="literary_works")

        self.assertEqual(
            row["rights_status"],
            "metadata_only; no license asserted for underlying work",
        )
        self.assertIn("underlying-work rights are not asserted", row["reuse_scope"])
        self.assertEqual(row["quality_status"], "not_reviewed")

    def test_machine_draft_and_provider_reference_are_distinguishable(self):
        provider = normalize_record({
            "source_license": "CC-BY-4.0",
            "transcript_review_status": "provider_transcript_unadjudicated",
            "machine_draft": "draft text",
            "machine_draft_model": "SraVaani",
        }, family="garhwali_speech")
        draft = normalize_record({
            "machine_transcript_model": "SraVaani",
            "review_status": "machine_draft_noisy_experimental",
            "quality_flags": "[\"needs_review\"]",
        }, family="sravaani_drafts")

        self.assertEqual(provider["quality_status"], "provider_transcript_unadjudicated")
        self.assertIn("machine_draft_present; not human ground truth", provider["record_quality_flags"])
        self.assertEqual(draft["quality_status"], "machine_draft_noisy_experimental")
        self.assertEqual(draft["record_quality_flags"], ["needs_review"])

    def test_join_tables_direct_users_to_rights_and_source_rows(self):
        row = normalize_record({"record_ref": "r1", "source_ref_id": "s1"}, family="record_sources")
        self.assertEqual(row["rights_status"], "resolve_via_record_and_source_join")
        self.assertEqual(row["reuse_scope"], "resolve_via_record_and_source_join")
        self.assertEqual(row["quality_status"], "provenance_metadata_only")


if __name__ == "__main__":
    unittest.main()
