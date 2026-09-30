#!/usr/bin/env python3
"""Convert a pinned, static Garhwali language-library snapshot into corpus rows."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "garhwali-language-library"
SOURCE_REVISION = "46564fab21299512c104e7b0cbf8bd3064285efd"
SOURCE_VERSION = "1.0.0"
SOURCE_REPOSITORY = "https://github.com/infoakshatsinghbisht-eng/garhwali-language-library"
SOURCE_RAW_BASE = f"https://raw.githubusercontent.com/infoakshatsinghbisht-eng/garhwali-language-library/{SOURCE_REVISION}/garhwali/lexicon/data"
RIGHTS_EVIDENCE = "https://pypi.org/project/garhwali/1.0.0/"
LICENSE_URL = "https://opensource.org/license/mit/"
RAW_DIR = Path("data/downloads/garhwali_language_library") / SOURCE_REVISION
OUTPUT = Path("corpus/garhwali_language_library.jsonl")
OUTPUT_MANIFEST = Path("corpus/garhwali_language_library_manifest.json")

SOURCE_FILES = {
    "words.json": ("lexicon", "garhwali", "english"),
    "phrases.json": ("phrase", "garhwali", "english"),
    "proverbs.json": ("proverb", "pakhana", "meaning"),
    "riddles.json": ("riddle", "aana", "english_hint"),
}
EXPECTED_GIT_BLOB_SHA1 = {
    "words.json": "ee3c3b5f974bba8e2c4eac887bb7d6096d9d76e1",
    "phrases.json": "86200850bec1af210001af400f748f8fc24757dd",
    "proverbs.json": "d40448e532ef5b1aa765d84123cacda95b7103f9",
    "riddles.json": "0f0892a2539761911b685cf10027565ce5a4fc5b",
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def sha256(text: str | bytes) -> str:
    data = text.encode("utf-8") if isinstance(text, str) else text
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def read_snapshot(raw_dir: Path = ROOT / RAW_DIR) -> tuple[dict, dict]:
    snapshot = json.loads((raw_dir / "snapshot-manifest.json").read_text(encoding="utf-8"))
    if snapshot.get("revision") != SOURCE_REVISION:
        raise ValueError("Garhwali Language Library snapshot revision does not match the pinned source")
    payloads = {}
    for filename, expected_git_sha in EXPECTED_GIT_BLOB_SHA1.items():
        data = (raw_dir / filename).read_bytes()
        if git_blob_sha1(data) != expected_git_sha:
            raise ValueError(f"Pinned upstream Git blob checksum mismatch: {filename}")
        payload = json.loads(data.decode("utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Expected a JSON array in {filename}")
        payloads[filename] = payload
    return payloads, snapshot


def records_from_payloads(payloads: dict, retrieved_at: str) -> list[dict]:
    records = []
    for filename, (kind, text_key, english_key) in SOURCE_FILES.items():
        rows = payloads.get(filename)
        if not isinstance(rows, list):
            raise ValueError(f"Missing source rows for {filename}")
        for index, row in enumerate(rows, start=1):
            original = row.get(text_key)
            text = normalize(original) if isinstance(original, str) else ""
            if not text:
                raise ValueError(f"{filename} row {index} has no Garhwali form")
            hindi_gloss = row.get("hindi")
            record = {
                "record_id": f"{SOURCE_ID}:{kind}:{index:04d}",
                "source_id": SOURCE_ID,
                "source_url": f"{SOURCE_RAW_BASE}/{filename}",
                "source_revision": SOURCE_REVISION,
                "source_file": filename,
                "source_version": SOURCE_VERSION,
                "retrieved_at": retrieved_at,
                "text_original": original,
                "text_normalized": text,
                "text_sha256": sha256(text),
                "iso_639_3": "gbm",
                "language": "Garhwali",
                "language_scope": "upstream-labeled; not independently language-reviewed",
                "script": "Deva" if any("\u0900" <= char <= "\u097f" for char in text) else "Latn",
                "genre": kind,
                "license": "MIT",
                "license_id": "MIT",
                "license_url": LICENSE_URL,
                "attribution": "Akshat Singh Bisht, Garhwali Language Library 1.0.0, pinned upstream source revision.",
                "rights_status": "licensed",
                "rights_evidence": RIGHTS_EVIDENCE,
                "native_reviewed": False,
                "quality_status": "upstream-authored; native review deferred",
                "training_eligible": False,
                "experimental_training_eligible": True,
                "corpus_layer": "open_experimental",
                "english_gloss": row.get(english_key) or "",
                "gloss_hi": hindi_gloss or "",
                "category": row.get("category") or kind,
                "quality_flags": [
                    "upstream_labeled_garhwali",
                    "language_identity_not_independently_verified",
                    "native_review_deferred",
                    "not_eligible_for_recommended_training",
                ],
            }
            if kind == "proverb":
                record["literal"] = row.get("literal") or ""
            if kind == "riddle":
                record["solution"] = row.get("solution") or ""
                record["english_hint"] = row.get("english_hint") or ""
            if kind == "phrase":
                record["audio_hint"] = row.get("audio_hint") or ""
            if kind == "lexicon":
                record["pos"] = row.get("pos") or ""
                record["gender"] = row.get("gender") or ""
                record["dialect_variants"] = row.get("dialect_variants") or {}
            records.append(record)
    return records


def existing_hashes(canonical_path: Path, own_source_id: str = SOURCE_ID) -> set[str]:
    if not canonical_path.exists():
        return set()
    result = set()
    with canonical_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if any(item.get("source_id") != own_source_id for item in row.get("provenance", [])):
                result.add(row["text_sha256"])
    return result


def summary(records: list[dict], preexisting_hashes: set[str]) -> dict:
    unique_hashes = {row["text_sha256"] for row in records}
    counts = Counter(row["genre"] for row in records)
    overlap = unique_hashes & preexisting_hashes
    return {
        "source_records": len(records),
        "records_by_type": dict(sorted(counts.items())),
        "unique_surface_forms": len(unique_hashes),
        "duplicate_source_rows": len(records) - len(unique_hashes),
        "exact_overlap_with_existing_unique_forms": len(overlap),
        "exact_new_unique_forms": len(unique_hashes) - len(overlap),
        "native_reviewed_records": 0,
        "recommended_training_eligible_records": 0,
        "experimental_training_eligible_records": len(records),
    }


def ingest(root: Path = ROOT) -> dict:
    raw_dir = root / RAW_DIR
    payloads, snapshot = read_snapshot(raw_dir)
    records = records_from_payloads(payloads, snapshot["retrieved_at"])
    metrics = summary(records, existing_hashes(root / "data/processed/text/canonical.jsonl"))
    output = root / OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records),
        encoding="utf-8",
    )
    source_hashes = snapshot.get("source_file_sha256", {})
    manifest = {
        "source": "Garhwali Language Library static word/phrase/proverb/riddle files",
        "source_id": SOURCE_ID,
        "source_url": SOURCE_REPOSITORY,
        "source_revision": SOURCE_REVISION,
        "source_version": SOURCE_VERSION,
        "license_id": "MIT",
        "license_url": LICENSE_URL,
        "rights_evidence_url": RIGHTS_EVIDENCE,
        "retrieved_at": snapshot["retrieved_at"],
        "source_file_sha256": source_hashes,
        "source_git_blob_sha1": EXPECTED_GIT_BLOB_SHA1,
        "output_file": str(OUTPUT),
        "output_sha256": sha256(output.read_bytes()),
        **metrics,
        "data_limitations": [
            "Only static word, phrase, proverb, and riddle entries are included; generated inflection output is not corpus data.",
            "Garhwali labels, translations, and dialect-variant labels are upstream claims and have not been independently or natively reviewed.",
            "Rows are experimental lexical/cultural evidence and are excluded from recommended model training.",
        ],
    }
    (root / OUTPUT_MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    print(json.dumps(ingest(), ensure_ascii=False, indent=2, sort_keys=True))
