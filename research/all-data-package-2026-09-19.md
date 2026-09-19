# Complete all-data package — 2026-09-19

This is the current report for the access-controlled `all-data` Hugging Face
profile. It preserves every collected text value and all experimental speech
hypotheses with source, rights, quality, and review metadata. It is not cleared
for public redistribution as a whole.

## Verified contents

| Layer | Rows |
| --- | ---: |
| Prepared text segments | 114,064 |
| Exact-unique source-text catalog | 28,755 |
| Catalog texts redacted | 0 |
| Human VAANI ASR records | 5,894 |
| Unique SraVaani draft audio identities | 104,534 |
| Lexicon | 1,114 |
| Instructions | 3,230 |
| Structured knowledge | 216 |
| **Total exported rows** | **257,807** |

The eight repeated SraVaani source rows collapse to unique audio hashes while
retaining `source_audio_records`. The 104,542 source draft rows therefore map to
104,534 exported audio identities. Thirty-four empty machine hypotheses remain
present with explicit quality flags; none is represented as human ground truth.

Every source text retains its original rights status. The separately generated
public profile contains 146,912 rows and redacts text for 24,560 catalog records
without a compatible public rights basis. The private upload plan is checksum
bound and rejects a public visibility setting for the all-data profile.

## Reproduce and verify

```bash
bash scripts/finalize_local_release.sh
```

The command rebuilds both profiles, validates the packages, refreshes release
metadata, runs the test suite, and rebuilds the compact SHA-256 artifact bundle.
The authoritative machine-readable summary is
[`release/v0.1.0-manifest.json`](../release/v0.1.0-manifest.json).
