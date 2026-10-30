#!/usr/bin/env bash
set -euo pipefail
# Working directory: shared invocation directory. CPU evaluator uses zero GPUs.
# Fixed input layout: out/eval_dir/published/<93 IDs>/apo_decoys/model_<1..5>.pdb.
CUDA_ROOT=''
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -f "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
        CUDA_ROOT=$root
        break
    fi
done
if [[ -n "$CUDA_ROOT" ]]; then
    export CUDACXX="$CUDA_ROOT/bin/nvcc" CUDAToolkit_ROOT="$CUDA_ROOT"
    export CUDA_INCLUDE_DIR="$CUDA_ROOT/include" CUDA_LIBRARY_DIR="$CUDA_ROOT/lib64"
    export PATH="$CUDA_ROOT/bin:$PATH"
else
    export CUDACXX=/usr/bin/nvcc CUDA_INCLUDE_DIR=/usr/include CUDA_LIBRARY_DIR=/usr/lib/x86_64-linux-gnu
fi
export LD_LIBRARY_PATH="$CUDA_LIBRARY_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
ls "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export CUDA_VISIBLE_DEVICES='' PINDER_RELEASE=2024-02 PINDER_BASE_DIR=./out PINDER_DATA_DIR=./out/pinder_data
export PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1
export XDG_CACHE_HOME=./out/cache MPLCONFIGDIR=./out/matplotlib TMPDIR=./out/tmp
mkdir -p out/tmp out/cache out/matplotlib
exec baseline-published/venv/bin/pinder_eval --eval_dir out/eval_dir --custom_index data/custom_index.parquet < data/confirmation.txt >> out/pinder_eval.log 2>&1
