#!/usr/bin/env bash
set -euo pipefail
# Invoke from the shared working directory. All run-directory paths stay relative.
source baseline-published/cuda.env
export CUDA_VISIBLE_DEVICES=0
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
mkdir -p out/run out/tmp out/cuda-cache
cd out/run
export PYTHONPATH=../../baseline-published/python
export TMPDIR=../tmp
export CUDA_CACHE_PATH=../cuda-cache
ln -sfn ../../data/5dfr_solv-cube_equil.pdb 5dfr_solv-cube_equil.pdb
# One visible GPU; default CUDA device 0. Published fixed work and seed mapping.
/usr/bin/python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 --platform CUDA --out ensemble.json 2>&1 | tee -a ../baseline.log
