import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from audit_model_accuracy_lineage import (
    BENCHMARKS,
    SINGLE_MANIFESTS,
    SPLIT_MANIFESTS,
    build_report,
    hash_overlap,
    read_jsonl,
    render_json,
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
            }.issubset(SPLIT_MANIFESTS)
        )
        self.assertIn("meta_omnilingual", SINGLE_MANIFESTS)
        self.assertEqual(set(BENCHMARKS), {"flores", "xorqa", "crosssum"})

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
