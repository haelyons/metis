#!/usr/bin/env bash
set -euo pipefail
source baseline-published/cuda-env.sh
export CUDA_VISIBLE_DEVICES=0
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0
export OPENMM_CPU_THREADS=1
mkdir -p out/baseline-run out/tmp/cuda-cache out/tmp/cache
export TMPDIR=../tmp
export CUDA_CACHE_PATH=../tmp/cuda-cache
export XDG_CACHE_HOME=../tmp/cache
cd out/baseline-run
export PYTHONPATH=../../baseline-published/python
ln -sfn ../../data/5dfr_solv-cube_equil.pdb 5dfr_solv-cube_equil.pdb
rm -f ensemble.json
/usr/bin/python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 --platform CUDA --out ensemble.json 2>&1 | tee -a ../baseline.stdout.log
