import json
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


class ReuseScopeLicenseTests(unittest.TestCase):
    """Every licence family maps to its own conditions; broader prefixes never win."""

    def test_each_license_family_gets_its_own_conditions(self):
        cases = {
            "CC-BY-4.0": "attribution required under source license",
            "CC BY 4.0": "attribution required under source license",
            "cc-by-sa-4.0": "attribution and share-alike required under source license",
            "CC-BY-NC-4.0": "noncommercial use and attribution required under source license",
            "CC-BY-NC-SA-4.0": "noncommercial use; attribution and share-alike required",
            "CC-BY-ND-4.0": "attribution required, no derivatives under source license",
            "CC-BY-NC-ND-4.0": "noncommercial use, attribution required, no derivatives under source license",
            "CC BY-NC-ND 3.0": "noncommercial use, attribution required, no derivatives under source license",
            "MIT": "MIT terms; preserve copyright and license notice",
            "Apache-2.0": "Apache-2.0 terms; preserve notices and review source scope",
            "CC0-1.0": "CC0 dedication recorded; verify any third-party content",
            "PDM-1.0": "public-domain mark or status recorded; verify source and jurisdiction",
            "public domain": "public-domain mark or status recorded; verify source and jurisdiction",
            "limited permission": "source-specific terms; inspect provenance before reuse",
        }
        for license_id, expected in cases.items():
            with self.subTest(license_id=license_id):
                self.assertEqual(normalize_record({"license_id": license_id})["reuse_scope"], expected)

    def test_no_derivatives_is_never_reported_as_plain_attribution(self):
        for license_id in ("CC-BY-ND-4.0", "CC-BY-NC-ND-4.0", "CC BY-NC-ND 3.0."):
            with self.subTest(license_id=license_id):
                self.assertIn("no derivatives", normalize_record({"license_id": license_id})["reuse_scope"])

    def test_most_restrictive_family_wins_when_sources_disagree(self):
        row = normalize_record({"provenance": [
            {"license_id": "CC-BY-4.0"}, {"license_id": "CC-BY-NC-SA-4.0"},
        ]})
        self.assertEqual(row["license_labels"], ["CC-BY-4.0", "CC-BY-NC-SA-4.0"])
        self.assertEqual(row["reuse_scope"], "noncommercial use; attribution and share-alike required")

    def test_explicit_reuse_scope_and_commercial_status_take_precedence(self):
        self.assertEqual(
            normalize_record({"reuse_scope": "local only", "license_id": "MIT"})["reuse_scope"],
            "local only",
        )
        row = normalize_record({"commercial_use_status": "allowed", "sharealike_required": True,
                                "license_id": "CC-BY-SA-4.0"})
        self.assertEqual(row["reuse_scope"], "allowed; share-alike required")


class RightsStatusFallbackTests(unittest.TestCase):
    def test_placeholder_statuses_fall_through_to_source_evidence(self):
        for placeholder in ("", "not_assessed", "Not_Recorded", " unassessed "):
            with self.subTest(placeholder=placeholder):
                row = normalize_record({
                    "rights_status": placeholder,
                    "provenance": [{"rights_status": "licensed"}],
                })
                self.assertEqual(row["rights_status"], "licensed")

    def test_conflicting_source_statuses_are_reported_as_mixed(self):
        row = normalize_record({"provenance": [
            {"rights_status": "licensed"}, {"rights_status": "rights_pending"},
            {"rights_status": "licensed"},
        ]})
        self.assertEqual(row["rights_status"], "mixed_source_statuses; inspect provenance")

    def test_public_url_without_license_is_not_promoted_to_permission(self):
        row = normalize_record({"source_url": "https://example.org/garhwali"})
        self.assertEqual(row["rights_status"], "not_assessed")
        self.assertEqual(row["reuse_scope"], "not assessed")
        self.assertEqual(row["license_labels"], [])
        self.assertEqual(row["quality_status"], "not_reviewed")

    def test_unavailable_text_is_rights_pending_and_not_cleared(self):
        row = normalize_record({"text_publicly_available": False, "license_id": "unknown"})
        self.assertEqual(row["rights_status"], "rights_pending")
        self.assertEqual(row["reuse_scope"], "not cleared for redistribution")
        self.assertEqual(row["record_quality_flags"], ["source_text_not_publicly_redistributable"])


class NormalizeRecordContractTests(unittest.TestCase):
    ROW = {
        "rights_status": "not_recorded",
        "provenance": [{"license_id": "CC-BY-SA-4.0", "quality_flags": ["ocr"]}],
        "quality_flags": ["short", "ocr", ""],
        "quality_summary_json": "{\"quality_flags\": [\"needs_review\"]}",
    }

    def test_input_row_is_not_mutated(self):
        original = json.loads(json.dumps(self.ROW))
        normalize_record(self.ROW)
        self.assertEqual(self.ROW, original)

    def test_normalizing_twice_is_stable(self):
        once = normalize_record(self.ROW)
        self.assertEqual(normalize_record(once), once)

    def test_flags_are_deduplicated_in_first_seen_order_without_blanks(self):
        row = normalize_record(self.ROW)
        self.assertEqual(row["record_quality_flags"], ["short", "ocr", "needs_review"])
        self.assertEqual(row["quality_status"], "automated_quality_assessed_unreviewed")

    def test_malformed_quality_summary_is_ignored_not_raised(self):
        row = normalize_record({"quality_summary_json": "{not json"})
        self.assertEqual(row["record_quality_flags"], [])
        self.assertEqual(row["quality_status"], "not_reviewed")


if __name__ == "__main__":
    unittest.main()
