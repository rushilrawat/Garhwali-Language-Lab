import unittest

import run_masked_lm_baseline as m


class MaskedLanguageModelBaselineTests(unittest.TestCase):
    def test_mask_selection_is_deterministic_and_excludes_special_tokens(self):
        token_ids = [101, 20, 21, 22, 102, 0]
        attention = [1, 1, 1, 1, 1, 0]
        first = m.select_mask_positions(token_ids, attention, {0, 101, 102}, 'record-a', 0.15, 17)
        second = m.select_mask_positions(token_ids, attention, {0, 101, 102}, 'record-a', 0.15, 17)
        self.assertEqual(first, second)
        self.assertTrue(first)
        self.assertTrue(set(first) <= {1, 2, 3})

    def test_mask_selection_returns_empty_when_no_content_tokens_exist(self):
        self.assertEqual(
            m.select_mask_positions([101, 102, 0], [1, 1, 0], {0, 101, 102}, 'x', 0.15, 17),
            [],
        )


if __name__ == '__main__':
    unittest.main()
