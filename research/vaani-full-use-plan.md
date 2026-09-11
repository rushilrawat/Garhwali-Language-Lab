# Project VAANI: remaining work for full Garhwali use

Status date: 2026-09-09

The metadata, transcripts, speech files, Garhwali-linked prompt images, restricted metadata, and canonical manifests are complete for the pinned current revisions. Remaining work is corpus cleanup, transcription of the unlabeled set, and model-ready evaluation design.

## Collection still required

1. **Main Garhwali audio — complete:** all 56 `audio/Garhwali` Parquet shards and 110,410 unique WAVs are local and verified.
2. **Transcription-only audio — complete:** the 26 WAVs absent from the main config were selectively retrieved; duplicate copies of the 5,868 shared WAVs were avoided.
3. **Prompt images — complete:** all 4,506 referenced JPEGs were selectively extracted after scanning only `image.path`; the unrelated 49.55 GB global image pack was not downloaded.
4. **Restricted metadata — complete:** `pincode` and `speakerImageHash` are stored in the ignored `restricted-metadata.jsonl` and excluded from the clean public manifest.

## Preparation required before training

- Build the canonical transcribed set by WAV path. Use the transcription repository's balanced train/validation/test split, retain both transcript versions, and record which version is selected.
- Normalize the 736 closing-`</pause>` differences. Manually review the six other disagreements.
- Retain the eight Bengali-script utterances in the experimental supervised view with explicit script flags and run broader language/script checks across all transcripts.
- Treat the 104,542 untranscribed main WAVs, totaling 126.706042 hours, as unlabeled speech. Generate draft ASR transcripts only as a derived layer and keep confidence scores; do not present them as human transcripts.
- Split training and evaluation by speaker or conservative speaker proxy. The dataset has 363 non-placeholder speaker IDs, while 89,387 rows use `NA`, so a random row split risks speaker or session leakage.
- Keep Tehri Garhwal and Uttarkashi labels. VAANI does not cover all Garhwali dialect regions, and its `Kumaoni`, `Pahadi`, and `Nepali` configs must remain separate unless language identification supports a specific reclassification.
- Preserve the CC BY 4.0 license, both pinned repository revisions, VAANI citation, source row index, WAV filename, and transformation history in every derived release.

## Recommended acquisition order

1. **Complete:** use byte-preserving extraction without audio decoding.
2. **Complete:** download and checksum the 56 main Garhwali shards.
3. **Complete:** extract WAV files and verify count, uniqueness, hashes, headers, and duration totals.
4. **Complete:** selectively retrieve the 26 transcription-only WAVs.
5. **Complete:** selectively retrieve the 4,506 referenced prompt images.
6. **Complete:** canonical supervised, flagged-experimental, unlabeled, and evaluation views exist; flags do not block local experimental use.
7. **Next:** run language identification, silence/clipping checks, transcript validation, and broader speaker/session-leakage checks before model training.

The adjacent VAANI `Kumaoni` and generic `Pahadi` configs may support multilingual comparison, but they are not part of the Garhwali corpus and should not be merged into it by name alone.
