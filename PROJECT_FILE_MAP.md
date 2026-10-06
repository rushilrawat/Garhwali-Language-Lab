# Project File Map

This generated index maps every Git-tracked and non-ignored project file. Ignored raw downloads, caches, model weights, and generated corpus payloads are not line-listed; their on-disk totals are summarized below, and their record inventories and hashes live in source, ingestion, release, and Hugging Face manifests under `research/`, `corpus/`, `data/`, and `release/`.

Files indexed: **1,022**.

Regenerate after adding, moving, or removing project files with:

```bash
python scripts/generate_project_file_map.py
```

## Root files

- `.gitignore`
- `ATTRIBUTION.md`
- `DATASET_CARD.md`
- `DEEP_DIVE_FINAL_AUDIT.md`
- `LICENSE`
- `LICENSE_POLICY.md`
- `PIPELINE.md`
- `PROJECT_FILE_MAP.md`
- `README.md`
- `REMOVAL_POLICY.md`
- `finalreport.md`
- `report-source.md`
- `requirements-asr.txt`
- `requirements-hf-release.txt`
- `requirements-model-audit.txt`
- `requirements-pipeline.txt`

## `.github/`

- `.github/workflows/ci.yml`
- `.github/workflows/source-freshness.yml`

## `corpus/`

- `corpus/README.md`
- `corpus/garhwali_language_library_manifest.json`
- `corpus/ingestion-report.json`
- `corpus/jambu_garhwali_manifest.json`

## `docs/`

- `docs/DATASET_SCHEMA.md`
- `docs/DEVELOPER_QUICKSTART.md`
- `docs/README.md`
- `docs/superpowers/plans/2026-09-10-corpus-preparation.md`
- `docs/superpowers/plans/2026-09-18-final-release-review.md`
- `docs/superpowers/plans/2026-09-24-model-accuracy-audit.md`
- `docs/superpowers/plans/2026-09-24-model-accuracy-final-report.md`
- `docs/superpowers/plans/2026-09-24-model-accuracy-improvement.md`
- `docs/superpowers/plans/2026-09-24-model-asr-accuracy.md`
- `docs/superpowers/plans/2026-09-24-model-generation-translation.md`
- `docs/superpowers/plans/2026-09-24-model-retrieval.md`
- `docs/superpowers/plans/2026-09-24-model-text-understanding.md`
- `docs/superpowers/plans/2026-09-24-model-tts-readiness.md`
- `docs/superpowers/specs/2026-09-24-model-accuracy-improvement-design.md`

## `examples/`

- `examples/search_garhwali_lexicon.py`

## `incoming/`

- `incoming/pdfs/Dictionary of English hindi Garhwali.json`
- `incoming/pdfs/Gadwali LokGeet.json`
- `incoming/pdfs/Gadwali Sahitya.json`
- `incoming/pdfs/Garhwali Bhasha_ Ek Bhashashashtriya Aur Vyakarnik Adhyayan.json`
- `incoming/pdfs/Garhwali Hindi Dictionary Uttarakhand Garwali Gadwali.json`
- `incoming/pdfs/Garhwali language and culture.json`
- `incoming/pdfs/Garhwali, A Syntactic Sketch of (Chandola).json`
- `incoming/pdfs/README.md`

## `release/`

- `release/final-audit.json`
- `release/v0.1.0-manifest.json`
- `release/v0.1.0/README.md`
- `release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/ATTRIBUTION.md`
- `release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/LICENSE_POLICY.md`
- `release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/README.md`
- `release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/REMOVAL_POLICY.md`
- `release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/manifest.json`
- `release/v0.1.0/artifacts/data/processed/audio/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/baseline_report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/confidence_calibration/sravaani/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/confidence_calibration/whisper_v0.2/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/curriculum_stage_0/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/curriculum_stage_0_validation/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/curriculum_stage_1_pilot/dry_run_report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/curriculum_stage_1_pilot/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/curriculum_stage_1_weighted_batch_pilot/dry_run_report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/curriculum_stage_1_weighted_batch_pilot/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_agreement/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_agreement/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_005000/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_020000/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_035000/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_050000/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/sravaani_1_0/full_draft_audit.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/sravaani_1_0/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/sravaani_decoding_sweep/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/sravaani_expanded_human/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/sravaani_finetune/cloud_output/held_out_evaluation/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/sravaani_refined_61/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/sravaani_six_config_sweep/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/whisper_small_zero_shot/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/asr/whisper_tiny_zero_shot/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_balanced_v0_1/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_cloud_v0_3/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_head_adaptation.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_lora_adaptation.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_lora_long.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_pdf_domain_extended_v0_2/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_pdf_domain_v0_1/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_transfer_test.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_16384_v0_5/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_32768_generation_analysis_v0_6/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_32768_seed43_v0_6/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_32768_selected_test_v0_6/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_cloud_v0_3/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_extended_v0_4/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_v0.2/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/mt5_instruction/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/controlled_modeling/text_scaling.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/data_quality/hf_package_local_validation/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_full_v0_1/integration_report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_full_v0_1/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_smoke_v0_1/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_v0_1/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/data_quality/ocr_pdf_adapter_v0_3/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/data_quality/ocr_validation_multiseed_v0_2/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/data_quality/ocr_validation_v0_1/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/data_quality/semantic_duplicates_refined_v0_2/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/data_quality/semantic_duplicates_v0_1/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/data_quality/text_noise_audit_v0_2/cloud_output/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/garhwali_bench/manifest.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/garhwali_bench/report.md`
- `release/v0.1.0/artifacts/data/processed/evaluation/model_audit/indicbertv2_masked_lm.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/model_audit/tokenizer_report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/retrieval/indicbertv2/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/retrieval/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/text_cleanup_ablation/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/translation/nllb_garhwali_adapter_hindi_proxy/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/translation/nllb_hindi_proxy/report.json`
- `release/v0.1.0/artifacts/data/processed/evaluation/translation/report.json`
- `release/v0.1.0/artifacts/data/processed/long_form_audio/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/asr_curriculum/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/asr_curriculum/trainer_dry_run_report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/asr_finetuning/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/audio/normalization_report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/audio/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/audio_normalized/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/cleaned/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/indicbert_balanced_domain/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/indicbert_pdf_domain/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/instructions/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/instructions_v0.2/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/language_quality/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/language_quality/vaani_source_conflicts_report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/language_resources/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/low_confidence_whisper_sample/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_020000/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_035000/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_050000/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_065000/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_080000/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_095000/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_expansion/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_sample/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/quality_v2/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/segments/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/splits/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/sravaani_expanded_human_finetune/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/sravaani_finetune/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/text_cleanup/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/text_quality_v2/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/text_source_audit/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware_report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/transcripts/machine_drafts_sravaani_quality_report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/transcripts/machine_drafts_sravaani_verified_report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/transcripts/report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_adjudication_report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_audio_grounded_review_report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_confidence_report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.2_report.json`
- `release/v0.1.0/artifacts/data/processed/model_ready/transcripts/supervised_review_model_evidence_report.json`
- `release/v0.1.0/artifacts/data/processed/native_review/packets/report.json`
- `release/v0.1.0/artifacts/data/processed/native_review/results/report.json`
- `release/v0.1.0/artifacts/data/processed/native_review/reviewed/report.json`
- `release/v0.1.0/artifacts/data/processed/native_review/templates/report.json`
- `release/v0.1.0/artifacts/data/processed/release/manifest.json`
- `release/v0.1.0/artifacts/data/processed/review/report.json`
- `release/v0.1.0/artifacts/data/processed/text/all_garhwali_report.json`
- `release/v0.1.0/artifacts/data/processed/text/cleaned_all_garhwali_report.json`
- `release/v0.1.0/artifacts/data/processed/text/paharili_garhwali_report.json`
- `release/v0.1.0/artifacts/data/processed/text/report.json`
- `release/v0.1.0/artifacts/data/processed/vaani/report.json`
- `release/v0.1.0/artifacts/index.json`
- `release/v0.1.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/GarhwaliCorpus-source-inventory.xlsx`
- `release/v0.1.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/GarhwaliCorpus-source-inventory.xlsx.inspect.ndjson`
- `release/v0.1.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/corpus-schema.png`
- `release/v0.1.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/inspection.txt`
- `release/v0.1.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/inventory.png`
- `release/v0.1.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/rights-guide.png`
- `release/v0.1.0/artifacts/outputs/online-ingestion-2026-09-07/dedup-report.json`
- `release/v0.1.0/artifacts/outputs/online-ingestion-2026-09-07/lsi-page-check.png`
- `release/v0.1.0/artifacts/outputs/online-ingestion-2026-09-07/report.md`
- `release/v0.1.0/huggingface-all-data-upload.json`
- `release/v0.1.0/huggingface-preflight.json`
- `release/v0.1.1-manifest.json`
- `release/v0.1.1/README.md`
- `release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/ATTRIBUTION.md`
- `release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/LICENSE_POLICY.md`
- `release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/README.md`
- `release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/REMOVAL_POLICY.md`
- `release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/manifest.json`
- `release/v0.1.1/artifacts/data/processed/audio/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/baseline_report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/confidence_calibration/sravaani/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/confidence_calibration/whisper_v0.2/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/curriculum_stage_0/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/curriculum_stage_0_validation/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/curriculum_stage_1_pilot/dry_run_report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/curriculum_stage_1_pilot/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/curriculum_stage_1_weighted_batch_pilot/dry_run_report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/curriculum_stage_1_weighted_batch_pilot/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/low_confidence_whisper_agreement/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_agreement/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_005000/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_020000/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_035000/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_050000/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/sravaani_1_0/full_draft_audit.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/sravaani_1_0/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/sravaani_decoding_sweep/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/sravaani_expanded_human/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/sravaani_finetune/cloud_output/held_out_evaluation/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/sravaani_refined_61/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/sravaani_six_config_sweep/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/whisper_small_zero_shot/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/asr/whisper_tiny_zero_shot/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/indicbert_balanced_v0_1/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/indicbert_cloud_v0_3/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/indicbert_head_adaptation.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/indicbert_lora_adaptation.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/indicbert_lora_long.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/indicbert_pdf_domain_extended_v0_2/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/indicbert_pdf_domain_v0_1/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/indicbert_transfer_test.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_16384_v0_5/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_32768_generation_analysis_v0_6/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_32768_seed43_v0_6/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_32768_selected_test_v0_6/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_cloud_v0_3/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_extended_v0_4/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_v0.2/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/mt5_instruction/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/controlled_modeling/text_scaling.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/data_quality/hf_package_local_validation/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_full_v0_1/integration_report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_full_v0_1/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_smoke_v0_1/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_v0_1/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/data_quality/ocr_pdf_adapter_v0_3/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/data_quality/ocr_validation_multiseed_v0_2/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/data_quality/ocr_validation_v0_1/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/data_quality/semantic_duplicates_refined_v0_2/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/data_quality/semantic_duplicates_v0_1/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/data_quality/text_noise_audit_v0_2/cloud_output/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/garhwali_bench/manifest.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/garhwali_bench/report.md`
- `release/v0.1.1/artifacts/data/processed/evaluation/garhwali_bench/v0.2-draft/manifest.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/model_audit/indicbertv2_masked_lm.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/model_audit/tokenizer_report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/retrieval/indicbertv2/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/retrieval/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/retrieval/roadmap_2026-09-25/bm25_dev/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/text_cleanup_ablation/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/translation/accuracy_dev/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/translation/nllb_garhwali_adapter_hindi_proxy/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/translation/nllb_hindi_proxy/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/translation/phase4_manifest_dev/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/translation/phase4_manifest_dev_gated/report.json`
- `release/v0.1.1/artifacts/data/processed/evaluation/translation/report.json`
- `release/v0.1.1/artifacts/data/processed/long_form_audio/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/asr_curriculum/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/asr_curriculum/trainer_dry_run_report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/asr_finetuning/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/audio/normalization_report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/audio/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/audio_normalized/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/cleaned/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/indicbert_balanced_domain/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/indicbert_pdf_domain/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/instructions/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/instructions_v0.2/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/language_quality/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/language_quality/vaani_source_conflicts_report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/language_resources/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/low_confidence_whisper_sample/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_020000/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_035000/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_050000/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_065000/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_080000/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_095000/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_expansion/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_sample/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/quality_v2/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/segments/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/splits/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/splits/text_recommended/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/sravaani_expanded_human_finetune/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/sravaani_finetune/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/text_cleanup/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/text_quality_v2/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/text_source_audit/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware_report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/transcripts/machine_drafts_sravaani_quality_report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/transcripts/machine_drafts_sravaani_verified_report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/transcripts/report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_adjudication_report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_audio_grounded_review_report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_confidence_report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.2_report.json`
- `release/v0.1.1/artifacts/data/processed/model_ready/transcripts/supervised_review_model_evidence_report.json`
- `release/v0.1.1/artifacts/data/processed/native_review/packets/report.json`
- `release/v0.1.1/artifacts/data/processed/native_review/results/report.json`
- `release/v0.1.1/artifacts/data/processed/native_review/reviewed/report.json`
- `release/v0.1.1/artifacts/data/processed/native_review/templates/report.json`
- `release/v0.1.1/artifacts/data/processed/release/manifest.json`
- `release/v0.1.1/artifacts/data/processed/review/report.json`
- `release/v0.1.1/artifacts/data/processed/text/all_garhwali_report.json`
- `release/v0.1.1/artifacts/data/processed/text/cleaned_all_garhwali_report.json`
- `release/v0.1.1/artifacts/data/processed/text/paharili_garhwali_report.json`
- `release/v0.1.1/artifacts/data/processed/text/report.json`
- `release/v0.1.1/artifacts/data/processed/vaani/report.json`
- `release/v0.1.1/artifacts/index.json`
- `release/v0.1.1/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/GarhwaliCorpus-source-inventory.xlsx`
- `release/v0.1.1/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/GarhwaliCorpus-source-inventory.xlsx.inspect.ndjson`
- `release/v0.1.1/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/corpus-schema.png`
- `release/v0.1.1/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/inspection.txt`
- `release/v0.1.1/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/inventory.png`
- `release/v0.1.1/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/rights-guide.png`
- `release/v0.1.1/artifacts/outputs/online-ingestion-2026-09-07/dedup-report.json`
- `release/v0.1.1/artifacts/outputs/online-ingestion-2026-09-07/lsi-page-check.png`
- `release/v0.1.1/artifacts/outputs/online-ingestion-2026-09-07/report.md`
- `release/v0.1.1/final-audit.json`
- `release/v0.1.1/huggingface-all-data-upload.json`
- `release/v0.1.1/huggingface-preflight.json`
- `release/v0.1.1/huggingface-public-preflight.json`
- `release/v0.1.1/huggingface-public-upload.json`
- `release/v0.2.0-manifest.json`
- `release/v0.2.0/README.md`
- `release/v0.2.0/artifacts/data/huggingface/garhwali-language-lab/ATTRIBUTION.md`
- `release/v0.2.0/artifacts/data/huggingface/garhwali-language-lab/LICENSE_POLICY.md`
- `release/v0.2.0/artifacts/data/huggingface/garhwali-language-lab/README.md`
- `release/v0.2.0/artifacts/data/huggingface/garhwali-language-lab/REMOVAL_POLICY.md`
- `release/v0.2.0/artifacts/data/huggingface/garhwali-language-lab/manifest.json`
- `release/v0.2.0/artifacts/data/processed/audio/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/baseline_report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/confidence_calibration/sravaani/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/confidence_calibration/whisper_v0.2/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/curriculum_stage_0/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/curriculum_stage_0_validation/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/curriculum_stage_1_pilot/dry_run_report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/curriculum_stage_1_pilot/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/curriculum_stage_1_weighted_batch_pilot/dry_run_report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/curriculum_stage_1_weighted_batch_pilot/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/heldout_lineage_audit_2026-09-28/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/heldout_lineage_audit_2026-09-28/report.md`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_agreement/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_agreement/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_005000/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_020000/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_035000/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_050000/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/sravaani_1_0/full_draft_audit.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/sravaani_1_0/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/sravaani_decoding_sweep/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/sravaani_expanded_human/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/sravaani_finetune/cloud_output/held_out_evaluation/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/sravaani_refined_61/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/sravaani_six_config_sweep/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/validation_comparison_manifested_2026-09-27/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/whisper_small_zero_shot/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/whisper_tiny_zero_shot/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/whisper_v02_validation_decode_sweep_2026-09-28/beam-1/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/whisper_v02_validation_decode_sweep_2026-09-28/beam-2/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/asr/whisper_v02_validation_decode_sweep_2026-09-28/beam-4/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/benchmark_scoring/translation_dev_existing_tm/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/benchmark_scoring/translation_dev_uncertainty/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_balanced_v0_1/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_cloud_v0_3/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_head_adaptation.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_lora_adaptation.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_lora_long.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_pdf_domain_extended_v0_2/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_pdf_domain_v0_1/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/indicbert_transfer_test.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_16384_v0_5/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_32768_generation_analysis_v0_6/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_32768_seed43_v0_6/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_32768_selected_test_v0_6/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_cloud_v0_3/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_extended_v0_4/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/mt0_instruction_v0.2/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/mt5_instruction/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/controlled_modeling/text_scaling.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/data_quality/hf_package_local_validation/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_full_v0_1/integration_report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_full_v0_1/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_smoke_v0_1/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/data_quality/incoming_pdf_reocr_v0_1/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/data_quality/ocr_pdf_adapter_v0_3/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/data_quality/ocr_validation_multiseed_v0_2/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/data_quality/ocr_validation_v0_1/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/data_quality/semantic_duplicates_refined_v0_2/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/data_quality/semantic_duplicates_v0_1/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/data_quality/text_noise_audit_v0_2/cloud_output/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/garhwali_bench/manifest.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/garhwali_bench/report.md`
- `release/v0.2.0/artifacts/data/processed/evaluation/garhwali_bench/v0.2-draft/manifest.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/garhwali_bench_parent_safe_v0.2_2026-09-28/manifest.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/garhwali_bench_parent_safe_v0.2_2026-09-28/report.md`
- `release/v0.2.0/artifacts/data/processed/evaluation/garhwali_bench_parent_safe_v0.2_2026-09-28/v0.2-draft/manifest.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/garhwali_bench_parent_safe_v0.2_2026-09-28/v0.2-frozen-candidate/manifest.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/generation/mt0_32768_validation_manifested_2026-09-27/seed-17/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/generation/mt0_32768_validation_manifested_2026-09-27/seed-29/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/generation/mt0_32768_validation_manifested_2026-09-27/seed-43/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/model_audit/indicbertv2_masked_lm.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/model_audit/tokenizer_report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/retrieval/indicbertv2/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/retrieval/phase4_manifest_dev/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/retrieval/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/retrieval/roadmap_2026-09-25/bm25_dev/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/retrieval/roadmap_2026-09-28/miss_analysis/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/retrieval/roadmap_2026-09-28/miss_analysis/report.md`
- `release/v0.2.0/artifacts/data/processed/evaluation/retrieval/roadmap_2026-09-28/source_page_cluster_bootstrap/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/retrieval/roadmap_2026-09-28/source_page_cluster_bootstrap/report.md`
- `release/v0.2.0/artifacts/data/processed/evaluation/text_cleanup_ablation/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/translation/accuracy_dev/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/translation/nllb_garhwali_adapter_hindi_proxy/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/translation/nllb_hindi_proxy/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/translation/phase4_manifest_dev/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/translation/phase4_manifest_dev_gated/report.json`
- `release/v0.2.0/artifacts/data/processed/evaluation/translation/report.json`
- `release/v0.2.0/artifacts/data/processed/long_form_audio/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/asr_curriculum/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/asr_curriculum/trainer_dry_run_report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/asr_finetuning/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/audio/normalization_report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/audio/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/audio_normalized/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/cleaned/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/indicbert_balanced_domain/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/indicbert_pdf_domain/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/instructions/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/instructions_v0.2/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/language_quality/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/language_quality/vaani_source_conflicts_report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/language_resources/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/low_confidence_whisper_sample/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_020000/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_035000/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_050000/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_065000/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_080000/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_095000/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_expansion/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/low_confidence_whisper_turbo_sample/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/quality_v2/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/segments/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/splits/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/splits/text_recommended/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/splits_parent_safe_v0.2_2026-09-28/garhwali_bench/manifest.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/splits_parent_safe_v0.2_2026-09-28/garhwali_bench/report.md`
- `release/v0.2.0/artifacts/data/processed/model_ready/splits_parent_safe_v0.2_2026-09-28/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/splits_parent_safe_v0.2_2026-09-28/text_recommended/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/sravaani_expanded_human_finetune/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/sravaani_finetune/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/text_cleanup/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/text_quality_v2/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/text_source_audit/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware_report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/transcripts/machine_drafts_sravaani_quality_report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/transcripts/machine_drafts_sravaani_verified_report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/transcripts/report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_adjudication_report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_audio_grounded_review_report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_confidence_report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.2_report.json`
- `release/v0.2.0/artifacts/data/processed/model_ready/transcripts/supervised_review_model_evidence_report.json`
- `release/v0.2.0/artifacts/data/processed/native_review/packets/report.json`
- `release/v0.2.0/artifacts/data/processed/native_review/results/report.json`
- `release/v0.2.0/artifacts/data/processed/native_review/reviewed/report.json`
- `release/v0.2.0/artifacts/data/processed/native_review/templates/report.json`
- `release/v0.2.0/artifacts/data/processed/release/manifest.json`
- `release/v0.2.0/artifacts/data/processed/review/report.json`
- `release/v0.2.0/artifacts/data/processed/text/all_garhwali_report.json`
- `release/v0.2.0/artifacts/data/processed/text/cleaned_all_garhwali_report.json`
- `release/v0.2.0/artifacts/data/processed/text/paharili_garhwali_report.json`
- `release/v0.2.0/artifacts/data/processed/text/report.json`
- `release/v0.2.0/artifacts/data/processed/vaani/report.json`
- `release/v0.2.0/artifacts/index.json`
- `release/v0.2.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/GarhwaliCorpus-source-inventory.xlsx`
- `release/v0.2.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/GarhwaliCorpus-source-inventory.xlsx.inspect.ndjson`
- `release/v0.2.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/corpus-schema.png`
- `release/v0.2.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/inspection.txt`
- `release/v0.2.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/inventory.png`
- `release/v0.2.0/artifacts/outputs/garhwali-corpus-inventory-2026-09-07/rights-guide.png`
- `release/v0.2.0/artifacts/outputs/online-ingestion-2026-09-07/dedup-report.json`
- `release/v0.2.0/artifacts/outputs/online-ingestion-2026-09-07/lsi-page-check.png`
- `release/v0.2.0/artifacts/outputs/online-ingestion-2026-09-07/report.md`
- `release/v0.2.0/final-audit.json`
- `release/v0.2.0/huggingface-all-data-preflight.json`
- `release/v0.2.0/huggingface-all-data-upload.json`
- `release/v0.2.0/huggingface-public-preflight.json`
- `release/v0.2.0/huggingface-public-upload.json`
- `release/v0.2.0/huggingface-publication.json`

## `research/`

- `research/all-data-package-2026-09-15.md`
- `research/all-data-package-2026-09-19.md`
- `research/asr-baseline-2026-09-10.md`
- `research/asr-baseline-consolidation-2026-09-26.md`
- `research/asr-corpus-metric-integration-2026-09-29.md`
- `research/asr-curriculum-stage0-2026-09-14.md`
- `research/asr-curriculum-stage1-pilot-2026-09-14.md`
- `research/asr-heldout-lineage-audit-2026-09-28.md`
- `research/asr-training-curriculum-2026-09-14.md`
- `research/asr-validation-error-analysis-2026-09-24.json`
- `research/asr-validation-error-analysis-2026-09-24.md`
- `research/asr-validation-run-manifest-2026-09-27.md`
- `research/asr-weighted-batch-ablation-2026-09-14.md`
- `research/asr-weighted-trainer-2026-09-14.md`
- `research/automated-pre-release-quality-plan.md`
- `research/benchmark-cross-language-exact-overlap-2026-09-28.md`
- `research/benchmark-model-roadmap.md`
- `research/benchmark-nested-overlap-review-2026-09-27.md`
- `research/benchmark-overlap-adjudication-2026-09-26.md`
- `research/benchmark-parent-safe-split-audit-2026-09-28.md`
- `research/benchmark-research-status-2026-09-25.md`
- `research/benchmark-rights-provenance-audit-2026-10-05.json`
- `research/benchmark-rights-provenance-audit-2026-10-05.md`
- `research/benchmark-source-page-families-2026-09-28.md`
- `research/benchmark-v02-export-2026-09-26.md`
- `research/controlled-modeling-2026-09-12.md`
- `research/controlled-text-scaling-2026-09-11.md`
- `research/corpus-preparation-status.md`
- `research/cultural-ingestion-report.md`
- `research/cultural-source-leads.json`
- `research/dataset-splits-2026-09-10.md`
- `research/gap-closure-plan.md`
- `research/garhwali-access-blockers-2026-09-10.md`
- `research/garhwali-bench-v0.1-2026-09-11.md`
- `research/garhwali-bench-v0.2-draft-cards.md`
- `research/garhwali-bench-v0.2-rights-inventory-2026-09-29.md`
- `research/garhwali-bench-v0.2-schema-contract.md`
- `research/garhwali-cultural-media.json`
- `research/garhwali-data-expansion-2026-09-29.md`
- `research/garhwali-folklore-internet-audit-2026-09-10.md`
- `research/garhwali-geography-catalog.json`
- `research/garhwali-historical-terms.json`
- `research/garhwali-literary-people-catalog.json`
- `research/garhwali-literary-works-catalog.json`
- `research/garhwali-poetry-plays-inventory-2026-09-15.md`
- `research/garhwali-popular-song-catalog.json`
- `research/garhwali-scholarly-guide.md`
- `research/garhwali-thematic-lexicon.json`
- `research/garhwali-university-research-catalog.json`
- `research/garhwali-web-goldmines-2026-09-30.md`
- `research/generation-output-diagnostics-2026-09-28.md`
- `research/generation-quality-2026-09-25.md`
- `research/generation-scoring-integration-2026-09-30.md`
- `research/huggingface-all-data-candidate-preflight-2026-10-05.json`
- `research/huggingface-corpus-gap-resolution-2026-10-06.md`
- `research/huggingface-corpus-v0.2.4-release-2026-10-05.md`
- `research/huggingface-corpus-v0.2.5-release-2026-10-05.md`
- `research/huggingface-corpus-v0.2.5-viewer-schema-repair-2026-10-05.md`
- `research/huggingface-corpus-v0.2.6-release-2026-10-05.md`
- `research/huggingface-corpus-v0.2.7-release-2026-10-06.md`
- `research/huggingface-dataset-quality-roadmap.md`
- `research/huggingface-existing-corpus-expansion-audit-2026-10-02.md`
- `research/huggingface-indic_dialect_asr_gbm-catalog-lineage-2026-10-05.json`
- `research/huggingface-indic_dialect_asr_gbm-cleaned-lineage-2026-10-05.json`
- `research/huggingface-indic_dialect_asr_gbm-lineage-2026-10-05.json`
- `research/huggingface-indic_dialect_asr_gbm-v0.2.5-text-lineage-2026-10-05.json`
- `research/huggingface-meta_omnilingual-catalog-lineage-2026-10-05.json`
- `research/huggingface-meta_omnilingual-cleaned-lineage-2026-10-05.json`
- `research/huggingface-meta_omnilingual-lineage-2026-10-05.json`
- `research/huggingface-meta_omnilingual-v0.2.5-text-lineage-2026-10-05.json`
- `research/huggingface-phase2-source-rights-lineage-audit-2026-10-05.md`
- `research/huggingface-quality-baseline-2026-10-01.md`
- `research/huggingface-quality-candidate-preflight-2026-10-01.json`
- `research/huggingface-quality-candidate-preflight-2026-10-02.json`
- `research/huggingface-quality-candidate-preflight-2026-10-05.json`
- `research/huggingface-release-continuity-v0.2.5-v0.2.6-2026-10-05.json`
- `research/huggingface-release-metrics-v0.2.5-to-v0.2.6-2026-10-05.json`
- `research/huggingface-release-metrics-v0.2.5-to-v0.2.6-2026-10-05.md`
- `research/huggingface-release-overlap-audit-2026-09-24.md`
- `research/huggingface-text-expansion-audit-2026-10-01.md`
- `research/huggingface-training-eligibility-audit-2026-10-05.json`
- `research/huggingface-training-eligibility-audit-2026-10-05.md`
- `research/huggingface-upstream-split-overlap-2026-10-05.json`
- `research/huggingface-upstream-split-overlap-2026-10-05.md`
- `research/huggingface-v0.2.3-upload-plan.json`
- `research/huggingface-v0.2.4-upload-plan.json`
- `research/huggingface-v0.2.5-comparison-preflight-2026-10-05.json`
- `research/huggingface-v0.2.5-upload-plan.json`
- `research/huggingface-v0.2.6-candidate-preflight-2026-10-05.json`
- `research/huggingface-v0.2.6-remote-file-verification-2026-10-05.json`
- `research/huggingface-v0.2.6-viewer-schema-hotfix-2026-10-05.md`
- `research/incoming-pdf-ingestion-2026-09-16.json`
- `research/incoming-pdf-ingestion-2026-09-16.md`
- `research/incoming-pdf-reocr-pilot-2026-09-17.md`
- `research/independent-evaluation-protocol-2026-09-29.md`
- `research/indicbert-balanced-domain-2026-09-16.md`
- `research/indicbert-cloud-continuation-2026-09-16.md`
- `research/indicbert-pdf-domain-2026-09-16.md`
- `research/indicbert-pdf-domain-extended-2026-09-16.md`
- `research/intensive-quality-audit-2026-09-14.md`
- `research/internet-archive-garhwali-folklore-search.json`
- `research/internet-archive-garhwali-search-2026-10-03.json`
- `research/internet-archive-intake-2026-10-03.md`
- `research/internet-archive-intake-quality-2026-10-04.md`
- `research/internet-archive-media-first-pass-2026-10-04.md`
- `research/internet-archive-priority-language-rights-review-2026-10-04.md`
- `research/internet-archive-source-disposition-2026-10-04.json`
- `research/internet-archive-source-disposition-2026-10-04.md`
- `research/issues&improvement plan.md`
- `research/language-quality-status-2026-09-10.md`
- `research/license-specific-source-export-audit-2026-10-05.md`
- `research/meta-omnilingual-asr-adaptation-2026-10-05.md`
- `research/meta-omnilingual-asr-validation-2026-10-04.md`
- `research/model-accuracy-lineage-2026-09-24.md`
- `research/model-accuracy-lineage-2026-09-28.md`
- `research/model-accuracy-preflight-2026-09-24.md`
- `research/model-assisted-text-cleanup-2026-09-11.md`
- `research/model-lineage-refresh-2026-10-05.md`
- `research/mt0-16384-validation-2026-09-16.md`
- `research/mt0-32768-partial-2026-09-16.md`
- `research/mt0-cloud-continuation-2026-09-16.md`
- `research/mt0-extended-validation-2026-09-16.md`
- `research/mt0-validation-run-manifest-2026-09-27.md`
- `research/multilingual-model-audit-2026-09-11.md`
- `research/native-reference-review-readiness-2026-09-15.md`
- `research/ocr-proposal-validation-2026-09-16.md`
- `research/outreach-drafts.md`
- `research/popular-song-ingestion-2026-09-15.md`
- `research/product-progress-2026-09-29.md`
- `research/retrieval-baseline-2026-09-11.md`
- `research/retrieval-miss-analysis-2026-09-28.md`
- `research/retrieval-quality-2026-09-25.md`
- `research/retrieval-source-page-cluster-uncertainty-2026-09-28.md`
- `research/scholarly-open-sources.json`
- `research/semantic-duplicate-audit-2026-09-16.md`
- `research/semantic-duplicate-refinement-2026-09-16.md`
- `research/social-media-ingestion-2026-09-10.md`
- `research/source-attribution-overlays-2026-10-05.json`
- `research/source-expansion-v2.0-2026-09-30.md`
- `research/speech-baseline-comparison-2026-09-11.md`
- `research/sravaani-adaptation-evaluation-2026-09-16.md`
- `research/sravaani-adaptation-readiness-2026-09-14.md`
- `research/sravaani-audio-grounded-review-2026-09-14.md`
- `research/sravaani-budget-sweep-2026-09-16.md`
- `research/sravaani-confidence-integration-2026-09-14.md`
- `research/sravaani-expanded-human-2026-09-16.md`
- `research/sravaani-recovery-adjudication-2026-09-14.md`
- `research/sravaani-recovery-confidence-2026-09-13.md`
- `research/sravaani-refined-61-result-2026-09-16.md`
- `research/sravaani-transcript-recovery-2026-09-13.md`
- `research/structured-rights-web-review-2026-09-23.md`
- `research/task-result-eligibility-2026-09-28.md`
- `research/tatoeba-attribution-audit-2026-10-05.json`
- `research/text-accuracy-review-2026-09-15.md`
- `research/text-noise-audit-2026-09-16.md`
- `research/text-release-quality-2026-09-16.json`
- `research/text-release-quality-2026-09-16.md`
- `research/text-rights-resolution-2026-09-30.md`
- `research/text-source-rights-audit-2026-09-15.md`
- `research/thematic-vocabulary-report.md`
- `research/translation-baseline-2026-09-11.md`
- `research/translation-quality-2026-09-26.md`
- `research/v0.2-public-announcement-roadmap-2026-09-29.md`
- `research/v2.0-release-report-2026-09-30.md`
- `research/vaani-audit-2026-09-09.md`
- `research/vaani-collection-completion-2026-09-09.md`
- `research/vaani-full-use-plan.md`
- `research/vaani-official-split-lineage-2026-10-04.md`
- `research/xhigh-final-data-audit-2026-09-10.md`

## `review/`

- `review/README.md`
- `review/decision-template.json`

## `scripts/`

- `scripts/README.md`
- `scripts/analyze_generation_output_diagnostics.py`
- `scripts/analyze_retrieval_cluster_uncertainty.py`
- `scripts/analyze_retrieval_misses.py`
- `scripts/analyze_saved_asr_validation.py`
- `scripts/analyze_sravaani_drafts.py`
- `scripts/analyze_translation_uncertainty.py`
- `scripts/asr_metrics.py`
- `scripts/audit_archive_alternate_ocr_overlap.py`
- `scripts/audit_archive_corpus_overlap.py`
- `scripts/audit_archive_intake_quality.py`
- `scripts/audit_archive_media_first_pass.py`
- `scripts/audit_archive_priority_page_evidence.py`
- `scripts/audit_audio_quality.py`
- `scripts/audit_benchmark_nested_overlap.py`
- `scripts/audit_benchmark_overlap_candidates.py`
- `scripts/audit_benchmark_v02_rights.py`
- `scripts/audit_final_release.py`
- `scripts/audit_garhwali_expansion.py`
- `scripts/audit_hf_release_continuity.py`
- `scripts/audit_hf_source_lineage.py`
- `scripts/audit_hf_training_eligibility.py`
- `scripts/audit_indicbert_cloud_input.py`
- `scripts/audit_model_accuracy_lineage.py`
- `scripts/audit_multilingual_tokenizers.py`
- `scripts/audit_saved_asr_heldout_lineage.py`
- `scripts/audit_semantic_duplicates.py`
- `scripts/audit_text_release_quality.py`
- `scripts/audit_text_sources.py`
- `scripts/audit_upstream_split_overlap.py`
- `scripts/audit_vaani.py`
- `scripts/audit_vaani_official_split_lineage.py`
- `scripts/audit_xorqa_source_page_families.py`
- `scripts/benchmark_metrics.py`
- `scripts/build_all_data_view.py`
- `scripts/build_archive_book_page_map.py`
- `scripts/build_archive_source_disposition.py`
- `scripts/build_asr_training_curriculum.py`
- `scripts/build_audio_training_manifests.py`
- `scripts/build_benchmark_usage_labels.py`
- `scripts/build_benchmark_v02.py`
- `scripts/build_dataset_splits.py`
- `scripts/build_garhwali_benchmark.py`
- `scripts/build_hf_meta_omni_speech.py`
- `scripts/build_hf_reference_index.py`
- `scripts/build_hf_speech_release.py`
- `scripts/build_hf_upload_plan.py`
- `scripts/build_huggingface_dataset.py`
- `scripts/build_instruction_accuracy_split.py`
- `scripts/build_instruction_dataset.py`
- `scripts/build_language_resources.py`
- `scripts/build_quality_tiers.py`
- `scripts/build_recommended_text_view.py`
- `scripts/build_release_bundle.py`
- `scripts/build_release_manifest.py`
- `scripts/build_review_queues.py`
- `scripts/build_sravaani_audio_grounded_review.py`
- `scripts/build_sravaani_recovery_adjudication.py`
- `scripts/build_vaani_corpus_manifests.py`
- `scripts/build_vaani_source_conflicts.py`
- `scripts/calibrate_sravaani_recovery_confidence.py`
- `scripts/check_source_freshness.py`
- `scripts/clean_text_corpus.py`
- `scripts/collect_online.py`
- `scripts/collect_vaani_reference_images.py`
- `scripts/compare_archive_ocr_variants.py`
- `scripts/compare_asr_predictions.py`
- `scripts/compare_hf_release_metrics.py`
- `scripts/dedup_report.py`
- `scripts/deep_cleanup.py`
- `scripts/download_garhwali_folktales.py`
- `scripts/download_vaani_transcription_only.py`
- `scripts/evaluate_indicbert_transfer.py`
- `scripts/evaluate_mt0_generation_checkpoints.py`
- `scripts/evaluate_mt0_selected_test.py`
- `scripts/evaluate_sravaani_finetune.py`
- `scripts/evaluation_run_manifest.py`
- `scripts/export_asr_finetuning_data.py`
- `scripts/export_licensed_sources.py`
- `scripts/extract_dhyani_idioms.py`
- `scripts/extract_downloaded_folklore.py`
- `scripts/extract_vaani_audio.py`
- `scripts/finalize_local_release.sh`
- `scripts/finalize_local_release_v0_2.sh`
- `scripts/generate_project_file_map.py`
- `scripts/hf_source_registry.py`
- `scripts/ingest_archive_dabral_references.py`
- `scripts/ingest_archive_holy_himalaya.py`
- `scripts/ingest_archive_language_studies.py`
- `scripts/ingest_archive_regional_historical_references.py`
- `scripts/ingest_archive_snow_balls.py`
- `scripts/ingest_garhwali_language_library.py`
- `scripts/ingest_geography.py`
- `scripts/ingest_historical_terms.py`
- `scripts/ingest_incoming_pdfs.py`
- `scripts/ingest_jambu_garhwali.py`
- `scripts/ingest_literary_people.py`
- `scripts/ingest_literary_works.py`
- `scripts/ingest_lsi_garhwali_specimens.py`
- `scripts/ingest_lsi_garhwali_table.py`
- `scripts/ingest_obs_tlf.py`
- `scripts/ingest_open.py`
- `scripts/ingest_popular_songs.py`
- `scripts/ingest_social_garhwali.py`
- `scripts/ingest_university_research.py`
- `scripts/ingest_upreti_1894_garhwali.py`
- `scripts/ingest_web_goldmines.py`
- `scripts/ingest_web_learning.py`
- `scripts/ingestion_graph.py`
- `scripts/integrate_reocr_evidence.py`
- `scripts/integrate_sravaani_confidence.py`
- `scripts/integrate_whisper_turbo_evidence.py`
- `scripts/manifest_saved_generation_validation.py`
- `scripts/native_review_workflow.py`
- `scripts/ocr_uou.py`
- `scripts/ocr_uou_more.py`
- `scripts/prepare_audio_normalization.py`
- `scripts/prepare_hf_additive_upload.py`
- `scripts/prepare_indicbert_balanced_domain.py`
- `scripts/prepare_indicbert_pdf_domain.py`
- `scripts/prepare_low_confidence_asr_sample.py`
- `scripts/prepare_meta_omnilingual_asr.py`
- `scripts/prepare_sravaani_expanded_finetune.py`
- `scripts/prepare_sravaani_finetune.py`
- `scripts/prepare_text_corpus.py`
- `scripts/prepare_transcripts.py`
- `scripts/prepare_vaani_supervised.py`
- `scripts/prepare_whisper_compatible_manifests.py`
- `scripts/promote_paharili_garhwali.py`
- `scripts/propose_text_cleanup.py`
- `scripts/reconcile_vaani_audio_paths.py`
- `scripts/record_schema.py`
- `scripts/redecode_sravaani_recovery.py`
- `scripts/redecode_supervised_review.py`
- `scripts/refine_priority_text.py`
- `scripts/refine_semantic_duplicates.py`
- `scripts/refresh_corpus_after_ingestion.py`
- `scripts/refresh_incoming_pdfs.sh`
- `scripts/register_asr_stage0.py`
- `scripts/register_asr_stage1_pilot.py`
- `scripts/register_asr_stage1_weighted_batch_pilot.py`
- `scripts/render_normalized_audio.py`
- `scripts/reocr_archive_quality_pages.py`
- `scripts/reprocess_ocr_candidates.py`
- `scripts/route_sravaani_recovery.py`
- `scripts/run_asr_baseline.py`
- `scripts/run_hf_package_validation_job.sh`
- `scripts/run_indicbert_adaptation.py`
- `scripts/run_indicbert_balanced_hf_job.sh`
- `scripts/run_indicbert_hf_job.sh`
- `scripts/run_indicbert_lora_adaptation.py`
- `scripts/run_indicbert_pdf_domain_extended_hf_job.sh`
- `scripts/run_indicbert_pdf_domain_hf_job.sh`
- `scripts/run_indicbert_retrieval_baseline.py`
- `scripts/run_masked_lm_baseline.py`
- `scripts/run_mt0_16384_hf_job.sh`
- `scripts/run_mt0_32768_hf_job.sh`
- `scripts/run_mt0_32768_seed43_hf_job.sh`
- `scripts/run_mt0_extended_hf_job.sh`
- `scripts/run_mt0_generation_analysis_hf_job.sh`
- `scripts/run_mt0_hf_job.sh`
- `scripts/run_mt0_selected_test_hf_job.sh`
- `scripts/run_mt5_instruction_tuning.py`
- `scripts/run_nllb_translation_baseline.py`
- `scripts/run_ocr_validation_hf_job.sh`
- `scripts/run_ocr_validation_multiseed_hf_job.sh`
- `scripts/run_pdf_adapter_ocr_validation_hf_job.sh`
- `scripts/run_retrieval_baseline.py`
- `scripts/run_semantic_duplicate_hf_job.sh`
- `scripts/run_semantic_refinement_hf_job.sh`
- `scripts/run_sravaani_comparison.py`
- `scripts/run_sravaani_expanded_hf_job.sh`
- `scripts/run_sravaani_hf_decoding_sweep.sh`
- `scripts/run_sravaani_hf_evaluation.sh`
- `scripts/run_sravaani_hf_job.sh`
- `scripts/run_sravaani_hf_refined_61.sh`
- `scripts/run_sravaani_hf_six_config_sweep.sh`
- `scripts/run_sravaani_hf_sweep.sh`
- `scripts/run_text_cleanup_ablation.py`
- `scripts/run_text_noise_audit_hf_job.sh`
- `scripts/run_text_scaling_experiment.py`
- `scripts/run_translation_baseline.py`
- `scripts/run_whisper_agreement_hf_job.sh`
- `scripts/run_whisper_comparison.py`
- `scripts/run_whisper_turbo_agreement_hf_job.sh`
- `scripts/score_benchmark_predictions.py`
- `scripts/segment_long_audio.py`
- `scripts/segment_text_corpus.py`
- `scripts/sweep_sravaani_decoding.py`
- `scripts/sweep_sravaani_garhwali.py`
- `scripts/sync_release_index.py`
- `scripts/tag_language_quality.py`
- `scripts/train_sravaani_garhwali.py`
- `scripts/train_whisper_garhwali.py`
- `scripts/transcribe_sravaani_drafts.py`
- `scripts/transcribe_vaani_drafts.py`
- `scripts/transcribe_whisper_agreement.py`
- `scripts/validate_benchmark_v02.py`
- `scripts/validate_hf_package_cloud.py`
- `scripts/validate_ocr_corrections.py`
- `scripts/validate_release_index.py`
- `scripts/verify_ingestion.py`
- `scripts/verify_vaani_collection.py`
- `scripts/wikitext_plain.py`

## `sources/`

- `sources/manual/garhwali-literature-writers-2026-09-16.md`
- `sources/online/README.md`
- `sources/online/deep-search-catalog.md`
- `sources/online/source-audit-2026-09-08.md`
- `sources/online/source-freshness-baseline.json`

## `tasks/`

- `tasks/lessons.md`
- `tasks/todo.md`

## `tests/`

- `tests/__init__.py`
- `tests/test_analyze_generation_output_diagnostics.py`
- `tests/test_analyze_retrieval_cluster_uncertainty.py`
- `tests/test_analyze_retrieval_misses.py`
- `tests/test_analyze_saved_asr_validation.py`
- `tests/test_analyze_sravaani_drafts.py`
- `tests/test_analyze_translation_uncertainty.py`
- `tests/test_archive_alternate_ocr_overlap.py`
- `tests/test_archive_book_page_map.py`
- `tests/test_archive_priority_page_evidence.py`
- `tests/test_asr_metrics.py`
- `tests/test_asr_requirements.py`
- `tests/test_audit_archive_corpus_overlap.py`
- `tests/test_audit_archive_intake_quality.py`
- `tests/test_audit_archive_media_first_pass.py`
- `tests/test_audit_audio_quality.py`
- `tests/test_audit_benchmark_nested_overlap.py`
- `tests/test_audit_benchmark_overlap_candidates.py`
- `tests/test_audit_benchmark_v02_rights.py`
- `tests/test_audit_final_release.py`
- `tests/test_audit_garhwali_expansion.py`
- `tests/test_audit_hf_release_continuity.py`
- `tests/test_audit_hf_source_lineage.py`
- `tests/test_audit_hf_training_eligibility.py`
- `tests/test_audit_indicbert_cloud_input.py`
- `tests/test_audit_model_accuracy_lineage.py`
- `tests/test_audit_multilingual_tokenizers.py`
- `tests/test_audit_saved_asr_heldout_lineage.py`
- `tests/test_audit_semantic_duplicates.py`
- `tests/test_audit_text_sources.py`
- `tests/test_audit_upstream_split_overlap.py`
- `tests/test_audit_vaani_official_split_lineage.py`
- `tests/test_audit_xorqa_source_page_families.py`
- `tests/test_benchmark_metrics.py`
- `tests/test_build_archive_source_disposition.py`
- `tests/test_build_asr_training_curriculum.py`
- `tests/test_build_audio_training_manifests.py`
- `tests/test_build_benchmark_usage_labels.py`
- `tests/test_build_benchmark_v02.py`
- `tests/test_build_dataset_splits.py`
- `tests/test_build_garhwali_benchmark.py`
- `tests/test_build_hf_reference_index.py`
- `tests/test_build_hf_upload_plan.py`
- `tests/test_build_huggingface_dataset.py`
- `tests/test_build_instruction_accuracy_split.py`
- `tests/test_build_instruction_dataset.py`
- `tests/test_build_language_resources.py`
- `tests/test_build_quality_tiers.py`
- `tests/test_build_recommended_text_view.py`
- `tests/test_build_release_bundle.py`
- `tests/test_build_release_manifest.py`
- `tests/test_build_sravaani_audio_grounded_review.py`
- `tests/test_build_sravaani_recovery_adjudication.py`
- `tests/test_build_vaani_corpus_manifests.py`
- `tests/test_build_vaani_source_conflicts.py`
- `tests/test_calibrate_sravaani_recovery_confidence.py`
- `tests/test_check_source_freshness.py`
- `tests/test_clean_text_corpus.py`
- `tests/test_collect_online.py`
- `tests/test_compare_archive_ocr_variants.py`
- `tests/test_compare_asr_predictions.py`
- `tests/test_compare_hf_release_metrics.py`
- `tests/test_deep_cleanup.py`
- `tests/test_evaluate_indicbert_transfer.py`
- `tests/test_evaluate_sravaani_finetune.py`
- `tests/test_evaluation_run_manifest.py`
- `tests/test_export_licensed_sources.py`
- `tests/test_generate_project_file_map.py`
- `tests/test_hf_meta_omni_schema.py`
- `tests/test_hf_meta_omni_speech.py`
- `tests/test_hf_speech_release.py`
- `tests/test_ingest_garhwali_language_library.py`
- `tests/test_ingest_geography.py`
- `tests/test_ingest_historical_terms.py`
- `tests/test_ingest_incoming_pdfs.py`
- `tests/test_ingest_jambu_garhwali.py`
- `tests/test_ingest_literary_people.py`
- `tests/test_ingest_literary_works.py`
- `tests/test_ingest_lsi_garhwali_specimens.py`
- `tests/test_ingest_lsi_garhwali_table.py`
- `tests/test_ingest_obs_tlf.py`
- `tests/test_ingest_open.py`
- `tests/test_ingest_popular_songs.py`
- `tests/test_ingest_university_research.py`
- `tests/test_ingest_upreti_1894_garhwali.py`
- `tests/test_ingest_web_goldmines.py`
- `tests/test_ingest_web_learning.py`
- `tests/test_ingestion_graph.py`
- `tests/test_integrate_release_evidence.py`
- `tests/test_integrate_sravaani_confidence.py`
- `tests/test_manifest_saved_generation_validation.py`
- `tests/test_native_review_workflow.py`
- `tests/test_ocr_uou_more.py`
- `tests/test_prepare_audio_normalization.py`
- `tests/test_prepare_hf_additive_upload.py`
- `tests/test_prepare_indicbert_pdf_domain.py`
- `tests/test_prepare_meta_omnilingual_asr.py`
- `tests/test_prepare_sravaani_expanded_finetune.py`
- `tests/test_prepare_sravaani_finetune.py`
- `tests/test_prepare_text_corpus.py`
- `tests/test_prepare_transcripts.py`
- `tests/test_prepare_vaani_supervised.py`
- `tests/test_prepare_whisper_compatible_manifests.py`
- `tests/test_propose_text_cleanup.py`
- `tests/test_record_schema.py`
- `tests/test_redecode_sravaani_recovery.py`
- `tests/test_redecode_supervised_review.py`
- `tests/test_refine_priority_text.py`
- `tests/test_refresh_corpus_after_ingestion.py`
- `tests/test_register_asr_stage0.py`
- `tests/test_register_asr_stage1_pilot.py`
- `tests/test_register_asr_stage1_weighted_batch_pilot.py`
- `tests/test_render_normalized_audio.py`
- `tests/test_reocr_archive_quality_pages.py`
- `tests/test_reprocess_ocr_candidates.py`
- `tests/test_route_sravaani_recovery.py`
- `tests/test_run_indicbert_adaptation.py`
- `tests/test_run_indicbert_lora_adaptation.py`
- `tests/test_run_indicbert_retrieval_baseline.py`
- `tests/test_run_masked_lm_baseline.py`
- `tests/test_run_mt5_instruction_tuning.py`
- `tests/test_run_nllb_translation_baseline.py`
- `tests/test_run_retrieval_baseline.py`
- `tests/test_run_sravaani_comparison.py`
- `tests/test_run_text_cleanup_ablation.py`
- `tests/test_run_text_scaling_experiment.py`
- `tests/test_run_translation_baseline.py`
- `tests/test_run_whisper_comparison.py`
- `tests/test_score_benchmark_predictions.py`
- `tests/test_search_garhwali_lexicon.py`
- `tests/test_segment_long_audio.py`
- `tests/test_segment_text_corpus.py`
- `tests/test_sweep_sravaani_decoding.py`
- `tests/test_sweep_sravaani_garhwali.py`
- `tests/test_sync_release_index.py`
- `tests/test_tag_language_quality.py`
- `tests/test_train_sravaani_garhwali.py`
- `tests/test_train_whisper_garhwali.py`
- `tests/test_transcribe_vaani_drafts.py`
- `tests/test_transcribe_whisper_agreement.py`
- `tests/test_validate_benchmark_v02.py`
- `tests/test_validate_hf_package_cloud.py`
- `tests/test_validate_ocr_corrections.py`
- `tests/test_validate_release_index.py`
- `tests/test_verify_ingestion.py`
- `tests/test_wikitext_plain.py`

## Workspace payload inventory

The detailed index above lists all tracked and non-ignored files. This inventory also accounts for ignored/generated files without copying a 226,000-plus-row binary-path dump into the Markdown map.

- Workspace files counted: **239,390**.
- Excluded from the count: Git internals, virtual environments, and runtime caches.
- Detailed file paths listed above: **1,022**.
- Ignored or otherwise unlisted payload files: **238,368** (172,460,415,751 bytes).
- Total workspace bytes counted: **172,478,519,362**.

| Payload directory | Files | Bytes |
| --- | ---: | ---: |
| `.superpowers/sdd/…/` | 9 | 13,679 |
| `Root-level payloads` | 1 | 77 |
| `benchmarks/indicgenbench_crosssum.jsonl/` | 1 | 4,698,112 |
| `benchmarks/indicgenbench_flores.jsonl/` | 1 | 5,242,368 |
| `benchmarks/indicgenbench_xorqa.jsonl/` | 1 | 3,092,221 |
| `corpus/asjp.jsonl/` | 1 | 78,762 |
| `corpus/chan_numerals_garhwali.jsonl/` | 1 | 54,508 |
| `corpus/garhwali_language_library.jsonl/` | 1 | 304,351 |
| `corpus/incubator_wt.jsonl/` | 1 | 10,768 |
| `corpus/jambu_garhwali.jsonl/` | 1 | 1,292,863 |
| `corpus/mamta_southasia_examples.jsonl/` | 1 | 91,753 |
| `corpus/meta_omni.jsonl/` | 1 | 8,399,925 |
| `corpus/opus_translatewiki_gbm.jsonl/` | 1 | 320,301 |
| `corpus/sand_garhwali.jsonl/` | 1 | 213,000 |
| `corpus/tatoeba.jsonl/` | 1 | 43,662 |
| `corpus/wikimedia.jsonl/` | 1 | 124,714 |
| `corpus/wiktionary_en.jsonl/` | 1 | 164,557 |
| `data/cache/…/` | 2 | 104,176 |
| `data/downloads/…/` | 1,136 | 9,350,565,536 |
| `data/extracted/…/` | 736 | 104,222,678 |
| `data/huggingface/…/` | 2,914 | 87,100,082,741 |
| `data/processed/…/` | 110,561 | 41,807,390,124 |
| `data/raw/…/` | 1 | 21,905 |
| `data/temp/…/` | 1 | 39,533 |
| `data/vaani/…/` | 115,189 | 32,112,461,505 |
| `experimental/dcad_gbm.jsonl/` | 1 | 2,405,996 |
| `experimental/garhwali_web_goldmines.jsonl/` | 1 | 23,532,696 |
| `experimental/hikinegi_garhwali.jsonl/` | 1 | 83,393 |
| `experimental/incoming_pdfs.jsonl/` | 1 | 5,787,773 |
| `experimental/indic_dialect_asr_gbm.jsonl/` | 1 | 58,611,938 |
| `experimental/madlad400_gbm_clean.jsonl/` | 1 | 360,489 |
| `experimental/paharili_gbm.jsonl/` | 1 | 26,926,978 |
| `experimental/web_learning_garhwali.jsonl/` | 1 | 159,991 |
| `extracted/historical/…/` | 8 | 7,732,983 |
| `incoming/pdfs/…/` | 7 | 165,313,272 |
| `models/controlled_modeling/…/` | 39 | 17,979,528 |
| `models/whisper-tiny-garhwali-curriculum-stage-1-pilot-h32-m2048-weighted-batches/…/` | 9 | 155,181,608 |
| `models/whisper-tiny-garhwali-curriculum-stage-1-pilot-h32-m2048/…/` | 9 | 155,180,855 |
| `models/whisper-tiny-garhwali-meta-multiseed-17/…/` | 9 | 155,447,974 |
| `models/whisper-tiny-garhwali-meta-multiseed-29/…/` | 9 | 155,447,974 |
| `models/whisper-tiny-garhwali-smoke/…/` | 9 | 155,001,786 |
| `models/whisper-tiny-garhwali-v0.1/…/` | 9 | 155,076,358 |
| `models/whisper-tiny-garhwali-v0.2/…/` | 10 | 155,077,066 |
| `outputs/garhwali-corpus-inventory-2026-09-07/…/` | 6 | 1,901,768 |
| `outputs/online-ingestion-2026-09-07/…/` | 3 | 531,867 |
| `research/model-accuracy-lineage-2026-09-24.json/` | 1 | 15,995,502 |
| `restricted/archive_folksong_thesis.jsonl/` | 1 | 7,498 |
| `restricted/hindialect_gbm.jsonl/` | 1 | 1,025,826 |
| `restricted/obs_garhwali.jsonl/` | 1 | 835,004 |
| `restricted/panlex_gbm.jsonl/` | 1 | 18,515 |
| `restricted/thematic_web_lexicon.jsonl/` | 1 | 959,665 |
| `restricted/uou_cgl_pages.jsonl/` | 1 | 4,087,789 |
| `restricted/uou_cgl_report.json/` | 1 | 148 |
| `restricted/uou_more_pages.jsonl/` | 1 | 1,754,652 |
| `restricted/uou_more_report.json/` | 1 | 284 |
| `sources/online/…/` | 747 | 520,948,495 |
| `sources/web/…/` | 8 | 130,802 |
| `tmp/incoming-pdf-reocr-full.log/` | 1 | 461 |
| `tmp/incoming-pdf-reocr-full.pid/` | 1 | 6 |
| `tmp/pdfs/…/` | 6,901 | 17,874,992 |
