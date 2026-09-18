# Incoming PDF ingestion — 2026-09-16

Seven user-supplied Garhwali PDFs were hashed before extraction. Six scans were
new. `Gadwali LokGeet.pdf` is byte-identical to the already ingested Internet
Archive copy (`6a1028…bfb34e`), whose 370 page records remain active, so it was
not extracted a second time.

## Result

| Source | Pages | Active page records | Method | Hugging Face text segments* |
| --- | ---: | ---: | --- | ---: |
| *Dictionary: English-Garhwali-Hindi* — Achlanand Jakhmola | 124 | 123 | Tesseract `hin+eng` | 9,214 |
| *Garhwali Sahitya ki Bhumika* — D. P. Thapliyal; S. C. Negi | 75 | 74 | Tesseract `hin+eng` | 555 |
| *Garhwali Bhasha: Ek Bhashashastriya Aur Vyakaranik Adhyayan* — Govind Chatak | 147 | 147 | Tesseract `hin+eng` | 1,682 |
| *Garhwali-Hindi Dictionary* — Arvind Purohit; Beena Benzwal | 239 | 239 | Tesseract `hin+eng` | 12,453 |
| *Garhwal: Bhasha, Sahitya aur Sanskriti* — Govind Chatak | 78 | 76 | Tesseract `hin+eng` | 3,329 |
| *A Syntactic Sketch of Garhwali* — Anang Chandra Chandola | 110 | 110 | embedded PDF text | 720 |

## Verified bibliography

Each PDF now has a neighboring JSON sidecar. Ingestion reads that sidecar and
preserves the fields below through page extraction, corpus preparation, text
segmentation, and the all-data Hugging Face package.

| Work | Role | Edition / date | Publisher | Identifier / extent |
| --- | --- | --- | --- | --- |
| *Dictionary: English-Garhwali-Hindi* | Achlanand Jakhmola, author | First edition, 2016 | Samaya Sakshaya Prakashan, Dehradun | ISBN 978-81-86810-16-1; 246 pp. |
| *Garhwali Lokgeet*, vol. 1: *Laghu Geet* | Govind Chatak, compiler and Hindi translator | 1956 | Jugal Kishore and Company, Dehradun | DOI 10.15026/8727; 376 scan pages |
| *Garhwali Sahitya ki Bhumika* | Damodar Prasad Thapliyal and Shyam Chand Negi, editors | First edition, 1,000 copies; 26 January 1954 | Garhwali Jan Sahitya Parishad; Yugvani Press, Dehradun | 75 pp. |
| *Garhwali Bhasha: Ek Bhashashastriya Aur Vyakaranik Adhyayan* | Govind Chatak, author; Dhirendra Varma, foreword | First edition, September 1959 | Lok Bharati; Mohini distributor, Dehradun | 147 pp. |
| *Garhwali-Hindi Shabdkosh* | Arvind Purohit and Beena Benjwal, compilers; Ramakant Benjwal, editor | First edition, June 2007 | Winsar Publishing Company, Dehradun | ISBN 81-86844-53-8; LCCN 2007431146; 472 pp. |
| *Garhwal: Bhasha, Sahitya aur Sanskriti* | Govind Chatak, author | First edition, 2008 | Takshila Prakashan, New Delhi | ISBN 978-81-7965-157-5; 152 pp. |
| *A Syntactic Sketch of Garhwali* | Anang Chandra Chandola, author | PhD dissertation, June 1966 | Department of Linguistics, University of Chicago | 103 pp.; Pauri dialect basis |

\*Counts are exact text rows carrying that source in the rebuilt all-data
Hugging Face package. Shared segments retain all parent sources. The union is
27,926 exact segment identities.

The six unique PDFs yielded **769 nonempty page records**, **1,774,697 page-text
characters**, and no exact page-text duplicates within the incoming batch or
against the earlier canonical page records. Four image pages contained no
recoverable text and are listed explicitly in the machine-readable report.

All 769 records are active in `experimental/incoming_pdfs.jsonl`. OCR warnings,
unknown rights, and native-review needs remain metadata; none is quarantined or
removed. Each record retains the complete available bibliography, source PDF
path and SHA-256, page number, extraction method, and quality flags. A verified
sample from the rebuilt Hugging Face text configuration includes the Jakhmola
book's author, publisher, place, edition, ISBN, physical extent, subjects,
catalog links, rights statement, and extraction provenance.

The rebuilt all-data package contains **28,755 exact-unique source texts** and
**114,082 exact-unique text segments**. Its 12 configurations contain **256,947
rows**, including the speech, lexicon, instruction, and complete text catalog
views. The catalog contains all 28,755 text values with zero redactions.

## Reproduce

```bash
PYTHONPATH=scripts .venv/bin/python scripts/ingest_incoming_pdfs.py
.venv/bin/python scripts/prepare_text_corpus.py
.venv/bin/python scripts/build_all_data_view.py
.venv/bin/python scripts/clean_text_corpus.py
.venv/bin/python scripts/deep_cleanup.py
.venv/bin/python scripts/segment_text_corpus.py
.venv/bin/python scripts/tag_language_quality.py
.venv/bin/python scripts/build_dataset_splits.py
.venv/bin/python scripts/build_quality_tiers.py
PYTHONPATH=scripts .venv/bin/python scripts/build_huggingface_dataset.py --profile all-data
```

The machine-readable intake report is
`research/incoming-pdf-ingestion-2026-09-16.json`. The OCR cache is resumable
and remains Git-ignored under `data/extracted/incoming_pdfs/page_cache/`.
