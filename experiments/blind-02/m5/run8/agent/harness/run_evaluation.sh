#!/usr/bin/env bash
set -euo pipefail
: "${EVAL_OUT:?}" "${EVAL_PROTOCOL:?}" "${EVAL_INPUTS:?}" "${EVAL_SEEDS:?}"
mkdir -p "$EVAL_OUT"
exec python3 -B harness/run_evaluation.py >> "$EVAL_OUT/evaluation.log" 2>&1
