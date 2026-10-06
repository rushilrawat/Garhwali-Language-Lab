#!/usr/bin/env python3
"""Build deterministic Hugging Face upload folders from prepared Garhwali views."""

from __future__ import annotations

import argparse
import copy
import errno
import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

from record_schema import normalize_record
from hf_source_registry import SOURCE_URLS, source_record_locator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab'
ALL_DATA_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab-all-data'
SOURCE_ATTRIBUTION_OVERLAY_PATH = ROOT / 'research/source-attribution-overlays-2026-10-05.json'
UPSTREAM_SPLIT_OVERLAP_PATH = ROOT / 'research/huggingface-upstream-split-overlap-2026-10-05.json'
PAHARILI_GBM_ROWS_PATH = ROOT / 'experimental/paharili_gbm.jsonl'
PAHARILI_LICENSE_PATH = ROOT / 'sources/online/paharili/c71d239df91726fc-LICENSE'
# Preserve these earlier local output paths in the overwrite guard. Their names
# are historical storage paths, not semantic project release versions.
LEGACY_PUBLIC_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab-v2.0.0-staging'
LEGACY_ALL_DATA_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab-all-data-v2.0.0-local'
RELEASE_VERSION = os.environ.get('GARHWALI_RELEASE_VERSION', '0.2.8').removeprefix('v')
RELEASE_PUBLIC_OUTPUT = ROOT / f'data/huggingface/garhwali-language-lab-v{RELEASE_VERSION}-staging'
RELEASE_ALL_DATA_OUTPUT = ROOT / f'data/huggingface/garhwali-language-lab-all-data-v{RELEASE_VERSION}-local'
MANAGED_OUTPUTS = {
    DEFAULT_OUTPUT.resolve(), ALL_DATA_OUTPUT.resolve(),
    LEGACY_PUBLIC_OUTPUT.resolve(), LEGACY_ALL_DATA_OUTPUT.resolve(),
    RELEASE_PUBLIC_OUTPUT.resolve(), RELEASE_ALL_DATA_OUTPUT.resolve(),
}
RELEASE_ID = f"garhwali-language-lab-v{RELEASE_VERSION}"
KNOWLEDGE_CONFIGS = {
    'geography': ROOT / 'data/extracted/geography/records.jsonl',
    'historical_terms': ROOT / 'data/extracted/historical_terms/records.jsonl',
    'literary_people': ROOT / 'data/extracted/literary_people/records.jsonl',
    'literary_works': ROOT / 'data/extracted/literary_works/records.jsonl',
    'popular_songs': ROOT / 'data/extracted/popular_songs/records.jsonl',
    'university_research': ROOT / 'data/extracted/university_research/records.jsonl',
}
KNOWLEDGE_SOURCE_CATALOGS = {
    'geography': ROOT / 'research/garhwali-geography-catalog.json',
    'historical_terms': ROOT / 'research/garhwali-historical-terms.json',
    'literary_people': ROOT / 'research/garhwali-literary-people-catalog.json',
    'literary_works': ROOT / 'research/garhwali-literary-works-catalog.json',
}
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


def prepare_package_output(output):
    output = Path(output)
    resolved = output.resolve()
    if output.exists() and resolved not in MANAGED_OUTPUTS:
        raise ValueError(
            'refusing to replace an existing custom output directory; use a new '
            'path or one of the managed Hugging Face package paths'
        )
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError(f'package output must be a regular directory: {output}')
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    return output


def asr_split_directory(profile):
    return 'asr_experimental' if profile_includes_all_data(profile) else 'asr'


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


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
    item = open_bible_stories_provenance(item) or item
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


def content_audio_path(audio_sha256):
    return f'audio/{audio_sha256[:2]}/{audio_sha256}.wav'


def public_speaker_id(row):
    speaker = row.get('speaker_id')
    if speaker in (None, '', 'NA'):
        return None
    value = f"{row.get('source', '')}|{speaker}".encode()
    return f'speaker_{hashlib.sha256(value).hexdigest()[:16]}'


def audio_row(row, transcript_field, include_audio_reference=True,
              serialize_evidence=False):
    keep = (
        'audio_sha256', 'duration_seconds', 'language', 'district', 'state',
        'gender', 'languages_known', 'source', 'license',
        'main_split', 'transcription_split', 'quality_flags',
        'training_quality_flags', 'review_status',
        'machine_transcript_model', 'machine_transcript_model_revision',
        'machine_transcript_quality',
        'recovery_status', 'recovery_confidence',
        'experimental_training_eligible', 'training_eligible',
        'language_scope_status', 'source_conflict_evidence',
        'active_for_source_error_analysis',
        'recovery_adjudication',
        'recovery_third_checkpoint',
        'audio_grounded_review',
    )
    exported = {key: row.get(key) for key in keep if key in row}
    if serialize_evidence:
        # Draft evidence is sparse and nested. JSON strings keep one stable
        # Arrow schema across shards while preserving every nested value.
        json_fields = (
            'machine_transcript_quality', 'recovery_confidence',
            'source_conflict_evidence', 'recovery_adjudication',
            'recovery_third_checkpoint', 'audio_grounded_review',
        )
        for key in json_fields:
            value = row.get(key)
            exported[key] = (
                json.dumps(value, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':'))
                if value is not None else ''
            )
        for key in ('quality_flags', 'training_quality_flags'):
            exported[key] = json.dumps(
                row.get(key) or [], ensure_ascii=False, separators=(',', ':')
            )
        exported['active_for_source_error_analysis'] = bool(
            row.get('active_for_source_error_analysis', False)
        )
        exported['language_scope_status'] = row.get('language_scope_status') or ''
    if include_audio_reference:
        exported['audio'] = content_audio_path(row['audio_sha256'])
    # Stable string typing prevents Dataset Viewer/Parquet inference from
    # treating early null-only rows as a Null feature before later IDs appear.
    exported['speaker_id'] = public_speaker_id(row) or ''
    exported['transcript'] = row.get(transcript_field, '')
    exported['source_audio_records'] = max(
        1, len(row.get('duplicate_source_audio_paths') or [])
    )
    return exported


def attach_recovery_adjudication(rows, adjudication_rows):
    by_hash = {row['audio_sha256']: row for row in adjudication_rows}
    if len(by_hash) != len(adjudication_rows):
        raise ValueError('Recovery adjudication audio hashes are not unique')
    safe_fields = (
        'candidates', 'pairwise_character_agreement',
        'whisper_v0.1_token_confidence_uncalibrated',
        'proposed_machine_transcript', 'proposed_machine_transcript_model',
        'proposed_machine_transcript_flags', 'proposal_basis',
        'evidence_status', 'review_priority', 'human_review_status',
        'automatic_correction', 'human_reference_available',
        'supervised_training_eligible',
        'recommended_for_machine_label_training',
        'original_transcript_preserved',
    )
    result = []
    for row in rows:
        enriched = dict(row)
        evidence = by_hash.get(row['audio_sha256'])
        if evidence:
            enriched['recovery_adjudication'] = {
                field: evidence[field] for field in safe_fields if field in evidence
            }
        result.append(enriched)
    return result


def attach_recovery_third_checkpoint(rows, checkpoint_rows):
    by_hash = {row['audio_sha256']: row for row in checkpoint_rows}
    if len(by_hash) != len(checkpoint_rows):
        raise ValueError('Third-checkpoint recovery audio hashes are not unique')
    result = []
    for row in rows:
        enriched = dict(row)
        evidence = by_hash.get(row['audio_sha256'])
        if evidence:
            enriched['recovery_third_checkpoint'] = {
                'transcript': evidence.get('machine_transcript', ''),
                'model': 'whisper-tiny-garhwali-v0.1',
                'mean_token_log_probability': evidence.get('mean_token_log_probability'),
                'token_confidence_uncalibrated': evidence.get('token_confidence_uncalibrated'),
                'confidence_is_calibrated': False,
                'human_reference_available': False,
            }
        result.append(enriched)
    return result


def attach_audio_grounded_review(rows, review_rows):
    by_hash = {row['audio_sha256']: row for row in review_rows}
    if len(by_hash) != len(review_rows):
        raise ValueError('Audio-grounded review hashes are not unique')
    safe_fields = (
        'audio_grounded_evidence', 'audio_review_category',
        'audio_review_priority', 'machine_audio_review_complete',
        'human_listening_review_required', 'automatic_correction',
        'human_reference_available', 'supervised_training_eligible',
        'recommended_for_machine_label_training',
        'original_transcript_preserved',
    )
    result = []
    for row in rows:
        enriched = dict(row)
        evidence = by_hash.get(row['audio_sha256'])
        if evidence:
            enriched['audio_grounded_review'] = {
                field: evidence[field] for field in safe_fields if field in evidence
            }
        result.append(enriched)
    return result


def draft_identity(row):
    return row['audio_sha256'], row.get('audio_path') or row.get('local_audio_path')


def drafts_cover_queue(queue, drafts):
    return Counter(map(draft_identity, queue)) == Counter(map(draft_identity, drafts))


def deduplicate_audio_rows(rows, transcript_field):
    groups = {}
    for row in rows:
        digest = row['audio_sha256']
        if digest not in groups:
            groups[digest] = dict(row)
            groups[digest]['duplicate_source_audio_paths'] = []
        current = groups[digest]
        if current.get(transcript_field, '') != row.get(transcript_field, ''):
            raise ValueError(f'conflicting transcripts for audio_sha256={digest}')
        source_path = row.get('audio_path') or row.get('local_audio_path')
        if source_path not in current['duplicate_source_audio_paths']:
            current['duplicate_source_audio_paths'].append(source_path)
    yield from groups.values()


def source_languages(row):
    """Return source-declared ISO codes without guessing from shared scripts."""
    return sorted({
        item.get('iso_639_3')
        for item in provenance_items(row)
        if item.get('iso_639_3')
    })


def normalized_text_key(text):
    """Match the release audit's conservative Unicode/alphanumeric text key."""
    normalized = unicodedata.normalize('NFKC', str(text or '')).casefold()
    return ''.join(character for character in normalized if character.isalnum())


def source_record_ids(row):
    """Return record-level source IDs from corpus or benchmark provenance."""
    values = []
    for field in ('provenance', 'sources'):
        source_rows = row.get(field) or []
        if isinstance(source_rows, dict):
            source_rows = source_rows.get('provenance') or []
        if isinstance(source_rows, list):
            values.extend(source_rows)
    return {
        item.get('record_id') for item in values
        if isinstance(item, dict) and item.get('record_id')
    }


def build_paharili_gbm_rows(source_rows, existing_text_rows):
    """Build a traceable Garhwali-only PahariLI view without duplicate text rows."""
    source_rows = list(source_rows)
    groups = {}
    garhwali_rows = []
    seen_record_ids = set()
    for row in source_rows:
        if row.get('iso_639_3') != 'gbm' or row.get('upstream_label') != 'gbm':
            continue
        record_id = str(row.get('record_id') or '')
        if record_id in seen_record_ids:
            raise ValueError(f'Duplicate PahariLI record ID: {record_id}')
        seen_record_ids.add(record_id)
        if not record_id.startswith('paharili_gbm:'):
            raise ValueError(f'Invalid PahariLI record ID: {record_id!r}')
        text = str(row.get('text_original') or row.get('text_normalized') or '')
        key = normalized_text_key(text)
        if not key:
            raise ValueError(f'Empty Garhwali PahariLI record: {record_id}')
        origin = row.get('provenance') or {}
        if not origin.get('url') or not re.fullmatch(
            r'[0-9a-f]{64}', str(origin.get('sha256') or '')
        ):
            raise ValueError(f'Missing raw-file provenance for {record_id}')
        if row.get('split') not in {'train', 'test'}:
            raise ValueError(
                f'Unexpected upstream PahariLI split for {record_id}: {row.get("split")!r}'
            )
        groups.setdefault(key, {})[record_id] = row
        garhwali_rows.append(row)

    existing_by_key = {}
    for row in existing_text_rows:
        for field in (
            'text', 'release_text', 'text_normalized', 'text_original',
            'transcript', 'asr_target_clean', 'machine_transcript', 'form',
        ):
            value = row.get(field)
            key = normalized_text_key(value) if isinstance(value, str) else ''
            if key:
                existing_by_key.setdefault(key, []).append(row)

    output = []
    already_present = 0
    already_present_source_ids = 0
    source_overlap_groups = 0
    split_records = Counter()
    for key, group in sorted(groups.items()):
        group_rows = list(group.values())
        record_ids = sorted(group)
        source_splits = sorted({str(row['split']) for row in group_rows})
        if key in existing_by_key:
            represented_ids = set().union(*(
                source_record_ids(existing)
                for existing in existing_by_key[key]
            ))
            missing_ids = set(record_ids) - represented_ids
            if missing_ids:
                raise ValueError(
                    'PahariLI text already exists in another release config but '
                    f'its source IDs are not preserved: {sorted(missing_ids)[:5]}'
                )
            already_present += 1
            already_present_source_ids += len(record_ids)
            continue

        split = 'source_overlap' if len(source_splits) > 1 else source_splits[0]
        source_overlap_groups += split == 'source_overlap'
        split_records[split] += 1
        source_texts = sorted({
            str(row.get('text_original') or row.get('text_normalized') or '')
            for row in group_rows
        })
        provenance = []
        for record_id in record_ids:
            row = group[record_id]
            origin = row['provenance']
            split_name = str(row['split'])
            try:
                source_record_index = int(record_id.rsplit(':', 1)[1])
            except (IndexError, ValueError) as exc:
                raise ValueError(f'Invalid PahariLI source index: {record_id}') from exc
            provenance.append({
                'source_id': 'paharili_gbm',
                'source_ref_id': 'PahariLI',
                'record_id': record_id,
                'source_url': str(row.get('source_url') or ''),
                'source_file_url': str(origin['url']),
                'source_file_sha256': str(origin['sha256']),
                'source_split': split_name,
                'source_record_index': source_record_index,
                'source_line_number': source_record_index + 1,
                'iso_639_3': 'gbm',
                'upstream_label': 'gbm',
                'license_id': str(row.get('license_id') or ''),
                'license_url': str(row.get('license_url') or ''),
                'rights_status': str(row.get('rights_status') or ''),
                'attribution': str(row.get('attribution') or ''),
            })

        first = group_rows[0]
        license_id = str(first.get('license_id') or '')
        rights_status = str(first.get('rights_status') or 'not_assessed')
        flags = sorted({
            str(flag)
            for row in group_rows
            for flag in row.get('quality_flags') or []
            if flag
        })
        text = source_texts[0]
        digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
        output.append({
            'id': f'paharili-gbm-{digest}',
            'text': text,
            'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'normalized_text_key_sha256': digest,
            'source_text_variants': source_texts,
            'source_record_ids': record_ids,
            'upstream_splits': source_splits,
            'split': split,
            'split_assignment': (
                'upstream_paharili_train_test; '
                'cross-split text grouped in source_overlap'
            ),
            'language': 'gbm',
            'iso_639_3': 'gbm',
            'language_name': 'Garhwali',
            'language_label_source': (
                'PahariLI upstream label; not independently reviewed'
            ),
            'script': str(first.get('script') or 'Deva'),
            'genre': 'mixed_web_and_scripture',
            'upstream_task': 'text language identification',
            'provenance': provenance,
            'attribution': 'Rachana Gusain, PahariLI repository',
            'license_id': license_id,
            'license_url': str(first.get('license_url') or ''),
            'rights_status': rights_status,
            'reuse_scope': (
                'The PahariLI repository declares Apache-2.0; sentence-level '
                'origins and redistribution rights are not independently established.'
            ),
            'license_labels': [license_id] if license_id else [],
            'quality_status': 'unreviewed; no native-language review',
            'quality_flags': flags,
            'record_quality_flags': flags,
            'native_reviewed': False,
            'training_eligible': False,
            'experimental_training_eligible': split == 'train',
            'recommended_for_general_language_model_training': False,
        })

    metrics = {
        'input_records': len(source_rows),
        'garhwali_source_records': len(garhwali_rows),
        'excluded_non_garhwali_records': len(source_rows) - len(garhwali_rows),
        'normalized_unique_source_texts': len(groups),
        'collapsed_duplicate_source_records': len(garhwali_rows) - len(groups),
        'already_present_in_existing_configs': already_present,
        'source_record_ids_already_in_existing_configs': already_present_source_ids,
        'new_records': len(output),
        'new_source_record_ids': sum(len(row['source_record_ids']) for row in output),
        'all_source_record_ids_preserved': (
            already_present_source_ids
            + sum(len(row['source_record_ids']) for row in output)
            == len(garhwali_rows)
        ),
        'source_split_overlap_groups': source_overlap_groups,
        'split_records': dict(sorted(split_records.items())),
    }
    return output, metrics


@lru_cache(maxsize=1)
def upstream_split_overlap_ids():
    """Return audited source IDs whose upstream component split is held out."""
    if not UPSTREAM_SPLIT_OVERLAP_PATH.is_file():
        raise FileNotFoundError(
            f'Missing upstream split audit: {UPSTREAM_SPLIT_OVERLAP_PATH}'
        )
    payload = json.loads(
        UPSTREAM_SPLIT_OVERLAP_PATH.read_text(encoding='utf-8')
    )
    if payload.get('schema_version') != 'garhwali-upstream-split-overlap-v1':
        raise ValueError('Unsupported upstream split overlap audit schema')
    direct_ids = payload.get('meta_upstream_eval_record_ids')
    aggregate_rows = payload.get('community_rows_with_eval_split_text_matches')
    if not isinstance(direct_ids, list) or not isinstance(aggregate_rows, list):
        raise ValueError('Upstream split overlap audit has incomplete ID lists')
    aggregate_ids = {
        str(row['record_id'])
        for row in aggregate_rows
        if isinstance(row, dict) and row.get('record_id')
    }
    return set(map(str, direct_ids)), aggregate_ids


def route_upstream_split_overlap(row, direct_eval_ids, aggregate_eval_ids):
    """Keep a row public but move a train row with upstream eval lineage aside."""
    result = dict(row)
    record_ids = source_record_ids(result)
    direct_matches = sorted(record_ids & direct_eval_ids)
    aggregate_matches = sorted(record_ids & aggregate_eval_ids)
    vaani_test_matches = sorted({
        str(item.get('record_id'))
        for item in provenance_items(result)
        if isinstance(item, dict)
        and (
            item.get('source_id') in {
                'vaani-official-test-remainder',
                'vaani-transcription-part',
            }
            or item.get('canonical_transcript_source')
            == 'ARTPARK-IISc/Vaani-transcription-part'
        )
        and item.get('transcription_split') == 'test'
        and item.get('record_id')
    })
    if direct_matches and aggregate_matches:
        status = 'upstream_record_and_transcript_match'
    elif direct_matches:
        status = 'upstream_eval_record_id_match'
    elif aggregate_matches:
        status = 'upstream_eval_transcript_match'
    elif vaani_test_matches:
        status = 'upstream_vaani_test_source_record_match'
    else:
        status = 'no_upstream_eval_match_detected'
    result['source_split_overlap_status'] = status
    result['source_split_overlap_source_ids'] = sorted(
        set(direct_matches + aggregate_matches + vaani_test_matches)
    )
    if result.get('split') == 'train' and status != 'no_upstream_eval_match_detected':
        result['original_split'] = result.get('original_split') or 'train'
        result['split'] = 'source_overlap'
        assignment = str(result.get('split_assignment') or '').strip()
        reason = (
            'upstream dev/test source overlap; text retained and routed to '
            'source_overlap instead of default train'
        )
        result['split_assignment'] = f'{assignment}; {reason}'.strip('; ')
        result['recommended_for_training'] = False
    return result


@lru_cache(maxsize=1)
def source_attribution_overlays():
    """Load audited, content-free creator and revision metadata once per build."""
    if not SOURCE_ATTRIBUTION_OVERLAY_PATH.is_file():
        return {}
    payload = json.loads(SOURCE_ATTRIBUTION_OVERLAY_PATH.read_text(encoding='utf-8'))
    if payload.get('schema_version') != 'garhwali-source-attribution-overlay-v1':
        raise ValueError('Unsupported source attribution overlay schema')
    records = payload.get('records')
    if not isinstance(records, dict):
        raise ValueError('Source attribution overlay has no record map')
    return records


def enrich_source_attribution(item, overlays=None):
    """Overlay audited attribution metadata without replacing source content."""
    item = dict(item)
    record_id = item.get('record_id')
    overlay = (source_attribution_overlays() if overlays is None else overlays).get(record_id)
    if not overlay:
        return item
    if overlay.get('source_id') != item.get('source_id'):
        raise ValueError(f'Source ID mismatch in attribution overlay for {record_id}')
    return {**item, **overlay}


def comparable_text_rows(rows, field):
    """Expose selected text-bearing fields to the shared exact-text deduper."""
    for row in rows:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            yield {**row, 'text': value}


def build_catalog_text_expansion(catalog_rows, existing_text_rows, benchmark_eval_rows=()):
    """Promote strict, rights-cleared catalog text that is net-new to text views.

    This is a separate train-only expansion view. It excludes exact normalized
    text already in existing text-bearing views, source record IDs used by
    validation/test or frozen benchmark validation/test, and internal duplicates.
    Source-page-family isolation is not claimed.
    """
    existing_text_rows = list(existing_text_rows)
    existing_ids = {row.get('id') for row in existing_text_rows}
    existing_text_keys = {
        normalized_text_key(row.get('text')) for row in existing_text_rows
        if normalized_text_key(row.get('text'))
    }
    evaluation_rows = [
        row for row in existing_text_rows
        if row.get('split') in {'validation', 'test'}
    ] + list(benchmark_eval_rows)
    evaluation_record_ids = set().union(
        *(source_record_ids(row) for row in evaluation_rows)
    ) if evaluation_rows else set()

    candidates = []
    counters = Counter()
    for row in catalog_rows:
        if not row.get('text'):
            continue
        if row.get('redistribution_status') != 'rights_cleared':
            continue
        if row.get('language_bucket') != 'garhwali_candidate':
            continue
        if (row.get('quality_v2') or {}).get('tier') != 'strict_gold_candidate':
            continue
        rights_basis = row.get('public_rights_basis') or []
        if not rights_basis or not all(
            is_publishable_provenance(item) for item in rights_basis
        ):
            continue
        sources = row.get('sources') or []
        languages = {
            item.get('iso_639_3') for item in sources
            if isinstance(item, dict) and item.get('iso_639_3')
        }
        if languages != {'gbm'}:
            continue
        counters['strict_rights_language_candidates'] += 1
        if row.get('id') in existing_ids:
            counters['excluded_exact_existing_identity'] += 1
            continue
        if source_record_ids({'sources': sources}) & evaluation_record_ids:
            counters['excluded_evaluation_source_record'] += 1
            continue
        text_key = normalized_text_key(row.get('text'))
        if not text_key or text_key in existing_text_keys:
            counters['excluded_normalized_existing_text'] += 1
            continue
        candidates.append((text_key, row))

    selected = {}
    for text_key, row in sorted(candidates, key=lambda item: item[1].get('id') or ''):
        if text_key in selected:
            counters['excluded_normalized_internal_duplicate'] += 1
            continue
        selected[text_key] = row

    output = []
    for row in selected.values():
        enriched = dict(row)
        sources = row.get('sources') or []
        quality_flags = list(row.get('record_quality_flags') or [])
        enriched.update({
            'language': 'gbm',
            'source_languages': ['gbm'],
            'language_buckets': ['garhwali_candidate'],
            'quality_tiers': ['strict_gold_candidate'],
            'recommended_for_training': False,
            'script': (row.get('language_quality') or {}).get('script_profile', {}).get('script', 'Other'),
            'split': 'train',
            'duplicate_component_id': None,
            'original_split': 'catalog/train',
            'split_assignment': 'strict rights-cleared catalog addition; normalized-text and project evaluation-source overlaps excluded; known upstream dev/test overlaps route to source_overlap; source-page-family isolation not assessed',
            'quality_flags': quality_flags,
            'provenance': list(row.get('public_rights_basis') or []),
        })
        enriched['recommended_for_training'] = recommended_text_training_row(enriched)
        output.append(enriched)
    counters['records'] = len(output)
    counters['recommended_for_training'] = sum(
        row['recommended_for_training'] for row in output
    )
    return output, dict(counters)


def build_catalog_text_resources(catalog_rows, existing_text_rows, benchmark_eval_rows=()):
    """Expose additional rights-cleared catalog text as a non-evaluation resource.

    This intentionally has higher recall than text_expansion: records do not
    need to meet the strict training tier, but must be Garhwali-only, have a
    recorded redistribution basis, be new after normalized cross-config
    deduplication, and have no source-record match to held-out evaluation data.
    Every row remains explicitly ineligible for benchmark/evaluation use.
    """
    existing_text_rows = list(existing_text_rows)
    existing_ids = {row.get('id') for row in existing_text_rows}
    existing_text_keys = {
        normalized_text_key(row.get('text')) for row in existing_text_rows
        if normalized_text_key(row.get('text'))
    }
    evaluation_rows = [
        row for row in existing_text_rows
        if row.get('split') in {'validation', 'test'}
    ] + list(benchmark_eval_rows)
    evaluation_record_ids = set().union(
        *(source_record_ids(row) for row in evaluation_rows)
    ) if evaluation_rows else set()

    candidates = []
    counters = Counter()
    for row in catalog_rows:
        if not row.get('text'):
            continue
        rights_status = row.get('redistribution_status')
        if rights_status == 'rights_cleared':
            rights_basis = row.get('public_rights_basis') or []
        elif rights_status == 'rights_cleared_noncommercial_sharealike':
            rights_basis = row.get('noncommercial_rights_basis') or []
        else:
            continue
        if not rights_basis or not all(
            is_publishable_provenance(item)
            or (
                item.get('license_id') == 'CC-BY-NC-SA-4.0'
                and item.get('commercial_use_status') == 'noncommercial_only'
                and bool(item.get('attribution'))
                and bool(item.get('source_url'))
            )
            for item in rights_basis
        ):
            continue
        if row.get('language_bucket') != 'garhwali_candidate':
            continue
        sources = row.get('sources') or []
        languages = {
            item.get('iso_639_3') for item in sources
            if isinstance(item, dict) and item.get('iso_639_3')
        }
        if languages != {'gbm'}:
            continue
        counters['rights_and_language_candidates'] += 1
        if row.get('id') in existing_ids:
            counters['excluded_existing_identity'] += 1
            continue
        if source_record_ids({'sources': sources}) & evaluation_record_ids:
            counters['excluded_evaluation_source_record'] += 1
            continue
        text_key = normalized_text_key(row.get('text'))
        if not text_key or text_key in existing_text_keys:
            counters['excluded_normalized_existing_text'] += 1
            continue
        candidates.append((text_key, row))

    selected = {}
    for text_key, row in sorted(candidates, key=lambda item: item[1].get('id') or ''):
        if text_key in selected:
            counters['excluded_normalized_internal_duplicate'] += 1
            continue
        selected[text_key] = row

    output = []
    for row in selected.values():
        rights_basis = (
            row.get('noncommercial_rights_basis') or []
            if row.get('redistribution_status') == 'rights_cleared_noncommercial_sharealike'
            else row.get('public_rights_basis') or []
        )
        enriched = dict(row)
        enriched.update({
            'language': 'gbm',
            'source_languages': ['gbm'],
            'split': 'train',
            'split_assignment': (
                'supplementary redistributable resource; normalized duplicates and '
                'project held-out evaluation source-record overlaps excluded; '
                'upstream dev/test overlaps route to source_overlap; not an '
                'evaluation split'
            ),
            'intended_use': ['language_resource_lookup', 'research'],
            'recommended_for_training': False,
            'recommended_for_evaluation': False,
            'provenance': list(rights_basis),
            'quality_flags': list(row.get('record_quality_flags') or []),
        })
        output.append(enriched)
    counters['records'] = len(output)
    counters['characters'] = sum(len(row['text']) for row in output)
    counters['whitespace_words'] = sum(len(row['text'].split()) for row in output)
    counters['recommended_for_training'] = sum(
        bool(row.get('recommended_for_training')) for row in output
    )
    return output, dict(counters)


def recommended_text_training_row(row):
    if row.get('split') not in (None, 'train'):
        return False
    rights_basis = row.get('public_rights_basis') or []
    provenance = row.get('provenance') or row.get('sources') or []
    source_rows = [
        item for item in [*provenance, *rights_basis]
        if isinstance(item, dict)
    ]
    source_training_flags = [
        item['training_eligible'] for item in source_rows
        if isinstance(item.get('training_eligible'), bool)
    ]
    source_quality_flags = {
        flag
        for item in source_rows
        for flag in item.get('quality_flags') or []
        if isinstance(flag, str) and flag
    }
    if (
        (source_training_flags and not any(source_training_flags))
        or source_quality_flags
        or row.get('record_quality_flags')
    ):
        return False
    return bool(
        row.get('language') == 'gbm'
        and set(row.get('source_languages') or []) == {'gbm'}
        and row.get('language_buckets') == ['garhwali_candidate']
        and 'strict_gold_candidate' in (row.get('quality_tiers') or [])
        and not row.get('quality_flags')
        and rights_basis
        and all(is_publishable_provenance(item) for item in rights_basis)
    )


def text_row(row, parent_quality=None):
    scripts = set()
    for character in row['text']:
        codepoint = ord(character)
        if 0x0900 <= codepoint <= 0x097F:
            scripts.add('Deva')
        elif 0x0980 <= codepoint <= 0x09FF:
            scripts.add('Beng')
        elif character.isascii() and character.isalpha():
            scripts.add('Latn')
    script = next(iter(scripts)) if len(scripts) == 1 else ('Mixed' if scripts else 'Other')
    parent_quality = parent_quality or {}
    parent_records = [
        parent_quality[parent['text_sha256']]
        for parent in row.get('parents') or []
        if parent.get('text_sha256') in parent_quality
    ]
    language_buckets = sorted({
        parent.get('language_bucket') for parent in parent_records
        if parent.get('language_bucket')
    })
    quality_tiers = sorted({
        (parent.get('quality_v2') or {}).get('tier') for parent in parent_records
        if (parent.get('quality_v2') or {}).get('tier')
    })
    languages = source_languages(row)
    if language_buckets == ['garhwali_candidate']:
        language = 'gbm'
    elif 'mixed_language' in language_buckets:
        language = 'mul'
    elif 'review' in language_buckets:
        language = 'und'
    elif len(languages) == 1:
        language = languages[0]
    elif languages:
        language = 'mul'
    else:
        language = 'und'
    exported = {
        'id': row['segment_sha256'],
        'text': row['text'],
        'language': language,
        'source_languages': languages,
        'language_buckets': language_buckets,
        'quality_tiers': quality_tiers,
        'recommended_for_training': False,
        'script': script,
        'split': row['split'],
        'duplicate_component_id': row.get('duplicate_component_id'),
        'original_split': row.get('original_split') or '',
        'split_assignment': row.get('split_assignment') or '',
        'quality_flags': row.get('quality_flags') or [],
        'provenance': [
            enrich_source_attribution(item) for item in provenance_items(row)
        ],
        'public_rights_basis': [
            catalog_provenance(item) for item in publishable_provenance_items(row)
        ],
    }
    exported['recommended_for_training'] = recommended_text_training_row(exported)
    return exported


def with_public_rights_basis(row):
    enriched = dict(row)
    enriched['provenance'] = [
        enrich_source_attribution(item) for item in provenance_items(row)
    ]
    enriched['public_rights_basis'] = [
        catalog_provenance(item) for item in publishable_provenance_items(row)
    ]
    return enriched


def lexicon_row(row):
    enriched = with_public_rights_basis(row)
    enriched['source_text_sha256'] = row.get('text_sha256')
    enriched['form_sha256'] = hashlib.sha256(
        str(row.get('form') or '').encode('utf-8')
    ).hexdigest()
    return enriched


def refresh_acceptable_responses(rows):
    groups = {}
    for row in rows:
        key = (
            row.get('task'),
            ' '.join(str(row.get('instruction') or '').casefold().split()),
        )
        groups.setdefault(key, set()).add(row.get('response'))
    for row in rows:
        key = (
            row.get('task'),
            ' '.join(str(row.get('instruction') or '').casefold().split()),
        )
        row['acceptable_responses'] = sorted(groups[key])
    return rows


def catalog_provenance(item):
    item = enrich_source_attribution(item)
    item = (
        open_bible_stories_provenance(item)
        or noncommercial_catalog_provenance(item)
        or pib_policy_catalog_provenance(item)
        or panos_reproduction_policy_provenance(item)
        or item
    )
    keep = (
        'source_id', 'source_url', 'source_title', 'source_kind',
        'source_snapshot_sha256', 'source_capture_id', 'source_capture_path',
        'source_notes', 'source_capture_bytes', 'record_id', 'source_revision',
        'source_history_url', 'source_title', 'item_url', 'iso_639_3', 'genre', 'script',
        'transcription_split', 'main_split', 'canonical_transcript_source',
        'license', 'license_id', 'license_url', 'rights_status', 'quality_flags',
        'training_eligible', 'experimental_training_eligible',
        'rights_evidence', 'attribution', 'attribution_name', 'contributor',
        'contributor_profile_url', 'contributor_added_date', 'attribution_status',
        'attribution_evidence_url', 'attribution_evidence_sha256',
        'attribution_evidence_retrieved_at', 'source_api_url', 'api_retrieved_at',
        'upstream_owner', 'upstream_orphaned', 'upstream_unapproved',
        'commercial_use_status', 'model_training_status',
        'third_party_material_included', 'sharealike_required',
        'permitted_audiences',
        'source_pdf', 'source_pdf_sha256', 'pdf_page', 'title', 'author',
        'publication_year', 'extraction_method', 'modifications',
    )
    result = {key: item.get(key) for key in keep if item.get(key) not in (None, '', [])}
    for key, value in source_record_locator(item).items():
        result.setdefault(key, value)
    if not result.get('source_url') and result.get('source_id') in SOURCE_URLS:
        result['source_url'] = SOURCE_URLS[result['source_id']]
    return result


def catalog_row(row, include_all_text=False, refinement=None):
    items = provenance_items(row)
    rights_basis = publishable_provenance_items(row)
    noncommercial_basis = catalog_noncommercial_basis(row)
    policy_basis = catalog_policy_basis(row)
    text = row.get('text_model') or row.get('text_clean') or row.get('text') or ''
    factual_basis = individual_word_fact_basis(row, text)
    distributable = bool(
        rights_basis or noncommercial_basis or policy_basis or factual_basis
    )
    text_is_public = distributable
    if rights_basis:
        redistribution_status = 'rights_cleared'
        commercial_use_status = 'permitted_under_row_level_license'
    elif noncommercial_basis:
        redistribution_status = 'rights_cleared_noncommercial_sharealike'
        commercial_use_status = 'noncommercial_only'
    elif policy_basis:
        redistribution_status = 'reproduced_under_source_policy'
        commercial_use_status = (
            'not_authorized_by_source_policy'
            if any(item.get('commercial_use_status') == 'not_authorized_by_source_policy'
                   for item in policy_basis)
            else 'not_explicitly_addressed_by_source_policy'
        )
    elif factual_basis:
        redistribution_status = 'individual_word_fact'
        commercial_use_status = 'no_source_license_claimed_for_single_word'
    else:
        redistribution_status = 'rights_pending'
        commercial_use_status = 'not_cleared'
    sharealike_required = any(
        item.get('license_id') in {'CC-BY-SA-4.0', 'CC-BY-NC-SA-4.0'}
        for item in rights_basis + noncommercial_basis
    )
    exported = {
        'id': row['text_sha256'],
        'split': row.get('split'),
        'text': text if distributable or include_all_text else None,
        'text_sha256': row['text_sha256'],
        'source_text_sha256': row['text_sha256'],
        'release_text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'text_character_count': len(text),
        'content_included': distributable or include_all_text,
        'active_for_quality_work': True,
        'text_publicly_available': text_is_public,
        'redistribution_status': redistribution_status,
        'commercial_use_status': commercial_use_status,
        'sharealike_required': sharealike_required,
        'redaction_reason': None if text_is_public or include_all_text else 'source_rights_do_not_permit_public_text_redistribution',
        'language_bucket': row.get('language_bucket'),
        'language_quality': row.get('language_quality'),
        'dialect_quality': row.get('dialect_quality'),
        'genre_quality': row.get('genre_quality'),
        'surface_quality': row.get('quality'),
        'quality_v2': row.get('quality_v2'),
        'sources': [
            {key: value for key, value in catalog_provenance(item).items()
             if not factual_basis or key != 'record_id'}
            for item in items
        ],
        'public_rights_basis': [catalog_provenance(item) for item in rights_basis + policy_basis],
        'noncommercial_rights_basis': [
            catalog_provenance(item) for item in noncommercial_basis
        ],
        'factual_publication_basis': factual_basis,
    }
    if refinement:
        exported['text_refinement'] = {
            key: refinement.get(key) for key in (
                'automatic_changes', 'review_signals', 'manual_review_required',
                'language_decision', 'quality_refinement_status',
                'release_text_sha256', 'quality_dimensions', 'review_priority',
            )
        }
        if text_is_public or include_all_text:
            exported['text_refinement']['release_text'] = refinement.get('release_text')
    return exported


def source_catalog_for_family(family):
    path = KNOWLEDGE_SOURCE_CATALOGS.get(family)
    if path is None or not path.exists():
        return {}
    catalog = json.loads(path.read_text(encoding='utf-8'))
    sources = {
        item['source_id']: item
        for item in catalog.get('sources', [])
        if item.get('source_id')
    }
    # Some catalog families share captures but keep their source registries
    # separately. Merge matching IDs so exported references retain the best
    # available URL or capture fingerprint.
    for other_path in KNOWLEDGE_SOURCE_CATALOGS.values():
        if not other_path.exists():
            continue
        for item in json.loads(other_path.read_text(encoding='utf-8')).get('sources', []):
            if item.get('source_id'):
                sources.setdefault(item['source_id'], item)
                if item['source_id'] in sources:
                    sources[item['source_id']] = {
                        **item, **sources[item['source_id']],
                        **{key: value for key, value in item.items()
                           if value and not sources[item['source_id']].get(key)},
                    }
    if family == 'geography':
        aliases = {
            'division_district_list': 'Garhwal Mandal official introduction',
            'division_headquarters': 'Garhwal Mandal official introduction',
            'district_portal': 'Government of Uttarakhand district portal',
            'district_page': 'Government of Uttarakhand district portal',
            'tehsil_list': 'Wikipedia list of tehsils of Uttarakhand',
            'map_lookup': 'OpenStreetMap search',
            'wikipedia_place': 'Wikipedia Garhwal division',
            'wikipedia_geography': 'Wikipedia Garhwal division',
            'division_geography': 'Wikipedia Garhwal division',
            'historic_capital': 'Wikipedia Garhwal division',
            'river_confluence': 'Wikipedia Garhwal division',
            'river_source': 'Wikipedia Garhwal division',
            'mountain_geography': 'Wikipedia Garhwal division',
            'protected_area': 'Wikipedia Garhwal division',
            'government_water_source': 'Garhwal Mandal official introduction',
            'pilgrimage_geography': 'Wikipedia Garhwal division',
        }
        by_name = {item.get('name'): item for item in catalog.get('sources', [])}
        for source_id, name in aliases.items():
            if name in by_name:
                sources[source_id] = by_name[name]
                sources[source_id]['source_id'] = source_id
    return sources


def source_provenance(source_id, source_catalog):
    source = source_catalog.get(source_id) or {}
    result = {'source_id': source_id}
    mapped = {
        'source_url': source.get('url') or source.get('canonical_url') or source.get('source_url'),
        'source_title': source.get('title') or source.get('name'),
        'source_kind': source.get('source_kind'),
        'source_snapshot_sha256': source.get('sha256'),
        'source_capture_id': source.get('capture_id'),
        'source_capture_path': source.get('local_capture'),
        'source_notes': source.get('notes'),
        'source_capture_bytes': source.get('captured_text_bytes'),
    }
    result.update({key: value for key, value in mapped.items() if value not in (None, '', [])})
    return result


def knowledge_row(row, family, source_catalog=None):
    """Add stable IDs and explicit provenance, quality, and rights fields."""
    identity = next(
        (row.get(key) for key in ('id', 'record_id', 'person_id', 'term_id') if row.get(key)),
        None,
    )
    if not identity:
        raise ValueError(f'{family} knowledge record has no stable ID')
    source_catalog = source_catalog or {}
    exported = {**row, 'id': identity, 'knowledge_family': family}
    if not exported.get('provenance'):
        provenance = []
        for field in ('source_ids', 'source_refs', 'evidence'):
            values = exported.get(field) or []
            if isinstance(values, str):
                values = [values]
            provenance.extend(
                source_provenance(value, source_catalog)
                for value in values if isinstance(value, str) and value.strip()
            )
        for field in (
            'source_url', 'wikipedia_url', 'osm_search_url', 'youtube_url',
            'lyrics_sources', 'translation_sources',
        ):
            values = exported.get(field) or []
            if isinstance(values, str):
                values = [values]
            provenance.extend(
                {'source_url': value}
                for value in values if isinstance(value, str) and value.strip()
            )
        exported['provenance'] = provenance
    else:
        exported['provenance'] = [
            {
                **(
                    source_provenance(item.get('source_id'), source_catalog)
                    if item.get('source_id') else {}
                ),
                **item,
            }
            for item in exported['provenance']
            if isinstance(item, dict)
        ]
    exported.setdefault('quality_metadata', {
        'review_status': 'not_reviewed',
        'source_verification_status': (
            exported.get('verification_status')
            or exported.get('ingestion_status')
            or 'not_assessed'
        ),
        'native_reviewed': False,
        'evidence_fields': [
            field for field in (
                'evidence', 'source_refs', 'source_ids', 'source_url',
                'wikipedia_url', 'lyrics_sources', 'translation_sources',
            ) if exported.get(field)
        ],
    })
    exported.setdefault('rights_status', 'not_assessed')
    exported.setdefault('public_rights_basis', [])
    return exported


PUBLIC_FACT_FIELDS = {
    'geography': (
        'name', 'name_local', 'division', 'districts', 'coordinates',
        'coordinates_status', 'place_type', 'wikipedia_title', 'wikipedia_url',
        'osm_query', 'osm_search_url', 'evidence',
    ),
    'historical_terms': (
        'term', 'term_local', 'name_variants', 'period', 'term_type', 'source_refs',
    ),
    'literary_people': (
        'canonical_name', 'aliases', 'associated_works', 'roles', 'source_ids',
        'verification_status',
    ),
    'literary_works': (
        'title', 'title_variants', 'creators', 'date_or_period', 'language_scope',
        'work_type', 'source_ids', 'ingestion_status',
    ),
    'popular_songs': (
        'title', 'artists', 'genre', 'language', 'caption_status', 'youtube_url',
        'youtube_video_id', 'lyrics_sources', 'translation_sources',
    ),
    'university_research': (
        'title', 'creators', 'institution', 'year', 'resource_type', 'language_scope',
        'topics', 'source_authority', 'source_url', 'visibility', 'access_level',
        'already_covered_by', 'ingestion_status',
    ),
}

PUBLIC_FACT_METADATA_FIELDS = {
    'id', 'knowledge_family', 'record_scope', 'rights_status',
    'expressive_source_content_included', 'omitted_content_fields',
    'provenance', 'public_metadata_note', 'quality_metadata',
    'reuse_scope', 'license_labels', 'quality_status', 'record_quality_flags',
}


def is_public_factual_metadata_row(row, family):
    """Validate the narrow metadata-only projection without asserting a license."""
    if family not in PUBLIC_FACT_FIELDS:
        return False
    return (
        row.get('knowledge_family') == family
        and row.get('record_scope') == 'factual_bibliographic_metadata_only'
        and row.get('rights_status') == 'metadata_only; no license asserted for underlying work'
        and row.get('expressive_source_content_included') is False
        and set(row).issubset(set(PUBLIC_FACT_FIELDS[family]) | PUBLIC_FACT_METADATA_FIELDS)
    )


def public_factual_metadata_row(row, family):
    """Release citation-level facts while omitting unlicensed source prose/content."""
    if family not in PUBLIC_FACT_FIELDS:
        raise ValueError(f'No factual-metadata projection for {family}')
    exported = {
        key: row[key] for key in PUBLIC_FACT_FIELDS[family]
        if key in row and row[key] not in (None, '', [])
    }
    exported.update({
        'id': row['id'],
        'knowledge_family': family,
        'record_scope': 'factual_bibliographic_metadata_only',
        'rights_status': 'metadata_only; no license asserted for underlying work',
        'expressive_source_content_included': False,
        'omitted_content_fields': [
            'extended_notes', 'source_passages', 'abstracts_or_summaries',
            'song_lyrics', 'translations', 'full_work_text',
        ],
        'provenance': [
            {
                key: item[key] for key in (
                    'source_id', 'source_url', 'source_title', 'source_kind',
                    'source_snapshot_sha256', 'source_capture_path', 'record_id',
                ) if item.get(key) not in (None, '', [])
            }
            for item in row.get('provenance') or []
            if isinstance(item, dict)
        ],
        'public_metadata_note': (
            'Only names, titles, dates, categories, identifiers, and source citations '
            'are included. This row does not license the underlying book, article, '
            'song, recording, or source-page prose.'
        ),
        'quality_metadata': {
            key: value for key, value in (row.get('quality_metadata') or {}).items()
            if key in {
                'review_status', 'source_verification_status',
                'native_reviewed', 'evidence_fields',
            }
        },
    })
    return exported


def write_shards(rows, directory, split, shard_rows=10_000):
    directory.mkdir(parents=True, exist_ok=True)
    for old in directory.glob(f'{split}-*.jsonl'):
        old.unlink()
    count = 0
    shard = -1
    handle = None
    paths = []
    try:
        family = directory.name
        for row in rows:
            if count % shard_rows == 0:
                if handle:
                    handle.close()
                shard += 1
                path = directory / f'{split}-{shard:05d}.jsonl'
                paths.append(path)
                handle = path.open('w', encoding='utf-8')
            row = normalize_record(row, family=family)
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
            count += 1
    finally:
        if handle:
            handle.close()
    files = [str(path.name) for path in paths]
    return {
        'records': count,
        'shards': len(paths),
        'files': files,
        'file_sha256': {path.name: sha256_file(path) for path in paths},
    }


def link_audio(rows, output):
    linked = 0
    seen = set()
    for row in rows:
        digest = row['audio_sha256']
        if digest in seen:
            continue
        seen.add(digest)
        source = (ROOT / row['local_audio_path']).resolve()
        audio_root = (ROOT / 'data/vaani/audio').resolve()
        if source.is_symlink() or not source.is_file() or not source.is_relative_to(audio_root):
            raise ValueError(f'unsafe audio source path: {row["local_audio_path"]}')
        if sha256_file(source) != digest:
            raise ValueError(f'audio SHA-256 mismatch: {row["local_audio_path"]}')
        target = output / content_audio_path(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            try:
                os.link(source, target)
            except OSError as error:
                if error.errno != errno.EXDEV:
                    raise
                shutil.copy2(source, target)
            linked += 1
    return {'new': linked, 'total': len(seen)}


def remove_packaged_audio(output):
    directory = Path(output) / 'audio'
    count = sum(1 for _ in directory.rglob('*.wav')) if directory.exists() else 0
    if directory.exists():
        shutil.rmtree(directory)
    return count


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def source_expansion_metrics():
    """Read the pinned-source intake manifests for the current major release."""
    jambu_path = ROOT / 'corpus/jambu_garhwali_manifest.json'
    library_path = ROOT / 'corpus/garhwali_language_library_manifest.json'
    jambu = json.loads(jambu_path.read_text(encoding='utf-8'))
    library = json.loads(library_path.read_text(encoding='utf-8'))
    return {
        'jambu': {
            'source_records': jambu.get('records', 0),
            'unique_forms': jambu.get('unique_forms', 0),
            'cross_source_overlap': jambu.get('exact_overlap_with_existing_unique_forms', 0),
            'new_vs_other_sources': jambu.get('exact_new_unique_forms', 0),
            'already_in_current_corpus': jambu.get('already_in_current_corpus_unique_forms', 0),
        },
        'language_library': {
            'source_records': library.get('source_records', 0),
            'unique_strings': library.get('unique_surface_forms', 0),
            'cross_source_overlap': library.get('exact_overlap_with_existing_unique_forms', 0),
            'new_vs_current_corpus': library.get('exact_new_unique_forms', 0),
            'records_by_type': library.get('records_by_type', {}),
        },
    }


def _is_hf_null_feature(feature):
    return (
        isinstance(feature, dict)
        and feature.get('_type') == 'Value'
        and feature.get('dtype') == 'null'
    )


def _merge_hf_feature_nodes(left, right, path):
    if left == right:
        return copy.deepcopy(left)
    if _is_hf_null_feature(left):
        return copy.deepcopy(right)
    if _is_hf_null_feature(right):
        return copy.deepcopy(left)
    if isinstance(left, dict) and isinstance(right, dict):
        left_type = left.get('_type')
        right_type = right.get('_type')
        if left_type == right_type == 'List':
            return {
                **copy.deepcopy(left),
                'feature': _merge_hf_feature_nodes(
                    left['feature'], right['feature'], f'{path}[]'
                ),
            }
        if left_type or right_type:
            raise ValueError(
                f'incompatible Hugging Face feature at {path}: '
                f'{left!r} versus {right!r}'
            )
        merged = {}
        for key in sorted(set(left) | set(right)):
            if key in left and key in right:
                merged[key] = _merge_hf_feature_nodes(
                    left[key], right[key], f'{path}.{key}'
                )
            else:
                merged[key] = copy.deepcopy(
                    left[key] if key in left else right[key]
                )
        return merged
    raise ValueError(
        f'incompatible Hugging Face feature at {path}: '
        f'{left!r} versus {right!r}'
    )


def merge_hf_feature_schemas(schemas):
    """Union JSON shard schemas, promoting null-only fields to observed types."""
    merged = {}
    for schema in schemas:
        merged = _merge_hf_feature_nodes(merged, schema, 'root')
    return merged


def infer_hf_config_features(config_dir):
    """Infer one stable Hub schema across a config's independently written shards."""
    try:
        from datasets import Dataset, Features
    except ImportError as exc:
        raise RuntimeError(
            'Install requirements-hf-release.txt to infer Dataset Viewer feature metadata'
        ) from exc

    shard_paths = sorted(Path(config_dir).glob('*.jsonl'))
    if not shard_paths:
        raise ValueError(f'No JSONL shards found in {config_dir}')
    with tempfile.TemporaryDirectory(prefix='garhwali-hf-feature-schema-') as cache_dir:
        schemas = [
            Dataset.from_json(
                str(path), cache_dir=cache_dir, keep_in_memory=True,
                chunksize=path.stat().st_size + 1,
            ).features.to_dict()
            for path in shard_paths
        ]
    features = Features.from_dict(merge_hf_feature_schemas(schemas))
    return features._to_yaml_list()


def dataset_info_for_release(output, config_report):
    """Declare stable features for configs that the Hub cannot safely infer."""
    dataset_info = []
    for config_name in (
        'sravaani_drafts', 'text', 'text_expansion', 'text_resources',
        'paharili_gbm',
    ):
        if config_report.get(f'{config_name}/train', {}).get('records', 0):
            dataset_info.append({
                'config_name': config_name,
                'features': infer_hf_config_features(
                    Path(output) / 'data' / config_name
                ),
            })
    return dataset_info


def dataset_card(report, dataset_info=None):
    release_version = str(report.get('release_id', '')).rsplit('-v', 1)[-1]
    candidate_history = ''
    if release_version == '0.2.4':
        candidate_history = '''
4. **v0.2.2 — improve traceability and report usable counts.** The package
   resolves existing social-record IDs to their item URLs, separates source
   references from content rows, reports rights and reuse labels by config, and
   adds a deduplicated `text_expansion` view from already-collected catalog
   values. Earlier files remain available.
5. **v0.2.3 — surface additional existing Garhwali resources.** Adds a
   deduplicated, rights-filtered `text_resources` view for catalog text not
   already present in other text-bearing configurations. The view preserves
   row-level rights and quality signals, excludes held-out evaluation source
   records, and is explicitly not an evaluation set or uniformly training-ready.
6. **v0.2.4 — improve source attribution and revision traceability.** Recovers
   creator attribution for 36 existing Tatoeba sentences and adds immutable
   page-revision/history links for 319 existing Wikimedia and Wiktionary
   records. No new text is added; source text, release eligibility, and review
   status are not promoted by this metadata update.'''
    elif release_version == '0.2.5':
        candidate_history = '''
4. **v0.2.2 — improve traceability and report usable counts.** Resolves existing
   social-record IDs to item URLs, separates source references from content,
   and adds a deduplicated `text_expansion` view from collected catalog values.
5. **v0.2.3 — surface existing Garhwali resources.** Adds a deduplicated,
   rights-filtered `text_resources` view with row-level source and quality data.
6. **v0.2.4 — improve source attribution and revision traceability.** Recovers
   creator attribution for 36 Tatoeba sentences and immutable history links for
   319 Wikimedia/Wiktionary records. It adds no source text.
7. **v0.2.5 — prevent upstream evaluation-source overlap in default train.**
   Keeps all records but routes text linked to upstream Meta/VAANI development
   or test sources into an explicit `source_overlap` split. The split audit and
   evidence IDs are included with the release.'''
    elif release_version == '0.2.3':
        candidate_history = '''
5. **v0.2.3 — surface additional existing Garhwali resources.** Adds a
   deduplicated, rights-filtered `text_resources` view for catalog text not
   already present in other text-bearing configurations. The view preserves
   row-level rights and quality signals, excludes held-out evaluation source
   records, and is explicitly not an evaluation set or uniformly training-ready.'''
    elif release_version == '0.2.2':
        candidate_history = '''
4. **v0.2.2 — improve traceability and report usable counts.** The package
   resolves existing social-record IDs to their item URLs, separates source
   references from content rows, reports rights and reuse labels by config, and
   adds a deduplicated `text_expansion` view from already-collected catalog
   values. Earlier files remain available.'''
    draft_status = 'complete' if report['drafts_complete'] else 'partial'
    exported_rows = sum(item['records'] for item in report['configs'].values())
    draft_unique_audio = report.get('draft_unique_audio', 0)
    draft_nonempty_audio = report.get(
        'draft_unique_nonempty_audio', draft_unique_audio
    )
    draft_empty_audio = report.get(
        'draft_empty_audio', max(0, draft_unique_audio - draft_nonempty_audio)
    )
    draft_source_rows = report.get('draft_records')
    draft_source_summary = (
        f' from {draft_source_rows:,} source rows'
        if draft_source_rows is not None else ''
    )
    audio_summary = (
        f"The package includes **{report['linked_audio_files']:,} content-addressed audio files**."
        if report['include_audio'] else
        'This transcript-only package does not include audio files or source filenames.'
    )
    nonempty_configs = {
        key: value for key, value in report['configs'].items()
        if value.get('records', 0) > 0
    }
    config_names = sorted({key.split('/', 1)[0] for key in nonempty_configs})
    config_count = len(config_names)
    config_word = 'configuration' if config_count == 1 else 'configurations'
    config_blocks = []
    for name in config_names:
        splits = set()
        for key, value in sorted(nonempty_configs.items()):
            config, split = key.split('/', 1)
            if config != name:
                continue
            # Dataset metadata accepts one declaration per split. Use a shard
            # glob so multiple JSONL shards do not become duplicate split names.
            splits.add(split)
        files = [
            f'  - split: {split}\n    path: data/{name}/{split}-*.jsonl'
            for split in sorted(splits)
        ]
        config_blocks.append(
            f'- config_name: {name}\n  data_files:\n' + '\n'.join(files)
        )
    configs_yaml = '\n'.join(config_blocks)
    dataset_info_yaml = ''
    if dataset_info:
        # JSON flow collections are valid YAML and keep generated feature
        # metadata deterministic without adding a YAML dependency to the pipeline.
        dataset_info_yaml = (
            'dataset_info: '
            + json.dumps(dataset_info, ensure_ascii=False, separators=(',', ':'))
            + '\n'
        )
    config_uses = {
        'asr': 'provider transcripts; not native-adjudicated',
        'catalog': 'unique text inventory with content and metadata-only entries',
        'geography': 'place facts and citations',
        'historical_terms': 'historical names and terms',
        'instructions': 'instruction/response examples',
        'lexicon': 'vocabulary and pronunciation candidates',
        'literary_people': 'writer and contributor metadata',
        'literary_works': 'work-level bibliography',
        'popular_songs': 'song-level metadata; no lyrics',
        'paharili_gbm': 'Garhwali-labeled PahariLI language-identification text; unreviewed and retains source-lineage and rights caveats',
        'record_index': 'archive references; not training examples',
        'record_sources': 'record-to-source links; not training examples',
        'source_catalog': 'deduplicated source and rights references',
        'sravaani_drafts': 'machine transcript drafts; not ground truth',
        'text': 'Garhwali text examples; source_overlap preserves rows linked to upstream dev/test content outside train',
        'text_expansion': 'strict-tier candidates; upstream dev/test overlaps are in source_overlap; not evaluation data',
        'text_resources': 'additional rights-cleared Garhwali resources; quality varies; upstream overlaps are separately split',
        'university_research': 'research bibliography',
    }
    config_rows = []
    for name in config_names:
        row_count = sum(
            details.get('records', 0)
            for key, details in nonempty_configs.items()
            if key.split('/', 1)[0] == name
        )
        config_rows.append(
            f'| `{name}` | {row_count:,} | '
            f'{config_uses.get(name, "source-specific records; inspect the schema")} |'
        )
    config_table = '\n'.join(config_rows)
    speech_companion = ''
    if profile_includes_all_data(report['profile']):
        language_header = '- gbm\n- hi\n- en'
        package_summary = (
            f'This complete all-data package contains **{exported_rows:,} records** '
            f'across {config_count} named {config_word} '
            f'({len(nonempty_configs)} config/split entries)'
        )
        resource_summary = '''Versioned Garhwali (`gbm`) text, speech, lexicon,
instructions, geography, historical terms, literature, music, and university-
research resources built by the Garhwali Language Lab. Available source, rights,
and review metadata vary by configuration.'''
        catalog_summary = f'''The `catalog` configuration contains all
**{report['catalog_records']:,} exact-unique collected text records with their full
text values. No catalog text values are redacted. Source, license, rights status,
quality tier, language evidence, and review state remain attached to every row so
research use and any later redistribution decision can be audited.'''
        access_notice = '''> **Access warning:** this all-data profile contains
restricted and rights-pending source content. Keep it local or access-controlled;
do not publish it as an open dataset until every included component is cleared.
It retains all structured records with row-level source, quality, and rights
metadata attached.'''
    else:
        speech_companion = '''\n\n## Linked speech dataset\n\nThe companion [Garhwali Speech dataset](https://huggingface.co/datasets/rushilrawat/garhwali-speech) contains VAANI audio with provider transcripts and separately labeled SraVaani drafts.'''
        language_header = '- gbm'
        package_summary = (
            f'This public-profile package contains **{exported_rows:,} records** '
            f'across {config_count} named {config_word} '
            f'({len(nonempty_configs)} config/split entries)'
        )
        resource_summary = '''This public profile contains Garhwali
text, human transcripts, lexicon and instructions, plus experimental SraVaani
drafts. The geography, history, literature, song, and university-research
configurations contain factual and bibliographic metadata, with expressive
notes, lyrics, summaries, and source passages omitted.'''
        catalog_summary = f'''The `catalog` configuration publicly accounts for all
**{report['catalog_records']:,} exact-unique collected text records**. Rows whose
source terms do not permit redistribution retain their stable content hash,
source URL, rights status, quality tier, language evidence, and review reasons;
their full text is not included in public content. The current catalog exposes **{report.get('catalog_noncommercial_records', 0):,}** CC BY-NC-SA 4.0 records,
**{report.get('catalog_sharealike_records', 0):,}** total share-alike records, and
**{report.get('catalog_source_policy_records', 0):,}** entries under source-specific reproduction policies (5 PIB instrument facts and 193 Mountain Voices glossary headwords), plus **{report.get('catalog_factual_word_records', 0):,}** exact one-token facts published without definitions, source record positions, or list arrangement. The fact-only projection includes individually selected tokens and lexical tokens that appear in at least two distinct thematic source collections; it is not a copy of any source list. The Panos guideline permits attributed reproduction by press, educational/research institutions, and nonprofits; commercial scope and machine-learning training are not expressly addressed, so these headwords are excluded from model-training views. Per-row terms apply; the package asserts no blanket content license.'''
        metadata_only = sum(
            report.get('structured_knowledge_metadata_only', {}).values()
        )
        access_notice = f'''All **{metadata_only:,} structured geography, history, literature, song, and research records** appear in factual/bibliographic form; no records are dropped from these metadata configurations. Prose notes, lyrics, translations, abstracts, and source passages are omitted unless separately licensed. For retained catalog entries, the full text not included in this public profile remains in the local all-data package; entries whose source text was not acquired remain represented by their available source metadata. Each text-catalog record carries its specific rights state: CC BY-SA rows require attribution and share-alike; CC BY-NC-SA rows are noncommercial and share-alike; the five PIB instrument terms cite the PIB reproduction policy; and the 193 Mountain Voices glossary headwords carry Panos's attributed-reproduction guideline for press, educational/research institutions, and nonprofits. That guideline does not expressly address commercial scope or model training, so those values are excluded from model-training views. The **{report.get('catalog_factual_word_records', 0):,}** isolated one-token facts are listed without definitions, source record positions, or list ordering. Lexical facts from unlicensed thematic sources are included only when independently present in at least two distinct source collections; all such facts remain catalog-only, outside training views, and retain language-review flags. See the [source-by-source rights-resolution log](research/text-rights-resolution-2026-09-30.md). Native-speaker review and dialect annotation are deferred; benchmark and model scores are automated research results, not native-validated claims.'''
    expansion_metrics = report.get('text_expansion_metrics') or {}
    resource_metrics = report.get('text_resource_metrics') or {}
    paharili_metrics = report.get('paharili_gbm_metrics') or {}
    text_expansion_summary = f'''## Fast-tracked text expansion

The `text_expansion` config adds **{expansion_metrics.get('records', 0):,}** Garhwali candidate texts from the existing catalog. Each passed automated strict-tier and recorded rights-basis checks, is absent from the existing text splits after NFKC/alphanumeric normalization, and has no source-record ID matching existing text validation/test or frozen benchmark validation/test rows. **{expansion_metrics.get('source_split_overlap_records', 0):,}** values with upstream Meta or VAANI development/test source matches remain published in the `source_overlap` split, outside default `train`. The values remain machine-screened, not native-reviewed. **{expansion_metrics.get('recommended_for_training', 0):,}** currently meet the project's conservative training-recommendation rule; **{max(0, expansion_metrics.get('records', 0) - expansion_metrics.get('recommended_for_training', 0)):,}** do not pass the current source-eligibility or quality gates. This is not training approval; source-page-family isolation is not assessed, so it is not an independent evaluation set. Values also appear in the `catalog` inventory by design; do not add config row counts when reporting unique texts.'''
    text_resources_summary = f'''## Supplementary text resources

The `text_resources` config adds **{resource_metrics.get('records', 0):,}** additional normalized-unique Garhwali records ({resource_metrics.get('whitespace_words', 0):,} whitespace-delimited words; {resource_metrics.get('characters', 0):,} characters) already present in the source catalog. These pass the recorded redistribution-basis and Garhwali-language filters and are absent from the existing text-bearing views after normalized deduplication. Their quality tiers vary; **{resource_metrics.get('recommended_for_training', 0):,}** are currently recommended for training and none are recommended for evaluation. The config is intended for lookup and research. Check each row's `redistribution_status`, license, quality flags, and source terms before reuse. CC BY-NC-SA rows are limited to noncommercial use and require share-alike; this subset is not uniformly training-ready or a native-reviewed text set.'''
    paharili_summary = ''
    if paharili_metrics:
        split_counts = paharili_metrics.get('split_records') or {}
        paharili_summary = f'''## PahariLI Garhwali text addition

The new `paharili_gbm` config adds **{paharili_metrics.get('new_records', 0):,} normalized-unique Garhwali-labeled sentence records** from the [PahariLI corpus](https://github.com/rachanagusain/PahariLI). It starts from {paharili_metrics.get('garhwali_source_records', 0):,} upstream GBM-labeled rows, which reduce to {paharili_metrics.get('normalized_unique_source_texts', 0):,} distinct normalized texts after collapsing {paharili_metrics.get('collapsed_duplicate_source_records', 0):,} repeated source rows. All source record IDs and surface variants are retained: {paharili_metrics.get('new_source_record_ids', 0):,} source IDs appear in this config, and {paharili_metrics.get('source_record_ids_already_in_existing_configs', 0):,} remain on the exact-matching row already in `text_expansion`. That existing text is not duplicated here.

The config keeps the upstream language-identification splits: {split_counts.get('train', 0):,} train, {split_counts.get('test', 0):,} test, and {split_counts.get('source_overlap', 0):,} text groups that occur in both upstream splits. The last group stays in `source_overlap` to avoid train/test leakage. This test split is the upstream PahariLI classification split; it is not an independent evaluation set for the project's language model or other tasks.

The PahariLI repository includes an Apache-2.0 license file, but its README does not identify the sentence-level source of each item. Each row therefore keeps the repository-level license declaration, raw-file URL and SHA-256, source index, attribution, and the existing `source_lineage_missing`, `component_rights_review_required`, and possible scripture/blog flags. The release makes no claim that Apache-2.0 independently clears underlying source text. Rows are unreviewed and not recommended for general language-model training; the upstream `train` partition remains usable for experimental language-identification work. The upstream license text is included at `licenses/PahariLI-Apache-2.0.txt`.'''
    release_version = str(report.get('release_id', '')).rsplit('-v', 1)[-1]
    overlap_audit_url = (
        'https://huggingface.co/datasets/rushilrawat/garhwali-corpus/blob/main/'
        f'releases/v{release_version}/research/'
        'huggingface-upstream-split-overlap-2026-10-05.md'
    )
    text_source_overlap_summary = f'''## Upstream source-split overlap

The text package preserves every row. The `text/source_overlap` split contains **{report.get('text_source_overlap_records', 0):,}** rows previously assigned to `text/train` that carry a Meta dev/test record ID, an official VAANI test-remainder source record, or a transcript match to held-out Meta/VAANI source material. The `text_expansion/source_overlap` split contains **{expansion_metrics.get('source_split_overlap_records', 0):,}** similar catalog additions. These rows remain downloadable and retain their source metadata, but are kept outside the default train split. This is a conservative source-lineage warning, not a claim that all matched audio recordings are identical. See the [split-overlap audit]({overlap_audit_url}).'''
    draft_summary = (
        f'{package_summary}. The SraVaani draft config covers '
        f'**{draft_unique_audio:,} unique audio hashes**{draft_source_summary}: '
        f'**{draft_nonempty_audio:,}** have non-empty draft text and '
        f'**{draft_empty_audio:,}** are empty.'
    )
    source_expansion = ''
    if str(report.get('release_id', '')).endswith('v0.2.1'):
        expansion = report.get('source_expansion') or {}
        jambu = expansion.get('jambu') or {}
        library = expansion.get('language_library') or {}
        type_counts = ', '.join(
            f'{kind} {count:,}'
            for kind, count in sorted((library.get('records_by_type') or {}).items())
        )
        source_expansion = f'''

## Garhwali source additions included in v0.2.1

- **Jambu Garhwali reflex lexicon:** {jambu.get('source_records', 0):,} source rows and
  {jambu.get('unique_forms', 0):,} distinct forms. This source was already in the
  preceding local corpus snapshot; the v0.2.1 refresh revalidates its pinned local
  snapshot and adds **{max(0, jambu.get('unique_forms', 0) - jambu.get('already_in_current_corpus', 0)):,}**
  new forms (the current snapshot already contains {jambu.get('already_in_current_corpus', 0):,}).
  Its earlier intake comparison found {jambu.get('cross_source_overlap', 0):,}
  forms shared with other sources and {jambu.get('new_vs_other_sources', 0):,}
  forms absent from those sources. It is an attributed CC BY 4.0 lexical source,
  not conversational text, and remains unreviewed by native speakers.
- **Garhwali Language Library 1.0.0:** {library.get('source_records', 0):,} pinned static
  word, phrase, proverb, and riddle entries; {library.get('unique_strings', 0):,}
  distinct strings, {library.get('cross_source_overlap', 0):,} exact overlaps with
  the existing corpus, and {library.get('new_vs_current_corpus', 0):,} exact-new
  strings. Types: {type_counts}. The static files are attributed under MIT;
  generated inflection forms are excluded and are not counted as corpus examples.

Both additions retain their upstream spellings, provenance, license and review
state. Exact matches keep source attribution without counting again as new text.
The public profile includes a row only when its rights filter passes. Neither
source entry has received native-speaker review or been promoted into
recommended training splits.
'''
    elif str(report.get('release_id', '')).endswith('v0.2.0'):
        source_expansion = '''

## Garhwali-only additions in v0.2.0

This release adds **671 exact-unique source texts** after normalization and
cross-corpus deduplication (696 source rows; 673 unique values within this
intake, including two exact matches already held in earlier layers):

- 632 Garhwali entries from the dialect-comparison table in the
  [Linguistic Survey of India, Vol. IX, Part IV](https://archive.org/details/LSIV0-V11),
  representing 609 exact-unique forms explicitly tagged Standard, Rathi, or
  Tehri. 496 table rows have OCR confidence below 60/100; all OCR remains
  machine-produced and unreviewed.
- Nine Devanagari Garhwali language specimens from the same historical volume.
  These are source-grounded OCR excerpts, not modern conversational speech.
- Five sayings explicitly identified as Garhwali in Upreti's 1894
  [*Proverbs & Folklore of Kumaun and Garhwal*](https://archive.org/details/cu31924089930774).
- Fifty Garhwali Open Bible Stories from the pinned
  [Door43 OBS-TLF source](https://git.door43.org/OBS-TLF/gbm_obs), revision
  `f08afc73e1770129fbcd3089181f2faf2abbf54d`, licensed CC BY-SA 4.0.

The historical excerpts use a recorded Public Domain Mark basis; each story
retains the upstream attribution and CC BY-SA terms. The corpus rows preserve
page, source revision or checksum, rights, script/language evidence, and quality
status. The OCR and translated stories have not received native-speaker review.
For the public profile, only rows passing the project's rights filter carry
full text; the all-data package retains every collected value locally.
'''
    return f'''---
language:
{language_header}
license: other
task_categories:
- automatic-speech-recognition
- text-classification
- text-generation
- translation
configs:
{configs_yaml}
{dataset_info_yaml}---

# Garhwali Language Lab

Release: **{report['release_id']}**

{access_notice}
{source_expansion}

## Project history

This release is the result of a staged corpus build, with older releases kept
available under their own versioned paths:

1. **v0.1.x — establish the corpus workflow.** The project began by collecting
   Garhwali text and language references with source attribution, then added a
   reproducible preparation and release pipeline.
2. **v0.2.0 — expand Garhwali-only sources.** A deduplicated source wave added
   671 exact-unique texts, including historical Garhwali specimens and stories.
   Historical OCR and translated stories remain visibly marked as unreviewed.
3. **v0.2.1 — continue the corpus and make it easier to use (30 September–1 October 2026).**
   The follow-up added 164 exact-new strings after deduplication, brought more
   values into the rights-filtered profile under their recorded bases, and
   exposed factual/bibliographic metadata for all 216 structured records. The
   release also adds a consistent rights-and-quality envelope, exact-count
   quick start, schema guide, searchable lexicon example, and linked speech
   dataset. Earlier release files remain available.
{candidate_history}

The figures below describe the current v{release_version} package, not a cumulative sum of
overlapping views. Row-level terms and quality labels remain authoritative.

## Developer quick start

Install the small tabular-data stack with `pip install datasets pandas duckdb`,
then stream three vocabulary entries:

```python
from datasets import load_dataset

lexicon = load_dataset(
    "rushilrawat/garhwali-corpus", "lexicon", split="train", streaming=True
)
for row in lexicon.take(3):
    print(row["form"], row.get("glosses"), row["rights_status"], row["quality_status"])
```

Counts are rows in the current views, not unique examples. Configurations can
overlap, and reference-index rows are not model-training examples. See the
[developer quick start](DEVELOPER_QUICKSTART.md), [schema guide](DATASET_SCHEMA.md),
and [lexicon search script](search_garhwali_lexicon.py) for practical examples.

## Configurations and current row counts

| Configuration | Rows | Use |
| --- | ---: | --- |
{config_table}

{resource_summary}

{draft_summary} {audio_summary}

This dataset card describes data scope, not model accuracy. Native-speaker
review and dialect annotation are deferred; transcripts and machine drafts retain
their review status. The project pipeline uses Python 3.12 and LangGraph for
resumable ingestion; quality checks and model metrics use task-specific scripts.
LangChain is not part of the current pipeline. See the [project README](https://github.com/rushilrawat/Garhwali-Language-Lab/blob/main/README.md)
and [benchmark research status](https://github.com/rushilrawat/Garhwali-Language-Lab/blob/main/research/benchmark-research-status-2026-09-25.md)
for the latest measured results and limitations.

{catalog_summary}

{text_source_overlap_summary}

{text_expansion_summary}

{text_resources_summary}

{paharili_summary}

The `asr` configuration contains human transcripts from VAANI. The
`sravaani_drafts` configuration contains machine-generated hypotheses from
`ARTPARK-IISc/SraVaani-1.0` revision
`f5dd5358325a5208775b91dad98918e079ea2b27`; these are noisy experimental data,
not human ground truth. Targeted rows also retain their local Whisper alternative,
cross-model agreement, and bounded review-confidence evidence. Draft export
status: **{draft_status}**.

All **{report['draft_third_checkpoint_records']:,}** targeted recordings retain
the third-checkpoint hypothesis. For the **{report['draft_three_checkpoint_review_records']:,}**
Garhwali review records, the package also carries a structurally ranked machine
proposal and its evidence limits. These proposals are pending audio review and
are never represented as automatic corrections or human references.
The remaining **{report['draft_audio_grounded_review_records']:,}** structural
outliers also include deterministic re-decoding, waveform activity, and
human-reference calibration evidence. They still require listening review.

The draft layer also preserves **{report['draft_source_label_conflicts']:,}
source-label conflict recordings**. These remain available for auditing but are
explicitly ineligible for Garhwali training.

To keep Dataset Viewer schemas stable across shards, the SraVaani draft
configuration stores nested evidence objects and draft quality-flag arrays as
compact JSON strings. Parse those columns with a JSON parser; their values are
preserved without flattening or omission.

This package uses multiple upstream licenses. Inspect each row's provenance
before redistribution or model release. Full documentation, limitations, and the
release audit are in the [source repository](https://github.com/rushilrawat/Garhwali-Language-Lab).{speech_companion}
'''


def _build_at(output, profile='public', include_audio=False,
              allow_partial_drafts=False, shard_rows=10_000):
    output = prepare_package_output(output)
    direct_eval_record_ids, aggregate_eval_record_ids = upstream_split_overlap_ids()
    overlap_audit = json.loads(
        UPSTREAM_SPLIT_OVERLAP_PATH.read_text(encoding='utf-8')
    )
    report = {
        'release_id': RELEASE_ID,
        'record_schema_version': '1.0.0',
        'profile': profile,
        'include_audio': include_audio,
        'upstream_split_overlap_audit': {
            'schema_version': overlap_audit['schema_version'],
            'sha256': sha256_file(UPSTREAM_SPLIT_OVERLAP_PATH),
            'direct_upstream_eval_record_ids': len(direct_eval_record_ids),
            'community_transcript_overlap_record_ids': len(aggregate_eval_record_ids),
        },
        'configs': {},
        'structured_knowledge_excluded_for_rights': {},
        'structured_knowledge_metadata_only': {},
    }
    if RELEASE_ID.endswith('v0.2.1'):
        report['source_expansion'] = source_expansion_metrics()

    quality_catalog = list(read_jsonl(
        ROOT / 'data/processed/model_ready/quality_v2/text.jsonl'
    ))
    parent_quality = {row['text_sha256']: row for row in quality_catalog}
    text_dir = ROOT / 'data/processed/model_ready/splits/text'
    for split in ('train', 'validation', 'test'):
        rows = read_jsonl(text_dir / f'{split}.jsonl')
        exported_rows = [text_row(row, parent_quality) for row in rows]
        if profile == 'public':
            exported_rows = (
                exported
                for exported in exported_rows
                if exported['language'] == 'gbm'
                and is_public_garhwali_text_row(exported)
            )
        exported_rows = [
            route_upstream_split_overlap(
                row, direct_eval_record_ids, aggregate_eval_record_ids
            )
            for row in exported_rows
        ]
        if split == 'train':
            train_rows = [row for row in exported_rows if row['split'] == 'train']
            overlap_rows = [
                row for row in exported_rows if row['split'] == 'source_overlap'
            ]
            report['text_source_overlap_records'] = len(overlap_rows)
            report['configs']['text/train'] = write_shards(
                train_rows, output / 'data/text', 'train', shard_rows
            )
            if overlap_rows:
                report['configs']['text/source_overlap'] = write_shards(
                    overlap_rows, output / 'data/text', 'source_overlap', shard_rows
                )
        else:
            report['configs'][f'text/{split}'] = write_shards(
                exported_rows, output / 'data/text', split, shard_rows
            )

    existing_text_rows = []
    for path in sorted((output / 'data/text').glob('*.jsonl')):
        existing_text_rows.extend(read_jsonl(path))

    # Deduplicate across text-bearing configs, not only the main text split.
    asr_source_dir = (
        ROOT / 'data/processed/model_ready/splits' / asr_split_directory(profile)
    )
    for split in ('train', 'validation', 'test'):
        asr_rows = list(read_jsonl(asr_source_dir / f'{split}.jsonl'))
        existing_text_rows.extend(comparable_text_rows(asr_rows, 'asr_target_clean'))
    draft_paths = (
        ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_verified.jsonl',
        ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl',
        ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality.jsonl',
        ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani.jsonl',
    )
    draft_source = next(path for path in draft_paths if path.exists())
    existing_text_rows.extend(comparable_text_rows(
        read_jsonl(draft_source), 'machine_transcript'
    ))
    lexicon_path = (
        ROOT / 'data/processed/model_ready/language_resources/pronunciation/lexicon.jsonl'
    )
    existing_text_rows.extend(comparable_text_rows(
        read_jsonl(lexicon_path), 'form'
    ))
    instructions_dir = ROOT / 'data/processed/model_ready/instructions_v0.2'
    for split in ('train', 'validation', 'test'):
        instruction_rows = list(read_jsonl(instructions_dir / f'{split}.jsonl'))
        existing_text_rows.extend(comparable_text_rows(instruction_rows, 'instruction'))
        existing_text_rows.extend(comparable_text_rows(instruction_rows, 'response'))

    refinement_path = ROOT / 'data/processed/model_ready/text_quality_v2/priority_text.jsonl'
    refinements = {
        row['text_sha256']: row for row in read_jsonl(refinement_path)
    } if refinement_path.exists() else {}
    catalog_rows = [
        catalog_row(
            row,
            include_all_text=profile_includes_all_data(profile),
            refinement=refinements.get(row['text_sha256']),
        )
        for row in quality_catalog
    ]
    report['catalog_refined_text_records'] = sum(
        'text_refinement' in row for row in catalog_rows
    )
    report['catalog_records'] = len(catalog_rows)
    report['catalog_redacted_text_records'] = sum(
        row['text'] is None for row in catalog_rows
    )
    report['catalog_rights_cleared_records'] = sum(
        row['redistribution_status'] == 'rights_cleared' for row in catalog_rows
    )
    report['catalog_noncommercial_records'] = sum(
        row['redistribution_status'] == 'rights_cleared_noncommercial_sharealike'
        for row in catalog_rows
    )
    report['catalog_source_policy_records'] = sum(
        row['redistribution_status'] == 'reproduced_under_source_policy'
        for row in catalog_rows
    )
    report['catalog_factual_word_records'] = sum(
        row['redistribution_status'] == 'individual_word_fact'
        for row in catalog_rows
    )
    report['catalog_sharealike_records'] = sum(
        any(
            item.get('license_id') in {'CC-BY-SA-4.0', 'CC-BY-NC-SA-4.0'}
            for item in row.get('public_rights_basis', [])
            + row.get('noncommercial_rights_basis', [])
        )
        for row in catalog_rows
    )
    report['all_collected_text_values_included'] = (
        report['catalog_redacted_text_records'] == 0
    )
    if profile_includes_all_data(profile) and not report['all_collected_text_values_included']:
        raise RuntimeError('All-data profile omitted one or more collected text values')
    report['configs']['catalog/train'] = write_shards(
        catalog_rows, output / 'data/catalog', 'train', shard_rows
    )

    benchmark_eval_dir = (
        ROOT / 'data/processed/evaluation/garhwali_bench_parent_safe_v0.2_2026-09-28'
        / 'v0.2-frozen-candidate'
    )
    benchmark_eval_rows = []
    for split in ('validation', 'test'):
        path = benchmark_eval_dir / f'text_recommended__{split}.jsonl'
        if path.exists():
            benchmark_eval_rows.extend(read_jsonl(path))
    text_expansion_rows, text_expansion_metrics = build_catalog_text_expansion(
        catalog_rows, existing_text_rows, benchmark_eval_rows
    )
    text_expansion_rows = [
        route_upstream_split_overlap(
            row, direct_eval_record_ids, aggregate_eval_record_ids
        )
        for row in text_expansion_rows
    ]
    expansion_overlap_rows = [
        row for row in text_expansion_rows if row['split'] == 'source_overlap'
    ]
    expansion_train_rows = [
        row for row in text_expansion_rows if row['split'] == 'train'
    ]
    text_expansion_metrics['source_split_overlap_records'] = len(
        expansion_overlap_rows
    )
    text_expansion_metrics['train_records'] = len(expansion_train_rows)
    report['text_expansion_metrics'] = text_expansion_metrics
    report['configs']['text_expansion/train'] = write_shards(
        expansion_train_rows, output / 'data/text_expansion', 'train', shard_rows
    )
    if expansion_overlap_rows:
        report['configs']['text_expansion/source_overlap'] = write_shards(
            expansion_overlap_rows, output / 'data/text_expansion',
            'source_overlap', shard_rows
        )
    text_resource_rows, text_resource_metrics = build_catalog_text_resources(
        catalog_rows, [*existing_text_rows, *text_expansion_rows], benchmark_eval_rows
    )
    text_resource_rows = [
        route_upstream_split_overlap(
            row, direct_eval_record_ids, aggregate_eval_record_ids
        )
        for row in text_resource_rows
    ]
    resource_overlap_rows = [
        row for row in text_resource_rows if row['split'] == 'source_overlap'
    ]
    resource_train_rows = [
        row for row in text_resource_rows if row['split'] == 'train'
    ]
    text_resource_metrics['source_split_overlap_records'] = len(
        resource_overlap_rows
    )
    text_resource_metrics['train_records'] = len(resource_train_rows)
    report['text_resource_metrics'] = text_resource_metrics
    report['configs']['text_resources/train'] = write_shards(
        resource_train_rows, output / 'data/text_resources', 'train', shard_rows
    )
    if resource_overlap_rows:
        report['configs']['text_resources/source_overlap'] = write_shards(
            resource_overlap_rows, output / 'data/text_resources',
            'source_overlap', shard_rows
        )

    if not PAHARILI_GBM_ROWS_PATH.is_file():
        raise FileNotFoundError(
            f'Missing prepared PahariLI Garhwali rows: {PAHARILI_GBM_ROWS_PATH}'
        )
    paharili_existing_rows = [
        *existing_text_rows, *text_expansion_rows, *text_resource_rows,
    ]
    paharili_rows, paharili_metrics = build_paharili_gbm_rows(
        read_jsonl(PAHARILI_GBM_ROWS_PATH), paharili_existing_rows
    )
    report['paharili_gbm_metrics'] = paharili_metrics
    for split in ('train', 'test', 'source_overlap'):
        split_rows = [row for row in paharili_rows if row['split'] == split]
        if split_rows:
            report['configs'][f'paharili_gbm/{split}'] = write_shards(
                split_rows, output / 'data/paharili_gbm', split, shard_rows
            )

    for family, path in KNOWLEDGE_CONFIGS.items():
        if not path.exists():
            raise FileNotFoundError(f'Missing structured knowledge catalog: {path}')
        source_catalog = source_catalog_for_family(family)
        rows = [
            knowledge_row(row, family, source_catalog)
            for row in read_jsonl(path)
        ]
        ids = [row['id'] for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f'Duplicate stable IDs in {family}')
        if profile == 'public':
            report['structured_knowledge_excluded_for_rights'][family] = 0
            report['structured_knowledge_metadata_only'][family] = len(rows)
            rows = [public_factual_metadata_row(row, family) for row in rows]
        report['configs'][f'{family}/train'] = write_shards(
            rows, output / f'data/{family}', 'train', shard_rows
        )

    audio_sources = []
    asr_dir = ROOT / 'data/processed/model_ready/splits' / asr_split_directory(profile)
    for split in ('train', 'validation', 'test'):
        rows = list(read_jsonl(asr_dir / f'{split}.jsonl'))
        audio_sources.extend(rows)
        report['configs'][f'asr/{split}'] = write_shards(
            (audio_row(row, 'asr_target_clean', include_audio) for row in rows),
            output / 'data/asr', split, shard_rows,
        )

    queue_path = ROOT / 'data/processed/model_ready/transcripts/untranscribed_queue.jsonl'
    confidence_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl'
    verified_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_verified.jsonl'
    quality_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality.jsonl'
    raw_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani.jsonl'
    drafts_path = next(
        path for path in (
            verified_drafts_path, confidence_drafts_path,
            quality_drafts_path, raw_drafts_path
        ) if path.exists()
    )
    queue = list(read_jsonl(queue_path))
    queue_count = len(queue)
    drafts = list(read_jsonl(drafts_path))
    unique_drafts = list(deduplicate_audio_rows(drafts, 'machine_transcript'))
    third_checkpoint_path = (
        ROOT / 'data/processed/model_ready/transcripts/'
        'sravaani_recovery_whisper_v0.1.jsonl'
    )
    third_checkpoint_rows = list(read_jsonl(third_checkpoint_path)) \
        if third_checkpoint_path.exists() else []
    unique_drafts = attach_recovery_third_checkpoint(
        unique_drafts, third_checkpoint_rows
    )
    adjudication_path = (
        ROOT / 'data/processed/model_ready/transcripts/'
        'sravaani_recovery_adjudication.jsonl'
    )
    adjudication_rows = list(read_jsonl(adjudication_path)) \
        if adjudication_path.exists() else []
    unique_drafts = attach_recovery_adjudication(unique_drafts, adjudication_rows)
    audio_review_path = (
        ROOT / 'data/processed/model_ready/transcripts/'
        'sravaani_recovery_audio_grounded_review.jsonl'
    )
    audio_review_rows = list(read_jsonl(audio_review_path)) \
        if audio_review_path.exists() else []
    unique_drafts = attach_audio_grounded_review(unique_drafts, audio_review_rows)
    report['draft_queue_records'] = queue_count
    report['draft_source'] = str(drafts_path.relative_to(ROOT))
    report['draft_records'] = len(drafts)
    report['draft_unique_audio'] = len(unique_drafts)
    report['draft_unique_nonempty_audio'] = sum(
        bool(str(row.get('machine_transcript') or '').strip())
        for row in unique_drafts
    )
    report['draft_empty_audio'] = (
        report['draft_unique_audio'] - report['draft_unique_nonempty_audio']
    )
    report['draft_source_label_conflicts'] = sum(
        row.get('language_scope_status') == 'source_label_conflict'
        for row in unique_drafts
    )
    report['draft_three_checkpoint_review_records'] = sum(
        bool(row.get('recovery_adjudication')) for row in unique_drafts
    )
    report['draft_third_checkpoint_records'] = sum(
        bool(row.get('recovery_third_checkpoint')) for row in unique_drafts
    )
    report['draft_audio_grounded_review_records'] = sum(
        bool(row.get('audio_grounded_review')) for row in unique_drafts
    )
    report['draft_inherited_duplicate_rows'] = len(drafts) - len(unique_drafts)
    report['drafts_complete'] = drafts_cover_queue(queue, drafts)
    if not report['drafts_complete'] and not allow_partial_drafts:
        raise RuntimeError(
            f'SraVaani drafts incomplete: {len(drafts)}/{queue_count}; '
            'use --allow-partial-drafts only for a preview'
        )
    audio_sources.extend(unique_drafts)
    report['configs']['sravaani_drafts/train'] = write_shards(
        (audio_row(row, 'machine_transcript', include_audio,
                   serialize_evidence=True) for row in unique_drafts),
        output / 'data/sravaani_drafts', 'train', shard_rows,
    )

    lexicon = read_jsonl(
        ROOT / 'data/processed/model_ready/language_resources/pronunciation/lexicon.jsonl'
    )
    if profile == 'public':
        lexicon = (row for row in lexicon if is_public_text_row(row))
    report['configs']['lexicon/train'] = write_shards(
        (lexicon_row(row) for row in lexicon),
        output / 'data/lexicon', 'train', shard_rows,
    )

    instructions_dir = ROOT / 'data/processed/model_ready/instructions_v0.2'
    for split in ('train', 'validation', 'test'):
        rows = list(read_jsonl(instructions_dir / f'{split}.jsonl'))
        if profile == 'public':
            rows = [row for row in rows if is_public_text_row(row)]
        rows = refresh_acceptable_responses(rows)
        report['configs'][f'instructions/{split}'] = write_shards(
            (with_public_rights_basis(row) for row in rows),
            output / 'data/instructions', split, shard_rows,
        )

    removed_audio_files = 0 if include_audio else remove_packaged_audio(output)
    link_report = link_audio(audio_sources, output) if include_audio else {'new': 0, 'total': 0}
    report['linked_audio_files'] = link_report['total']
    report['newly_linked_audio_files'] = link_report['new']
    report['removed_audio_files'] = removed_audio_files
    output.mkdir(parents=True, exist_ok=True)
    dataset_info = dataset_info_for_release(output, report['configs'])
    (output / 'README.md').write_text(
        dataset_card(report, dataset_info=dataset_info), encoding='utf-8'
    )
    for name in ('LICENSE_POLICY.md', 'ATTRIBUTION.md', 'REMOVAL_POLICY.md'):
        shutil.copy2(ROOT / name, output / name)
    for name in ('DEVELOPER_QUICKSTART.md', 'DATASET_SCHEMA.md'):
        shutil.copy2(ROOT / 'docs' / name, output / name)
    if not PAHARILI_LICENSE_PATH.is_file():
        raise FileNotFoundError(
            f'Missing PahariLI repository license: {PAHARILI_LICENSE_PATH}'
        )
    paharili_license_target = output / 'licenses' / 'PahariLI-Apache-2.0.txt'
    paharili_license_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PAHARILI_LICENSE_PATH, paharili_license_target)
    shutil.copy2(
        ROOT / 'examples' / 'search_garhwali_lexicon.py',
        output / 'search_garhwali_lexicon.py',
    )
    rights_report = ROOT / 'research/text-rights-resolution-2026-09-30.md'
    rights_report_target = output / 'research' / rights_report.name
    rights_report_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rights_report, rights_report_target)
    for name in (
        'huggingface-upstream-split-overlap-2026-10-05.md',
        'huggingface-upstream-split-overlap-2026-10-05.json',
    ):
        shutil.copy2(ROOT / 'research' / name, output / 'research' / name)
    (output / 'manifest.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    report['manifest_sha256'] = sha256_file(output / 'manifest.json')
    return report


def build(output, profile='public', include_audio=False, allow_partial_drafts=False,
          shard_rows=10_000):
    """Build in a sibling staging directory, then replace the managed package."""
    output = Path(output)
    if output.exists() and output.resolve() not in MANAGED_OUTPUTS:
        raise ValueError(
            'refusing to replace an existing custom output directory; use a new '
            'path or one of the managed Hugging Face package paths'
        )
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError(f'package output must be a regular directory: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(
        dir=output.parent, prefix=f'.{output.name}.building-'
    ))
    staging.rmdir()
    backup = Path(tempfile.mkdtemp(
        dir=output.parent, prefix=f'.{output.name}.previous-'
    ))
    backup.rmdir()
    try:
        report = _build_at(
            staging, profile=profile, include_audio=include_audio,
            allow_partial_drafts=allow_partial_drafts, shard_rows=shard_rows,
        )
        if output.exists():
            output.rename(backup)
        staging.rename(output)
        if backup.exists():
            shutil.rmtree(backup)
        return report
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if backup.exists() and not output.exists():
            backup.rename(output)
        elif backup.exists():
            shutil.rmtree(backup)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    parser.add_argument(
        '--profile', choices=('public', 'all-data'),
        default='public',
    )
    parser.add_argument('--include-audio', action='store_true')
    parser.add_argument('--allow-partial-drafts', action='store_true')
    parser.add_argument('--shard-rows', type=int, default=10_000)
    args = parser.parse_args()
    output = args.output or (
        ALL_DATA_OUTPUT if profile_includes_all_data(args.profile) else DEFAULT_OUTPUT
    )
    print(json.dumps(build(
        output,
        profile=args.profile,
        include_audio=args.include_audio,
        allow_partial_drafts=args.allow_partial_drafts,
        shard_rows=args.shard_rows,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
