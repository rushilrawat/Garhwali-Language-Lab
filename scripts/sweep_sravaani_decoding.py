#!/usr/bin/env python3
"""Compare SraVaani RNNT and auxiliary CTC decoding on validation data."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from sweep_sravaani_garhwali import (
    extract_split,
    sha256_file,
    transcribe_split,
    write_json,
)
from train_sravaani_garhwali import (
    OFFICIAL_CHECKPOINT_BYTES,
    OFFICIAL_CHECKPOINT_URL,
    download_checkpoint,
    validate_checkpoint_file,
)


def decoding_plan() -> list[dict]:
    return [
        {"config_id": "rnnt-greedy-batch", "decoder": "rnnt", "strategy": "greedy_batch"},
        {"config_id": "rnnt-beam-2", "decoder": "rnnt", "strategy": "beam", "beam_size": 2},
        {"config_id": "rnnt-beam-4", "decoder": "rnnt", "strategy": "beam", "beam_size": 4},
        {"config_id": "rnnt-beam-8", "decoder": "rnnt", "strategy": "beam", "beam_size": 8},
        {"config_id": "rnnt-tsd-4", "decoder": "rnnt", "strategy": "tsd", "beam_size": 4},
        {"config_id": "ctc-greedy-batch", "decoder": "ctc", "strategy": "greedy_batch"},
    ]


def configure_decoding(model, variant: dict, rnnt_base, ctc_base) -> None:
    from omegaconf import OmegaConf, open_dict

    if variant["decoder"] == "rnnt":
        cfg = OmegaConf.create(OmegaConf.to_container(rnnt_base, resolve=True))
        with open_dict(cfg):
            cfg.strategy = variant["strategy"]
            if "beam_size" in variant:
                cfg.beam.beam_size = variant["beam_size"]
                cfg.beam.return_best_hypothesis = True
        model.change_decoding_strategy(cfg, decoder_type="rnnt", verbose=False)
        return
    cfg = OmegaConf.create(OmegaConf.to_container(ctc_base, resolve=True))
    with open_dict(cfg):
        cfg.strategy = variant["strategy"]
    model.change_decoding_strategy(cfg, decoder_type="ctc", verbose=False)


def run(data: Path, checkpoint: Path, output: Path) -> dict:
    import tempfile
    import torch
    from nemo.collections.asr.models import EncDecHybridRNNTCTCBPEModel

    data, checkpoint, output = Path(data), Path(checkpoint), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if not checkpoint.is_file():
        download_checkpoint(checkpoint, OFFICIAL_CHECKPOINT_URL, OFFICIAL_CHECKPOINT_BYTES)
    validate_checkpoint_file(checkpoint)
    if not torch.cuda.is_available():
        raise RuntimeError("Decoding sweep requires a CUDA-capable NVIDIA GPU")

    model = EncDecHybridRNNTCTCBPEModel.restore_from(str(checkpoint)).cuda().eval()
    rnnt_base = copy.deepcopy(model.cfg.decoding)
    ctc_base = copy.deepcopy(model.cfg.aux_ctc.decoding)
    results = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        validation = extract_split(data, "validation", root / "validation")
        test = extract_split(data, "test", root / "test")
        for variant in decoding_plan():
            row = dict(variant)
            try:
                configure_decoding(model, variant, rnnt_base, ctc_base)
                metrics, predictions = transcribe_split(
                    model, validation, root / "validation", batch_size=4
                )
                row.update({"status": "completed", "validation": metrics})
                write_json(output / f"{variant['config_id']}-validation.json", predictions)
            except Exception as error:
                row.update({
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "error": str(error),
                })
            results.append(row)
            write_json(output / "progress.json", results)

        completed = [row for row in results if row["status"] == "completed"]
        if not completed:
            raise RuntimeError("Every decoding configuration failed")
        selected = min(
            completed,
            key=lambda row: (row["validation"]["wer"], row["validation"]["cer"]),
        )
        configure_decoding(model, selected, rnnt_base, ctc_base)
        test_metrics, test_predictions = transcribe_split(
            model, test, root / "test", batch_size=4
        )
        write_json(output / "selected-test-predictions.json", test_predictions)

    report = {
        "run_id": "garhwali-sravaani-decoding-sweep-v0.1",
        "model_id": "ARTPARK-IISc/SraVaani-1.0",
        "checkpoint_sha256": sha256_file(checkpoint),
        "selection_metric": "validation_wer_then_cer",
        "selection_used_test_split": False,
        "configurations": results,
        "selected_configuration": selected,
        "selected_test": test_metrics,
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
