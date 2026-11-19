#!/usr/bin/env python3
"""Generate a map of the Git-tracked project files.

Only tracked files are listed, and no local disk totals are added, so the map
comes out the same on every checkout and a local refresh does not leave
machine-specific changes in the committed file.
"""

from __future__ import annotations

import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "PROJECT_FILE_MAP.md"
EXCLUDED_PARTS = {
    ".git", ".venv", ".cache", ".pytest_cache", "node_modules", "__pycache__",
}


def collect_project_files(root: Path = ROOT, runner=subprocess.run) -> list[str]:
    result = runner(
        ["git", "ls-files", "--cached", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    paths = {
        value.decode("utf-8")
        for value in result.stdout.split(b"\0")
        if value
        and (root / value.decode("utf-8")).exists()
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
        "This index maps the Git-tracked files in the public checkout. Ignored raw "
        "downloads, caches, model weights, and generated corpus payloads are not listed. "
        "Local disk totals vary by checkout; record inventories and hashes live in the "
        "source, ingestion, release, and Hugging Face manifests under `research/`, "
        "`corpus/`, `data/`, and `release/`.",
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


def generate(root: Path = ROOT, runner=subprocess.run) -> Path:
    paths = collect_project_files(root, runner=runner)
    output = root / "PROJECT_FILE_MAP.md"
    output.write_text(render_file_map(paths), encoding="utf-8")
    return output


if __name__ == "__main__":
    print(generate())
