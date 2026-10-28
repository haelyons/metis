#!/usr/bin/env bash
set -euo pipefail
source baseline-published/cuda-env.sh
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY"
export PATH="$CUDA_BIN:$PATH"
export PYTHONPATH=../../baseline-published/python
export CUDA_VISIBLE_DEVICES=0
export GPU_COUNT=1
export CUDACXX="$CUDA_NVCC"
export OPENMM_CUDA_COMPILER="$CUDA_NVCC"
export CPATH="$CUDA_INCLUDE${CPATH:+:$CPATH}"
export LD_LIBRARY_PATH="${CUDA_LIBRARY%/*}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p out/run
cd out/run
ln -sfn ../../data/5dfr_solv-cube_equil.pdb 5dfr_solv-cube_equil.pdb
log=$(mktemp command.XXXXXXXX.log)
printf '%s\n' 'configuration: platform=CUDA precision=single DeterministicForces=true gpu_count=1 CUDA_VISIBLE_DEVICES=0 replicas=8 steps=25000 seed0=1000 step_fs=4 energy_interval=250 atoms=23558 PME cutoff_nm=0.9 HBonds hydrogen_mass_amu=1.5 LangevinMiddleIntegrator temperature_K=300 friction_per_ps=1 constraint_tolerance=1e-5' | tee "$log"
python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 2>&1 | tee -a "$log"
cp "$log" command.log
