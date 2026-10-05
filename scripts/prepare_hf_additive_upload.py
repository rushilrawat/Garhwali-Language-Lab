#!/usr/bin/env python3
"""Prepare a versioned Hugging Face upload without replacing older files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from pathlib import PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = os.environ.get('GARHWALI_RELEASE_VERSION', '0.2.1').removeprefix('v')
DEFAULT_PACKAGE = ROOT / f"data/huggingface/garhwali-language-lab-v{RELEASE_VERSION}-staging"
DEFAULT_OUTPUT = ROOT / f"data/huggingface/garhwali-corpus-v{RELEASE_VERSION}-additive-upload"
DEFAULT_PLAN = ROOT / f"data/huggingface/garhwali-corpus-v{RELEASE_VERSION}-upload-plan.json"
PAYLOAD_SUFFIXES = {
    ".pdf", ".doc", ".docx", ".epub", ".mp3", ".wav", ".m4a", ".flac",
    ".ogg", ".mp4", ".mov", ".webm", ".zip", ".tar", ".gz", ".7z",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_files(package: Path) -> list[Path]:
    return sorted(path for path in package.rglob("*") if path.is_file())


def validate_package(package: Path) -> list[Path]:
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("profile") != "public":
        raise ValueError("Only the rights-filtered public profile may be prepared for upload")
    if manifest.get("include_audio") or manifest.get("linked_audio_files", 0):
        raise ValueError("This additive text release must not contain audio payloads")
    if manifest.get("removed_audio_files", 0):
        raise ValueError("A package claiming removed audio files needs separate review")

    declared: set[Path] = {
        Path(name) for name in ("README.md", "ATTRIBUTION.md", "LICENSE_POLICY.md",
                                "REMOVAL_POLICY.md", "manifest.json",
                                "DEVELOPER_QUICKSTART.md", "DATASET_SCHEMA.md",
                                "search_garhwali_lexicon.py",
                                "reference_index_manifest.json",
                                "research/text-rights-resolution-2026-09-30.md")
    }
    optional_support_files = {
        Path("research/huggingface-upstream-split-overlap-2026-10-05.json"),
        Path("research/huggingface-upstream-split-overlap-2026-10-05.md"),
    }
    declared.update(
        path for path in optional_support_files if (package / path).is_file()
    )
    for config_name, details in manifest.get("configs", {}).items():
        family = config_name.split("/", 1)[0]
        for filename in details.get("files", []):
            relative = Path("data") / family / filename
            path = package / relative
            if not path.is_file():
                raise ValueError(f"Missing manifest file: {relative}")
            expected = details.get("file_sha256", {}).get(filename)
            if expected and sha256(path) != expected:
                raise ValueError(f"Checksum mismatch: {relative}")
            declared.add(relative)

    reference = json.loads(
        (package / "reference_index_manifest.json").read_text(encoding="utf-8")
    )
    if reference.get("profile") != "metadata_only_complete_reference_index":
        raise ValueError("The public reference tables are not declared metadata-only")
    for details in reference.get("tables", {}).values():
        relative = Path(details["file"])
        path = package / relative
        if not path.is_file() or sha256(path) != details.get("sha256"):
            raise ValueError(f"Reference-index file missing or changed: {relative}")
        declared.add(relative)

    actual = {path.relative_to(package) for path in package_files(package)}
    if actual != declared:
        extras = sorted(str(path) for path in actual - declared)
        missing = sorted(str(path) for path in declared - actual)
        raise ValueError(f"Package inventory mismatch; extra={extras}, missing={missing}")
    forbidden = [str(path) for path in actual if path.suffix.casefold() in PAYLOAD_SUFFIXES]
    if forbidden:
        raise ValueError(f"Unexpected source/audio payload files: {forbidden}")
    return [package / path for path in sorted(actual)]


def version_card(source: str, prefix: str) -> str:
    old_path = "path: data/"
    new_path = f"path: {prefix}/data/"
    if old_path not in source:
        raise ValueError("Dataset card has no relative data_files paths to version")
    source = source.replace(old_path, new_path)
    asset = f"https://huggingface.co/datasets/rushilrawat/garhwali-corpus/resolve/main/{prefix}/"
    source = source.replace(
        "(research/text-rights-resolution-2026-09-30.md)",
        f"({asset}research/text-rights-resolution-2026-09-30.md)",
    )
    return source.replace(
        "(reference_index_manifest.json)",
        f"({asset}reference_index_manifest.json)",
    ).replace(
        "(DEVELOPER_QUICKSTART.md)",
        f"({asset}DEVELOPER_QUICKSTART.md)",
    ).replace(
        "(DATASET_SCHEMA.md)",
        f"({asset}DATASET_SCHEMA.md)",
    ).replace(
        "(search_garhwali_lexicon.py)",
        f"({asset}search_garhwali_lexicon.py)",
    )


def prepare(
    package: Path, output: Path, plan_path: Path, prefix: str | None = None
) -> dict:
    package = package.resolve()
    output = output.resolve()
    plan_path = plan_path.resolve()
    release_id = json.loads(
        (package / "manifest.json").read_text(encoding="utf-8")
    )["release_id"]
    version = release_id.removeprefix("garhwali-language-lab-v")
    prefix = prefix or f"releases/v{version}"
    prefix_path = PurePosixPath(prefix)
    if (
        not prefix
        or prefix_path.is_absolute()
        or any(part in {"", ".", ".."} for part in prefix_path.parts)
        or "\\" in prefix
    ):
        raise ValueError("Release prefix must be a safe relative POSIX path")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing upload tree: {output}")
    files = validate_package(package)
    card = version_card((package / "README.md").read_text(encoding="utf-8"), prefix)
    output.mkdir(parents=True)
    uploads = []
    release_root = output / prefix
    for source in files:
        relative = source.relative_to(package)
        target = release_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative.name == "README.md":
            target.write_text(card, encoding="utf-8")
        else:
            os.link(source, target)
        uploads.append({
            "path_in_repo": (Path(prefix) / relative).as_posix(),
            "bytes": target.stat().st_size,
            "sha256": sha256(target),
        })
    root_card = output / "README.md"
    root_card.write_text(card, encoding="utf-8")
    uploads.append({"path_in_repo": "README.md", "bytes": root_card.stat().st_size,
                    "sha256": sha256(root_card)})
    plan = {
        "repo_id": "rushilrawat/garhwali-corpus",
        "repo_type": "dataset",
        "release_id": release_id,
        "strategy": "add files under a versioned prefix and update the root dataset card; no deletion operations",
        "release_prefix": prefix,
        "file_count": len(uploads),
        "payload_bytes": sum(item["bytes"] for item in uploads),
        "uploads": uploads,
        "command": f"hf upload rushilrawat/garhwali-corpus {output} . --repo-type dataset --commit-message 'Add Garhwali corpus v{version}'",
    }
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--prefix")
    args = parser.parse_args()
    plan = prepare(args.package, args.output, args.plan, args.prefix)
    print(json.dumps({key: value for key, value in plan.items() if key != "uploads"}, indent=2))


if __name__ == "__main__":
    main()
