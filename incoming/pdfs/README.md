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

Prioritize PDFs with an explicit Creative Commons license, a reliable
public-domain basis, or written permission. Prefer original scans and stable
institutional or archive landing pages. Keep uncertain-rights PDFs: they can be
hashed and reviewed, but their text will stay outside the training pool.

Useful first downloads are Garhwali dictionaries with clear reuse terms,
pre-1931 books or periodicals, institutional grammars and wordlists, and
permissioned Garhwali transcripts. Avoid downloading a second mirror when the
same edition and scan already exists in `sources/online/`.
