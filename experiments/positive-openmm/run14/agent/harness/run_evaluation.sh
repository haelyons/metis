#!/usr/bin/env bash
set -euo pipefail
: "${EVAL_OUT:?}" "${EVAL_ARM:?}" "${BASELINE_DIR:?}" "${EVAL_PROTOCOL:?}" "${EVAL_INPUTS:?}" "${EVAL_SEEDS:?}"
mkdir -p "$EVAL_OUT"
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
export GPU_COUNT=1
export PYTHONNOUSERSITE=1

case "$EVAL_ARM" in
    baseline) EVALUATION_SOURCE="$BASELINE_DIR" ;;
    method) EVALUATION_SOURCE="${METHOD_DIR:?}" ;;
    *) echo "Unknown evaluation arm: $EVAL_ARM" >&2; exit 1 ;;
esac
export EVALUATION_SOURCE
export PYTHONPATH="$EVALUATION_SOURCE/python"
unset OPENMM_PLUGIN_DIR
/usr/bin/python3 - <<'EVALUATE'
import json, math, pathlib, re

def load_measurement(path, log, seed0):
    d = json.loads(pathlib.Path(path).read_text())
    def finite(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
    if d.get('platform') != 'CUDA' or d.get('properties') != {'Precision':'single','DeterministicForces':'true'}:
        raise ValueError('Invalid output platform/properties')
    if d.get('simulated_ns') != 0.8 or not finite(d.get('total_wall_s')) or d['total_wall_s'] <= 0:
        raise ValueError('Invalid ensemble measurement')
    rows = d.get('replicas', [])
    if len(rows) != 8:
        raise ValueError('Missing replicas')
    for i, row in enumerate(rows):
        if (row.get('replica'), row.get('seed'), row.get('steps')) != (i, seed0+i, 25000):
            raise ValueError('Output differs from execution arguments')
        for key in ('wall_s','final_potential_kj_mol','mean_potential_kj_mol'):
            if not finite(row.get(key)):
                raise ValueError('Missing or nonfinite '+key)
        if row['wall_s'] <= 0:
            raise ValueError('Invalid replica time')
    text = pathlib.Path(log).read_text()
    wall = re.findall(r'^total_wall_s: ([0-9.]+)$',text,re.M)
    rate = re.findall(r'^aggregate_ns_per_day: ([0-9.]+)$',text,re.M)
    if not wall or not rate:
        raise ValueError('Missing printed measurements')
    throughput = d['simulated_ns']/d['total_wall_s']*86400
    if abs(float(wall[-1])-d['total_wall_s']) > 0.00051 or abs(float(rate[-1])-throughput)>0.051:
        raise ValueError('Printed and saved measurements disagree')
    return d, throughput

import os, subprocess, time, ctypes
out = pathlib.Path(os.environ['EVAL_OUT'])
base = pathlib.Path(os.environ['EVALUATION_SOURCE'])
baseline = pathlib.Path(os.environ['BASELINE_DIR'])
protocol = json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs = json.loads(os.environ['EVAL_INPUTS'])
seedspec = json.loads(os.environ['EVAL_SEEDS'])
if seedspec['kind'] == 'paired_median':
    seeds = seedspec['seeds']
    if not seeds or any(type(s) is not int for s in seeds):
        raise ValueError('Invalid paired seeds')
elif seedspec['kind'] == 'deterministic':
    seeds = [None]
else:
    raise ValueError('Unknown seed protocol')
ids = inputs['ids']
if not isinstance(ids, list) or not ids or any(not isinstance(x,str) for x in ids):
    raise ValueError('Invalid sealed input identities')
scope = protocol.get('timing_scope')
if scope is None:
    raise ValueError('Seal missing timing_scope')
mode = os.environ.get('EVAL_MODE','equivalence')
if mode == 'anchors':
    subprocess.run(['bash', str(baseline.parent/'harness'/'run_anchors.sh')], cwd=baseline.parent, check=True)
    raise SystemExit(0)
if mode not in ('equivalence','warmup','performance','curve'):
    raise ValueError('Unknown evaluation mode')
budget_text = os.environ.get('EVAL_COMPUTE_BUDGET','')
budget = None
if mode == 'curve':
    budget = json.loads(budget_text)
    if isinstance(budget,dict):
        limits = [budget[k] for k in ('gpu_seconds','gpu_s','compute_budget') if k in budget]
        if len(limits)!=1:
            raise ValueError('Curve requires numeric GPU-second budget')
        limit = float(limits[0])
    else:
        limit = float(budget)
    if not math.isfinite(limit) or limit <= 0:
        raise ValueError('Invalid curve budget')
# Synchronize the single used device before stopping any reported outer timer.
cuda = ctypes.CDLL('libcuda.so.1')
def sync():
    for call, args in ((cuda.cuInit,(0,)),):
        if call(*args): raise RuntimeError('CUDA initialization failed')
    device = ctypes.c_int()
    if cuda.cuDeviceGet(ctypes.byref(device),0): raise RuntimeError('CUDA device unavailable')
    ctx = ctypes.c_void_p()
    if cuda.cuDevicePrimaryCtxRetain(ctypes.byref(ctx),device): raise RuntimeError('CUDA primary context unavailable')
    try:
        if cuda.cuCtxSetCurrent(ctx) or cuda.cuCtxSynchronize(): raise RuntimeError('CUDA synchronization failed')
    finally:
        cuda.cuDevicePrimaryCtxRelease(device)
# Paired seeds are individual trajectories, not starting seeds for overlapping
# eight-replica ensembles. Execute each sealed block exactly once and retain
# its individual scientific summaries for the seed-indexed records.
metric_names = [m['name'] for m in protocol['equivalence_metrics']]
if any(name not in ('mean_potential_kj_mol', 'final_potential_kj_mol')
       for name in metric_names):
    raise ValueError('Unsupported scientific metric')
gpu_count = protocol['hardware_cost_basis'][os.environ['EVAL_ARM']+'_gpus']
if gpu_count != 1:
    raise ValueError('This fixed-scale adapter requires one GPU')
pdb = baseline.parent/'data'/'5dfr_solv-cube_equil.pdb'
if not pdb.is_file():
    raise FileNotFoundError(pdb)
blocks = []
if seedspec['kind'] == 'paired_median':
    if len(seeds) % 8:
        raise ValueError('Sealed seed list must contain complete eight-replica blocks')
    for offset in range(0, len(seeds), 8):
        block = seeds[offset:offset+8]
        if block != list(range(block[0], block[0]+8)):
            raise ValueError('Published driver requires consecutive seeds in each block')
        blocks.append((block[0], block))
else:
    blocks.append((1000, [None]))
measurements = {}
sync()
began=time.perf_counter()
deadline = began + 1100
if mode == 'curve':
    deadline = min(deadline, began + limit/gpu_count)
for block_index, (seed0, block_seeds) in enumerate(blocks):
    for input_index, input_id in enumerate(ids):
        run = out / ('block-%04d-input-%04d' % (block_index, input_index))
        run.mkdir(parents=True, exist_ok=False)
        (run/'5dfr_solv-cube_equil.pdb').symlink_to(pdb)
        command = ['/usr/bin/python3', str(base/'dhfr_ensemble.py'),
                   '--replicas', '8', '--steps', '25000', '--seed0', str(seed0),
                   '--platform', 'CUDA', '--out', 'ensemble.json']
        # The driver queries CUDA energies and destroys each context before
        # exiting; waiting for process exit includes all of its device work.
        remaining = deadline-time.perf_counter()
        if remaining <= 0:
            raise RuntimeError('Evaluation compute budget exhausted')
        with (run/'stdout.log').open('w') as log:
            subprocess.run(command, cwd=run, stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=remaining)
        sync()
        d, rate = load_measurement(run/'ensemble.json', run/'stdout.log', seed0)
        if block_seeds == [None]:
            metrics = {name: sum(row[name] for row in d['replicas'])/8
                       for name in metric_names}
            measurements[(None, input_id)] = metrics
        else:
            for seed, row in zip(block_seeds, d['replicas']):
                measurements[(seed, input_id)] = {name: row[name] for name in metric_names}
records = [{'input_id': input_id, 'seed': seed,
            'metrics': measurements[(seed, input_id)]}
           for seed in seeds for input_id in ids]
result = {'records': records, 'timing_scope': scope, 'gpu_count': gpu_count}
if mode == 'curve':
    result['compute_budget'] = budget
# Include scientific merging and serialization in the measured scope.
json.dumps(result, allow_nan=False)
sync()
wall = time.perf_counter()-began
if not math.isfinite(wall) or wall <= 0:
    raise RuntimeError('Invalid measured wall time')
if time.perf_counter() > deadline:
    raise RuntimeError('Evaluation compute budget exhausted')
result['wall_s'] = wall
(out/'evaluation.json').write_text(json.dumps(result, allow_nan=False, indent=2)+'\n')
EVALUATE
