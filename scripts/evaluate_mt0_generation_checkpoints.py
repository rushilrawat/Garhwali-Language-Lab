#!/usr/bin/env python3
"""Evaluate saved mT0 LoRA checkpoints on the unchanged validation split."""

import argparse
import gc
import json
from pathlib import Path

import run_mt5_instruction_tuning as tuning


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--old-checkpoints", type=Path, required=True)
    parser.add_argument("--new-checkpoints", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    import torch
    from peft import PeftModel

    rows = tuning.select_rows(tuning.read_jsonl(args.data / "validation.jsonl"), 130, 101)
    tokenizer = tuning.load_tokenizer(args.model)
    systems = {"seed-17": args.old_checkpoints / "seed-17",
               "seed-29": args.old_checkpoints / "seed-29",
               "seed-43": args.new_checkpoints / "seed-43"}
    report = {
        "run_id": "garhwali-mt0-32768-generation-analysis-v0.6",
        "validation_records": len(rows),
        "selection_split": "validation",
        "fixed_test_opened": False,
        "systems": {},
    }
    predictions = []
    for name, checkpoint in systems.items():
        base = tuning.load_base_model("cpu", args.model)
        model = PeftModel.from_pretrained(base, checkpoint, local_files_only=True).to("cuda")
        metrics, hypotheses = tuning.evaluate_test_model(
            model, tokenizer, rows, 96, 72, 32, 4, "cuda"
        )
        diagnostics, details = tuning.generation_diagnostics(rows, hypotheses)
        report["systems"][name] = metrics | {"diagnostics": diagnostics}
        predictions.extend({"system": name} | item for item in details)
        del model, base
        gc.collect()
        torch.cuda.empty_cache()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tuning.write_jsonl(args.output / "validation_predictions.jsonl", predictions)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
