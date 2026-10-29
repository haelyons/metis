#!/usr/bin/env bash
set -euo pipefail
source data/toolkit.env
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
mkdir -p out/run out/cuda-cache
cd out/run
export CUDA_CACHE_PATH=../cuda-cache
ln -sfn ../../data/5dfr_solv-cube_equil.pdb 5dfr_solv-cube_equil.pdb
exec ../../baseline-published/.venv/bin/python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 >> stdout.log 2>> stderr.log
