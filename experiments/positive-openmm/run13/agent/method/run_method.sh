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


: "${METHOD_DIR:?METHOD_DIR is required}"
: "${BASELINE_DIR:?BASELINE_DIR is required}"
export PYTHONNOUSERSITE=1
export PYTHONUNBUFFERED=1
export PYTHONPATH="$METHOD_DIR/python"
export OMP_NUM_THREADS=1
export OPENMM_CPU_THREADS=1
export GPU_COUNT=1
mkdir -p out "${EVAL_OUT:-${METHOD_OUT:-out}}"
# No fallback to non-MPS execution: all workers must use the provisioned daemon.
echo get_server_list | nvidia-cuda-mps-control >/dev/null
/usr/bin/python3 "$METHOD_DIR/dhfr_concurrent.py"
