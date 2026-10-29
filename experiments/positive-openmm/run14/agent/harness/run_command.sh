#!/usr/bin/env bash
set -euo pipefail
# Select only layouts discovered by the box probe; prefer complete roots.
CUDA_ROOT_SELECTED=
for candidate in /usr/local/cuda /usr/lib/cuda; do
    if [[ -f "$candidate/bin/nvcc" && -f "$candidate/include/cuda_runtime.h" && -f "$candidate/lib64/libcudart.so" ]]; then
        CUDA_ROOT_SELECTED=$candidate
        break
    fi
done
if [[ -n "$CUDA_ROOT_SELECTED" ]]; then
    export CUDACXX="$CUDA_ROOT_SELECTED/bin/nvcc"
    export CUDA_INCLUDE_DIR="$CUDA_ROOT_SELECTED/include"
    export CUDA_LIBRARY_DIR="$CUDA_ROOT_SELECTED/lib64"
    export CUDAToolkit_ROOT="$CUDA_ROOT_SELECTED"
    export PATH="$CUDA_ROOT_SELECTED/bin:/usr/bin:/bin"
else
    export CUDACXX=/usr/bin/nvcc
    export CUDA_INCLUDE_DIR=/usr/include
    export CUDA_LIBRARY_DIR=/usr/lib/x86_64-linux-gnu
    export PATH=/usr/bin:/bin
fi
ls "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export LD_LIBRARY_PATH="$CUDA_LIBRARY_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CUDA_VISIBLE_DEVICES=0
export GPU_COUNT=1
export PYTHONNOUSERSITE=1

mkdir -p out/run
cd out/run
ln -sfn ../../data/5dfr_solv-cube_equil.pdb 5dfr_solv-cube_equil.pdb
export PYTHONPATH=../../baseline-published/python
unset OPENMM_PLUGIN_DIR
# OpenMM energy queries synchronize CUDA; the published driver destroys every context before its timer ends.
/usr/bin/python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 --platform CUDA --out ensemble.json >> ../baseline.log 2>&1
