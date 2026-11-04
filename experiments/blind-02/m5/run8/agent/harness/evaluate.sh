#!/usr/bin/env bash
set -euo pipefail
: "${CMP_ARM_OUT:?}" "${CMP_PRIVATE:?}" "${CMP_EVAL_OUT:?}" "${CMP_INPUT:?}"
mkdir -p "$CMP_EVAL_OUT"
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$CMP_EVAL_OUT/tmp" XDG_CACHE_HOME="$CMP_EVAL_OUT/cache" PINDER_BASE_DIR="$CMP_EVAL_OUT/pinder-cache" MPLCONFIGDIR="$CMP_EVAL_OUT/mpl"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME" "$PINDER_BASE_DIR" "$MPLCONFIGDIR"
exec baseline-published/eval-venv/bin/python harness/evaluate_dockq.py >> "$CMP_EVAL_OUT/evaluator.log" 2>&1
