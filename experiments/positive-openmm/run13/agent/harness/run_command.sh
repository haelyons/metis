#!/usr/bin/env bash
set -euo pipefail
select_cuda() {
    local root
    CUDA_NVCC=
    for root in /usr/local/cuda /usr/lib/cuda; do
        if [[ -x "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
            CUDA_NVCC="$root/bin/nvcc"
            CUDA_INCLUDE="$root/include"
            CUDA_LIBRARY="$root/lib64"
            export CUDAToolkit_ROOT="$root"
            break
        fi
    done
    if [[ -z "${CUDA_NVCC:-}" ]]; then
        CUDA_NVCC=/usr/bin/nvcc
        CUDA_INCLUDE=/usr/include
        CUDA_LIBRARY=/usr/lib/x86_64-linux-gnu
    fi
    ls "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY/libcudart.so"
    export PATH="${CUDA_NVCC%/*}:$PATH"
    export LD_LIBRARY_PATH="$CUDA_LIBRARY${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    export OPENMM_CUDA_COMPILER="$CUDA_NVCC"
}
select_cuda

export CUDA_VISIBLE_DEVICES=0
export GPU_COUNT=1
export PYTHONNOUSERSITE=1
export PYTHONUNBUFFERED=1
mkdir -p out
run_dir=$(mktemp -d out/baseline.XXXXXXXX)
printf '%s\n' "$run_dir" > out/latest-baseline-run.txt
for name in 5dfr_solv-cube_equil.pdb amber99sb.xml tip3p.xml; do
    ln -s "../../data/$name" "$run_dir/$name"
done
cd "$run_dir"
mkdir -p tmp cuda-cache
export TMPDIR=tmp
export CUDA_CACHE_PATH=cuda-cache
export PYTHONPATH=../../baseline-published/python
/usr/bin/python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 > stdout.log 2> stderr.log
