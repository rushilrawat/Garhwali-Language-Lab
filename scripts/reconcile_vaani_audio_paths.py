#!/usr/bin/env python3
"""Reconcile VAANI repositories by reading only the nested audio.path column."""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import time

import fsspec
import pyarrow.parquet as pq
import requests
from huggingface_hub import get_token

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "vaani"
VIEWER = "https://datasets-server.huggingface.co/parquet"
REPOS = {
    "main": ("ARTPARK-IISc/Vaani", OUT / "garhwali-main-metadata.jsonl"),
    "transcription_part": ("ARTPARK-IISc/Vaani-transcription-part", OUT / "garhwali-transcriptions.jsonl"),
}


def read_paths(item, headers, cache_path):
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    for attempt in range(6):
        try:
            fs = fsspec.filesystem("http", headers=headers)
            with fs.open(item["url"], "rb") as remote:
                rows = pq.ParquetFile(remote).read(columns=["audio.path"]).to_pylist()
            paths = [row["audio"]["path"] for row in rows]
            temp = cache_path.with_suffix(".tmp")
            temp.write_text(json.dumps(paths), encoding="utf-8")
            temp.replace(cache_path)
            return paths
        except Exception:
            if attempt == 5:
                raise
            time.sleep(2 ** attempt)


def repository_paths(repo, headers, workers=8):
    response = requests.get(VIEWER, params={"dataset": repo, "config": "Garhwali"}, headers=headers, timeout=120)
    response.raise_for_status()
    files = response.json()["parquet_files"]
    results = {}
    cache_dir = OUT / ".path-cache" / repo.replace("/", "__")
    cache_dir.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(read_paths, item, headers, cache_dir / f"{index:03d}.json"): index
            for index, item in enumerate(files)
        }
        for done, future in enumerate(as_completed(futures), 1):
            results[futures[future]] = future.result()
            print(f"{repo}: {done}/{len(files)} path-only files", flush=True)
    return [path for index in range(len(files)) for path in results[index]]


def add_paths(manifest, paths):
    records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]
    if len(records) != len(paths):
        raise RuntimeError(f"path count mismatch for {manifest}: {len(paths)} vs {len(records)}")
    temp = manifest.with_suffix(manifest.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        for record, path in zip(records, paths):
            record["audio_path"] = path
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    temp.replace(manifest)
    return records


def main():
    token = get_token()
    if not token:
        raise SystemExit("No Hugging Face token found")
    headers = {"Authorization": f"Bearer {token}"}
    data = {}
    for name, (repo, manifest) in REPOS.items():
        data[name] = add_paths(manifest, repository_paths(repo, headers))

    main_by_path = {row["audio_path"]: row for row in data["main"]}
    trans_by_path = {row["audio_path"]: row for row in data["transcription_part"]}
    shared = set(main_by_path) & set(trans_by_path)
    same_text = sum(
        " ".join(main_by_path[path]["transcript"].split()).casefold()
        == " ".join(trans_by_path[path]["transcript"].split()).casefold()
        for path in shared
    )
    result = {
        "main_rows": len(data["main"]),
        "main_unique_audio_paths": len(main_by_path),
        "transcription_rows": len(data["transcription_part"]),
        "transcription_unique_audio_paths": len(trans_by_path),
        "shared_unique_audio_paths": len(shared),
        "transcription_paths_absent_from_main": len(set(trans_by_path) - set(main_by_path)),
        "main_paths_absent_from_transcription": len(set(main_by_path) - set(trans_by_path)),
        "shared_paths_with_equal_normalized_transcript": same_text,
        "shared_paths_with_different_normalized_transcript": len(shared) - same_text,
        "duplicate_main_audio_paths": sum(v - 1 for v in Counter(r["audio_path"] for r in data["main"]).values()),
        "duplicate_transcription_audio_paths": sum(v - 1 for v in Counter(r["audio_path"] for r in data["transcription_part"]).values()),
    }
    (OUT / "audio-path-reconciliation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
