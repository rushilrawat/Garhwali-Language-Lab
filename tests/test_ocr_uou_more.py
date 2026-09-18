import hashlib
import unittest


class AdditionalUOUOCRTests(unittest.TestCase):
    def test_specs_choose_canonical_copy_and_targeted_ranges(self):
        import ocr_uou_more as module

        self.assertEqual(module.PAGE_RANGES, {
            'MAHL-204': (156, 185),
            'MAHL-611': (5, 130),
        })
        self.assertNotIn('MAHL-610', module.PAGE_RANGES)

    def test_exact_duplicate_pages_are_removed_before_record_creation(self):
        import ocr_uou_more as module

        duplicate = 'गढ़वाली पाठ'
        known = {hashlib.sha256(duplicate.encode()).hexdigest()}
        pages = [
            {'course': 'MAHL-204', 'page': 156, 'text': duplicate},
            {'course': 'MAHL-611', 'page': 5, 'text': 'नवीन पाठ'},
            {'course': 'MAHL-611', 'page': 6, 'text': 'नवीन पाठ'},
        ]
        kept, stats = module.unique_ocr_pages(pages, known)

        self.assertEqual([(row['course'], row['page']) for row in kept], [('MAHL-611', 5)])
        self.assertEqual(stats, {'known_duplicates': 1, 'within_batch_duplicates': 1})


if __name__ == '__main__':
    unittest.main()
