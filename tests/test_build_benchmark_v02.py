import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build_benchmark_v02 import (
    adapt_record,
    build_export_from_views,
    metric_contracts,
    validate_export_artifacts,
)


def sha(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class BuildBenchmarkV02Tests(unittest.TestCase):
    def test_external_record_keeps_original_and_scoring_text_separate(self):
        row = {
            'record_id': 'flores:test:1',
            'split': 'test',
            'text_original': ' का पाठ ',
            'text_normalized': 'का पाठ',
            'text_sha256': sha('का पाठ'),
            'iso_639_3': 'gbm',
            'script': 'Deva',
            'source_id': 'flores',
            'attribution': 'source attribution',
            'license_id': 'CC-BY-4.0',
            'license_url': 'https://example.test/license',
            'rights_status': 'upstream_declared_license; review_before_redistribution',
            'training_eligible': False,
            'usage': 'evaluation_only',
            'native_reviewed': False,
            'quality_status': 'unreviewed',
            'provenance': {'url': 'https://example.test/source', 'sha256': 'a' * 64},
            'source_example': {'source': 'source sentence', 'target': 'का पाठ'},
        }

        record = adapt_record('external/flores', row)

        self.assertEqual(record['text']['text_raw'], ' का पाठ ')
        self.assertEqual(record['text']['text_scoring'], 'का पाठ')
        self.assertEqual(record['text']['normalizer_id'], 'unicode-nfc-trim-v1')
        self.assertEqual(record['text']['text_raw_sha256'], sha(' का पाठ '))
        self.assertEqual(record['text']['text_scoring_sha256'], sha('का पाठ'))
        self.assertEqual(record['legacy_record'], row)
        self.assertFalse(record['rights']['public_release_cleared'])

    def test_internal_text_does_not_mislabel_v01_text_as_raw_original(self):
        row = {
            'segment_sha256': sha('गढ़वाली पाठ'),
            'duplicate_component_id': 'component-a',
            'text': 'गढ़वाली पाठ',
            'split': 'test',
            'parents': [{'record_id': 'source:1'}],
        }

        record = adapt_record('internal/text', row)

        self.assertIsNone(record['text']['text_raw'])
        self.assertEqual(record['text']['text_source'], 'गढ़वाली पाठ')
        self.assertEqual(record['text']['text_scoring'], 'गढ़वाली पाठ')
        self.assertFalse(record['text']['raw_text_available'])
        self.assertEqual(record['text']['raw_text_status'], 'not_available_in_v01_view')

    def test_xorqa_usage_overlay_is_linked_without_dropping_record(self):
        row = {
            'record_id': 'xorqa:dev:1',
            'split': 'dev',
            'text_original': 'प्रश्न?',
            'text_normalized': 'प्रश्न?',
            'text_sha256': sha('प्रश्न?'),
            'iso_639_3': 'gbm',
            'script': 'Deva',
            'source_id': 'xorqa',
            'attribution': 'source attribution',
            'license_id': 'MIT',
            'license_url': 'https://example.test/license',
            'rights_status': 'upstream_declared_license',
            'training_eligible': False,
            'usage': 'evaluation_only',
            'native_reviewed': False,
            'quality_status': 'unreviewed',
            'provenance': {'url': 'https://example.test/source', 'sha256': 'a' * 64},
            'source_example': {
                'context': 'A long enough source context for the question.',
                'question': 'प्रश्न?', 'answers': [{'text': 'उत्तर', 'answer_start': 0}],
            },
        }
        overlay = {
            'usage_label': 'open_diagnostic_only_split_overlap',
            'record_retained': True,
            'source_family_sha256': 'b' * 64,
            'normalized_context_sha256': 'c' * 64,
            'open_diagnostic_eligible': True,
            'independent_source_generalization_eligible': False,
        }

        record = adapt_record('external/xorqa', row, overlay)

        self.assertEqual(record['example_id'], 'xorqa:dev:1')
        self.assertEqual(record['usage']['usage_label'], overlay['usage_label'])
        self.assertEqual(record['lineage']['overlay_source_family_sha256'], 'b' * 64)
        self.assertTrue(record['usage']['record_retained'])

    def test_asr_preserves_target_and_marks_local_audio_private(self):
        row = {
            'audio_path': 'upstream/clip.wav',
            'local_audio_path': 'data/audio/clip.wav',
            'audio_sha256': 'a' * 64,
            'transcript': 'मूल ट्रांसक्रिप्ट ।',
            'asr_target': 'मूल ट्रांसक्रिप्ट ।',
            'asr_target_sha256': sha('मूल ट्रांसक्रिप्ट ।'),
            'split': 'test',
            'main_split': 'train',
            'duration_seconds': 1.25,
            'speaker_id': 'speaker-local',
            'source': 'ARTPARK-IISc/Vaani',
            'config': 'Garhwali',
            'license': 'CC-BY-4.0',
        }

        record = adapt_record('internal/asr', row)

        self.assertEqual(record['task'], 'asr')
        self.assertEqual(record['text']['text_raw'], 'मूल ट्रांसक्रिप्ट ।')
        self.assertEqual(record['text']['text_scoring'], 'मूल ट्रांसक्रिप्ट')
        self.assertEqual(record['lineage']['audio_sha256'], 'a' * 64)
        self.assertEqual(record['payload']['local_audio_path'], 'data/audio/clip.wav')
        self.assertTrue(record['privacy']['contains_local_identifiers'])

    def test_export_keeps_all_rows_and_is_deterministic(self):
        row = {
            'record_id': 'xorqa:dev:1', 'split': 'dev',
            'text_original': 'प्रश्न?', 'text_normalized': 'प्रश्न?',
            'text_sha256': sha('प्रश्न?'), 'iso_639_3': 'gbm', 'script': 'Deva',
            'source_id': 'xorqa', 'attribution': 'source attribution',
            'license_id': 'MIT', 'license_url': 'https://example.test/license',
            'rights_status': 'upstream_declared_license', 'training_eligible': False,
            'usage': 'evaluation_only', 'native_reviewed': False,
            'quality_status': 'unreviewed',
            'provenance': {'url': 'https://example.test/source', 'sha256': 'a' * 64},
            'source_example': {'context': 'Context', 'question': 'प्रश्न?', 'answers': []},
        }
        views = {'external/xorqa': [row, dict(row, record_id='xorqa:dev:2')]}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = build_export_from_views(
                views, {}, {'external/xorqa': 'd' * 64}, 'e' * 64, 'f' * 64, root / 'out',
            )
            first_bytes = (root / 'out' / 'external__xorqa.jsonl').read_bytes()
            second = build_export_from_views(
                views, {}, {'external/xorqa': 'd' * 64}, 'e' * 64, 'f' * 64, root / 'out',
            )
            second_bytes = (root / 'out' / 'external__xorqa.jsonl').read_bytes()

        self.assertEqual(first['views']['external/xorqa']['records'], 2)
        self.assertEqual(first['total_records'], 2)
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(first, second)

    def test_metric_contracts_are_explicitly_draft_and_do_not_claim_scores(self):
        contracts = metric_contracts()

        self.assertIn('translation', contracts)
        self.assertIn('signature', contracts['translation']['metrics'][0])
        self.assertEqual(contracts['translation']['status'], 'draft_not_release_frozen')
        self.assertFalse(contracts['translation']['scores_computed'])

    def test_export_validator_detects_written_view_drift(self):
        row = {
            'id': 'text-1', 'text': 'गढ़वाली पाठ', 'split': 'train',
            'language': 'gbm', 'script': 'Deva', 'provenance': [],
            'public_rights_basis': [], 'recommended_for_training': True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / 'out'
            manifest = build_export_from_views(
                {'text_recommended/train': [row]}, {},
                {'text_recommended/train': 'a' * 64}, 'b' * 64, 'c' * 64,
                output_dir,
            )
            self.assertEqual(validate_export_artifacts(output_dir, manifest)['status'], 'pass')
            (output_dir / manifest['views']['text_recommended/train']['path']).write_bytes(b'changed\n')
            result = validate_export_artifacts(output_dir, manifest)

        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any('SHA-256 differs' in error for error in result['errors']))


if __name__ == '__main__':
    unittest.main()
