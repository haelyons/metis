#!/usr/bin/env bash
set -euo pipefail
# Working directory is the pipeline's shared work directory.
source baseline-published/cuda.env
export CUDA_VISIBLE_DEVICES=''
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
export PINDER_BASE_DIR=data
export PINDER_RELEASE=2024-02
export PINDER_DATA_DIR=data/2024-02
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
mkdir -p out
baseline-published/venv/bin/python baseline-published/run_baseline.py --cases data/cases.json --out out --mpi-np 8 --n-solutions 100 --gpu-count 0 2>&1 | tee -a out/baseline.log
