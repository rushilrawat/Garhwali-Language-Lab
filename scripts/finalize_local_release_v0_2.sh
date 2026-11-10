#!/usr/bin/env bash
set -euo pipefail

export GARHWALI_RELEASE_VERSION="${GARHWALI_RELEASE_VERSION:-$(PYTHONPATH=scripts "${PYTHON_BIN:-.venv/bin/python}" -m garhwali_lab.version corpus)}"
exec bash "$(dirname "$0")/finalize_local_release.sh" "$@"
