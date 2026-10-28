#!/usr/bin/env bash
set -euo pipefail
source baseline-published/toolkit.env
export CUDA_VISIBLE_DEVICES=0
export PYTHONDONTWRITEBYTECODE=1
mkdir -p out/run
ls "$CUDACXX" "$CUDA_INCLUDE_DIRS/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so" >> out/run/command.log 2>&1
ln -sfn ../../data/5dfr_solv-cube_equil.pdb out/run/5dfr_solv-cube_equil.pdb
cd out/run
exec ../../baseline-published/venv/bin/python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 --platform CUDA --out ensemble.json >> command.log 2>&1
