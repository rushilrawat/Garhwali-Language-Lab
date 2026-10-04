#!/usr/bin/env python3
"""Index Garhwal-specific OCR pages from newly acquired regional history books."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from ingest_archive_dabral_references import ROOT, existing_text_hashes, source_pages


OUTPUT = ROOT / "data/extracted/research/internet_archive_reference_books_2026-10-03"
DEVANAGARI_GARHWAL = re.compile(
    r"गढ़वाल|गढवाल|गढ़वाली|गढवाली|गढ़वालि|गढ़वाळ|गढ़राज्य|गढ़पति|"
    r"अलकनन्दा|अलकनंदा|टिहरी|चमोली|पौड़ी|देहरादून|केदारनाथ|बदरीनाथ|Garhwal|Garhwali",
    re.IGNORECASE,
)
SOURCES = [
    {
        "source_id": "ia_krishna_kumar_garhwal_ancient_inscriptions",
        "archive_id": "cVko_garhwal-ke-pracheen-abhilekha-aur-unka-itihasika-mahatva-by-krishna-kumar-haridwar-mayank-praka",
        "directory": "data/downloads/history/internet_archive/garhwal_ancient_inscriptions_krishna_kumar",
        "title": "Garhwal Ke Pracheen Abhilekha Aur Unka Itihasika Mahatva",
        "author": "Krishna Kumar (Archive title attribution; details not independently verified)",
        "year_claim": None,
        "genre": "regional_epigraphy_and_history_reference",
        "language": "Hindi OCR; regional history reference, not verified Garhwali text",
        "rights_status": "unverified_uploader_license_claim",
        "reuse_scope": "local_research_reference_pending_rights_and_content_review",
        "terms": DEVANAGARI_GARHWAL,
    },
    {
        "source_id": "ia_mahidhar_sharma_barthwal_garhwal_me_kon_kahan_se_1938",
        "archive_id": "garhwal-me-kon-kahan-se_20250415",
        "directory": "data/downloads/history/internet_archive/garhwal_me_kon_kahan_se_1938",
        "title": "Garhwal Me Kon Kahan Se",
        "author": "Mahidhar Sharma Barthwal (Archive metadata attribution)",
        "year_claim": 1938,
        "genre": "regional_history_and_place_reference",
        "language": "Hindi OCR; regional history reference, not verified Garhwali text",
        "rights_status": "unverified_archive_public_domain_mark_claim",
        "reuse_scope": "local_research_reference_pending_rights_and_content_review",
        "terms": DEVANAGARI_GARHWAL,
    },
    {
        "source_id": "ia_rahul_sankrityayan_himalaya_parichay_garhwal_1953",
        "archive_id": "pawc_himalaya-parichay-1-garhwal-by-rahul-sankrityayan-hindi-himalayan-studies-allaha",
        "directory": "data/downloads/geography/internet_archive/himalaya_parichay_garhwal_vol1_1953",
        "title": "Himalaya Parichay, Vol. 1: Garhwal",
        "author": "Rahul Sankrityayan (Archive title attribution)",
        "year_claim": 1953,
        "genre": "regional_geography_and_cultural_history_reference",
        "language": "Hindi OCR; regional history reference, not verified Garhwali text",
        "rights_status": "unverified_uploader_license_claim",
        "reuse_scope": "local_research_reference_pending_rights_and_content_review",
        "terms": DEVANAGARI_GARHWAL,
    },
    {
        "source_id": "ia_note_on_bhotias_almora_british_garhwal_1905",
        "archive_id": "dli.pahar.1694",
        "directory": "data/downloads/history/internet_archive/bhotias_almora_british_garhwal_1905",
        "title": "Note On The Bhotias Of Almora And British Garhwal",
        "author": "Not identified in the Archive metadata reviewed",
        "year_claim": 1905,
        "genre": "historical_ethnographic_reference",
        "language": "English OCR; regional ethnographic reference, not Garhwali text",
        "rights_status": "archive_license_recorded_cc_by_nc_4_0",
        "reuse_scope": "local_noncommercial_research_reference_pending_license_compatibility_review",
        "terms": re.compile(r"Garhwal|Garhwali|Bhotia|Bhotiyas|Bhotiya|Almora", re.IGNORECASE),
    },
    {
        "source_id": "ia_rai_pati_ram_bahadur_garhwal_ancient_modern_1916",
        "archive_id": "in.ernet.dli.2015.43255",
        "directory": "data/downloads/history/garhwal_ancient_and_modern_1916/internet_archive",
        "title": "Garhwal Ancient and Modern",
        "author": "Rai Pati Ram Bahadur (Archive/DLI attribution)",
        "year_claim": 1916,
        "genre": "regional_history_reference",
        "language": "English OCR; regional history reference, not Garhwali text",
        "rights_status": "no_explicit_reuse_license_recorded",
        "reuse_scope": "local_research_reference_pending_rights_and_content_review",
        "terms": re.compile(r"Garhwal|Garhwali|Tehri|Srinagar|Pauri|Chamoli|Kedarnath|Badrinath", re.IGNORECASE),
    },
    {
        "source_id": "ia_babicz_peaks_passes_garhwal_1990",
        "archive_id": "dli.pahar.3635",
        "directory": "data/downloads/geography/peaks_and_passes_garhwal_1990/internet_archive",
        "title": "Peaks and Passes of Garhwal Himalaya",
        "author": "Babicz (Archive metadata attribution)",
        "year_claim": 1990,
        "genre": "regional_geography_reference",
        "language": "English OCR; regional geography reference, not Garhwali text",
        "rights_status": "unverified_uploader_cc_by_nc_4_0_claim",
        "reuse_scope": "local_research_reference_pending_rights_and_content_review",
        "terms": re.compile(r"Garhwal|Garhwali|Tehri|Srinagar|Pauri|Chamoli|Kedarnath|Badrinath", re.IGNORECASE),
    },
    {
        "source_id": "ia_tehri_garhwal_district_gazetteer_1971",
        "archive_id": "dli.ministry.08781",
        "directory": "data/downloads/geography/tehri_garhwal_district_gazetteer_1971/internet_archive",
        "title": "Uttar Pradesh District Gazetteers: Tehri Garhwal",
        "author": "Government gazetteer committee (Archive metadata attribution)",
        "year_claim": 1971,
        "genre": "district_gazetteer_reference",
        "language": "English OCR; district gazetteer, not Garhwali text",
        "rights_status": "no_explicit_reuse_license_recorded",
        "reuse_scope": "local_research_reference_pending_rights_and_content_review",
        "terms": re.compile(r"Garhwal|Garhwali|Tehri|Bhagirathi|Bhilangana|Srinagar|Pauri|Chamoli", re.IGNORECASE),
    },
    {
        "source_id": "ia_strachey_duthie_garhwal_flora_catalogue_1906",
        "archive_id": "catalogueplants00duthgoog",
        "directory": "data/downloads/geography/catalogue_plants_kumaon_garhwal_tibet_1906/internet_archive",
        "title": "Catalogue of the Plants of Kumaon and of the Adjacent Portions of Garhwal and Tibet",
        "author": "Richard Strachey and John Firminger Duthie (Archive attribution)",
        "year_claim": 1906,
        "genre": "regional_ethnobotany_reference",
        "language": "English OCR; botanical reference, vernacular Garhwali labels not confirmed",
        "rights_status": "no_explicit_reuse_license_recorded",
        "reuse_scope": "local_research_reference_pending_rights_and_content_review",
        "terms": re.compile(r"Garhwal|Garhwali|Kumaon|Kumaun|Tibet|Tehri", re.IGNORECASE),
    },
    {
        "source_id": "ia_dharmanand_joshi_notes_garhwal_district_1910",
        "archive_id": "dli.ministry.29693",
        "directory": "data/downloads/history/notes_on_garhwal_district_1910/internet_archive",
        "title": "Notes on the Garhwal District",
        "author": "Dharmanand Joshi (Archive metadata attribution)",
        "year_claim": 1910,
        "genre": "regional_history_and_administration_reference",
        "language": "English OCR; regional reference, not Garhwali text",
        "rights_status": "no_explicit_reuse_license_recorded",
        "reuse_scope": "local_research_reference_pending_rights_and_content_review",
        "terms": re.compile(r"Garhwal|Garhwali|Tehri|Srinagar|Pauri|Chamoli|Kedarnath|Badrinath", re.IGNORECASE),
    },
]


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    output_paths = {OUTPUT / f"{source['source_id']}.jsonl" for source in SOURCES}
    extracted = []
    for source in SOURCES:
        rows, report = source_pages(source)
        output = OUTPUT / f"{source['source_id']}.jsonl"
        extracted.append((source, rows, report, output))

    prior_hashes = existing_text_hashes({path.resolve() for path in output_paths})
    all_hashes = Counter(row["text_sha256"] for _, rows, _, _ in extracted for row in rows)
    for source, rows, report, output in extracted:
        for row in rows:
            flags = set(row["quality_flags"])
            if all_hashes[row["text_sha256"]] > 1:
                flags.add("exact_duplicate_within_intake")
            if row["text_sha256"] in prior_hashes:
                flags.add("exact_duplicate_in_existing_project_data")
            row["quality_flags"] = sorted(flags)
        output.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
        report["exact_page_overlaps_with_existing_project"] = sum(
            row["text_sha256"] in prior_hashes for row in rows
        )
        report["exact_unique_pages_new_to_existing_project"] = len(
            {row["text_sha256"] for row in rows if row["text_sha256"] not in prior_hashes}
        )
        report["output_jsonl"] = str(output.relative_to(ROOT))

    all_rows = [row for _, rows, _, _ in extracted for row in rows]
    manifest = {
        "retrieved_date": "2026-10-04",
        "selection_rule": "Index only OCR pages with an explicit Garhwal/Garhwali spelling, a named Garhwal place, or the Bhotia/Almora terms in the identified regional reference. English and Hindi pages remain contextual reference material, not Garhwali-language training data.",
        "all_records_training_eligible": False,
        "all_records_public_redistribution_eligible": False,
        "records": len(all_rows),
        "exact_unique_page_texts": len({row["text_sha256"] for row in all_rows}),
        "exact_duplicate_rows_within_intake": len(all_rows) - len(all_hashes),
        "exact_page_text_overlaps_with_existing_project": sum(row["text_sha256"] in prior_hashes for row in all_rows),
        "sources": [report for _, _, report, _ in extracted],
    }
    manifest_path = OUTPUT / "ia_additional_historical_reference_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
