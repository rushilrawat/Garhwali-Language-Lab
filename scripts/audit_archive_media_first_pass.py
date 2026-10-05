#!/usr/bin/env python3
"""Verify local Archive media identities and summarize technical metadata only."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES_PATH = Path(
    "data/extracted/research/internet_archive_candidate_views_2026-10-04/media_review_candidates.jsonl"
)
QUALITY_PATH = Path("data/extracted/research/internet_archive_quality_audit_2026-10-04.json")
OUTPUT_PATH = Path("data/extracted/research/internet_archive_media_first_pass_2026-10-04.json")
DURATION_TOLERANCE_SECONDS = 0.01
TRANSCRIPT_EXTENSIONS = {".ass", ".dfxp", ".lrc", ".sbv", ".scc", ".ssa", ".srt", ".sub", ".ttml", ".vtt"}
TRANSCRIPT_WORDS = ("caption", "closedcaption", "subtitle", "transcript")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def media_type(streams: list[dict]) -> str:
    has_audio = any(row.get("codec_type") == "audio" for row in streams)
    has_video = any(row.get("codec_type") == "video" for row in streams)
    if has_audio and has_video:
        return "audio+video"
    if has_audio:
        return "audio-only"
    if has_video:
        return "video-only"
    return "no audio/video stream"


def looks_like_transcript_or_caption(name: str, file_format: str = "") -> bool:
    value = f"{name} {file_format}".casefold()
    return Path(name).suffix.casefold() in TRANSCRIPT_EXTENSIONS or any(
        word in value for word in TRANSCRIPT_WORDS
    ) or "webvtt" in value or "subrip" in value or "timed text" in value


def scan_transcript_sidecars(candidate_rows: list[dict], root: Path) -> dict:
    """Check captured IA file listings and downloaded item folders for sidecars."""
    root = root.resolve()
    identifiers = {}
    for row in candidate_rows:
        identifier = str(row.get("archive_identifier") or "")
        if identifier in identifiers:
            continue
        try:
            media_path = (root / row["media_path"]).resolve()
            media_path.relative_to(root)
        except (KeyError, TypeError, ValueError, OSError):
            identifiers[identifier] = None
            continue
        identifiers[identifier] = next(
            (parent / "archive_metadata.json" for parent in media_path.parents
             if parent.is_relative_to(root) and (parent / "archive_metadata.json").is_file()),
            None,
        )

    missing = []
    errors = []
    listed_count = 0
    listing_candidates = []
    local_candidates = []
    for identifier, metadata_path in sorted(identifiers.items()):
        if metadata_path is None:
            missing.append(identifier)
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            file_rows = metadata.get("files", [])
            if not isinstance(file_rows, list):
                raise ValueError("files field is not a list")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, AttributeError) as exc:
            errors.append({"archive_identifier": identifier, "error": type(exc).__name__})
            continue

        listed_count += len(file_rows)
        for item in file_rows:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "")
            file_format = str(item.get("format") or "")
            if looks_like_transcript_or_caption(name, file_format):
                listing_candidates.append({
                    "archive_identifier": identifier,
                    "filename": name,
                    "format": file_format,
                })

        for path in metadata_path.parent.rglob("*"):
            if path.is_file() and looks_like_transcript_or_caption(path.name):
                local_candidates.append({
                    "archive_identifier": identifier,
                    "media_path": path.relative_to(root).as_posix(),
                })

    return {
        "status": "complete" if not missing and not errors else "incomplete",
        "archive_item_count": len(identifiers),
        "metadata_snapshots_found": len(identifiers) - len(missing) - len(errors),
        "listed_file_entries": listed_count,
        "archive_caption_or_transcript_candidates": listing_candidates,
        "local_caption_or_transcript_files": local_candidates,
        "items_missing_metadata": missing,
        "metadata_errors": errors,
    }


def scan_local_machine_drafts(root: Path) -> tuple[dict[str, list[dict]], int, list[dict]]:
    """Index only local draft metadata; never copy machine transcript text."""
    report_dir = root / "data" / "extracted" / "research"
    reports = sorted(report_dir.glob("internet_archive_asr_pilot_*.json")) if report_dir.is_dir() else []
    drafts_by_hash = defaultdict(list)
    errors = []
    for path in reports:
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
            digest = str(row.get("media_sha256") or "")
            if len(digest) != 64:
                raise ValueError("missing_or_invalid_media_sha256")
            drafts_by_hash[digest].append({
                "archive_identifier": row.get("archive_identifier"),
                "path": path.relative_to(root).as_posix(),
                "review_status": row.get("review_status", "not_recorded"),
                "training_eligible": row.get("training_eligible"),
                "public_redistribution_eligible": row.get("public_redistribution_eligible"),
            })
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, AttributeError) as exc:
            errors.append({"filename": path.name, "error": type(exc).__name__})
    return dict(drafts_by_hash), len(reports), errors


def build_media_report(candidate_rows: list[dict], quality_report: dict, root: Path) -> dict:
    root = root.resolve()
    sidecar_scan = scan_transcript_sidecars(candidate_rows, root)
    machine_drafts, machine_draft_report_count, machine_draft_errors = scan_local_machine_drafts(root)
    quality_rows = quality_report.get("media", {}).get("files", [])
    quality_by_path = {}
    errors = []
    for row in quality_rows:
        try:
            key = Path(row["path"]).resolve()
        except (KeyError, TypeError, OSError) as exc:
            errors.append({"code": "invalid_quality_report_path", "detail": str(exc)})
            continue
        if key in quality_by_path:
            errors.append({"code": "duplicate_quality_report_path", "path": key.relative_to(root).as_posix() if key.is_relative_to(root) else "outside_project"})
        quality_by_path[key] = row

    assets = []
    hashes = defaultdict(list)
    summary_counts = {
        "media_type_counts": Counter(),
        "rights_claim_class_counts": Counter(),
        "source_transcript_status_counts": Counter(),
        "local_machine_draft_status_counts": Counter(),
        "content_review_status_counts": Counter(),
        "stream_codec_counts": Counter(),
        "audio_sample_rate_counts": Counter(),
        "audio_channel_counts": Counter(),
        "video_resolution_counts": Counter(),
    }
    duration_by_type = Counter()
    total_bytes = total_duration = 0

    for candidate in candidate_rows:
        row_errors = []
        raw_path = candidate.get("media_path")
        try:
            path = (root / raw_path).resolve()
            relative_path = path.relative_to(root).as_posix()
        except (TypeError, ValueError, OSError):
            path = None
            relative_path = str(raw_path or "")
            row_errors.append({"code": "media_path_outside_project_root"})

        probe = quality_by_path.get(path) if path else None
        if path and not path.is_file():
            row_errors.append({"code": "media_file_missing"})
        if path and path.is_file() and probe is None:
            row_errors.append({"code": "missing_quality_probe"})

        actual_hash = actual_bytes = None
        if path and path.is_file():
            actual_bytes = path.stat().st_size
            actual_hash = sha256_file(path)
            if actual_hash != candidate.get("media_sha256"):
                row_errors.append({"code": "sha256_mismatch"})
            if candidate.get("bytes") is not None and actual_bytes != candidate.get("bytes"):
                row_errors.append({"code": "candidate_byte_count_mismatch"})

        streams = probe.get("streams", []) if probe else []
        duration = probe.get("duration_seconds") if probe else None
        if probe and actual_bytes != probe.get("size_bytes"):
            row_errors.append({"code": "quality_byte_count_mismatch"})
        if probe and duration is not None and candidate.get("duration_seconds") is not None:
            if abs(float(duration) - float(candidate["duration_seconds"])) > DURATION_TOLERANCE_SECONDS:
                row_errors.append({"code": "duration_mismatch"})
        if probe and candidate.get("streams") and candidate["streams"] != streams:
            row_errors.append({"code": "stream_metadata_mismatch"})

        kind = media_type(streams)
        if actual_hash:
            hashes[actual_hash].append(relative_path)
        if duration is not None:
            total_duration += float(duration)
            duration_by_type[kind] += float(duration)
        if actual_bytes is not None:
            total_bytes += actual_bytes
        summary_counts["media_type_counts"][kind] += 1
        summary_counts["rights_claim_class_counts"][str(candidate.get("license_claim_class") or "not_recorded")]+= 1
        summary_counts["source_transcript_status_counts"][str(candidate.get("transcript_status") or "not_recorded")]+= 1
        local_draft = machine_drafts.get(actual_hash, []) if actual_hash else []
        draft_status = "present_unreviewed" if local_draft else "not_generated"
        summary_counts["local_machine_draft_status_counts"][draft_status] += 1
        summary_counts["content_review_status_counts"][str(candidate.get("content_review_status") or "not_recorded")]+= 1
        for stream in streams:
            summary_counts["stream_codec_counts"][f"{stream.get('codec_type')}:{stream.get('codec_name')}"] += 1
            if stream.get("codec_type") == "audio":
                if stream.get("sample_rate"):
                    summary_counts["audio_sample_rate_counts"][str(stream["sample_rate"])] += 1
                if stream.get("channels") is not None:
                    summary_counts["audio_channel_counts"][str(stream["channels"])] += 1
            if stream.get("codec_type") == "video" and stream.get("width") and stream.get("height"):
                summary_counts["video_resolution_counts"][f"{stream['width']}x{stream['height']}"] += 1

        errors.extend({**item, "media_path": relative_path} for item in row_errors)
        assets.append({
            "archive_identifier": candidate.get("archive_identifier"),
            "title": candidate.get("title"),
            "source_url": candidate.get("source_url"),
            "media_path": relative_path,
            "sha256": actual_hash,
            "size_bytes": actual_bytes,
            "duration_seconds": duration,
            "media_type": kind,
            "streams": streams,
            "license_claim": candidate.get("license_claim"),
            "license_claim_class": candidate.get("license_claim_class"),
            "rights_evidence_decision": candidate.get("rights_evidence_decision"),
            "publication_and_training_decision": candidate.get("publication_and_training_decision"),
            "source_transcript_status": candidate.get("transcript_status"),
            "local_machine_draft_status": draft_status,
            "local_machine_draft_outputs": local_draft,
            "content_review_status": candidate.get("content_review_status"),
            "validation_status": "failed" if row_errors else "passed",
        })

    duplicate_groups = [
        {"sha256": digest, "media_paths": sorted(paths)}
        for digest, paths in sorted(hashes.items()) if len(paths) > 1
    ]
    media_probe_failures = quality_report.get("media", {}).get("probe_failures", [])
    errors.extend({"code": "ffprobe_failure", "detail": str(item.get("path", ""))} for item in media_probe_failures)
    if quality_report.get("media", {}).get("files_probed") != len(quality_rows):
        errors.append({"code": "quality_probe_count_mismatch"})
    if len(quality_rows) != len(candidate_rows):
        errors.append({"code": "candidate_probe_asset_count_mismatch"})

    return {
        "audit_date": date.today().isoformat(),
        "purpose": "Verify local Archive media identity against source-linked candidates and summarize technical metadata. This does not identify language, transcribe content, clear rights, or change records.",
        "summary": {
            "asset_count": len(assets),
            "archive_item_count": len({row.get("archive_identifier") for row in candidate_rows}),
            "total_size_bytes": total_bytes,
            "total_playback_seconds": round(total_duration, 3),
            "total_playback_hours": round(total_duration / 3600, 5),
            "duration_seconds_by_media_type": {key: round(value, 3) for key, value in sorted(duration_by_type.items())},
            "media_type_counts": dict(sorted(summary_counts["media_type_counts"].items())),
            "rights_claim_class_counts": dict(sorted(summary_counts["rights_claim_class_counts"].items())),
            "source_transcript_status_counts": dict(sorted(summary_counts["source_transcript_status_counts"].items())),
            "local_machine_draft_status_counts": dict(sorted(summary_counts["local_machine_draft_status_counts"].items())),
            "local_machine_draft_output_count": machine_draft_report_count,
            "local_machine_draft_matched_assets": sum(
                1 for row in assets if row["local_machine_draft_status"] == "present_unreviewed"
            ),
            "content_review_status_counts": dict(sorted(summary_counts["content_review_status_counts"].items())),
            "stream_codec_counts": dict(sorted(summary_counts["stream_codec_counts"].items())),
            "audio_sample_rate_counts": dict(sorted(summary_counts["audio_sample_rate_counts"].items())),
            "audio_channel_counts": dict(sorted(summary_counts["audio_channel_counts"].items())),
            "video_resolution_counts": dict(sorted(summary_counts["video_resolution_counts"].items())),
            "exact_duplicate_hash_groups": len(duplicate_groups),
        },
        "validation": {
            "status": "passed" if not errors else "failed",
            "candidate_rows": len(candidate_rows),
            "quality_probe_rows": len(quality_rows),
            "errors": errors,
        },
        "exact_duplicate_hash_groups": duplicate_groups,
        "transcript_sidecar_scan": sidecar_scan,
        "local_machine_draft_scan": {
            "status": "complete" if not machine_draft_errors else "incomplete",
            "errors": machine_draft_errors,
            "unmatched_output_count": sum(
                len(rows) for digest, rows in machine_drafts.items()
                if digest not in hashes
            ),
        },
        "assets": sorted(assets, key=lambda row: (str(row.get("archive_identifier") or ""), row["media_path"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--candidates", type=Path, default=CANDIDATES_PATH)
    parser.add_argument("--quality-report", type=Path, default=QUALITY_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    root = args.root.resolve()
    candidates_path = args.candidates if args.candidates.is_absolute() else root / args.candidates
    quality_path = args.quality_report if args.quality_report.is_absolute() else root / args.quality_report
    output_path = args.output if args.output.is_absolute() else root / args.output

    report = build_media_report(read_jsonl(candidates_path), json.loads(quality_path.read_text(encoding="utf-8")), root)
    report["input_sha256"] = {
        "media_candidates_jsonl": sha256_file(candidates_path),
        "media_quality_audit_json": sha256_file(quality_path),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output_path),
        "status": report["validation"]["status"],
        "assets": report["summary"]["asset_count"],
        "duration_hours": report["summary"]["total_playback_hours"],
        "exact_duplicate_hash_groups": report["summary"]["exact_duplicate_hash_groups"],
        "transcript_sidecar_candidates": len(report["transcript_sidecar_scan"]["archive_caption_or_transcript_candidates"]),
        "local_transcript_sidecar_files": len(report["transcript_sidecar_scan"]["local_caption_or_transcript_files"]),
        "local_machine_draft_matched_assets": report["summary"]["local_machine_draft_matched_assets"],
        "errors": len(report["validation"]["errors"]),
    }, indent=2))
    return 0 if report["validation"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
