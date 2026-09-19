#!/usr/bin/env python3
"""Re-OCR weak incoming-PDF pages under multiple layouts without overwriting text."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from ingest_incoming_pdfs import FONTCONFIG, PDFTOPPM, TESSERACT, locate_tessdata, normalized_text


ROOT = Path(__file__).resolve().parents[1]
DEVANAGARI = re.compile(r"[\u0900-\u097f]")
REPLACEMENT = "\ufffd"


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def weakness(text: str) -> float:
    """Rank likely OCR failures using only observable surface evidence."""
    length = max(1, len(text))
    letters = sum(char.isalpha() for char in text)
    deva = len(DEVANAGARI.findall(text))
    controls = sum(ord(char) < 32 and char not in "\n\t" for char in text)
    repeated = len(re.findall(r"([^\w\s])\1{2,}", text))
    return round(
        6 * text.count(REPLACEMENT)
        + 3 * controls
        + 2 * repeated
        + 2 * (1 - letters / length)
        + (1 - deva / max(1, letters)),
        6,
    )


def parse_tsv(tsv: str) -> tuple[str, float | None, int]:
    rows = list(csv.DictReader(tsv.splitlines(), delimiter="\t"))
    words = []
    confidences = []
    for row in rows:
        token = (row.get("text") or "").strip()
        try:
            confidence = float(row.get("conf", "-1"))
        except ValueError:
            confidence = -1
        if token:
            words.append(token)
            if confidence >= 0:
                confidences.append(confidence)
    text = normalized_text(" ".join(words))
    mean = round(sum(confidences) / len(confidences), 4) if confidences else None
    return text, mean, len(confidences)


def render_page(pdf: Path, page: int, dpi: int, output: Path) -> None:
    if not PDFTOPPM:
        raise FileNotFoundError(
            "pdftoppm is required; install Poppler or set PDFTOPPM_BIN"
        )
    env = os.environ.copy()
    if FONTCONFIG and FONTCONFIG.exists():
        env["FONTCONFIG_FILE"] = str(FONTCONFIG)
    env.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "garhwali-font-cache"))
    subprocess.run(
        [PDFTOPPM, "-f", str(page), "-l", str(page), "-r", str(dpi),
         "-png", "-singlefile", str(pdf), str(output.with_suffix(""))],
        check=True, capture_output=True, env=env,
    )


def ocr_variant(image: Path, tessdata: Path, psm: int) -> dict:
    if not TESSERACT:
        raise FileNotFoundError(
            "tesseract is required; install it or set TESSERACT_BIN"
        )
    result = subprocess.run(
        [TESSERACT, str(image), "stdout", "--tessdata-dir", str(tessdata),
         "-l", "hin+eng", "--psm", str(psm), "-c", "tessedit_create_tsv=1"],
        check=True, capture_output=True, text=True,
    )
    text, confidence, words = parse_tsv(result.stdout)
    return {"psm": psm, "text": text, "mean_word_confidence": confidence,
            "confident_word_count": words,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest()}


def choose_candidate(candidates: list[dict]) -> tuple[int | None, int]:
    hashes = Counter(item["text_sha256"] for item in candidates if item["text"])
    best_hash, agreement = hashes.most_common(1)[0] if hashes else (None, 0)
    eligible = [
        (index, item) for index, item in enumerate(candidates)
        if item["text"] and item["text_sha256"] == best_hash
    ]
    if not eligible:
        return None, 0
    index, _ = max(
        eligible,
        key=lambda pair: (pair[1]["mean_word_confidence"] or -1,
                          pair[1]["confident_word_count"]),
    )
    return index, agreement


def run(input_path: Path, output_dir: Path, limit: int, dpi: int,
        layouts: tuple[int, ...]) -> dict:
    output_dir = output_dir.resolve()
    rows = [row for row in read_jsonl(input_path)
            if row.get("extraction_method") == "tesseract_hin_eng"]
    rows.sort(key=lambda row: (-weakness(row.get("text", "")), row["record_id"]))
    selected = rows[:limit]
    output_dir.mkdir(parents=True, exist_ok=True)
    tessdata = locate_tessdata(output_dir / "runtime")
    output_path = output_dir / "candidates.jsonl"
    agreements = Counter()
    completed = {}
    if output_path.exists():
        completed = {row["record_id"]: row for row in read_jsonl(output_path)}
        agreements.update(row.get("exact_variant_agreement", 0)
                          for row in completed.values())
    mode = "a" if completed else "w"
    with output_path.open(mode, encoding="utf-8") as handle:
        for row in selected:
            if row["record_id"] in completed:
                continue
            pdf = ROOT / row["source_pdf"]
            with tempfile.TemporaryDirectory(prefix="garhwali-reocr-") as temp:
                image = Path(temp) / "page.png"
                render_page(pdf, row["pdf_page"], dpi, image)
                candidates = [ocr_variant(image, tessdata, psm) for psm in layouts]
            chosen, agreement = choose_candidate(candidates)
            agreements[agreement] += 1
            handle.write(json.dumps({
                "record_id": row["record_id"],
                "source_id": row["source_id"],
                "source_pdf": row["source_pdf"],
                "pdf_page": row["pdf_page"],
                "original_text": row["text"],
                "original_text_sha256": row["text_sha256"],
                "surface_weakness": weakness(row["text"]),
                "dpi": dpi,
                "candidates": candidates,
                "selected_candidate_index": chosen,
                "exact_variant_agreement": agreement,
                "application": "evidence_only",
                "original_preserved": True,
            }, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
    report = {
        "run_id": "incoming-pdf-multilayout-reocr-pilot-v0.1",
        "available_machine_ocr_pages": len(rows),
        "reprocessed_pages": len(selected),
        "resumed_from_pages": len(completed),
        "dpi": dpi,
        "layouts": list(layouts),
        "exact_variant_agreement_distribution": dict(sorted(agreements.items())),
        "output": str(output_path.relative_to(ROOT)),
        "policy": "evidence only; original OCR retained; no automatic lexical replacement",
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "experimental/incoming_pdfs.jsonl")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "data/processed/evaluation/data_quality/incoming_pdf_reocr_v0_1")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--layouts", default="3,4,6,11")
    args = parser.parse_args()
    report = run(args.input, args.output, args.limit, args.dpi,
                 tuple(int(value) for value in args.layouts.split(",")))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
