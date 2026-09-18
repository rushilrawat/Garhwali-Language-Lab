#!/usr/bin/env python3
"""Generate independent Whisper hypotheses for a low-confidence SraVaani sample."""

import argparse
import json
import statistics
import time
from pathlib import Path


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def row_identity(row):
    return row.get("audio_sha256") or row["audio_path"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-id", default="openai/whisper-small")
    parser.add_argument("--revision", default="973afd24965f72e36ca33b3055d56a652f456b4d")
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    from asr_metrics import score
    from run_asr_baseline import read_audio

    rows = read_jsonl(args.data / "manifest.jsonl")
    processor = WhisperProcessor.from_pretrained(args.model, local_files_only=True)
    model = WhisperForConditionalGeneration.from_pretrained(
        args.model, local_files_only=True, torch_dtype=torch.float16,
    ).to("cuda").eval()
    args.output.mkdir(parents=True, exist_ok=True)
    predictions_path = args.output / "predictions.jsonl"
    results = read_jsonl(predictions_path) if predictions_path.exists() else []
    completed = {row_identity(row) for row in results}
    pending = [row for row in rows if row_identity(row) not in completed]
    started = time.monotonic()
    mode = "a" if results else "w"
    with torch.no_grad(), predictions_path.open(mode, encoding="utf-8") as output:
        for start in range(0, len(pending), args.batch_size):
            batch = pending[start:start + args.batch_size]
            audio = [read_audio(args.data / row["audio_path"]) for row in batch]
            features = processor(
                audio, sampling_rate=16000, return_tensors="pt", padding=True,
            ).input_features.to("cuda", dtype=torch.float16)
            generated = model.generate(
                features, language="hi", task="transcribe", max_length=128,
                do_sample=False,
            )
            hypotheses = processor.batch_decode(generated, skip_special_tokens=True)
            for row, hypothesis in zip(batch, hypotheses):
                hypothesis = hypothesis.strip()
                agreement = score(row["sravaani_transcript"], hypothesis)
                result = {
                    **row,
                    "whisper_transcript": hypothesis,
                    "agreement_wer": agreement["wer"],
                    "agreement_cer": agreement["cer"],
                    "human_reference_available": False,
                    "automatic_promotion": False,
                }
                results.append(result)
                output.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
            output.flush()
            print(f"processed={len(results)}/{len(rows)}", flush=True)
    report = {
        "run_id": f'garhwali-low-confidence-{args.model_id.replace("/", "--")}-agreement-v0.1',
        "records": len(results),
        "model_id": args.model_id,
        "revision": args.revision,
        "mean_agreement_wer": round(statistics.mean(row["agreement_wer"] for row in results), 8),
        "mean_agreement_cer": round(statistics.mean(row["agreement_cer"] for row in results), 8),
        "exact_agreement_records": sum(row["agreement_cer"] == 0 for row in results),
        "empty_whisper_outputs": sum(not row["whisper_transcript"] for row in results),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "policy": "agreement evidence only; no human ground truth; no automatic promotion",
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
