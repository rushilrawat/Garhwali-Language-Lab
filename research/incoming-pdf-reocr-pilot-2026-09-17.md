# Incoming PDF multi-layout OCR pilot

The automated pre-release cleanup reprocessed the 20 weakest surface-quality
pages among 659 incoming-PDF machine-OCR records. Each page was rendered at
300 DPI and passed through Tesseract `hin+eng` with layout modes 3, 4, 6, and
11. Original OCR remains unchanged; all new text is stored as evidence-only
candidates.

| Layout | Mean word confidence | Median confidence | Mean characters | Confidence wins |
|---:|---:|---:|---:|---:|
| 3 | 81.234 | 82.066 | 3,626.8 | 6 |
| 4 | 79.041 | 80.572 | 7,135.4 | 0 |
| 6 | 75.252 | 78.286 | 7,510.6 | 1 |
| 11 | 81.400 | 82.815 | 6,101.8 | 13 |

No two layouts produced byte-identical full-page text. This rules out exact
page agreement as a useful automatic selection criterion. Layout 11 most often
maximized word confidence, while layouts 4 and 6 recovered more text on dense
or two-column pages. The full run therefore retains all four outputs for later
token-level consensus and source-layout selection rather than applying one
global winner.

The first attempted pilot exposed that this Tesseract build does not recognize
the `tsv` config shortcut. It treated `tsv` as a missing parameter file and
returned ordinary text. The corrected invocation uses
`-c tessedit_create_tsv=1`; a regression test now verifies the command and TSV
parsing.

Artifacts are under
`data/processed/evaluation/data_quality/incoming_pdf_reocr_v0_1/`.
