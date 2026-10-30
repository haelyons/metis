#!/usr/bin/env bash
set -euo pipefail
method=${METHOD_DIR:?METHOD_DIR is required}
base=${BASELINE_DIR:?BASELINE_DIR is required}
if [[ -f "$base/baseline-published/dhfr_ensemble.py" ]]; then
    root=$base
else
    root=$(dirname "$base")
fi
source "$method/cuda-env.sh"
export OPENMM_CPU_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export CUDA_VISIBLE_DEVICES=0
export PYTHONPATH="$method/python${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
if [[ ${EVAL_MODE:-anchors} == anchors ]]; then
    exec bash "$(dirname "${BASH_SOURCE[0]}")/run_anchors.sh"
fi
export EVAL_OUT=${EVAL_OUT:-${METHOD_OUT:?}}
python3 - "$root" "$method" <<'PY'
import ctypes
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

root, published = map(Path, sys.argv[1:])
mode = os.environ['EVAL_MODE']
if mode not in ('equivalence', 'warmup', 'performance', 'curve'):
    raise RuntimeError('Unsupported evaluation mode')
if not os.environ.get('EVAL_ARM'):
    raise RuntimeError('EVAL_ARM is required')
protocol = json.loads(Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs = json.loads(os.environ['EVAL_INPUTS'])
seed_spec = json.loads(os.environ['EVAL_SEEDS'])
ids = inputs['ids']
if not isinstance(ids, list) or not ids or not all(isinstance(x, str) for x in ids):
    raise RuntimeError('Invalid sealed input identities')
if seed_spec['kind'] == 'paired_median':
    seeds = seed_spec['seeds']
    if not seeds or not all(type(s) is int for s in seeds):
        raise RuntimeError('Invalid paired execution seeds')
elif seed_spec['kind'] == 'deterministic':
    seeds = [None]
else:
    raise RuntimeError('Unsupported seed protocol')
# This published input is one ensemble, with the paired seeds identifying its
# existing replicas. Do not shift seed0 or repeat the ensemble for every seed.
configuration = inputs['configuration']
seed0 = configuration['seed0']
replicas = configuration['replicas']
steps = configuration['steps_per_replica']
if (replicas, steps, seed0) != (8, 25000, 1000):
    raise RuntimeError('Sealed input differs from the published fixed scale')
if any(s is not None and s not in range(seed0, seed0 + replicas) for s in seeds):
    raise RuntimeError('Seed does not identify a published replica')
metric_names = [m['name'] for m in protocol['equivalence_metrics']]
if set(metric_names) != {'mean_potential_kj_mol', 'final_potential_kj_mol'}:
    raise RuntimeError('Unsupported sealed metric definition')
timing_scope = protocol['timing_scope']
gpu_count = protocol['hardware_cost_basis']['method_gpus']
if gpu_count != 1:
    raise RuntimeError('Published baseline requires one GPU')
out = Path(os.environ['EVAL_OUT']).resolve()
out.mkdir(parents=True, exist_ok=True)
if (out / 'evaluation.json').exists():
    raise RuntimeError('Evaluation output directory must be fresh')
budget = None
limit = 1170.0
if mode == 'curve':
    budget = json.loads(os.environ['EVAL_COMPUTE_BUDGET'])
    if isinstance(budget, dict):
        values = [budget[k] for k in ('gpu_seconds', 'gpu_s', 'budget_gpu_seconds',
                  'compute_budget_gpu_s', 'seconds') if k in budget]
        if len(values) != 1:
            raise RuntimeError('Ambiguous compute budget')
        budget_s = float(values[0])
    elif isinstance(budget, (int, float)) and not isinstance(budget, bool):
        budget_s = float(budget)
    else:
        raise RuntimeError('Invalid compute budget')
    if not math.isfinite(budget_s) or budget_s <= 0:
        raise RuntimeError('Invalid GPU-second limit')
    limit = min(limit, budget_s / gpu_count)

def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise RuntimeError('Invalid measured metric')
    return value

# Energy retrieval and destruction of each OpenMM Context complete the child's
# GPU work before exit. Synchronize the sole visible device in the adapter too.
cuda = ctypes.CDLL('libcuda.so.1')
def checked(name, *args):
    status = getattr(cuda, name)(*args)
    if status:
        raise RuntimeError(f'{name} failed: {status}')
checked('cuInit', ctypes.c_uint(0))
device = ctypes.c_int()
checked('cuDeviceGet', ctypes.byref(device), ctypes.c_int(0))
context = ctypes.c_void_p()
checked('cuDevicePrimaryCtxRetain', ctypes.byref(context), device)
def synchronize():
    checked('cuCtxSetCurrent', context)
    checked('cuCtxSynchronize')

# Input staging is outside the launch-to-exit timer. The actual published
# process still loads the staged PDB/XML and constructs the full system.
workdirs = []
for i, input_id in enumerate(ids):
    work = out / ('run' if i == 0 else f'input_{i}')
    work.mkdir()
    for name in ('5dfr_solv-cube_equil.pdb', 'amber99sb.xml', 'tip3p.xml'):
        shutil.copyfile(root / 'data' / name, work / name)
    workdirs.append(work)
results = {}
try:
    synchronize()
    began = time.perf_counter()
    for input_id, work in zip(ids, workdirs):
        remaining = limit - (time.perf_counter() - began)
        if remaining <= 0:
            raise RuntimeError('Compute budget exhausted before fixed work completed')
        command = [sys.executable, str(published / 'dhfr_ensemble.py'),
                   '--replicas', str(replicas), '--steps', str(steps),
                   '--seed0', str(seed0), '--out', str(work / 'ensemble.json')]
        with (work / 'method.log').open('wb') as log:
            child = subprocess.Popen(command, cwd=work, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            try:
                status = child.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                synchronize()
                raise RuntimeError('Fixed workload exceeded compute budget')
            if status:
                raise RuntimeError(f'Published driver failed ({status}); see {work / "method.log"}')
        synchronize()
        measured = json.loads((work / 'ensemble.json').read_text())
        if measured['platform'] != 'CUDA' or measured['properties'] != {
                'Precision': 'single', 'DeterministicForces': 'true'}:
            raise RuntimeError('Measured platform differs from published configuration')
        if measured['simulated_ns'] != 0.8 or len(measured['replicas']) != replicas:
            raise RuntimeError('Measured work differs from fixed scale')
        if finite(measured['total_wall_s']) <= 0:
            raise RuntimeError('Invalid measured ensemble time')
        by_seed = {}
        for index, replica in enumerate(measured['replicas']):
            if (replica['replica'], replica['seed'], replica['steps']) != (index, seed0 + index, steps):
                raise RuntimeError('Measured replica identity differs from published configuration')
            by_seed[replica['seed']] = {name: finite(replica[name]) for name in metric_names}
        results[input_id] = by_seed
    records = []
    for seed in seeds:
        for input_id in ids:
            if seed is None:
                metrics = {name: sum(v[name] for v in results[input_id].values()) / replicas
                           for name in metric_names}
            else:
                metrics = results[input_id][seed]
            records.append({'input_id': input_id, 'seed': seed, 'metrics': metrics})
    synchronize()
    elapsed = time.perf_counter() - began
    if not math.isfinite(elapsed) or elapsed <= 0 or elapsed > limit:
        raise RuntimeError('Fixed workload did not complete within compute budget')
    evaluation = {'records': records, 'timing_scope': timing_scope,
                  'gpu_count': gpu_count, 'wall_s': elapsed}
    if mode == 'curve':
        evaluation['compute_budget'] = budget
    temporary = out / 'evaluation.json.tmp'
    temporary.write_text(json.dumps(evaluation, allow_nan=False, indent=2) + '\n')
    temporary.replace(out / 'evaluation.json')
finally:
    synchronize()
    checked('cuDevicePrimaryCtxRelease', device)
PY
