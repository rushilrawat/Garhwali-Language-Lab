#!/usr/bin/env python3
"""Prepare a versioned Hugging Face upload without replacing older files."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from pathlib import PurePosixPath
import yaml

from garhwali_lab.hashing import sha256_file as sha256
from garhwali_lab.version import corpus_release_version, ensure_unpublished_corpus_version


ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = corpus_release_version()
DEFAULT_PACKAGE = ROOT / f"data/huggingface/garhwali-language-lab-v{RELEASE_VERSION}-staging"
DEFAULT_OUTPUT = ROOT / f"data/huggingface/garhwali-corpus-v{RELEASE_VERSION}-additive-upload"
DEFAULT_PLAN = ROOT / f"data/huggingface/garhwali-corpus-v{RELEASE_VERSION}-upload-plan.json"
PAYLOAD_SUFFIXES = {
    ".pdf", ".doc", ".docx", ".epub", ".mp3", ".wav", ".m4a", ".flac",
    ".ogg", ".mp4", ".mov", ".webm", ".zip", ".tar", ".gz", ".7z",
}


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
        Path("licenses/PahariLI-Apache-2.0.txt"),
    }
    declared.update(
        path for path in optional_support_files if (package / path).is_file()
    )
    if any(
        config.split("/", 1)[0] == "paharili_gbm"
        for config in manifest.get("configs", {})
    ) and Path("licenses/PahariLI-Apache-2.0.txt") not in declared:
        raise ValueError("PahariLI data requires its upstream license text in the package")
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


def preflight_candidate(package: Path) -> dict:
    """Run the full record-level release validator without writing into the package."""
    with tempfile.TemporaryDirectory(prefix="garhwali-hf-preflight-") as directory:
        report_path = Path(directory) / "report.json"
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_hf_package_cloud.py"),
                "--package", str(package),
                "--output", str(report_path),
            ],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if not report_path.is_file():
            detail = result.stderr.strip() or "validator produced no report"
            raise ValueError(f"Candidate preflight could not complete: {detail}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if result.returncode or report.get("status") != "passed":
            errors = report.get("errors") or [result.stderr.strip()]
            raise ValueError(f"Candidate full preflight failed: {errors[:5]}")
        manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
        if (
            report.get("release_id") != manifest.get("release_id")
            or not report.get("record_schema_version")
            or report.get("record_schema_version")
            != manifest.get("record_schema_version")
        ):
            raise ValueError("Candidate preflight and manifest provenance disagree")
        return {
            "run_id": report["run_id"],
            "status": report["status"],
            "report_sha256": sha256(report_path),
            "record_schema_version": report.get("record_schema_version"),
            "config_count": len(report.get("configs", {})),
        }


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


def _front_matter(card: str) -> tuple[str, str, str]:
    """Split a dataset card into (front matter, separator+body, prefix)."""
    if not card.startswith("---\n"):
        raise ValueError("Dataset card has no YAML front matter")
    end = card.index("\n---\n", 4)
    return card[4:end], card[end:], "---\n"


def _config_blocks(front: str) -> dict[str, str]:
    """Return each '- config_name:' block of the top-level configs list, verbatim."""
    blocks: dict[str, str] = {}
    lines = front.split("\n")
    in_configs = False
    current = None
    for line in lines:
        if line.startswith("configs:"):
            in_configs = True
            continue
        if in_configs and line and not line.startswith((" ", "-")):
            break
        if in_configs and line.startswith("- config_name:"):
            current = line.split(":", 1)[1].strip()
            blocks[current] = line
        elif in_configs and current is not None:
            blocks[current] += "\n" + line
    return {name: block.rstrip("\n") for name, block in blocks.items()}


def carry_forward_configs(card: str, previous_card: str, prefix: str) -> tuple[str, list[str]]:
    """Keep configs the live card declares from earlier releases.

    The upload replaces the root card, and the card decides which configs the
    Hub shows. A config the new card lacks, whose files all live under an
    earlier ``releases/`` prefix, would silently disappear from the Hub even
    though its files stay in the repo. Such configs are appended, with their
    dataset_info entry, exactly as the live card declares them.
    """
    front, rest, opener = _front_matter(card)
    previous_front, _, _ = _front_matter(previous_card)
    new_blocks = _config_blocks(front)
    previous_blocks = _config_blocks(previous_front)
    previous_meta = yaml.safe_load(previous_front) or {}
    previous_paths = {
        config["config_name"]: [item["path"] for item in config.get("data_files", [])]
        for config in previous_meta.get("configs", [])
    }
    carried = [
        name for name in previous_blocks
        if name not in new_blocks
        and previous_paths.get(name)
        and all(
            path.startswith("releases/") and not path.startswith(f"{prefix}/")
            for path in previous_paths[name]
        )
    ]
    if not carried:
        return card, []
    lines = front.split("\n")
    info_index = next(
        (index for index, line in enumerate(lines) if line.startswith("dataset_info:")), None
    )
    if info_index is None:
        raise ValueError("New card has no dataset_info line to extend")
    insert = "\n".join(previous_blocks[name] for name in carried).split("\n")
    lines[info_index:info_index] = insert
    info_index += len(insert)
    info_value = lines[info_index].split(":", 1)[1].strip()
    if not info_value.startswith("["):
        raise ValueError("Expected dataset_info as a one-line JSON list in the new card")
    info = json.loads(info_value)
    previous_info = {
        entry.get("config_name"): entry for entry in previous_meta.get("dataset_info") or []
    }
    info.extend(previous_info[name] for name in carried if name in previous_info)
    lines[info_index] = "dataset_info: " + json.dumps(info, ensure_ascii=False, separators=(",", ":"))
    merged_front = "\n".join(lines)
    merged = yaml.safe_load(merged_front)
    names = [config["config_name"] for config in merged["configs"]]
    if len(names) != len(set(names)) or not set(carried) <= set(names):
        raise ValueError("Carried-forward configs did not merge cleanly")
    return opener + merged_front + rest, carried


def prepare(
    package: Path, output: Path, plan_path: Path, prefix: str | None = None,
    previous_card: Path | None = None,
) -> dict:
    package = package.resolve()
    output = output.resolve()
    plan_path = plan_path.resolve()
    release_id = json.loads(
        (package / "manifest.json").read_text(encoding="utf-8")
    )["release_id"]
    release_match = re.fullmatch(
        r"garhwali-language-lab-v(?P<version>\d+\.\d+\.\d+)", release_id
    )
    if not release_match:
        raise ValueError(f"Invalid release_id: {release_id}")
    version = release_match.group("version")
    ensure_unpublished_corpus_version(version)
    expected_prefix = f"releases/v{version}"
    prefix = prefix or expected_prefix
    prefix_path = PurePosixPath(prefix)
    if (
        not prefix
        or prefix_path.is_absolute()
        or any(part in {"", ".", ".."} for part in prefix_path.parts)
        or "\\" in prefix
    ):
        raise ValueError("Release prefix must be a safe relative POSIX path")
    if prefix != expected_prefix:
        raise ValueError(
            f"Release prefix must match manifest release_id: {expected_prefix}"
        )
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing upload tree: {output}")
    files = validate_package(package)
    preflight = preflight_candidate(package)
    card = version_card((package / "README.md").read_text(encoding="utf-8"), prefix)
    carried: list[str] = []
    if previous_card is not None:
        card, carried = carry_forward_configs(
            card, Path(previous_card).read_text(encoding="utf-8"), prefix
        )
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
        "input_manifest_sha256": sha256(package / "manifest.json"),
        "record_schema_version": preflight["record_schema_version"],
        "candidate_preflight": preflight,
        "strategy": "add files under a versioned prefix and update the root dataset card; no deletion operations",
        "release_prefix": prefix,
        "previous_card_checked": previous_card is not None,
        "previous_card_sha256": sha256(Path(previous_card)) if previous_card is not None else None,
        "carried_forward_configs": carried,
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
    parser.add_argument(
        "--previous-card", type=Path,
        help="the live dataset card (README.md) downloaded from the Hub; configs it "
             "declares from earlier releases are kept",
    )
    parser.add_argument(
        "--allow-dropping-configs", action="store_true",
        help="skip the live-card check (configs absent from the new card leave the Hub)",
    )
    args = parser.parse_args()
    if args.previous_card is None and not args.allow_dropping_configs:
        parser.error("pass --previous-card <live README.md> (or --allow-dropping-configs)")
    plan = prepare(args.package, args.output, args.plan, args.prefix, args.previous_card)
    print(json.dumps({key: value for key, value in plan.items() if key != "uploads"}, indent=2))


if __name__ == "__main__":
    main()
