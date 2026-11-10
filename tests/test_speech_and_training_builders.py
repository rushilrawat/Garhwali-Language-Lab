"""Tests for the speaker-recovered ASR, speech-view, and text-candidate builders."""

import json
import unittest

import build_hf_speech_training_views_v0_2 as speech_views
import build_model_training_candidate as candidate
import build_vaani_speaker_recovered_asr_v0_1 as recovered


def clean_row(**overrides):
    row = {
        "speaker_id": "spk-1",
        "language_quality": {"status": "garhwali_candidate", "review_required": False},
        "transcript_review_flags": [],
        "asr_target_clean": "मेरु गौं",
        "recommended_for_supervised_training": True,
        "audio_quality": {"readable": True},
        "training_quality_flags": [],
    }
    row.update(overrides)
    return row


class SpeakerRecoveredAsrTests(unittest.TestCase):
    def test_placeholder_speakers_are_unidentified(self):
        for value in (None, "", " NA ", "n/a", "Unknown", "null", "unidentified"):
            self.assertFalse(recovered.is_identified(value), value)
        self.assertTrue(recovered.is_identified("spk-7"))

    def test_exclusion_reasons_follow_review_priority(self):
        self.assertIsNone(recovered.exclusion_reason(clean_row()))
        self.assertEqual(
            recovered.exclusion_reason(clean_row(speaker_id="NA")), "unidentified_speaker"
        )
        for override in (
            {"language_quality": {"status": "mixed_language"}},
            {"language_quality": {"status": "garhwali_candidate", "review_required": True}},
            {"transcript_review_flags": ["possibly_incomplete"]},
            {"asr_target_clean": "  "},
        ):
            self.assertEqual(
                recovered.exclusion_reason(clean_row(**override)),
                "transcript_or_language_review", override,
            )
        for override in (
            {"recommended_for_supervised_training": False},
            {"audio_quality": {"readable": False}},
            {"training_quality_flags": ["clipping"]},
        ):
            self.assertEqual(
                recovered.exclusion_reason(clean_row(**override)), "audio_quality_review", override
            )

    def test_source_keys_match_raw_and_prepared_field_names(self):
        raw = {"referenceImage": "img.jpg", "district": "Tehri", "transcript": " मेरु   गौं "}
        prepared = {"reference_image": "img.jpg", "district": "Tehri", "transcript": "मेरु गौं"}
        self.assertEqual(recovered.exact_source_key(raw), recovered.prepared_source_key(prepared))

    def test_target_key_ignores_punctuation_and_case_for_split_safety(self):
        self.assertEqual(
            recovered.normalized_target_key({"asr_target_clean": "Mero, गौं!"}),
            recovered.normalized_target_key({"asr_target_clean": "mero गौं"}),
        )


class SpeechTrainingViewTests(unittest.TestCase):
    def test_training_guide_reports_split_counts(self):
        guide = speech_views.training_guide({"train": 2202, "validation": 373, "test": 143})
        self.assertIn("2,202\ntrain, 373 validation, and 143 test rows", guide)

    def test_readme_update_requires_existing_v01_paths(self):
        with self.assertRaisesRegex(ValueError, "missing expected v0.1 card path"):
            speech_views.updated_readme("no paths here", {"train": 1, "validation": 1, "test": 1})


class TextTrainingCandidateTests(unittest.TestCase):
    def test_json_cells_and_csv_values_round_trip(self):
        self.assertEqual(candidate.parse_json_cell("", ["default"]), ["default"])
        self.assertEqual(candidate.parse_json_cell('["a","b"]', []), ["a", "b"])
        with self.assertRaisesRegex(ValueError, "JSON-encoded CSV value"):
            candidate.parse_json_cell("[unterminated", [])
        self.assertEqual(candidate.csv_value(["क", {"x": 1}]), '["क",{"x":1}]')
        self.assertEqual(candidate.csv_value(None), "")
        self.assertEqual(candidate.csv_value(3), 3)

    def _meta_row(self, text, **overrides):
        row = {
            "id": "row-1", "text": text, "source_id": "meta_omni",
            "source_record_ids": json.dumps(["meta:1"]),
            "training_eligibility_decision_id": "meta_omnilingual_cc_by_4_0_training_2026_10_06",
            "recommended_for_training": "true", "source_license_id": "CC-BY-4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "rights_status": "upstream_meta_cc_by_4_0", "rights_evidence_url": "https://example.org",
            "attribution": "Meta", "quality_status": "automated", "quality_flags": "[]",
        }
        row.update(overrides)
        return row

    def test_meta_rows_need_the_exact_project_decision_to_be_training_eligible(self):
        long_text = "मेरु गौं पहाड़ मा च बल"
        eligible = candidate.meta_record(self._meta_row(long_text))
        self.assertTrue(eligible["project_training_eligible"])
        self.assertEqual(eligible["split"], "train")
        other = candidate.meta_record(self._meta_row(long_text, training_eligibility_decision_id="other"))
        self.assertFalse(other["project_training_eligible"])
        self.assertFalse(other["project_public_release_cleared"])

    def test_meta_rows_are_routed_by_length(self):
        with self.assertRaisesRegex(ValueError, "Short text incorrectly routed to training"):
            candidate.meta_record(self._meta_row("दुई शब्द"))
        context = candidate.meta_record(self._meta_row("दुई शब्द"), context=True)
        self.assertEqual(context["split"], "context")
        self.assertFalse(context["project_training_eligible"])

    def test_source_rows_stay_in_the_review_queue(self):
        split, row = candidate.source_record({
            "record_id": "obs:1", "text_normalized": "एक दुई तीन चार पांच छह",
            "benchmark_split": "train", "source_id": "obs", "source_record_id": "obs:1",
            "license_id": "CC-BY-SA-4.0", "license_url": "https://example.org", "rights_status": "x",
        })
        self.assertEqual(split, "review_queue")
        self.assertTrue(row["candidate_for_experimental_training"])
        self.assertFalse(row["project_training_eligible"])
        with self.assertRaisesRegex(ValueError, "Unexpected source split"):
            candidate.source_record({"record_id": "x", "benchmark_split": "dev"})


if __name__ == "__main__":
    unittest.main()
