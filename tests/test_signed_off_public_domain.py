import unittest

import hf_rights
import hf_rows


def item(source_id, **overrides):
    spec = hf_rights.SIGNED_OFF_PUBLIC_DOMAIN_SOURCES[source_id]
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


TIER_A = (
    'ia_british_garhwal_1910',
    'ia_strachey_duthie_garhwal_flora_catalogue_1906',
    'ia_e_sherman_oakley_holy_himalaya_1905',
    'ia_note_on_bhotias_almora_british_garhwal_1905',
)
PAGE_EXCLUDED = (
    'ia_rai_pati_ram_bahadur_garhwal_ancient_modern_1916',
    'ia_himalayan_folklore_1935',
)


class SignedOffPublicDomainTests(unittest.TestCase):
    def test_each_tier_a_source_becomes_publishable_with_its_basis(self):
        self.assertEqual(len(hf_rights.SIGNED_OFF_PUBLIC_DOMAIN_SOURCES), 6)
        for source_id in TIER_A:
            with self.subTest(source_id=source_id):
                source = item(source_id)
                self.assertTrue(hf_rights.is_publishable_provenance(source))
                exported = hf_rows.catalog_provenance(source)
                self.assertEqual(exported['rights_status'], hf_rights.PUBLIC_DOMAIN_INDIA_US_SIGNED_OFF)
                self.assertEqual(exported['license_id'], 'Public-Domain-India-US')
                self.assertEqual(exported['rights_decision_ledger'], hf_rights.RIGHTS_DECISION_LEDGER)
                self.assertNotEqual(exported['attribution'], 'Archive attribution')

    def test_sherring_attribution_and_year_are_corrected(self):
        exported = hf_rows.catalog_provenance(item(
            'ia_note_on_bhotias_almora_british_garhwal_1905',
            rights_status='archive_license_recorded_cc_by_nc_4_0',
            author='Not identified in the Archive metadata reviewed',
        ))
        self.assertEqual(exported['author'], 'C. A. Sherring')
        self.assertEqual(exported['publication_year'], 1906)

    def test_other_scan_or_edition_is_not_cleared(self):
        source = item('ia_british_garhwal_1910', source_url='https://archive.org/details/some-other-scan')
        self.assertIsNone(hf_rights.signed_off_public_domain_provenance(source))
        self.assertFalse(hf_rights.is_publishable_provenance(source))

    def test_blocking_flag_still_blocks(self):
        source = item('ia_e_sherman_oakley_holy_himalaya_1905',
                      quality_flags=['component_rights_review_required'])
        self.assertFalse(hf_rights.is_publishable_provenance(source))

    def test_uncleared_tier_b_source_stays_unpublishable(self):
        source = {
            'source_id': 'ia_rahul_sankrityayan_himalaya_parichay_garhwal_1953',
            'source_url': 'https://archive.org/details/x',
            'rights_status': 'no_explicit_reuse_license_recorded',
            'attribution': 'x',
        }
        self.assertIsNone(hf_rights.signed_off_public_domain_provenance(source))
        self.assertFalse(hf_rights.is_publishable_provenance(source))

    def test_english_reference_rows_do_not_enter_garhwali_training_views(self):
        row = {'provenance': [item('ia_british_garhwal_1910')]}
        self.assertTrue(hf_rights.is_public_text_row(row))
        self.assertFalse(hf_rights.is_public_garhwali_text_row(row))


class PageExcludedSignOffTests(unittest.TestCase):
    def test_nothing_clears_until_the_page_list_is_verified(self):
        for source_id in PAGE_EXCLUDED:
            with self.subTest(source_id=source_id):
                spec = hf_rights.SIGNED_OFF_PUBLIC_DOMAIN_SOURCES[source_id]
                self.assertIsNone(spec['excluded_scan_pages'])
                self.assertIsNone(hf_rights.signed_off_public_domain_provenance(item(source_id)))
                self.assertFalse(hf_rights.is_publishable_provenance(item(source_id)))

    def test_listed_pages_stay_local_and_other_pages_clear(self):
        source_id = 'ia_himalayan_folklore_1935'
        spec = hf_rights.SIGNED_OFF_PUBLIC_DOMAIN_SOURCES[source_id]
        original = spec['excluded_scan_pages']
        spec['excluded_scan_pages'] = frozenset({3, 4})
        try:
            self.assertIsNone(hf_rights.signed_off_public_domain_provenance(
                item(source_id, record_id=f'{source_id}:scan-page:0004')))
            cleared = hf_rights.signed_off_public_domain_provenance(
                item(source_id, record_id=f'{source_id}:scan-page:0020'))
            self.assertEqual(cleared['rights_status'], hf_rights.PUBLIC_DOMAIN_INDIA_US_SIGNED_OFF)
            self.assertNotIn('excluded_scan_pages', cleared)
            self.assertNotIn('excluded_layer', cleared)
            self.assertIsNone(hf_rights.signed_off_public_domain_provenance(
                item(source_id, record_id=f'{source_id}:whole-book')))
        finally:
            spec['excluded_scan_pages'] = original

    def test_joshi_stays_unpublishable(self):
        source = {
            'source_id': 'ia_dharmanand_joshi_notes_garhwal_district_1910',
            'source_url': 'https://archive.org/details/dli.ministry.29693',
            'rights_status': 'no_explicit_reuse_license_recorded',
            'attribution': 'x',
        }
        self.assertIsNone(hf_rights.signed_off_public_domain_provenance(source))
        self.assertFalse(hf_rights.is_publishable_provenance(source))


if __name__ == '__main__':
    unittest.main()
