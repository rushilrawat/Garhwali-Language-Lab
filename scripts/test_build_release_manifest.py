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
                'data/processed/model_ready/transcripts/sravaani_recovery_adjudication_report.json': {
                    'run_id': 'sravaani-adjudication-test',
                    'records': 1090,
                },
                'data/processed/model_ready/asr_curriculum/trainer_dry_run_report.json': {
                    'run_id': 'asr-curriculum-dry-run-test',
                    'status': 'passed',
                },
                'data/processed/evaluation/asr/curriculum_stage_0/report.json': {
                    'run_id': 'asr-stage-0-test',
                    'selected_checkpoint': 'whisper_tiny_v0.2',
                },
                'data/processed/evaluation/asr/curriculum_stage_1_pilot/report.json': {
                    'run_id': 'asr-stage-1-pilot-test',
                    'comparison': {'decision': 'rejected'},
                },
                'data/processed/evaluation/asr/curriculum_stage_1_weighted_batch_pilot/report.json': {
                    'run_id': 'asr-stage-1-weighted-batch-pilot-test',
                    'decision': 'rejected',
                },
                'data/processed/model_ready/sravaani_finetune/report.json': {
                    'run_id': 'sravaani-finetune-package-test',
                    'package_status': 'ready_for_nemo_cuda_training',
                },
                'data/processed/evaluation/asr/sravaani_finetune/plan.json': {
                    'run_id': 'sravaani-finetune-plan-test',
                    'external_dependencies': {
                        'status': 'blocked_external_dependencies',
                    },
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
            adjudication_path = root / 'data/processed/model_ready/transcripts/sravaani_recovery_adjudication.jsonl'
            adjudication_path.parent.mkdir(parents=True, exist_ok=True)
            adjudication_path.write_text('{}\n', encoding='utf-8')

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
            self.assertEqual(
                manifest['sravaani_recovery_adjudication_report']['records'], 1090
            )
            self.assertEqual(
                manifest['asr_curriculum_trainer_dry_run']['status'],
                'passed',
            )
            self.assertEqual(
                manifest['asr_curriculum_stage0_report']['selected_checkpoint'],
                'whisper_tiny_v0.2',
            )
            self.assertEqual(
                manifest['asr_curriculum_stage1_pilot_report']['comparison']['decision'],
                'rejected',
            )
            self.assertEqual(
                manifest['asr_curriculum_stage1_weighted_batch_pilot_report']['decision'],
                'rejected',
            )
            self.assertEqual(
                manifest['sravaani_finetune_package_report']['package_status'],
                'ready_for_nemo_cuda_training',
            )
            self.assertEqual(
                manifest['sravaani_finetune_plan']['external_dependencies']['status'],
                'blocked_external_dependencies',
            )
            self.assertEqual(manifest['files']['asr_curriculum_train']['records'], 2)
            self.assertEqual(
                manifest['files']['vaani_sravaani_recovery_adjudication']['records'], 1
            )
            self.assertIn('vaani_sravaani_transcript_drafts', manifest['experimental_views'])
            self.assertIn('vaani_sravaani_transcript_quality', manifest['experimental_views'])
            self.assertIn('asr_curriculum_train', manifest['experimental_views'])
            self.assertIn(
                'vaani_sravaani_recovery_adjudication', manifest['experimental_views']
            )


if __name__ == '__main__':
    unittest.main()
