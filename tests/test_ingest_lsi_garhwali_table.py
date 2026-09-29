import csv
import importlib.util
import io
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/ingest_lsi_garhwali_table.py'
SPEC = importlib.util.spec_from_file_location('ingest_lsi_garhwali_table', SCRIPT)
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class LsiGarhwaliTableIngestionTests(unittest.TestCase):
    def tsv(self, rows):
        output = io.StringIO()
        writer = csv.writer(output, delimiter='\t')
        writer.writerow(('level', 'page_num', 'block_num', 'par_num', 'line_num',
                         'word_num', 'left', 'top', 'width', 'height', 'conf', 'text'))
        for row in rows:
            writer.writerow(row)
        return output.getvalue()

    def test_number_crop_provides_exact_row_centers(self):
        rows = [
            (5, 1, 1, 1, 1, 1, 5, 100, 25, 20, 91, '1.'),
            (5, 1, 1, 1, 2, 1, 5, 176, 25, 20, 88, '2.'),
        ]
        centers = module.row_centers_from_number_column(self.tsv(rows), 355, 1, 2)
        self.assertEqual(centers, [360, 436])

    def test_interpolates_one_missed_anchor_between_detected_rows(self):
        rows = [
            (5, 1, 1, 1, 1, 1, 5, 100, 25, 20, 91, '1.'),
            (5, 1, 1, 1, 3, 1, 5, 252, 25, 20, 88, '3.'),
        ]
        centers = module.row_centers_from_number_column(self.tsv(rows), 355, 1, 3)
        self.assertEqual(centers, [360, 436, 512])

    def test_item_number_anchors_prevent_a_missed_first_row_shift(self):
        rows = [
            (5, 1, 1, 1, 1, 1, 5, 176, 25, 20, 91, '2.'),
            (5, 1, 1, 1, 2, 1, 5, 328, 25, 20, 88, '4.'),
        ]
        centers = module.row_centers_from_number_column(self.tsv(rows), 355, 1, 4)
        self.assertEqual(centers, [360, 436, 512, 588])

    def test_rejects_number_crop_when_too_few_anchors_to_interpolate(self):
        rows = [(5, 1, 1, 1, 1, 1, 5, 100, 25, 20, 91, '1.')]
        with self.assertRaisesRegex(ValueError, 'too few'):
            module.row_centers_from_number_column(self.tsv(rows), 355, 1, 2)

    def test_removes_punctuation_only_table_artifact(self):
        rows = [
            (5, 1, 1, 1, 1, 1, 5, 100, 25, 20, 91, '1.'),
            (5, 1, 1, 1, 2, 1, 5, 138, 12, 12, 20, ':'),
            (5, 1, 1, 1, 3, 1, 5, 176, 25, 20, 88, '2.'),
        ]
        centers = module.row_centers_from_number_column(self.tsv(rows), 355, 1, 2)
        self.assertEqual(centers, [360, 436])

    def test_repairs_missed_row_when_punctuation_mark_masks_count_difference(self):
        rows = [
            (5, 1, 1, 1, 1, 1, 5, 100, 25, 20, 91, '1.'),
            (5, 1, 1, 1, 2, 1, 5, 214, 12, 12, 20, ':'),
            (5, 1, 1, 1, 3, 1, 5, 252, 25, 20, 88, '3.'),
        ]
        centers = module.row_centers_from_number_column(self.tsv(rows), 355, 1, 3)
        self.assertEqual(centers, [360, 436, 512])

    def test_column_crop_aligns_cells_and_ignores_dot_leaders(self):
        rows = [
            (5, 1, 1, 1, 1, 1, 20, 100, 24, 18, 92, 'Ek'),
            (5, 1, 1, 1, 1, 2, 80, 100, 12, 18, 50, '.'),
            (5, 1, 1, 1, 1, 3, 44, 100, 26, 18, 88, 'baghat'),
            (5, 1, 1, 1, 2, 1, 20, 176, 30, 18, 65, 'Dwi'),
        ]
        cells = module.cells_from_column_tsv(self.tsv(rows), [360, 436])
        self.assertEqual(cells[0]['text'], 'Ek baghat')
        self.assertEqual(cells[0]['confidence'], 90)
        self.assertEqual(cells[1]['text'], 'Dwi')

    def test_page_parser_preserves_garhwali_dialect_and_rights_metadata(self):
        anchor = self.tsv([
            (5, 1, 1, 1, 1, 1, 5, 100, 25, 20, 91, '1.'),
            (5, 1, 1, 1, 2, 1, 5, 176, 25, 20, 88, '2.'),
        ])
        columns = {
            name: self.tsv([
                (5, 1, 1, 1, 1, 1, 20, 100, 35, 18, 55 if name == 'rathi' else 90, form1),
                (5, 1, 1, 1, 2, 1, 20, 176, 35, 18, 90, form2),
            ])
            for name, form1, form2 in (
                ('standard', 'Ek', 'Dwi'),
                ('rathi', 'Ekha', 'Dwi'),
                ('tehri', 'Ek', 'Dui'),
                ('english', 'One', 'Two'),
            )
        }
        rows = module.parse_cropped_page(355, 1, 2, anchor, columns)
        self.assertEqual(len(rows), 6)
        first = rows[0]
        self.assertEqual(first['text_normalized'], 'Ek')
        self.assertEqual(first['dialect'], 'standard')
        self.assertEqual(first['english_gloss_ocr'], 'One')
        self.assertEqual(first['source_pdf_page'], 370)
        self.assertEqual(first['table_item'], 1)
        self.assertEqual(first['license_id'], 'PDM-1.0')
        low_confidence = next(row for row in rows if row['dialect'] == 'rathi')
        self.assertIn('low_ocr_confidence', low_confidence['quality_flags'])
        self.assertFalse(low_confidence['training_eligible'])
        self.assertTrue(low_confidence['experimental_training_eligible'])


if __name__ == '__main__':
    unittest.main()
