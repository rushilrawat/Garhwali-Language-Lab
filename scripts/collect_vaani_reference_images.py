#!/usr/bin/env python3
"""Selectively collect images referenced by the Garhwali VAANI rows."""

from __future__ import annotations

import hashlib
import io
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time

import fsspec
from PIL import Image
import pyarrow.parquet as pq
import requests
from huggingface_hub import get_token


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vaani"
REPO = "ARTPARK-IISc/Vaani"
REVISION = "fe12c49bc61c083d5bb2092513fb6ec2e7ae72ee"
PARQUET_URL = "https://datasets-server.huggingface.co/parquet"


def remote_parquet(item, headers):
    fs = fsspec.filesystem("http", headers=headers)
    return fs, fs.open(item["url"], "rb")


def read_paths(item, headers, cache_path):
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    for attempt in range(6):
        try:
            fs, handle = remote_parquet(item, headers)
            with handle:
                rows = pq.ParquetFile(handle).read(columns=["image.path"]).to_pylist()
            paths = [Path(row["image"]["path"]).name for row in rows]
            temp = cache_path.with_suffix(".tmp")
            temp.write_text(json.dumps(paths), encoding="utf-8")
            temp.replace(cache_path)
            return paths
        except Exception:
            if attempt == 5:
                raise
            time.sleep(2 ** attempt)


def validate_image(payload: bytes) -> tuple[str, int, int]:
    with Image.open(io.BytesIO(payload)) as image:
        image.verify()
    with Image.open(io.BytesIO(payload)) as image:
        return image.format or "unknown", image.width, image.height


def extract_file(item, file_index, wanted_rows, headers, output):
    records = []
    fs, handle = remote_parquet(item, headers)
    with handle:
        parquet = pq.ParquetFile(handle)
        boundaries = []
        start = 0
        for group_index in range(parquet.num_row_groups):
            count = parquet.metadata.row_group(group_index).num_rows
            boundaries.append((start, start + count, group_index))
            start += count
        by_group = defaultdict(set)
        for row_index in wanted_rows:
            for begin, end, group_index in boundaries:
                if begin <= row_index < end:
                    by_group[group_index].add(row_index - begin)
                    break
        for group_index, local_indices in sorted(by_group.items()):
            rows = parquet.read_row_group(group_index, columns=["image"]).to_pylist()
            for local_index in sorted(local_indices):
                image = rows[local_index]["image"]
                name = Path(image["path"]).name
                payload = image["bytes"]
                fmt, width, height = validate_image(payload)
                destination = output / f"{file_index:03d}" / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                temp = destination.with_suffix(destination.suffix + ".tmp")
                temp.write_bytes(payload)
                temp.replace(destination)
                records.append({
                    "image_path": name,
                    "local_path": str(destination.relative_to(ROOT)),
                    "source_shard_index": file_index,
                    "source_row_index": next(begin for begin, end, group in boundaries if group == group_index) + local_index,
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "format": fmt,
                    "width": width,
                    "height": height,
                    "source": REPO,
                    "revision": REVISION,
                    "license": "CC-BY-4.0",
                })
    return records, len(by_group)


def main() -> None:
    token = get_token()
    if not token:
        raise SystemExit("No Hugging Face token found")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(PARQUET_URL, params={"dataset": REPO, "config": "images"}, headers=headers, timeout=120)
    response.raise_for_status()
    files = response.json()["parquet_files"]
    if len(files) != 114:
        raise RuntimeError(f"Expected 114 image shards, found {len(files)}")

    main_rows = [json.loads(line) for line in (DATA / "garhwali-main-metadata.jsonl").open(encoding="utf-8")]
    wanted = {Path(row["reference_image"]).name for row in main_rows}
    if len(wanted) != 4506:
        raise RuntimeError(f"Expected 4506 distinct reference images, found {len(wanted)}")

    cache = DATA / ".image-path-cache"
    cache.mkdir(parents=True, exist_ok=True)
    paths_by_file = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(read_paths, item, headers, cache / f"{index:03d}.json"): index
            for index, item in enumerate(files)
        }
        for done, future in enumerate(as_completed(futures), 1):
            paths_by_file[futures[future]] = future.result()
            print(f"path map {done}/{len(files)}", flush=True)

    wanted_rows = defaultdict(set)
    found = set()
    for file_index, paths in paths_by_file.items():
        for row_index, name in enumerate(paths):
            if name in wanted:
                wanted_rows[file_index].add(row_index)
                found.add(name)
    missing = wanted - found
    if missing:
        raise RuntimeError(f"VAANI image config is missing {len(missing)} referenced images")

    output = DATA / "images" / "reference"
    all_records = []
    row_groups = 0
    selected_files = sorted(wanted_rows)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(extract_file, files[index], index, wanted_rows[index], headers, output): index
            for index in selected_files
        }
        for done, future in enumerate(as_completed(futures), 1):
            records, groups = future.result()
            all_records.extend(records)
            row_groups += groups
            print(f"image extraction {done}/{len(selected_files)} files", flush=True)
    all_records.sort(key=lambda row: row["image_path"])
    if len(all_records) != len(wanted) or len({row["image_path"] for row in all_records}) != len(wanted):
        raise RuntimeError("Extracted image count or uniqueness check failed")

    manifest = DATA / "reference-image-manifest.jsonl"
    with manifest.open("w", encoding="utf-8") as handle:
        for row in all_records:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")
    report = {
        "source": REPO,
        "revision": REVISION,
        "global_image_shards_scanned_by_path": len(files),
        "source_shards_with_selected_images": len(selected_files),
        "source_row_groups_read_with_bytes": row_groups,
        "referenced_images": len(all_records),
        "payload_bytes": sum(row["bytes"] for row in all_records),
        "formats": dict(sorted(__import__("collections").Counter(row["format"] for row in all_records).items())),
        "manifest": str(manifest.relative_to(ROOT)),
    }
    (DATA / "reference-image-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
