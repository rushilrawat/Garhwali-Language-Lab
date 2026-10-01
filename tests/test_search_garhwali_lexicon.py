import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from search_garhwali_lexicon import search, searchable_text, source_citations


class LexiconSearchTests(unittest.TestCase):
    def test_search_matches_form_and_multiple_gloss_shapes(self):
        rows = [
            {"form": "पाणी", "glosses": {"english": ["water"], "hindi": ["जल"]}},
            {"form": "घर", "glosses": {"english": "house"}},
        ]
        self.assertEqual(search(rows, "WATER"), [rows[0]])
        self.assertEqual(search(rows, "घर"), [rows[1]])
        self.assertIn("water", searchable_text(rows[0]))

    def test_source_citations_keep_attribution_and_url(self):
        row = {"provenance": [{
            "attribution": "Contributor group",
            "source_url": "https://example.org/entry",
            "file": "internal/path.jsonl",
        }]}
        self.assertEqual(
            source_citations(row),
            ["Contributor group — https://example.org/entry"],
        )

    def test_search_validates_query_and_stops_at_limit(self):
        rows = [{"form": f"word-{index}"} for index in range(4)]
        with self.assertRaisesRegex(ValueError, "query"):
            search(rows, "  ")
        self.assertEqual(len(search(rows, "word", limit=2)), 2)


if __name__ == "__main__":
    unittest.main()
