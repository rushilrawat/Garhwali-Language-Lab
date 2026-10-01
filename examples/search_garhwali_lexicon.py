#!/usr/bin/env python3
"""Search the rights-filtered Garhwali lexicon by form or English/Hindi gloss."""

from __future__ import annotations

import argparse


DATASET = "rushilrawat/garhwali-corpus"


def searchable_text(row: dict) -> str:
    parts = [str(row.get("form") or "")]
    glosses = row.get("glosses") or {}
    if isinstance(glosses, dict):
        for value in glosses.values():
            if isinstance(value, list):
                parts.extend(str(item) for item in value)
            elif value:
                parts.append(str(value))
    return " ".join(parts).casefold()


def search(rows, query: str, limit: int = 20) -> list[dict]:
    needle = query.casefold().strip()
    if not needle:
        raise ValueError("query must contain at least one non-space character")
    matches = []
    for row in rows:
        if needle in searchable_text(row):
            matches.append(row)
            if len(matches) >= limit:
                break
    return matches


def source_citations(row: dict) -> list[str]:
    citations = []
    for item in row.get("provenance") or row.get("public_rights_basis") or []:
        if not isinstance(item, dict):
            continue
        parts = [item.get("attribution"), item.get("source_url")]
        citation = " — ".join(str(part) for part in parts if part)
        if citation and citation not in citations:
            citations.append(citation)
    return citations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Garhwali form or English/Hindi gloss")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--revision", default="main", help="Hub commit or branch")
    parser.add_argument(
        "--data-file",
        help="Local JSONL file or quoted glob; omit to stream the Hub lexicon config",
    )
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be at least 1")

    from datasets import load_dataset

    if args.data_file:
        rows = load_dataset("json", data_files=args.data_file, split="train")
    else:
        rows = load_dataset(
            DATASET, "lexicon", split="train", revision=args.revision, streaming=True
        )
    results = search(rows, args.query, args.limit)
    if not results:
        print("No matching entries.")
        return
    for row in results:
        print(f"{row.get('form', '')} — {row.get('glosses', {})}")
        print(
            "  rights: ", row.get("rights_status", "not provided"),
            " | reuse: ", row.get("reuse_scope", "inspect provenance"),
            " | quality: ", row.get("quality_status", "not provided"),
            sep="",
        )
        for citation in source_citations(row):
            print("  source: ", citation, sep="")


if __name__ == "__main__":
    main()
