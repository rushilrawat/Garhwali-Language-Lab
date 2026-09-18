#!/usr/bin/env python3
"""Run a budget-capped SraVaani Garhwali adaptation sweep on one GPU."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import shutil
import tarfile
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from asr_metrics import score
from train_sravaani_garhwali import (
    OFFICIAL_CHECKPOINT_BYTES,
    OFFICIAL_CHECKPOINT_URL,
    download_checkpoint,
    validate_checkpoint_file,
)


HARD_TIMEOUT_HOURS = 6.0
HOURLY_COST_USD = 0.80
FINALIZATION_RESERVE_SECONDS = 15 * 60


@dataclass(frozen=True)
class Trial:
    trial_id: str
    scope: str
    learning_rate: float
    epochs: int
    batch_size: int
    accumulate_grad_batches: int
    seed: int


def build_trial_plan() -> list[Trial]:
    """Order broad comparisons first, then confirmation seeds and longer runs."""
    trials = [
        Trial("decoder-lr1e-5-e1-s17", "decoder_joint", 1e-5, 1, 4, 8, 17),
        Trial("decoder-lr3e-5-e1-s17", "decoder_joint", 3e-5, 1, 4, 8, 17),
        Trial("decoder-lr1e-4-e1-s17", "decoder_joint", 1e-4, 1, 4, 8, 17),
        Trial("full-lr1e-6-e1-s17", "full", 1e-6, 1, 1, 32, 17),
        Trial("full-lr3e-6-e1-s17", "full", 3e-6, 1, 1, 32, 17),
        Trial("full-lr1e-5-e1-s17", "full", 1e-5, 1, 1, 32, 17),
        Trial("decoder-lr1e-5-e2-s17", "decoder_joint", 1e-5, 2, 4, 8, 17),
        Trial("decoder-lr3e-5-e2-s17", "decoder_joint", 3e-5, 2, 4, 8, 17),
        Trial("full-lr1e-6-e2-s17", "full", 1e-6, 2, 1, 32, 17),
        Trial("full-lr3e-6-e2-s17", "full", 3e-6, 2, 1, 32, 17),
        Trial("decoder-lr1e-5-e2-s29", "decoder_joint", 1e-5, 2, 4, 8, 29),
        Trial("decoder-lr3e-5-e2-s29", "decoder_joint", 3e-5, 2, 4, 8, 29),
        Trial("full-lr1e-6-e2-s29", "full", 1e-6, 2, 1, 32, 29),
        Trial("full-lr3e-6-e2-s29", "full", 3e-6, 2, 1, 32, 29),
        Trial("decoder-lr1e-5-e4-s17", "decoder_joint", 1e-5, 4, 4, 8, 17),
        Trial("decoder-lr3e-5-e4-s17", "decoder_joint", 3e-5, 4, 4, 8, 17),
        Trial("full-lr1e-6-e3-s17", "full", 1e-6, 3, 1, 32, 17),
        Trial("full-lr3e-6-e3-s17", "full", 3e-6, 3, 1, 32, 17),
    ]
    for seed in (41, 53, 71, 89, 101, 113):
        trials.extend([
            Trial(f"decoder-lr1e-5-e2-s{seed}", "decoder_joint", 1e-5, 2, 4, 8, seed),
            Trial(f"decoder-lr3e-5-e2-s{seed}", "decoder_joint", 3e-5, 2, 4, 8, seed),
            Trial(f"decoder-lr5e-5-e2-s{seed}", "decoder_joint", 5e-5, 2, 4, 8, seed),
            Trial(f"full-lr1e-6-e2-s{seed}", "full", 1e-6, 2, 1, 32, seed),
            Trial(f"full-lr3e-6-e2-s{seed}", "full", 3e-6, 2, 1, 32, seed),
            Trial(f"full-lr5e-6-e2-s{seed}", "full", 5e-6, 2, 1, 32, seed),
        ])
    trials.extend([
        Trial("decoder-lr3e-6-e4-s17", "decoder_joint", 3e-6, 4, 4, 8, 17),
        Trial("decoder-lr5e-5-e4-s17", "decoder_joint", 5e-5, 4, 4, 8, 17),
        Trial("decoder-lr1e-5-e6-s17", "decoder_joint", 1e-5, 6, 4, 8, 17),
        Trial("decoder-lr3e-5-e6-s17", "decoder_joint", 3e-5, 6, 4, 8, 17),
        Trial("full-lr3e-7-e3-s17", "full", 3e-7, 3, 1, 32, 17),
        Trial("full-lr1e-6-e4-s17", "full", 1e-6, 4, 1, 32, 17),
        Trial("full-lr3e-6-e4-s17", "full", 3e-6, 4, 1, 32, 17),
    ])
    return trials


def build_refined_decoder_plan() -> list[Trial]:
    """Refine the decoder region after full-model adaptation failed validation."""
    trials = []
    for seed in (17, 29, 41, 53, 71):
        for learning_rate in (5e-6, 1e-5, 2e-5, 3e-5, 4e-5, 5e-5):
            label = f"{learning_rate:.0e}".replace("+", "")
            for epochs in (1, 2):
                trials.append(Trial(
                    f"decoder-lr{label}-e{epochs}-s{seed}",
                    "decoder_joint",
                    learning_rate,
                    epochs,
                    4,
                    8,
                    seed,
                ))
    trials.append(Trial(
        "decoder-lr3e-5-e4-s17",
        "decoder_joint",
        3e-5,
        4,
        4,
        8,
        17,
    ))
    return trials


def build_expanded_human_plan() -> list[Trial]:
    """Use the validation-selected decoder recipe on the expanded human set."""
    return [Trial(
        "expanded-human-decoder-lr5e-5-e2-s17",
        "decoder_joint",
        5e-5,
        2,
        4,
        8,
        17,
    )]


def conservative_prior_cost_usd(job_durations_seconds: list[float]) -> float:
    return round(sum(job_durations_seconds) / 3600 * HOURLY_COST_USD, 6)


def max_combined_cost_usd(prior_cost_usd: float) -> float:
    return round(prior_cost_usd + HARD_TIMEOUT_HOURS * HOURLY_COST_USD, 6)


def optimizer_steps(records: int, trial: Trial) -> int:
    microbatches = math.ceil(records / trial.batch_size)
    return math.ceil(microbatches / trial.accumulate_grad_batches) * trial.epochs


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(path: Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    names = [row["audio_filepath"] for row in rows]
    if len(names) != len(set(names)):
        raise ValueError(f"Duplicate audio paths in {path}")
    return rows


def extract_split(data: Path, split: str, target: Path) -> list[dict]:
    rows = read_manifest(data / split / "shard_0000.json")
    expected = {row["audio_filepath"] for row in rows}
    extracted = set()
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(data / split / "shard_0000.tar") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            if Path(member.name).name != member.name or member.name not in expected:
                raise ValueError(f"Unexpected {split} archive member: {member.name}")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"Unreadable {split} archive member: {member.name}")
            with source, (target / member.name).open("wb") as destination:
                shutil.copyfileobj(source, destination)
            extracted.add(member.name)
    if extracted != expected:
        raise ValueError(f"{split} archive and manifest differ")
    return rows


def summarize_scores(rows: list[dict]) -> dict:
    totals = {
        key: sum(row[key] for row in rows)
        for key in (
            "word_errors",
            "reference_words",
            "character_errors",
            "reference_characters",
        )
    }
    totals["wer"] = totals["word_errors"] / max(1, totals["reference_words"])
    totals["cer"] = totals["character_errors"] / max(
        1, totals["reference_characters"]
    )
    return totals


def hypothesis_text(hypothesis) -> str:
    if isinstance(hypothesis, str):
        return hypothesis.strip()
    text = getattr(hypothesis, "text", None)
    if isinstance(text, str):
        return text.strip()
    raise TypeError(f"Unsupported hypothesis: {type(hypothesis).__name__}")


def transcribe_split(model, rows: list[dict], audio_dir: Path, batch_size: int) -> tuple[dict, list[dict]]:
    import torch

    results = []
    model = model.cuda().eval()
    with torch.no_grad():
        for offset in range(0, len(rows), batch_size):
            batch = rows[offset : offset + batch_size]
            hypotheses = model.transcribe(
                audio=[str(audio_dir / row["audio_filepath"]) for row in batch],
                batch_size=batch_size,
                return_hypotheses=False,
                verbose=False,
            )
            if isinstance(hypotheses, tuple):
                hypotheses = hypotheses[0]
            for row, hypothesis in zip(batch, hypotheses, strict=True):
                text = hypothesis_text(hypothesis)
                results.append({
                    "audio_filepath": row["audio_filepath"],
                    "reference": row["text"],
                    "hypothesis": text,
                    **score(row["text"], text),
                })
    return summarize_scores(results), results


def configure_model(model, data: Path, trial: Trial, train_records: int):
    from omegaconf import OmegaConf, open_dict

    if trial.scope == "decoder_joint":
        model.encoder.freeze()
    elif trial.scope == "full":
        if hasattr(model.encoder, "unfreeze"):
            model.encoder.unfreeze()
        else:
            for parameter in model.encoder.parameters():
                parameter.requires_grad = True
    else:
        raise ValueError(f"Unknown scope: {trial.scope}")

    steps = optimizer_steps(train_records, trial)
    with open_dict(model.cfg):
        model.cfg.train_ds.manifest_filepath = str(data / "train/shard_0000.json")
        model.cfg.train_ds.tarred_audio_filepaths = str(data / "train/shard_0000.tar")
        model.cfg.train_ds.is_tarred = True
        model.cfg.train_ds.shuffle_n = 2048
        model.cfg.train_ds.batch_size = trial.batch_size
        model.cfg.train_ds.num_workers = 1
        model.cfg.train_ds.pin_memory = True
        model.cfg.validation_ds.manifest_filepath = str(
            data / "validation/shard_0000.json"
        )
        model.cfg.validation_ds.tarred_audio_filepaths = str(
            data / "validation/shard_0000.tar"
        )
        model.cfg.validation_ds.is_tarred = True
        model.cfg.validation_ds.batch_size = trial.batch_size
        model.cfg.validation_ds.num_workers = 1
        model.cfg.optim.name = "adamw"
        model.cfg.optim.lr = trial.learning_rate
        model.cfg.optim.weight_decay = 1e-3
        model.cfg.optim.sched = OmegaConf.create({
            "name": "CosineAnnealing",
            "warmup_steps": min(10, max(1, steps // 10)),
            "max_steps": steps,
            "min_lr": max(1e-8, trial.learning_rate / 100),
        })
    model.setup_training_data(model.cfg.train_ds)
    model.setup_validation_data(model.cfg.validation_ds)
    model.setup_optimization(model.cfg.optim)
    return steps


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run(
    data: Path,
    checkpoint: Path,
    output: Path,
    max_runtime_seconds: int,
    max_trials: int | None = None,
    plan_mode: str = "broad",
) -> dict:
    import lightning.pytorch as pl
    import torch
    from nemo.collections.asr.models import EncDecHybridRNNTCTCBPEModel

    data = Path(data)
    checkpoint = Path(checkpoint)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if not checkpoint.is_file():
        download_checkpoint(
            checkpoint,
            url=OFFICIAL_CHECKPOINT_URL,
            expected_bytes=OFFICIAL_CHECKPOINT_BYTES,
        )
    validate_checkpoint_file(checkpoint)
    if not torch.cuda.is_available():
        raise RuntimeError("SraVaani sweep requires a CUDA-capable NVIDIA GPU")

    started = time.monotonic()
    train_rows = read_manifest(data / "train/shard_0000.json")
    if plan_mode == "broad":
        trials = build_trial_plan()
    elif plan_mode == "refined_decoder":
        trials = build_refined_decoder_plan()
    elif plan_mode == "expanded_human":
        trials = build_expanded_human_plan()
    else:
        raise ValueError(f"Unknown plan mode: {plan_mode}")
    if max_trials is not None:
        if max_trials < 1:
            raise ValueError("max_trials must be positive")
        trials = trials[:max_trials]
    trial_results = []
    best = None
    best_checkpoint = output / "best-sravaani-garhwali.nemo"

    with tempfile.TemporaryDirectory() as directory:
        split_root = Path(directory)
        validation_rows = extract_split(data, "validation", split_root / "validation")
        test_rows = extract_split(data, "test", split_root / "test")

        base_model = EncDecHybridRNNTCTCBPEModel.restore_from(str(checkpoint))
        base_validation, _ = transcribe_split(
            base_model, validation_rows, split_root / "validation", batch_size=4
        )
        del base_model
        gc.collect()
        torch.cuda.empty_cache()
        write_json(output / "base-validation.json", base_validation)

        rolling_trial_seconds = 20 * 60
        for trial in trials:
            elapsed = time.monotonic() - started
            remaining = max_runtime_seconds - elapsed
            if remaining <= rolling_trial_seconds + FINALIZATION_RESERVE_SECONDS:
                break
            trial_started = time.monotonic()
            result = {**asdict(trial), "status": "started"}
            model = None
            trainer = None
            try:
                pl.seed_everything(trial.seed, workers=True)
                model = EncDecHybridRNNTCTCBPEModel.restore_from(str(checkpoint))
                steps = configure_model(model, data, trial, len(train_rows))
                trainable = sum(
                    parameter.numel()
                    for parameter in model.parameters()
                    if parameter.requires_grad
                )
                trainer = pl.Trainer(
                    devices=1,
                    accelerator="gpu",
                    precision="16-mixed",
                    max_epochs=trial.epochs,
                    accumulate_grad_batches=trial.accumulate_grad_batches,
                    gradient_clip_val=1.0,
                    val_check_interval=1.0,
                    log_every_n_steps=10,
                    logger=False,
                    enable_checkpointing=False,
                    enable_progress_bar=True,
                )
                trainer.fit(model)
                validation, predictions = transcribe_split(
                    model,
                    validation_rows,
                    split_root / "validation",
                    batch_size=4,
                )
                result.update({
                    "status": "completed",
                    "optimizer_steps_planned": steps,
                    "optimizer_steps_completed": trainer.global_step,
                    "trainable_parameters": trainable,
                    "validation": validation,
                })
                if best is None or validation["wer"] < best["validation"]["wer"]:
                    model.save_to(str(best_checkpoint))
                    write_json(
                        output / "best-validation-predictions.json",
                        predictions,
                    )
                    best = result.copy()
                    write_json(output / "best-trial.json", best)
            except Exception as error:
                result.update({
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "error": str(error),
                })
            finally:
                model = None
                trainer = None
                gc.collect()
                torch.cuda.empty_cache()
                result["elapsed_seconds"] = round(
                    time.monotonic() - trial_started, 3
                )
                trial_results.append(result)
                rolling_trial_seconds = max(
                    60,
                    sum(row["elapsed_seconds"] for row in trial_results)
                    / len(trial_results),
                )
                write_json(output / "trials.json", trial_results)

        test_result = None
        test_predictions = None
        if best and best["validation"]["wer"] < base_validation["wer"]:
            selected = EncDecHybridRNNTCTCBPEModel.restore_from(str(best_checkpoint))
            test_result, test_predictions = transcribe_split(
                selected, test_rows, split_root / "test", batch_size=4
            )
            del selected
            write_json(output / "held-out-test.json", test_result)
            write_json(output / "held-out-test-predictions.json", test_predictions)

    report = {
        "run_id": "garhwali-sravaani-budget-sweep-v0.2",
        "plan_mode": plan_mode,
        "hardware": torch.cuda.get_device_name(0),
        "hourly_cost_usd": HOURLY_COST_USD,
        "hard_timeout_hours": HARD_TIMEOUT_HOURS,
        "max_new_job_cost_usd": HARD_TIMEOUT_HOURS * HOURLY_COST_USD,
        "base_checkpoint_sha256": sha256_file(checkpoint),
        "base_validation": base_validation,
        "trials_planned": len(trials),
        "trials_attempted": len(trial_results),
        "trials_completed": sum(row["status"] == "completed" for row in trial_results),
        "trials_failed": sum(row["status"] == "failed" for row in trial_results),
        "best_trial": best,
        "best_checkpoint_sha256": (
            sha256_file(best_checkpoint) if best_checkpoint.is_file() else None
        ),
        "held_out_test_run": test_result is not None,
        "held_out_test": test_result,
        "selection_used_test_split": False,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-runtime-seconds", type=int, default=20_700)
    parser.add_argument("--max-trials", type=int)
    parser.add_argument(
        "--plan-mode",
        choices=("broad", "refined_decoder", "expanded_human"),
        default="broad",
    )
    args = parser.parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
