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


if __name__ == '__main__': unittest.main()
