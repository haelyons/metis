#!/usr/bin/env bash
set -uo pipefail
TEST_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONDONTWRITEBYTECODE=1
# Output inspection only: never invoke BASELINE_DIR or METHOD_DIR programs.
python3 "$TEST_DIR/check_outputs.py"
