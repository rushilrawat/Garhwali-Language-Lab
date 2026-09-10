# Garhwali access blockers after VAANI

Checked with the project's authenticated Hugging Face account on 2026-09-10.

## Same gate pattern as VAANI

### Chaashini

- Repository: <https://huggingface.co/datasets/kapturecx/Chaashini>
- Current revision: `f27d29c29ef0b6b48c4a3377f314f44dfb9a538b`
- Gate: manual Hugging Face approval/contact sharing.
- Current account state: repository metadata is visible, but the Garhwali file returns HTTP 403 and Dataset Viewer returns inaccessible/404.
- Garhwali payload: config `gbm`, file `data/gbm/chaashini-gbm-00000.parquet`, 73,599 bytes.
- Published card license: Apache-2.0.
- Previously visible catalogue quantity: one approximately 2.2-second Garhwali clip. The current payload cannot be independently inspected until access is approved.

This is the only currently verified source with the same practical sequence as VAANI: the owner accepts the Hugging Face gate, then the project audits the actual schema, source lineage, consent, license scope, duplication, audio properties, and transcript before promotion.

## Gated, but opening the gate does not currently add Garhwali data

### GlotLID corpus

- Repository: <https://huggingface.co/datasets/cis-lmu/glotlid-corpus>
- Gate: manual Hugging Face approval.
- License card: `other`; its documentation says the CC0 grant applies to metadata/annotations rather than automatically relicensing collected source text.
- Current tree: 6,102 files, with no filename or directory containing `gbm` or Garhwali.

It is useful for language-identification methodology, but there is no verified current Garhwali payload to collect. Access approval alone would also not resolve source-document rights.

### `somu9/gbm-tokenizer`

- Repository: <https://huggingface.co/somu9/gbm-tokenizer>
- Gate: manual Hugging Face approval.
- Contents: a SentencePiece model and vocabulary only (`gbm_tokenizer.model` and `gbm_tokenizer.vocab`).
- No training corpus is published.

The tokenizer may become a comparison artifact after access, but it cannot increase the Garhwali language dataset.

## Valuable Garhwali sources with different blockers

| Source | Potential yield | Actual blocker | Required action |
|---|---:|---|---|
| [HimLingo](https://himlingo.com/) | Reported 4,206 words across 13 dialects, potentially with examples/pronunciation | Terms prohibit unauthorized scraping and contributors retain ownership | Request a versioned export plus explicit redistribution/model-training rights and contributor sublicensing evidence |
| [Max Planck/TLA Garhwali elicitation collection](https://hdl.handle.net/1839/00-0000-0000-0021-4D9C-7) | Inventory previously exposed 20 WAV references and 28 working/final-data references, roughly 7 GB | Resource downloads returned 403 and no usable license was displayed | Request archive access and written use/redistribution terms |
| [Garhwali New Testament](https://www.freebiblesindia.in/bible/gbm/index.html) | 27 books / 260 chapters, text and advertised audio | CC BY-SA 4.0 is stated, but the advertised ZIP returns 404 and the reader presents an access challenge | Ask the publisher for a working source-native export; preserve ShareAlike attribution |
| Heidelberg open Garhwali scholarly chapter | One research chapter | CC BY-SA metadata is visible, but the host presents an Anubis JavaScript challenge | Download manually through the normal browser or request the file from the publisher; use as linguistic research, not bulk conversational text |
| Historical *Garhwali* periodical | Microfilm catalogue reports 1916–1926 holdings | No public issue scans | Request digitization from the holding institution and perform issue-level rights review |
| *Rajniti* (1901) and early Garhwali New Testament witnesses | Public-domain-era printed Garhwali | Physical/catalogue holdings without public scans | Submit library digitization requests and verify each edition |
| Modern dictionaries, plays, novels, poetry, blogs and recordings | Potentially large and culturally valuable | Copyright or contributor permission, not a technical access gate | Obtain licenses from authors, publishers, estates, performers, and speakers |

## Priority

1. Obtain Chaashini access because it is the only unresolved VAANI-like account gate, though its Garhwali yield appears tiny.
2. Pursue HimLingo because it offers the largest structured dialect vocabulary gain.
3. Pursue Max Planck/TLA because it may add elicited speech and aligned working files unavailable from VAANI.
4. Ask Free Bibles India for a working Garhwali New Testament export.
5. Submit digitization requests for public-domain-era books and periodicals.

