import unittest

import prepare_transcripts as m


class TranscriptTests(unittest.TestCase):
    def test_spoken_text_removes_annotations_but_keeps_words(self):
        source = '<noise> होटल {hotel} म लोग [breathing] <pause> बैठीं। </pause></noise>'
        self.assertEqual(m.spoken_text(source), 'होटल म लोग बैठीं।')

    def test_annotation_flags_detect_unbalanced_known_tags(self):
        self.assertIn('unbalanced_noise_tag', m.annotation_flags('<noise> पाठ'))
        self.assertEqual(m.annotation_flags('<noise> पाठ </noise>'), [])

    def test_batch_id_is_stable(self):
        self.assertEqual(m.batch_id(0), 'batch-0001')
        self.assertEqual(m.batch_id(1000), 'batch-0002')


if __name__ == '__main__': unittest.main()
