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

    def test_prepare_fills_missing_source_id_from_filename(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "corpus" / "garhwali_folklore.jsonl"
            source.parent.mkdir()
            source.write_text(json.dumps({"record_id": "page:1", "text": "गढ़वाली कथा"}) + "\n")
            m.prepare([source], root / "out", root=root)
            record = json.loads((root / "out/canonical.jsonl").read_text())
            self.assertEqual(record["provenance"][0]["source_id"], "garhwali_folklore")
            self.assertEqual(record["provenance"][0]["rights_status"], "not_recorded")

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

    def test_prepare_preserves_rights_evidence_and_license_id(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "corpus" / "licensed.jsonl"
            source.parent.mkdir()
            source.write_text(json.dumps({
                "record_id": "licensed:1",
                "text_normalized": "गढ़वाली पाठ",
                "iso_639_3": "gbm",
                "license_id": "CC-BY-4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "rights_evidence": "https://example.test/dataset-card",
                "attribution": "Example contributors",
            }) + "\n")
            m.prepare([source], root / "out", root=root)
            record = json.loads((root / "out/canonical.jsonl").read_text())
            provenance = record["provenance"][0]
            self.assertEqual(provenance["license_id"], "CC-BY-4.0")
            self.assertEqual(
                provenance["rights_evidence"], "https://example.test/dataset-card"
            )
            self.assertEqual(provenance["attribution"], "Example contributors")

    def test_prepare_preserves_structured_extraction_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'corpus' / 'dictionary.jsonl'
            source.parent.mkdir()
            source.write_text(json.dumps({
                'record_id': 'dictionary:1',
                'text_normalized': 'रिक',
                'iso_639_3': 'gbm',
                'text_format': 'structured_wiktionary',
                'source_text_format': 'wikitext',
                'relation': 'alternative_form',
                'headword': 'रिख',
            }) + '\n', encoding='utf-8')
            m.prepare([source], root / 'out', root=root)
            record = json.loads((root / 'out/canonical.jsonl').read_text())
            provenance = record['provenance'][0]
            self.assertEqual(provenance['text_format'], 'structured_wiktionary')
            self.assertEqual(provenance['source_text_format'], 'wikitext')
            self.assertEqual(provenance['linguistic_metadata']['relation'], 'alternative_form')
            self.assertEqual(provenance['linguistic_metadata']['headword'], 'रिख')

    def test_prepare_preserves_pdf_page_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'experimental' / 'incoming_pdfs.jsonl'
            source.parent.mkdir()
            source.write_text(json.dumps({
                'record_id': 'book:page:7',
                'text': 'गढ़वाली पाठ',
                'source_pdf': 'incoming/pdfs/book.pdf',
                'source_pdf_sha256': 'a' * 64,
                'pdf_page': 7,
                'title': 'Garhwali Book',
                'author': 'Example Author',
                'publication_year': 1954,
                'extraction_method': 'tesseract_hin_eng',
            }) + '\n', encoding='utf-8')
            m.prepare([source], root / 'out', root=root)
            row = json.loads((root / 'out/canonical.jsonl').read_text())
            provenance = row['provenance'][0]
            self.assertEqual(provenance['source_pdf_sha256'], 'a' * 64)
            self.assertEqual(provenance['pdf_page'], 7)
            self.assertEqual(provenance['title'], 'Garhwali Book')
            self.assertEqual(provenance['author'], 'Example Author')
            self.assertEqual(provenance['publication_year'], 1954)
            self.assertEqual(provenance['extraction_method'], 'tesseract_hin_eng')

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
