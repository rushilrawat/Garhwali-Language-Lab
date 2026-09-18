import json
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import native_review_workflow as m


class NativeReviewWorkflowTests(unittest.TestCase):
    def test_two_matching_reviewers_adjudicate_and_disagreement_stays_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decisions = root / 'decisions.jsonl'
            rows = [
                {'review_type': 'lexicon', 'target_id': 'a', 'reviewer_id': 'r1', 'round': 1, 'decision': 'accept', 'corrected_text': 'पाणी'},
                {'review_type': 'lexicon', 'target_id': 'a', 'reviewer_id': 'r2', 'round': 2, 'decision': 'accept', 'corrected_text': 'पाणी'},
                {'review_type': 'text', 'target_id': 'b', 'reviewer_id': 'r1', 'round': 1, 'decision': 'accept', 'corrected_text': 'एक'},
                {'review_type': 'text', 'target_id': 'b', 'reviewer_id': 'r2', 'round': 2, 'decision': 'reject', 'corrected_text': ''},
                {'review_type': 'dialect', 'target_id': 'c', 'reviewer_id': 'r1', 'round': 1, 'decision': 'accept', 'dialect_labels': ['Tehriyali']},
            ]
            decisions.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')

            report = m.adjudicate(decisions, root / 'out')

            accepted = [json.loads(line) for line in (root / 'out/adjudicated.jsonl').read_text().splitlines()]
            disagreements = [json.loads(line) for line in (root / 'out/disagreements.jsonl').read_text().splitlines()]
            pending = [json.loads(line) for line in (root / 'out/pending.jsonl').read_text().splitlines()]
            self.assertEqual([(row['review_type'], row['target_id']) for row in accepted], [('lexicon', 'a')])
            self.assertEqual([(row['review_type'], row['target_id']) for row in disagreements], [('text', 'b')])
            self.assertEqual([(row['review_type'], row['target_id']) for row in pending], [('dialect', 'c')])
            self.assertEqual(report, {'adjudicated': 1, 'decisions': 5, 'disagreements': 1, 'pending_second_review': 1})

    def test_rejects_duplicate_reviewer_as_two_pass_review(self):
        decisions = [
            {'review_type': 'text', 'target_id': 'a', 'reviewer_id': 'same', 'round': 1, 'decision': 'accept'},
            {'review_type': 'text', 'target_id': 'a', 'reviewer_id': 'same', 'round': 2, 'decision': 'accept'},
        ]
        result = m.adjudicate_rows(decisions)
        self.assertEqual(len(result['pending']), 1)
        self.assertEqual(result['adjudicated'], [])

    def test_reviewer_notes_do_not_create_a_false_decision_disagreement(self):
        decisions = [
            {
                'review_type': 'text_accuracy', 'target_id': 'a',
                'reviewer_id': 'r1', 'round': 1, 'decision': 'accept_source_form',
                'notes': 'common local spelling',
            },
            {
                'review_type': 'text_accuracy', 'target_id': 'a',
                'reviewer_id': 'r2', 'round': 2, 'decision': 'accept_source_form',
                'notes': 'checked against English context',
            },
        ]

        result = m.adjudicate_rows(decisions)

        self.assertEqual(len(result['adjudicated']), 1)
        self.assertEqual(result['disagreements'], [])
        self.assertEqual(result['adjudicated'][0]['reviewer_notes'], {
            'r1': 'common local spelling',
            'r2': 'checked against English context',
        })

    def test_materialize_reviewed_records_preserves_source_and_applies_correction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet_dir = root / 'packets'
            result_dir = root / 'results'
            output_dir = root / 'reviewed'
            packet_dir.mkdir()
            result_dir.mkdir()
            (packet_dir / 'ocr.jsonl').write_text(json.dumps({
                'review_type': 'ocr',
                'target_id': 'abc',
                'payload': {'text': 'गढवाली', 'source_id': 'scan-1'},
            }, ensure_ascii=False) + '\n', encoding='utf-8')
            (result_dir / 'adjudicated.jsonl').write_text(json.dumps({
                'review_type': 'ocr',
                'target_id': 'abc',
                'status': 'two_pass_agreement',
                'decision': 'correct',
                'corrected_text': 'गढ़वाली',
                'reviewer_ids': ['r1', 'r2'],
            }, ensure_ascii=False) + '\n', encoding='utf-8')

            report = m.materialize_reviewed_records(packet_dir, result_dir, output_dir)

            rows = m.read_jsonl(output_dir / 'accepted' / 'ocr.jsonl')
            self.assertEqual(report['accepted'], 1)
            self.assertEqual(rows[0]['source_payload']['text'], 'गढवाली')
            self.assertEqual(rows[0]['effective_text'], 'गढ़वाली')
            self.assertEqual(rows[0]['review']['reviewer_ids'], ['r1', 'r2'])

    def test_build_packets_merges_multiple_sources_for_one_review_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / 'first.jsonl'
            second = root / 'second.jsonl'
            first.write_text('{"audio_sha256":"a"}\n', encoding='utf-8')
            second.write_text('{"audio_sha256":"b"}\n', encoding='utf-8')
            sources = (
                ('transcript', 'first.jsonl', 'audio_sha256'),
                ('transcript', 'second.jsonl', 'audio_sha256'),
            )

            with patch.object(m, 'PACKET_SOURCES', sources):
                report = m.build_packets(root, root / 'packets')

            rows = m.read_jsonl(root / 'packets/transcript.jsonl')
            self.assertEqual(report['packet_counts']['transcript'], 2)
            self.assertEqual([row['target_id'] for row in rows], ['a', 'b'])

    def test_text_accuracy_packet_exposes_alignment_and_decision_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'accuracy.jsonl'
            source.write_text(json.dumps({
                'text_sha256': 'text-1',
                'text': 'नव पन्ना',
                'review_priority': {'label': 'source_accuracy', 'reasons': ['native_accuracy_unverified']},
                'provenance': [{
                    'source_id': 'opus_translatewiki_gbm',
                    'linguistic_metadata': {'english_alignments': ['New page']},
                }],
            }, ensure_ascii=False) + '\n', encoding='utf-8')

            with patch.object(m, 'PACKET_SOURCES', (
                ('text_accuracy', 'accuracy.jsonl', 'text_sha256'),
            )):
                report = m.build_packets(root, root / 'packets')

            packet = m.read_jsonl(root / 'packets/text_accuracy.jsonl')[0]
            context = packet['review_context']
            self.assertEqual(report['packet_counts']['text_accuracy'], 1)
            self.assertEqual(context['display_text'], 'नव पन्ना')
            self.assertEqual(context['aligned_meanings'], ['New page'])
            self.assertEqual(context['source_ids'], ['opus_translatewiki_gbm'])
            self.assertEqual(context['review_priority'], 'source_accuracy')
            self.assertIn('correct_text', context['decision_options'])
            self.assertFalse(context['source_evidence_is_native_review'])

    def test_transcript_packet_exposes_audio_and_model_hypotheses(self):
        row = {
            'audio_sha256': 'audio-1',
            'local_audio_path': 'data/vaani/example.wav',
            'reference_text': 'अर येक यखा का जु छा',
            'duration_seconds': 3.8,
            'district': 'TehriGarhwal',
            'model_evidence': {'hypotheses': {'model-a': 'अर एक'}},
        }

        context = m.review_context('transcript', row)

        self.assertTrue(context['requires_audio_listening'])
        self.assertEqual(context['audio_path'], 'data/vaani/example.wav')
        self.assertEqual(context['reference_text'], 'अर येक यखा का जु छा')
        self.assertEqual(context['model_hypotheses'], {'model-a': 'अर एक'})

    def test_review_templates_are_flat_and_ready_for_independent_reviewers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet_dir = root / 'packets'
            packet_dir.mkdir()
            packet = {
                'review_type': 'text_accuracy',
                'target_id': 'text-1',
                'required_independent_reviews': 2,
                'review_context': {
                    'display_text': 'नव पन्ना',
                    'aligned_meanings': ['New page'],
                    'source_ids': ['opus_translatewiki_gbm'],
                    'review_priority': 'source_accuracy',
                    'review_reasons': ['native_accuracy_unverified'],
                    'decision_options': ['accept_source_form', 'correct_text'],
                },
                'payload': {},
            }
            m.write_jsonl(packet_dir / 'text_accuracy.jsonl', [packet])

            report = m.write_review_templates(packet_dir, root / 'templates')

            with (root / 'templates/text_accuracy.csv').open(encoding='utf-8', newline='') as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(report['template_counts'], {'text_accuracy': 1})
            self.assertEqual(rows[0]['target_id'], 'text-1')
            self.assertEqual(rows[0]['source_text'], 'नव पन्ना')
            self.assertEqual(rows[0]['aligned_meanings'], 'New page')
            self.assertEqual(rows[0]['decision'], '')
            self.assertEqual(rows[0]['reviewer_id'], '')
            self.assertEqual(rows[0]['round'], '')

    def test_flat_templates_skip_packet_types_without_review_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet_dir = root / 'packets'
            packet_dir.mkdir()
            m.write_jsonl(packet_dir / 'dialect.jsonl', [{
                'review_type': 'dialect', 'target_id': 'text-1',
                'required_independent_reviews': 2, 'review_context': {},
                'payload': {'text': 'गढ़वाली'},
            }])

            report = m.write_review_templates(packet_dir, root / 'templates')

            self.assertEqual(report['template_counts'], {})
            self.assertFalse((root / 'templates/dialect.csv').exists())

    def test_imports_completed_csv_decisions_and_ignores_unfilled_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / 'reviewer-one.csv'
            fields = [
                'review_type', 'target_id', 'decision', 'corrected_text',
                'language', 'dialect_labels', 'pronunciation', 'notes',
                'reviewer_id', 'round',
            ]
            with first.open('w', encoding='utf-8', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow({
                    'review_type': 'text_accuracy', 'target_id': 'text-1',
                    'decision': 'correct_text', 'corrected_text': 'नौं पन्ना',
                    'language': 'gbm', 'dialect_labels': 'Tehriyali | Srinagariya',
                    'pronunciation': '', 'notes': 'checked in context',
                    'reviewer_id': 'reviewer-1', 'round': '1',
                })
                writer.writerow({
                    'review_type': 'text_accuracy', 'target_id': 'text-2',
                    'decision': '', 'reviewer_id': 'reviewer-1', 'round': '1',
                })

            report = m.import_review_csv_files([first], root / 'decisions.jsonl')

            rows = m.read_jsonl(root / 'decisions.jsonl')
            self.assertEqual(report['decisions'], 1)
            self.assertEqual(rows[0]['corrected_text'], 'नौं पन्ना')
            self.assertEqual(rows[0]['dialect_labels'], ['Tehriyali', 'Srinagariya'])
            self.assertEqual(rows[0]['round'], 1)


if __name__ == '__main__':
    unittest.main()
