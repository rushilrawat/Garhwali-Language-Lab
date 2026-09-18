import json
import tempfile
import unittest
from pathlib import Path

import prepare_sravaani_expanded_finetune as m


def row(audio_hash, speaker_id=None, status="unidentified"):
    return {
        "audio_sha256": audio_hash,
        "speaker_id": speaker_id,
        "speaker_metadata": {"status": status},
        "duration_seconds": 1.0,
    }


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(value) + "\n" for value in rows))


class ExpandedHumanPackageTests(unittest.TestCase):
    def test_excludes_fixed_hashes_and_known_benchmark_speakers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            strict = root / "strict"
            experimental = root / "experimental"
            write(strict / "validation.jsonl", [row("v", "speaker-v", "identified")])
            write(strict / "test.jsonl", [row("t", "speaker-t", "identified")])
            write(experimental / "train.jsonl", [row("a"), row("v")])
            write(
                experimental / "validation.jsonl",
                [row("b", "speaker-v", "identified")],
            )
            write(experimental / "test.jsonl", [row("c")])

            splits, audit = m.build_rows(strict, experimental)

        self.assertEqual([value["audio_sha256"] for value in splits["train"]], ["a", "c"])
        self.assertEqual(audit["excluded_fixed_audio_hashes"], 2)
        self.assertEqual(audit["excluded_identified_speaker_rows"], 1)
        self.assertEqual(audit["fixed_audio_hash_overlap"], 0)
        self.assertEqual(audit["identified_speaker_overlap"], 0)

    def test_rejects_duplicate_candidate_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            strict = root / "strict"
            experimental = root / "experimental"
            write(strict / "validation.jsonl", [row("v")])
            write(strict / "test.jsonl", [row("t")])
            write(experimental / "train.jsonl", [row("a")])
            write(experimental / "validation.jsonl", [row("a")])
            write(experimental / "test.jsonl", [])
            with self.assertRaisesRegex(ValueError, "Duplicate experimental audio hash"):
                m.build_rows(strict, experimental)


if __name__ == "__main__":
    unittest.main()
