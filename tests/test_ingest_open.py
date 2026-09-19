import tempfile
import unittest
import json
import bz2
from pathlib import Path
from unittest.mock import patch
import ingest_open as m


class LegacyIngestionTests(unittest.TestCase):
    def test_missing_author_is_explicit_and_preserves_attribution_gap(self):
        payload = b'123\tgbm\tsample\t\\N\n'
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(m, 'RAW', Path(directory)), patch.object(
                m, 'fetch',
                return_value=(bz2.compress(payload), {'raw_path': 'x'}),
            ):
                row = m.tatoeba()[0]
        self.assertIsNone(row['contributor'])
        self.assertIn('missing_contributor', row['quality_flags'])
        self.assertFalse(row['training_eligible'])

    def test_record_defaults_do_not_promote_unreviewed_material(self):
        row = m.record('x', '1', 'text', 'CC-BY-4.0', m.BY, 'author', {})
        self.assertFalse(row['training_eligible'])

    def test_wikimedia_ingestion_renders_plain_garhwali_text(self):
        payload = {
            'batchcomplete': '',
            'query': {'pages': {'1': {
                'pageid': 1,
                'title': 'Wp/gbm/उत्तराखण्ड',
                'revisions': [{
                    'revid': 2,
                    'slots': {'main': {'*': (
                        "__NOTOC__\n'''उत्तरखण्ड''' [[Wp/gbm/भारत|भारतौ]] यऽक राज्य च।\n"
                        '[[Category:Wp/gbm]]'
                    )}},
                }],
            }}},
        }
        with patch.object(m, 'fetch', return_value=(
            json.dumps(payload).encode(), {'raw_path': 'snapshot.json', 'sha256': 'abc'}
        )):
            rows = m.wiki()
        self.assertEqual(rows[0]['text_normalized'], 'उत्तरखण्ड भारतौ यऽक राज्य च।')
        self.assertEqual(rows[0]['text_format'], 'plain_text_from_wikitext')

    def test_wikimedia_ingestion_skips_redirect_pages_before_rendering(self):
        payload = {
            'batchcomplete': '',
            'query': {'pages': {
                '1': {
                    'pageid': 1,
                    'title': 'Wp/gbm/Redirect',
                    'revisions': [{
                        'revid': 2,
                        'slots': {'main': {'*': '#REDIRECT [[Template:Wp/gbm/Standard]]'}},
                    }],
                },
                '3': {
                    'pageid': 3,
                    'title': 'Wp/gbm/पाठ',
                    'revisions': [{
                        'revid': 4,
                        'slots': {'main': {'*': 'गढ़वळी पाठ।'}},
                    }],
                },
            }},
        }
        with patch.object(m, 'fetch', return_value=(
            json.dumps(payload).encode(), {'raw_path': 'snapshot.json', 'sha256': 'abc'}
        )):
            rows = m.wiki()
        self.assertEqual([row['text_normalized'] for row in rows], ['गढ़वळी पाठ।'])


if __name__ == '__main__':
    unittest.main()
