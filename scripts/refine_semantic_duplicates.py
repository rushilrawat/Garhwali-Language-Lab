#!/usr/bin/env python3
"""Re-score semantic duplicate candidates without deleting or mutating text."""

import argparse
import json
import math
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sigmoid(value):
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, float(value)))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()

    from sentence_transformers import CrossEncoder

    rows = read_jsonl(args.input)
    pairs = [(row["left_text"], row["right_text"]) for row in rows]
    model = CrossEncoder(args.model, device="cuda")
    logits = model.predict(pairs, batch_size=args.batch_size, show_progress_bar=True)
    args.output.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    cross_split_supported = 0
    with (args.output / "refined_candidates.jsonl").open("w", encoding="utf-8") as handle:
        for row, logit in zip(rows, logits):
            lexical = SequenceMatcher(None, row["left_text"], row["right_text"]).ratio()
            score = sigmoid(logit)
            if lexical >= 0.98 and score >= 0.90:
                decision = "high_confidence_near_duplicate"
            elif lexical >= 0.90 and score >= 0.75:
                decision = "supported_candidate"
            elif lexical < 0.35 and score < 0.25:
                decision = "likely_false_positive"
            else:
                decision = "review_required"
            counts[decision] += 1
            cross_split_supported += int(row.get("cross_split", False) and decision in {
                "high_confidence_near_duplicate", "supported_candidate"
            })
            enriched = dict(row)
            enriched.update({
                "cross_encoder_model": args.model,
                "cross_encoder_score": round(score, 8),
                "lexical_similarity": round(lexical, 8),
                "refined_decision": decision,
                "automatic_deletion": False,
            })
            handle.write(json.dumps(enriched, ensure_ascii=False, sort_keys=True) + "\n")
    report = {
        "run_id": "garhwali-semantic-near-duplicate-refinement-v0.2",
        "input_candidate_pairs": len(rows),
        "model_id": args.model,
        "decisions": dict(sorted(counts.items())),
        "cross_split_supported_pairs": cross_split_supported,
        "records_deleted_or_mutated": 0,
        "policy": "evidence_only; preserve source records",
    }
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
