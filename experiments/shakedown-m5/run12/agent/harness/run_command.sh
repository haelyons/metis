#!/usr/bin/env bash
set -euo pipefail
ROOT=$(pwd -P)
BASELINE=${BASELINE_DIR:-$ROOT/baseline-published}
source "$ROOT/data/cuda-env.sh"
ls -l "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY" >/dev/null
export CUDA_VISIBLE_DEVICES=0
mkdir -p "$ROOT/out/command"
LOG=$(mktemp "$ROOT/out/command/run.XXXXXXXX.log")
ln -sfn "$(basename "$LOG")" "$ROOT/out/command/latest.log"
cd "$BASELINE"
set +e
./build-mc/MonteCarloMultiGPU --method=streamed --scaling=strong 2>&1 | tee "$LOG"
status=${PIPESTATUS[0]}
set -e
printf '%s\n' "$status" > "$LOG.status"
exit "$status"
