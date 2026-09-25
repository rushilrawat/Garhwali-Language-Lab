import unittest

from analyze_saved_asr_validation import build_report


class SavedAsrValidationTests(unittest.TestCase):
    def test_scores_only_frozen_validation_hashes_and_pairs_both_models(self):
        manifest = [
            {
                "row_idx": 7,
                "split": "validation",
                "audio_sha256": "val-a",
                "asr_target_clean": "एक घर",
            }
        ]
        predictions = {
            "sravaani": [
                {
                    "audio_sha256": "val-a",
                    "reference": "एक घर",
                    "hypothesis": "एक घर",
                },
                {
                    "audio_sha256": "test-b",
                    "reference": "test words",
                    "hypothesis": "wrong test text",
                },
            ],
            "whisper": [
                {
                    "audio_sha256": "val-a",
                    "reference": "एक घर",
                    "hypothesis": "एक",
                },
                {
                    "audio_sha256": "test-b",
                    "reference": "test words",
                    "hypothesis": "other test text",
                },
            ],
        }

        report = build_report(manifest, predictions)

        self.assertEqual(report["record_count"], 1)
        self.assertEqual(report["models"]["sravaani"]["word_errors"], 0)
        self.assertEqual(report["models"]["whisper"]["word_errors"], 1)
        self.assertEqual(report["ignored_prediction_rows"]["sravaani"], 1)
        self.assertEqual(report["ignored_prediction_rows"]["whisper"], 1)

    def test_rejects_prediction_reference_that_differs_from_frozen_manifest(self):
        manifest = [
            {
                "row_idx": 8,
                "split": "validation",
                "audio_sha256": "val-a",
                "asr_target_clean": "एक घर",
            }
        ]
        predictions = {
            name: [
                {
                    "audio_sha256": "val-a",
                    "reference": "दूसरा पाठ",
                    "hypothesis": "एक घर",
                }
            ]
            for name in ("sravaani", "whisper")
        }

        with self.assertRaisesRegex(ValueError, "reference does not match"):
            build_report(manifest, predictions)

    def test_rejects_missing_or_duplicate_validation_predictions(self):
        manifest = [
            {
                "row_idx": 8,
                "split": "validation",
                "audio_sha256": "val-a",
                "asr_target_clean": "एक घर",
            }
        ]
        incomplete = {"audio_sha256": "val-a", "reference": "एक घर", "hypothesis": "एक घर"}
        with self.assertRaisesRegex(ValueError, "missing validation prediction"):
            build_report(manifest, {"sravaani": [], "whisper": [incomplete]})

        duplicate = [incomplete, incomplete]
        with self.assertRaisesRegex(ValueError, "duplicate validation prediction"):
            build_report(manifest, {"sravaani": duplicate, "whisper": [incomplete]})


if __name__ == "__main__":
    unittest.main()
