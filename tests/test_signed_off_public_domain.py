import unittest

import build_huggingface_dataset as m


def item(source_id, **overrides):
    spec = m.SIGNED_OFF_PUBLIC_DOMAIN_SOURCES[source_id]
    base = {
        'source_id': source_id,
        'source_url': spec['source_url'],
        'record_id': f'{source_id}:scan-page:0001',
        'rights_status': 'no_explicit_reuse_license_recorded',
        'attribution': 'Archive attribution',
        'quality_flags': ['uncorrected_ocr', 'not_native_reviewed'],
    }
    base.update(overrides)
    return base


class SignedOffPublicDomainTests(unittest.TestCase):
    def test_each_tier_a_source_becomes_publishable_with_its_basis(self):
        self.assertEqual(len(m.SIGNED_OFF_PUBLIC_DOMAIN_SOURCES), 4)
        for source_id in m.SIGNED_OFF_PUBLIC_DOMAIN_SOURCES:
            with self.subTest(source_id=source_id):
                source = item(source_id)
                self.assertTrue(m.is_publishable_provenance(source))
                exported = m.catalog_provenance(source)
                self.assertEqual(exported['rights_status'], m.PUBLIC_DOMAIN_INDIA_US_SIGNED_OFF)
                self.assertEqual(exported['license_id'], 'Public-Domain-India-US')
                self.assertEqual(exported['rights_decision_ledger'], m.RIGHTS_DECISION_LEDGER)
                self.assertNotEqual(exported['attribution'], 'Archive attribution')

    def test_sherring_attribution_and_year_are_corrected(self):
        exported = m.catalog_provenance(item(
            'ia_note_on_bhotias_almora_british_garhwal_1905',
            rights_status='archive_license_recorded_cc_by_nc_4_0',
            author='Not identified in the Archive metadata reviewed',
        ))
        self.assertEqual(exported['author'], 'C. A. Sherring')
        self.assertEqual(exported['publication_year'], 1906)

    def test_other_scan_or_edition_is_not_cleared(self):
        source = item('ia_british_garhwal_1910', source_url='https://archive.org/details/some-other-scan')
        self.assertIsNone(m.signed_off_public_domain_provenance(source))
        self.assertFalse(m.is_publishable_provenance(source))

    def test_blocking_flag_still_blocks(self):
        source = item('ia_e_sherman_oakley_holy_himalaya_1905',
                      quality_flags=['component_rights_review_required'])
        self.assertFalse(m.is_publishable_provenance(source))

    def test_uncleared_tier_b_source_stays_unpublishable(self):
        source = {
            'source_id': 'ia_rahul_sankrityayan_himalaya_parichay_garhwal_1953',
            'source_url': 'https://archive.org/details/x',
            'rights_status': 'no_explicit_reuse_license_recorded',
            'attribution': 'x',
        }
        self.assertIsNone(m.signed_off_public_domain_provenance(source))
        self.assertFalse(m.is_publishable_provenance(source))

    def test_english_reference_rows_do_not_enter_garhwali_training_views(self):
        row = {'provenance': [item('ia_british_garhwal_1910')]}
        self.assertTrue(m.is_public_text_row(row))
        self.assertFalse(m.is_public_garhwali_text_row(row))


if __name__ == '__main__':
    unittest.main()
