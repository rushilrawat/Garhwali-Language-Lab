import unittest

from ingest_garhwali_language_library import (
    SOURCE_ID,
    git_blob_sha1,
    records_from_payloads,
    summary,
)


class GarhwaliLanguageLibraryIngestionTests(unittest.TestCase):
    def test_pinned_git_blob_checksum_matches_git_object_format(self):
        self.assertEqual(
            git_blob_sha1(b"hello\n"),
            "ce013625030ba8dba906f756967f9e9ca394464a",
        )

    def test_static_entries_keep_surface_glosses_and_source_rights(self):
        payloads = {
            "words.json": [{
                "garhwali": "  ब्वै\n",
                "hindi": "माँ",
                "english": "mother",
                "pos": "noun",
                "gender": "F",
                "category": "kinship",
                "dialect_variants": {"tehri": "ब्वे"},
            }],
            "phrases.json": [{
                "garhwali": "कै छा?", "hindi": "कैसे हो?", "english": "How are you?",
                "category": "greeting", "audio_hint": "sample",
            }],
            "proverbs.json": [{
                "pakhana": "अखाण", "hindi": "कहावत", "meaning": "proverb meaning",
                "literal": "literal meaning",
            }],
            "riddles.json": [{
                "aana": "आणा", "english_hint": "riddle hint", "solution": "answer",
            }],
        }

        rows = records_from_payloads(payloads, "2026-09-30T00:00:00+00:00")

        self.assertEqual([row["genre"] for row in rows], ["lexicon", "phrase", "proverb", "riddle"])
        self.assertEqual(rows[0]["text_normalized"], "ब्वै")
        self.assertEqual(rows[0]["english_gloss"], "mother")
        self.assertEqual(rows[0]["dialect_variants"], {"tehri": "ब्वे"})
        self.assertEqual(rows[2]["english_gloss"], "proverb meaning")
        self.assertEqual(rows[3]["solution"], "answer")
        self.assertEqual(rows[0]["source_id"], SOURCE_ID)
        self.assertEqual(rows[0]["license_id"], "MIT")
        self.assertFalse(rows[0]["training_eligible"])
        self.assertTrue(rows[0]["experimental_training_eligible"])
        self.assertFalse(rows[0]["native_reviewed"])

    def test_summary_deduplicates_surfaces_and_counts_existing_overlap(self):
        records = [
            {"text_sha256": "existing", "genre": "lexicon"},
            {"text_sha256": "new", "genre": "phrase"},
            {"text_sha256": "new", "genre": "phrase"},
        ]

        result = summary(records, {"existing"})

        self.assertEqual(result["source_records"], 3)
        self.assertEqual(result["unique_surface_forms"], 2)
        self.assertEqual(result["duplicate_source_rows"], 1)
        self.assertEqual(result["exact_overlap_with_existing_unique_forms"], 1)
        self.assertEqual(result["exact_new_unique_forms"], 1)
        self.assertEqual(result["recommended_training_eligible_records"], 0)


if __name__ == "__main__":
    unittest.main()
