#!/usr/bin/env python3
"""Generate an exhaustive map of Git-visible project files."""

from __future__ import annotations

import subprocess
import os
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "PROJECT_FILE_MAP.md"
EXCLUDED_PARTS = {
    ".git", ".venv", ".cache", ".pytest_cache", "node_modules", "__pycache__",
}


def collect_project_files(root: Path = ROOT, runner=subprocess.run) -> list[str]:
    result = runner(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    paths = {
        value.decode("utf-8")
        for value in result.stdout.split(b"\0")
        if value
    }
    return sorted(
        path for path in paths
        if not EXCLUDED_PARTS.intersection(Path(path).parts)
    )


def render_file_map(paths: list[str]) -> str:
    groups: dict[str, list[str]] = defaultdict(list)
    for path in sorted(set(paths)):
        parts = Path(path).parts
        section = parts[0] if len(parts) > 1 else "Root files"
        groups[section].append(path)

    lines = [
        "# Project File Map",
        "",
        "This generated index maps every Git-tracked and non-ignored project file. "
        "Ignored raw downloads, caches, model weights, and generated corpus payloads "
        "are not line-listed; their on-disk totals are summarized below, and their "
        "record inventories and hashes live in source, ingestion, release, and Hugging Face "
        "manifests under `research/`, `corpus/`, `data/`, and `release/`.",
        "",
        f"Files indexed: **{len(set(paths)):,}**.",
        "",
        "Regenerate after adding, moving, or removing project files with:",
        "",
        "```bash",
        "python scripts/generate_project_file_map.py",
        "```",
        "",
    ]
    for section in sorted(groups, key=lambda value: (value != "Root files", value.casefold())):
        lines.extend((f"## `{section}/`" if section != "Root files" else "## Root files", ""))
        lines.extend(f"- `{path}`" for path in groups[section])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def collect_disk_inventory(root: Path = ROOT, listed_paths: list[str] | None = None) -> dict:
    """Count every workspace file except version-control and runtime caches."""
    listed = set(listed_paths or collect_project_files(root))
    total_files = 0
    total_bytes = 0
    unlisted_files = 0
    unlisted_bytes = 0
    groups: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    for base, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in EXCLUDED_PARTS]
        base_path = Path(base)
        for name in files:
            path = base_path / name
            relative = path.relative_to(root).as_posix()
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            total_files += 1
            total_bytes += size
            if relative in listed:
                continue
            unlisted_files += 1
            unlisted_bytes += size
            parts = Path(relative).parts
            if len(parts) == 1:
                group = "Root-level payloads"
            elif len(parts) == 2:
                group = f"{parts[0]}/{parts[1]}/"
            else:
                group = f"{parts[0]}/{parts[1]}/…/"
            groups[group][0] += 1
            groups[group][1] += size

    return {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "listed_files": len(listed),
        "unlisted_files": unlisted_files,
        "unlisted_bytes": unlisted_bytes,
        "groups": dict(groups),
    }


def append_disk_inventory(document: str, inventory: dict) -> str:
    lines = [
        "## Workspace payload inventory",
        "",
        "The detailed index above lists all tracked and non-ignored files. This "
        "inventory also accounts for ignored/generated files without copying a "
        "226,000-plus-row binary-path dump into the Markdown map.",
        "",
        f"- Workspace files counted: **{inventory['total_files']:,}**.",
        "- Excluded from the count: Git internals, virtual environments, and runtime caches.",
        f"- Detailed file paths listed above: **{inventory['listed_files']:,}**.",
        f"- Ignored or otherwise unlisted payload files: **{inventory['unlisted_files']:,}** ({inventory['unlisted_bytes']:,} bytes).",
        f"- Total workspace bytes counted: **{inventory['total_bytes']:,}**.",
        "",
        "| Payload directory | Files | Bytes |",
        "| --- | ---: | ---: |",
    ]
    lines.extend(
        f"| `{name}` | {counts[0]:,} | {counts[1]:,} |"
        for name, counts in sorted(inventory["groups"].items())
    )
    return document.rstrip() + "\n\n" + "\n".join(lines) + "\n"


def generate(root: Path = ROOT, runner=subprocess.run) -> Path:
    paths = collect_project_files(root, runner=runner)
    output = root / "PROJECT_FILE_MAP.md"
    document = append_disk_inventory(render_file_map(paths), collect_disk_inventory(root, paths))
    output.write_text(document, encoding="utf-8")
    return output


if __name__ == "__main__":
    print(generate())
