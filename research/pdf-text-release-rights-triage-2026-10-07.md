# PDF and text release rights triage — 2026-10-07

## Decision

No additional PDF-derived full text is cleared for Hugging Face or Kaggle publication by this review. The audit concerns **existing local sources** and does not add corpus examples. The useful next step is targeted permission or edition evidence, not another OCR or bulk upload.

| Source in pending inventory | Local extent | Evidence checked | Release decision and next evidence |
| --- | ---: | --- | --- |
| Uttarakhand Open University CGL study material | 436 page records | [Current UOU terms](https://uou.ac.in/terms-use) say its SLM is CC BY-NC-SA 4.0; the [specific CGL-101 PDF](https://uou.ac.in/sites/default/files/slm/CGL-101.pdf) has a reproduction restriction on page 3 noted in the [earlier edition audit](text-rights-resolution-2026-09-30.md), and the material quotes other authors. | **Pending.** Ask UOU to confirm in writing that the site license supersedes the restriction for the exact CGL PDFs, and identify the licensed portions versus quotations. CC BY-NC-SA also restricts commercial use; a general-purpose training corpus needs explicit terms rather than an unqualified open-data label. |
| e-Magazine of Uttarakhand | 1,770 text values | [Existing source audit](text-rights-resolution-2026-09-30.md) found author-attributed posts and at least one copyright notice, with no blanket reuse license. | **Pending.** Seek permission per author/post or an editor's documented authority for a named set of posts, including model-training and public redistribution scope. Publish links and bibliographic facts meanwhile. |
| Govind Chatak books (1956/1958) | 370 + 276 page records in different works/views | [Archive page and edition audit](internet-archive-priority-language-rights-review-2026-10-04.md) found strong Garhwali content relevance, but no author/publisher grant. The reported 2007 death date makes a simple old-book public-domain inference unsound. | **Pending.** Seek publisher/heir permission for the exact edition and quoted folk material. Keep OCR local. |
| Gunanand Juyal, 1967 comparative study | 200 useful page records | The [scan audit](internet-archive-priority-language-rights-review-2026-10-04.md) records an all-rights-reserved notice conflicting with an uploader CC0 claim. | **Pending.** Require evidence from the rightsholder that the specific edition was dedicated/licensed, or establish expiry with authoritative authorship and term evidence. Do not infer permission from a digitizer watermark. |
| *Linguistic Survey of India*, Vol. IX, Part IV (1916) | Separate historical source, not the Rai Pati Ram book | The [Wikimedia Commons file page](https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu) identifies the 1916 Grierson scan and marks that **file** public domain. | **Promising, edition-specific lead; OCR overlap checked.** The selected-column OCR mostly duplicates existing text; six unmatched cells are in a local expert-review queue. Transcribe and deduplicate only after fluent-speaker review. The Commons status does not clear other books, later annotations, or the unrelated 1916 *Garhwal Ancient and Modern* scan. |

## Practical order

1. Ask a fluent Garhwali reviewer to transcribe and verify the six queued LSI cells. Then deduplicate each corrected dialect value before considering a cited, rights-compatible addition; do not re-run bulk OCR.
2. Send UOU one focused rights question naming CGL-101 and the conflicting notices. The institution's answer should specify commercial and model-training use, redistribution, and third-party quotations.
3. Approach e-Magazine authors with a short opt-in form for named posts. Without grants, keep the 1,770 values local.

## LSI corpus-overlap check — 7 October 2026

Before treating the LSI scan as an expansion source, 632 non-empty rows from
`data/extracted/historical/lsi_1916_garhwali_dialect_table.jsonl` were compared
against the public v0.2.7 `text` config using Unicode NFKC, case folding, and
collapsed whitespace. **626 selected-column OCR strings matched existing
public text exactly after that normalization.** The remaining six stored OCR
strings did not match. A visual check of their source-page crops shows printed
cell content in all six; several stored values are single-letter outputs, one
contains table-layout OCR debris, and another is incomplete. Therefore they
cannot be dismissed as useless fragments, but their dialect text and cell
alignment are not reliable enough to publish as corrected labels.

Five of those six records also have a separate `source_standard_form_ocr`
field whose value occurs exactly in the public text after normalization. That
field is another table column, not the Rathi or Tehri dialect-cell transcription,
so it does not validate or replace the selected dialect value. The local,
unpublished review queue keeps all six unresolved with blank corrections; the
queue itself is not included in this public report. No LSI row was added to
public training data. The source's 284-row count in the rights-specific export
is a different derived-view count; this overlap check counts the extracted
OCR records.

The scan remains a possible source of carefully transcribed historical
examples, subject to fluent-speaker review and exact deduplication. No bulk
re-extraction or upload was done. A corrected row would need a source-page
transcription, verified row/column alignment, provenance, and a check against
existing public text before release.

The [previous archive review](internet-archive-priority-language-rights-review-2026-10-04.md) also found that several historic Garhwal books are mainly English or mixed Hindi/Garhwali. Copyright clearance alone would not make all their pages Garhwali training data. This is an evidence triage, not a legal opinion.
