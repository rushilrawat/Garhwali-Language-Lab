import unittest

import segment_text_corpus as m


class SegmentTests(unittest.TestCase):
    def test_splits_danda_and_sentence_punctuation(self):
        self.assertEqual(m.segment('एक वाक्य। दूसर वाक्य! तिसर?'),
                         ['एक वाक्य।', 'दूसर वाक्य!', 'तिसर?'])

    def test_keeps_unpunctuated_text(self):
        self.assertEqual(m.segment('गढ़वाली भाषा'), ['गढ़वाली भाषा'])

    def test_does_not_split_decimal(self):
        self.assertEqual(m.segment('माप 3.14 छ।'), ['माप 3.14 छ।'])

    def test_segment_split_is_deterministic(self):
        digest = 'a' * 64
        self.assertEqual(m.split_for_hash(digest), m.split_for_hash(digest))
        self.assertIn(m.split_for_hash(digest), {'train', 'validation', 'test'})

    def test_document_aware_splits_follow_transitive_segment_links(self):
        records = [
            {
                'segment_sha256': '1' * 64,
                'parents': [
                    {'text_sha256': 'a' * 64, 'parent_split': 'train'},
                    {'text_sha256': 'b' * 64, 'parent_split': 'test'},
                ],
            },
            {
                'segment_sha256': '2' * 64,
                'parents': [
                    {'text_sha256': 'b' * 64, 'parent_split': 'test'},
                    {'text_sha256': 'c' * 64, 'parent_split': 'validation'},
                ],
            },
            {
                'segment_sha256': '3' * 64,
                'parents': [
                    {'text_sha256': 'd' * 64, 'parent_split': 'train'},
                ],
            },
        ]

        assigned, documents = m.assign_document_aware_splits(records)

        linked_splits = {row['split'] for row in assigned[:2]}
        self.assertEqual(len(linked_splits), 1)
        by_document = {row['text_sha256']: row for row in documents}
        self.assertEqual(by_document['a' * 64]['split'], by_document['c' * 64]['split'])
        self.assertEqual(by_document['a' * 64]['component_document_count'], 3)
        self.assertNotEqual(
            by_document['a' * 64]['component_sha256'],
            by_document['d' * 64]['component_sha256'],
        )

    def test_document_aware_assignment_is_input_order_independent(self):
        records = [
            {
                'segment_sha256': '1' * 64,
                'parents': [
                    {'text_sha256': 'a' * 64, 'parent_split': 'train'},
                    {'text_sha256': 'b' * 64, 'parent_split': 'test'},
                ],
            },
            {
                'segment_sha256': '2' * 64,
                'parents': [{'text_sha256': 'c' * 64, 'parent_split': 'train'}],
            },
        ]

        assigned_a, documents_a = m.assign_document_aware_splits(records)
        assigned_b, documents_b = m.assign_document_aware_splits(list(reversed(records)))

        self.assertEqual(
            {row['segment_sha256']: row['split'] for row in assigned_a},
            {row['segment_sha256']: row['split'] for row in assigned_b},
        )
        self.assertEqual(documents_a, documents_b)

    def test_single_document_preserves_its_existing_split(self):
        records = [
            {
                'segment_sha256': '1' * 64,
                'parents': [{'text_sha256': 'd' * 64, 'parent_split': 'test'}],
            },
        ]

        assigned, documents = m.assign_document_aware_splits(records)

        self.assertEqual(assigned[0]['split'], 'test')
        self.assertEqual(documents[0]['split'], 'test')

    def test_connected_component_uses_majority_parent_split(self):
        records = [
            {
                'segment_sha256': '1' * 64,
                'parents': [
                    {'text_sha256': 'a' * 64, 'parent_split': 'train'},
                    {'text_sha256': 'b' * 64, 'parent_split': 'test'},
                ],
            },
            {
                'segment_sha256': '2' * 64,
                'parents': [
                    {'text_sha256': 'b' * 64, 'parent_split': 'test'},
                    {'text_sha256': 'c' * 64, 'parent_split': 'test'},
                ],
            },
        ]

        assigned, documents = m.assign_document_aware_splits(records)

        self.assertEqual({row['split'] for row in assigned}, {'test'})
        self.assertEqual({row['split'] for row in documents}, {'test'})


if __name__ == '__main__': unittest.main()
