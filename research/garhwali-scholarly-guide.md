# Garhwali scholarly guide for corpus design

Updated 2026-09-09. This guide records what the acquired scholarship says about
Garhwali and converts those findings into dataset decisions. It is a research
reference, not a substitute for native-speaker review. Papers are not promoted
into the Garhwali text corpus merely because they can be read online.

## Admission and rights rule

A source enters this register only when its identity, authorship, publication
page, and reuse terms can be checked. Full text may be stored locally for
research when the publisher supplies a compatible Creative Commons license.
The language examples and claims remain attributable to the paper. Material
with a NonCommercial term stays outside any commercial training release;
NoDerivatives material is retained unchanged for reference and is not converted
into a derived training set. Public access without an explicit reuse license is
catalogue evidence only.

## Acquired and catalogued scholarship

| Work | Verified rights | Local status | Project use |
| --- | --- | --- | --- |
| Dhasmana, Srivastava & Chiang (2026), [*Dialect Matters*](https://aclanthology.org/2026.vardial-1.12/) | CC BY 4.0 under the [ACL Anthology copyright policy](https://aclanthology.org/faq/copyright/) | Full PDF acquired | ASR evaluation, dialect transfer, orthography and error taxonomy |
| Montaut (2022), [*On the Non-Lexical Categories of avyay…*](https://hasp.ub.uni-heidelberg.de/catalog/book/919/chapter/12616) | CC BY-SA 4.0 on the chapter page | Metadata and license verified; automated full-text retrieval blocked by the publisher's Anubis JavaScript challenge | Case marking, postpositions, particles and grammaticalization; indexed evidence only until a person downloads the chapter normally |
| Sahu (2023), [*Preserving the Linguistic Diversity of Uttarakhand*](https://www.journals.asianresassoc.org/index.php/ijll/article/view/1194) | CC BY 4.0 on the article page | Full PDF acquired | Sociolinguistic vitality, education and documentation priorities |
| Uniyal (2019), [*English-Garhwali SMT System – Development and Evaluation*](https://www.researchpublish.com/papers/english-garhwali-smt-system--development-and-evaluation) | CC BY-NC 3.0 on the publisher page | Full PDF acquired | Parallel-data history, MT evaluation and error categories; noncommercial research only |
| Stroński (2010), [*Non-Nominative Subjects in Rajasthani and Central Pahari*](https://pressto.amu.edu.pl/index.php/linpo/article/view/v10122-010-0007-9) | CC BY-NC-ND 4.0 on the journal page | Full PDF acquired | Split ergativity and obligatory constructions; unchanged noncommercial reference only |

The machine-readable companion is
[`scholarly-open-sources.json`](scholarly-open-sources.json). The seventh
ingestion wave added five scholarly records and zero language-corpus rows.

## Findings that change the pipeline

### Speech, dialect and orthography

The 2026 VarDial paper studies spontaneous, noisy, code-mixed Garhwali speech
from VAANI. Its Garhwali-specific models use an 87/6/7 train/test/validation
split. The reported Garhwali results are WER/CER 0.650/0.270 for XLS-R,
0.493/0.193 for wav2vec2-BERT, 0.629/0.650 for Whisper-small, and 0.515/0.199
for HuBERT. The authors identify English transliteration inconsistency, Hindi
pretraining bias, Garhwali substitutions and omissions, and orthographic
variation as recurring errors. Across their languages, a higher share of
single-occurrence words correlates with higher WER (Pearson 0.705, p=0.0004).

The corpus must therefore retain both `text_original` and a reversible
`text_normalized`. It should add dialect/region, recording domain, speaker,
code-switch spans, and normalization-rule fields. Evaluation splits should be
stratified by dialect, speaker and domain; a random-only split can conceal
leakage and overstate generalization. Orthographic variants should be linked,
not silently collapsed.

### Case, aspect and modality

Stroński describes Central Pahari split ergativity and Garhwali future
obligation patterns in which the subject can be ergative-marked with an
infinitive. The paper also discusses movement toward Hindi-like dative marking
and variation across historical and contemporary evidence. Montaut's chapter
indexes several Garhwali postposition and case-marker families, including
ablative, dative/accusative, instrumental/ablative, ergative/agentive and
inflecting genitive forms. Their surface variants carry grammatical and
dialectal information.

Cleaning should flag unfamiliar case markers for review rather than replacing
them with Hindi forms. An annotation sample should cover case marker, aspect,
modality/obligation, gender/number agreement, construction type, source date,
and locality. Historical forms and modern forms require separate provenance.

### Machine translation and corpus lineage

Uniyal reports 40,000 monolingual Garhwali sentences assembled from magazine
OCR, Bible excerpts and blogs, plus 30,000 English-Garhwali sentence pairs made
by manually translating English prompts from ILCI. The paper reports BLEU 35.52
for Moses and 33.21 for Microsoft Translator Hub. Its error discussion points
to punctuation and decimal segmentation, untranslated or transliterated
English, lexicon gaps, and gender agreement. These are reported corpus sizes,
not released datasets with verified row-level rights.

The project should seek the author's or institution's permission and a source
manifest before acquiring those corpora. If obtained, magazine, Bible, blog and
ILCI-derived rows must preserve separate lineage and licenses. Evaluation needs
deduplication against every current benchmark before any train split is made.

### Vitality and collection priorities

Sahu describes pressure from Hindi and English, reduced use in urban and formal
domains, and the importance of intergenerational transmission, education,
dictionaries, audio/video documentation and digital media. The article is a
policy overview rather than a structural grammar, so numeric speaker claims
should be checked against census or other primary demographic sources before
publication.

Collection should prioritize consented contemporary speech across districts,
ages and settings, with speaker and consent metadata. Written collection should
cover conversation, oral history, education, public information and new
community writing rather than overrepresenting religious translation or OCR.

## Required quality fields for the next cleanup pass

1. Preserve `text_original`; make every normalization rule reversible and
   versioned.
2. Record dialect/locality, source date, genre, medium, speaker or author,
   script, code-switching, and source-level rights.
3. Add reviewer judgments for language identity, OCR confidence, spelling,
   case marking, agreement, segmentation and semantic completeness.
4. Maintain independent `core_open`, `restricted_nc`, `restricted_nc_nd`,
   `historical_review`, `benchmark_only`, and `quarantine` layers.
5. Split evaluation data by speaker, document and source before text-level
   randomization, then publish exact and near-duplicate checks.
6. Keep scholarly examples in an attributable research-example table. Do not
   merge them into anonymous training text.

## Publicly readable leads without verified open reuse terms

These sources can inform reading and outreach, but are not open-use corpus
inputs under the present evidence:

- Saket Raman Bahuguna, [*Grammatical Gender in Garhwali*](https://www.languageinindia.com/may2023/saketgrammaticalgendergarhwali.html) and [*The Development of Ergative in Garhwali*](https://languageinindia.com/aug2023/saketergativedevelopmentgarhwali1.html): publicly readable, no verified Creative Commons grant found.
- [University of Kashmir article on aspect in Garhwali](https://linguistics.uok.edu.in/Files/f6ec3740-422d-4ac1-9f52-ddfe2cffcb28/Journal/0cfe1c5e-eda8-4e21-8361-abeccc57c40a.pdf): public PDF, no verified open-content license found.
- [*Language Identification of Devanagari Poems*](https://arxiv.org/abs/2012.15023): includes Garhwali, but an arXiv download page alone does not grant dataset reuse rights.
- Uniyal's reported 40,000-sentence monolingual and 30,000-pair parallel corpora: high-value permission target; availability and component licenses remain unverified.

## Immediate research and ingestion queue

1. Process user-supplied PDFs through checksum, OCR/text extraction, page-level
   quality metrics and a rights manifest; keep originals in `incoming/pdfs/`.
2. Request a licensed manifest or export for Uniyal's monolingual and parallel
   corpora, including provenance for every component.
3. Obtain Montaut's chapter through ordinary human browser download and verify
   its checksum; do not automate or bypass the publisher's challenge.
4. Build a small native-reviewed evaluation set stratified by dialect, speaker,
   genre and code-switching.
5. Run OCR cleanup with separate flags for scan defects and authentic language
   variation, followed by native-speaker adjudication.
