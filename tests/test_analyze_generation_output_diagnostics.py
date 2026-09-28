import json
import unittest

from analyze_generation_output_diagnostics import summarize_predictions


class GenerationOutputDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.validation_rows = [
            {
                "instruction_sha256": f"{index:064x}",
                "split": "validation",
                "task": "translation",
                "response": reference,
            }
            for index, reference in enumerate(("Latin", "Latin", "देवनागरी", "text"), start=1)
        ]
        hypotheses = (
            "A A A A A A", "a a a a a a", "कककककक", "\ufffd\u200b\x01\ud800",
        )
        self.predictions = {
            "seed-17": [
                {
                    "record_id": f"instruction:{row['instruction_sha256']}",
                    "instruction_sha256": row["instruction_sha256"],
                    "task": row["task"],
                    "reference": row["response"],
                    "hypothesis": hypothesis,
                }
                for row, hypothesis in zip(self.validation_rows, hypotheses)
            ],
        }

    def test_reports_structure_and_mode_collapse_without_copying_text(self):
        report = summarize_predictions(self.validation_rows, self.predictions)
        seed_report = report["seeds"]["seed-17"]
        overall = seed_report["overall"]
        task = seed_report["by_task"]["translation"]

        self.assertEqual(report["evaluation_split"], "instructions_v0.2/validation")
        self.assertFalse(report["test_rows_scored"])
        self.assertEqual(overall["records"], 4)
        self.assertEqual(task["unique_normalized_outputs"], 3)
        self.assertEqual(task["repeated_output_groups"], 1)
        self.assertEqual(task["rows_in_repeated_output_groups"], 2)
        self.assertEqual(task["largest_mode_count"], 2)
        self.assertNotIn("largest_mode_count", overall)
        self.assertEqual(overall["max_adjacent_token_run"], 6)
        self.assertEqual(overall["outputs_with_token_run_at_least_3"], 2)
        self.assertEqual(overall["max_repeated_character_run"], 6)
        self.assertEqual(overall["outputs_with_character_run_at_least_6"], 1)
        self.assertEqual(overall["unicode_replacement_character_outputs"], 1)
        self.assertEqual(overall["surrogate_code_point_outputs"], 1)
        self.assertEqual(overall["control_character_outputs"], 1)
        self.assertEqual(overall["suspicious_invisible_character_outputs"], 1)
        self.assertEqual(
            overall["output_script_profile"],
            {"latin_only": 2, "devanagari_only": 1, "mixed_latin_devanagari": 0,
             "other_or_mixed": 0, "no_letters": 1},
        )
        serialized = json.dumps(report, ensure_ascii=False)
        for hypothesis in self.predictions["seed-17"]:
            self.assertNotIn(hypothesis["hypothesis"], serialized)

    def test_rejects_rows_outside_validation_and_duplicate_prediction_ids(self):
        rows = [dict(row) for row in self.validation_rows]
        rows[0]["split"] = "test"
        with self.assertRaisesRegex(ValueError, "validation"):
            summarize_predictions(rows, self.predictions)

        rows = self.validation_rows
        predictions = {"seed-17": [*self.predictions["seed-17"], self.predictions["seed-17"][0]]}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            summarize_predictions(rows, predictions)


if __name__ == "__main__":
    unittest.main()
