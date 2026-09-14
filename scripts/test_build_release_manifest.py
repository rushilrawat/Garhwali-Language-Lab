import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import build_release_manifest as m


class ReleaseManifestTests(unittest.TestCase):
    def test_manifest_includes_dataset_split_report_and_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = {
                'data/processed/text/report.json': {'unique_texts': 1},
                'data/processed/vaani/report.json': {'supervised_rows': 1},
                'data/processed/audio/report.json': {'records': 1},
                'data/processed/model_ready/splits/report.json': {
                    'release_id': 'candidate-splits',
                    'leakage_checks': {'text_hash_cross_split': 0},
                },
                'data/processed/model_ready/language_resources/report.json': {'tokenizer_vocabulary_size': 332},
                'data/processed/native_review/results/report.json': {'adjudicated': 0},
                'data/processed/long_form_audio/report.json': {'clips': 3},
                'data/processed/evaluation/garhwali_bench/manifest.json': {
                    'release_id': 'garhwali-bench-test',
                    'records': {'external_total': 3},
                },
                'data/processed/evaluation/model_audit/tokenizer_report.json': {
                    'audit_id': 'tokenizers-test',
                },
                'data/processed/evaluation/model_audit/indicbertv2_masked_lm.json': {
                    'run_id': 'masked-lm-test',
                },
                'data/processed/evaluation/translation/report.json': {
                    'run_id': 'translation-floors-test',
                },
                'data/processed/evaluation/translation/nllb_hindi_proxy/report.json': {
                    'run_id': 'nllb-base-test',
                },
                'data/processed/evaluation/translation/nllb_garhwali_adapter_hindi_proxy/report.json': {
                    'run_id': 'nllb-adapter-test',
                },
                'data/processed/evaluation/retrieval/report.json': {
                    'run_id': 'retrieval-floors-test',
                },
                'data/processed/evaluation/retrieval/indicbertv2/report.json': {
                    'run_id': 'retrieval-indicbert-test',
                },
                'data/processed/evaluation/asr/whisper_tiny_zero_shot/report.json': {
                    'run_id': 'whisper-tiny-zero-shot-test',
                },
                'data/processed/evaluation/asr/whisper_small_zero_shot/report.json': {
                    'run_id': 'whisper-small-zero-shot-test',
                },
                'data/processed/model_ready/asr_curriculum/report.json': {
                    'run_id': 'asr-curriculum-test',
                },
                'models/whisper-tiny-garhwali-v0.1/report.json': {'wer': 0.79},
                'models/whisper-tiny-garhwali-v0.2/report.json': {'wer': 0.74},
            }
            for relative, payload in reports.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(payload), encoding='utf-8')
            split_path = root / 'data/processed/model_ready/splits/text/train.jsonl'
            split_path.parent.mkdir(parents=True, exist_ok=True)
            split_path.write_text('{"segment_sha256":"abc"}\n', encoding='utf-8')
            normalized_path = root / 'data/processed/model_ready/audio_normalized/manifests/train.jsonl'
            normalized_path.parent.mkdir(parents=True, exist_ok=True)
            normalized_path.write_text('{"derived_audio_sha256":"def"}\n', encoding='utf-8')
            long_form_path = root / 'data/processed/long_form_audio/manifest.jsonl'
            long_form_path.parent.mkdir(parents=True, exist_ok=True)
            long_form_path.write_text('{}\n{}\n{}\n', encoding='utf-8')
            curriculum_path = root / 'data/processed/model_ready/asr_curriculum/train.jsonl'
            curriculum_path.parent.mkdir(parents=True, exist_ok=True)
            curriculum_path.write_text('{}\n{}\n', encoding='utf-8')

            with patch.object(m, 'ROOT', root):
                with redirect_stdout(io.StringIO()):
                    m.main()

            manifest = json.loads((root / 'data/processed/release/manifest.json').read_text())
            self.assertEqual(manifest['dataset_split_report']['release_id'], 'candidate-splits')
            self.assertEqual(manifest['files']['split_text_train']['records'], 1)
            self.assertEqual(manifest['files']['audio_normalized_train']['records'], 1)
            self.assertEqual(manifest['files']['long_form_audio_segments']['records'], 3)
            self.assertEqual(manifest['language_resources_report']['tokenizer_vocabulary_size'], 332)
            self.assertEqual(manifest['long_form_audio_report']['clips'], 3)
            self.assertEqual(manifest['garhwali_benchmark_report']['release_id'], 'garhwali-bench-test')
            self.assertEqual(manifest['multilingual_tokenizer_audit']['audit_id'], 'tokenizers-test')
            self.assertEqual(manifest['indicbertv2_masked_lm_report']['run_id'], 'masked-lm-test')
            self.assertEqual(manifest['translation_floor_report']['run_id'], 'translation-floors-test')
            self.assertEqual(manifest['nllb_translation_report']['run_id'], 'nllb-base-test')
            self.assertEqual(manifest['nllb_adapter_report']['run_id'], 'nllb-adapter-test')
            self.assertEqual(manifest['retrieval_floor_report']['run_id'], 'retrieval-floors-test')
            self.assertEqual(manifest['indicbertv2_retrieval_report']['run_id'], 'retrieval-indicbert-test')
            self.assertEqual(manifest['whisper_tiny_zero_shot_report']['run_id'], 'whisper-tiny-zero-shot-test')
            self.assertEqual(manifest['whisper_small_zero_shot_report']['run_id'], 'whisper-small-zero-shot-test')
            self.assertEqual(manifest['asr_finetune_report']['wer'], 0.74)
            self.assertEqual(
                manifest['asr_training_curriculum_report']['run_id'],
                'asr-curriculum-test',
            )
            self.assertEqual(manifest['files']['asr_curriculum_train']['records'], 2)
            self.assertIn('vaani_sravaani_transcript_drafts', manifest['experimental_views'])
            self.assertIn('vaani_sravaani_transcript_quality', manifest['experimental_views'])
            self.assertIn('asr_curriculum_train', manifest['experimental_views'])


if __name__ == '__main__':
    unittest.main()
