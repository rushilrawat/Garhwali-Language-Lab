# PDF intake

## Current intake status (2026-09-26)

Seven supplied PDFs have been hash-checked: six unique books yielded **769
active page records** and 1,774,697 extracted characters; one exact duplicate
reuses the earlier 370-page *Gadwali LokGeet* extraction. The new pages flow
through the all-data pipeline and preserve their bibliography, page, source
hash, OCR method, quality, and rights metadata. They are not all cleared for
public redistribution. See the [ingestion report](../../research/incoming-pdf-ingestion-2026-09-16.md).

Four-layout OCR evidence was also generated for 659 machine-OCR pages. The
original text remains intact; 69 same-engine layout-consensus variants are
reversible proposals, not verified corrections. See the
[OCR report](../../research/incoming-pdf-reocr-pilot-2026-09-17.md).

You can place candidate PDFs in this folder now. PDF files are ignored by Git,
but this README and source metadata can be versioned.

For each PDF, add a neighboring JSON file with the same base name:

```json
{
  "title": "Exact title",
  "author": "Author or institution",
  "publication_year": 1900,
  "download_url": "https://example.org/item.pdf",
  "landing_page": "https://example.org/catalog-record",
  "license_or_rights_statement": "Public domain / CC license / unknown",
  "rights_evidence_url": "https://example.org/rights",
  "suspected_garhwali_pages": "61-84",
  "notes": "Dialect, scan quality, or duplicate-copy information"
}
```

Prefer original scans and stable institutional or archive landing pages. Every
non-empty page is retained in the active experimental corpus with source,
rights, extraction, and quality fields. Public redistribution remains a
separate decision recorded in those fields.

Useful first downloads are Garhwali dictionaries with clear reuse terms,
pre-1931 books or periodicals, institutional grammars and wordlists, and
permissioned Garhwali transcripts. Avoid downloading a second mirror when the
same edition and scan already exists in `sources/online/`.

Run the resumable intake with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/ingest_incoming_pdfs.py
```

The command checks exact PDF hashes before extraction, reuses prior work for an
exact duplicate, uses an existing PDF text layer when it is substantive, OCRs
image-only pages with Tesseract `hin+eng`, and caches each completed page under
`data/extracted/`.

To assimilate every new PDF through normalization, segmentation, quality tags,
splits, and the local all-data package, run:

```bash
bash scripts/refresh_incoming_pdfs.sh
```

The refresh is local and resumable; it does not spend Hugging Face GPU credit.
It rebuilds the all-data package, but does not upload it. Before a public release,
review the resulting provenance and source-specific rights; the current text
repository remains owner-private, and the public-profile build may redact values
or omit records without compatible redistribution evidence.
