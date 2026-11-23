#!/usr/bin/env python3
"""Run one Hugging Face Jobs container entry point by name.

This replaces the 27 ``run_*_hf_job.sh`` scripts that used to live in this
folder. Each job runs the same steps its script ran, in the same order: an
optional ``pip install``, an optional pinned ``hf download``, then the task
command. A failing step stops the job, as ``set -euo pipefail`` did.

Launch it inside the job container the way the shell scripts were launched::

    hf jobs run ... bash -c 'python /workspace/scripts/hf_jobs/run_hf_job.py mt0_32768'

Use ``--list`` to see the job names and ``--dry-run`` to print the commands
without running them. Nothing here starts a Hugging Face job by itself; it only
runs inside one that was already launched.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass

WORKSPACE = "/workspace/scripts"

# Packages each family of jobs installs before running.
TRANSFORMERS = ["huggingface_hub[cli]", "transformers==4.56.2"]
PEFT = ["huggingface_hub[cli]", "transformers==4.56.2", "peft==0.17.1", "sentencepiece"]
NEMO = ["nemo_toolkit[asr,cu12]", "pytorch-lightning", "omegaconf"]
WEIGHT_FILES = ["*.json", "*.model", "*.bin", "*.safetensors"]


@dataclass(frozen=True)
class Download:
    repo: str
    revision: str
    local_dir: str
    include: tuple[str, ...] = ()

    def argv(self) -> list[str]:
        argv = ["hf", "download", self.repo, "--revision", self.revision]
        if self.include:
            argv += ["--include", *self.include]
        return argv + ["--local-dir", self.local_dir]


INDICBERT = "ai4bharat/IndicBERTv2-MLM-only"
INDICBERT_REV = "8598f13fe52443bc3fc054fcd665944560145b5c"
MT0 = "bigscience/mt0-small"
MT0_REV = "8116a34237e19160ec003147e758f065876d95f0"


def indicbert(include: bool = True) -> Download:
    return Download(INDICBERT, INDICBERT_REV, "/tmp/indicbertv2", tuple(WEIGHT_FILES) if include else ())


def mt0(include: bool = True) -> Download:
    return Download(MT0, MT0_REV, "/tmp/mt0-small", tuple(WEIGHT_FILES) if include else ())


@dataclass(frozen=True)
class Job:
    script: str
    args: tuple[str, ...]
    packages: tuple[str, ...] = ()
    download: Download | None = None
    pythonpath: bool = False
    legacy_script: str = ""
    summary: str = ""

    def steps(self) -> list[tuple[dict[str, str], list[str]]]:
        """Return the (extra environment, argv) pairs this job runs, in order."""
        steps: list[tuple[dict[str, str], list[str]]] = []
        if self.packages:
            steps.append(({}, ["python", "-m", "pip", "install", "--no-cache-dir", *self.packages]))
        if self.download:
            steps.append(({}, self.download.argv()))
        env = {"PYTHONPATH": WORKSPACE} if self.pythonpath else {}
        steps.append((env, ["python", f"{WORKSPACE}/{self.script}", *self.args]))
        return steps


def job(script: str, *args: str, **kwargs) -> Job:
    return Job(script=script, args=args, **kwargs)


def indicbert_lora(*args: str, **kwargs) -> Job:
    return job(
        "experiments/run_indicbert_lora_adaptation.py",
        *args,
        packages=tuple(PEFT),
        **kwargs,
    )


def mt0_tuning(run_id: str, steps: str, *extra: str, **kwargs) -> Job:
    return job(
        "run_mt5_instruction_tuning.py",
        "--data-dir", "/data", "--output-dir", "/output", "--checkpoint-dir", "/output/checkpoints",
        "--model-path", "/tmp/mt0-small", "--model-id", MT0, "--revision", MT0_REV,
        "--run-id", run_id, "--device", "cuda", "--steps", steps, *extra,
        packages=tuple(PEFT),
        **kwargs,
    )


def mt0_v04_plus(run_id: str, steps: str, seeds: str, **kwargs) -> Job:
    return mt0_tuning(
        run_id, steps,
        "--training-records", "2178", "--validation-records", "130", "--learning-rate", "0.0001",
        "--seeds", seeds, "--skip-test", "--evaluate-validation-generation",
        download=mt0(), **kwargs,
    )


def sravaani_sweep(*args: str, **kwargs) -> Job:
    return job(
        "experiments/sweep_sravaani_garhwali.py",
        "--data", "/data", "--checkpoint", "/tmp/SraVaani-nemo-checkpoint.nemo", "--output", "/output", *args,
        packages=tuple(NEMO),
        **kwargs,
    )


def whisper(name: str, revision: str, *extra: str, **kwargs) -> Job:
    local_dir = f"/tmp/{name.split('/')[1]}"
    return job(
        "experiments/transcribe_whisper_agreement.py",
        "--data", "/data", "--output", "/output", "--model", local_dir, *extra, "--batch-size", "16",
        packages=(*TRANSFORMERS, "soundfile"),
        download=Download(name, revision, local_dir, ("*.json", "*.txt", "*.model", "*.bin", "*.safetensors")),
        pythonpath=True,
        **kwargs,
    )


def ocr_validation(*extra: str, peft: bool = False, **kwargs) -> Job:
    packages = (*TRANSFORMERS, "peft==0.17.1", "sentencepiece") if peft else (*TRANSFORMERS, "sentencepiece")
    return job(
        "validate_ocr_corrections.py",
        "--input", "/data/priority.jsonl", "--output", "/output", "--model-path", "/tmp/indicbertv2", *extra,
        packages=packages,
        download=indicbert(),
        **kwargs,
    )


INDICBERT_COMMON = ("--output", "/output/report.json", "--checkpoint-dir", "/output/checkpoints",
                    "--model-path", "/tmp/indicbertv2", "--device", "cuda")

JOBS: dict[str, Job] = {
    "hf_package_validation": job(
        "validate_hf_package_cloud.py", "--package", "/package", "--output", "/output",
        legacy_script="run_hf_package_validation_job.sh",
        summary="Validate a built HF dataset package in the cloud.",
    ),
    "indicbert": indicbert_lora(
        "--train", "/data/train.jsonl", "--validation", "/data/validation.jsonl", *INDICBERT_COMMON,
        "--steps", "4096", "--training-records", "106804", "--evaluation-records", "128", "--seeds", "17,29,43",
        download=indicbert(include=False),
        legacy_script="run_indicbert_hf_job.sh",
        summary="IndicBERT LoRA adaptation, 4096 steps.",
    ),
    "indicbert_balanced": indicbert_lora(
        "--train", "/data/train.jsonl", "--validation", "/data/validation_general.jsonl",
        "--secondary-validation", "/data/validation_pdf.jsonl", *INDICBERT_COMMON,
        "--steps", "16384", "--training-records", "51966", "--evaluation-records", "256",
        "--secondary-evaluation-records", "615", "--learning-rate", "0.00005", "--seeds", "17,29,43",
        download=indicbert(),
        legacy_script="run_indicbert_balanced_hf_job.sh",
        summary="IndicBERT LoRA on the balanced general/PDF mix, 16384 steps.",
    ),
    "indicbert_pdf_domain": indicbert_lora(
        "--train", "/data/train.jsonl", "--validation", "/data/validation.jsonl", *INDICBERT_COMMON,
        "--steps", "8192", "--training-records", "25983", "--evaluation-records", "615",
        "--learning-rate", "0.0001", "--seeds", "17,29,43",
        download=indicbert(),
        legacy_script="run_indicbert_pdf_domain_hf_job.sh",
        summary="IndicBERT LoRA on PDF-domain text, 8192 steps.",
    ),
    "indicbert_pdf_domain_extended": indicbert_lora(
        "--train", "/data/train.jsonl", "--validation", "/data/validation.jsonl", *INDICBERT_COMMON,
        "--steps", "32768", "--training-records", "25983", "--evaluation-records", "615",
        "--learning-rate", "0.00005", "--seeds", "17,29,43",
        download=indicbert(),
        legacy_script="run_indicbert_pdf_domain_extended_hf_job.sh",
        summary="IndicBERT LoRA on PDF-domain text, 32768 steps.",
    ),
    "mt0": mt0_tuning(
        "garhwali-mt0-instruction-lora-cloud-v0.3", "2048",
        "--training-records", "2046", "--validation-records", "130", "--seeds", "17,29,43", "--skip-test",
        download=mt0(include=False),
        legacy_script="run_mt0_hf_job.sh",
        summary="mT0-small instruction LoRA v0.3, 2048 steps.",
    ),
    "mt0_extended": mt0_v04_plus(
        "garhwali-mt0-instruction-lora-extended-v0.4", "8192", "17,29,43",
        legacy_script="run_mt0_extended_hf_job.sh",
        summary="mT0-small instruction LoRA v0.4, 8192 steps.",
    ),
    "mt0_16384": mt0_v04_plus(
        "garhwali-mt0-instruction-lora-16384-v0.5", "16384", "17,29,43",
        legacy_script="run_mt0_16384_hf_job.sh",
        summary="mT0-small instruction LoRA v0.5, 16384 steps.",
    ),
    "mt0_32768": mt0_v04_plus(
        "garhwali-mt0-instruction-lora-32768-v0.6", "32768", "17,29,43",
        legacy_script="run_mt0_32768_hf_job.sh",
        summary="mT0-small instruction LoRA v0.6, 32768 steps.",
    ),
    "mt0_32768_seed43": mt0_v04_plus(
        "garhwali-mt0-instruction-lora-32768-seed43-v0.6", "32768", "43",
        legacy_script="run_mt0_32768_seed43_hf_job.sh",
        summary="mT0-small instruction LoRA v0.6, 32768 steps, seed 43 only.",
    ),
    "mt0_generation_analysis": job(
        "experiments/evaluate_mt0_generation_checkpoints.py",
        "--data", "/data", "--model", "/tmp/mt0-small",
        "--old-checkpoints", "/checkpoints-old", "--new-checkpoints", "/checkpoints-new", "--output", "/output",
        packages=tuple(PEFT), download=mt0(), pythonpath=True,
        legacy_script="run_mt0_generation_analysis_hf_job.sh",
        summary="Compare generations from old and new mT0 checkpoints.",
    ),
    "mt0_selected_test": job(
        "experiments/evaluate_mt0_selected_test.py",
        "--data", "/data", "--model", "/tmp/mt0-small", "--checkpoint", "/checkpoint", "--output", "/output",
        packages=tuple(PEFT), download=mt0(), pythonpath=True,
        legacy_script="run_mt0_selected_test_hf_job.sh",
        summary="Evaluate the selected mT0 checkpoint on the test split.",
    ),
    "ocr_validation": ocr_validation(
        "--device", "cuda",
        legacy_script="run_ocr_validation_hf_job.sh",
        summary="Score OCR corrections with IndicBERT.",
    ),
    "ocr_validation_multiseed": ocr_validation(
        "--device", "cuda", "--seeds", "17,29,43",
        legacy_script="run_ocr_validation_multiseed_hf_job.sh",
        summary="Score OCR corrections with IndicBERT over three seeds.",
    ),
    "pdf_adapter_ocr_validation": ocr_validation(
        "--adapter-path", "/adapter", "--device", "cuda", "--seeds", "17,29,43", "--ocr-only",
        peft=True,
        legacy_script="run_pdf_adapter_ocr_validation_hf_job.sh",
        summary="Score OCR corrections with the PDF-domain IndicBERT adapter.",
    ),
    "semantic_duplicate": job(
        "audit_semantic_duplicates.py",
        "--input", "/data", "--output", "/output", "--threshold", "0.92", "--neighbors", "12",
        "--limit", "200000", "--batch-size", "128",
        packages=("sentence-transformers==5.1.1", "faiss-cpu==1.12.0", "huggingface_hub[cli]"),
        legacy_script="run_semantic_duplicate_hf_job.sh",
        summary="Find semantic near-duplicates in the text corpus.",
    ),
    "semantic_refinement": job(
        "refine_semantic_duplicates.py",
        "--input", "/data/candidates.jsonl", "--output", "/output", "--batch-size", "128",
        packages=("sentence-transformers==5.1.1", "transformers==4.56.2"),
        legacy_script="run_semantic_refinement_hf_job.sh",
        summary="Re-score semantic duplicate candidates.",
    ),
    "sravaani": job(
        "experiments/train_sravaani_garhwali.py",
        "--package-report", "/data/report.json", "--data", "/data",
        "--checkpoint", "/tmp/SraVaani-nemo-checkpoint.nemo", "--download-checkpoint",
        "--output", "/output/sravaani-garhwali-decoder-pilot-v0.1.nemo",
        "--experiments", "/output/experiments", "--plan-output", "/output/plan.json", "--execute",
        packages=tuple(NEMO),
        legacy_script="run_sravaani_hf_job.sh",
        summary="SraVaani Garhwali decoder pilot training.",
    ),
    "sravaani_evaluation": job(
        "experiments/evaluate_sravaani_finetune.py",
        "--checkpoint", "/output/sravaani-garhwali-decoder-pilot-v0.1.nemo", "--data", "/data",
        "--output", "/output/held_out_evaluation", "--batch-size", "4",
        packages=tuple(NEMO),
        legacy_script="run_sravaani_hf_evaluation.sh",
        summary="Held-out evaluation of the SraVaani pilot checkpoint.",
    ),
    "sravaani_decoding_sweep": job(
        "experiments/sweep_sravaani_decoding.py",
        "--data", "/data", "--checkpoint", "/tmp/SraVaani-nemo-checkpoint.nemo", "--output", "/output",
        packages=tuple(NEMO),
        legacy_script="run_sravaani_hf_decoding_sweep.sh",
        summary="SraVaani decoding parameter sweep.",
    ),
    "sravaani_sweep": sravaani_sweep(
        "--max-runtime-seconds", "20700",
        legacy_script="run_sravaani_hf_sweep.sh",
        summary="SraVaani fine-tuning sweep, 20700 s budget.",
    ),
    "sravaani_six_config_sweep": sravaani_sweep(
        "--max-runtime-seconds", "4500", "--max-trials", "6",
        legacy_script="run_sravaani_hf_six_config_sweep.sh",
        summary="SraVaani sweep capped at six trials.",
    ),
    "sravaani_refined_61": sravaani_sweep(
        "--max-runtime-seconds", "17100", "--plan-mode", "refined_decoder",
        legacy_script="run_sravaani_hf_refined_61.sh",
        summary="SraVaani refined decoder sweep.",
    ),
    "sravaani_expanded": sravaani_sweep(
        "--plan-mode", "expanded_human", "--max-runtime-seconds", "4500",
        legacy_script="run_sravaani_expanded_hf_job.sh",
        summary="SraVaani sweep on the expanded human set.",
    ),
    "text_noise_audit": job(
        "propose_text_cleanup.py",
        "--input", "/data/text.jsonl", "--output-dir", "/output", "--model-records", "28755",
        "--device", "cuda", "--model-path", "/tmp/indicbertv2",
        packages=(*TRANSFORMERS, "sentencepiece"), download=indicbert(),
        legacy_script="run_text_noise_audit_hf_job.sh",
        summary="Propose text cleanups scored with IndicBERT.",
    ),
    "whisper_agreement": whisper(
        "openai/whisper-small", "973afd24965f72e36ca33b3055d56a652f456b4d",
        legacy_script="run_whisper_agreement_hf_job.sh",
        summary="Whisper-small transcription agreement.",
    ),
    "whisper_turbo_agreement": whisper(
        "openai/whisper-large-v3-turbo", "41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
        "--model-id", "openai/whisper-large-v3-turbo", "--revision", "41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
        legacy_script="run_whisper_turbo_agreement_hf_job.sh",
        summary="Whisper-large-v3-turbo transcription agreement.",
    ),
}

LEGACY_NAMES = {spec.legacy_script: name for name, spec in JOBS.items()}


def resolve(name: str) -> str:
    """Accept a job name or the old ``run_*.sh`` file name."""
    if name in JOBS:
        return name
    base = os.path.basename(name)
    if base in LEGACY_NAMES:
        return LEGACY_NAMES[base]
    raise SystemExit(f"unknown job {name!r}; run with --list to see the job names")


def render(env: dict[str, str], argv: list[str]) -> str:
    prefix = "".join(f"{key}={shlex.quote(value)} " for key, value in env.items())
    return prefix + shlex.join(argv)


def run_job(name: str, dry_run: bool = False, runner=subprocess.run, out=None) -> int:
    out = out or sys.stdout
    for env, argv in JOBS[resolve(name)].steps():
        print(f"+ {render(env, argv)}", file=out, flush=True)
        if dry_run:
            continue
        result = runner(argv, env={**os.environ, **env} if env else None, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("job", nargs="?", help="job name (or the old run_*.sh file name)")
    parser.add_argument("--list", action="store_true", help="list the jobs and exit")
    parser.add_argument("--dry-run", action="store_true", help="print the commands without running them")
    args = parser.parse_args(argv)
    if args.list:
        width = max(map(len, JOBS))
        for name, spec in sorted(JOBS.items()):
            print(f"{name:<{width}}  {spec.summary}")
        return 0
    if not args.job:
        parser.error("a job name is required (or --list)")
    return run_job(args.job, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
