import csv
import importlib.util
import io
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/ingest_lsi_garhwali_specimens.py'
SPEC = importlib.util.spec_from_file_location('ingest_lsi_garhwali_specimens', SCRIPT)
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class LsiGarhwaliSpecimenTests(unittest.TestCase):
    def make_tsv(self):
        output = io.StringIO()
        writer = csv.writer(output, delimiter='\t')
        writer.writerow(('level', 'page_num', 'block_num', 'par_num', 'line_num',
                         'word_num', 'left', 'top', 'width', 'height', 'conf', 'text'))
        rows = [
            (1, 1, 1, 1, 1, 1, 100, 100, 50, 20, 90, 'शीर्षक'),
            (5, 1, 1, 1, 2, 1, 100, 400, 40, 20, 90, 'यह'),
            (5, 1, 1, 1, 2, 2, 150, 400, 70, 20, 80, 'गढ़वाली'),
            (5, 1, 1, 1, 2, 3, 230, 400, 40, 20, 85, 'पाठ'),
            (5, 1, 1, 1, 4, 1, 100, 2600, 40, 20, 90, 'अंत'),
            (5, 1, 1, 1, 5, 1, 100, 800, 60, 20, 90, 'English'),
        ]
        for word_num in range(4, 80):
            rows.append((5, 1, 1, 1, 2, word_num, 230 + word_num * 50,
                         400, 40, 20, 90, 'शब्द'))
        for row in rows:
            writer.writerow(row)
        return output.getvalue()

    def test_filters_page_heading_footer_and_non_devanagari_lines(self):
        text, confidence = module.parse_page_tsv(self.make_tsv(), 298, 300)
        self.assertTrue(text.startswith('यह गढ़वाली पाठ'))
        self.assertNotIn('शीर्षक', text)
        self.assertNotIn('अंत', text)
        self.assertNotIn('English', text)
        self.assertGreater(confidence, 89)
        self.assertGreaterEqual(module.devanagari_share(text), 0.75)

    def test_rejects_page_without_enough_garhwali_script_text(self):
        with self.assertRaisesRegex(ValueError, 'too little'):
            module.parse_page_tsv(self.make_tsv(), 298, 1000)

    def test_all_new_specimens_are_explicitly_labeled_garhwali_dialects(self):
        new_ids = {
            'lsi_1916_garhwali:lohbya_specimen_4',
            'lsi_1916_garhwali:badhani_specimen_5',
            'lsi_1916_garhwali:dasaulya_specimen_6',
            'lsi_1916_garhwali:nagpuriya_specimen_8',
            'lsi_1916_garhwali:salani_specimen_9',
        }
        configured = {row['record_id']: row for row in module.SPECIMENS}
        self.assertTrue(new_ids <= configured.keys())
        for record_id in new_ids:
            row = configured[record_id]
            self.assertIn('Garhwali', row['language_evidence'])
            self.assertTrue(all(page > 0 and top >= 0 for page, top in row['pages']))

    def test_short_continuation_page_can_use_a_lower_character_floor(self):
        text, _ = module.parse_page_tsv(self.make_tsv(), 329, 300, min_chars=100)
        self.assertGreaterEqual(len(text), 100)


if __name__ == '__main__':
    unittest.main()
