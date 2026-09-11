import json
import tempfile
import unittest
from pathlib import Path

import prepare_text_corpus as m


class TextPreparationTests(unittest.TestCase):
    def test_normalize_text_uses_nfc_and_collapses_whitespace(self):
        self.assertEqual(m.normalize_text("  गढ़वाली\n\tभाषा  "), "गढ़वाली भाषा")

    def test_prepare_groups_duplicates_and_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            left = root / "corpus" / "left.jsonl"
            right = root / "restricted" / "right.jsonl"
            left.parent.mkdir(); right.parent.mkdir()
            left.write_text(json.dumps({"record_id": "a", "text_normalized": "म्यार भाषा"}) + "\n")
            right.write_text(json.dumps({"id": "b", "text": " म्यार\nभाषा "}) + "\n")
            report = m.prepare([left, right], root / "out", root=root)
            canonical = [json.loads(x) for x in (root / "out/canonical.jsonl").read_text().splitlines()]
            duplicates = [json.loads(x) for x in (root / "out/duplicates.jsonl").read_text().splitlines()]
            self.assertEqual(report["source_records"], 2)
            self.assertEqual(report["unique_texts"], 1)
            self.assertEqual(len(canonical[0]["provenance"]), 2)
            self.assertEqual(len(duplicates), 1)

    def test_prepare_skips_empty_text_and_uses_transcript_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "rows.jsonl"
            source.write_text("\n".join([json.dumps({"id": "empty", "text": "  "}), json.dumps({"id": "speech", "transcript": "मी ठीक छौं"})]) + "\n")
            report = m.prepare([source], root / "out", root=root)
            self.assertEqual(report["source_records"], 2)
            self.assertEqual(report["empty_records"], 1)
            self.assertEqual(report["unique_texts"], 1)

    def test_prepare_preserves_language_quality_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "corpus" / "lexicon.jsonl"
            source.parent.mkdir()
            source.write_text(json.dumps({
                "record_id": "word:1", "text_normalized": "कुकुर", "iso_639_3": "gbm",
                "script": "Deva", "genre": "thematic_lexicon", "dialect": "Srinagar",
                "english_gloss": "dog", "semantic_domain": "animal",
            }) + "\n")
            m.prepare([source], root / "out", root=root)
            record = json.loads((root / "out/canonical.jsonl").read_text().splitlines()[0])
            provenance = record["provenance"][0]
            self.assertEqual(provenance.get("iso_639_3"), "gbm")
            self.assertEqual(provenance.get("genre"), "thematic_lexicon")
            self.assertEqual(provenance.get("dialect"), "Srinagar")
            self.assertEqual(provenance.get("linguistic_metadata", {}).get("english_gloss"), "dog")
            self.assertEqual(provenance.get("linguistic_metadata", {}).get("semantic_domain"), "animal")

    def test_split_assignment_is_stable(self):
        digest = "a" * 64
        self.assertEqual(m.split_for_hash(digest), m.split_for_hash(digest))
        self.assertIn(m.split_for_hash(digest), {"train", "validation", "test"})

    def test_experimental_training_eligibility_survives_canonicalization(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'experimental' / 'rows.jsonl'
            source.parent.mkdir()
            source.write_text(json.dumps({
                'record_id': 'experimental:1',
                'text_normalized': 'म्यार भाषा',
                'experimental_training_eligible': True,
                'training_eligible': False,
            }) + '\n', encoding='utf-8')
            m.prepare([source], root / 'out', root=root)
            row = json.loads((root / 'out/canonical.jsonl').read_text())
            self.assertTrue(row['provenance'][0]['experimental_training_eligible'])
            self.assertTrue(row['any_experimental_training_eligible_source'])


if __name__ == "__main__":
    unittest.main()
