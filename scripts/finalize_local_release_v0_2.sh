#!/usr/bin/env bash
set -euo pipefail

export GARHWALI_RELEASE_VERSION="${GARHWALI_RELEASE_VERSION:-0.2.8}"
exec bash "$(dirname "$0")/finalize_local_release.sh" "$@"
