#!/usr/bin/env bash
set -euo pipefail
# Canonical measured command. The caller and profiler use the shared working directory.
source baseline-published/harness-environment.sh
ls -l "$HARNESS_CUDA_COMPILER" "$HARNESS_CUDA_INCLUDE/cuda_runtime.h" "$HARNESS_CUDA_LIBRARY"
mkdir -p out
# Append complete runs, preserving previous logs and a stable latest-run output path.
run_log=$(mktemp out/baseline-run.XXXXXXXX.log)
ln -sfn "$(basename "$run_log")" out/baseline.stdout.log
./baseline-published/build-mc/MonteCarloMultiGPU --method=streamed --scaling=strong 2>&1 | tee "$run_log"
