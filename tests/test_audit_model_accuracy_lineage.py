import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import hashlib

from audit_model_accuracy_lineage import (
    BENCHMARKS,
    SINGLE_MANIFESTS,
    SPLIT_MANIFESTS,
    build_report,
    hash_overlap,
    read_jsonl,
    render_json,
    render_markdown,
)


class HashOverlapTests(unittest.TestCase):
    def test_reports_duplicate_hash_across_train_and_test_only(self):
        named_rows = {
            "train": [
                {"id": "train-1", "audio_sha256": "same-audio"},
                {"id": "train-2", "audio_sha256": "train-only"},
            ],
            "test": [
                {"id": "test-1", "audio_sha256": "same-audio"},
                {"id": "test-2", "audio_sha256": "test-only"},
            ],
        }

        self.assertEqual(
            hash_overlap(named_rows, "audio_sha256"),
            [
                {
                    "hash": "same-audio",
                    "rows": [
                        {"row_id": "test-1", "split": "test"},
                        {"row_id": "train-1", "split": "train"},
                    ],
                    "splits": ["test", "train"],
                }
            ],
        )

    def test_keeps_audio_duplicate_rows_with_conflicting_transcripts(self):
        rows = [
            {
                "id": "row-a",
                "audio_sha256": "shared-audio",
                "selected_transcript_sha256": "transcript-a",
            },
            {
                "id": "row-b",
                "audio_sha256": "shared-audio",
                "selected_transcript_sha256": "transcript-b",
            },
        ]

        groups = hash_overlap({"train": rows}, "audio_sha256")

        self.assertEqual(len(groups), 1)
        self.assertEqual([row["id"] for row in rows], ["row-a", "row-b"])
        self.assertEqual(
            [row["row_id"] for row in groups[0]["rows"]], ["row-a", "row-b"]
        )


class JsonlReaderTests(unittest.TestCase):
    def test_empty_manifest_returns_no_rows(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "empty.jsonl"
            path.write_text("\n", encoding="utf-8")

            self.assertEqual(read_jsonl(path), [])

    def test_malformed_line_reports_path_and_one_based_line(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.jsonl"
            path.write_text('{"id": "ok"}\nnot-json\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, rf"{path}:2:"):
                read_jsonl(path)


class LineageReportTests(unittest.TestCase):
    def _write_required_manifests(self, root):
        for family, splits in SPLIT_MANIFESTS.items():
            for split, relative_path in splits.items():
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                row = self._row(f"{family}:{split}:0", split)
                path.write_text(json.dumps(row) + "\n", encoding="utf-8")
        for family, config in SINGLE_MANIFESTS.items():
            path = root / config["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            rows = [
                self._row(f"{family}:{split}:0", split)
                for split in config["required_splits"]
            ]
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        for name, relative_path in BENCHMARKS.items():
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            rows = [self._row(f"{name}:{split}:0", split) for split in ("train", "dev", "test")]
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    @staticmethod
    def _row(record_id, split):
        token = record_id.replace(":", "-")
        return {
            "record_id": record_id,
            "audio_sha256": f"audio-{token}",
            "text_sha256": f"text-{token}",
            "selected_transcript_sha256": f"selected-{token}",
            "asr_target_sha256": f"target-{token}",
            "instruction_sha256": f"instruction-{token}",
            "speaker_id": f"speaker-{token}",
            "split": split,
        }

    def test_configuration_covers_all_planned_families_and_benchmarks(self):
        self.assertTrue(
            {
                "asr",
                "asr_expanded_human",
                "asr_experimental",
                "text_recommended",
                "instructions_v0.2",
                "tts",
                "meta_omnilingual_whisper_compatible",
            }.issubset(SPLIT_MANIFESTS)
        )
        self.assertIn("meta_omnilingual", SINGLE_MANIFESTS)
        self.assertEqual(set(BENCHMARKS), {"flores", "xorqa", "crosssum"})

    def test_markdown_keeps_speaker_identifier_ledger_local_only(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            markdown = render_markdown(build_report(root))

        self.assertIn("local-only JSON ledger", markdown)
        self.assertIn("contains VAANI speaker identifiers", markdown)
        self.assertIn("excluded from Git and public packages", markdown)

    def test_missing_required_split_fails_with_family_and_split(self):
        with TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(FileNotFoundError, r"asr/train.*train\.jsonl"):
                build_report(Path(temp_dir))

    def test_report_matches_prior_predictions_to_manifest_rows(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            asr_test = self._row("asr:test:0", "test")
            prediction_path = root / "data/processed/evaluation/asr/fake_predictions.jsonl"
            prediction_path.parent.mkdir(parents=True, exist_ok=True)
            prediction_path.write_text(
                json.dumps(
                    {
                        "record_id": asr_test["record_id"],
                        "audio_sha256": asr_test["audio_sha256"],
                        "hypothesis": "prediction",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (prediction_path.parent / "report.json").write_text(
                json.dumps(
                    {
                        "model_id": "example/model",
                        "revision": "abc123",
                        "dataset": {"test_sha256": "frozen-test-hash", "test_records": 1},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(root)

            prediction = next(
                item for item in report["predictions"] if item["path"].endswith("fake_predictions.jsonl")
            )
            self.assertEqual(prediction["matched_split_counts"]["asr"]["test"], 1)
            self.assertEqual(
                prediction["matched_test_rows"]["asr"][0]["hashes"]["audio_sha256"],
                asr_test["audio_sha256"],
            )
            self.assertEqual(prediction["model_metadata"]["model_id"], "example/model")
            self.assertEqual(prediction["model_metadata"]["test_sha256"], "frozen-test-hash")
            self.assertEqual(
                report["evaluation_decisions"]["vaani_asr_test"]["status"],
                "historical_only",
            )

    def test_internal_text_candidate_is_historical_after_aggregate_baseline(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)

            test_path = root / SPLIT_MANIFESTS["text_recommended"]["test"]
            test_rows = read_jsonl(test_path)
            test_rows[0]["text"] = "Garhwali example"
            test_path.write_text(
                "".join(json.dumps(row) + "\n" for row in test_rows),
                encoding="utf-8",
            )

            internal_path = root / "data/processed/evaluation/garhwali_bench/internal_text.jsonl"
            internal_path.parent.mkdir(parents=True, exist_ok=True)
            internal_path.write_text(
                json.dumps({"record_id": test_rows[0]["record_id"], "text": "Garhwali example"}) + "\n",
                encoding="utf-8",
            )
            internal_sha256 = hashlib.sha256(internal_path.read_bytes()).hexdigest()
            benchmark_manifest_path = root / "data/processed/evaluation/garhwali_bench/manifest.json"
            benchmark_manifest_path.write_text(
                json.dumps({
                    "records": {"text_evaluation": 1},
                    "internal_evaluation": {"text": {"sha256": internal_sha256}},
                    "baselines": {"character_bigram": {"model": "add-one-smoothed_character_bigram", "perplexity": 1.5}},
                }),
                encoding="utf-8",
            )

            report = build_report(root)

            decision = report["evaluation_decisions"]["text_recommended_test"]
            self.assertEqual(decision["status"], "historical_only")
            self.assertIn("aggregate", decision["reason"])
            self.assertEqual(decision["previously_scored_row_count"], 0)
            self.assertEqual(decision["aggregate_scored_row_count"], 1)
            self.assertEqual(len(decision["aggregate_scored_row_set_sha256"]), 64)

    def test_text_candidate_score_is_unresolved_when_aggregate_rows_do_not_match(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)

            internal_path = root / "data/processed/evaluation/garhwali_bench/internal_text.jsonl"
            internal_path.parent.mkdir(parents=True, exist_ok=True)
            internal_path.write_text(
                json.dumps({"record_id": "unrelated-row", "text": "different row"}) + "\n",
                encoding="utf-8",
            )
            internal_sha256 = hashlib.sha256(internal_path.read_bytes()).hexdigest()
            benchmark_manifest_path = root / "data/processed/evaluation/garhwali_bench/manifest.json"
            benchmark_manifest_path.write_text(
                json.dumps({
                    "records": {"text_evaluation": 1},
                    "internal_evaluation": {"text": {"sha256": internal_sha256}},
                    "baselines": {"character_bigram": {"model": "add-one-smoothed_character_bigram", "perplexity": 1.5}},
                }),
                encoding="utf-8",
            )

            decision = build_report(root)["evaluation_decisions"]["text_recommended_test"]

            self.assertEqual(decision["status"], "unresolved")
            self.assertEqual(decision["aggregate_scored_row_count"], 0)
            self.assertIn("could not be reconciled", decision["reason"])

    def test_known_previously_scored_test_splits_are_historical_only(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)

            decisions = build_report(root)["evaluation_decisions"]

            for name in ("flores_test", "instructions_test", "vaani_asr_test", "xorqa_test"):
                with self.subTest(evaluation=name):
                    self.assertEqual(decisions[name]["status"], "historical_only")

    def test_report_serialization_is_deterministic(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)

            first = render_json(build_report(root))
            second = render_json(build_report(root))

            self.assertEqual(first, second)

    def test_exact_text_without_source_hash_is_checked_across_splits(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            train_path = root / SPLIT_MANIFESTS["text_recommended"]["train"]
            test_path = root / SPLIT_MANIFESTS["text_recommended"]["test"]
            train_row = self._row("text:train:0", "train")
            test_row = self._row("text:test:0", "test")
            for row in (train_row, test_row):
                for field in ("text_sha256", "selected_transcript_sha256", "asr_target_sha256", "instruction_sha256"):
                    row.pop(field, None)
                row["text"] = "same Garhwali sentence"
            train_path.write_text(json.dumps(train_row) + "\n", encoding="utf-8")
            test_path.write_text(json.dumps(test_row) + "\n", encoding="utf-8")

            report = build_report(root)

            overlap = report["manifest_families"]["text_recommended"]["overlaps"]["derived_text_sha256"]
            self.assertEqual(overlap["cross_split_group_count"], 1)

    def test_audio_path_named_by_hash_matches_saved_prediction(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            test_row = self._row("asr:test:0", "test")
            prediction_path = root / "data/processed/evaluation/asr/path_prediction.jsonl"
            prediction_path.parent.mkdir(parents=True, exist_ok=True)
            prediction_path.write_text(
                json.dumps(
                    {"audio_filepath": f"/normalized/{test_row['audio_sha256']}.wav"}
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_report(root)

            prediction = next(
                item for item in report["predictions"] if item["path"].endswith("path_prediction.jsonl")
            )
            self.assertEqual(prediction["matched_split_counts"]["asr"]["test"], 1)

    def test_non_unique_instruction_hash_is_ambiguous_not_split_evidence(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            train_path = root / SPLIT_MANIFESTS["instructions_v0.2"]["train"]
            test_path = root / SPLIT_MANIFESTS["instructions_v0.2"]["test"]
            train_row = read_jsonl(train_path)[0]
            test_row = read_jsonl(test_path)[0]
            test_row["instruction_sha256"] = train_row["instruction_sha256"]
            test_path.write_text(json.dumps(test_row) + "\n", encoding="utf-8")
            prediction_path = root / "data/processed/evaluation/controlled_modeling/test_predictions.jsonl"
            prediction_path.parent.mkdir(parents=True, exist_ok=True)
            prediction_path.write_text(
                json.dumps({"instruction_sha256": train_row["instruction_sha256"]}) + "\n",
                encoding="utf-8",
            )

            report = build_report(root)

            prediction = report["predictions"][0]
            self.assertEqual(prediction["matched_split_counts"], {})
            self.assertEqual(prediction["ambiguous_prediction_row_count"], 1)
            self.assertEqual(prediction["unmatched_prediction_row_count"], 0)

    def test_unknown_speaker_placeholder_is_not_a_cross_split_speaker(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            for split in ("train", "test"):
                path = root / SPLIT_MANIFESTS["asr"][split]
                row = read_jsonl(path)[0]
                row["speaker_id"] = "NA"
                path.write_text(json.dumps(row) + "\n", encoding="utf-8")

            report = build_report(root)

            speaker_overlap = report["manifest_families"]["asr"]["overlaps"]["speaker_id"]
            self.assertEqual(speaker_overlap["cross_split_speaker_count"], 0)

    def test_meta_duplicate_flags_are_compared_with_computed_hashes(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            meta_path = root / SINGLE_MANIFESTS["meta_omnilingual"]["path"]
            rows = read_jsonl(meta_path)
            train_row = next(row for row in rows if row["split"] == "train")
            test_row = next(row for row in rows if row["split"] == "test")
            test_row["audio_sha256"] = train_row["audio_sha256"]
            train_row["cross_split_audio_overlap"] = False
            test_row["cross_split_audio_overlap"] = False
            meta_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

            report = build_report(root)

            check = report["manifest_families"]["meta_omnilingual"]["flag_consistency"]["cross_split_audio_overlap"]
            self.assertEqual(check["computed_true_rows"], 2)
            self.assertEqual(check["declared_true_rows"], 0)
            self.assertEqual(check["mismatch_count"], 2)

    def test_meta_whisper_compatible_views_and_adaptation_predictions_are_audited(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            family = "meta_omnilingual_whisper_compatible"
            compatible_paths = {
                "train": "data/processed/model_ready/splits/meta_omnilingual_asr/whisper_tiny_compatible/train.jsonl",
                "validation": "data/processed/model_ready/splits/meta_omnilingual_asr/whisper_tiny_compatible/validation.jsonl",
            }
            train_row = self._row(f"{family}:train:0", "train")
            validation_row = self._row(f"{family}:validation:0", "validation")
            for split, row in (("train", train_row), ("validation", validation_row)):
                path = root / compatible_paths[split]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(row) + "\n", encoding="utf-8")

            prediction_path = (
                root
                / "models/whisper-tiny-garhwali-meta-multiseed-17/evaluation_predictions.jsonl"
            )
            prediction_path.parent.mkdir(parents=True, exist_ok=True)
            prediction_path.write_text(
                json.dumps({"record_id": validation_row["record_id"], "hypothesis": "draft"})
                + "\n",
                encoding="utf-8",
            )
            train_manifest_path = root / compatible_paths["train"]
            validation_manifest_path = root / compatible_paths["validation"]
            (prediction_path.parent / "report.json").write_text(
                json.dumps(
                    {
                        "training_manifest": compatible_paths["train"],
                        "training_manifest_sha256": hashlib.sha256(
                            train_manifest_path.read_bytes()
                        ).hexdigest(),
                        "training_examples": 1,
                        "evaluation_manifest": compatible_paths["validation"],
                        "evaluation_manifest_sha256": hashlib.sha256(
                            validation_manifest_path.read_bytes()
                        ).hexdigest(),
                        "evaluation_records": 1,
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(root)

            compatible = report["manifest_families"][family]
            self.assertEqual(compatible["row_counts"], {"train": 1, "validation": 1})
            self.assertEqual(
                compatible["overlaps"]["audio_sha256"]["cross_split_group_count"], 0
            )
            self.assertEqual(
                compatible["overlaps"]["text_sha256"]["cross_split_group_count"], 0
            )
            self.assertEqual(
                compatible["overlaps"]["speaker_id"]["cross_split_speaker_count"],
                0,
            )
            prediction = next(
                item
                for item in report["predictions"]
                if item["path"].endswith("evaluation_predictions.jsonl")
            )
            self.assertEqual(
                prediction["matched_split_counts"][family]["validation"], 1
            )
            self.assertEqual(
                prediction["model_metadata"]["training_manifest_sha256"],
                hashlib.sha256(train_manifest_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                prediction["manifest_lineage_checks"]["training"]["status"],
                "verified_match",
            )
            self.assertEqual(
                prediction["manifest_lineage_checks"]["evaluation"]["status"],
                "verified_match",
            )
            decision = report["evaluation_decisions"][
                "meta_omnilingual_whisper_compatible_validation"
            ]
            self.assertEqual(decision["status"], "development_only")
            self.assertEqual(decision["previously_scored_row_count"], 1)

    def test_declared_manifest_hash_mismatch_is_reported(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            family = "meta_omnilingual_whisper_compatible"
            train_path = root / SPLIT_MANIFESTS[family]["train"]
            prediction_path = root / "models/whisper-tiny-garhwali-meta-mismatch/evaluation_predictions.jsonl"
            prediction_path.parent.mkdir(parents=True, exist_ok=True)
            prediction_path.write_text("{}\n", encoding="utf-8")
            (prediction_path.parent / "report.json").write_text(
                json.dumps(
                    {
                        "training_manifest": SPLIT_MANIFESTS[family]["train"],
                        "training_manifest_sha256": "0" * 64,
                        "training_examples": 2,
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(root)
            prediction = next(
                item
                for item in report["predictions"]
                if item["path"].endswith("evaluation_predictions.jsonl")
            )

            check = prediction["manifest_lineage_checks"]["training"]
            self.assertEqual(check["status"], "mismatch")
            self.assertFalse(check["hash_matches"])
            self.assertFalse(check["row_count_matches"])
            markdown = render_markdown(report)
            self.assertIn("## Model-declared manifest checks", markdown)
            self.assertIn("mismatch", markdown)

    def test_cross_family_train_to_test_audio_overlap_is_reported(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            asr_test = self._row("asr:test:0", "test")
            expanded_train_path = root / SPLIT_MANIFESTS["asr_expanded_human"]["train"]
            expanded_train = read_jsonl(expanded_train_path)[0]
            expanded_train["audio_sha256"] = asr_test["audio_sha256"]
            expanded_train_path.write_text(
                json.dumps(expanded_train) + "\n", encoding="utf-8"
            )

            report = build_report(root)

            groups = report["cross_role_overlaps"]["audio_sha256"]["groups"]
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0]["hash"], asr_test["audio_sha256"])
            self.assertEqual(
                {row["split"] for row in groups[0]["evaluation_rows"]}, {"test"}
            )
            self.assertEqual(
                {row["family"] for row in groups[0]["training_rows"]},
                {"asr_expanded_human"},
            )

    def test_meta_test_is_unresolved_and_decisions_hash_the_selected_rows(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            meta_path = root / SINGLE_MANIFESTS["meta_omnilingual"]["path"]
            rows = read_jsonl(meta_path)
            for row in rows:
                row["split_safe_for_evaluation"] = True
            meta_path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            report = build_report(root)

            decision = report["evaluation_decisions"]["meta_omnilingual_test"]
            self.assertEqual(decision["status"], "unresolved")
            self.assertEqual(decision["selected_row_count"], 1)
            self.assertEqual(decision["previously_scored_row_count"], 0)
            self.assertEqual(len(decision["row_set_sha256"]), 64)
            self.assertFalse(decision["eligible_for_heldout_claim"])
            self.assertIn("upstream", decision["reason"])

    def test_any_saved_test_prediction_makes_the_split_historical_only(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            meta_path = root / SINGLE_MANIFESTS["meta_omnilingual"]["path"]
            rows = read_jsonl(meta_path)
            test_row = next(row for row in rows if row["split"] == "test")
            prediction_path = (
                root / "data/processed/evaluation/asr/meta_test_predictions.jsonl"
            )
            prediction_path.parent.mkdir(parents=True, exist_ok=True)
            prediction = {
                "record_id": test_row["record_id"],
                "audio_sha256": test_row["audio_sha256"],
                "hypothesis": "saved output",
            }
            prediction_path.write_text(
                json.dumps(prediction) + "\n",
                encoding="utf-8",
            )

            report = build_report(root)

            decision = report["evaluation_decisions"]["meta_omnilingual_test"]
            self.assertEqual(decision["status"], "historical_only")
            self.assertEqual(decision["previously_scored_row_count"], 1)
            self.assertFalse(decision["eligible_for_heldout_claim"])

    def test_same_audio_conflicting_transcripts_are_reported_without_removing_rows(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_required_manifests(root)
            train_path = root / SPLIT_MANIFESTS["asr"]["train"]
            rows = read_jsonl(train_path)
            conflict = self._row("asr:conflict:0", "train")
            conflict["audio_sha256"] = rows[0]["audio_sha256"]
            rows.append(conflict)
            train_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

            report = build_report(root)

            groups = report["manifest_families"]["asr"]["overlaps"]["audio_transcript_conflicts"]["selected_transcript_sha256"]
            self.assertEqual(len(rows), 2)
            self.assertEqual(len(groups), 1)
            self.assertEqual(
                {row["row_id"] for row in groups[0]["rows"]},
                {"asr:train:0", "asr:conflict:0"},
            )


if __name__ == "__main__":
    unittest.main()
