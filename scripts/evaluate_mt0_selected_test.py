#!/usr/bin/env python3
"""One-time frozen-test evaluation for the validation-selected mT0 adapter."""

import argparse
import gc
import json
from pathlib import Path

import run_mt5_instruction_tuning as tuning


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    from peft import PeftModel

    rows = tuning.read_jsonl(args.data / "test.jsonl")
    tokenizer = tuning.load_tokenizer(args.model)
    systems = {}
    predictions = []
    for name, checkpoint in (("base", None), ("seed-43", args.checkpoint)):
        base = tuning.load_base_model("cpu", args.model)
        model = base if checkpoint is None else PeftModel.from_pretrained(
            base, checkpoint, local_files_only=True
        )
        model = model.to("cuda")
        metrics, hypotheses = tuning.evaluate_test_model(
            model, tokenizer, rows, 96, 72, 32, 4, "cuda"
        )
        diagnostics, details = tuning.generation_diagnostics(rows, hypotheses)
        systems[name] = metrics | {"diagnostics": diagnostics}
        predictions.extend({"system": name} | item for item in details)
        del model, base
        gc.collect()
    report = {
        "run_id": "garhwali-mt0-32768-selected-frozen-test-v0.6",
        "selection": "seed 43 selected by lowest validation cross-entropy",
        "test_records": len(rows),
        "test_sha256": tuning.dataset_digest(rows),
        "systems": systems,
        "test_opened_once": True,
        "further_selection_on_test_prohibited": True,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tuning.write_jsonl(args.output / "test_predictions.jsonl", predictions)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
