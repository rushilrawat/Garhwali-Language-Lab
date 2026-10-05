#!/usr/bin/env python3
"""Build a reversible page/section-cue index for two local Archive books."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = Path(
    "data/extracted/research/internet_archive_candidate_views_2026-10-04/"
    "text_review_candidates.jsonl"
)
OUTPUT_PATH = Path(
    "data/extracted/research/archive_chatak_shailesh_page_section_map_2026-10-04.jsonl"
)
SOURCES = {
    "ia_govind_chatak_gadwali_lok_gathayen_1958": Path(
        "data/downloads/folklore/internet_archive/"
        "gadwali_lok_gathayen_1958/source_djvu.xml"
    ),
    "ia_haridatta_bhatta_garhwali_bhasha_sahitya_1976": Path(
        "data/downloads/linguistics/internet_archive/"
        "garhwali_bhasha_sahitya_1976/source_djvu.xml"
    ),
}
SECTION_CUES = {
    "contents": re.compile(
        r"contents|index|अनुक्रमणिका|विषय\s*सूची|विषयसूची", re.IGNORECASE
    ),
    "section": re.compile(
        r"अध्याय|खंड|भाग|प्रस्तावना|भूमिका|परिशिष्ट|chapter|appendix", re.IGNORECASE
    ),
    "chatak_genre_terms": re.compile(
        r"जागर|चैती|पवाड़ा|पंवाड़ा|पवारा|प्रणय|jā?gar|chaitī|pawā?ṛā|praṇaya",
        re.IGNORECASE,
    ),
}
STRUCTURAL_START = re.compile(
    r"^\s*(?:अध्याय|खंड|भाग|प्रस्तावना|भूमिका|परिशिष्ट|chapter|appendix)"
    r"(?:\s|[0-9.:।-]|$)",
    re.IGNORECASE,
)
CONTENTS_START = re.compile(
    r"^\s*(?:contents|index|अनुक्रमणिका|विषय\s*सूची|विषयसूची)",
    re.IGNORECASE,
)
TERMINAL_PROSE = re.compile(r"[।.!?,;:—–\-\"'’”)]$", re.UNICODE)

# Manually transcribed from Shailesh's scanned contents page (physical scan
# page 13). The physical-to-printed offset is independently checked against
# printed pages 13, 14, and 426 in the scan. Titles are navigational metadata;
# they do not label the language on any page or determine reuse rights.
SHAILESH_SOURCE_ID = "ia_haridatta_bhatta_garhwali_bhasha_sahitya_1976"
SHAILESH_PHYSICAL_PAGE_OFFSET = 13
SHAILESH_CONTENTS_PAGE = 13
SHAILESH_TOC_RANGES = [
    ("preface", "Preface", 9, 14),
    ("language_development", "Development of Garhwali", 15, 31),
    ("grammar", "Garhwali grammar", 32, 51),
    ("word_sources", "Word sources and meanings", 52, 62),
    ("published_literature", "Published Garhwali literature", 65, 140),
    ("folk_songs", "Garhwali folk songs", 141, 179),
    ("folk_epics", "Garhwali folk epics", 180, 309),
    ("folk_tales", "Garhwali folk tales", 310, 357),
    ("proverbs", "Garhwali proverbs", 358, 366),
    ("riddles", "Garhwali riddles", 367, 368),
    ("vocabulary_appendix", "Appendix: Garhwali words", 369, 403),
    ("grierson_classification", "Appendix: Grierson language classification", 404, 405),
    ("language_classification", "Appendix: language classification", 406, 408),
    ("bibliography", "Bibliography", 409, 411),
    ("word_index", "Word index", 412, 426),
]


def _section_assignment(source_id: str, pdf_page: int, contents_page: bool) -> dict:
    """Return only evidence-supported navigation metadata for one scan page."""
    empty = {
        "section_assignment": "unreviewed_candidate_map",
        "section_id": None,
        "section_title": None,
        "printed_page_number": None,
        "section_printed_page_range": None,
        "physical_page_offset": None,
        "section_assignment_evidence": None,
    }
    if source_id != SHAILESH_SOURCE_ID:
        return empty
    if contents_page or pdf_page == SHAILESH_CONTENTS_PAGE:
        return {
            **empty,
            "section_assignment": "contents_page",
            "section_assignment_evidence": "visually_checked_contents_page",
        }
    if pdf_page <= 21:
        return {
            **empty,
            "section_assignment": "preliminary_matter_unassigned",
            "physical_page_offset": SHAILESH_PHYSICAL_PAGE_OFFSET,
            "section_assignment_evidence": "physical_scan_position_only",
        }
    if pdf_page <= 439:
        printed_page = pdf_page - SHAILESH_PHYSICAL_PAGE_OFFSET
        for section_id, section_title, start_page, end_page in SHAILESH_TOC_RANGES:
            if start_page <= printed_page <= end_page:
                return {
                    "section_assignment": "toc_derived",
                    "section_id": section_id,
                    "section_title": section_title,
                    "printed_page_number": printed_page,
                    "section_printed_page_range": [start_page, end_page],
                    "physical_page_offset": SHAILESH_PHYSICAL_PAGE_OFFSET,
                    "section_assignment_evidence": "visually_checked_contents_and_page_number_offset",
                }
        return {
            **empty,
            "section_assignment": "unmapped_toc_gap",
            "printed_page_number": printed_page,
            "physical_page_offset": SHAILESH_PHYSICAL_PAGE_OFFSET,
            "section_assignment_evidence": "visually_checked_contents_and_page_number_offset",
        }
    return {
        **empty,
        "section_assignment": "unnumbered_suffix_unassigned",
        "physical_page_offset": SHAILESH_PHYSICAL_PAGE_OFFSET,
        "section_assignment_evidence": "physical_scan_position_only",
    }


def _read_candidate_rows(path: Path) -> dict[tuple[str, int], dict]:
    rows: dict[tuple[str, int], dict] = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            source_id = row.get("source_id")
            if source_id not in SOURCES:
                continue
            key = (source_id, int(row["pdf_page"]))
            if key in rows:
                raise ValueError(f"Duplicate candidate page key: {key}")
            rows[key] = row
    return rows


def _line_text(line: ET.Element) -> str:
    words = [
        "".join(word.itertext()).strip()
        for word in line.findall(".//WORD")
    ]
    return " ".join(word for word in words if word).strip()


def _contents_page_refs(lines: list[dict]) -> list[dict]:
    refs = []
    for line in lines:
        normalized_digits = "".join(
            str(unicodedata.digit(char)) if char.isdigit() else char
            for char in line["text"]
        )
        match = re.search(r"(?<!\d)(\d{1,3})\s*$", normalized_digits)
        if match:
            refs.append({
                "line_number": line["line_number"],
                "printed_page_number": int(match.group(1)),
                "title_candidate": normalized_digits[:match.start()].strip()[:180],
            })
    return refs


def _page_map(source_id: str, xml_path: Path, candidates: dict) -> tuple[list[dict], dict]:
    root = ET.parse(xml_path).getroot()
    page_maps = []
    cue_page_counts: Counter[str] = Counter()
    candidate_heading_pages = 0
    aligned_candidates = 0

    for page_number, obj in enumerate(root.findall(".//OBJECT"), start=1):
        page_lines = []
        page_cues: set[str] = set()
        low_confidence_tokens = 0
        confidence_values = []
        for line_number, line in enumerate(obj.findall(".//LINE"), start=1):
            text = _line_text(line)
            if not text:
                continue
            words = line.findall(".//WORD")
            for word in words:
                try:
                    confidence = float(word.attrib["x-confidence"])
                except (KeyError, ValueError):
                    continue
                confidence_values.append(confidence)
                low_confidence_tokens += confidence < 70

            cue_types = [name for name, cue in SECTION_CUES.items() if cue.search(text)]
            layout_class = line.attrib.get("x-struct")
            title_like_layout = (
                layout_class == "header" and len(text) <= 45 and len(text.split()) <= 6
            )
            short_standalone = (
                len(text) <= 90
                and len(text.split()) <= 12
                and not TERMINAL_PROSE.search(text)
                and (
                    bool(STRUCTURAL_START.search(text))
                    or bool(CONTENTS_START.search(text))
                    or title_like_layout
                )
            )
            page_lines.append({
                "line_number": line_number,
                "layout_class": layout_class,
                "cue_types": cue_types,
                "heading_candidate": short_standalone,
                "text": text,
            })
            page_cues.update(cue_types)

        cue_page_counts.update(page_cues)

        candidate = candidates.get((source_id, page_number))
        if candidate:
            aligned_candidates += 1
        heading_lines = [line for line in page_lines if line["heading_candidate"]]
        candidate_heading_pages += bool(heading_lines)
        contents_lines = [
            {"line_number": line["line_number"], "text": line["text"][:300]}
            for line in page_lines
        ] if "contents" in page_cues else []
        assignment = _section_assignment(
            source_id, page_number, bool(contents_lines)
        )
        page_maps.append({
            "source_id": source_id,
            "archive_identifier": candidate.get("archive_identifier") if candidate else None,
            "source_url": candidate.get("source_url") if candidate else None,
            "pdf_page": page_number,
            "candidate_record_id": candidate.get("record_id") if candidate else None,
            "candidate_text_sha256": candidate.get("text_sha256") if candidate else None,
            "candidate_normalized_characters": len(str(
                candidate.get("text_normalized") or ""
            )) if candidate else 0,
            "candidate_script_profile": candidate.get("automated_page_triage", {}).get(
                "script_profile"
            ) if candidate else None,
            "candidate_ocr_warning_flags": candidate.get("automated_page_triage", {}).get(
                "warning_flags", []
            ) if candidate else [],
            "ocr_line_count": len(page_lines),
            "ocr_token_count": sum(len(line.findall(".//WORD")) for line in obj.findall(".//LINE")),
            "ocr_tokens_under_confidence_70": low_confidence_tokens,
            "ocr_mean_word_confidence": round(sum(confidence_values) / len(confidence_values), 2)
            if confidence_values else None,
            "ocr_empty": not page_lines,
            "section_cue_types": sorted({cue for line in page_lines for cue in line["cue_types"]}),
            "contents_page_detected": bool(contents_lines),
            "contents_page_lines": contents_lines,
            "contents_page_refs": _contents_page_refs(contents_lines),
            "heading_candidates": [
                {
                    "line_number": line["line_number"],
                    "layout_class": line["layout_class"],
                    "cue_types": line["cue_types"],
                    "text": line["text"][:180],
                }
                for line in heading_lines
            ],
            **assignment,
            "rights_status": candidate.get("rights_status") if candidate else None,
            "training_eligible": bool(candidate and candidate.get("training_eligible")),
            "public_redistribution_eligible": bool(
                candidate and candidate.get("public_redistribution_eligible")
            ),
        })

    assignment_counts = Counter(row["section_assignment"] for row in page_maps)
    section_page_counts = Counter(
        row["section_id"] for row in page_maps if row["section_id"]
    )
    summary = {
        "xml_pages": len(page_maps),
        "candidate_rows_aligned": aligned_candidates,
        "candidate_rows_unmatched": sum(1 for key in candidates if key[0] == source_id) - aligned_candidates,
        "empty_ocr_pages": sum(row["ocr_empty"] for row in page_maps),
        "pages_with_heading_candidates": candidate_heading_pages,
        "contents_pages": [row["pdf_page"] for row in page_maps if row["contents_page_detected"]],
        "contents_page_reference_count": sum(len(row["contents_page_refs"]) for row in page_maps),
        "section_assignment_counts": dict(assignment_counts),
        "toc_section_page_counts": dict(section_page_counts),
        "toc_section_ranges": [
            {
                "section_id": section_id,
                "section_title": title,
                "printed_page_range": [start_page, end_page],
                "physical_scan_page_range": [
                    start_page + SHAILESH_PHYSICAL_PAGE_OFFSET,
                    end_page + SHAILESH_PHYSICAL_PAGE_OFFSET,
                ],
            }
            for section_id, title, start_page, end_page in SHAILESH_TOC_RANGES
        ] if source_id == SHAILESH_SOURCE_ID else [],
        "section_cue_page_counts": dict(cue_page_counts),
    }
    return page_maps, summary


def build_page_maps(root: Path, candidate_path: Path, output_path: Path) -> dict:
    candidates = _read_candidate_rows(root / candidate_path)
    summaries = {}
    all_pages = []
    for source_id, relative_xml in SOURCES.items():
        pages, summary = _page_map(source_id, root / relative_xml, candidates)
        all_pages.extend(pages)
        summaries[source_id] = summary

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        for row in all_pages:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"page_objects": len(all_pages), "sources": summaries, "output": str(output_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    summary = build_page_maps(args.root, args.input, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
