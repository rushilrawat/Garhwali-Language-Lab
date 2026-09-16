import unittest

import sync_release_index as m


class SyncReleaseIndexTests(unittest.TestCase):
    def test_refreshes_dynamic_package_and_split_counts(self):
        index = {
            'text': {},
            'all_data_package': {},
            'public_text_release': {},
            'evaluation_candidates': {},
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

        refreshed = m.refresh(index, splits, text, public, all_data)
        self.assertEqual(refreshed['text']['total'], 15)
        self.assertEqual(refreshed['text']['unique_parent_documents'], 7)
        self.assertEqual(refreshed['public_text_release']['exact_unique_with_public_rights_basis'], 2)
        self.assertEqual(refreshed['public_text_release']['rights_pending_catalog_records'], 5)
        self.assertEqual(refreshed['all_data_package']['transcript_only_package_rows'], 31)
        self.assertEqual(refreshed['all_data_package']['full_text_segments'], 15)
        self.assertEqual(refreshed['structured_knowledge']['records'], 1)
        self.assertEqual(refreshed['evaluation_candidates']['text'], 4)


if __name__ == '__main__':
    unittest.main()
