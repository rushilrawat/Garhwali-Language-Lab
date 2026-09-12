import json
import tempfile
import unittest
from pathlib import Path

import build_instruction_dataset as m


class InstructionDatasetTests(unittest.TestCase):
    def test_parallel_pair_produces_bidirectional_records_in_parent_split(self):
        pair = {
            'pair_sha256': 'pair', 'text_sha256': 'parent',
            'garhwali': 'मी ठीक छौं', 'english': 'I am fine',
            'source_id': 'source', 'rights_status': 'local_experimental',
        }
        records = m.parallel_instructions(pair, 'validation')
        self.assertEqual(len(records), 2)
        self.assertTrue(all(record['split'] == 'validation' for record in records))
        self.assertEqual({record['task'] for record in records}, {
            'garhwali_to_english', 'english_to_garhwali',
        })

    def test_lexicon_instructions_preserve_semantic_domain_and_provenance(self):
        row = {
            'text_sha256': 'word', 'form': 'हत्थ',
            'glosses': {'english': ['hand'], 'hindi': ['हाथ'], 'other': []},
            'semantic_domains': ['body'], 'provenance': [{'source_id': 'lexicon'}],
        }
        records = m.lexicon_instructions(row, 'train')
        self.assertEqual(len(records), 4)
        self.assertTrue(all(record['semantic_domains'] == ['body'] for record in records))
        self.assertTrue(all(record['provenance'] == row['provenance'] for record in records))

    def test_build_keeps_parent_groups_disjoint_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text = root / 'text.jsonl'
            parallel = root / 'parallel.jsonl'
            lexicon = root / 'lexicon.jsonl'
            text.write_text('\n'.join([
                json.dumps({'text_sha256': 'a', 'split': 'train'}),
                json.dumps({'text_sha256': 'b', 'split': 'test'}),
            ]) + '\n')
            pair = {
                'pair_sha256': 'p', 'text_sha256': 'a', 'garhwali': 'गढ़वाली',
                'english': 'Garhwali', 'source_id': 'x',
            }
            parallel.write_text((json.dumps(pair, ensure_ascii=False) + '\n') * 2)
            lexicon.write_text(json.dumps({
                'text_sha256': 'b', 'form': 'हत्थ',
                'glosses': {'english': ['hand'], 'hindi': [], 'other': []},
                'semantic_domains': [], 'provenance': [],
            }, ensure_ascii=False) + '\n')
            report = m.build(text, parallel, lexicon, root / 'out')
            self.assertEqual(report['records']['train'], 2)
            self.assertEqual(report['records']['test'], 2)
            self.assertEqual(report['integrity']['parent_cross_split'], 0)
            self.assertEqual(report['integrity']['duplicate_instruction_pairs'], 2)


if __name__ == '__main__':
    unittest.main()
