# PDF intake

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

The command checks exact PDF hashes before extraction, uses an existing PDF
text layer when it is substantive, OCRs image-only pages with Tesseract
`hin+eng`, and caches each completed page under `data/extracted/`.

To assimilate every new PDF through normalization, segmentation, quality tags,
splits, and the upload-ready Hugging Face all-data package, run:

```bash
bash scripts/refresh_incoming_pdfs.sh
```

The refresh is local and resumable; it does not spend Hugging Face GPU credit.
Upload happens only when the completed dataset package is explicitly published.
