import unittest

import run_nllb_translation_baseline as m


class NllbTranslationBaselineTests(unittest.TestCase):
    def test_selects_deterministic_test_subset(self):
        rows = [
            {'split': 'dev', 'record_id': '0'},
            {'split': 'test', 'record_id': 'b'},
            {'split': 'test', 'record_id': 'a'},
        ]
        self.assertEqual(
            [row['record_id'] for row in m.select_test_rows(rows, 1)],
            ['a'],
        )

    def test_zero_limit_keeps_complete_test_split(self):
        rows = [{'split': 'test', 'record_id': value} for value in ('b', 'a')]
        self.assertEqual(len(m.select_test_rows(rows, 0)), 2)


if __name__ == '__main__':
    unittest.main()
