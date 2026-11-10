"""Release version resolution.

``release/versions.json`` is the single source of truth. The environment
variable ``GARHWALI_RELEASE_VERSION`` still overrides either line for one run.

Two lines exist and must not be confused:

* ``corpus``: the public Hugging Face corpus (``releases/v0.2.x``).
* ``bundle``: the frozen GitHub release bundle under ``release/v0.1.x``.
"""

import json
import os
import sys

from garhwali_lab.paths import ROOT

VERSIONS_FILE = ROOT / "release" / "versions.json"
ENV_VAR = "GARHWALI_RELEASE_VERSION"
ALLOW_REBUILD_ENV = "GARHWALI_ALLOW_PUBLISHED_REBUILD"


class PublishedVersionError(RuntimeError):
    pass


def _load() -> dict:
    return json.loads(VERSIONS_FILE.read_text(encoding="utf-8"))


def _from_env() -> str | None:
    value = os.environ.get(ENV_VAR)
    return value.removeprefix("v") if value else None


def corpus_default_version() -> str:
    return _load()["corpus"]["next"]


def corpus_release_version() -> str:
    return _from_env() or corpus_default_version()


def bundle_release_version() -> str:
    return _from_env() or _load()["bundle"]["current"]


def is_published_corpus_version(version: str) -> bool:
    data = _load()["corpus"]
    version = version.removeprefix("v")
    return version in data["published"] or version in data.get("retired_labels", [])


def ensure_unpublished_corpus_version(version: str) -> None:
    """Refuse to rebuild or re-upload a version that is already public."""
    if is_published_corpus_version(version) and os.environ.get(ALLOW_REBUILD_ENV) != "1":
        raise PublishedVersionError(
            f"Corpus version v{version.removeprefix('v')} is already published. Set "
            f"{ENV_VAR} to a new version (next unreleased: v{corpus_default_version()}), "
            f"or set {ALLOW_REBUILD_ENV}=1 to rebuild it deliberately."
        )


if __name__ == "__main__":
    line = sys.argv[1] if len(sys.argv) > 1 else "corpus"
    print(corpus_release_version() if line == "corpus" else bundle_release_version())
