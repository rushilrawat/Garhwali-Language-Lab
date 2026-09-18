#!/usr/bin/env python3
"""Model-check reversible spelling/OCR proposals without applying them."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import propose_text_cleanup as cleanup


def proposed_text(row):
    text = row.get("text_original") or row.get("original_text", "")
    changed = text
    applied = []
    for candidate in row.get("spelling_candidates", []):
        observed, replacement = candidate.get("observed"), candidate.get("candidate")
        if observed and replacement and observed in changed:
            changed = changed.replace(observed, replacement, 1)
            applied.append({"observed": observed, "candidate": replacement})
    return changed, applied


def classify(deltas):
    support = sum(delta <= -0.5 for delta in deltas)
    reject = sum(delta >= 0.5 for delta in deltas)
    if support > len(deltas) / 2:
        return "model_supported_proposal", "high" if support == len(deltas) else "medium"
    if reject > len(deltas) / 2:
        return "model_rejects_proposal", "high" if reject == len(deltas) else "medium"
    return "inconclusive", "low"


def run(input_path: Path, output_dir: Path, model_path: Path, device="cuda", seeds=(17, 29, 43),
        adapter_path=None, ocr_only=False):
    rows = list(cleanup.read_jsonl(input_path))
    candidates = []
    for row in rows:
        if ocr_only and "ocr_source_priority" not in row.get("proposal_types", []):
            continue
        text, changes = proposed_text(row)
        original = row.get("text_original") or row.get("original_text", "")
        if changes and text != original:
            key = row.get("text_sha256")
            candidates.append((row, text, changes, key))
    originals = [{"text_sha256": key, "text": row.get("text_original") or row.get("original_text", "")} for row, _, _, key in candidates]
    proposals = [{"text_sha256": key, "text": text} for _, text, _, key in candidates]
    scores = {}
    metadata = []
    for seed in seeds:
        original_scores, original_meta = cleanup.score_with_masked_lm(
            originals, model_path=model_path, device=device, seed=seed,
            adapter_path=adapter_path,
        )
        proposed_scores, proposed_meta = cleanup.score_with_masked_lm(
            proposals, model_path=model_path, device=device, seed=seed,
            adapter_path=adapter_path,
        )
        scores[seed] = (original_scores, proposed_scores)
        metadata.append({"seed": seed, "original": original_meta, "proposed": proposed_meta})
    output_dir.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    with (output_dir / "validated_proposals.jsonl").open("w", encoding="utf-8") as handle:
        for row, text, changes, key in candidates:
            seed_scores = []
            for seed in seeds:
                before, after = scores[seed][0].get(key), scores[seed][1].get(key)
                if before is not None and after is not None:
                    seed_scores.append({"seed": seed, "original_loss": before,
                                        "proposed_loss": after,
                                        "loss_delta": round(after - before, 6)})
            deltas = [item["loss_delta"] for item in seed_scores]
            status, confidence = classify(deltas)
            counts[status] += 1
            handle.write(json.dumps({
                "text_sha256": key, "original_text": row.get("text_original") or row.get("original_text", ""),
                "proposed_text": text, "changes": changes,
                "seed_scores": seed_scores, "mean_loss_delta": (
                    round(sum(deltas) / len(deltas), 6) if deltas else None
                ), "status": status, "confidence": confidence,
                "application": "proposal_only", "provenance": row.get("provenance", []),
            }, ensure_ascii=False, sort_keys=True) + "\n")
    report = {
        "run_id": "garhwali-ocr-spelling-validation-v0.1",
        "input_priority_records": len(rows), "scored_candidate_records": len(candidates),
        "decisions": dict(sorted(counts.items())), "seeds": list(seeds),
        "ocr_only": ocr_only, "adapter_path": str(adapter_path) if adapter_path else None,
        "model_runs": metadata,
        "policy": {"originals_preserved": True, "automatic_application": False,
                   "native_review_required": True},
    }
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--seeds", default="17,29,43")
    parser.add_argument("--adapter-path", type=Path)
    parser.add_argument("--ocr-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(
        args.input, args.output, args.model_path, args.device,
        tuple(int(seed) for seed in args.seeds.split(',')),
        adapter_path=args.adapter_path, ocr_only=args.ocr_only,
    ), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
