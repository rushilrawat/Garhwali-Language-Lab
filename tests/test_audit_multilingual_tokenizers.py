import unittest

import audit_multilingual_tokenizers as m


class FakeTokenizer:
    unk_token_id = 0
    vocab_size = 10

    def __call__(self, text, add_special_tokens=False):
        return {'input_ids': [0 if token == '?' else len(token) for token in text.split()]}


class MultilingualTokenizerAuditTests(unittest.TestCase):
    def test_scores_fertility_unknowns_and_context_overflow(self):
        report = m.score_tokenizer(FakeTokenizer(), ['गढ़वाली भाषा', '? शब्द'], max_length=1)
        self.assertEqual(report['records'], 2)
        self.assertEqual(report['tokens'], 4)
        self.assertEqual(report['whitespace_words'], 4)
        self.assertEqual(report['fertility_tokens_per_word'], 1.0)
        self.assertEqual(report['unknown_token_rate'], 0.25)
        self.assertEqual(report['sequences_over_context'], 2)

    def test_empty_input_is_reported_without_division_error(self):
        report = m.score_tokenizer(FakeTokenizer(), [''], max_length=8)
        self.assertEqual(report['empty_encodings'], 1)
        self.assertEqual(report['fertility_tokens_per_word'], 0.0)


if __name__ == '__main__':
    unittest.main()
