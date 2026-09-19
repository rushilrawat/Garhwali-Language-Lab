import unittest

import sync_release_index as m


class SyncReleaseIndexTests(unittest.TestCase):
    def test_refreshes_dynamic_package_and_split_counts(self):
        index = {
            'text': {},
            'all_data_package': {},
            'public_text_release': {},
            'evaluation_candidates': {},
            'garhwali_bench': {},
            'language_resources': {},
        }
        splits = {
            'text': {'records': {'train': 10, 'validation': 2, 'test': 3}},
            'evaluation_candidates': {'text_records': 4},
        }
        text = {'unique_texts': 7}
        public = {
            'catalog_records': 7,
            'catalog_redacted_text_records': 5,
            'configs': {
                'text/train': {'records': 2},
                'catalog/train': {'records': 7},
                'geography/train': {'records': 1},
            },
        }
        all_data = {
            'catalog_records': 7,
            'catalog_redacted_text_records': 0,
            'all_collected_text_values_included': True,
            'configs': {
                'text/train': {'records': 10},
                'text/validation': {'records': 2},
                'text/test': {'records': 3},
                'asr/train': {'records': 4},
                'lexicon/train': {'records': 5},
                'instructions/train': {'records': 6},
                'geography/train': {'records': 1},
            },
        }

        benchmark = {
            'release_id': 'bench', 'status': 'candidate',
            'native_reviewed': False, 'dialect_aware': False,
            'records': {'external_total': 3, 'text_evaluation': 2, 'asr_evaluation': 1},
            'leakage': {'external_exact_train_text': 0,
                        'internal_text_exact_train_text': 0, 'asr_speaker_overlap': 0},
            'baselines': {'character_bigram': {'perplexity': 12.5,
                                                'oov_character_rate': 0.01}},
        }
        resources = {
            'tokenizer_type': 'unicode_character', 'tokenizer_vocabulary_size': 10,
            'tokenizer_training_texts': 10, 'word_types': 20,
            'pronunciation_candidates': 5,
            'pronunciation_with_source_phonetics': 2, 'tts_pairs': 3,
        }
        refreshed = m.refresh(
            index, splits, text, public, all_data, benchmark, resources
        )
        self.assertEqual(refreshed['text']['total'], 15)
        self.assertEqual(refreshed['text']['unique_parent_documents'], 7)
        self.assertEqual(refreshed['public_text_release']['exact_unique_with_public_rights_basis'], 2)
        self.assertEqual(refreshed['public_text_release']['rights_pending_catalog_records'], 5)
        self.assertEqual(refreshed['all_data_package']['transcript_only_package_rows'], 31)
        self.assertEqual(refreshed['all_data_package']['full_text_segments'], 15)
        self.assertEqual(refreshed['structured_knowledge']['records'], 1)
        self.assertEqual(refreshed['evaluation_candidates']['text'], 2)
        self.assertEqual(refreshed['garhwali_bench']['character_bigram_perplexity'], 12.5)
        self.assertEqual(refreshed['language_resources']['word_types'], 20)


if __name__ == '__main__':
    unittest.main()
