import json
import tempfile
import unittest
from pathlib import Path

import build_huggingface_dataset as m


class HuggingFaceDatasetBuilderTests(unittest.TestCase):
    def test_public_text_requires_every_component_to_be_publishable(self):
        allowed = {
            'parents': [{'provenance': [{
                'training_eligible': False,
                'license': 'CC-BY-4.0',
                'iso_639_3': 'gbm',
            }]}],
        }
        blocked = {
            'parents': [{'provenance': [{
                'license': 'CC-BY-4.0',
                'rights_status': 'source_component_and_consent_review_pending',
            }]}],
        }
        self.assertTrue(m.is_public_text_row(allowed))
        self.assertFalse(m.is_public_text_row(blocked))
        self.assertTrue(m.is_public_garhwali_text_row(allowed))
        allowed['parents'][0]['provenance'][0]['iso_639_3'] = 'eng'
        self.assertFalse(m.is_public_garhwali_text_row(allowed))

    def test_text_export_derives_script(self):
        base = {'segment_sha256': 'a', 'split': 'train', 'quality_flags': []}
        self.assertEqual(m.text_row({**base, 'text': 'गढ़वाली'})['script'], 'Deva')
        self.assertEqual(m.text_row({**base, 'text': 'garhwali'})['script'], 'Latn')

    def test_catalog_keeps_every_identity_but_redacts_unlicensed_text(self):
        row = {
            'text_sha256': 'a' * 64,
            'text': 'गढ़वाली पाठ',
            'split': 'train',
            'language_bucket': 'garhwali_candidate',
            'quality_v2': {'tier': 'high_quality_local_only'},
            'provenance': [{
                'source_id': 'example',
                'source_url': 'https://example.test/garhwali',
                'iso_639_3': 'gbm',
                'rights_status': 'public_webpage_no_open_license_stated',
            }],
        }
        exported = m.catalog_row(row, refinement={
            'automatic_changes': [],
            'review_signals': ['romanized_text_requires_native_review'],
            'manual_review_required': True,
            'language_decision': 'unchanged_pending_native_review',
            'quality_refinement_status': 'review_required',
            'release_text': 'protected corrected text',
            'release_text_sha256': 'c' * 64,
            'quality_dimensions': {'language_identity': {'status': 'pending'}},
            'review_priority': {'rank': 2, 'reasons': ['native_accuracy_unverified']},
        })
        self.assertIsNone(exported['text'])
        self.assertFalse(exported['text_publicly_available'])
        self.assertEqual(exported['text_sha256'], row['text_sha256'])
        self.assertEqual(exported['sources'][0]['source_url'], 'https://example.test/garhwali')
        self.assertEqual(exported['quality_v2']['tier'], 'high_quality_local_only')
        self.assertEqual(
            exported['text_refinement']['review_signals'],
            ['romanized_text_requires_native_review'],
        )
        self.assertNotIn('release_text', exported['text_refinement'])
        self.assertEqual(
            exported['text_refinement']['quality_dimensions']['language_identity']['status'],
            'pending',
        )
        self.assertEqual(exported['text_refinement']['review_priority']['rank'], 2)

    def test_catalog_includes_open_text(self):
        row = {
            'text_sha256': 'b' * 64,
            'text': 'गढ़वाली पाठ',
            'provenance': [{'iso_639_3': 'gbm', 'license': 'CC-BY-4.0'}],
        }
        exported = m.catalog_row(row)
        self.assertEqual(exported['text'], 'गढ़वाली पाठ')
        self.assertTrue(exported['text_publicly_available'])
        self.assertIsNone(exported['redaction_reason'])

    def test_audio_export_uses_content_addressed_relative_path(self):
        row = {
            'audio_sha256': 'ab' * 32,
            'local_audio_path': 'data/audio/source.wav',
            'source': 'VAANI',
            'speaker_id': 'raw-speaker-id',
            'asr_target_clean': 'गढ़वाली',
            'machine_transcript_quality': {'flags': ['mixed_script']},
            'recovery_status': 'confidence_scored_alternative_available',
            'recovery_confidence': {
                'confidence_band': 'very_low',
                'confidence_is_accuracy_probability': False,
                'whisper_candidate': 'गढ़वाली',
            },
            'duplicate_source_audio_paths': ['private-1.wav', 'private-2.wav'],
            'language_scope_status': 'source_label_conflict',
            'source_conflict_evidence': {'human_bengali_transcripts': 8},
            'active_for_source_error_analysis': True,
        }
        exported = m.audio_row(row, transcript_field='asr_target_clean')
        self.assertEqual(exported['audio'], f'audio/ab/{"ab" * 32}.wav')
        self.assertEqual(exported['transcript'], 'गढ़वाली')
        self.assertEqual(exported['machine_transcript_quality']['flags'], ['mixed_script'])
        self.assertEqual(exported['recovery_status'], 'confidence_scored_alternative_available')
        self.assertEqual(exported['recovery_confidence']['confidence_band'], 'very_low')
        self.assertTrue(exported['speaker_id'].startswith('speaker_'))
        self.assertNotEqual(exported['speaker_id'], 'raw-speaker-id')
        self.assertEqual(exported['source_audio_records'], 2)
        self.assertNotIn('duplicate_source_audio_paths', exported)
        self.assertNotIn('local_audio_path', exported)
        self.assertEqual(exported['language_scope_status'], 'source_label_conflict')
        self.assertTrue(exported['active_for_source_error_analysis'])

    def test_shards_are_deterministic_and_reported(self):
        rows = [{'id': str(index)} for index in range(5)]
        with tempfile.TemporaryDirectory() as directory:
            report = m.write_shards(rows, Path(directory), 'train', shard_rows=2)
            self.assertEqual(report['records'], 5)
            self.assertEqual(report['shards'], 3)
            paths = sorted(Path(directory).glob('train-*.jsonl'))
            self.assertEqual([p.name for p in paths], [
                'train-00000.jsonl', 'train-00001.jsonl', 'train-00002.jsonl'
            ])
            self.assertEqual(json.loads(paths[-1].read_text())['id'], '4')

    def test_draft_coverage_accepts_source_rows_with_duplicate_audio(self):
        queue = [
            {'audio_sha256': 'same', 'audio_path': 'one.wav'},
            {'audio_sha256': 'same', 'audio_path': 'two.wav'},
        ]
        drafts = [
            {'audio_sha256': 'same', 'audio_path': 'one.wav'},
            {'audio_sha256': 'same', 'audio_path': 'two.wav'},
        ]
        self.assertTrue(m.drafts_cover_queue(queue, drafts))
        self.assertFalse(m.drafts_cover_queue(queue, drafts[:1]))

    def test_duplicate_audio_rows_merge_source_paths(self):
        rows = [
            {'audio_sha256': 'same', 'audio_path': 'one.wav', 'machine_transcript': 'पाठ'},
            {'audio_sha256': 'same', 'audio_path': 'two.wav', 'machine_transcript': 'पाठ'},
        ]
        merged = list(m.deduplicate_audio_rows(rows, 'machine_transcript'))
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['duplicate_source_audio_paths'], ['one.wav', 'two.wav'])

    def test_audio_link_report_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.wav'
            source.write_bytes(b'audio')
            old_root = m.ROOT
            try:
                m.ROOT = root
                row = {'audio_sha256': 'ab' * 32, 'local_audio_path': 'source.wav'}
                first = m.link_audio([row], root / 'package')
                second = m.link_audio([row], root / 'package')
            finally:
                m.ROOT = old_root
        self.assertEqual(first, {'new': 1, 'total': 1})
        self.assertEqual(second, {'new': 0, 'total': 1})

    def test_transcript_only_cleanup_removes_packaged_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / 'audio/ab/file.wav'
            audio.parent.mkdir(parents=True)
            audio.write_bytes(b'audio')
            self.assertEqual(m.remove_packaged_audio(root), 1)
            self.assertFalse((root / 'audio').exists())


if __name__ == '__main__':
    unittest.main()
