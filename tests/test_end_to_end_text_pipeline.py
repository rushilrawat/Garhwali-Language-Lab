"""End-to-end check of the core text and speech preparation chain.

Copies the pipeline scripts into a temporary repository root, writes a tiny
fixture corpus, and runs the same steps the refresh pipeline runs, from
``prepare_text_corpus`` through ``build_dataset_splits``. It then checks the
invariants every release depends on, that two runs produce byte-identical
outputs, and that split membership matches the stored expectation.

Regenerate the expectation after an intentional change with:

    GARHWALI_UPDATE_E2E_EXPECTED=1 python -m unittest tests.test_end_to_end_text_pipeline
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from garhwali_lab.text import leakage_key

REPO = Path(__file__).resolve().parents[1]
EXPECTED = Path(__file__).with_name("fixtures") / "e2e_text_pipeline_expected.json"
STEPS = (
    "prepare_text_corpus.py",
    "build_all_data_view.py",
    "clean_text_corpus.py",
    "deep_cleanup.py",
    "tag_language_quality.py",
    "segment_text_corpus.py",
    "build_dataset_splits.py",
)
SENTENCES = (
    "मेरु गौं पहाड़ मा च।",
    "आज बरखा होणी च।",
    "तुम कख जाणा छन?",
    "हमरु घर नदी का किनारा च।",
    "बच्चा स्कूल जाणा छन।",
    "काम पूरु ह्वेगे।",
    "कम पाणी च आज।",
    "गढ़वाली हमारि भाषा च।",
    "ब्वारि खाणु बणाणी च।",
    "मेरु गौं पहाड़ मा च।",  # exact duplicate of the first sentence
    "चखुल डाळ मा बैठ्यूं च।",
    "सुबेर घाम ऐगे।",
)


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_fixture(root):
    _write_jsonl(root / "corpus/fixture.jsonl", [
        {
            "record_id": f"fixture:{index}", "source_id": "fixture",
            "text": text, "text_normalized": text, "iso_639_3": "gbm", "language": "Garhwali",
            "license_id": "CC-BY-4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "attribution": "test fixture", "rights_status": "licensed", "corpus_layer": "corpus",
            "training_eligible": False, "genre": "conversation",
        }
        for index, text in enumerate(SENTENCES)
    ])
    _write_jsonl(root / "data/processed/model_ready/transcripts/supervised.jsonl", [
        {
            "record_id": f"audio:{index}", "audio_sha256": f"{index:064x}", "asr_target": text,
            "speaker_id": f"spk{index % 3}", "split": ("train", "validation", "test")[index % 3],
            "district": "Tehri", "gender": "female", "source": "fixture", "license": "CC-BY-4.0",
            "language": "Garhwali", "duration_seconds": 2.5,
        }
        for index, text in enumerate(SENTENCES[:6])
    ])
    _write_jsonl(root / "data/processed/model_ready/audio/untranscribed_all.jsonl", [])


def _run_pipeline(root):
    shutil.copytree(
        REPO / "scripts", root / "scripts",
        ignore=shutil.ignore_patterns("__pycache__", "experiments", "archive", "hf_jobs"),
    )
    _write_fixture(root)
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": "scripts",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
    }
    for step in STEPS:
        result = subprocess.run(
            [sys.executable, f"scripts/{step}"], cwd=root, env=environment,
            capture_output=True, text=True, check=False,
        )
        if result.returncode:
            raise AssertionError(f"{step} failed:\n{result.stderr[-3000:]}")


def _output_digests(root):
    data = root / "data/processed"
    return {
        path.relative_to(data).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(data.rglob("*"))
        if path.is_file() and path.suffix in {".jsonl", ".json"}
    }


def _split_membership(root):
    splits = root / "data/processed/model_ready/splits"
    return {
        "text": {
            split: sorted(row["text"] for row in _read_jsonl(splits / "text" / f"{split}.jsonl"))
            for split in ("train", "validation", "test")
        },
        "asr_experimental": {
            split: sorted(row["record_id"] for row in _read_jsonl(splits / "asr_experimental" / f"{split}.jsonl"))
            for split in ("train", "validation", "test")
        },
    }


class EndToEndTextPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._first = tempfile.TemporaryDirectory()
        cls._second = tempfile.TemporaryDirectory()
        cls.root = Path(cls._first.name)
        cls.rerun_root = Path(cls._second.name)
        _run_pipeline(cls.root)
        _run_pipeline(cls.rerun_root)

    @classmethod
    def tearDownClass(cls):
        cls._first.cleanup()
        cls._second.cleanup()

    def test_exact_duplicates_collapse_but_vowel_sign_variants_survive(self):
        report = json.loads((self.root / "data/processed/text/report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["source_records"], 12)
        self.assertEqual(report["unique_texts"], 11)
        self.assertEqual(report["duplicate_rows"], 1)
        segments = {row["text"] for row in _read_jsonl(
            self.root / "data/processed/model_ready/segments/all_segments.jsonl"
        )}
        self.assertIn("काम पूरु ह्वेगे।", segments)
        self.assertIn("कम पाणी च आज।", segments)

    def test_every_segment_lands_in_exactly_one_text_split(self):
        membership = _split_membership(self.root)["text"]
        placed = [text for texts in membership.values() for text in texts]
        segments = [row["text"] for row in _read_jsonl(
            self.root / "data/processed/model_ready/segments/all_segments.jsonl"
        )]
        self.assertEqual(sorted(placed), sorted(segments))
        self.assertEqual(len(placed), len(set(placed)))

    def test_leakage_keys_and_speakers_do_not_cross_splits(self):
        splits = self.root / "data/processed/model_ready/splits"
        key_splits = {}
        for split in ("train", "validation", "test"):
            for row in _read_jsonl(splits / "text" / f"{split}.jsonl"):
                key_splits.setdefault(leakage_key(row["text"]), set()).add(split)
        self.assertTrue(all(len(found) == 1 for found in key_splits.values()))
        speaker_splits = {}
        for split in ("train", "validation", "test"):
            for row in _read_jsonl(splits / "asr_experimental" / f"{split}.jsonl"):
                speaker_splits.setdefault(row["speaker_id"], set()).add(split)
        self.assertEqual(len(speaker_splits), 3)
        self.assertTrue(all(len(found) == 1 for found in speaker_splits.values()))

    def test_two_runs_produce_byte_identical_outputs(self):
        first, second = _output_digests(self.root), _output_digests(self.rerun_root)
        self.assertGreater(len(first), 20)
        self.assertEqual(first, second)

    def test_split_membership_matches_stored_expectation(self):
        actual = _split_membership(self.root)
        if os.environ.get("GARHWALI_UPDATE_E2E_EXPECTED") == "1":
            EXPECTED.parent.mkdir(parents=True, exist_ok=True)
            EXPECTED.write_text(json.dumps(actual, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assertEqual(actual, json.loads(EXPECTED.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
