import unittest

import clean_text_corpus as m


class CleanTextTests(unittest.TestCase):
    def test_removes_invisible_characters_and_collapses_whitespace(self):
        text, changes = m.clean_text('  गढ़\u200bवाली\n भाषा\ufeff  ')
        self.assertEqual(text, 'गढ़वाली भाषा')
        self.assertEqual(changes, ['removed_invisible_characters', 'normalized_whitespace'])

    def test_flags_markup_urls_replacement_and_mixed_latin(self):
        flags = m.review_flags('<b>गढ़वाली</b> https://example.com � hello')
        self.assertIn('html_markup', flags)
        self.assertIn('url', flags)
        self.assertIn('replacement_character', flags)
        self.assertIn('mixed_latin_devanagari', flags)

    def test_native_text_needs_no_automatic_change(self):
        text = 'म्यार गढ़वाली भाषा'
        self.assertEqual(m.clean_text(text), (text, []))


if __name__ == '__main__':
    unittest.main()
