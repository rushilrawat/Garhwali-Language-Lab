"""Direct tests for refresh steps that previously had little coverage."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import build_all_data_view
import dedup_report
import verify_ingestion


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class BuildAllDataViewTests(unittest.TestCase):
    def test_marks_every_row_and_flags_experimental_or_restricted_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data/processed/text/canonical.jsonl"
            output = root / "data/processed/text/all_garhwali.jsonl"
            write_jsonl(source, [
                {"text": "अ", "provenance": [{"layer": "corpus"}]},
                {"text": "ब", "provenance": [{"layer": "corpus"}, {"layer": "experimental"}]},
                {"text": "क", "provenance": [{"layer": "restricted"}]},
            ])
            source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            report = build_all_data_view.build_view(source, output, root)
            rows = read_jsonl(output)
            self.assertEqual(report["records"], 3)
            self.assertEqual(report["output"], "data/processed/text/all_garhwali.jsonl")
            self.assertTrue(all(row["candidate_use"] == "all_data_experimental" for row in rows))
            self.assertEqual(
                [row["includes_experimental_or_restricted"] for row in rows], [False, True, True]
            )
            saved = json.loads((output.parent / "all_garhwali_report.json").read_text(encoding="utf-8"))
            self.assertEqual(saved, report)


class DedupReportTests(unittest.TestCase):
    def test_counts_duplicates_within_and_across_layers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_jsonl(root / "corpus/a.jsonl", [
                {"record_id": "a:1", "source_id": "a", "text_normalized": "गौं"},
                {"record_id": "a:2", "source_id": "a", "text_normalized": "पाणी"},
            ])
            write_jsonl(root / "experimental/b.jsonl", [
                {"record_id": "b:1", "source_id": "b", "text_normalized": "गौं"},
                {"record_id": "b:2", "source_id": "b", "text_normalized": "गौं"},
            ])
            layers = {"corpus": root / "corpus", "experimental": root / "experimental"}
            report = dedup_report.build_report(layers, root)
        self.assertEqual(report["total_records"], 4)
        self.assertEqual(report["unique_normalized_texts"], 2)
        self.assertEqual(report["duplicate_rows"], 2)
        self.assertEqual(report["pairwise_unique_text_overlap"], {"corpus <> experimental": 1})
        self.assertEqual(report["duplicate_group_count"], 1)
        largest = report["largest_duplicate_groups"][0]
        self.assertEqual(largest["text_sha256"], hashlib.sha256("गौं".encode()).hexdigest())
        self.assertEqual([item["record_id"] for item in largest["records"]], ["a:1", "b:1", "b:2"])


class VerifyIngestionTests(unittest.TestCase):
    def _fixture(self, root):
        raw = root / "sources/online/demo/raw.txt"
        raw.parent.mkdir(parents=True)
        raw.write_bytes(b"snapshot")
        (raw.parent / "raw.txt.metadata.json").write_text(json.dumps({
            "raw_path": "sources/online/demo/raw.txt",
            "sha256": hashlib.sha256(b"snapshot").hexdigest(),
        }), encoding="utf-8")
        base = {"attribution": "x", "license_url": "https://example.org/license"}
        write_jsonl(root / "corpus/c.jsonl", [{**base, "record_id": "c:1"}])
        write_jsonl(root / "restricted/uou_cgl_pages.jsonl", [
            {**base, "record_id": f"uou:{index}", "text_normalized": "गढ़वाली"} for index in range(436)
        ])
        write_jsonl(root / "experimental/madlad400_gbm_clean.jsonl", [
            {
                **base, "record_id": f"madlad:{index}", "corpus_layer": "experimental",
                "experimental_training_eligible": True,
                "quality_flags": ["component_rights_review_required"],
                "quality_metrics": {"devanagari_share_of_nonspace": 0.9},
            }
            for index in range(18)
        ])

    def test_accepts_consistent_layers_and_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            report = verify_ingestion.verify(root)
        self.assertEqual(report["snapshots_verified"], 1)
        self.assertEqual(report["layer_counts"]["restricted"], 436)
        self.assertEqual(report["total_records"], 1 + 436 + 18)
        self.assertEqual(report["uou_devanagari_ratio"], 1.0)

    def test_rejects_checksum_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            (root / "sources/online/demo/raw.txt").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "snapshot checksum mismatch"):
                verify_ingestion.verify(root)

    def test_rejects_ids_duplicated_across_layers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            write_jsonl(root / "benchmarks/b.jsonl", [
                {"record_id": "c:1", "attribution": "x", "license_url": "https://example.org/license"}
            ])
            with self.assertRaisesRegex(ValueError, "duplicate ID across layers"):
                verify_ingestion.verify(root)

    def test_rejects_unauthorized_training_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            write_jsonl(root / "corpus/c.jsonl", [{
                "record_id": "c:1", "attribution": "x", "license_url": "https://example.org/license",
                "training_eligible": True,
            }])
            with self.assertRaisesRegex(ValueError, "corpus"):
                verify_ingestion.verify(root)


if __name__ == "__main__":
    unittest.main()
