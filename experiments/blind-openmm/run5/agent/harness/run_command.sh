#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
# Keep previous invocations while retaining stable paths for output consumers.
for name in baseline.stdout.log baseline.stderr.log; do
    if [[ -e "out/$name" ]]; then mv "out/$name" "out/$name.$(date +%s%N)"; fi
done
readarray -t cuda < <(python3 - <<'PY'
import json
c=json.load(open('baseline-published/cuda-layout.json'))
for k in ('compiler','include','library','toolkit'): print(c[k])
PY
)
[[ ${#cuda[@]} == 4 ]]
ls "${cuda[0]}" "${cuda[1]}/cuda_runtime.h" "${cuda[2]}/libcudart.so" >&2
export PATH="$(dirname "${cuda[0]}"):$PATH"
export CUDACXX="${cuda[0]}" OPENMM_CUDA_COMPILER="${cuda[0]}"
if [[ -n "${cuda[3]}" ]]; then export CUDAToolkit_ROOT="${cuda[3]}" CUDA_HOME="${cuda[3]}"; fi
export CPATH="${cuda[1]}${CPATH:+:$CPATH}" LIBRARY_PATH="${cuda[2]}${LIBRARY_PATH:+:$LIBRARY_PATH}"
export LD_LIBRARY_PATH="${cuda[2]}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CUDA_VISIBLE_DEVICES=0
export PYTHONPATH=../../python-packages PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
# Redirections open in caller's working directory before cd follows shared tree links.
# Every energy observation synchronizes CUDA; process exit destroys all CUDA contexts.
(
    cd baseline-published/SI/Benchmarks
    printf 'HARNESS_CONFIGURATION CUDA_VISIBLE_DEVICES=%s gpu_count=1 working_directory=SI/Benchmarks command=python3_energyBenchmarks.py modes=single,mixed,double trials_per_precision=10 steps_per_trial=500000 samples_per_trial=1000 timestep_fs=2 compiler=%s include=%s library=%s\n' "$CUDA_VISIBLE_DEVICES" "$CUDACXX" "${cuda[1]}" "${cuda[2]}"
    exec python3 energyBenchmarks.py
) >out/baseline.stdout.log 2>out/baseline.stderr.log
