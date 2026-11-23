# Hugging Face Jobs runner

`run_hf_job.py` is the one entry point for the cloud jobs this project has run
on Hugging Face Jobs. It replaces the 27 `run_*_hf_job.sh` scripts that used to
sit here. Each job runs the same steps its script ran, in the same order: the
`pip install`, the pinned `hf download` where there was one, and the task
command. A failing step stops the job, as `set -euo pipefail` did.

Inside the job container:

```bash
python /workspace/scripts/hf_jobs/run_hf_job.py mt0_32768
```

Locally, to see what a job would run without running it:

```bash
python scripts/hf_jobs/run_hf_job.py --list
python scripts/hf_jobs/run_hf_job.py mt0_32768 --dry-run
```

The old script file names still work as the job argument, so a launch command
copied from a dated research report, such as `run_sravaani_hf_sweep.sh`, maps
to its job. The runner never launches a Hugging Face job itself; it only runs
inside one that was already started.

`tests/test_run_hf_job.py` checks every job against
`tests/fixtures/hf_jobs_legacy_commands.json`, the commands parsed from the old
scripts before they were removed, so a change to a job's behavior shows up in
CI.

| Job | Old script | What it does |
| --- | --- | --- |
| `hf_package_validation` | `run_hf_package_validation_job.sh` | Validate a built HF dataset package in the cloud. |
| `indicbert` | `run_indicbert_hf_job.sh` | IndicBERT LoRA adaptation, 4096 steps. |
| `indicbert_balanced` | `run_indicbert_balanced_hf_job.sh` | IndicBERT LoRA on the balanced general/PDF mix, 16384 steps. |
| `indicbert_pdf_domain` | `run_indicbert_pdf_domain_hf_job.sh` | IndicBERT LoRA on PDF-domain text, 8192 steps. |
| `indicbert_pdf_domain_extended` | `run_indicbert_pdf_domain_extended_hf_job.sh` | IndicBERT LoRA on PDF-domain text, 32768 steps. |
| `mt0` | `run_mt0_hf_job.sh` | mT0-small instruction LoRA v0.3, 2048 steps. |
| `mt0_16384` | `run_mt0_16384_hf_job.sh` | mT0-small instruction LoRA v0.5, 16384 steps. |
| `mt0_32768` | `run_mt0_32768_hf_job.sh` | mT0-small instruction LoRA v0.6, 32768 steps. |
| `mt0_32768_seed43` | `run_mt0_32768_seed43_hf_job.sh` | mT0-small instruction LoRA v0.6, 32768 steps, seed 43 only. |
| `mt0_extended` | `run_mt0_extended_hf_job.sh` | mT0-small instruction LoRA v0.4, 8192 steps. |
| `mt0_generation_analysis` | `run_mt0_generation_analysis_hf_job.sh` | Compare generations from old and new mT0 checkpoints. |
| `mt0_selected_test` | `run_mt0_selected_test_hf_job.sh` | Evaluate the selected mT0 checkpoint on the test split. |
| `ocr_validation` | `run_ocr_validation_hf_job.sh` | Score OCR corrections with IndicBERT. |
| `ocr_validation_multiseed` | `run_ocr_validation_multiseed_hf_job.sh` | Score OCR corrections with IndicBERT over three seeds. |
| `pdf_adapter_ocr_validation` | `run_pdf_adapter_ocr_validation_hf_job.sh` | Score OCR corrections with the PDF-domain IndicBERT adapter. |
| `semantic_duplicate` | `run_semantic_duplicate_hf_job.sh` | Find semantic near-duplicates in the text corpus. |
| `semantic_refinement` | `run_semantic_refinement_hf_job.sh` | Re-score semantic duplicate candidates. |
| `sravaani` | `run_sravaani_hf_job.sh` | SraVaani Garhwali decoder pilot training. |
| `sravaani_decoding_sweep` | `run_sravaani_hf_decoding_sweep.sh` | SraVaani decoding parameter sweep. |
| `sravaani_evaluation` | `run_sravaani_hf_evaluation.sh` | Held-out evaluation of the SraVaani pilot checkpoint. |
| `sravaani_expanded` | `run_sravaani_expanded_hf_job.sh` | SraVaani sweep on the expanded human set. |
| `sravaani_refined_61` | `run_sravaani_hf_refined_61.sh` | SraVaani refined decoder sweep. |
| `sravaani_six_config_sweep` | `run_sravaani_hf_six_config_sweep.sh` | SraVaani sweep capped at six trials. |
| `sravaani_sweep` | `run_sravaani_hf_sweep.sh` | SraVaani fine-tuning sweep, 20700 s budget. |
| `text_noise_audit` | `run_text_noise_audit_hf_job.sh` | Propose text cleanups scored with IndicBERT. |
| `whisper_agreement` | `run_whisper_agreement_hf_job.sh` | Whisper-small transcription agreement. |
| `whisper_turbo_agreement` | `run_whisper_turbo_agreement_hf_job.sh` | Whisper-large-v3-turbo transcription agreement. |
