# VAANI Garhwali collection completion

The pinned VAANI Garhwali collection is locally complete as of 2026-09-09.

## Collected and verified

- 56 main Parquet shards: 15,466,110,561 bytes and 110,410 rows.
- 110,410 main WAVs: 15,611,311,036 bytes and 135.472682 hours from WAV headers.
- 26 transcription-only WAVs: 4,232,542 bytes and 0.036731 hours.
- Complete supervised set: 5,894 WAV/transcript pairs and 8.803724 hours.
- 4,506 referenced prompt images: 709,237,212 bytes, all valid JPEGs.
- Canonical full manifest: 110,410 rows.
- Canonical supervised manifest: 5,894 rows.
- Restricted metadata manifest: 110,410 rows, 40 non-empty pincodes, and 28,796 unique non-empty speaker-image hashes.

All 110,436 WAVs are mono, 16 kHz, 16-bit PCM. Every canonical local audio and image path exists. SHA-256 checks passed for every extracted WAV and image.

The supplied split has no speaker-image-hash overlap between train, validation, and test among the 5,868 rows that can be linked back to the main repository. Twenty-six transcription-only rows have no corresponding main speaker hash.

## Quality findings carried forward

- 5,126 shared transcripts match after whitespace and case normalization.
- 736 differ only by closing `</pause>` tags.
- Six have other annotation or text differences and are flagged for manual review.
- Eight supervised rows contain Bengali script under the Garhwali label; they retain script flags and remain active in the experimental supervised view.
- 104,542 main WAVs remain untranscribed, totaling approximately 126.706 hours.

## Local artifacts

The ignored `data/vaani/` tree occupies about 30 GB and contains source shards, extracted audio, selected images, canonical manifests, restricted metadata, checksums, and verification reports. Approximately 113 GiB remained free after collection.

The authoritative machine-readable completion result is `data/vaani/collection-verification-report.json`.
