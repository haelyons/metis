#!/usr/bin/env bash
set -euo pipefail
source baseline-published/cuda.env
ls -l "$OPENMM_CUDA_COMPILER" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export CUDA_VISIBLE_DEVICES=0
export PYTHONNOUSERSITE=1
unset CUDA_MPS_ACTIVE_THREAD_PERCENTAGE CUDA_MPS_PIPE_DIRECTORY CUDA_MPS_LOG_DIRECTORY
mkdir -p out/run
if [[ -f out/run_command.log ]]; then cp out/run_command.log "out/run_command.$(date +%s%N).log"; fi
if [[ -f out/run/ensemble.json ]]; then mv out/run/ensemble.json "out/run/ensemble.$(date +%s%N).json"; fi
(
    cd out/run
    export PYTHONPATH=../../baseline-published/python
    export CUDA_CACHE_PATH=../cuda-cache
    export TMPDIR=../tmp
    mkdir -p "$CUDA_CACHE_PATH" "$TMPDIR"
    for name in 5dfr_solv-cube_equil.pdb amber99sb.xml tip3p.xml; do
        ln -sfn "../../data/$name" "$name"
    done
    command=(python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000)
    printf 'configuration: cwd=out/run gpu_count=1 CUDA_VISIBLE_DEVICES=%s replicas=8 steps=25000 seed0=1000 platform=CUDA Precision=single DeterministicForces=true\n' "$CUDA_VISIBLE_DEVICES"
    printf 'command:'; printf ' %q' "${command[@]}"; printf '\n'
    "${command[@]}"
) 2>&1 | tee out/run_command.log
