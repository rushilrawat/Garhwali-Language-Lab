# Dataset attribution

Garhwali Language Lab is a multi-source collection. It has no single dataset-wide
content license. Every redistributed record must retain its `provenance`,
`public_rights_basis`, source identifier, creator or attribution statement,
license identifier and URL, and transformation notes.

Most public content views use records with an explicit source-level reuse basis.
The v0.2.7 `paharili_gbm` config is an explicit experimental inclusion with
unresolved sentence-level origin and redistribution status; its rows retain
that status and are not covered by a corpus-wide license. Public availability
in the Hub does not grant a reuse right. The all-data profile also contains
restricted and rights-pending research inputs. Consult `LICENSE_POLICY.md`
before redistribution or model release.

When citing the collection, cite the Garhwali Language Lab release identifier and
the original sources named on the records used. Attribution to this project does
not replace attribution required by an upstream source.

## v0.2.7 PahariLI Garhwali text

Rachana Gusain, [PahariLI](https://github.com/rachanagusain/PahariLI), a
four-language text language-identification corpus. This release includes
Garhwali-labeled records from its train and test files. The upstream repository
includes an Apache-2.0 license file; its README does not identify sentence-level
origins. This project preserves the repository license declaration and
underlying-source uncertainty on every row and does not assert that Apache-2.0
clears underlying source texts. The export collapses normalized duplicate
sentences, preserves their source IDs and surface-form variants, and routes
four train/test-crossing text groups to `source_overlap`. Original file
checksums and source URLs are in row-level provenance.

## v0.2.0 Garhwali text additions

- Grierson, George A. *Linguistic Survey of India*, Vol. IX, Part IV: Garhwali
  dialect table and selected language specimens. Digitized scan:
  [Internet Archive](https://archive.org/details/LSIV0-V11); rights evidence:
  [Wikimedia Commons scan page](https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu).
  The extracted historical material is marked Public Domain Mark 1.0 in its
  rows. OCR confidence and printed/source page locators remain attached.
- Upreti, Atmaram, compiler. *Proverbs & Folklore of Kumaun and Garhwal* (1894),
  [Internet Archive item](https://archive.org/details/cu31924089930774). This
  intake includes only five lines explicitly identified as Garhwali in the
  source. The captured source and printed-page/line locators are recorded per
  row; the rows carry a Public Domain Mark 1.0 status.
- Door43 OBS-TLF, [Garhwali Open Bible Stories](https://git.door43.org/OBS-TLF/gbm_obs),
  release `v1`, revision `f08afc73e1770129fbcd3089181f2faf2abbf54d`.
  Text is licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/);
  the source attribution, pinned revision, and archive checksums are retained
  on each record. Illustrations are not included.

The v0.2.0 intake contains 696 source rows, 673 exact-unique values within the
intake, and 671 exact-unique texts not present in the prior corpus layers.
Exact duplicate rows and their separate source attributions remain preserved in
the source-level extraction records.
