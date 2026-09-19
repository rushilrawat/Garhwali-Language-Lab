import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import ingest_web_learning as m


class WebLearningTests(unittest.TestCase):
    def test_extracts_labeled_pairs(self):
        text = 'English: What is your name? Garhwali: Tyar naam kya cha? English: Fine Garhwali: Theek cha'
        self.assertEqual(m.labeled_pairs(text), [('What is your name?', 'Tyar naam kya cha?'), ('Fine', 'Theek cha')])

    def test_pairwise_values(self):
        self.assertEqual(m.pairwise(['I','Mi','He','Wu']), [('I','Mi'),('He','Wu')])

    def test_labeled_pairs_stop_before_page_footer(self):
        text = 'English: Fine Garhwali: Theek cha. Continue to Lesson 2 Posted by: Author'
        self.assertEqual(m.labeled_pairs(text), [('Fine', 'Theek cha.')])

    def test_failed_refresh_does_not_overwrite_existing_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'existing.jsonl'
            output.write_text('preserve me\n')
            with (
                patch.object(m, 'RAW', root / 'raw'),
                patch.object(m, 'OUT', output),
                patch.object(m, 'fetch', side_effect=OSError('offline')),
                self.assertRaisesRegex(RuntimeError, 'incomplete'),
            ):
                m.main()
            self.assertEqual(output.read_text(), 'preserve me\n')


if __name__ == '__main__': unittest.main()
