#!/usr/bin/env bash
set -euo pipefail
source baseline-published/cuda-env.sh
ls "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export CUDA_VISIBLE_DEVICES=0
export PYTHONNOUSERSITE=1
mkdir -p out/command
cd out/command
ln -sfn ../../data/5dfr_solv-cube_equil.pdb 5dfr_solv-cube_equil.pdb
rm -f ensemble.json
if [[ -f stdout.log ]]; then
    mkdir -p logs
    mv stdout.log "$(mktemp logs/stdout.XXXXXX.log)"
fi
../../baseline-published/venv/bin/python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 2>&1 | tee stdout.log
