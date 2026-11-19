import unittest

import segment_text_corpus as m


class SegmentTests(unittest.TestCase):
    def test_splits_danda_and_sentence_punctuation(self):
        self.assertEqual(m.segment('एक वाक्य। दूसर वाक्य! तिसर?'),
                         ['एक वाक्य।', 'दूसर वाक्य!', 'तिसर?'])

    def test_splits_double_danda_verses(self):
        self.assertEqual(m.segment('पैली पंक्ति ॥ दूसरी पंक्ति ॥ तिसरी'),
                         ['पैली पंक्ति ॥', 'दूसरी पंक्ति ॥', 'तिसरी'])

    def test_keeps_verse_number_with_its_verse(self):
        self.assertEqual(m.segment('पैली पंक्ति ॥ १ ॥ दूसरी पंक्ति ॥२॥ तिसरी'),
                         ['पैली पंक्ति ॥ १ ॥', 'दूसरी पंक्ति ॥२॥', 'तिसरी'])

    def test_does_not_split_after_devanagari_abbreviation(self):
        self.assertEqual(m.segment('डॉ. शिवानंद नौटियाल न लेखी। अगलो वाक्य'),
                         ['डॉ. शिवानंद नौटियाल न लेखी।', 'अगलो वाक्य'])

    def test_keeps_unpunctuated_text(self):
        self.assertEqual(m.segment('गढ़वाली भाषा'), ['गढ़वाली भाषा'])

    def test_does_not_split_decimal(self):
        self.assertEqual(m.segment('माप 3.14 छ।'), ['माप 3.14 छ।'])

    def test_empty_and_whitespace_text_has_no_segments(self):
        self.assertEqual(m.segment(''), [])
        self.assertEqual(m.segment('  \n '), [])

    def test_repeated_terminal_punctuation_stays_with_its_sentence(self):
        self.assertEqual(m.segment('कख जाणा?? घर!'), ['कख जाणा??', 'घर!'])

    def test_abbreviation_at_end_of_text_is_kept(self):
        self.assertEqual(m.segment('लेखक डॉ.'), ['लेखक डॉ.'])

    def test_segmentation_never_drops_or_reorders_characters(self):
        texts = (
            'एक वाक्य। दूसर वाक्य! तिसर?',
            'पैली पंक्ति ॥ १ ॥ दूसरी पंक्ति ॥२॥ तिसरी',
            'डॉ. शिवानंद नौटियाल न लेखी। माप 3.14 छ। Hello world. Next',
        )
        for text in texts:
            with self.subTest(text=text):
                self.assertEqual(''.join(m.segment(text)).replace(' ', ''), text.replace(' ', ''))

    def test_hash_split_boundaries_give_a_90_5_5_target(self):
        def digest(bucket):
            return f'{bucket:08x}' + '0' * 56

        cases = {0: 'train', 899: 'train', 900: 'validation', 949: 'validation',
                 950: 'test', 999: 'test', 1000: 'train'}
        for bucket, split in cases.items():
            with self.subTest(bucket=bucket):
                self.assertEqual(m.split_for_hash(digest(bucket)), split)

    def test_document_aware_splits_follow_transitive_segment_links(self):
        records = [
            {
                'segment_sha256': '1' * 64,
                'text': 'गढ़वाली वाक्य संख्या 1।',
                'parents': [
                    {'text_sha256': 'a' * 64, 'parent_split': 'train'},
                    {'text_sha256': 'b' * 64, 'parent_split': 'test'},
                ],
            },
            {
                'segment_sha256': '2' * 64,
                'text': 'गढ़वाली वाक्य संख्या 2।',
                'parents': [
                    {'text_sha256': 'b' * 64, 'parent_split': 'test'},
                    {'text_sha256': 'c' * 64, 'parent_split': 'validation'},
                ],
            },
            {
                'segment_sha256': '3' * 64,
                'text': 'गढ़वाली वाक्य संख्या 3।',
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
                'text': 'गढ़वाली वाक्य संख्या 4।',
                'parents': [
                    {'text_sha256': 'a' * 64, 'parent_split': 'train'},
                    {'text_sha256': 'b' * 64, 'parent_split': 'test'},
                ],
            },
            {
                'segment_sha256': '2' * 64,
                'text': 'गढ़वाली वाक्य संख्या 5।',
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
                'text': 'गढ़वाली वाक्य संख्या 6।',
                'parents': [{'text_sha256': 'd' * 64, 'parent_split': 'test'}],
            },
        ]

        assigned, documents = m.assign_document_aware_splits(records)

        self.assertEqual(assigned[0]['split'], 'test')
        self.assertEqual(documents[0]['split'], 'test')

    def test_junk_segment_does_not_connect_documents(self):
        documents = [{'text_sha256': f'{index:064x}', 'parent_split': split}
                     for index, split in enumerate(('train', 'validation', 'test'))]
        records = [
            {'segment_sha256': f'{index + 1:064x}', 'text': f'अलग वाक्य संख्या {index}।',
             'parents': [document]}
            for index, document in enumerate(documents)
        ]
        records.append({'segment_sha256': 'f' * 64, 'text': '.', 'parents': documents})

        assigned, assigned_documents = m.assign_document_aware_splits(records)

        self.assertEqual(
            {row['text_sha256']: row['split'] for row in assigned_documents},
            {document['text_sha256']: document['parent_split'] for document in documents},
        )
        self.assertEqual(len({row['component_sha256'] for row in assigned_documents}), 3)

    def test_connected_component_uses_majority_parent_split(self):
        records = [
            {
                'segment_sha256': '1' * 64,
                'text': 'गढ़वाली वाक्य संख्या 7।',
                'parents': [
                    {'text_sha256': 'a' * 64, 'parent_split': 'train'},
                    {'text_sha256': 'b' * 64, 'parent_split': 'test'},
                ],
            },
            {
                'segment_sha256': '2' * 64,
                'text': 'गढ़वाली वाक्य संख्या 8।',
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
