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


if __name__ == '__main__': unittest.main()
