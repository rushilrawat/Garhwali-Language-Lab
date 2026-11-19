import unittest

import clean_text_corpus as m


class CleanTextTests(unittest.TestCase):
    def test_removes_invisible_characters_and_collapses_whitespace(self):
        text, changes = m.clean_text('  गढ़\u200bवाली\n भाषा\ufeff  ')
        self.assertEqual(text, 'गढ़वाली भाषा')
        self.assertEqual(changes, ['removed_invisible_characters', 'normalized_whitespace'])

    def test_flags_markup_urls_replacement_and_mixed_latin(self):
        flags = m.review_flags('<b>गढ़वाली</b> https://example.com \ufffd hello')
        self.assertEqual(flags, ['html_markup', 'url', 'replacement_character', 'mixed_latin_devanagari'])

    def test_flags_text_without_devanagari_and_very_short_text(self):
        self.assertEqual(m.review_flags('ab'), ['no_devanagari', 'very_short'])
        self.assertEqual(m.review_flags(''), ['no_devanagari', 'very_short'])
        self.assertEqual(m.review_flags('www.example.org'), ['url', 'no_devanagari'])

    def test_clean_native_text_has_no_flags(self):
        self.assertEqual(m.review_flags('म्यार गढ़वाली भाषा'), [])

    def test_whitespace_only_change_is_reported_alone(self):
        self.assertEqual(m.clean_text('गढ़वाली\t\tभाषा'), ('गढ़वाली भाषा', ['normalized_whitespace']))

    def test_cleaning_is_idempotent(self):
        once, _ = m.clean_text(' गढ़\u200cवाली \n\n भाषा ')
        self.assertEqual(m.clean_text(once), (once, []))

    def test_precomposed_nukta_letters_are_nfc_normalized(self):
        text, _ = m.clean_text('\u095c')  # precomposed DDDHA is a composition exclusion
        self.assertEqual(text, '\u0921\u093c')

    def test_native_text_needs_no_automatic_change(self):
        text = 'म्यार गढ़वाली भाषा'
        self.assertEqual(m.clean_text(text), (text, []))


if __name__ == '__main__':
    unittest.main()
