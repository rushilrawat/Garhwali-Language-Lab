#!/usr/bin/env python3
"""Deduplicate and extract every non-empty page from user-supplied Garhwali PDFs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "incoming/pdfs"
DEFAULT_OUTPUT = ROOT / "experimental/incoming_pdfs.jsonl"
DEFAULT_REPORT = ROOT / "research/incoming-pdf-ingestion-2026-09-16.json"
DEFAULT_CACHE = ROOT / "data/extracted/incoming_pdfs/page_cache"
PDFTOPPM = shutil.which("pdftoppm") or str(
    Path.home()
    / ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm"
)
TESSERACT = shutil.which("tesseract") or "/opt/homebrew/bin/tesseract"
FONTCONFIG = (
    Path.home()
    / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/etc/fonts/fonts.conf"
)

KNOWN_DUPLICATE_OUTPUTS = {
    "6a1028710506a4dd2f2695953ad538a1152b2b8b4efd58e95e64109fafbfb34e":
        "data/extracted/folklore/govind_chatak_gadwali_lokgeet_1956.jsonl",
}

SOURCE_METADATA = {
    "Gadwali LokGeet.pdf": {
        "source_id": "incoming_gadwali_lokgeet",
        "title": "Gadwali LokGeet",
        "author": "Govind Chatak",
        "publication_year": 1956,
        "genre": "folk_literature",
    },
    "Garhwali language and culture.pdf": {
        "source_id": "incoming_garhwali_language_and_culture",
        "title": "Garhwal: Bhasha, Sahitya aur Sanskriti",
        "author": "Govind Chatak",
        "publication_year": 2008,
        "genre": "language_culture_research",
    },
    "Garhwali Bhasha_ Ek Bhashashashtriya Aur Vyakarnik Adhyayan.pdf": {
        "source_id": "incoming_garhwali_bhasha_linguistic_grammatical_study",
        "title": "Garhwali Bhasha: Ek Bhashashastriya Aur Vyakaranik Adhyayan",
        "author": "Govind Chatak",
        "genre": "grammar_linguistics",
    },
    "Garhwali, A Syntactic Sketch of (Chandola).pdf": {
        "source_id": "incoming_chandola_syntactic_sketch",
        "title": "A Syntactic Sketch of Garhwali",
        "author": "Anang Chandra Chandola",
        "genre": "grammar_linguistics",
    },
    "Dictionary of English hindi Garhwali.pdf": {
        "source_id": "incoming_english_hindi_garhwali_dictionary",
        "title": "Dictionary: English-Garhwali-Hindi",
        "author": "Achlanand Jakhmola",
        "publication_year": 2016,
        "genre": "dictionary_lexicon",
    },
    "Garhwali Hindi Dictionary Uttarakhand Garwali Gadwali.pdf": {
        "source_id": "incoming_garhwali_hindi_dictionary",
        "title": "Garhwali-Hindi Dictionary",
        "author": "Arvind Purohit; Beena Benzwal",
        "publication_year": 2007,
        "genre": "dictionary_lexicon",
    },
    "Gadwali Sahitya.pdf": {
        "source_id": "incoming_gadwali_sahitya",
        "title": "Garhwali Sahitya ki Bhumika",
        "author": "Damodar Prasad Thapliyal; Shyam Chand Negi",
        "publication_year": 1954,
        "genre": "literature_language_culture",
    },
}


def source_metadata_for(pdf: Path) -> dict:
    """Combine built-in metadata with an optional neighboring JSON sidecar."""
    fallback_id = "incoming_" + re.sub(
        r"[^a-z0-9]+", "_", pdf.stem.casefold()
    ).strip("_")
    metadata = dict(SOURCE_METADATA.get(pdf.name, {
        "source_id": fallback_id,
        "title": pdf.stem,
        "genre": "reference_material",
    }))
    sidecar = pdf.with_suffix(".json")
    if sidecar.is_file():
        value = json.loads(sidecar.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"PDF metadata sidecar must contain an object: {sidecar}")
        metadata.update({key: item for key, item in value.items() if item is not None})
    metadata.setdefault("source_id", fallback_id)
    metadata.setdefault("title", pdf.stem)
    metadata.setdefault("genre", "reference_material")
    return metadata


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_exact_duplicate(candidate: Path, pdf_paths: list[Path]) -> Path | None:
    candidate = candidate.resolve()
    digest = sha256_file(candidate)
    matches = [
        path.resolve()
        for path in sorted(pdf_paths)
        if path.resolve() != candidate and sha256_file(path.resolve()) == digest
    ]
    return matches[0] if matches else None


def normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def has_substantive_embedded_text(text: str) -> bool:
    clean = normalized_text(text)
    alphabetic = sum(character.isalpha() for character in clean)
    return len(clean) >= 100 and alphabetic >= 60


def detected_script(text: str) -> str:
    deva = any("\u0900" <= character <= "\u097f" for character in text)
    latin = any(character.isascii() and character.isalpha() for character in text)
    if deva and latin:
        return "Mixed"
    if deva:
        return "Deva"
    if latin:
        return "Latn"
    return "Other"


def page_record(*, source_id: str, source_pdf: Path, source_sha256: str,
                page_number: int, text: str, extraction_method: str,
                title: str, author: str | None = None,
                publication_year: int | None = None,
                genre: str = "reference_material",
                source_metadata: dict | None = None) -> dict:
    text = normalized_text(text)
    source_metadata = source_metadata or {}
    flags = ["needs_native_review", "user_supplied_pdf"]
    if not source_metadata.get("license_or_rights_statement"):
        flags.append("rights_unknown")
    if extraction_method.startswith("tesseract"):
        flags.append("machine_ocr")
    else:
        flags.append("embedded_pdf_text_layer")
    text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    record = {
        "record_id": f"{source_id}:page:{page_number}",
        "source_id": source_id,
        "source_pdf": str(source_pdf),
        "source_pdf_sha256": source_sha256,
        "pdf_page": page_number,
        "title": title,
        "author": author,
        "publication_year": publication_year,
        "attribution": author or title,
        "text": text,
        "text_sha256": text_sha256,
        "iso_639_3": "gbm",
        "language": "Garhwali",
        "language_scope": "garhwali_focused_mixed_reference",
        "script": detected_script(text),
        "genre": genre,
        "modality": "text",
        "extraction_method": extraction_method,
        "corpus_layer": "experimental",
        "usage": "all_data_experimental_user_approved",
        "training_eligible": False,
        "experimental_training_eligible": True,
        "rights_status": "user_supplied_source_rights_unverified",
        "license": "unknown",
        "quality_flags": sorted(flags),
        "modifications": (
            "Unicode NFC; whitespace normalization; PDF text-layer extraction"
            if extraction_method == "embedded_pdf_text_layer"
            else "PDF page rendered to image; Tesseract hin+eng OCR; Unicode NFC; whitespace normalization"
        ),
    }
    for field in (
        "download_url", "landing_page", "license_or_rights_statement",
        "rights_evidence_url", "suspected_garhwali_pages", "notes", "subtitle",
        "edition", "publisher", "publication_place", "isbn", "lccn",
        "physical_pages", "languages", "subjects", "catalog_records",
        "persistent_identifier", "work_type", "degree", "institution",
        "department", "dialect_scope", "editor", "compiler", "volume",
    ):
        if source_metadata.get(field) is not None:
            record[field] = source_metadata[field]
    return record


def locate_tessdata(work_dir: Path) -> Path:
    target = work_dir / "tessdata"
    target.mkdir(parents=True, exist_ok=True)
    hindi = next((ROOT / "sources/online/uou_cgl").glob("*-hin.traineddata"), None)
    if hindi is None:
        raise FileNotFoundError("Project Hindi Tesseract model is missing")
    english_candidates = [
        Path("/opt/homebrew/share/tessdata/eng.traineddata"),
        Path("/usr/local/share/tessdata/eng.traineddata"),
    ]
    english = next((path for path in english_candidates if path.exists()), None)
    if english is None:
        raise FileNotFoundError("English Tesseract model is missing")
    for source, name in ((hindi, "hin.traineddata"), (english, "eng.traineddata")):
        destination = target / name
        if not destination.exists() or destination.stat().st_size != source.stat().st_size:
            shutil.copy2(source, destination)
    return target


def extract_ocr_page(pdf: Path, page_number: int, cache_file: Path,
                     tessdata: Path, dpi: int) -> tuple[int, str]:
    if cache_file.exists():
        return page_number, json.loads(cache_file.read_text(encoding="utf-8"))["text"]
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="garhwali-pdf-page-") as tmp:
        prefix = Path(tmp) / "page"
        env = os.environ.copy()
        if FONTCONFIG.exists():
            env["FONTCONFIG_FILE"] = str(FONTCONFIG)
        env["XDG_CACHE_HOME"] = "/private/tmp/garhwali-font-cache"
        subprocess.run(
            [PDFTOPPM, "-f", str(page_number), "-l", str(page_number),
             "-r", str(dpi), "-jpeg", "-singlefile", str(pdf), str(prefix)],
            check=True, capture_output=True, env=env,
        )
        result = subprocess.run(
            [TESSERACT, str(prefix.with_suffix(".jpg")), "stdout", "--tessdata-dir",
             str(tessdata), "-l", "hin+eng", "--psm", "3"],
            check=True, capture_output=True, text=True,
        )
    text = normalized_text(result.stdout)
    cache_file.write_text(
        json.dumps({"page": page_number, "text": text}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return page_number, text


def existing_text_hashes(exclude: Path) -> set[str]:
    hashes: set[str] = set()
    for directory in ("corpus", "restricted", "experimental", "extracted", "data/extracted"):
        folder = ROOT / directory
        if not folder.exists():
            continue
        for path in folder.rglob("*.jsonl"):
            if path.resolve() == exclude.resolve():
                continue
            with path.open(encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    try:
                        row = json.loads(line)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    for field in ("text_normalized", "text", "source_text", "transcript"):
                        value = row.get(field)
                        if isinstance(value, str) and value.strip():
                            hashes.add(hashlib.sha256(normalized_text(value).encode("utf-8")).hexdigest())
                            break
    return hashes


def ingest(input_dir: Path, output: Path, report_path: Path, cache_dir: Path,
           workers: int = 6, dpi: int = 220) -> dict:
    from pypdf import PdfReader

    input_pdfs = sorted(input_dir.glob("*.pdf"))
    all_pdfs = sorted(ROOT.rglob("*.pdf"))
    prior_hashes = existing_text_hashes(output)
    records = []
    documents = []
    work_dir = cache_dir.parent
    tessdata = None

    for pdf in input_pdfs:
        digest = sha256_file(pdf)
        duplicate = find_exact_duplicate(pdf, all_pdfs)
        reader = PdfReader(pdf)
        metadata = source_metadata_for(pdf)
        document = {
            "file": str(pdf.relative_to(ROOT)),
            "sha256": digest,
            "bytes": pdf.stat().st_size,
            "pages": len(reader.pages),
            "source_id": metadata["source_id"],
            "title": metadata["title"],
            "author": metadata.get("author"),
            "publication_year": metadata.get("publication_year"),
            "metadata_sidecar": (
                str(pdf.with_suffix(".json").relative_to(ROOT))
                if pdf.with_suffix(".json").is_file() else None
            ),
            "bibliographic_metadata": metadata,
            "exact_duplicate_of": str(duplicate.relative_to(ROOT)) if duplicate else None,
            "already_ingested_as": KNOWN_DUPLICATE_OUTPUTS.get(digest),
        }
        if duplicate:
            document.update(status="exact_duplicate_not_reextracted", extracted_records=0)
            documents.append(document)
            continue

        embedded = []
        for page in reader.pages:
            try:
                embedded.append(page.extract_text() or "")
            except Exception:
                embedded.append("")
        use_embedded = sum(has_substantive_embedded_text(text) for text in embedded) >= max(
            1, int(len(embedded) * 0.8)
        )
        extracted = {}
        method = "embedded_pdf_text_layer" if use_embedded else "tesseract_hin_eng"
        if use_embedded:
            extracted = {index: normalized_text(text) for index, text in enumerate(embedded, 1)}
        else:
            if tessdata is None:
                tessdata = locate_tessdata(work_dir)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(
                        extract_ocr_page, pdf, page_number,
                        cache_dir / digest / f"{page_number:04d}.json",
                        tessdata, dpi,
                    ): page_number
                    for page_number in range(1, len(reader.pages) + 1)
                }
                for future in as_completed(futures):
                    page_number, text = future.result()
                    extracted[page_number] = text

        before = len(records)
        blank_pages = []
        for page_number in range(1, len(reader.pages) + 1):
            text = extracted.get(page_number, "")
            if not text:
                blank_pages.append(page_number)
                continue
            records.append(page_record(
                source_id=metadata["source_id"], source_pdf=pdf.relative_to(ROOT),
                source_sha256=digest, page_number=page_number, text=text,
                extraction_method=method, title=metadata["title"],
                author=metadata.get("author"),
                publication_year=metadata.get("publication_year"),
                genre=metadata["genre"],
                source_metadata=metadata,
            ))
        document.update(
            status="extracted_active_experimental",
            extraction_method=method,
            extracted_records=len(records) - before,
            blank_or_no_text_pages=blank_pages,
        )
        documents.append(document)
        print(f"{pdf.name}: {document['extracted_records']} records ({method})", flush=True)

    records.sort(key=lambda row: (row["source_id"], row["pdf_page"]))
    text_counts = Counter(row["text_sha256"] for row in records)
    for row in records:
        duplicate_flags = []
        if text_counts[row["text_sha256"]] > 1:
            duplicate_flags.append("duplicate_text_within_incoming_batch")
        if row["text_sha256"] in prior_hashes:
            duplicate_flags.append("duplicate_text_already_in_corpus")
        row["quality_flags"] = sorted(set(row["quality_flags"] + duplicate_flags))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records),
        encoding="utf-8",
    )
    report = {
        "generated_at": "2026-09-16",
        "policy": "Every non-empty unique-PDF page is active experimental data; quality and rights signals do not remove it.",
        "input_pdfs": len(input_pdfs),
        "unique_pdfs_extracted": sum(document["status"] == "extracted_active_experimental" for document in documents),
        "exact_duplicate_pdfs": sum(document["status"] == "exact_duplicate_not_reextracted" for document in documents),
        "records": len(records),
        "characters": sum(len(row["text"]) for row in records),
        "duplicate_text_records_within_batch": sum(
            text_counts[row["text_sha256"]] > 1 for row in records
        ),
        "text_records_already_in_corpus": sum(
            row["text_sha256"] in prior_hashes for row in records
        ),
        "all_nonempty_records_active_experimentally": all(
            row["experimental_training_eligible"] for row in records
        ),
        "output": str(output.relative_to(ROOT)),
        "documents": documents,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--dpi", type=int, default=220)
    args = parser.parse_args()
    print(json.dumps(
        ingest(args.input, args.output, args.report, args.cache, args.workers, args.dpi),
        ensure_ascii=False, indent=2,
    ))


if __name__ == "__main__":
    main()
