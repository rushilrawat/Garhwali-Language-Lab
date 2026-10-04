#!/usr/bin/env python3
"""Profile local Internet Archive OCR records and media without changing them."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OCR_DIRS = (
    Path("data/extracted/research/internet_archive_language_studies_2026-10-03"),
    Path("data/extracted/research/internet_archive_reference_books_2026-10-03"),
)
REPORT_PATH = Path("data/extracted/research/internet_archive_quality_audit_2026-10-04.json")
MEDIA_EXTENSIONS = {".mp3", ".mp4"}
REPEATED_CHARACTER = re.compile(r"(.)\1{3,}", re.DOTALL)


def profile_text(text: str) -> dict:
    """Return script and OCR-warning signals; these are not language judgments."""
    letters = Counter()
    controls = format_chars = joiners = replacements = digits = symbols = 0
    repeated = bool(REPEATED_CHARACTER.search(text))
    for char in text:
        category = unicodedata.category(char)
        codepoint = ord(char)
        if category.startswith("L"):
            if 0x0900 <= codepoint <= 0x097F:
                letters["Devanagari"] += 1
            elif "LATIN" in unicodedata.name(char, ""):
                letters["Latin"] += 1
            else:
                letters["Other"] += 1
        elif category == "Nd":
            digits += 1
        elif category == "Cc" and char not in "\r\n\t":
            controls += 1
        elif category == "Cf":
            if codepoint in {0x200C, 0x200D}:
                joiners += 1
            else:
                format_chars += 1
        elif category == "So" or category == "Co":
            symbols += 1
        if char == "\ufffd":
            replacements += 1

    letter_total = sum(letters.values())
    if not letter_total:
        script = "no_letters"
    elif letters["Devanagari"] / letter_total >= 0.7 and letters["Latin"] / letter_total < 0.1:
        script = "mostly_devanagari"
    elif letters["Latin"] / letter_total >= 0.7 and letters["Devanagari"] / letter_total < 0.1:
        script = "mostly_latin"
    elif letters["Devanagari"] / letter_total >= 0.1 and letters["Latin"] / letter_total >= 0.1:
        script = "mixed_devanagari_latin"
    else:
        script = "other_or_unclear"

    char_count = len(text)
    digit_ratio = digits / max(1, letter_total + digits)
    symbol_ratio = symbols / max(1, char_count)
    warnings = []
    if replacements:
        warnings.append("replacement_character")
    if controls:
        warnings.append("control_character")
    if format_chars:
        warnings.append("unexpected_unicode_format_character")
    if digit_ratio > 0.20:
        warnings.append("high_digit_ratio")
    if symbol_ratio > 0.10:
        warnings.append("high_symbol_ratio")
    if repeated:
        warnings.append("repeated_character_run")

    return {
        "characters": char_count,
        "words": len(text.split()),
        "script_profile": script,
        "script_letter_counts": dict(letters),
        "replacement_characters": replacements,
        "control_characters": controls,
        "format_characters": format_chars,
        "orthographic_joiners": joiners,
        "warning_flags": warnings,
    }


def read_ocr_records(root: Path) -> tuple[list[dict], list[str]]:
    records = []
    errors = []
    for relative_dir in OCR_DIRS:
        directory = root / relative_dir
        for path in sorted(directory.glob("*.jsonl")):
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict) or not isinstance(row.get("text"), str):
                        raise ValueError("expected a record object with string text")
                    records.append({"path": path, "line": line_number, "row": row})
                except (json.JSONDecodeError, ValueError) as exc:
                    errors.append(f"{path.relative_to(root)}:{line_number}: {exc}")
    return records, errors


def profile_ocr(records: list[dict]) -> dict:
    per_source = defaultdict(lambda: {
        "records": 0,
        "nonempty_records": 0,
        "characters": 0,
        "lengths": [],
        "scripts": Counter(),
        "language_labels": Counter(),
        "titles": Counter(),
        "rights_statuses": Counter(),
        "warning_rows": Counter(),
        "training_eligible_true": 0,
        "public_redistribution_eligible_true": 0,
    })
    all_hashes = Counter()
    record_ids = Counter()
    global_scripts = Counter()
    warning_rows = Counter()
    char_total = empty = joiner_char_total = 0
    missing_record_ids = missing_source_ids = missing_text_hashes = 0
    for item in records:
        row = item["row"]
        source_id = str(row.get("source_id") or item["path"].stem)
        text = row.get("text_normalized") or row["text"]
        profile = profile_text(text)
        source = per_source[source_id]
        source["records"] += 1
        source["nonempty_records"] += bool(text.strip())
        source["characters"] += profile["characters"]
        source["lengths"].append(profile["characters"])
        source["scripts"][profile["script_profile"]] += 1
        source["language_labels"][str(row.get("language") or "unlabeled")] += 1
        source["titles"][str(row.get("title") or "unlabeled")] += 1
        source["rights_statuses"][str(row.get("rights_status") or "unlabeled")] += 1
        source["training_eligible_true"] += row.get("training_eligible") is True
        source["public_redistribution_eligible_true"] += row.get("public_redistribution_eligible") is True
        for warning in set(profile["warning_flags"]):
            source["warning_rows"][warning] += 1
            warning_rows[warning] += 1
        joiner_char_total += profile["orthographic_joiners"]
        global_scripts[profile["script_profile"]] += 1
        char_total += profile["characters"]
        empty += not text.strip()
        all_hashes[str(row.get("text_sha256") or text)] += 1
        missing_record_ids += not bool(row.get("record_id"))
        missing_source_ids += not bool(row.get("source_id"))
        missing_text_hashes += not bool(row.get("text_sha256"))
        if row.get("record_id"):
            record_ids[str(row["record_id"])] += 1

    sources = {}
    for source_id, value in sorted(per_source.items()):
        lengths = sorted(value.pop("lengths"))
        sources[source_id] = {
            **value,
            "median_characters": lengths[len(lengths) // 2] if lengths else 0,
            "script_profiles": dict(sorted(value["scripts"].items())),
            "language_labels": dict(sorted(value["language_labels"].items())),
            "titles": dict(sorted(value["titles"].items())),
            "rights_statuses": dict(sorted(value["rights_statuses"].items())),
            "ocr_warning_rows": dict(sorted(value["warning_rows"].items())),
        }
        del sources[source_id]["scripts"]
        del sources[source_id]["warning_rows"]

    duplicate_text_rows = sum(count - 1 for count in all_hashes.values() if count > 1)
    return {
        "records": len(records),
        "exact_unique_texts": len(all_hashes),
        "exact_duplicate_text_rows_within_intake": duplicate_text_rows,
        "duplicate_record_id_rows": sum(count - 1 for count in record_ids.values() if count > 1),
        "empty_text_rows": empty,
        "missing_record_id_rows": missing_record_ids,
        "missing_source_id_rows": missing_source_ids,
        "missing_text_hash_rows": missing_text_hashes,
        "characters": char_total,
        "script_profiles": dict(sorted(global_scripts.items())),
        "ocr_warning_rows": dict(sorted(warning_rows.items())),
        "orthographic_joiner_characters": joiner_char_total,
        "sources": sources,
        "language_classification_note": "Script profile and source-level language metadata only; this audit does not identify Garhwali versus Hindi and is not native review.",
        "ocr_confidence_note": "Archive OCR sidecars do not provide comparable page-level recognition confidence; warning flags are transparent heuristics, not OCR accuracy scores.",
    }


def probe_media(paths: list[Path], ffprobe: str = "ffprobe") -> dict:
    files = []
    failures = []
    for path in sorted(paths):
        try:
            result = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries",
                 "format=duration,size:stream=codec_type,codec_name,sample_rate,channels,width,height",
                 "-of", "json", str(path)],
                check=True, capture_output=True, text=True,
            )
            payload = json.loads(result.stdout)
            duration = float(payload.get("format", {}).get("duration", 0) or 0)
            files.append({
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "duration_seconds": duration,
                "streams": payload.get("streams", []),
            })
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as exc:
            failures.append({"path": str(path), "error": str(exc)})
    return {
        "files_found": len(paths),
        "files_probed": len(files),
        "probe_failures": failures,
        "total_playback_seconds": round(sum(row["duration_seconds"] for row in files), 3),
        "files": files,
        "content_note": "Container/stream metadata only; ffprobe does not establish that a recording contains Garhwali speech, music, or usable transcripts.",
    }


def build_report(root: Path = ROOT, ffprobe: str = "ffprobe") -> dict:
    records, errors = read_ocr_records(root)
    media_paths = [
        path for path in (root / "data/downloads").rglob("*")
        if path.is_file()
        and path.suffix.lower() in MEDIA_EXTENSIONS
        and any("internet_archive" in part.casefold() for part in path.parts)
    ]
    return {
        "audit_date": "2026-10-04",
        "purpose": "Automated, non-destructive quality profile of the local Internet Archive OCR and media intake.",
        "input_jsonl_files": len({item["path"] for item in records}),
        "parse_errors": errors,
        "ocr": profile_ocr(records),
        "media": probe_media(media_paths, ffprobe=ffprobe),
        "limits": [
            "Page script does not distinguish Garhwali from Hindi when both use Devanagari.",
            "OCR warning heuristics identify review candidates, not corrected text or measured word accuracy.",
            "Media probes establish technical readability only; speech language, speaker, transcript accuracy, clipping, and content rights remain unreviewed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--output", type=Path, default=REPORT_PATH)
    args = parser.parse_args()
    report = build_report(args.root.resolve(), args.ffprobe)
    output = args.output if args.output.is_absolute() else args.root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "ocr_records": report["ocr"]["records"],
        "exact_unique_texts": report["ocr"]["exact_unique_texts"],
        "media_probed": report["media"]["files_probed"],
        "media_failures": len(report["media"]["probe_failures"]),
    }, indent=2))
    return 1 if report["parse_errors"] or report["media"]["probe_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
