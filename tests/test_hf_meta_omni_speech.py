import json
import tempfile
import unittest
from pathlib import Path

from build_hf_meta_omni_speech import (
    annotate_audio_duplicates,
    annotate_text_overlaps,
    combine_annotations,
    make_release_record,
    release_split,
    _update_release_files,
)


class MetaOmnilingualSpeechReleaseTests(unittest.TestCase):
    def test_rebuilding_release_metadata_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            (output / 'manifest.json').write_text(json.dumps({
                'source_rows': 1,
                'duration_hours': 0.25,
                'audio_bytes': 100,
            }), encoding='utf-8')
            (output / 'manifest.jsonl').write_text(
                json.dumps({'audio_sha256': 'a' * 64}) + '\n', encoding='utf-8'
            )
            (output / 'meta_omnilingual-manifest.jsonl').write_text(
                json.dumps({'audio_sha256': 'b' * 64}) + '\n', encoding='utf-8'
            )
            (output / 'README.md').write_text(
                '---\nconfigs:\n- config_name: garhwali_speech\n'
                '  data_files:\n  - split: train\n    path: data/train-*.parquet\n'
                '  - split: validation\n    path: data/validation-*.parquet\n'
                '  - split: test\n    path: data/test-*.parquet\n---\n\n'
                '# Garhwali Speech\n\n## Contents\n\n- VAANI rows.\n\n'
                'Load with `datasets.load_dataset("rushilrawat/garhwali-speech", "garhwali_speech")`.\n',
                encoding='utf-8',
            )
            (output / 'ATTRIBUTION.md').write_text(
                '# Attribution\n\nVAANI attribution.\n', encoding='utf-8'
            )
            meta = {
                'source_rows': 3,
                'split_counts': {'train': 1, 'validation': 1, 'test': 1},
                'duration_hours': 0.5,
                'source_audio_bytes': 200,
                'duplicate_audio_rows': 2,
                'duplicate_audio_groups': 1,
                'cross_split_duplicate_audio_groups': 1,
                'cross_split_transcript_groups': 1,
                'cross_corpus_audio_overlap_rows': 0,
                'cross_corpus_exact_text_overlap_rows': 0,
                'split_safe_for_training_rows': 2,
            }

            _update_release_files(output, meta)
            first = tuple((output / name).read_text(encoding='utf-8') for name in (
                'README.md', 'ATTRIBUTION.md', 'manifest.json',
            ))
            _update_release_files(output, meta)
            second = tuple((output / name).read_text(encoding='utf-8') for name in (
                'README.md', 'ATTRIBUTION.md', 'manifest.json',
            ))

            self.assertEqual(first, second)
            self.assertEqual(first[0].count('- config_name: meta_omnilingual'), 1)
            self.assertEqual(first[0].count('- Overlap audit:'), 1)
            self.assertEqual(first[0].count('## Additional source: Meta Omnilingual ASR Corpus'), 1)
            self.assertEqual(first[1].count('Meta Omnilingual Garhwali audio and transcripts'), 1)

    def test_dev_maps_to_validation_and_other_splits_are_preserved(self):
        self.assertEqual(release_split('dev'), 'validation')
        self.assertEqual(release_split('train'), 'train')
        self.assertEqual(release_split('test'), 'test')

    def test_duplicate_audio_rows_remain_visible_but_are_not_model_eligible(self):
        rows = [
            {'record_id': 'row-a', 'split': 'train', 'audio_sha256': 'a', 'text_sha256': 'x'},
            {'record_id': 'row-b', 'split': 'test', 'audio_sha256': 'a', 'text_sha256': 'y'},
            {'record_id': 'row-c', 'split': 'validation', 'audio_sha256': 'b', 'text_sha256': 'z'},
        ]
        annotations = annotate_audio_duplicates(rows)

        self.assertEqual(annotations['row-a']['duplicate_audio_count'], 2)
        self.assertTrue(annotations['row-a']['cross_split_audio_overlap'])
        self.assertTrue(annotations['row-a']['transcript_conflict_for_audio'])
        self.assertFalse(annotations['row-a']['split_safe_for_training'])
        self.assertFalse(annotations['row-b']['split_safe_for_evaluation'])
        self.assertEqual(annotations['row-c']['duplicate_audio_count'], 1)
        self.assertTrue(annotations['row-c']['split_safe_for_evaluation'])

    def test_audio_and_text_safety_restrictions_are_both_applied(self):
        audio = {
            'row': {
                'split_safe_for_training': False,
                'split_safe_for_evaluation': False,
                'duplicate_audio_count': 2,
            },
        }
        text = {
            'row': {
                'split_safe_for_training': True,
                'split_safe_for_evaluation': True,
                'duplicate_text_count': 1,
            },
        }

        combined = combine_annotations(audio, text)

        self.assertFalse(combined['row']['split_safe_for_training'])
        self.assertFalse(combined['row']['split_safe_for_evaluation'])
        self.assertEqual(combined['row']['duplicate_text_count'], 1)

    def test_exact_text_overlap_across_splits_is_flagged_and_not_split_safe(self):
        rows = [
            {'record_id': 'train-row', 'split': 'train', 'text_sha256': 'same'},
            {'record_id': 'test-row', 'split': 'test', 'text_sha256': 'same'},
            {'record_id': 'other-row', 'split': 'validation', 'text_sha256': 'other'},
        ]
        flags = annotate_text_overlaps(rows, {'train': set(), 'evaluation': set()})

        self.assertEqual(flags['train-row']['duplicate_text_count'], 2)
        self.assertTrue(flags['test-row']['cross_split_text_overlap'])
        self.assertFalse(flags['train-row']['split_safe_for_training'])
        self.assertFalse(flags['test-row']['split_safe_for_evaluation'])
        self.assertTrue(flags['other-row']['split_safe_for_training'])

    def test_public_record_keeps_transcript_provenance_without_speaker_ids(self):
        record = make_release_record(
            {
                'record_id': 'meta-omni-train-00001',
                'source_split': 'train',
                'split': 'train',
                'audio_sha256': 'a' * 64,
                'text_sha256': 'b' * 64,
                'transcript': 'गढ़वळी पाठ',
                'elicitation_prompt': 'Tell a story.',
                'duration_seconds': 3.5,
                'source_file': 'data/gbm_Deva/train-00000-of-00005.parquet',
                'source_file_sha256': 'c' * 64,
                'upstream_row_index': 18,
            },
            {
                'duplicate_audio_count': 1,
                'duplicate_text_count': 1,
                'cross_split_audio_overlap': False,
                'cross_corpus_audio_overlap': False,
                'cross_split_text_overlap': False,
                'cross_corpus_text_overlap': False,
                'cross_corpus_train_text_overlap': False,
                'cross_corpus_evaluation_text_overlap': False,
                'transcript_conflict_for_audio': False,
                'split_safe_for_training': True,
                'split_safe_for_evaluation': True,
            },
        )

        self.assertEqual(record['transcript'], 'गढ़वळी पाठ')
        self.assertEqual(record['transcript_source'], 'facebook/omnilingual-asr-corpus')
        self.assertEqual(record['source_license'], 'CC-BY-4.0')
        self.assertEqual(record['source_license_url'], 'https://creativecommons.org/licenses/by/4.0/')
        self.assertEqual(record['upstream_row_index'], 18)
        self.assertEqual(record['quality_status'], 'unreviewed')
        self.assertEqual(record['split'], 'train')
        self.assertNotIn('speaker_id', record)
        self.assertNotIn('prompt_id', record)
        self.assertNotIn('segment_id', record)


if __name__ == '__main__':
    unittest.main()
