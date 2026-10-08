#!/usr/bin/env python3
"""Run a small, CPU-first masked-language-model experiment on the Hub view.

The source labels are automated and have not been reviewed by a fluent speaker.
The deterministic record-level development split is only for monitoring loss;
it is not an independent language-quality benchmark.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from text_training_utils import (
    deterministic_train_dev_split,
    is_recommended_training_row,
)


DATASET_ID = "rushilrawat/garhwali-corpus"
CONFIG = "screened_meta_gbm"
DEFAULT_MODEL = "ai4bharat/IndicBERTv2-MLM-only"
DEFAULT_OUTPUT = Path("outputs/garhwali-indicbert-mlm-smoke")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--revision", default="main", help="Hub commit SHA or branch")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--max-train-records", type=int, default=64,
        help="CPU-friendly smoke limit; use 0 to include every training row",
    )
    parser.add_argument(
        "--max-dev-records", type=int, default=32,
        help="Development-loss limit; use 0 to include every development row",
    )
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--local-model-files-only", action="store_true")
    args = parser.parse_args()
    if args.max_train_records < 0 or args.max_dev_records < 0:
        parser.error("record limits must be zero (all rows) or positive")
    if args.max_length < 8 or args.batch_size < 1 or args.epochs <= 0:
        parser.error("max length must be >= 8, batch size and epochs must be positive")
    return args


def main() -> None:
    args = parse_args()
    os.environ.setdefault("HF_HOME", ".cache/huggingface")

    try:
        from datasets import Dataset, load_dataset
        from transformers import (
            AutoModelForMaskedLM,
            AutoTokenizer,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
            set_seed,
        )
    except ImportError as error:
        raise SystemExit(
            "Training dependencies are missing. Run: "
            "python -m pip install -r requirements-training.txt"
        ) from error

    set_seed(args.seed)
    source = load_dataset(
        DATASET_ID,
        CONFIG,
        split="train",
        revision=args.revision,
    )
    eligible = [
        row for row in source
        if str(row.get("text") or "").strip()
        and is_recommended_training_row(row)
    ]
    if len(eligible) < 2:
        raise ValueError(
            "The selected Hub revision did not provide at least two non-empty, "
            "recommended_for_training rows. Check the dataset config and schema."
        )

    train_rows, dev_rows = deterministic_train_dev_split(eligible, seed=args.seed)
    if args.max_train_records:
        train_rows = train_rows[:args.max_train_records]
    if args.max_dev_records:
        dev_rows = dev_rows[:args.max_dev_records]
    if not train_rows or not dev_rows:
        raise ValueError("Both training and development views must contain rows")

    tokenizer = AutoTokenizer.from_pretrained(
        args.model, local_files_only=args.local_model_files_only
    )
    if tokenizer.mask_token_id is None:
        raise ValueError(f"Model {args.model!r} has no mask token for MLM training")
    model = AutoModelForMaskedLM.from_pretrained(
        args.model, local_files_only=args.local_model_files_only
    )

    train_dataset = Dataset.from_list(train_rows)
    dev_dataset = Dataset.from_list(dev_rows)

    def tokenize(batch: dict) -> dict:
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=args.max_length,
        )

    train_tokens = train_dataset.map(
        tokenize, batched=True, remove_columns=train_dataset.column_names
    )
    dev_tokens = dev_dataset.map(
        tokenize, batched=True, remove_columns=dev_dataset.column_names
    )
    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=True)
    training_args = TrainingArguments(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=5e-5,
        eval_strategy="epoch",
        save_strategy="no",
        logging_strategy="steps",
        logging_steps=1,
        report_to="none",
        use_cpu=True,
        seed=args.seed,
        data_seed=args.seed,
        dataloader_num_workers=0,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tokens,
        eval_dataset=dev_tokens,
        data_collator=collator,
        processing_class=tokenizer,
    )
    train_result = trainer.train()
    eval_metrics = trainer.evaluate()
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(args.output)

    report = {
        "experiment_type": "cpu_first_mlm_smoke",
        "dataset": DATASET_ID,
        "config": CONFIG,
        "source_split": "train",
        "dataset_revision_requested": args.revision,
        "model": args.model,
        "seed": args.seed,
        "training_rows": len(train_rows),
        "development_rows": len(dev_rows),
        "development_split": "deterministic record-level hash split from the same source train view",
        "training_result": train_result.metrics,
        "development_metrics": eval_metrics,
        "reference_review_status": "automatically screened; not native-speaker reviewed",
        "interpretation": (
            "A runnable training and loss-monitoring example only. Development loss is not an "
            "independent benchmark and does not establish Garhwali language quality."
        ),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    report_path = args.output / "run_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
