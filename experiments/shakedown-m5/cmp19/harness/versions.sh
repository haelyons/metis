#!/usr/bin/env bash
# Prints each arm's and the evaluator's version and main executable (relative to the shared run directory or absolute).
set -euo pipefail
pin=$(git -C baseline-published rev-parse HEAD)
py=$(python3 --version 2>&1)
printf '{"A0": {"version": "cuda-samples %s MonteCarloMultiGPU", "executable": "baseline-published/build-mc/MonteCarloMultiGPU"}, "A1": {"version": "cuda-samples %s MonteCarloMultiGPU", "executable": "baseline-published/build-mc/MonteCarloMultiGPU"}, "evaluator": {"version": "%s", "executable": "/usr/bin/python3"}}\n' "$pin" "$pin" "$py"
