#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
# Select only layouts discovered by the supplied probe.
if [[ -x /usr/local/cuda/bin/nvcc && -f /usr/local/cuda/include/cuda_runtime.h && -f /usr/local/cuda/lib64/libcudart.so ]]; then
    cuda_bin=/usr/local/cuda/bin/nvcc
    cuda_inc=/usr/local/cuda/include
    cuda_lib=/usr/local/cuda/lib64
    export CUDAToolkit_ROOT=/usr/local/cuda
elif [[ -x /usr/lib/cuda/bin/nvcc && -f /usr/lib/cuda/include/cuda_runtime.h && -f /usr/lib/cuda/lib64/libcudart.so ]]; then
    cuda_bin=/usr/lib/cuda/bin/nvcc
    cuda_inc=/usr/lib/cuda/include
    cuda_lib=/usr/lib/cuda/lib64
    export CUDAToolkit_ROOT=/usr/lib/cuda
elif [[ -x /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    cuda_bin=/usr/bin/nvcc
    cuda_inc=/usr/include
    cuda_lib=/usr/lib/x86_64-linux-gnu
else
    echo 'No complete probed CUDA toolkit or distro layout available' >&2
    exit 1
fi
ls "$cuda_bin" "$cuda_inc/cuda_runtime.h" "$cuda_lib/libcudart.so"
export OPENMM_CUDA_COMPILER="$cuda_bin"
export CUDACXX="$cuda_bin"
export CUDA_INCLUDE_DIR="$cuda_inc"
export CUDA_CUDART_LIBRARY="$cuda_lib/libcudart.so"
export PATH="${cuda_bin%/*}:$PATH"

export CUDA_VISIBLE_DEVICES=0
export PYTHONDONTWRITEBYTECODE=1
# Each invocation gets independent writable files; source/data links stay read-only.
run_dir=$(mktemp -d out/dhfr.XXXXXXXX)
ln -s ../../baseline-published/dhfr_ensemble.py "$run_dir/dhfr_ensemble.py"
input=${DHFR_INPUT:-data/5dfr_solv-cube_equil.pdb}
[[ "$input" != /* && "$input" != *..* ]] || { echo 'Input must be a relative staged path' >&2; exit 1; }
ln -s "../../$input" "$run_dir/5dfr_solv-cube_equil.pdb"
seed0=${DHFR_SEED0:-1000}
[[ "$seed0" =~ ^[0-9]+$ ]] || { echo 'Invalid ensemble seed' >&2; exit 1; }
export PYTHONPATH="../../baseline-published/python${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$cuda_lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
for libdir in baseline-published/python/nvidia/*/lib; do
    if [[ -d "$libdir" ]]; then export LD_LIBRARY_PATH="../../$libdir:$LD_LIBRARY_PATH"; fi
done
export CUDA_CACHE_PATH=../cuda-cache
export TMPDIR=../tmp
mkdir -p out/cuda-cache out/tmp
# Pointer identifies this invocation without discarding earlier logs.
printf '%s\n' "$run_dir" > out/last_run.txt
cd "$run_dir"
python3 - "$seed0" <<'PY_CONFIG' | tee configuration.json
import json, os, sys
c={'atoms': 23558, 'force_fields': ['amber99sb.xml', 'tip3p.xml'], 'nonbonded_method': 'PME', 'cutoff_nm': 0.9, 'constraints': 'HBonds', 'hydrogen_mass_amu': 1.5, 'integrator': 'LangevinMiddleIntegrator', 'temperature_K': 300, 'friction_per_ps': 1, 'step_fs': 4, 'constraint_tolerance': 1e-05, 'platform': 'CUDA', 'properties': {'Precision': 'single', 'DeterministicForces': 'true'}, 'gpu_count': 1, 'replicas': 8, 'steps_per_replica': 25000, 'seeds': [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007], 'energy_interval_steps': 250}
c['seeds']=list(range(int(sys.argv[1]),int(sys.argv[1])+8))
c['CUDA_VISIBLE_DEVICES']=os.environ['CUDA_VISIBLE_DEVICES']
c['command']=['python3','dhfr_ensemble.py','--replicas','8','--steps','25000','--seed0',sys.argv[1]]
print(json.dumps(c))
PY_CONFIG
set +e
python3 dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 "$seed0" > >(tee stdout.log) 2> >(tee stderr.log >&2)
status=$?
wait
exit "$status"
