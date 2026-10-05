#!/usr/bin/env python3
"""Create alternate Hindi/English OCR for flagged pages without replacing source OCR."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE_MAP = Path(
    "data/extracted/research/archive_chatak_shailesh_page_section_map_2026-10-04.jsonl"
)
OUTPUT_PATH = Path(
    "data/extracted/research/archive_chatak_shailesh_alternate_ocr_2026-10-04.jsonl"
)
TESSDATA_DIR = Path("data/extracted/research/tesseract_runtime_2026-10-04")
HINDI_MODEL = Path("data/extracted/research/tesseract_models/hin.traineddata")
SOURCES = {
    "ia_govind_chatak_gadwali_lok_gathayen_1958": Path(
        "data/downloads/folklore/internet_archive/gadwali_lok_gathayen_1958/source.pdf"
    ),
    "ia_haridatta_bhatta_garhwali_bhasha_sahitya_1976": Path(
        "data/downloads/linguistics/internet_archive/garhwali_bhasha_sahitya_1976/source.pdf"
    ),
}
MODEL_URL = "https://github.com/tesseract-ocr/tessdata_best/blob/main/hin.traineddata"
MODEL_LICENSE = "Apache-2.0"


def select_targets(page_rows: list[dict]) -> list[dict]:
    """Select only pages marked empty or carrying a prior OCR warning."""
    return [
        row for row in page_rows
        if row.get("source_id") in SOURCES
        and (row.get("ocr_empty") or row.get("candidate_ocr_warning_flags"))
    ]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tesseract_words(tsv: str) -> tuple[str, list[float]]:
    by_line: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    confidences = []
    for row in csv.DictReader(tsv.splitlines(), delimiter="\t"):
        if row.get("level") != "5" or not row.get("text", "").strip():
            continue
        key = tuple(row.get(field, "") for field in ("page_num", "block_num", "par_num", "line_num"))
        by_line[key].append(row["text"].strip())
        try:
            confidences.append(float(row["conf"]))
        except (ValueError, TypeError):
            pass
    text = "\n".join(" ".join(words) for words in by_line.values())
    return text, confidences


def run_ocr(page_map_path: Path, output_path: Path, tessdata_dir: Path, root: Path) -> dict:
    tesseract = shutil.which("tesseract")
    pdftoppm = shutil.which("pdftoppm")
    if not tesseract or not pdftoppm:
        raise RuntimeError("Both tesseract and pdftoppm must be installed and on PATH.")
    if not (root / HINDI_MODEL).is_file():
        raise FileNotFoundError(f"Hindi OCR model is missing: {root / HINDI_MODEL}")
    languages = subprocess.run(
        [tesseract, "--tessdata-dir", str(root / tessdata_dir), "--list-langs"],
        check=True, capture_output=True, text=True,
    ).stdout
    if "hin" not in languages.split():
        raise RuntimeError(f"Hindi OCR model not available in {root / tessdata_dir}")

    page_rows = [json.loads(line) for line in (root / page_map_path).open(encoding="utf-8")]
    targets = sorted(select_targets(page_rows), key=lambda row: (row["source_id"], row["pdf_page"]))
    if not targets:
        return {"target_pages": 0, "processed_pages": 0, "output": str(output_path)}

    source_hashes = {
        source_id: sha256_file(root / path) for source_id, path in SOURCES.items()
        if any(row["source_id"] == source_id for row in targets)
    }
    version = subprocess.run([tesseract, "--version"], check=True, capture_output=True, text=True).stdout.splitlines()[0]
    model_hash = sha256_file(root / HINDI_MODEL)
    destination = root / output_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="garhwali-reocr-") as temp_dir:
        temp = Path(temp_dir)
        with destination.open("w", encoding="utf-8") as output:
            for index, row in enumerate(targets, start=1):
                source_id = row["source_id"]
                pdf = root / SOURCES[source_id]
                prefix = temp / f"page-{index}"
                subprocess.run(
                    [pdftoppm, "-f", str(row["pdf_page"]), "-l", str(row["pdf_page"]),
                     "-r", "300", "-png", "-singlefile", str(pdf), str(prefix)],
                    check=True, capture_output=True, text=True,
                )
                output_base = prefix.with_name(prefix.name + "-ocr")
                subprocess.run(
                    [tesseract, "--tessdata-dir", str(root / tessdata_dir), "--oem", "1",
                     "--psm", "3", "-l", "hin+eng", "-c", "tessedit_create_tsv=1",
                     str(prefix.with_suffix(".png")), str(output_base)],
                    check=True, capture_output=True, text=True,
                )
                tsv_path = output_base.with_suffix(".tsv")
                alternate_text, confidences = tesseract_words(tsv_path.read_text(encoding="utf-8"))
                record = {
                    "schema_version": "1.0.0",
                    "source_id": source_id,
                    "archive_identifier": row.get("archive_identifier"),
                    "source_url": row.get("source_url"),
                    "pdf_page": row["pdf_page"],
                    "candidate_record_id": row.get("candidate_record_id"),
                    "source_pdf_sha256": source_hashes[source_id],
                    "existing_ocr_sha256": row.get("candidate_text_sha256"),
                    "existing_normalized_characters": row.get("candidate_normalized_characters", 0),
                    "existing_ocr_warning_flags": row.get("candidate_ocr_warning_flags", []),
                    "alternate_ocr_text": alternate_text,
                    "alternate_ocr_sha256": hashlib.sha256(alternate_text.encode("utf-8")).hexdigest(),
                    "alternate_ocr_characters": len(alternate_text),
                    "tesseract_version": version,
                    "recognition_language": "hin+eng",
                    "page_segmentation_mode": 3,
                    "mean_word_confidence": round(sum(confidences) / len(confidences), 2)
                    if confidences else None,
                    "low_confidence_word_count": sum(value < 70 for value in confidences),
                    "model_source": MODEL_URL,
                    "model_sha256": model_hash,
                    "model_license": MODEL_LICENSE,
                    "status": "alternate_machine_ocr_unreviewed",
                }
                output.write(json.dumps(record, ensure_ascii=False) + "\n")
                output.flush()
                print(f"Processed {index}/{len(targets)}: {source_id} page {row['pdf_page']}", flush=True)

    return {"target_pages": len(targets), "processed_pages": len(targets), "output": str(destination)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--page-map", type=Path, default=PAGE_MAP)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--tessdata-dir", type=Path, default=TESSDATA_DIR)
    args = parser.parse_args()
    print(json.dumps(run_ocr(args.page_map, args.output, args.tessdata_dir, args.root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
