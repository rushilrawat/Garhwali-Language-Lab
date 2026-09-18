import json
import tempfile
import unittest
from pathlib import Path

import propose_text_cleanup as m


class TextCleanupProposalTests(unittest.TestCase):
    def test_mechanical_cleanup_is_reversible_and_conservative(self):
        proposal = m.mechanical_cleanup('गढ़वाली\u200b  पाठ  ।।।।')
        self.assertEqual(proposal['proposed_text'], 'गढ़वाली पाठ ।।।')
        self.assertEqual(
            proposal['changes'],
            ['removed_invisible_characters', 'collapsed_whitespace', 'limited_repeated_punctuation'],
        )

    def test_spelling_candidate_requires_rare_token_and_strong_corpus_evidence(self):
        frequencies = {'गढ़वाली': 40, 'गढ़वालि': 1, 'भाषा': 20}
        index = m.build_deletion_index(frequencies, minimum_frequency=5)
        candidates = m.spelling_candidates('गढ़वालि भाषा', frequencies, index)
        self.assertEqual(candidates[0]['observed'], 'गढ़वालि')
        self.assertEqual(candidates[0]['candidate'], 'गढ़वाली')
        self.assertEqual(candidates[0]['edit_distance'], 1)
        self.assertEqual(candidates[0]['status'], 'proposal_only')

    def test_existing_word_and_unrelated_word_are_not_rewritten(self):
        frequencies = {'गढ़वाली': 40, 'भाषा': 20, 'कखगघ': 1}
        index = m.build_deletion_index(frequencies, minimum_frequency=5)
        self.assertEqual(m.spelling_candidates('गढ़वाली कखगघ', frequencies, index), [])

    def test_language_signal_preserves_source_label(self):
        result = m.language_signal(
            {'language_bucket': 'garhwali_candidate', 'language_quality': {'confidence': 'high'}},
            model_loss=12.0,
            high_loss_threshold=10.0,
        )
        self.assertEqual(result['status'], 'model_source_disagreement')
        self.assertEqual(result['decision'], 'retain_source_label')

    def test_proposal_retains_original_and_all_data_status(self):
        row = {
            'text_sha256': 'abc',
            'text': 'गढ़वालि',
            'text_model': 'गढ़वालि',
            'language_bucket': 'garhwali_candidate',
            'language_quality': {'confidence': 'medium'},
            'dialect_quality': {'status': 'unlabeled'},
            'genre_quality': {'tags': ['folk_text']},
            'cleanup_review_flags': ['machine_ocr'],
            'provenance': [{'source_id': 'book'}],
        }
        frequencies = {'गढ़वाली': 40, 'गढ़वालि': 1}
        proposal = m.build_proposal(
            row, frequencies, m.build_deletion_index(frequencies, 5), model_loss=8.0,
            high_loss_threshold=10.0,
        )
        self.assertEqual(proposal['text_original'], 'गढ़वालि')
        self.assertEqual(proposal['text_current'], 'गढ़वालि')
        self.assertTrue(proposal['active_for_experiment'])
        self.assertEqual(proposal['application_status'], 'proposal_only')
        self.assertNotIn('quarantine', json.dumps(proposal).casefold())

    def test_pipeline_writes_every_input_record_and_summary(self):
        rows = [
            {
                'text_sha256': 'a', 'text': 'गढ़वाली', 'text_model': 'गढ़वाली',
                'language_bucket': 'garhwali_candidate',
                'language_quality': {'confidence': 'high'},
                'dialect_quality': {'status': 'explicit_label'},
                'genre_quality': {'tags': ['sentence']}, 'provenance': [],
            },
            {
                'text_sha256': 'b', 'text': 'गढ़वालि\u200b', 'text_model': 'गढ़वालि\u200b',
                'language_bucket': 'review', 'language_quality': {'confidence': 'low'},
                'dialect_quality': {'status': 'unlabeled'},
                'genre_quality': {'tags': ['folk_text']}, 'provenance': [],
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.jsonl'
            source.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
            report = m.run(source, root / 'out', model_scores={'a': 1.0, 'b': 9.0})
            written = [json.loads(line) for line in (root / 'out/proposals.jsonl').read_text().splitlines()]
            self.assertEqual(len(written), 2)
            self.assertEqual(report['records']['total'], 2)
            self.assertEqual(report['records']['active_for_experiment'], 2)
            self.assertEqual(report['records']['excluded'], 0)


if __name__ == '__main__':
    unittest.main()
