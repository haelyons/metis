#!/usr/bin/env bash
set -euo pipefail
# Invocation directory is the shared work directory; exactly one visible GPU.
source baseline-published/runtime.env
ls "$CUDA_COMPILER" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export CUDA_VISIBLE_DEVICES=0 GPU_COUNT=1
export OPENMM_CPU_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
mkdir -p out/baseline-run/cuda-cache
cd out/baseline-run
export PYTHONPATH=../../baseline-published/python
export OPENMM_CACHE_DIR=cuda-cache CUDA_CACHE_PATH=cuda-cache
ln -sfn ../../data/5dfr_solv-cube_equil.pdb 5dfr_solv-cube_equil.pdb
# Append logs across retries; remove stale result so failures cannot reuse it.
rm -f ensemble.json
/usr/bin/python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 --out ensemble.json 2>&1 | tee -a stdout.log
