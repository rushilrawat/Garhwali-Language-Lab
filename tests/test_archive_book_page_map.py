import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from build_archive_book_page_map import (
    SHAILESH_SOURCE_ID,
    SHAILESH_TOC_RANGES,
    _contents_page_refs,
    _page_map,
    _section_assignment,
)


class ArchiveBookPageMapTests(unittest.TestCase):
    def _write_djvu(self, directory: Path) -> Path:
        root = ET.Element("DjVuXML")
        body = ET.SubElement(root, "BODY")
        obj = ET.SubElement(body, "OBJECT")
        hidden = ET.SubElement(obj, "HIDDENTEXT")
        column = ET.SubElement(hidden, "PAGECOLUMN")
        region = ET.SubElement(column, "REGION")
        paragraph = ET.SubElement(region, "PARAGRAPH")
        for value, confidence in (("प्रणय", "90"), ("गाथा", "85")):
            line = ET.SubElement(paragraph, "LINE", {"x-struct": "header"})
            ET.SubElement(line, "WORD", {"x-confidence": confidence}).text = value
        body_sentence = ET.SubElement(paragraph, "LINE")
        ET.SubElement(body_sentence, "WORD", {"x-confidence": "60"}).text = "Body sentence."
        ET.SubElement(body, "OBJECT")  # Preserve an empty scanned page in the map.
        path = directory / "sample.xml"
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
        return path

    def test_maps_empty_scanned_pages_and_only_short_heading_candidates(self):
        source_id = "ia_govind_chatak_gadwali_lok_gathayen_1958"
        candidate = {
            "archive_identifier": "sample-item",
            "source_url": "https://archive.org/details/sample-item",
            "record_id": "sample:page:0001",
            "text_sha256": "abc123",
            "text_normalized": "normalized page text",
            "automated_page_triage": {
                "script_profile": "mostly_devanagari",
                "warning_flags": ["low_text_density"],
            },
            "rights_status": "unverified_uploader_license_claim",
            "training_eligible": False,
            "public_redistribution_eligible": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            pages, summary = _page_map(
                source_id,
                self._write_djvu(Path(directory)),
                {(source_id, 1): candidate},
            )

        self.assertEqual(len(pages), 2)
        self.assertEqual(summary["xml_pages"], 2)
        self.assertEqual(summary["candidate_rows_aligned"], 1)
        self.assertEqual(summary["empty_ocr_pages"], 1)
        self.assertTrue(pages[1]["ocr_empty"])
        self.assertEqual(pages[0]["candidate_record_id"], "sample:page:0001")
        self.assertEqual(pages[0]["candidate_script_profile"], "mostly_devanagari")
        self.assertEqual(pages[0]["ocr_tokens_under_confidence_70"], 1)
        self.assertEqual(summary["section_cue_page_counts"]["chatak_genre_terms"], 1)
        self.assertEqual(len(pages[0]["heading_candidates"]), 2)
        self.assertNotIn("text", pages[0])
        self.assertEqual(pages[0]["section_assignment"], "unreviewed_candidate_map")

    def test_parses_devanagari_printed_page_references(self):
        refs = _contents_page_refs([
            {"line_number": 1, "text": "प्रस्तावना १४"},
            {"line_number": 2, "text": "अध्याय ३१"},
            {"line_number": 3, "text": "शीर्षक बिना पृष्ठ-संख्या"},
        ])

        self.assertEqual([ref["printed_page_number"] for ref in refs], [14, 31])
        self.assertEqual([ref["line_number"] for ref in refs], [1, 2])

    def test_shailesh_section_map_uses_verified_offset_and_keeps_gaps_explicit(self):
        def assign(scan_page):
            return _section_assignment(SHAILESH_SOURCE_ID, scan_page, False)

        self.assertEqual(sum(end - start + 1 for _, _, start, end in SHAILESH_TOC_RANGES), 416)
        self.assertEqual(assign(13)["section_assignment"], "contents_page")
        self.assertEqual(assign(26)["printed_page_number"], 13)
        self.assertEqual(assign(26)["section_id"], "preface")
        self.assertEqual(assign(27)["section_id"], "preface")
        self.assertEqual(assign(28)["section_id"], "language_development")
        self.assertEqual(assign(75)["section_id"], "word_sources")
        self.assertEqual(assign(76)["section_assignment"], "unmapped_toc_gap")
        self.assertEqual(assign(77)["section_assignment"], "unmapped_toc_gap")
        self.assertEqual(assign(78)["section_id"], "published_literature")
        self.assertEqual(assign(439)["section_id"], "word_index")
        self.assertEqual(assign(440)["section_assignment"], "unnumbered_suffix_unassigned")
        self.assertEqual(
            _section_assignment("ia_govind_chatak_gadwali_lok_gathayen_1958", 20, False)[
                "section_assignment"
            ],
            "unreviewed_candidate_map",
        )


if __name__ == "__main__":
    unittest.main()
