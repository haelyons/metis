#!/usr/bin/env bash
set -uo pipefail
script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# Output inspection only: never invoke a driver, workload, or method script.
exec python3 "$script_dir/check_outputs.py"
