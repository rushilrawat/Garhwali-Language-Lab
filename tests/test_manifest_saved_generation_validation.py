import unittest

from manifest_saved_generation_validation import build_manifest_runs
from run_mt5_instruction_tuning import generation_diagnostics


class SavedGenerationManifestTests(unittest.TestCase):
    def setUp(self):
        self.validation_rows = [
            {
                "instruction_sha256": "a" * 64,
                "split": "validation",
                "task": "garhwali_to_english",
                "instruction": "Translate A",
                "response": "Answer A",
                "acceptable_responses": ["Answer A", "Alternative A"],
            },
            {
                "instruction_sha256": "b" * 64,
                "split": "validation",
                "task": "english_to_garhwali",
                "instruction": "Translate B",
                "response": "Answer B",
                "acceptable_responses": ["Answer B"],
            },
        ]
        self.predictions = [
            {
                "system": seed,
                "task": row["task"],
                "instruction_sha256": row["instruction_sha256"],
                "reference": row["response"],
                "hypothesis": f"{seed} output {row['instruction_sha256'][0]}",
            }
            for seed in ("seed-17", "seed-29")
            for row in self.validation_rows
        ]
        system_metrics = {}
        for seed in ("seed-17", "seed-29"):
            seed_predictions = [row for row in self.predictions if row["system"] == seed]
            rows = [
                row | {"acceptable_responses": [prediction["reference"]]}
                for row, prediction in zip(self.validation_rows, seed_predictions)
            ]
            hypotheses = [row["hypothesis"] for row in seed_predictions]
            diagnostics, _ = generation_diagnostics(rows, hypotheses)
            system_metrics[seed] = {
                "cross_entropy": 1.0,
                "corpus_chrf2": diagnostics["overall"]["corpus_chrf2"],
                "exact_match": diagnostics["overall"]["exact_match"],
                "diagnostics": diagnostics,
            }
        self.report = {
            "run_id": "mt0-validation",
            "selection_split": "validation",
            "validation_records": 2,
            "fixed_test_opened": False,
            "systems": system_metrics,
        }

    def test_builds_seed_runs_only_for_exact_validation_selection(self):
        runs = build_manifest_runs(
            self.validation_rows,
            self.predictions,
            self.report,
            validation_sha256="c" * 64,
            prediction_sha256="d" * 64,
            generation_report_sha256="e" * 64,
        )

        self.assertEqual(set(runs), {"seed-17", "seed-29"})
        for seed, run in runs.items():
            self.assertEqual(run["report"]["evaluation_split"], "instructions_v0.2/validation")
            self.assertEqual(run["report"]["evaluation_records"], 2)
            self.assertEqual(run["report"]["input_sha256"], "c" * 64)
            self.assertEqual(run["report"]["prediction_input_sha256"], "d" * 64)
            self.assertEqual(run["report"]["generation_report_sha256"], "e" * 64)
            self.assertEqual(run["report"]["metrics"], self.report["systems"][seed])
            reconciliation = run["report"]["metric_reconciliation"]
            self.assertEqual(
                reconciliation["recomputed_primary_reference_diagnostics"],
                self.report["systems"][seed]["diagnostics"],
            )
            self.assertIn(
                "chrf2_delta_vs_primary",
                reconciliation["current_validation_alternative_reference_sensitivity"],
            )
            self.assertEqual(run["config"]["source_validation_manifest_sha256"], "c" * 64)
            self.assertEqual(run["config"]["source_predictions_sha256"], "d" * 64)
            self.assertEqual(run["config"]["source_report_sha256"], "e" * 64)
            self.assertEqual(
                {row["record_id"] for row in run["predictions"]},
                {f"instruction:{row['instruction_sha256']}" for row in self.validation_rows},
            )
            self.assertFalse(run["report"]["test_rows_scored"])

    def test_rejects_missing_seed_prediction(self):
        predictions = [row for row in self.predictions if not (
            row["system"] == "seed-17" and row["instruction_sha256"] == "a" * 64
        )]
        with self.assertRaisesRegex(ValueError, "do not share one validation record set"):
            build_manifest_runs(
                self.validation_rows,
                predictions,
                self.report,
                validation_sha256="c" * 64,
                prediction_sha256="d" * 64,
                generation_report_sha256="e" * 64,
            )

    def test_rejects_reference_or_task_mismatch(self):
        predictions = [dict(row) for row in self.predictions]
        predictions[0]["reference"] = "wrong reference"
        with self.assertRaisesRegex(ValueError, "reference differs"):
            build_manifest_runs(
                self.validation_rows,
                predictions,
                self.report,
                validation_sha256="c" * 64,
                prediction_sha256="d" * 64,
                generation_report_sha256="e" * 64,
            )

        predictions = [dict(row) for row in self.predictions]
        predictions[0]["task"] = "wrong_task"
        with self.assertRaisesRegex(ValueError, "task differs"):
            build_manifest_runs(
                self.validation_rows,
                predictions,
                self.report,
                validation_sha256="c" * 64,
                prediction_sha256="d" * 64,
                generation_report_sha256="e" * 64,
            )

    def test_rejects_saved_generation_metric_mismatch(self):
        report = {
            **self.report,
            "systems": {
                **self.report["systems"],
                "seed-17": {
                    **self.report["systems"]["seed-17"],
                    "corpus_chrf2": 0.9,
                },
            },
        }
        with self.assertRaisesRegex(ValueError, "primary-reference generation metrics differ"):
            build_manifest_runs(
                self.validation_rows,
                self.predictions,
                report,
                validation_sha256="c" * 64,
                prediction_sha256="d" * 64,
                generation_report_sha256="e" * 64,
            )

if __name__ == "__main__":
    unittest.main()
