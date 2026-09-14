#!/usr/bin/env python3
"""Create a compact manifest for the current reproducible corpus release."""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def line_count(path):
    with path.open(encoding='utf-8') as f:
        return sum(1 for line in f if line.strip())

def read_optional_json(path):
    return json.loads(path.read_text()) if path.exists() else None

def main():
    text_report = json.loads((ROOT/'data/processed/text/report.json').read_text())
    vaani_report = json.loads((ROOT/'data/processed/vaani/report.json').read_text())
    audio_report = json.loads((ROOT/'data/processed/audio/report.json').read_text())
    dataset_split_report = json.loads((ROOT/'data/processed/model_ready/splits/report.json').read_text())
    language_resources_report = read_optional_json(ROOT/'data/processed/model_ready/language_resources/report.json')
    native_review_report = read_optional_json(ROOT/'data/processed/native_review/results/report.json')
    long_form_audio_report = read_optional_json(ROOT/'data/processed/long_form_audio/report.json')
    garhwali_benchmark_report = read_optional_json(
        ROOT/'data/processed/evaluation/garhwali_bench/manifest.json'
    )
    multilingual_tokenizer_audit = read_optional_json(
        ROOT/'data/processed/evaluation/model_audit/tokenizer_report.json'
    )
    indicbertv2_masked_lm_report = read_optional_json(
        ROOT/'data/processed/evaluation/model_audit/indicbertv2_masked_lm.json'
    )
    translation_floor_report = read_optional_json(
        ROOT/'data/processed/evaluation/translation/report.json'
    )
    nllb_translation_report = read_optional_json(
        ROOT/'data/processed/evaluation/translation/nllb_hindi_proxy/report.json'
    )
    nllb_adapter_report = read_optional_json(
        ROOT/'data/processed/evaluation/translation/nllb_garhwali_adapter_hindi_proxy/report.json'
    )
    retrieval_floor_report = read_optional_json(
        ROOT/'data/processed/evaluation/retrieval/report.json'
    )
    indicbertv2_retrieval_report = read_optional_json(
        ROOT/'data/processed/evaluation/retrieval/indicbertv2/report.json'
    )
    whisper_tiny_zero_shot_report = read_optional_json(
        ROOT/'data/processed/evaluation/asr/whisper_tiny_zero_shot/report.json'
    )
    whisper_small_zero_shot_report = read_optional_json(
        ROOT/'data/processed/evaluation/asr/whisper_small_zero_shot/report.json'
    )
    sravaani_report = read_optional_json(
        ROOT/'data/processed/evaluation/asr/sravaani_1_0/report.json'
    )
    sravaani_draft_quality_report = read_optional_json(
        ROOT/'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality_report.json'
    )
    sravaani_confidence_integration_report = read_optional_json(
        ROOT/'data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware_report.json'
    )
    asr_training_curriculum_report = read_optional_json(
        ROOT/'data/processed/model_ready/asr_curriculum/report.json'
    )
    asr_curriculum_trainer_dry_run = read_optional_json(
        ROOT/'data/processed/model_ready/asr_curriculum/trainer_dry_run_report.json'
    )
    asr_curriculum_stage0_report = read_optional_json(
        ROOT/'data/processed/evaluation/asr/curriculum_stage_0/report.json'
    )
    asr_curriculum_stage1_pilot_report = read_optional_json(
        ROOT/'data/processed/evaluation/asr/curriculum_stage_1_pilot/report.json'
    )
    asr_curriculum_stage1_weighted_batch_pilot_report = read_optional_json(
        ROOT/'data/processed/evaluation/asr/curriculum_stage_1_weighted_batch_pilot/report.json'
    )
    asr_finetune_report = (
        read_optional_json(ROOT/'models/whisper-tiny-garhwali-v0.2/report.json')
        or read_optional_json(ROOT/'models/whisper-tiny-garhwali-v0.1/report.json')
    )
    files = {
      'text_canonical': 'data/processed/text/canonical.jsonl',
      'text_all_experimental': 'data/processed/text/all_garhwali.jsonl',
      'text_cleaned_all': 'data/processed/text/cleaned_all_garhwali.jsonl',
      'paharili_garhwali': 'data/processed/text/paharili_garhwali.jsonl',
      'vaani_supervised': 'data/processed/vaani/supervised.jsonl',
      'vaani_untranscribed': 'data/processed/vaani/untranscribed.jsonl',
      'vaani_experimental_review': 'data/processed/vaani/experimental_review.jsonl',
      'audio_quality': 'data/processed/audio/quality.jsonl',
      'audio_supervised_model_ready': 'data/processed/model_ready/audio/supervised_all.jsonl',
      'audio_untranscribed_model_ready': 'data/processed/model_ready/audio/untranscribed_all.jsonl',
      'transcripts_supervised_model_ready': 'data/processed/model_ready/transcripts/supervised.jsonl',
      'transcripts_untranscribed_queue': 'data/processed/model_ready/transcripts/untranscribed_queue.jsonl',
      'deep_cleaned_text': 'data/processed/model_ready/cleaned/text.jsonl',
      'deep_cleaned_audio_transcripts': 'data/processed/model_ready/cleaned/audio_transcripts.jsonl',
      'text_segments_all': 'data/processed/model_ready/segments/all_segments.jsonl',
      'audio_normalization_plan': 'data/processed/model_ready/audio/normalization.jsonl',
      'web_learning_experimental': 'experimental/web_learning_garhwali.jsonl',
      'language_quality_text_all': 'data/processed/model_ready/language_quality/text.jsonl',
      'language_quality_text_garhwali_candidates': 'data/processed/model_ready/language_quality/text_garhwali_candidates.jsonl',
      'language_quality_text_mixed': 'data/processed/model_ready/language_quality/text_mixed_language.jsonl',
      'language_quality_text_review': 'data/processed/model_ready/language_quality/text_language_review.jsonl',
      'language_quality_non_garhwali_context': 'data/processed/model_ready/language_quality/text_non_garhwali_context.jsonl',
      'language_quality_audio_supervised': 'data/processed/model_ready/language_quality/audio_supervised.jsonl',
      'language_quality_audio_untranscribed': 'data/processed/model_ready/language_quality/audio_untranscribed.jsonl',
      'language_quality_lexicon_candidates': 'data/processed/model_ready/language_quality/lexicon_candidates.jsonl',
      'language_quality_parallel_examples': 'data/processed/model_ready/language_quality/parallel_examples.jsonl',
      'language_quality_grammar_sources': 'data/processed/model_ready/language_quality/grammar_source_candidates.jsonl',
      'asr_finetuning_train': 'data/processed/model_ready/asr_finetuning/train.jsonl',
      'asr_finetuning_validation': 'data/processed/model_ready/asr_finetuning/validation.jsonl',
      'asr_finetuning_test': 'data/processed/model_ready/asr_finetuning/test.jsonl',
      'asr_baseline_predictions': 'data/processed/evaluation/asr/baseline_predictions.jsonl',
      'split_text_train': 'data/processed/model_ready/splits/text/train.jsonl',
      'split_text_validation': 'data/processed/model_ready/splits/text/validation.jsonl',
      'split_text_test': 'data/processed/model_ready/splits/text/test.jsonl',
      'split_asr_train': 'data/processed/model_ready/splits/asr/train.jsonl',
      'split_asr_validation': 'data/processed/model_ready/splits/asr/validation.jsonl',
      'split_asr_test': 'data/processed/model_ready/splits/asr/test.jsonl',
      'split_tts_train': 'data/processed/model_ready/splits/tts/train.jsonl',
      'split_tts_validation': 'data/processed/model_ready/splits/tts/validation.jsonl',
      'split_tts_test': 'data/processed/model_ready/splits/tts/test.jsonl',
      'split_asr_experimental_train': 'data/processed/model_ready/splits/asr_experimental/train.jsonl',
      'split_asr_experimental_validation': 'data/processed/model_ready/splits/asr_experimental/validation.jsonl',
      'split_asr_experimental_test': 'data/processed/model_ready/splits/asr_experimental/test.jsonl',
      'split_tts_experimental_train': 'data/processed/model_ready/splits/tts_experimental/train.jsonl',
      'split_tts_experimental_validation': 'data/processed/model_ready/splits/tts_experimental/validation.jsonl',
      'split_tts_experimental_test': 'data/processed/model_ready/splits/tts_experimental/test.jsonl',
      'split_text_evaluation_candidate': 'data/processed/model_ready/splits/evaluation/text_candidate.jsonl',
      'split_asr_evaluation_candidate': 'data/processed/model_ready/splits/evaluation/asr_candidate.jsonl',
      'audio_normalized_train': 'data/processed/model_ready/audio_normalized/manifests/train.jsonl',
      'audio_normalized_validation': 'data/processed/model_ready/audio_normalized/manifests/validation.jsonl',
      'audio_normalized_test': 'data/processed/model_ready/audio_normalized/manifests/test.jsonl',
      'audio_normalization_requires_review': 'data/processed/model_ready/audio_normalized/requires_review.jsonl',
      'audio_normalized_review_copies': 'data/processed/model_ready/audio_normalized/review_manifest.jsonl',
      'pronunciation_candidates': 'data/processed/model_ready/language_resources/pronunciation/lexicon.jsonl',
      'tts_pairs_train': 'data/processed/model_ready/language_resources/tts/train.jsonl',
      'tts_pairs_validation': 'data/processed/model_ready/language_resources/tts/validation.jsonl',
      'tts_pairs_test': 'data/processed/model_ready/language_resources/tts/test.jsonl',
      'native_review_adjudicated': 'data/processed/native_review/results/adjudicated.jsonl',
      'native_review_disagreements': 'data/processed/native_review/results/disagreements.jsonl',
      'long_form_audio_segments': 'data/processed/long_form_audio/manifest.jsonl',
      'asr_finetune_predictions': 'models/whisper-tiny-garhwali-v0.2/evaluation_predictions.jsonl',
      'vaani_machine_transcript_drafts': 'data/processed/model_ready/transcripts/machine_drafts.jsonl',
      'vaani_sravaani_transcript_drafts': 'data/processed/model_ready/transcripts/machine_drafts_sravaani.jsonl',
      'vaani_sravaani_transcript_quality': 'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality.jsonl',
      'vaani_sravaani_confidence_aware': 'data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl',
      'asr_curriculum_train': 'data/processed/model_ready/asr_curriculum/train.jsonl',
      'asr_curriculum_validation': 'data/processed/model_ready/asr_curriculum/validation.jsonl',
      'asr_curriculum_test': 'data/processed/model_ready/asr_curriculum/test.jsonl',
      'asr_curriculum_stage_plan': 'data/processed/model_ready/asr_curriculum/stage_plan.json',
    }
    entries = {}
    for name, rel in files.items():
        path = ROOT/rel
        entries[name] = {'path': rel, 'exists': path.exists(), 'records': line_count(path) if path.exists() else None}
    manifest = {
      'release_id': 'garhwali-preparation-2026-09-11',
      'generated': date.today().isoformat(),
      'language': 'Garhwali (gbm)',
      'text_report': text_report,
      'vaani_report': vaani_report,
      'audio_report': audio_report,
      'dataset_split_report': dataset_split_report,
      'language_resources_report': language_resources_report,
      'native_review_report': native_review_report,
      'long_form_audio_report': long_form_audio_report,
      'garhwali_benchmark_report': garhwali_benchmark_report,
      'multilingual_tokenizer_audit': multilingual_tokenizer_audit,
      'indicbertv2_masked_lm_report': indicbertv2_masked_lm_report,
      'translation_floor_report': translation_floor_report,
      'nllb_translation_report': nllb_translation_report,
      'nllb_adapter_report': nllb_adapter_report,
      'retrieval_floor_report': retrieval_floor_report,
      'indicbertv2_retrieval_report': indicbertv2_retrieval_report,
      'whisper_tiny_zero_shot_report': whisper_tiny_zero_shot_report,
      'whisper_small_zero_shot_report': whisper_small_zero_shot_report,
      'sravaani_report': sravaani_report,
      'sravaani_draft_quality_report': sravaani_draft_quality_report,
      'sravaani_confidence_integration_report': sravaani_confidence_integration_report,
      'asr_training_curriculum_report': asr_training_curriculum_report,
      'asr_curriculum_trainer_dry_run': asr_curriculum_trainer_dry_run,
      'asr_curriculum_stage0_report': asr_curriculum_stage0_report,
      'asr_curriculum_stage1_pilot_report': asr_curriculum_stage1_pilot_report,
      'asr_curriculum_stage1_weighted_batch_pilot_report': (
          asr_curriculum_stage1_weighted_batch_pilot_report
      ),
      'asr_finetune_report': asr_finetune_report,
      'files': entries,
      'raw_data_policy': 'raw downloads and caches remain gitignored',
      'experimental_views': [
        'text_all_experimental',
        'paharili_garhwali',
        'split_asr_experimental_train',
        'split_asr_experimental_validation',
        'split_asr_experimental_test',
        'split_tts_experimental_train',
        'split_tts_experimental_validation',
        'split_tts_experimental_test',
        'vaani_untranscribed',
        'vaani_machine_transcript_drafts',
        'vaani_sravaani_transcript_drafts',
        'vaani_sravaani_transcript_quality',
        'vaani_sravaani_confidence_aware',
        'asr_curriculum_train',
      ],
    }
    out = ROOT/'data/processed/release'; out.mkdir(parents=True, exist_ok=True)
    (out/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))

if __name__ == '__main__': main()
