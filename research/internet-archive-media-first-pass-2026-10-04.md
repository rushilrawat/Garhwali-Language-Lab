# Internet Archive media technical first pass — 2026-10-04

## Result

The local, source-linked inventory contains **39 media files across 31
Internet Archive items**. Every candidate was re-hashed and compared with its
captured file size and `ffprobe` stream/duration record. All **39/39 passed**;
there are no validation errors and no exact duplicate SHA-256 groups. This is a
technical identity check, not a language or content review.

| Measure | Verified result |
| --- | ---: |
| Local files / Archive item identifiers | 39 / 31 |
| Combined size | 4,379,507,956 bytes (4.38 GB / 4.08 GiB) |
| Playback duration | 50,965.531 seconds (14:09:25.531; 14.15709 hours) |
| Audio-only MP3 / video with audio | 15 / 24 |
| Files with an audio stream / stereo streams | 39 / 39 |
| Audio sample rate, 44.1 kHz / 48 kHz | 13 / 26 |
| H.264 video, 640×480 / 1920×1080 / 320×180 | 16 / 7 / 1 |
| Exact duplicate file-hash groups | 0 |
| Passed technical identity/probe checks | 39 / 39 |
| Source transcript/caption sidecars found | 0 |
| Local machine drafts matched to source audio | 1 / 39 (unreviewed) |

The 14:09:25.531 is total playback time, **not** measured Garhwali speech
time. All 39 assets remain marked `not_reviewed_for_language_or_content` in
the source inventory. No language identification, listening review, or rights
clearance was performed. Captured
rights claims are mixed: 21 files have no reuse-license claim recorded; 10
claim CC BY-NC, 1 claims CC BY-NC-ND, and 7 claim CC BY. The seven CC-BY files
belong to an Archive item whose separate `rights` field conflicts with its
CC-BY-SA license URL. These remain source metadata claims, not verified reuse
permission.

The 31 captured Archive metadata snapshots list **1,047 files**. None has a
transcript/caption filename or format marker, and a local directory scan found
**0 matching transcript/caption sidecar files**. The Archive `language` field
explicitly includes Garhwali on 6 of the 31 items (one folk-song item and five
Joshi Math volumes); one other item has the generic value `mul`, and 24 have no
language value. These are unverified catalog claims, not language labels for
individual files or segments.

## Reproduction

From the repository root, run:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_archive_media_first_pass.py
PYTHONPATH=scripts .venv/bin/python -m unittest tests.test_audit_archive_media_first_pass -v
```

The command checks candidate paths stay inside the project, file SHA-256 and
size, duration within 0.01 seconds, stream metadata, probe coverage, and exact
file-hash duplicates. It separately records source-provided transcript status
and local machine drafts matched by audio hash, without copying transcript
text into the technical audit. The 39-row machine report is generated under
Git-ignored `data/extracted/research/`. The test suite covers valid
aggregation, hash/duration mismatch, escaped paths, and draft/source status
separation.

## Limits and next action

The source sidecar check found no supplied transcripts. A separate local pilot
then ran the existing `whisper-tiny-garhwali-v0.2` checkpoint, using the
repository-pinned PyTorch/Transformers dependencies, on **27.481 seconds** from
`1-salut-anglais-garhwali`. CPU inference produced a 100-character repetitive
machine draft in 2.083 seconds. The draft has no reference transcript, so no
WER/CER can be computed and this does not verify the recording's language. The
saved checkpoint's prior 112-row test report gives 74.3% WER and 40.4% CER;
these are historical project results, not independent accuracy claims. The
pilot output is stored locally at the Git-ignored
`data/extracted/research/internet_archive_asr_pilot_2026-10-04.json`, with
`training_eligible=false` and `public_redistribution_eligible=false`.

The pilot proves local inference can run, but this checkpoint is not suitable
for bulk transcript generation as a quality improvement. No alternative
general Whisper-tiny checkpoint is cached locally, and no new model weights
were downloaded. **The Garhwali speech amount and number of usable transcripts
remain unknown.** Next, identify a better independently scored local ASR option
or stop at this flagged draft layer; do not present its output as verified
Garhwali or publish media/transcripts without an applicable reuse basis.
