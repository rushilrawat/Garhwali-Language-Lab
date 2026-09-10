# Garhwali social-media ingestion

Updated 2026-09-10.

## Result

- Reddit: 9 exact-unique records from public language-learning discussions,
  including vocabulary lists, dialect-labelled terminology and conversational
  examples.
- YouTube: 3 Garhwali folk-story metadata records from Ghaseri. Two checked
  videos expose no machine-readable transcript through YouTube.
- Facebook: the public Ghaseri profile was catalogued, but reusable post text
  was not exposed to unauthenticated search.
- Instagram: `garhwali.bhasha`, `garhkumaon_linguist` and `dmpant31` were
  catalogued. Search results confirm their relevance, while complete captions
  were not publicly exposed for bulk collection.

The 12 text/metadata records contain 3,494 normalized characters and have zero
exact overlap with 33,906 other local text records checked during this pass.
Public community vocabulary is marked for native review because individual
posts contain spelling variants, romanization, mixed Hindi/English glosses and
explicit uncertainty from contributors.

## Storage

- `data/extracted/social_garhwali/records.jsonl`
- `data/extracted/social_garhwali/catalog.json`
- `data/extracted/social_garhwali/manifest.json`

All are under the Git-ignored `data/extracted/` tree. The reproducible seed
builder is `scripts/ingest_social_garhwali.py`.

## Access results

Reddit's unauthenticated JSON and RSS search endpoints returned HTTP 403. Public
indexed pages remained readable in a browser, so the collector retained only
relevant visible post and comment content with post URLs. This is an endpoint
access restriction rather than a rate-limit pause. Facebook and Instagram
similarly provide profile discovery but limited public bulk text without their
authenticated interfaces.

The next high-yield social layer is audio transcription: the Ghaseri folktale
videos and the already archived 66-episode Garhwali Folktales podcast. Automatic
YouTube transcript export found no transcript for the two sampled Ghaseri
videos, so audio acquisition and local speech recognition are required.
