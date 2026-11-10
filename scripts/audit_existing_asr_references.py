#!/usr/bin/env python3
"""Audit existing strict ASR references and prioritize validation labels for review.

This script writes metadata only. It does not create, copy, relabel, or upload audio.
Model disagreement is a review signal, never an automatic label correction.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from garhwali_lab.hashing import sha256_file as sha256
from garhwali_lab.io import read_jsonl


ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data/processed/model_ready/splits/asr"
PREDICTIONS = ROOT / "models/whisper-tiny-garhwali-cpu-v0.1/evaluation_predictions.jsonl"
OUT = ROOT / "data/review/existing-asr-validation-labels-v0.1"


def build() -> None:
    splits = {split: read_jsonl(SPLITS / f"{split}.jsonl") for split in ("train", "validation", "test")}
    predictions = {row["audio_sha256"]: row for row in read_jsonl(PREDICTIONS)}
    all_rows = [row for rows in splits.values() for row in rows]
    hashes = [row["audio_sha256"] for row in all_rows]
    assert len(hashes) == len(set(hashes)), "audio is repeated across strict splits"
    speaker_sets = {split: {row["speaker_id"] for row in rows} for split, rows in splits.items()}
    assert all("NA" not in speakers for speakers in speaker_sets.values()), "unidentified speaker in strict split"
    assert not any(speaker_sets[a] & speaker_sets[b] for a, b in (("train", "validation"), ("train", "test"), ("validation", "test")))

    validation = splits["validation"]
    assert all(row["audio_sha256"] in predictions for row in validation), "missing validation prediction"
    flagged = [row for row in validation if "possibly_incomplete" in row.get("deep_cleanup_flags", [])]
    other = [row for row in validation if row not in flagged]

    def error_rates(rows: list[dict]) -> dict:
        scored = [predictions[row["audio_sha256"]] for row in rows]
        return {
            "rows": len(rows),
            "wer": sum(row["word_errors"] for row in scored) / sum(row["reference_words"] for row in scored),
            "cer": sum(row["character_errors"] for row in scored) / sum(row["reference_characters"] for row in scored),
        }

    other.sort(key=lambda row: (-predictions[row["audio_sha256"]]["cer"], row["audio_sha256"]))
    disagreement = []
    speakers = set()
    for row in other:
        if len(disagreement) == 25:
            break
        if row["speaker_id"] not in speakers:
            disagreement.append(row)
            speakers.add(row["speaker_id"])
    if len(disagreement) < 25:
        selected_hashes = {row["audio_sha256"] for row in disagreement}
        disagreement.extend(row for row in other if row["audio_sha256"] not in selected_hashes and len(disagreement) < 25)

    queue = []
    for priority, row in enumerate(flagged + disagreement, 1):
        prediction = predictions[row["audio_sha256"]]
        audio = ROOT / row["local_audio_path"]
        assert audio.is_file(), f"missing local audio: {audio}"
        queue.append({
            "priority": priority,
            "reason": "source_marked_possibly_incomplete" if row in flagged else "high_model_reference_disagreement",
            "split": "validation",
            "audio_sha256": row["audio_sha256"],
            "speaker_id": row["speaker_id"],
            "district": row["district"],
            "duration_seconds": row["duration_seconds"],
            "audio_path": str(audio),
            "current_reference": row["asr_target_clean"],
            "model_prediction_review_hint_only": prediction["prediction"],
            "model_cer_review_hint_only": round(prediction["cer"], 4),
            "review_status": "pending_listen",
            "corrected_reference": "",
            "reviewer_note": "",
        })

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "review.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=queue[0].keys())
        writer.writeheader()
        writer.writerows(queue)

    report = {
        "source": "existing strict VAANI ASR splits; no new examples or audio copies",
        "split_counts": {split: len(rows) for split, rows in splits.items()},
        "district_counts": {split: dict(Counter(row["district"] for row in rows)) for split, rows in splits.items()},
        "possibly_incomplete_counts": {split: sum("possibly_incomplete" in row.get("deep_cleanup_flags", []) for row in rows) for split, rows in splits.items()},
        "unique_audio_hashes": len(set(hashes)),
        "identified_speaker_cross_split_overlap": 0,
        "validation_predictions_matched": len(validation),
        "validation_model_error_by_reference_flag": {
            "all": error_rates(validation),
            "possibly_incomplete": error_rates(flagged),
            "without_possibly_incomplete": error_rates(other),
        },
        "review_queue_rows": len(queue),
        "review_queue_incomplete": len(flagged),
        "review_queue_model_disagreement": len(disagreement),
        "automatic_corrections": 0,
        "source_file_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in [*(SPLITS / f"{split}.jsonl" for split in splits), PREDICTIONS]},
    }
    (OUT / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(
        "# Existing ASR label review\n\n"
        "This is a review queue for **existing** validation audio. No audio was copied and no new training examples were created. "
        "The 55 source-marked possibly incomplete references come first; then 25 additional high model-disagreement rows, spread across speakers where possible. "
        "Listen to the audio before changing `review_status` or entering `corrected_reference`. A model prediction can be wrong even when the reference is right. "
        "Keep this validation material out of training. Preserve the original reference and record any correction separately so historical evaluations remain reproducible.\n",
        encoding="utf-8",
    )
    print(json.dumps({key: report[key] for key in ("split_counts", "district_counts", "possibly_incomplete_counts", "review_queue_rows")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()
