import unittest

import build_quality_tiers as m


class QualityTierTests(unittest.TestCase):
    def test_text_strict_tier_requires_language_rights_and_clean_signals(self):
        row = {
            "text": "मि ठीक छौं।",
            "language_bucket": "garhwali_candidate",
            "language_quality": {"confidence": "high", "review_required": False},
            "quality": {"quality_band": "review"},
            "cleanup_review_flags": [],
            "deep_cleanup_flags": [],
            "any_training_eligible_source": True,
            "provenance": [{"license": "CC-BY-4.0"}],
        }
        self.assertEqual(m.text_quality_decision(row)["tier"], "strict_gold_candidate")
        row["language_quality"]["confidence"] = "medium"
        self.assertEqual(m.text_quality_decision(row)["tier"], "experimental_review")

    def test_rights_only_failure_is_kept_as_high_quality_local(self):
        row = {
            "text": "मि ठीक छौं।",
            "language_bucket": "garhwali_candidate",
            "language_quality": {"confidence": "high", "review_required": False},
            "quality": {"quality_band": "review"},
            "cleanup_review_flags": [],
            "deep_cleanup_flags": [],
            "any_training_eligible_source": False,
            "provenance": [{"rights_status": "public_webpage_no_open_license_stated"}],
        }
        result = m.text_quality_decision(row)
        self.assertEqual(result["tier"], "high_quality_local_only")
        self.assertFalse(result["value_changed"])

    def test_resolved_cleanup_flags_allow_strict_promotion(self):
        row = {
            "text": "'''गढ़वाली'''",
            "language_bucket": "garhwali_candidate",
            "language_quality": {"confidence": "high", "review_required": False},
            "quality": {"quality_band": "review"},
            "cleanup_review_flags": ["html_markup"],
            "deep_cleanup_flags": [],
            "provenance": [{"license": "CC-BY-4.0"}],
        }
        refinement = {
            "release_text": "गढ़वाली",
            "remaining_cleanup_flags": [],
            "review_signals": [],
            "manual_review_required": False,
        }
        result = m.text_quality_decision(row, refinement)
        self.assertEqual(result["tier"], "strict_gold_candidate")
        self.assertTrue(result["value_changed"])

    def test_resolved_short_lexicon_is_not_low_surface_quality(self):
        row = {
            "text": "तू",
            "language_bucket": "garhwali_candidate",
            "language_quality": {"confidence": "high", "review_required": False},
            "quality": {"quality_band": "low"},
            "cleanup_review_flags": ["very_short"],
            "deep_cleanup_flags": [],
            "provenance": [{"license": "CC-BY-4.0"}],
        }
        refinement = {
            "release_text": "तू",
            "resolved_cleanup_flags": ["very_short"],
            "remaining_cleanup_flags": [],
            "review_signals": [],
            "manual_review_required": False,
        }
        self.assertEqual(
            m.text_quality_decision(row, refinement)["tier"],
            "strict_gold_candidate",
        )

    def test_supervised_speech_rejects_flagged_or_bad_audio(self):
        row = {
            "asr_target": "गढ़वाली पाठ",
            "language": "Garhwali",
            "quality_flags": [],
            "training_quality_flags": [],
            "transcript_review_flags": [],
            "audio_quality": {"readable": True, "sample_rate_hz": 16000, "channels": 1, "clipped_sample_share": 0},
            "recommended_for_supervised_training": True,
            "license": "CC-BY-4.0",
        }
        self.assertEqual(m.supervised_quality_decision(row)["tier"], "strict_gold_candidate")
        row["transcript_review_flags"] = ["mixed_script"]
        self.assertEqual(m.supervised_quality_decision(row)["tier"], "experimental_review")

    def test_supervised_refinement_adds_model_and_value_evidence(self):
        row = {
            "asr_target": "एक ( पाठ",
            "language": "Garhwali",
            "quality_flags": ["manual-transcript-review"],
            "training_quality_flags": ["manual-transcript-review"],
            "transcript_review_flags": ["manual-transcript-review"],
            "audio_quality": {
                "readable": True, "sample_rate_hz": 16000,
                "channels": 1, "clipped_sample_share": 0,
            },
            "recommended_for_supervised_training": False,
            "license": "CC-BY-4.0",
        }
        refinement = {
            "release_text": "एक पाठ",
            "automatic_changes": ["unmatched_open_parenthesis_removed"],
            "review_status": "listening_review_required",
            "model_evidence": {"models_agree": False},
        }
        result = m.supervised_quality_decision(row, refinement)
        self.assertEqual(result["tier"], "experimental_review")
        self.assertTrue(result["value_changed"])
        self.assertIn("mechanical_cleanup_applied", result["reasons"])
        self.assertIn("model_disagreement_requires_listening", result["reasons"])

    def test_machine_drafts_never_enter_gold_tier(self):
        standard = {"machine_transcript": "गढ़वाली पाठ", "machine_transcript_quality": {"level": "standard", "flags": []}}
        risky = {"machine_transcript": "", "machine_transcript_quality": {"level": "high_risk", "flags": ["no_devanagari_letters"]}}
        self.assertEqual(m.draft_quality_decision(standard)["tier"], "machine_draft_experimental")
        self.assertEqual(m.draft_quality_decision(risky)["tier"], "machine_draft_review")

    def test_source_conflict_draft_has_a_separate_preserved_tier(self):
        row = {
            "machine_transcript": "বাংলা পাঠ",
            "machine_transcript_quality": {
                "level": "high_risk", "flags": ["bengali_script"],
            },
            "language_scope_status": "source_label_conflict",
        }
        result = m.draft_quality_decision(row)
        self.assertEqual(result["tier"], "source_label_conflict_preserved")
        self.assertIn("source_label_conflict", result["reasons"])


if __name__ == "__main__":
    unittest.main()
