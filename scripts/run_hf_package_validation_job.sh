#!/usr/bin/env bash
set -euo pipefail

python /workspace/scripts/validate_hf_package_cloud.py \
  --package /package \
  --output /output
