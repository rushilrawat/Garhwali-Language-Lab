import json
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


if __name__ == '__main__':
    unittest.main()
