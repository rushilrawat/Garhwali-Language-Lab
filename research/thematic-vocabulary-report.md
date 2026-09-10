# Garhwali thematic vocabulary web pass

Verified 2026-09-09. This pass answers a specific corpus gap: searchable local
words grouped by meaning, including birds, animals, instruments, plants, food,
household objects, occupations and other cultural terms.

## Result

The machine-readable lexicon contains 666 source-level records representing
642 distinct normalized written forms. A form can occur more than once when separate
sources attest it or attach a different gloss. Twelve forms currently have
more than one source witness, including `कुकुर`, `माछु`, `किदलु`, `गौड़ी`,
`बल्द`, `बांदर`, `पाणी` and `घास`.

| Domain | Source-level records | Examples |
| --- | ---: | --- |
| Animals | 121 | `कुकुर` dog, `माछु` fish, `गुर्रो` snake, `घ्वीड़` deer |
| Birds | 17 | `चखुल` bird, `घुघती` pigeon, `घिण्ड्यूड़ी` sparrow, `मुणाल` monal |
| Insects | 36 | `माख` fly, `किर्मव्ल` ant, `म्वारा` honeybee |
| Instruments | 5 | `ढोल`, `दमाऊ`, `मंजीरा`, `झांझर`, `भंकोरा` |
| Occupations | 65 | `ग्वेर` cowherd, `मछोई` fisher, `ल्वार` blacksmith, `औजी` musician/tailor |
| Body and kinship/people | 59 | `कन्दूड़` ear, `जिकुड़ि` heart, `बुबा` father |
| Nature and plants | 46 | `डाळु` tree, `बोण` forest, `घस्यूड़` grass, `ह्यूं` snow |
| Food, objects, clothing, land, agriculture and ritual culture | 91 | Regional glossary terms with English explanations |
| Other basic and local cultural vocabulary | 226 | General words and regional glossary entries |

## Sources and treatment

- The rendered English Wiktionary Garhwali Swadesh table contributed 203
  variant records under CC BY-SA 4.0.
- The Uttarakhandi Words and E-Magazine of Uttarakhand animal/bird lists
  contributed 165 records. Their Garhwali column was kept separate from the
  Kumaoni column.
- A GarhwaliLanguage.com Hindi–Garhwali table contributed 35 records.
- An attributed occupation list based on the Ramakant Benjwal and Beena
  Benjwal dictionary contributed 65 records.
- The Panos London Mountain Voices glossary contributed 193 Roman-script
  regional terms. The source labels these as Garhwali/Hindi and does not
  separate the two, so every one carries an explicit language-identity review
  flag.
- A Press Information Bureau publication on Ramman supplied five instrument
  names with descriptions.

All community and modern publisher material stays in the restricted research
layer when the page does not state reusable-content terms. None of these 666
records is training eligible yet. Source spellings, variant forms, confidence,
rights status and review flags are retained. A native speaker should confirm
dialect, spelling, meaning and whether broad regional terms are specifically
Garhwali before promotion.

## Artifacts

- `research/garhwali-thematic-lexicon.json`: readable master lexicon with all
  source metadata and semantic domains.
- `restricted/thematic_web_lexicon.jsonl`: pipeline-compatible records.
- Raw public responses and immutable metadata pointers are stored below
  `sources/online/themed_vocabulary/` and excluded from Git by policy.
- The reproducible acquire/extract implementation is the ninth wave in
  `scripts/collect_online.py` and `scripts/ingestion_graph.py`.
