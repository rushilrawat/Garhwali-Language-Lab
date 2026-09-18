import unittest

import verify_ingestion as m


class VerifyIngestionTests(unittest.TestCase):
    def test_explicit_experimental_use_is_allowed(self):
        row = {'training_eligible': True, 'usage': 'all_data_experimental_user_approved'}
        self.assertTrue(m.training_use_is_authorized(row, 'experimental'))
        self.assertFalse(m.training_use_is_authorized(row, 'corpus'))

    def test_unlicensed_source_requires_rights_status_and_source_url(self):
        row = {'attribution': 'publisher', 'source_url': 'https://example.test',
               'rights_status': 'no_open_license_stated'}
        self.assertTrue(m.rights_are_documented(row))
        self.assertFalse(m.rights_are_documented({'attribution': 'publisher'}))

    def test_user_supplied_pdf_can_document_rights_with_local_source_path(self):
        row = {
            'attribution': 'Example Author',
            'source_pdf': 'incoming/pdfs/book.pdf',
            'rights_status': 'user_supplied_source_rights_unverified',
        }
        self.assertTrue(m.rights_are_documented(row))


if __name__ == '__main__': unittest.main()
