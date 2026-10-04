#!/usr/bin/env python3
"""Find exact and high-similarity Archive OCR matches in the canonical text view.

This is a read-only candidate audit. It emits stable IDs and hashes, never text,
and does not remove or modify either source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from audit_archive_intake_quality import OCR_DIRS


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = Path("data/processed/model_ready/cleaned/text.jsonl")
OUTPUT_PATH = Path("data/extracted/research/internet_archive_corpus_overlap_2026-10-04.json")
CANDIDATE_VIEW_PATH = Path("data/extracted/research/internet_archive_candidate_views_2026-10-04/text_review_candidates.jsonl")


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(
        "".join(char if unicodedata.category(char)[0] in {"L", "M", "N"} else " " for char in text).split()
    )


def text_ngrams(text: str, size: int) -> set[str]:
    return {text[index:index + size] for index in range(len(text) - size + 1)}


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            rows.append(row)
    return rows


def read_archive_rows(root: Path) -> list[dict]:
    candidate_path = root / CANDIDATE_VIEW_PATH
    if candidate_path.is_file():
        return [
            {
                "record_id": str(row.get("record_id") or ""),
                "source_id": str(row.get("source_id") or row.get("archive_identifier") or ""),
                "text": row.get("text_normalized") or row.get("text") or "",
            }
            for row in read_jsonl(candidate_path)
        ]
    rows = []
    for relative_dir in OCR_DIRS:
        for path in sorted((root / relative_dir).glob("*.jsonl")):
            for row in read_jsonl(path):
                rows.append({
                    "record_id": str(row.get("record_id") or ""),
                    "source_id": str(row.get("source_id") or path.stem),
                    "text": row.get("text_normalized") or row.get("text") or "",
                })
    return rows


def corpus_text(row: dict) -> str:
    for key in ("text_clean", "text_model", "text", "source_text", "transcript"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def corpus_provenance_summary(row: dict) -> dict:
    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        provenance = [provenance]
    if not isinstance(provenance, list):
        provenance = []
    record_ids = sorted({str(item.get("record_id")) for item in provenance if item.get("record_id")})
    source_ids = sorted({str(item.get("source_id")) for item in provenance if item.get("source_id")})
    rights_statuses = sorted({str(item.get("rights_status")) for item in provenance if item.get("rights_status")})
    return {
        "source_record_ids": record_ids,
        "source_ids": source_ids,
        "rights_statuses": rights_statuses,
    }


def audit_overlap(
    archive_rows: list[dict],
    corpus_rows: list[dict],
    *,
    ngram_size: int = 5,
    min_chars: int = 40,
    min_jaccard: float = 0.85,
    max_archive_gram_frequency: int = 100,
) -> dict:
    if ngram_size < 1 or min_chars < ngram_size:
        raise ValueError("ngram_size must be positive and min_chars must cover it")
    if not 0 < min_jaccard <= 1:
        raise ValueError("min_jaccard must be in (0, 1]")

    prepared = []
    archive_exact = defaultdict(list)
    archive_gram_frequency = defaultdict(int)
    for row in archive_rows:
        normalized = normalize_text(row.get("text"))
        if not normalized:
            continue
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        member = {
            "record_id": row.get("record_id") or "",
            "source_id": row.get("source_id") or "",
            "normalized_text_sha256": digest,
            "characters": len(normalized),
        }
        archive_exact[normalized].append(member)
        grams = text_ngrams(normalized, ngram_size) if len(normalized) >= min_chars else set()
        index = len(prepared)
        prepared.append((member, normalized, grams))
        for gram in grams:
            archive_gram_frequency[gram] += 1

    postings = defaultdict(list)
    for index, (_member, _text, grams) in enumerate(prepared):
        for gram in grams:
            if archive_gram_frequency[gram] <= max_archive_gram_frequency:
                postings[gram].append(index)

    exact_matches = []
    archive_exact_groups = []
    for text, members in archive_exact.items():
        if len(members) > 1:
            archive_exact_groups.append({"members": members, "normalized_text_sha256": members[0]["normalized_text_sha256"]})

    for line_number, row in enumerate(corpus_rows, 1):
        normalized = normalize_text(corpus_text(row))
        if not normalized:
            continue
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        corpus_member = {
            "view": "model_ready/cleaned/text",
            "line_number": line_number,
            "record_id": str(row.get("record_id") or row.get("id") or ""),
            **corpus_provenance_summary(row),
            "text_sha256": digest,
            "characters": len(normalized),
        }
        for archive_member in archive_exact.get(normalized, []):
            exact_matches.append({"archive": archive_member, "corpus": corpus_member})

    near_matches = []
    candidate_pair_count = 0
    for line_number, row in enumerate(corpus_rows, 1):
        normalized = normalize_text(corpus_text(row))
        if len(normalized) < min_chars:
            continue
        grams = text_ngrams(normalized, ngram_size)
        shared_counts = defaultdict(int)
        for gram in grams:
            for archive_index in postings.get(gram, ()):
                archive_size = len(prepared[archive_index][2])
                largest = max(archive_size, len(grams))
                if largest and min(archive_size, len(grams)) / largest >= min_jaccard:
                    shared_counts[archive_index] += 1
        candidate_pair_count += len(shared_counts)
        corpus_digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        for archive_index, shared in shared_counts.items():
            archive_member, archive_text, archive_grams = prepared[archive_index]
            if archive_text == normalized:
                continue
            minimum_intersection = min_jaccard * (
                len(archive_grams) + len(grams)
            ) / (1 + min_jaccard)
            if shared < minimum_intersection:
                continue
            intersection = len(archive_grams & grams)
            union = len(archive_grams | grams)
            similarity = intersection / union if union else 0.0
            if similarity < min_jaccard:
                continue
            near_matches.append({
                "archive": archive_member,
                "corpus": {
                    "view": "model_ready/cleaned/text",
                    "line_number": line_number,
                    "record_id": str(row.get("record_id") or row.get("id") or ""),
                    **corpus_provenance_summary(row),
                    "text_sha256": corpus_digest,
                    "characters": len(normalized),
                },
                "shared_candidate_ngrams": shared,
                "char_ngram_jaccard": round(similarity, 8),
                "review_state": "candidate_only_unadjudicated",
            })

    near_matches.sort(key=lambda item: (-item["char_ngram_jaccard"], item["archive"]["record_id"], item["corpus"]["line_number"]))
    exact_matches.sort(key=lambda item: (item["archive"]["record_id"], item["corpus"]["line_number"]))
    return {
        "schema_version": "archive-cleaned-corpus-overlap-v1",
        "archive_rows": len(archive_rows),
        "canonical_corpus_rows": len(corpus_rows),
        "canonical_corpus_view": str(CORPUS_PATH),
        "exact": {
            "normalized_match_rows": len(exact_matches),
            "archive_rows_with_match": len({item["archive"]["record_id"] for item in exact_matches}),
            "matched_corpus_rows": len({item["corpus"]["line_number"] for item in exact_matches}),
            "within_archive_duplicate_groups": len(archive_exact_groups),
            "matches": exact_matches,
            "within_archive_groups": archive_exact_groups,
        },
        "near_duplicate": {
            "candidate_pairs_scored": candidate_pair_count,
            "threshold_pairs": len(near_matches),
            "threshold": min_jaccard,
            "method": f"NFKC-casefolded Unicode letters/marks/numbers, character {ngram_size}-gram Jaccard",
            "candidate_generation": f"archive n-grams present in no more than {max_archive_gram_frequency} archive rows; a set-length upper-bound prunes impossible threshold pairs; pairs with only more-common n-grams may be missed",
            "matches": near_matches,
            "interpretation": "Similarity candidates are not proof of duplication; absence of a candidate is not proof of no semantic or source-family overlap.",
        },
        "limits": [
            "The comparison uses the 32,072-row canonical cleaned parent-text view only; it does not compare audio, transcripts, segments, or every research index.",
            "A close OCR match can be a quotation, title, shared formula, or scan variant; no rows are removed or changed.",
            "No language-identification judgment is made; Archive source-level labels are not page-level Garhwali confirmation.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--corpus", type=Path, default=CORPUS_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    root = args.root.resolve()
    corpus_path = args.corpus if args.corpus.is_absolute() else root / args.corpus
    output = args.output if args.output.is_absolute() else root / args.output
    archive_rows = read_archive_rows(root)
    corpus_rows = read_jsonl(corpus_path)
    report = audit_overlap(archive_rows, corpus_rows)
    report["input_hashes"] = {
        "canonical_cleaned_text_sha256": hashlib.sha256(corpus_path.read_bytes()).hexdigest(),
        "archive_record_ids_sha256": hashlib.sha256(
            "\n".join(str(row.get("record_id") or "") for row in archive_rows).encode("utf-8")
        ).hexdigest(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "archive_rows": report["archive_rows"],
        "corpus_rows": report["canonical_corpus_rows"],
        "exact_match_rows": report["exact"]["normalized_match_rows"],
        "near_duplicate_pairs": report["near_duplicate"]["threshold_pairs"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
