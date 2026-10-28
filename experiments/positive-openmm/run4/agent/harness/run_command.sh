#!/usr/bin/env bash
set -euo pipefail
source baseline-published/cuda-env.sh
ls -l "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export OPENMM_CUDA_COMPILER="$CUDACXX"
export CUDA_VISIBLE_DEVICES=0
export PYTHONDONTWRITEBYTECODE=1
mkdir -p out
run_dir=$(mktemp -d out/run.XXXXXXXX)
printf '%s\n' "$run_dir" > out/last_run.txt
ln -s ../../baseline-published/dhfr_ensemble.py "$run_dir/dhfr_ensemble.py"
ln -s ../../data/5dfr_solv-cube_equil.pdb "$run_dir/5dfr_solv-cube_equil.pdb"
cd "$run_dir"
export PYTHONPATH=../../baseline-published/python
export CUDA_CACHE_PATH=cuda-cache
mkdir -p "$CUDA_CACHE_PATH"
printf 'working_directory=%s CUDA_VISIBLE_DEVICES=%s gpu_count=1\n' "$run_dir" "$CUDA_VISIBLE_DEVICES" | tee configuration.log
printf '%s\n' 'command=python3 dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000' | tee -a configuration.log
# Synchronous energy queries and context destruction complete GPU work before exit.
python3 dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 2>&1 | tee command.log
