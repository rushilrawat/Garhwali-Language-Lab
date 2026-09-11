# VAANI Garhwali metadata audit

Audit date: 2026-09-09  
License: CC BY 4.0  
Method: authenticated, column-pruned reads of the Hugging Face Dataset Viewer Parquet exports. The `audio.path` leaf was read for identity reconciliation; the `audio.bytes` leaf was excluded. No bulk audio was downloaded.

## Current exact counts

### `ARTPARK-IISc/Vaani`, config `Garhwali`

- Revision: `fe12c49bc61c083d5bb2092513fb6ec2e7ae72ee`
- Split: train, 110,410 utterances
- Summed duration: 487,702.928 seconds, or **135.473036 hours**
- `isTranscriptionAvailable=Yes`: 5,868
- Non-empty transcript: 5,868
- Unique WAV paths: 110,410
- Unique non-placeholder speaker IDs: 363
- Rows whose speaker ID is `NA`: 89,387. The speaker count therefore covers only identified speakers and is not a count of every real speaker.

District rows and durations:

| District | Rows | Hours |
|---|---:|---:|
| TehriGarhwal | 35,867 | 49.539369 |
| Uttarkashi | 74,543 | 85.933667 |
| **Total** | **110,410** | **135.473036** |

Gender distribution:

| Gender | Rows |
|---|---:|
| Female | 43,109 |
| Male | 67,301 |

The repository card reports 136.800 hours (50.024 Tehri Garhwal + 86.776 Uttarkashi). The current row-level `duration` values sum to 135.473036 hours, 1.326964 hours lower. This report uses the values in the pinned current revision and records the card figure as a documented discrepancy.

### `ARTPARK-IISc/Vaani-transcription-part`, config `Garhwali`

- Revision: `d2acadff1ccce766d127c11b1a157251460dd68a`
- Train: 4,778
- Validation: 666
- Test: 450
- Total: **5,894**
- Non-empty transcripts: 5,894
- Unique WAV paths: 5,894

| Field | Value counts |
|---|---|
| District | TehriGarhwal 4,000; Uttarkashi 1,894 |
| Gender | Female 2,161; Male 3,733 |

## How the repositories relate

The transcription repository is a transcribed subset/export of VAANI, but it is not an exact subset of the current main Garhwali configuration:

- 5,868 WAV filenames occur in both repositories.
- Those 5,868 filenames are exactly the rows marked `Yes` and carrying non-empty transcripts in the main repository.
- The transcription repository has 26 additional WAV filenames that are absent from the current main configuration: 23 train, one validation, and two test rows; 17 are labelled TehriGarhwal and nine Uttarkashi.
- The main repository has 104,542 untranscribed WAVs that do not occur in the transcription repository.
- There are no duplicate WAV filenames within either repository.

For the 5,868 shared WAVs, 5,126 transcript strings match after whitespace and case normalization. Another 736 differ only because the transcription repository adds closing `</pause>` tags. Six have other annotation or text differences. Eight supervised rows contain Bengali script under the Garhwali label; one is also among the six cross-repository disagreements. These rows retain explicit script flags while remaining in the active experimental supervised view. The transcription repository should therefore be treated as a related, partly revised transcript release rather than blindly appended to the main transcript column.

The shared transcribed WAVs total 31,561.176 seconds, or **8.766993 hours**, using durations from the main repository. The 26 transcription-only rows have no public duration field in the transcription repository, so their duration cannot be added without reading their audio.

## Saved artifacts

All generated dataset artifacts are under the ignored `data/vaani/` directory:

- `garhwali-main-metadata.jsonl`: 110,410 metadata rows
- `garhwali-transcriptions.jsonl`: 5,894 transcript rows
- `summary.json`: counts, distributions, repository revisions, hashes, and reconciliation
- `provenance.json`: source URLs, schemas, extraction method, exclusions, and license
- `audio-path-reconciliation.json`: filename-level overlap results

Every manifest row records repository ID, pinned revision, config, split, row index, and CC BY 4.0 license. The manifests store stable WAV paths but no WAV content or temporary signed URLs.

Reproduce the audit with:

```bash
HF_HOME="$PWD/.cache/huggingface" /opt/anaconda3/bin/python scripts/audit_vaani.py
```

The audit intentionally selects metadata leaves and `audio.path`; it does not select `audio.bytes`.

The remaining acquisition and preparation steps are tracked in `research/vaani-full-use-plan.md`.
