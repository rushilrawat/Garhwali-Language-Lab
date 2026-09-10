#!/usr/bin/env python3
"""Create metadata-only Garhwali VAANI manifests through Dataset Viewer."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import fsspec
import pyarrow.parquet as pq
import requests
from huggingface_hub import HfApi, get_token


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "vaani"
VIEWER = "https://datasets-server.huggingface.co"
MAIN_REPO = "ARTPARK-IISc/Vaani"
TRANS_REPO = "ARTPARK-IISc/Vaani-transcription-part"
CONFIG = "Garhwali"


def clean_text(value: object) -> str:
    return " ".join(str(value or "").split())


def norm(value: object) -> str:
    return clean_text(value).casefold()


def fetch_json(session: requests.Session, endpoint: str, params: dict) -> dict:
    response = session.get(f"{VIEWER}/{endpoint}", params=params, timeout=120)
    response.raise_for_status()
    return response.json()


def get_size(session: requests.Session, repo: str) -> dict[str, int]:
    payload = fetch_json(session, "size", {"dataset": repo, "config": CONFIG})
    return {item["split"]: int(item["num_rows"]) for item in payload["size"]["splits"]}


def main_record(row: dict, revision: str, split: str, row_idx: int) -> dict:
    return {
        "source": MAIN_REPO,
        "revision": revision,
        "config": CONFIG,
        "split": split,
        "row_idx": row_idx,
        "audio_path": (row.get("audio") or {}).get("path"),
        "language": row.get("language"),
        "duration_seconds": row.get("duration"),
        "speaker_id": row.get("speakerID"),
        "languages_known": row.get("languagesKnown"),
        "gender": row.get("gender"),
        "state": row.get("state"),
        "district": row.get("district"),
        "stay_years": row.get("stay(years)"),
        "is_transcription_available": row.get("isTranscriptionAvailable"),
        "transcript": clean_text(row.get("transcript")),
        "reference_image": row.get("referenceImage"),
        "utterance_sequence_id": row.get("UtteranceSequenceID"),
        "license": "CC-BY-4.0",
    }


def trans_record(row: dict, split: str, revision: str, row_idx: int) -> dict:
    return {
        "source": TRANS_REPO,
        "revision": revision,
        "config": CONFIG,
        "split": split,
        "row_idx": row_idx,
        "audio_path": (row.get("audio") or {}).get("path"),
        "language": row.get("language"),
        "gender": row.get("gender"),
        "state": row.get("state"),
        "district": row.get("district"),
        "transcript": clean_text(row.get("transcript")),
        "reference_image": row.get("referenceImage"),
        "license": "CC-BY-4.0",
    }


def read_metadata_file(item, columns, headers):
    fs = fsspec.filesystem("http", headers=headers)
    with fs.open(item["url"], "rb") as remote:
        return pq.ParquetFile(remote).read(columns=columns).to_pylist()


def download_manifest(session, repo, revision, output, converter, headers, workers):
    files = fetch_json(session, "parquet", {"dataset": repo, "config": CONFIG})["parquet_files"]
    columns = (
        ["audio.path", "language", "duration", "speakerID", "languagesKnown", "gender", "state", "district", "pincode",
         "stay(years)", "isTranscriptionAvailable", "transcript", "referenceImage", "UtteranceSequenceID"]
        if repo == MAIN_REPO else
        ["audio.path", "language", "gender", "state", "district", "transcript", "referenceImage"]
    )
    file_rows = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(read_metadata_file, item, columns, headers): file_no
            for file_no, item in enumerate(files)
        }
        for done, future in enumerate(as_completed(futures), 1):
            file_rows[futures[future]] = future.result()
            print(f"{repo}: {done}/{len(files)} metadata-only Parquet files", flush=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    records = []
    split_offsets = Counter()
    with temp.open("w", encoding="utf-8") as handle:
        for file_no, item in enumerate(files):
            split = item["split"]
            for row in file_rows[file_no]:
                row_idx = split_offsets[split]
                record = converter(row, revision, split, row_idx) if repo == MAIN_REPO else converter(row, split, revision, row_idx)
                records.append(record)
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                split_offsets[split] += 1
    temp.replace(output)
    return records


def counted(values):
    return dict(sorted(Counter(str(value or "<missing>") for value in values).items()))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(workers: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    token = get_token()
    if not token:
        raise SystemExit("No Hugging Face token found in the configured HF_HOME")
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    api = HfApi(token=token)
    revisions = {repo: api.dataset_info(repo).sha for repo in (MAIN_REPO, TRANS_REPO)}
    sizes = {repo: get_size(session, repo) for repo in (MAIN_REPO, TRANS_REPO)}

    main_path = OUT / "garhwali-main-metadata.jsonl"
    trans_path = OUT / "garhwali-transcriptions.jsonl"
    headers = {"Authorization": f"Bearer {token}"}
    main_rows = download_manifest(session, MAIN_REPO, revisions[MAIN_REPO], main_path, main_record, headers, workers)
    trans_rows = download_manifest(session, TRANS_REPO, revisions[TRANS_REPO], trans_path, trans_record, headers, workers)

    main_nonempty = [r for r in main_rows if r["transcript"]]
    trans_nonempty = [r for r in trans_rows if r["transcript"]]
    main_texts = Counter(norm(r["transcript"]) for r in main_nonempty)
    trans_texts = Counter(norm(r["transcript"]) for r in trans_nonempty)
    text_overlap = sum((main_texts & trans_texts).values())
    key = lambda r: (norm(r["transcript"]), norm(r["district"]), norm(r["gender"]), norm(r["reference_image"]))
    composite_overlap = sum((Counter(map(key, main_nonempty)) & Counter(map(key, trans_nonempty))).values())
    main_by_audio = {r["audio_path"]: r for r in main_rows}
    trans_by_audio = {r["audio_path"]: r for r in trans_rows}
    shared_audio = main_by_audio.keys() & trans_by_audio.keys()
    without_closing_pause = lambda value: norm(re.sub(r"</pause>", "", value or "", flags=re.I))
    exact_text = sum(norm(main_by_audio[p]["transcript"]) == norm(trans_by_audio[p]["transcript"]) for p in shared_audio)
    pause_only = sum(
        norm(main_by_audio[p]["transcript"]) != norm(trans_by_audio[p]["transcript"])
        and without_closing_pause(main_by_audio[p]["transcript"]) == without_closing_pause(trans_by_audio[p]["transcript"])
        for p in shared_audio
    )
    flagged = sum(norm(r["is_transcription_available"]) in {"yes", "true", "1"} for r in main_rows)
    duration = sum(float(r["duration_seconds"] or 0) for r in main_rows)
    speakers = {str(r["speaker_id"]) for r in main_rows if norm(r["speaker_id"]) not in {"", "na", "n/a", "none"}}
    created = datetime.now(timezone.utc).isoformat()
    summary = {
        "created_at": created,
        "method": "Authenticated Dataset Viewer Parquet URLs with leaf-column pruning; audio.path read, audio.bytes excluded",
        "license": "CC-BY-4.0",
        "main": {
            "repo": MAIN_REPO, "revision": revisions[MAIN_REPO], "splits": sizes[MAIN_REPO],
            "rows": len(main_rows), "duration_seconds": duration, "duration_hours": duration / 3600,
            "transcription_flag_yes": flagged, "nonempty_transcripts": len(main_nonempty),
            "districts": counted(r["district"] for r in main_rows),
            "genders": counted(r["gender"] for r in main_rows),
            "unique_nonplaceholder_speakers": len(speakers),
        },
        "transcription_part": {
            "repo": TRANS_REPO, "revision": revisions[TRANS_REPO], "splits": sizes[TRANS_REPO],
            "rows": len(trans_rows), "nonempty_transcripts": len(trans_nonempty),
            "districts": counted(r["district"] for r in trans_rows),
            "genders": counted(r["gender"] for r in trans_rows),
        },
        "reconciliation": {
            "normalized_transcript_multiset_overlap": text_overlap,
            "normalized_transcript_district_gender_reference_image_multiset_overlap": composite_overlap,
            "main_nonempty_not_matched_by_text": len(main_nonempty) - text_overlap,
            "transcription_part_not_matched_by_text": len(trans_nonempty) - text_overlap,
            "shared_unique_audio_paths": len(shared_audio),
            "transcription_paths_absent_from_main": len(trans_by_audio.keys() - main_by_audio.keys()),
            "shared_paths_with_equal_normalized_transcript": exact_text,
            "shared_differing_only_by_closing_pause_tag": pause_only,
            "shared_with_other_text_or_annotation_differences": len(shared_audio) - exact_text - pause_only,
            "shared_duration_seconds_from_main": sum(float(main_by_audio[p]["duration_seconds"] or 0) for p in shared_audio),
            "relationship": "The main config's transcript-bearing WAVs are present in the transcription repository, which also contains additional WAVs absent from the current main config.",
        },
        "artifacts": {
            main_path.name: {"rows": len(main_rows), "sha256": digest(main_path)},
            trans_path.name: {"rows": len(trans_rows), "sha256": digest(trans_path)},
        },
        "provenance": {
            "main_url": f"https://huggingface.co/datasets/{MAIN_REPO}",
            "transcription_url": f"https://huggingface.co/datasets/{TRANS_REPO}",
            "official_license_url": "https://vaani.iisc.ac.in/dataset/Version1",
        },
    }
    for repo, expected in sizes.items():
        actual = len(main_rows) if repo == MAIN_REPO else len(trans_rows)
        if actual != sum(expected.values()):
            raise RuntimeError(f"row-count mismatch for {repo}: expected {expected}, got {actual}")
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    run(parser.parse_args().workers)
