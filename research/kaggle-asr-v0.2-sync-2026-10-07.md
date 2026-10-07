# Kaggle ASR v0.2 sync — 7 October 2026

The private [Garhwali ASR reference clips](https://www.kaggle.com/datasets/rushilrawat1/garhwali-asr-reference-clips-v0-1) dataset is now at Kaggle version 2. Its live `manifest.csv` preview shows 2,718 rows and 13 columns. Kaggle's file tree shows 2,722 files: 2,718 audio files plus `manifest.csv`, `README.md`, `ATTRIBUTION.md`, and `release.json`. The new version contains only the v0.2 package; the v0.1 ZIP was removed from the proposed version. The dataset remains private, with link sharing off. Its title, subtitle, and description now reflect v0.2.

The local upload package is
`data/kaggle/garhwali-asr-reference-v0.2.zip` (437,339,932 bytes; SHA-256
`d448f7faf0eff1de34df3e17b36e0a09d432aaeb68fec05cc6985daf62c81f33`).
It follows the published Hugging Face `asr_reference` v0.2 Parquet files:
2,202 train, 373 validation, 143 test. All 2,718 audio files were checked
against their SHA-256 names. All 2,002 old Kaggle rows retain their split,
audio path, hash, and transcript; 716 already-existing VAANI references were
added. No new recording or transcript was created. The manifest also includes
source record ID, reference provenance, quality flags, district, and speaker
identity resolution without publishing raw speaker IDs or image hashes.

The [Kaggle baseline notebook](https://www.kaggle.com/code/rushilrawat1/garhwali-asr-baseline-reference-labels) was updated to expect the v0.2 counts and ZIP, and its attached dataset input was changed from version 1 to version 2. Kaggle notebook version 3 was saved successfully as a source-only quick save. The notebook was not rerun, and no new model result is claimed. The local notebook generator and notebook match this input.
