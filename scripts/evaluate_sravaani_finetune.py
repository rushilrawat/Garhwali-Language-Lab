#!/usr/bin/env python3
"""Evaluate the fine-tuned SraVaani checkpoint once on the frozen test split."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = (
    ROOT
    / "data/processed/evaluation/asr/sravaani_finetune/cloud_output"
    / "sravaani-garhwali-decoder-pilot-v0.1.nemo"
)
DATA = ROOT / "data/processed/model_ready/sravaani_finetune"
OUTPUT = ROOT / "data/processed/evaluation/asr/sravaani_finetune/held_out_evaluation"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hypothesis_text(hypothesis) -> str:
    if isinstance(hypothesis, str):
        return hypothesis.strip()
    text = getattr(hypothesis, "text", None)
    if isinstance(text, str):
        return text.strip()
    raise TypeError(f"Unsupported NeMo hypothesis type: {type(hypothesis).__name__}")


def summarize_scores(scores: list[dict]) -> dict:
    keys = ("word_errors", "reference_words", "character_errors", "reference_characters")
    totals = {key: sum(row[key] for row in scores) for key in keys}
    totals["wer"] = totals["word_errors"] / max(1, totals["reference_words"])
    totals["cer"] = totals["character_errors"] / max(1, totals["reference_characters"])
    return totals


def read_manifest(path: Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    names = [row["audio_filepath"] for row in rows]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate audio paths in held-out manifest")
    if any(Path(name).name != name for name in names):
        raise ValueError("Held-out manifest contains a non-basename audio path")
    return rows


def extract_audio(archive: Path, target: Path, expected_names: set[str]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    extracted = set()
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            if Path(member.name).name != member.name or member.name not in expected_names:
                raise ValueError(f"Unexpected held-out archive member: {member.name}")
            source = tar.extractfile(member)
            if source is None:
                raise ValueError(f"Unreadable held-out archive member: {member.name}")
            with source, (target / member.name).open("wb") as destination:
                shutil.copyfileobj(source, destination)
            extracted.add(member.name)
    if extracted != expected_names:
        raise ValueError("Held-out archive and manifest do not contain the same audio files")


def run(
    checkpoint: Path = CHECKPOINT,
    data: Path = DATA,
    output: Path = OUTPUT,
    batch_size: int = 4,
) -> dict:
    import torch
    from nemo.collections.asr.models import EncDecHybridRNNTCTCBPEModel
    from asr_metrics import score

    checkpoint = Path(checkpoint)
    data = Path(data)
    manifest = data / "test/shard_0000.json"
    archive = data / "test/shard_0000.tar"
    rows = read_manifest(manifest)
    if len(rows) != 112:
        raise ValueError(f"Frozen held-out split changed: expected 112 rows, found {len(rows)}")
    if not torch.cuda.is_available():
        raise RuntimeError("Held-out SraVaani evaluation requires CUDA")

    model = EncDecHybridRNNTCTCBPEModel.restore_from(str(checkpoint))
    model = model.cuda().eval()
    predictions = []
    scores = []
    started = time.monotonic()
    with tempfile.TemporaryDirectory() as directory:
        audio_dir = Path(directory)
        extract_audio(archive, audio_dir, {row["audio_filepath"] for row in rows})
        with torch.no_grad():
            for offset in range(0, len(rows), batch_size):
                batch = rows[offset : offset + batch_size]
                paths = [str(audio_dir / row["audio_filepath"]) for row in batch]
                hypotheses = model.transcribe(
                    audio=paths,
                    batch_size=batch_size,
                    return_hypotheses=False,
                    verbose=False,
                )
                if isinstance(hypotheses, tuple):
                    hypotheses = hypotheses[0]
                for row, hypothesis in zip(batch, hypotheses, strict=True):
                    transcript = hypothesis_text(hypothesis)
                    metrics = score(row["text"], transcript)
                    scores.append(metrics)
                    predictions.append({
                        "audio_filepath": row["audio_filepath"],
                        "reference": row["text"],
                        "hypothesis": transcript,
                        **metrics,
                    })
                progress = summarize_scores(scores)
                print(
                    f"{len(scores)}/{len(rows)} "
                    f"WER={progress['wer']:.6f} CER={progress['cer']:.6f}",
                    flush=True,
                )

    report = {
        "run_id": "garhwali-sravaani-decoder-pilot-v0.1-held-out-test",
        "model_id": "ARTPARK-IISc/SraVaani-1.0",
        "adaptation": "decoder_and_joint_only_encoder_frozen",
        "checkpoint": checkpoint.name,
        "checkpoint_sha256": sha256_file(checkpoint),
        "evaluation_manifest_sha256": sha256_file(manifest),
        "evaluation_archive_sha256": sha256_file(archive),
        "evaluation_records": len(rows),
        "batch_size": batch_size,
        "device": torch.cuda.get_device_name(0),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "test_used_for_training_or_selection": False,
        **summarize_scores(scores),
    }
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in predictions),
        encoding="utf-8",
    )
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(run(args.checkpoint, args.data, args.output, args.batch_size), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
