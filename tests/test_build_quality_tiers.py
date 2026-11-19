import unittest
from collections import Counter

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

    def test_rights_only_failure_is_kept_as_high_quality_rights_pending(self):
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
        self.assertEqual(result["tier"], "high_quality_rights_pending")
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


def strict_text_row(**overrides):
    row = {
        "text": "मि ठीक छौं।",
        "language_bucket": "garhwali_candidate",
        "language_quality": {"confidence": "high", "review_required": False},
        "quality": {"quality_band": "review"},
        "cleanup_review_flags": [],
        "deep_cleanup_flags": [],
        "provenance": [{"license": "CC-BY-4.0"}],
    }
    row.update(overrides)
    return row


def strict_speech_row(**overrides):
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
    row.update(overrides)
    return row


class TextGateTests(unittest.TestCase):
    """Each strict-tier gate demotes a row on its own and names its reason."""

    def test_baseline_row_is_strict(self):
        self.assertEqual(
            m.text_quality_decision(strict_text_row()),
            {"tier": "strict_gold_candidate", "reasons": [], "value_changed": False},
        )

    def test_each_failed_gate_demotes_with_exactly_its_reason(self):
        cases = {
            "language_confidence_not_high": {"language_quality": {"confidence": "medium"}},
            "language_review_required": {"language_quality": {"confidence": "high", "review_required": True}},
            "low_surface_quality": {"quality": {"quality_band": "low"}},
            "cleanup_review_required": {"deep_cleanup_flags": ["broken_matra"]},
        }
        for reason, overrides in cases.items():
            with self.subTest(reason=reason):
                result = m.text_quality_decision(strict_text_row(**overrides))
                self.assertEqual(result["tier"], "experimental_review")
                self.assertEqual(result["reasons"], [reason])

    def test_empty_and_non_garhwali_rows_get_their_own_tiers(self):
        empty = m.text_quality_decision(strict_text_row(text="   "))
        self.assertEqual(empty["tier"], "unusable_empty")
        self.assertIn("empty_text", empty["reasons"])
        context = m.text_quality_decision(strict_text_row(language_bucket="hindi_context"))
        self.assertEqual(context["tier"], "non_strict_context")
        self.assertEqual(context["reasons"], ["not_garhwali_candidate"])

    def test_rights_plus_another_failure_is_not_rights_pending(self):
        result = m.text_quality_decision(strict_text_row(
            provenance=[{"rights_status": "rights_pending"}],
            quality={"quality_band": "low"},
        ))
        self.assertEqual(result["tier"], "experimental_review")
        self.assertEqual(result["reasons"], ["low_surface_quality", "no_rights_cleared_training_source"])

    def test_refinement_replaces_row_cleanup_flags(self):
        row = strict_text_row(cleanup_review_flags=["html_markup"])
        still_flagged = {"release_text": row["text"], "remaining_cleanup_flags": ["url"]}
        self.assertEqual(m.text_quality_decision(row, still_flagged)["reasons"], ["cleanup_review_required"])
        manual = {"release_text": row["text"], "manual_review_required": True}
        self.assertEqual(m.text_quality_decision(row, manual)["reasons"], ["cleanup_review_required"])

    def test_short_lexicon_needing_manual_review_stays_low_quality(self):
        refinement = {
            "release_text": "तू",
            "resolved_cleanup_flags": ["very_short"],
            "manual_review_required": True,
        }
        result = m.text_quality_decision(strict_text_row(text="तू", quality={"quality_band": "low"}), refinement)
        self.assertIn("low_surface_quality", result["reasons"])


class SpeechGateTests(unittest.TestCase):
    def test_baseline_row_is_strict(self):
        self.assertEqual(m.supervised_quality_decision(strict_speech_row())["reasons"], [])

    def test_each_failed_gate_demotes_with_exactly_its_reason(self):
        good_audio = strict_speech_row()["audio_quality"]
        cases = {
            "empty_transcript": {"asr_target": " "},
            "source_language_not_garhwali": {"language": "Hindi"},
            "existing_review_flag": {"training_quality_flags": ["noisy"]},
            "unreadable_audio": {"audio_quality": {**good_audio, "readable": False}},
            "noncanonical_audio_format": {"audio_quality": {**good_audio, "sample_rate_hz": 8000}},
            "material_clipping": {"audio_quality": {**good_audio, "clipped_sample_share": 0.0011}},
            "not_recommended_for_supervised_training": {"recommended_for_supervised_training": False},
            "missing_license": {"license": ""},
        }
        for reason, overrides in cases.items():
            with self.subTest(reason=reason):
                result = m.supervised_quality_decision(strict_speech_row(**overrides))
                self.assertEqual(result["tier"], "experimental_review")
                self.assertEqual(result["reasons"], [reason])

    def test_stereo_audio_is_noncanonical(self):
        audio = {**strict_speech_row()["audio_quality"], "channels": 2}
        self.assertEqual(
            m.supervised_quality_decision(strict_speech_row(audio_quality=audio))["reasons"],
            ["noncanonical_audio_format"],
        )

    def test_clipping_threshold_is_exclusive(self):
        audio = {**strict_speech_row()["audio_quality"], "clipped_sample_share": 0.001}
        self.assertEqual(m.supervised_quality_decision(strict_speech_row(audio_quality=audio))["reasons"], [])

    def test_agreeing_models_without_cleanup_keep_strict_tier(self):
        refinement = {"release_text": "गढ़वाली पाठ", "model_evidence": {"models_agree": True}}
        result = m.supervised_quality_decision(strict_speech_row(), refinement)
        self.assertEqual(result, {"tier": "strict_gold_candidate", "reasons": [], "value_changed": False})


class DraftAndSummaryTests(unittest.TestCase):
    def test_low_cross_model_confidence_needs_review(self):
        for band in ("low", "very_low"):
            with self.subTest(band=band):
                result = m.draft_quality_decision({
                    "machine_transcript": "गढ़वाली पाठ",
                    "recovery_confidence": {"confidence_band": band},
                })
                self.assertEqual(result["tier"], "machine_draft_review")
                self.assertEqual(result["reasons"], ["low_cross_model_confidence"])

    def test_draft_reasons_are_sorted_and_unique(self):
        result = m.draft_quality_decision({
            "machine_transcript": "",
            "machine_transcript_quality": {"level": "high_risk", "flags": ["z_flag", "empty_machine_transcript"]},
        })
        self.assertEqual(result["reasons"], ["empty_machine_transcript", "machine_draft_high_risk", "z_flag"])

    def test_summary_rates_and_reason_order(self):
        summary = m.summarize(Counter({"b": 1, "a": 3}), Counter({"y": 2, "x": 2, "z": 5}))
        self.assertEqual(summary["records"], 4)
        self.assertEqual(summary["tier_rates"], {"a": 0.75, "b": 0.25})
        self.assertEqual(list(summary["reason_counts"]), ["z", "x", "y"])

    def test_empty_summary_does_not_divide_by_zero(self):
        self.assertEqual(m.summarize(Counter(), Counter())["records"], 0)


if __name__ == "__main__":
    unittest.main()
