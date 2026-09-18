import unittest

import deep_cleanup as m


class DeepCleanupTests(unittest.TestCase):
    def test_removes_known_speech_annotations_and_glosses(self):
        source = '<noise> होटल {hotel} मा [breathing] लोग <pause> बैठीं। </pause></noise>'
        text, changes, flags = m.clean_model_text(source)
        self.assertEqual(text, 'होटल मा लोग बैठीं।')
        self.assertIn('removed_speech_annotations', changes)
        self.assertEqual(flags, [])

    def test_truncation_marker_is_removed_and_flagged(self):
        text, changes, flags = m.clean_model_text('म्यार वाक्य --')
        self.assertEqual(text, 'म्यार वाक्य')
        self.assertIn('removed_truncation_marker', changes)
        self.assertIn('possibly_incomplete', flags)

    def test_strips_markup_without_changing_words(self):
        text, changes, flags = m.clean_model_text('<b>गढ़वाली</b> भाषा')
        self.assertEqual(text, 'गढ़वाली भाषा')
        self.assertIn('removed_markup_tags', changes)

    def test_removes_complete_nested_mediawiki_placeholder(self):
        text, changes, flags = m.clean_model_text('खोजा {{SITENAME}}')
        self.assertEqual(text, 'खोजा')
        self.assertNotIn('}', text)
        self.assertIn('removed_speech_annotations', changes)


if __name__ == '__main__': unittest.main()
