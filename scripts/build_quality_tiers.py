#!/usr/bin/env python3
"""Build evidence-based quality tiers without rewriting source values."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/model_ready/quality_v2"


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def text_quality_decision(row):
    reasons = []
    language = row.get("language_quality") or {}
    quality = row.get("quality") or {}
    text = (row.get("text_model") or row.get("text_clean") or row.get("text") or "").strip()
    if not text:
        reasons.append("empty_text")
    if row.get("language_bucket") != "garhwali_candidate":
        reasons.append("not_garhwali_candidate")
    if language.get("confidence") != "high":
        reasons.append("language_confidence_not_high")
    if language.get("review_required"):
        reasons.append("language_review_required")
    if quality.get("quality_band") == "low":
        reasons.append("low_surface_quality")
    if row.get("cleanup_review_flags") or row.get("deep_cleanup_flags"):
        reasons.append("cleanup_review_required")
    if not row.get("any_training_eligible_source"):
        reasons.append("no_rights_cleared_training_source")

    if not reasons:
        tier = "strict_gold_candidate"
    elif "empty_text" in reasons:
        tier = "unusable_empty"
    elif "not_garhwali_candidate" in reasons:
        tier = "non_strict_context"
    elif reasons == ["no_rights_cleared_training_source"]:
        tier = "high_quality_local_only"
    else:
        tier = "experimental_review"
    return {"tier": tier, "reasons": reasons, "value_changed": False}


def supervised_quality_decision(row):
    reasons = []
    target = (row.get("asr_target") or "").strip()
    audio = row.get("audio_quality") or {}
    if not target:
        reasons.append("empty_transcript")
    if row.get("language") != "Garhwali":
        reasons.append("source_language_not_garhwali")
    if row.get("quality_flags") or row.get("training_quality_flags") or row.get("transcript_review_flags"):
        reasons.append("existing_review_flag")
    if not audio.get("readable"):
        reasons.append("unreadable_audio")
    if audio.get("sample_rate_hz") != 16000 or audio.get("channels") != 1:
        reasons.append("noncanonical_audio_format")
    if audio.get("clipped_sample_share", 0) > 0.001:
        reasons.append("material_clipping")
    if not row.get("recommended_for_supervised_training"):
        reasons.append("not_recommended_for_supervised_training")
    if not row.get("license"):
        reasons.append("missing_license")
    return {
        "tier": "strict_gold_candidate" if not reasons else "experimental_review",
        "reasons": reasons,
        "value_changed": False,
    }


def draft_quality_decision(row):
    transcript = (row.get("machine_transcript") or "").strip()
    quality = row.get("machine_transcript_quality") or {}
    reasons = list(quality.get("flags") or [])
    if not transcript:
        reasons.append("empty_machine_transcript")
    if quality.get("level") == "high_risk":
        reasons.append("machine_draft_high_risk")
    confidence = row.get("recovery_confidence") or {}
    if confidence and confidence.get("confidence_band") in {"low", "very_low"}:
        reasons.append("low_cross_model_confidence")
    tier = "machine_draft_review" if reasons else "machine_draft_experimental"
    return {"tier": tier, "reasons": sorted(set(reasons)), "value_changed": False}


def tier_rows(source, decision):
    counts = Counter()
    reason_counts = Counter()
    rows = []
    for row in read_jsonl(source):
        quality = decision(row)
        enriched = dict(row)
        enriched["quality_v2"] = quality
        rows.append(enriched)
        counts[quality["tier"]] += 1
        reason_counts.update(quality["reasons"])
    return rows, counts, reason_counts


def summarize(counts, reasons):
    total = sum(counts.values())
    return {
        "records": total,
        "tiers": dict(sorted(counts.items())),
        "tier_rates": {key: round(value / total, 6) if total else 0 for key, value in sorted(counts.items())},
        "reason_counts": dict(sorted(reasons.items(), key=lambda item: (-item[1], item[0]))),
    }


def main():
    sources = {
        "text": (ROOT / "data/processed/model_ready/language_quality/text.jsonl", text_quality_decision),
        "supervised_speech": (ROOT / "data/processed/model_ready/transcripts/supervised.jsonl", supervised_quality_decision),
        "machine_drafts": (ROOT / "data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl", draft_quality_decision),
    }
    report = {
        "method": "Evidence-only tiering; original and cleaned values are preserved byte-for-byte.",
        "strict_policy": "Strict candidates require strong language evidence, clean structure, compatible training rights, and no active review flags.",
        "datasets": {},
    }
    for name, (source, decision) in sources.items():
        rows, counts, reasons = tier_rows(source, decision)
        write_jsonl(OUT / f"{name}.jsonl", rows)
        report["datasets"][name] = summarize(counts, reasons)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
