#!/usr/bin/env python3
"""Create a compact manifest for the current reproducible corpus release."""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def line_count(path):
    with path.open(encoding='utf-8') as f:
        return sum(1 for line in f if line.strip())

def main():
    text_report = json.loads((ROOT/'data/processed/text/report.json').read_text())
    vaani_report = json.loads((ROOT/'data/processed/vaani/report.json').read_text())
    audio_report = json.loads((ROOT/'data/processed/audio/report.json').read_text())
    files = {
      'text_canonical': 'data/processed/text/canonical.jsonl',
      'text_all_experimental': 'data/processed/text/all_garhwali.jsonl',
      'text_cleaned_all': 'data/processed/text/cleaned_all_garhwali.jsonl',
      'paharili_garhwali': 'data/processed/text/paharili_garhwali.jsonl',
      'vaani_supervised': 'data/processed/vaani/supervised.jsonl',
      'vaani_untranscribed': 'data/processed/vaani/untranscribed.jsonl',
      'vaani_quarantine': 'data/processed/vaani/quarantine.jsonl',
      'audio_quality': 'data/processed/audio/quality.jsonl',
      'audio_supervised_model_ready': 'data/processed/model_ready/audio/supervised_all.jsonl',
      'audio_untranscribed_model_ready': 'data/processed/model_ready/audio/untranscribed_all.jsonl',
      'transcripts_supervised_model_ready': 'data/processed/model_ready/transcripts/supervised.jsonl',
      'transcripts_untranscribed_queue': 'data/processed/model_ready/transcripts/untranscribed_queue.jsonl',
      'deep_cleaned_text': 'data/processed/model_ready/cleaned/text.jsonl',
      'deep_cleaned_audio_transcripts': 'data/processed/model_ready/cleaned/audio_transcripts.jsonl',
      'text_segments_all': 'data/processed/model_ready/segments/all_segments.jsonl',
      'audio_normalization_plan': 'data/processed/model_ready/audio/normalization.jsonl',
      'web_learning_quarantine': 'quarantine/web_learning_garhwali.jsonl',
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
    }
    entries = {}
    for name, rel in files.items():
        path = ROOT/rel
        entries[name] = {'path': rel, 'exists': path.exists(), 'records': line_count(path) if path.exists() else None}
    manifest = {
      'release_id': 'garhwali-preparation-2026-09-10',
      'generated': date.today().isoformat(),
      'language': 'Garhwali (gbm)',
      'text_report': text_report,
      'vaani_report': vaani_report,
      'audio_report': audio_report,
      'files': entries,
      'raw_data_policy': 'raw downloads and caches remain gitignored',
      'experimental_views': ['text_all_experimental', 'paharili_garhwali'],
    }
    out = ROOT/'data/processed/release'; out.mkdir(parents=True, exist_ok=True)
    (out/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))

if __name__ == '__main__': main()
