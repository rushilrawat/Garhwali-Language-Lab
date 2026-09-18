#!/usr/bin/env python3
"""Find high-similarity text pairs without changing or deleting corpus records."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def read_rows(input_dir: Path) -> list[dict]:
    rows = []
    for split in ("train", "validation", "test"):
        with (input_dir / f"{split}.jsonl").open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    rows.append({"split": split, **row})
    return rows


def source_ids(row: dict) -> list[str]:
    return sorted({
        provenance.get("source_id") or "unknown"
        for parent in row.get("parents", [])
        for provenance in parent.get("provenance", [])
    })


def collect_pairs(rows, neighbor_indices, neighbor_scores, threshold=0.92, limit=200000):
    pairs = {}
    for left, (indices, scores) in enumerate(zip(neighbor_indices, neighbor_scores)):
        for right, score in zip(indices, scores):
            right = int(right)
            score = float(score)
            if right < 0 or left == right or score < threshold:
                continue
            a, b = sorted((left, right))
            if rows[a]["segment_sha256"] == rows[b]["segment_sha256"]:
                continue
            key = (a, b)
            pairs[key] = max(score, pairs.get(key, -1.0))
    ranked = sorted(pairs.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [{
        "left_segment_sha256": rows[a]["segment_sha256"],
        "right_segment_sha256": rows[b]["segment_sha256"],
        "left_split": rows[a]["split"],
        "right_split": rows[b]["split"],
        "cross_split": rows[a]["split"] != rows[b]["split"],
        "cosine_similarity": round(score, 8),
        "left_source_ids": source_ids(rows[a]),
        "right_source_ids": source_ids(rows[b]),
        "left_text": rows[a].get("text", "")[:500],
        "right_text": rows[b].get("text", "")[:500],
    } for (a, b), score in ranked]


def run(input_dir: Path, output_dir: Path, model_id: str, threshold: float,
        neighbors: int, limit: int, batch_size: int) -> dict:
    import faiss
    from sentence_transformers import SentenceTransformer

    rows = read_rows(input_dir)
    model = SentenceTransformer(model_id, device="cuda")
    embeddings = model.encode(
        [row.get("text", "") for row in rows], batch_size=batch_size,
        normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=True,
    ).astype("float32")
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    scores, indices = index.search(embeddings, neighbors)
    pairs = collect_pairs(rows, indices, scores, threshold, limit)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "candidates.jsonl").open("w", encoding="utf-8") as handle:
        for pair in pairs:
            handle.write(json.dumps(pair, ensure_ascii=False, sort_keys=True) + "\n")
    report = {
        "run_id": "garhwali-semantic-near-duplicate-audit-v0.1",
        "model_id": model_id,
        "records": len(rows),
        "split_records": dict(Counter(row["split"] for row in rows)),
        "threshold": threshold,
        "neighbors_per_record": neighbors,
        "candidate_pairs": len(pairs),
        "cross_split_candidate_pairs": sum(pair["cross_split"] for pair in pairs),
        "records_deleted_or_mutated": 0,
        "review_required_before_deduplication": True,
    }
    (output_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    parser.add_argument("--threshold", type=float, default=0.92)
    parser.add_argument("--neighbors", type=int, default=12)
    parser.add_argument("--limit", type=int, default=200000)
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output, args.model, args.threshold,
                         args.neighbors, args.limit, args.batch_size), indent=2))


if __name__ == "__main__":
    main()
