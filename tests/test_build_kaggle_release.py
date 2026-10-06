import csv
import json
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.build_kaggle_release import CORPUS_CONFIGS, build_corpus, build_speech


class BuildKaggleReleaseTests(unittest.TestCase):
    def test_corpus_export_preserves_configs_and_excludes_sentence_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "corpus"
            data = root / "data"
            for config in (*CORPUS_CONFIGS, "paharili_gbm"):
                folder = data / config
                folder.mkdir(parents=True)
                row = {"id": f"{config}-1", "rights_status": "licensed"}
                if config == "text":
                    row.update({"text": "गढ़वाळी वाक्य", "provenance": {"url": "https://example.org/a"}})
                if config == "paharili_gbm":
                    row.update({
                        "text": "sentence that must not ship",
                        "text_sha256": "abc123",
                        "source_record_ids": ["source-1"],
                        "license_id": "Apache-2.0",
                        "reuse_scope": "underlying text not assessed",
                    })
                (folder / "train-00000.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
            output = Path(temporary) / "out"
            manifest = build_corpus(root, output)

            self.assertEqual(set(manifest["configuration_counts"]), set(CORPUS_CONFIGS))
            self.assertEqual(manifest["configuration_view_rows"], len(CORPUS_CONFIGS))
            metrics = manifest["text_training_metrics"]
            self.assertEqual(metrics["rows"], 1)
            self.assertEqual(metrics["recommended_rows"], 0)
            self.assertEqual(metrics["whitespace_words"], 2)
            readme = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("0 of those rows are currently marked recommended", readme)
            with (output / "text.csv").open(encoding="utf-8", newline="") as stream:
                text_rows = list(csv.DictReader(stream))
            self.assertEqual(text_rows[0]["text"], "गढ़वाळी वाक्य")
            self.assertEqual(json.loads(text_rows[0]["provenance"]), {"url": "https://example.org/a"})
            with (output / "paharili_source_index.csv").open(encoding="utf-8", newline="") as stream:
                index_rows = list(csv.DictReader(stream))
            self.assertEqual(len(index_rows), 1)
            self.assertNotIn("text", index_rows[0])
            self.assertEqual(index_rows[0]["text_sha256"], "abc123")
            self.assertIn("underlying sentence rights", index_rows[0]["content_omitted_reason"].lower())

    def test_speech_export_omits_audio_bytes_and_keeps_transcript_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "speech"
            (root / "data/meta_omnilingual").mkdir(parents=True)
            (root / "data").mkdir(exist_ok=True)
            pq.write_table(pa.table({
                "record_id": ["vaani-1"],
                "audio_sha256": ["hash-1"],
                "transcript": ["गढ़वाळी"],
                "rights_status": ["licensed"],
                "audio": pa.array([{"bytes": b"secret-audio", "path": "a.wav"}], type=pa.struct([
                    pa.field("bytes", pa.binary()), pa.field("path", pa.string())
                ])),
            }), root / "data/train-00000.parquet")
            pq.write_table(pa.table({
                "record_id": ["meta-1"],
                "audio_sha256": ["hash-2"],
                "transcript": ["नमस्कार"],
                "split_safe_for_evaluation": [True],
                "audio": pa.array([{"bytes": b"secret-audio-2", "path": "b.wav"}], type=pa.struct([
                    pa.field("bytes", pa.binary()), pa.field("path", pa.string())
                ])),
            }), root / "data/meta_omnilingual/test-00000.parquet")
            output = Path(temporary) / "out"
            manifest = build_speech(root, output)

            self.assertEqual(manifest["metadata_rows"], 2)
            self.assertEqual(manifest["configuration_counts"], {"garhwali_speech": 1, "meta_omnilingual": 1})
            with (output / "speech_records.csv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual({row["record_id"] for row in rows}, {"vaani-1", "meta-1"})
            self.assertTrue(all(row["audio_included"] == "false" for row in rows))
            self.assertTrue(all(row["audio_dataset_url"].startswith("https://huggingface.co/") for row in rows))
            self.assertTrue(all("audio" not in row for row in rows))
            exported = (output / "speech_records.csv").read_text(encoding="utf-8")
            self.assertNotIn("secret-audio", exported)


if __name__ == "__main__":
    unittest.main()
