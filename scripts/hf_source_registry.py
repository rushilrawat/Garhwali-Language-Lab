"""Verified public locator URLs for source identifiers used in HF exports."""

import json
from functools import lru_cache
from pathlib import Path

SOURCE_URLS = {
    "asjp": "https://asjp.clld.org/contributors/VS",
    "atkinson_himalayan_gazetteer": "https://openlibrary.org/books/OL44548030M/The_Him%C3%A1layan_districts_of_the_North-Western_Provinces_of_India",
    "dhyani_occupations": "https://sites.google.com/view/dhyani/%E0%A4%B0%E0%A4%AE%E0%A4%95%E0%A4%A4-%E0%A4%AC%E0%A4%9C%E0%A4%B5%E0%A4%B2/%E0%A4%97%E0%A4%A2%E0%A4%B5%E0%A4%B2-%E0%A4%AE-%E0%A4%B2%E0%A4%95-%E0%A4%B5%E0%A4%AF%E0%A4%B5%E0%A4%B8%E0%A4%AF-%E0%A4%B8%E0%A4%AE%E0%A4%AC%E0%A4%A8%E0%A4%A7-%E0%A4%B6%E0%A4%AC%E0%A4%A6%E0%A4%B5%E0%A4%B2",
    "emagazine_animals": "https://e-magazineofuttarakhand.blogspot.com/2012/02/names-of-animals-birds-etc-in-garhwali.html",
    "garhwalilanguage_dictionary": "https://www.garhwalilanguage.com/en/garhwali-dictionary",
    "itihaas-garhwali-capture": "https://www.itihaas.ai/en/languages/garhwali-language",
    "mountainvoices_local_glossary": "https://mountainvoices.org/intro.html",
    "pib_ramman_instruments": "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/sep/doc2025929651301.pdf",
    "user-literature-writers-2026-09-16": "https://github.com/rushilrawat/Garhwali-Language-Lab/blob/main/sources/manual/garhwali-literature-writers-2026-09-16.md",
    "uttarakhandiwords_animals": "https://uttarakhandiwords.blogspot.com/2011/09/blog-post.html",
    "wiktionary_swadesh_thematic": "https://en.wiktionary.org/wiki/Appendix:Garhwali_Swadesh_list",
}

SOCIAL_RECORDS_RELATIVE_PATH = "data/extracted/social_garhwali/records.jsonl"


@lru_cache(maxsize=1)
def social_record_locators() -> dict[tuple[str, int], dict[str, str]]:
    """Index explicit URLs from the known social seed file by ID and line."""
    path = Path(__file__).resolve().parents[1] / SOCIAL_RECORDS_RELATIVE_PATH
    if not path.is_file():
        return {}
    result = {}
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            record_id = str(row.get("id") or "")
            source_url = row.get("url")
            if (record_id and isinstance(source_url, str)
                    and source_url.startswith(("https://", "http://"))):
                result[(record_id, line_number)] = {
                    "source_url": source_url,
                    **({"source_title": str(row["title"])} if row.get("title") else {}),
                    **({"source_kind": f"social_media_{row['platform']}"}
                       if row.get("platform") else {}),
                }
    return result


def source_record_locator(item: dict,
                          locators: dict[tuple[str, int], dict[str, str]] | None = None
                          ) -> dict[str, str]:
    """Resolve verified social seed IDs, optionally checked against file and line."""
    normalized_path = str(item.get("file") or "").replace("\\", "/")
    if normalized_path and normalized_path != SOCIAL_RECORDS_RELATIVE_PATH:
        return {}
    record_id = str(item.get("record_id") or "")
    if not record_id.startswith("social-garhwali:"):
        return {}
    locators = social_record_locators() if locators is None else locators
    if item.get("line") is not None:
        try:
            line_number = int(item["line"])
        except (TypeError, ValueError):
            return {}
        if line_number < 1:
            return {}
        return dict(locators.get((record_id, line_number), {}))
    matches = [value for (candidate_id, _), value in locators.items()
               if candidate_id == record_id]
    return dict(matches[0]) if len(matches) == 1 else {}
