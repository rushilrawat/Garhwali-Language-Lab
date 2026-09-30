import json
import tempfile
import unittest
from pathlib import Path

from ingest_jambu_garhwali import (
    LICENSE_URL,
    acquire_snapshot,
    parse_page,
    records_from_rows,
    write_records,
)


FIXTURE = """<!doctype html>
<p>Showing 1&mdash;2 of 2 reflexes.</p>
<table><thead><tr class="lang-row"><th>header</th></tr></thead>
<tbody class="results">
<tr class="lang-row"><td>Indo-Aryan</td><td><p><a href="/reflexes/0-265">ākʰar</a></p></td><td><p><a href="/entries/38">akṣára [38]</a></p></td><td></td><td></td><td><a href="/references/CDIAL">T1962—1966</a></td></tr>
<tr class="lang-row"><td>Indo-Aryan</td><td><p><a href="/reflexes/0-633">ageṭʰī</a></p></td><td><p><a href="/entries/65">agniṣṭʰá [65]</a></p></td><td>portable firepan</td><td>f</td><td><a href="/references/CDIAL">T1962—1966</a></td></tr>
</tbody></table>"""


class JambuIngestionTests(unittest.TestCase):
    def test_parse_page_extracts_rows_and_excludes_header(self):
        page, rows = parse_page(FIXTURE, 1)

        self.assertEqual(page, {"page": 1, "first": 1, "last": 2, "total": 2})
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1]["text"], "ākʰar")
        self.assertEqual(rows[1][3]["text"], "portable firepan")
        self.assertEqual(rows[1][4]["text"], "f")

    def test_parse_page_rejects_changed_or_truncated_row_count(self):
        truncated = FIXTURE.replace(
            '<tr class="lang-row"><td>Indo-Aryan</td><td><p><a href="/reflexes/0-633">ageṭʰī</a></p></td><td><p><a href="/entries/65">agniṣṭʰá [65]</a></p></td><td>portable firepan</td><td>f</td><td><a href="/references/CDIAL">T1962—1966</a></td></tr>',
            "",
        )
        with self.assertRaisesRegex(ValueError, "advertises 2 rows"):
            parse_page(truncated, 1)

    def test_records_retain_license_source_ids_and_glosses(self):
        _, rows = parse_page(FIXTURE, 1)
        manifest = {
            "source": "Jambu Garhwali [Garh] reflex listing",
            "retrieved_at": "2026-09-30T00:00:00+00:00",
            "pages": [{
                "page": 1,
                "url": "https://neojambu.herokuapp.com/languages/Garh",
                "sha256": "page-hash",
                "raw_path": "data/downloads/jambu_garhwali/pages/page-01.html",
            }],
        }

        records = records_from_rows(rows, manifest)

        self.assertEqual([record["record_id"] for record in records], [
            "jambu-garhwali:0-265", "jambu-garhwali:0-633"
        ])
        self.assertTrue(all(record["license_url"] == LICENSE_URL for record in records))
        self.assertEqual(records[1]["english_gloss"], "portable firepan")
        self.assertEqual(records[1]["source_citation"], "T1962—1966")
        self.assertFalse(records[0]["training_eligible"])
        self.assertTrue(records[0]["experimental_training_eligible"])
        self.assertFalse(records[0]["native_reviewed"])

    def test_acquire_snapshot_is_offline_and_checksums_cached_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "data/downloads/jambu_garhwali"
            pages = raw / "pages"
            pages.mkdir(parents=True)
            page_manifest = {
                "source": "Jambu Garhwali [Garh] reflex listing",
                "url": "https://neojambu.herokuapp.com/languages/Garh",
                "license_id": "CC-BY-4.0",
                "license_url": LICENSE_URL,
                "rights_evidence_url": "https://neojambu.herokuapp.com/languages/Garh",
                "retrieved_at": "2026-09-30T00:00:00+00:00",
                "pages": [{
                    "page": 1, "first": 1, "last": 2, "total": 2,
                    "url": "https://neojambu.herokuapp.com/languages/Garh",
                    "sha256": __import__("hashlib").sha256(FIXTURE.encode()).hexdigest(),
                }],
            }
            # Use a single-page test layout; the production manifest has all 16 pages.
            from ingest_jambu_garhwali import PAGE_COUNT, PAGE_SIZE, PAGES_DIR, SNAPSHOT_MANIFEST
            import ingest_jambu_garhwali as module
            old_page_count, old_page_size = module.PAGE_COUNT, module.PAGE_SIZE
            try:
                module.PAGE_COUNT, module.PAGE_SIZE = 1, 50
                (pages / "page-01.html").write_text(FIXTURE, encoding="utf-8")
                page_manifest["pages"][0]["raw_path"] = str((PAGES_DIR / "page-01.html").as_posix())
                (raw / "web-snapshot-manifest.json").write_text(json.dumps(page_manifest), encoding="utf-8")
                rows, manifest = acquire_snapshot(root, offline=True)
            finally:
                module.PAGE_COUNT, module.PAGE_SIZE = old_page_count, old_page_size

            self.assertEqual(len(rows), 2)
            self.assertEqual(manifest["parsed_rows"], 2)

    def test_write_records_emits_manifest_with_unique_form_count(self):
        _, rows = parse_page(FIXTURE, 1)
        manifest = {
            "source": "Jambu Garhwali [Garh] reflex listing",
            "retrieved_at": "2026-09-30T00:00:00+00:00",
            "pages": [{
                "page": 1,
                "url": "https://neojambu.herokuapp.com/languages/Garh",
                "sha256": "page-hash",
                "raw_path": "data/downloads/jambu_garhwali/pages/page-01.html",
            }],
        }
        records = records_from_rows(rows, manifest)

        with tempfile.TemporaryDirectory() as directory:
            summary = write_records(Path(directory), records, manifest)
            stored = [json.loads(line) for line in (Path(directory) / "corpus/jambu_garhwali.jsonl").read_text().splitlines()]
            saved_manifest = json.loads((Path(directory) / "corpus/jambu_garhwali_manifest.json").read_text())

        self.assertEqual(len(stored), 2)
        self.assertEqual(summary["unique_forms"], 2)
        self.assertEqual(summary["exact_overlap_with_existing_unique_forms"], 0)
        self.assertEqual(summary["exact_new_unique_forms"], 2)
        self.assertEqual(summary["already_in_current_corpus_unique_forms"], 0)
        self.assertEqual(saved_manifest["source_file_sha256"], summary["source_file_sha256"])

    def test_write_records_counts_only_exact_new_forms_against_other_sources(self):
        import hashlib

        _, rows = parse_page(FIXTURE, 1)
        manifest = {
            "source": "Jambu Garhwali [Garh] reflex listing",
            "retrieved_at": "2026-09-30T00:00:00+00:00",
            "pages": [{
                "page": 1,
                "url": "https://neojambu.herokuapp.com/languages/Garh",
                "sha256": "page-hash",
                "raw_path": "data/downloads/jambu_garhwali/pages/page-01.html",
            }],
        }
        records = records_from_rows(rows, manifest)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            canonical = root / "data/processed/text/canonical.jsonl"
            canonical.parent.mkdir(parents=True)
            existing = {
                "text_sha256": hashlib.sha256("ākʰar".encode()).hexdigest(),
                "provenance": [{"source_id": "other-open-source"}],
            }
            canonical.write_text(json.dumps(existing) + "\n", encoding="utf-8")
            summary = write_records(root, records, manifest)

        self.assertEqual(summary["exact_overlap_with_existing_unique_forms"], 1)
        self.assertEqual(summary["exact_new_unique_forms"], 1)
        self.assertEqual(summary["already_in_current_corpus_unique_forms"], 1)


if __name__ == "__main__":
    unittest.main()
