import hashlib
import io
import json
import os
from collections import Counter
from contextlib import redirect_stderr
from unittest import mock
import tempfile
import unittest
from pathlib import Path

import build_dataset_splits as m


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
        encoding='utf-8',
    )


class DatasetSplitTests(unittest.TestCase):
    def test_builds_strict_audio_and_pending_evaluation_splits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path = root / 'text.jsonl'
            audio_path = root / 'audio.jsonl'
            out = root / 'out'
            write_jsonl(text_path, [
                {'segment_sha256': 'a' * 64, 'split': 'train', 'quality_flags': []},
                {'segment_sha256': 'b' * 64, 'split': 'test', 'quality_flags': []},
                {'segment_sha256': 'c' * 64, 'split': 'test', 'quality_flags': ['very_short']},
            ])
            clean = {
                'recommended_for_supervised_training': True,
                'language_quality': {
                    'status': 'garhwali_candidate',
                    'review_required': False,
                },
                'transcript_review_flags': [],
                'training_quality_flags': [],
                'audio_quality': {'readable': True},
                'asr_target_clean': 'गढ़वाली पाठ',
                'duration_seconds': 2.0,
            }
            write_jsonl(audio_path, [
                {**clean, 'audio_sha256': '1' * 64, 'speaker_id': 'speaker-1', 'split': 'train'},
                {**clean, 'audio_sha256': '2' * 64, 'speaker_id': 'speaker-2', 'split': 'test'},
                {**clean, 'audio_sha256': '3' * 64, 'speaker_id': 'NA', 'split': 'test'},
                {
                    **clean,
                    'audio_sha256': '4' * 64,
                    'speaker_id': 'speaker-3',
                    'split': 'validation',
                    'transcript_review_flags': ['script_review'],
                },
            ])

            report = m.build_splits(text_path, audio_path, out, semantic_path=None)

            self.assertEqual(report['text']['records'], {'test': 2, 'train': 1, 'validation': 0})
            self.assertEqual(report['asr_strict']['records'], {'test': 1, 'train': 1, 'validation': 0})
            self.assertEqual(report['tts_candidate']['records'], {'test': 1, 'train': 1, 'validation': 0})
            self.assertEqual(report['asr_experimental_all']['records'], {
                'test': 2, 'train': 1, 'validation': 1,
            })
            self.assertEqual(report['excluded_audio']['unidentified_speaker'], 1)
            self.assertEqual(report['excluded_audio']['transcript_or_language_review'], 1)
            evaluation = [json.loads(line) for line in (out / 'evaluation/asr_candidate.jsonl').read_text().splitlines()]
            self.assertEqual([row['audio_sha256'] for row in evaluation], ['2' * 64])
            self.assertEqual(evaluation[0]['review_status'], 'automated_quality_screened')
            self.assertTrue(evaluation[0]['experimental_evaluation_eligible'])
            text_evaluation = [json.loads(line) for line in (out / 'evaluation/text_candidate.jsonl').read_text().splitlines()]
            self.assertEqual([row['segment_sha256'] for row in text_evaluation], ['b' * 64])
            experimental = [
                json.loads(line)
                for line in (out / 'asr_experimental/test.jsonl').read_text().splitlines()
            ]
            self.assertEqual(len(experimental), 2)
            self.assertTrue(all(row['experimental_training_eligible'] for row in experimental))
            # Every artifact entry records the written file's hash and row count.
            from garhwali_lab.hashing import sha256_file
            for relative, entry in report['artifacts'].items():
                self.assertEqual(entry['sha256'], sha256_file(out / relative), relative)
                self.assertEqual(entry['records'], len((out / relative).read_text().splitlines()), relative)

    def test_rejects_identified_speaker_crossing_splits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path = root / 'text.jsonl'
            audio_path = root / 'audio.jsonl'
            write_jsonl(text_path, [])
            base = {
                'recommended_for_supervised_training': True,
                'language_quality': {'status': 'garhwali_candidate', 'review_required': False},
                'transcript_review_flags': [],
                'training_quality_flags': [],
                'audio_quality': {'readable': True},
                'asr_target_clean': 'गढ़वाली पाठ',
                'duration_seconds': 2.0,
                'speaker_id': 'same-speaker',
            }
            write_jsonl(audio_path, [
                {**base, 'audio_sha256': '1' * 64, 'split': 'train'},
                {**base, 'audio_sha256': '2' * 64, 'split': 'test'},
            ])

            with self.assertRaisesRegex(ValueError, 'speaker crosses splits'):
                m.build_splits(text_path, audio_path, root / 'out')

    def test_supported_semantic_duplicates_are_reassigned_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path = root / 'text.jsonl'
            audio_path = root / 'audio.jsonl'
            semantic_path = root / 'semantic.jsonl'
            write_jsonl(text_path, [
                {'segment_sha256': 'a' * 64, 'split': 'train', 'text': 'भौत शुक्रिया!'},
                {'segment_sha256': 'b' * 64, 'split': 'test', 'text': 'भौत शुक्रिया।'},
            ])
            write_jsonl(audio_path, [])
            write_jsonl(semantic_path, [{
                'left_segment_sha256': 'a' * 64,
                'right_segment_sha256': 'b' * 64,
                'refined_decision': 'supported_candidate',
            }])
            report = m.build_splits(
                text_path, audio_path, root / 'out', semantic_path=semantic_path
            )
            expected = m.split_for_hash('a' * 64)
            self.assertEqual(report['text']['records'][expected], 2)
            self.assertEqual(sum(report['text']['records'].values()), 2)
            self.assertEqual(
                report['text_duplicate_components']['conflicting_components_hash_assigned'], 1
            )

    def test_semantic_reassignment_keeps_all_segments_of_parent_document_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path = root / 'text.jsonl'
            audio_path = root / 'audio.jsonl'
            semantic_path = root / 'semantic.jsonl'
            rows = [
                {
                    'segment_sha256': 'a' * 64,
                    'split': 'test',
                    'text': 'पहिलो वाक्य।',
                    'parents': [{'text_sha256': 'doc-1'}],
                },
                {
                    'segment_sha256': 'b' * 64,
                    'split': 'test',
                    'text': 'दोस्रो वाक्य।',
                    'parents': [{'text_sha256': 'doc-1'}],
                },
                {
                    'segment_sha256': 'c' * 64,
                    'split': 'train',
                    'text': 'पहिलो वाक्यको रूप।',
                    'parents': [{'text_sha256': 'doc-2'}],
                },
            ]
            write_jsonl(text_path, rows)
            write_jsonl(audio_path, [])
            write_jsonl(semantic_path, [{
                'left_segment_sha256': 'a' * 64,
                'right_segment_sha256': 'c' * 64,
                'refined_decision': 'supported_candidate',
            }])

            report = m.build_splits(
                text_path, audio_path, root / 'out', semantic_path=semantic_path
            )

            expected = m.split_for_hash('a' * 64)
            self.assertEqual(report['text']['records'][expected], 3)
            self.assertEqual(report['leakage_checks']['parent_document_cross_split'], 0)

    def test_shared_junk_segment_does_not_trip_parent_document_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path, audio_path = root / 'text.jsonl', root / 'audio.jsonl'
            write_jsonl(text_path, [
                {'segment_sha256': 'a' * 64, 'split': 'train', 'text': 'पहिलो किताबको वाक्य।',
                 'parents': [{'text_sha256': 'doc-1'}]},
                {'segment_sha256': 'b' * 64, 'split': 'test', 'text': 'दोस्रो किताबको वाक्य।',
                 'parents': [{'text_sha256': 'doc-2'}]},
                {'segment_sha256': 'c' * 64, 'split': 'train', 'text': '.',
                 'parents': [{'text_sha256': 'doc-1'}, {'text_sha256': 'doc-2'}]},
            ])
            write_jsonl(audio_path, [])

            report = m.build_splits(text_path, audio_path, root / 'out', semantic_path=None)

            self.assertEqual(report['leakage_checks']['parent_document_cross_split'], 0)
            self.assertEqual(report['text']['records']['test'], 1)

    def test_custom_release_id_is_recorded_for_versioned_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path = root / 'text.jsonl'
            audio_path = root / 'audio.jsonl'
            write_jsonl(text_path, [])
            write_jsonl(audio_path, [])

            report = m.build_splits(
                text_path,
                audio_path,
                root / 'out',
                semantic_path=None,
                release_id='parent-safe-candidate-v0.2',
            )

            self.assertEqual(report['release_id'], 'parent-safe-candidate-v0.2')

    def test_report_records_input_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path = root / 'text.jsonl'
            audio_path = root / 'audio.jsonl'
            semantic_path = root / 'semantic.jsonl'
            write_jsonl(text_path, [])
            write_jsonl(audio_path, [])
            write_jsonl(semantic_path, [])

            report = m.build_splits(
                text_path, audio_path, root / 'out', semantic_path=semantic_path
            )

            self.assertEqual(report['source_hashes'], {
                'text_segments': hashlib.sha256(text_path.read_bytes()).hexdigest(),
                'audio_supervised': hashlib.sha256(audio_path.read_bytes()).hexdigest(),
                'semantic_edges': hashlib.sha256(semantic_path.read_bytes()).hexdigest(),
            })

class ComponentSplitPolicyTests(unittest.TestCase):
    def test_conflicting_components_keep_the_target_ratio(self):
        rows = []
        for index in range(4000):
            left = hashlib.sha256(f'left-{index}'.encode()).hexdigest()
            right = hashlib.sha256(f'right-{index}'.encode()).hexdigest()
            rows.append({'segment_sha256': left, 'split': 'train', 'text': f'वाक्य {index}'})
            rows.append({'segment_sha256': right, 'split': 'test', 'text': f'वाक्य {index}!'})
        result, report = m.component_safe_text_splits(rows, semantic_path=None)
        counts = Counter(row['split'] for row in result)
        self.assertEqual(report['conflicting_components_hash_assigned'], 4000)
        self.assertGreater(counts['validation'] / len(result), 0.035)
        self.assertGreater(counts['test'] / len(result), 0.035)
        by_component = {}
        for row in result:
            by_component.setdefault(row['duplicate_component_id'], set()).add(row['split'])
        self.assertTrue(all(len(splits) == 1 for splits in by_component.values()))

    def test_short_and_boilerplate_keys_do_not_chain_documents(self):
        rows = []
        for index in range(30):
            document = hashlib.sha256(f'doc-{index}'.encode()).hexdigest()
            split = ('train', 'validation', 'test')[index % 3]
            for text in (f'अलग वाक्य संख्या {index}', 'c', '0 in public domain'):
                rows.append({
                    'segment_sha256': hashlib.sha256(f'{index}-{text}'.encode()).hexdigest(),
                    'split': split, 'text': text, 'parents': [{'text_sha256': document}],
                })
        result, report = m.component_safe_text_splits(rows, semantic_path=None)
        self.assertEqual(report['normalized_keys_skipped_short'], 1)
        self.assertEqual(report['normalized_keys_skipped_boilerplate'], 1)
        # The junk segments stay out of every group, so each document body stands alone.
        self.assertEqual(report['largest_component_records'], 1)
        self.assertEqual(report['records_reassigned'], 0)
        self.assertEqual(Counter(row['split'] for row in result), {'train': 30, 'validation': 30, 'test': 30})

    def test_junk_segment_with_many_parents_does_not_bridge_documents(self):
        rows = []
        parents = []
        for index in range(30):
            document = hashlib.sha256(f'doc-{index}'.encode()).hexdigest()
            parents.append({'text_sha256': document})
            rows.append({
                'segment_sha256': hashlib.sha256(f'body-{index}'.encode()).hexdigest(),
                'split': ('train', 'validation', 'test')[index % 3],
                'text': f'अलग वाक्य संख्या {index}', 'parents': [{'text_sha256': document}],
            })
        # One deduplicated '.' segment that lists every document as a parent.
        rows.append({'segment_sha256': 'f' * 64, 'split': 'train', 'text': '.', 'parents': parents})
        result, report = m.component_safe_text_splits(rows, semantic_path=None)
        self.assertEqual(report['largest_component_records'], 1)
        self.assertEqual(report['records_reassigned'], 0)

    def test_oversized_component_goes_to_train(self):
        rows = [{
            'segment_sha256': hashlib.sha256(f'seg-{index}'.encode()).hexdigest(),
            'split': ('train', 'validation', 'test')[index % 3],
            'text': f'एक ही किताब का वाक्य {index}', 'parents': [{'text_sha256': 'book'}],
        } for index in range(150)]
        result, report = m.component_safe_text_splits(rows, semantic_path=None)
        self.assertEqual(report['oversized_components_to_train'], 1)
        self.assertEqual({row['split'] for row in result}, {'train'})

    def test_train_heavy_input_is_topped_up_to_the_held_out_target(self):
        # 400 two-segment documents, all inherited as train (as upstream
        # chaining leaves them), plus one oversized book that must stay in train.
        rows = []
        for index in range(400):
            document = f'doc-{index}'
            for part in range(2):
                rows.append({
                    'segment_sha256': hashlib.sha256(f'{index}-{part}'.encode()).hexdigest(),
                    'split': 'train', 'text': f'अलग वाक्य {index} भाग {part}',
                    'parents': [{'text_sha256': document}],
                })
        rows += [{
            'segment_sha256': hashlib.sha256(f'book-{index}'.encode()).hexdigest(),
            'split': 'train', 'text': f'किताब का वाक्य {index}', 'parents': [{'text_sha256': 'book'}],
        } for index in range(200)]
        result, report = m.component_safe_text_splits(rows, semantic_path=None)
        counts = Counter(row['split'] for row in result)
        target = int(len(rows) * m.HELD_OUT_TARGET_SHARE)
        self.assertEqual(report['held_out_target_records'], target)
        self.assertEqual(counts['validation'], target)
        self.assertEqual(counts['test'], target)
        self.assertEqual(report['held_out_top_up_records'], {'validation': target, 'test': target})
        by_document = {}
        for row in result:
            by_document.setdefault(row['parents'][0]['text_sha256'], set()).add(row['split'])
        self.assertTrue(all(len(splits) == 1 for splits in by_document.values()))
        self.assertEqual(by_document['book'], {'train'})
        moved = [row for row in result if row['split'] != 'train']
        self.assertTrue(all(row['split_assignment'] == 'held_out_top_up' for row in moved))

    def test_top_up_leaves_balanced_input_alone(self):
        rows = [{
            'segment_sha256': hashlib.sha256(f'seg-{index}'.encode()).hexdigest(),
            'split': ('validation', 'test')[index % 2] if index < 20 else 'train',
            'text': f'वाक्य संख्या {index}',
        } for index in range(100)]
        result, report = m.component_safe_text_splits(rows, semantic_path=None)
        self.assertEqual(report['held_out_top_up_records'], {'validation': 0, 'test': 0})
        self.assertEqual(report['records_reassigned'], 0)

    def test_repeated_sentence_still_links_its_documents(self):
        rows = [
            {'segment_sha256': 'a' * 64, 'split': 'train', 'text': 'मी घौर जाणू छौं',
             'parents': [{'text_sha256': 'd1'}]},
            {'segment_sha256': 'b' * 64, 'split': 'test', 'text': 'मी घौर जाणू छौं।',
             'parents': [{'text_sha256': 'd2'}]},
        ]
        result, report = m.component_safe_text_splits(rows, semantic_path=None)
        self.assertEqual(len({row['split'] for row in result}), 1)
        self.assertEqual(report['normalized_edges'], 1)

    def test_agreeing_components_keep_their_split(self):
        rows = [
            {'segment_sha256': 'a' * 64, 'split': 'validation', 'text': 'एक'},
            {'segment_sha256': 'b' * 64, 'split': 'validation', 'text': 'एक।'},
        ]
        result, report = m.component_safe_text_splits(rows, semantic_path=None)
        self.assertEqual({row['split'] for row in result}, {'validation'})
        self.assertEqual(report['records_reassigned'], 0)

    def test_missing_semantic_file_is_reported_and_can_be_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / 'absent.jsonl'
            rows = [{'segment_sha256': 'a' * 64, 'split': 'train', 'text': 'एक'}]
            with redirect_stderr(io.StringIO()) as err:
                _, report = m.component_safe_text_splits(rows, semantic_path=missing)
            self.assertEqual(report['semantic_edges_source'], 'missing')
            self.assertIn('warning', err.getvalue())
            with mock.patch.dict(os.environ, {m.REQUIRE_SEMANTIC_ENV: '1'}):
                with self.assertRaises(FileNotFoundError):
                    m.component_safe_text_splits(rows, semantic_path=missing)


class ExperimentalAudioLeakageTests(unittest.TestCase):
    def test_flags_speaker_and_transcript_leakage(self):
        rows = [
            {'speaker_id': 'S1', 'split': 'train', 'asr_target_clean': 'पाणी ल्या', 'experimental_quality_flags': []},
            {'speaker_id': 'S1', 'split': 'test', 'asr_target_clean': 'घौर जा', 'experimental_quality_flags': []},
            {'speaker_id': '', 'split': 'validation', 'asr_target_clean': 'पाणी ल्या।', 'experimental_quality_flags': []},
            {'speaker_id': 'S2', 'split': 'test', 'asr_target_clean': 'अलग', 'experimental_quality_flags': []},
        ]
        with redirect_stderr(io.StringIO()):
            report = m.flag_experimental_audio_leakage(rows)
        self.assertEqual(report, {
            'experimental_unidentified_speaker_records': 1,
            'experimental_speaker_cross_split_records': 2,
            'experimental_transcript_cross_split_records': 2,
        })
        self.assertIn('speaker_crosses_splits', rows[1]['experimental_quality_flags'])
        self.assertIn('transcript_crosses_splits', rows[2]['experimental_quality_flags'])
        self.assertEqual(rows[3]['experimental_quality_flags'], [])


if __name__ == '__main__':
    unittest.main()
