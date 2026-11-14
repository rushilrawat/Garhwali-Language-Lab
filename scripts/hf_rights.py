"""Rights and publication rules for Hugging Face package rows.

Decides which provenance items, text rows, and knowledge rows may appear in the
public profile, and records the source-specific policies behind each decision.
"""

from __future__ import annotations

import re
import unicodedata

OPEN_LICENSE_MARKERS = (
    'cc0', 'creativecommons.org/publicdomain', 'cc-by-', 'cc_by_',
    '/licenses/by/', '/licenses/by-sa/', 'apache-2.0',
)
BLOCKING_FLAGS = {
    'component_rights_review_required', 'source_lineage_missing', 'unlicensed',
    'publisher_license_not_stated', 'underlying_web_copyrights_not_cleared',
}
BLOCKING_RIGHTS_MARKERS = (
    'not_sublicensed', 'review_pending', 'review_required',
    'no_open_license', 'copyrights_not_cleared', 'license_link_missing',
    'license_not_stated', 'author_death_evidence_pending',
    'component_review', 'no_license',
)
# Owner sign-off on 2026-11-10 for Tier A of the rights triage
# (research/rights-clearance-triage-2026-11-09.md and the decision ledger
# research/rights-clearance-decisions-2026-11-09.json). Each entry matches one
# exact Internet Archive item, so a different scan or edition never inherits
# the clearance. These are English reference works: they reach the public
# catalog but not the Garhwali training views, which require iso_639_3 == gbm.
PUBLIC_DOMAIN_INDIA_US_SIGNED_OFF = 'public_domain_india_and_us_term_expired_owner_signoff_2026_11_10'
RIGHTS_DECISION_LEDGER = 'research/rights-clearance-decisions-2026-11-09.json'
_PD_LAW = (
    'https://copyright.gov.in/Copyright_Act_1957/chapter_v.html; '
    'https://web.law.duke.edu/cspd/publicdomainday/2026/'
)
SIGNED_OFF_PUBLIC_DOMAIN_SOURCES = {
    'ia_british_garhwal_1910': {
        'source_url': 'https://archive.org/details/in.ernet.dli.2015.48008',
        'author': 'H. G. Walton',
        'publication_year': 1910,
        'attribution': 'H. G. Walton, British Garhwal: A Gazetteer (District Gazetteers of the United Provinces, vol. XXXVI), Government Press, Allahabad, 1910. Internet Archive item in.ernet.dli.2015.48008.',
        'rights_evidence': 'India: Government work, Copyright Act 1957 s.28, term ended 1970. US: published 1910, before 1931. ' + _PD_LAW + '; https://wzcc.nvli.in/gazettes/british-garhwal-gazetteer-being-volume-xxxvi-district-gazetteers-united-provinces-agra-and; https://search.worldcat.org/oclc/160247247',
    },
    'ia_strachey_duthie_garhwal_flora_catalogue_1906': {
        'source_url': 'https://archive.org/details/catalogueplants00duthgoog',
        'author': 'Richard Strachey; revised by J. F. Duthie',
        'publication_year': 1906,
        'attribution': 'R. Strachey, revised by J. F. Duthie, Catalogue of the Plants of Kumaon and of the Adjacent Portions of Garhwal and Tibet, Lovell Reeve, London, 1906. Internet Archive item catalogueplants00duthgoog.',
        'rights_evidence': 'Last author J. F. Duthie died 23 Feb 1922: India life+50 term ended 1972, not revived in 1992. US: published 1906. ' + _PD_LAW + '; https://heenecemetery.org.uk/burial/john-duthie-buried-1922; https://catalog.hathitrust.org/Record/002000543.marc',
    },
    'ia_e_sherman_oakley_holy_himalaya_1905': {
        'source_url': 'https://archive.org/details/holyhimalayareli00oaklrich',
        'author': 'E. Sherman Oakley',
        'publication_year': 1905,
        'attribution': 'E. Sherman Oakley, Holy Himalaya, Oliphant Anderson & Ferrier, Edinburgh, 1905. Internet Archive item holyhimalayareli00oaklrich.',
        'rights_evidence': 'Author died 1934/35: India life+50 term ended by 1985. US: published 1905. ' + _PD_LAW + '; https://whowaswho-indology.info/?p=18788; https://ci.nii.ac.jp/ncid/BA03824796',
    },
    'ia_note_on_bhotias_almora_british_garhwal_1905': {
        'source_url': 'https://archive.org/details/dli.pahar.1694',
        'author': 'C. A. Sherring',
        'publication_year': 1906,
        'title': 'Notes on the Bhotias of Almora and British Garhwal',
        'attribution': 'C. A. Sherring, Notes on the Bhotias of Almora and British Garhwal, Memoirs of the Asiatic Society of Bengal vol. I no. 8, Calcutta, 1906. Internet Archive item dli.pahar.1694 (the uploader\'s CC BY-NC label covers the scan, not the 1906 text).',
        'rights_evidence': 'Author died 8 Oct 1940: India life+50 term ended 31 Dec 1990, before the 1992 extension. US: published 1906. ' + _PD_LAW + '; https://collections.westminster.org.uk/index.php/sherring-charles-atmore-1868-1940; https://ci.nii.ac.jp/ncid/BA03928441',
    },
}

TERRITORIAL_PUBLIC_DOMAIN_EVIDENCE = {
    'public_domain_us_uk_india_term_expired': {
        'license_id': 'Public-Domain-US-UK-India',
        'required_evidence': (
            'copyright.gov.in/documents/international%20copyright%20order.htm',
            'legislation.gov.uk/ukpga/1988/48/section/12',
            'nature.com/articles/112663b0',
            'nature.com/articles/055577a0',
            'gutenberg.org/ebooks/43681',
            'gutenberg.org/ebooks/43682',
        ),
    },
    'public_domain_india_government_work_term_expired': {
        'license_id': 'Public-Domain-India',
        'required_evidence': (
            'copyright.gov.in/copyright_act_1957/chapter_i.html',
            'copyright.gov.in/copyright_act_1957/chapter_iv.html',
            'copyright.gov.in/copyright_act_1957/chapter_v.html',
            'books.google.com/books/about/british_garhwal.html',
        ),
    },
    'public_domain_us_uk_india_term_expired_upreti_proverbs': {
        'license_id': 'Public-Domain-US-UK-India',
        'required_evidence': (
            'copyright.gov/what-is-copyright',
            'copyright.gov.in/copyright_act_1957/chapter_v.html',
            'legislation.gov.uk/ukpga/1988/48/section/12',
            'garudalife.in/proverbs-and-folklore-of-kumaun-and-garhwal',
            'ignca.gov.in/proverbs-and-folklore-of-kumaun-and-garhwal',
            'archive.org/details/cu31924089930774',
        ),
    },
    'public_domain_us_uk_india_term_expired_upreti_hill_dialects': {
        'license_id': 'Public-Domain-US-UK-India',
        'required_evidence': (
            'copyright.gov/what-is-copyright',
            'copyright.gov.in/copyright_act_1957/chapter_v.html',
            'legislation.gov.uk/ukpga/1988/48/section/12',
            'garudalife.in/proverbs-and-folklore-of-kumaun-and-garhwal',
            'ignca.gov.in/proverbs-and-folklore-of-kumaun-and-garhwal',
            'books.google.com/books?id=veutaaaayaaj',
        ),
    },
    'public_domain_us_uk_india_term_expired_grierson': {
        'license_id': 'Public-Domain-US-UK-India',
        'required_evidence': (
            'copyright.gov/what-is-copyright',
            'commons.wikimedia.org/wiki/file:linguistic_survey_of_india_vol_9_part_4.djvu',
            'nature.com/articles/147408a0',
            'legislation.gov.uk/ukpga/1988/48/section/12',
            'copyright.gov.in/copyright_act_1957/chapter_v.html',
            'glottolog.org/resource/reference/id/50321',
        ),
    },
    PUBLIC_DOMAIN_INDIA_US_SIGNED_OFF: {
        'license_id': 'Public-Domain-India-US',
        'required_evidence': (
            'copyright.gov.in/copyright_act_1957/chapter_v.html',
            'web.law.duke.edu/cspd/publicdomainday/2026',
        ),
    },
}

# These records have source-specific terms that are compatible with a public
# catalog, but not with the package's unrestricted model-training views.
# Keeping the mappings exact prevents a site-level license from clearing an
# unrelated source or a different version of the content.
NONCOMMERCIAL_CATALOG_SOURCES = {
    'hindialect_gbm': {
        'license_id': 'CC-BY-NC-SA-4.0',
        'license_url': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
        'source_url_contains': '11234/1-4839',
        'accepted_statuses': {
            'noncommercial_sharealike; upstream component review required',
            'dataset_deposit_declares_CC_BY_NC_SA_4',
        },
        'rights_status': 'upstream_dataset_declares_CC_BY_NC_SA_4',
        'rights_evidence': 'https://b2find.eudat.eu/dataset/bd804d5e-e53c-5ee3-b48c-cd2ecbad34de; https://huggingface.co/datasets/mteb/HinDialectClassification/blob/main/README.md',
        'attribution': 'Bafna, Niyati; Žabokrtský, Zdeněk; España-Bonet, Cristina; van Genabith, Josef; Kumar, Lalit Samyak Lalit; Suman, Sharda; Shivay, Rahul. HinDialect 1.1 (2022), LINDAT/CLARIAH-CZ and Kavita Kosh Project. CC BY-NC-SA 4.0.',
    },
    'panlex_gbm': {
        'license_id': 'CC-BY-NC-SA-4.0',
        'license_url': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
        'source_url_contains': 'huggingface.co/datasets/lbourdois/panlex',
        'accepted_statuses': {
            'official_current_page_CC_BY_NC_SA_4; mirror_card_says_CC0; conservative_license_applied',
            'panlex_database_explicitly_CC_BY_NC_SA_4',
        },
        'rights_status': 'PanLex_database_declares_CC_BY_NC_SA_4; commercial_use_requires_written_permission',
        'rights_evidence': 'https://panlex.org/license/; https://dev.panlex.org/source-registration/',
        'attribution': 'PanLex materials are part of the PanLex project of The Long Now Foundation, and are shared under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. PanLex and The Long Now Foundation disclaim any warranties associated with the provision of these materials. For more information about PanLex, please visit panlex.org. Hugging Face mirror: lbourdois/panlex.',
    },
}

OPEN_BIBLE_STORIES_SOURCE = {
    'license_id': 'CC-BY-SA-4.0',
    'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
    'source_url_contains': 'media.ipsapps.org/in/osa/stories/36-Garhwali-',
    'accepted_statuses': {
        'catalog_footer_CC_BY_NC_SA_4; item_page_has_no_license_block',
        'upstream_openbiblestories_declares_CC_BY_SA_4; v1_2026_06_26; text_only',
    },
    'rights_status': 'upstream_openbiblestories_declares_CC_BY_SA_4; v1_2026_06_26; text_only',
    'rights_evidence': 'https://openbiblestories.org/l/gbm/; https://git.door43.org/OBS-TLF/gbm_obs/releases/tag/v1',
    'attribution': 'Open Bible Stories — Garhwali (gbm), OBS-TLF v1 (2026-06-26), aggregated by the unfoldingWord OBS Library project; text-only extraction from the TLF umbrella OBS Android app. CC BY-SA 4.0. Audio and Sweet Publishing illustrations are excluded.',
}

META_OMNILINGUAL_TRAINING_DECISION = {
    'decision_id': 'meta_omnilingual_cc_by_4_0_training_2026_10_06',
    'source_id': 'meta_omni',
    'source_url': 'https://huggingface.co/datasets/facebook/omnilingual-asr-corpus',
    'rights_status': 'upstream_meta_cc_by_4_0',
    'license_id': 'CC-BY-4.0',
    'license_url': 'https://creativecommons.org/licenses/by/4.0/',
    'rights_evidence': 'sources/online/meta_omni/card.md.metadata.json',
    'rights_evidence_sha256': 'ec52ce7ee1bd2960f3c8d3b76d734683be979e4f8c0dc087e90d6e9ecaebf836',
    'checked_at': '2026-10-06',
    'evidence_urls': [
        'https://huggingface.co/datasets/facebook/omnilingual-asr-corpus/blob/main/README.md',
        'https://creativecommons.org/licenses/by/4.0/legalcode.en',
    ],
}

PIB_INSTRUMENT_POLICY = {
    'source_url': 'https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/sep/doc2025929651301.pdf',
    'license_url': 'https://www.pib.gov.in/ContentPage.aspx?lang=2&menuid=3604&reg=48',
    'rights_status': 'PIB_policy_permits_reproduction_of_PIB_material_with_attribution; third_party_material_excluded',
    'rights_evidence': 'https://www.pib.gov.in/ContentPage.aspx?lang=2&menuid=3604&reg=48',
    'attribution': 'Press Information Bureau, Government of India, “Sacred Stages”; reproduced under the PIB Copyright Policy with prominent source acknowledgement.',
    'record_ids': {f'pib_ramman_instruments:{index}' for index in range(1, 6)},
}

PANOS_REPRODUCTION_POLICY = {
    'source_url': 'https://mountainvoices.org/i_glossary.html',
    'license_url': 'https://mountainvoices.org/transcripts.html',
    'rights_status': (
        'Panos_archive_guidelines_permit_reproduction_by_press_education_research_'
        'institutions_and_nonprofits_with_attribution; model_training_scope_unspecified'
    ),
    'rights_evidence': (
        'https://mountainvoices.org/transcripts.html; '
        'https://mountainvoices.org/i_glossary.html'
    ),
    'license_id': 'LicenseRef-Panos-Source-Policy-Restricted',
    'license': (
        'Panos source-specific reproduction guideline; press, educational and '
        'research institutions, and nonprofit organisations; attribution required'
    ),
    'attribution': (
        'Mountain Voices glossary, Panos Oral Testimony Programme; cite the '
        'glossary source and acknowledge Panos.'
    ),
    'permitted_audiences': [
        'press', 'educational institutions', 'research institutions',
        'nonprofit organisations',
    ],
    'record_prefix': 'mountainvoices_local_glossary:',
    'record_count': 193,
}

# These isolated tokens are factual catalog entries, not definitions or copied
# prose. The thematic sources are narrowly allowlisted; the builder omits their
# record positions and list ordering. This basis never clears training views.
INDIVIDUAL_WORD_FACTS = {
    ('languageshome', 'languageshome:2'): 'Wu',
    ('languageshome', 'languageshome:4'): 'Yu',
    ('languageshome', 'languageshome:5'): 'Yu',
    ('languageshome', 'languageshome:7'): 'A',
    ('languageshome', 'languageshome:16'): 'Khanu',
    ('languageshome', 'languageshome:17'): 'Pinu',
    ('languageshome', 'languageshome:18'): 'Jitun',
    ('languageshome', 'languageshome:36'): 'Kya',
    ('languageshome', 'languageshome:38'): 'Nam',
    ('uttarakhandiwords_animals', 'uttarakhandiwords_animals:64:1'): 'उपण',
    ('emagazine_animals', 'emagazine_animals:81:1'): 'उपन',
    ('garhwalilanguage_dictionary', 'garhwalilanguage_dictionary:10:2'): 'बरफ',
}
INDIVIDUAL_WORD_FACT_SOURCE_IDS = {
    'emagazine_animals',
    'dhyani_occupations',
    'uttarakhandiwords_animals',
    'garhwalilanguage_dictionary',
}
INDIVIDUAL_WORD_FACT_EXCLUDED_FLAGS = {
    'uncorrected_ocr', 'language_mixed',
    'garhwali_language_candidate_not_confirmed',
}
INDIVIDUAL_WORD_FACT_EVIDENCE = {
    'basis_type': 'individual_lexical_token_only',
    'authority': (
        'Indian Copyright Office, Practice and Procedure Manual: Literary '
        'Works (draft), section 10: a single word cannot be protected as a '
        'literary work; Indian Copyright Office Handbook: factual information '
        'and short word combinations are not ordinarily protected'
    ),
    'evidence_url': 'https://copyright.gov.in/Documents/Manuals/LITERARY_MANUAL.pdf',
    'additional_evidence_url': 'https://copyright.gov.in/documents/handbook.html',
    'scope': (
        'Only this exact one-token value is exposed; no source definition, '
        'sentence, source record position, list ordering, or surrounding '
        'expression is included. This is not a source license and does not '
        'clear model training.'
    ),
}


def profile_includes_all_data(profile):
    return profile == 'all-data'


def asr_split_directory(profile):
    return 'asr_experimental' if profile_includes_all_data(profile) else 'asr'


def signed_off_public_domain_provenance(item):
    """Apply an owner-signed-off public-domain basis to one exact source item."""
    spec = SIGNED_OFF_PUBLIC_DOMAIN_SOURCES.get(item.get('source_id'))
    if (
        not spec
        or str(item.get('source_url') or '').rstrip('/') != spec['source_url']
        or set(item.get('quality_flags') or []) & BLOCKING_FLAGS
    ):
        return None
    enriched = dict(item)
    enriched.update({key: value for key, value in spec.items() if key != 'source_url'})
    enriched.update({
        'license': 'Public domain (India and US)',
        'license_id': 'Public-Domain-India-US',
        'license_url': 'https://creativecommons.org/publicdomain/mark/1.0/',
        'rights_status': PUBLIC_DOMAIN_INDIA_US_SIGNED_OFF,
        'rights_decision_ledger': RIGHTS_DECISION_LEDGER,
        'commercial_use_status': 'public_domain_in_india_and_us',
        'model_training_status': 'public_domain_in_india_and_us',
    })
    return enriched


def open_bible_stories_provenance(item):
    """Use the exact Garhwali OBS v1 license rather than its host-site footer."""
    record_id = str(item.get('record_id') or '')
    story_match = re.fullmatch(r'obs_garhwali:(\d{3})', record_id)
    status = str(item.get('rights_status') or '')
    if (
        item.get('source_id') != 'obs_garhwali'
        or not story_match
        or not 1 <= int(story_match.group(1)) <= 50
        or OPEN_BIBLE_STORIES_SOURCE['source_url_contains'] not in str(item.get('source_url') or '')
        or status not in OPEN_BIBLE_STORIES_SOURCE['accepted_statuses']
        or item.get('license_id') not in {'CC-BY-NC-SA-4.0', 'CC-BY-SA-4.0'}
        or not item.get('attribution')
        or set(item.get('quality_flags') or []) & BLOCKING_FLAGS
    ):
        return None
    enriched = dict(item)
    enriched.update({
        'license': 'CC BY-SA 4.0',
        'license_id': OPEN_BIBLE_STORIES_SOURCE['license_id'],
        'license_url': OPEN_BIBLE_STORIES_SOURCE['license_url'],
        'rights_status': OPEN_BIBLE_STORIES_SOURCE['rights_status'],
        'rights_evidence': OPEN_BIBLE_STORIES_SOURCE['rights_evidence'],
        'source_title': 'Open Bible Stories — Garhwali (gbm), OBS-TLF v1',
        'attribution': OPEN_BIBLE_STORIES_SOURCE['attribution'],
        'commercial_use_status': 'permitted_with_attribution_and_sharealike',
        'sharealike_required': True,
        'third_party_material_included': False,
    })
    return enriched


def is_publishable_provenance(item):
    item = (
        signed_off_public_domain_provenance(item)
        or open_bible_stories_provenance(item)
        or item
    )
    flags = set(item.get('quality_flags') or [])
    if flags & BLOCKING_FLAGS:
        return False
    rights = re.sub(
        r'[^a-z0-9]+', '_', str(item.get('rights_status') or '').casefold()
    ).strip('_')
    if any(marker in rights for marker in BLOCKING_RIGHTS_MARKERS):
        return False
    public_domain = TERRITORIAL_PUBLIC_DOMAIN_EVIDENCE.get(rights)
    if public_domain:
        evidence = str(item.get('rights_evidence') or '').casefold()
        return (
            item.get('license_id') == public_domain['license_id']
            and bool(item.get('license_url'))
            and bool(item.get('source_url'))
            and bool(item.get('attribution'))
            and all(url in evidence for url in public_domain['required_evidence'])
        )
    license_text = ' '.join(str(item.get(key) or '') for key in (
        'license', 'license_id', 'license_url',
    )).casefold()
    compact_license = re.sub(r'[^a-z0-9]+', '', license_text)
    if any(marker in compact_license for marker in (
        'ccbync', 'ccbynd', 'licensesbync', 'licensesbynd',
    )):
        return False
    if re.search(r'(?<![a-z0-9])mit(?![a-z0-9])', license_text):
        return True
    return any(marker in license_text for marker in OPEN_LICENSE_MARKERS)


def provenance_items(row):
    direct = row.get('provenance') or []
    nested = [
        item
        for parent in row.get('parents') or []
        for item in parent.get('provenance') or []
    ]
    return direct + nested


def publishable_provenance_items(row):
    return [item for item in provenance_items(row) if is_publishable_provenance(item)]


def noncommercial_catalog_provenance(item):
    """Return an explicitly licensed NC-SA basis only for known source rows."""
    source_id = item.get('source_id')
    spec = NONCOMMERCIAL_CATALOG_SOURCES.get(source_id)
    if not spec:
        return None
    status = str(item.get('rights_status') or '')
    flags = set(item.get('quality_flags') or [])
    source_url = str(item.get('source_url') or '')
    if (
        item.get('license_id') != spec['license_id']
        or item.get('license_url') != spec['license_url']
        or status not in spec['accepted_statuses']
        or spec['source_url_contains'] not in source_url
        or not item.get('attribution')
        or flags & BLOCKING_FLAGS
    ):
        return None
    enriched = dict(item)
    enriched.update({
        'rights_status': spec['rights_status'],
        'rights_evidence': spec['rights_evidence'],
        'attribution': spec['attribution'],
        'commercial_use_status': 'noncommercial_only',
        'model_training_status': 'not_cleared_for_commercial_training',
    })
    return enriched


def pib_policy_catalog_provenance(item):
    """Permit the five cited PIB instrument terms under PIB's reproduction policy."""
    old_record = (
        item.get('license_id') == 'LicenseRef-Government-Publication'
        and 'doc2025929651301.pdf' in str(item.get('license_url') or '')
        and item.get('rights_status') == 'not_recorded'
    )
    updated_record = (
        item.get('license_id') == 'LicenseRef-PIB-Copyright-Policy'
        and item.get('license_url') == PIB_INSTRUMENT_POLICY['license_url']
        and item.get('rights_status') == PIB_INSTRUMENT_POLICY['rights_status']
    )
    if (
        item.get('source_id') != 'pib_ramman_instruments'
        or item.get('record_id') not in PIB_INSTRUMENT_POLICY['record_ids']
        or not (old_record or updated_record)
        or 'Press Information Bureau' not in str(item.get('attribution') or '')
        or set(item.get('quality_flags') or []) & BLOCKING_FLAGS
    ):
        return None
    enriched = dict(item)
    enriched.update({
        'license_id': 'LicenseRef-PIB-Copyright-Policy',
        'license': 'PIB reproduction policy (source-specific permission; not a standard open license)',
        'license_url': PIB_INSTRUMENT_POLICY['license_url'],
        'source_url': PIB_INSTRUMENT_POLICY['source_url'],
        'rights_status': PIB_INSTRUMENT_POLICY['rights_status'],
        'rights_evidence': PIB_INSTRUMENT_POLICY['rights_evidence'],
        'attribution': PIB_INSTRUMENT_POLICY['attribution'],
        'commercial_use_status': 'not_explicitly_addressed_by_source_policy',
        'third_party_material_included': False,
    })
    return enriched


def panos_reproduction_policy_provenance(item):
    """Apply Panos's explicit reproduction guideline to its 193 glossary rows."""
    record_id = str(item.get('record_id') or '')
    match = re.fullmatch(r'mountainvoices_local_glossary:(\d+)', record_id)
    source_url = str(item.get('source_url') or '')
    license_url = str(item.get('license_url') or '')
    rights_status = item.get('rights_status')
    flags = set(item.get('quality_flags') or [])
    allowed_flags = {
        'regional_glossary', 'language_identity_requires_native_review',
        'publisher_license_not_stated',
    }
    if (
        item.get('source_id') != 'mountainvoices_local_glossary'
        or not match
        or not 1 <= int(match.group(1)) <= PANOS_REPRODUCTION_POLICY['record_count']
        or item.get('license_id') not in {
            'LicenseRef-Panos-Website-Terms-Unverified',
            PANOS_REPRODUCTION_POLICY['license_id'],
        }
        or license_url not in {
            PANOS_REPRODUCTION_POLICY['source_url'],
            PANOS_REPRODUCTION_POLICY['license_url'],
        }
        or rights_status not in {
            None, '', 'not_recorded',
            PANOS_REPRODUCTION_POLICY['rights_status'],
        }
        or source_url not in {'', PANOS_REPRODUCTION_POLICY['source_url']}
        or not str(item.get('attribution') or '').startswith('Panos')
        or not flags.issubset(allowed_flags)
    ):
        return None
    enriched = dict(item)
    enriched.update({
        'source_url': PANOS_REPRODUCTION_POLICY['source_url'],
        'license_id': PANOS_REPRODUCTION_POLICY['license_id'],
        'license': PANOS_REPRODUCTION_POLICY['license'],
        'license_url': PANOS_REPRODUCTION_POLICY['license_url'],
        'rights_status': PANOS_REPRODUCTION_POLICY['rights_status'],
        'rights_evidence': PANOS_REPRODUCTION_POLICY['rights_evidence'],
        'attribution': PANOS_REPRODUCTION_POLICY['attribution'],
        'permitted_audiences': PANOS_REPRODUCTION_POLICY['permitted_audiences'],
        'commercial_use_status': 'not_explicitly_addressed_by_source_policy',
        'model_training_status': 'separate_model_training_permission_not_established',
    })
    return enriched


def catalog_noncommercial_basis(row):
    return [
        item for item in (noncommercial_catalog_provenance(source)
                          for source in provenance_items(row))
        if item
    ]


def catalog_policy_basis(row):
    return [
        item for item in (
            pib_policy_catalog_provenance(source)
            or panos_reproduction_policy_provenance(source)
            for source in provenance_items(row)
        )
        if item
    ]


def individual_word_fact_basis(row, text):
    if not text or any(unicodedata.category(char)[0] not in {'L', 'M'} for char in text):
        return []
    explicit_matches = []
    thematic_matches = []
    for item in provenance_items(row):
        key = (str(item.get('source_id') or ''), str(item.get('record_id') or ''))
        flags = set(item.get('quality_flags') or [])
        if INDIVIDUAL_WORD_FACTS.get(key) == text:
            explicit_matches.append((item, key))
        source_word_match = (
            key[0] in INDIVIDUAL_WORD_FACT_SOURCE_IDS
            and item.get('genre') == 'thematic_lexicon'
            and bool(key[1])
            and not flags.intersection(INDIVIDUAL_WORD_FACT_EXCLUDED_FLAGS)
        )
        if source_word_match:
            thematic_matches.append((item, key))
    thematic_source_ids = {key[0] for _, key in thematic_matches}
    corroborated_matches = thematic_matches if len(thematic_source_ids) >= 2 else []
    evidence = []
    for item, key in explicit_matches + corroborated_matches:
        evidence.append({
            **INDIVIDUAL_WORD_FACT_EVIDENCE,
            'source_id': key[0],
            'source_url': item.get('source_url'),
            'attribution': item.get('attribution'),
            'source_license_id': item.get('license_id'),
            'source_rights_status': item.get('rights_status'),
            'model_training_status': 'not_cleared_by_source_license',
        })
    return evidence


def is_public_text_row(row):
    return bool(publishable_provenance_items(row))


def is_public_garhwali_text_row(row):
    items = publishable_provenance_items(row)
    return bool(items) and all(
        item.get('iso_639_3') == 'gbm' for item in items
    )


def is_public_knowledge_row(row):
    rights_basis = row.get('public_rights_basis') or []
    rights_status = re.sub(
        r'[^a-z0-9]+', '_', str(row.get('rights_status') or '').casefold()
    ).strip('_')
    return bool(rights_basis) and rights_status not in {
        'not_assessed', 'review_pending', 'rights_pending', 'unknown',
    } and all(
        is_publishable_provenance(item)
        and item.get('attribution')
        and (item.get('source_url') or item.get('source_snapshot_sha256'))
        for item in rights_basis
    )
