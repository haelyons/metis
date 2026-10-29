#!/usr/bin/env bash
set -euo pipefail
source data/toolkit.env
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
: "${EVAL_OUT:?EVAL_OUT is required}"
: "${BASELINE_DIR:?BASELINE_DIR is required}"
: "${EVAL_PROTOCOL:?EVAL_PROTOCOL is required}"
: "${EVAL_INPUTS:?EVAL_INPUTS is required}"
: "${EVAL_SEEDS:?EVAL_SEEDS is required}"
mkdir -p "$EVAL_OUT"
/usr/bin/python3 - <<'EVALUATE'
import json
import math
import os
from pathlib import Path
import subprocess
import time

started = time.perf_counter()
output = Path(os.environ['EVAL_OUT'])
protocol = json.loads(Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs = json.loads(os.environ['EVAL_INPUTS'])
seed_spec = json.loads(os.environ['EVAL_SEEDS'])
mode = os.environ.get('EVAL_MODE', 'performance')
if mode not in ('equivalence', 'warmup', 'performance', 'curve'):
    raise RuntimeError('Unsupported EVAL_MODE')
ids = inputs['ids']
if not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids) or len(set(ids)) != len(ids):
    raise RuntimeError('Invalid sealed input IDs')
if seed_spec['kind'] == 'deterministic':
    seeds = [None]
elif seed_spec['kind'] == 'paired_median':
    seeds = seed_spec['seeds']
    if not seeds or any(type(s) is not int for s in seeds):
        raise RuntimeError('Invalid paired seeds')
else:
    raise RuntimeError('Unsupported sealed seed protocol')
timing_scope = protocol['timing_scope']
compute_budget = None
limit = 1180.0
if mode == 'curve':
    raw = os.environ.get('EVAL_COMPUTE_BUDGET', '')
    if not raw:
        raise RuntimeError('Curve requires EVAL_COMPUTE_BUDGET in GPU seconds')
    compute_budget = json.loads(raw)
    if isinstance(compute_budget, dict):
        candidates = [compute_budget[k] for k in ('gpu_seconds', 'gpu_s', 'seconds', 'budget_s', 'compute_budget') if k in compute_budget]
        if len(candidates) != 1:
            raise RuntimeError('Curve budget must specify one GPU-second limit')
        budget_seconds = candidates[0]
    else:
        budget_seconds = compute_budget
    if isinstance(budget_seconds, bool) or not isinstance(budget_seconds, (int, float)) or not math.isfinite(budget_seconds) or budget_seconds <= 0:
        raise RuntimeError('Invalid GPU-second budget')
    # One used GPU: elapsed seconds conservatively charge all launch/transfer/merge overhead.
    limit = min(limit, float(budget_seconds))
base = Path(os.environ['BASELINE_DIR']).resolve()
python = base / '.venv/bin/python3'
driver = base / 'dhfr_ensemble.py'
pdb = (Path.cwd() / 'data/5dfr_solv-cube_equil.pdb').resolve()
records = []

def finite(x, positive=False):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or (positive and x <= 0):
        raise RuntimeError('Missing or invalid measured output')
    return x

# Execute unchanged published driver, then explicitly synchronize its visible GPU
# in the same interpreter before parent stops its reported timer.
runner = """import ctypes, runpy, sys
script = sys.argv.pop(1)
runpy.run_path(script, run_name='__main__')
runtime = ctypes.CDLL('libcudart.so')
code = runtime.cudaDeviceSynchronize()
if code:
    raise RuntimeError('cudaDeviceSynchronize failed: %d' % code)
"""
for seed_index, seed in enumerate(seeds):
    for input_index, input_id in enumerate(ids):
        # Each sealed identity names the same published fixed configuration;
        # descriptive metadata never creates additional executions.
        work = output / 'runs' / f'seed-{seed_index}-input-{input_index}'
        work.mkdir(parents=True, exist_ok=True)
        coords = work / '5dfr_solv-cube_equil.pdb'
        if not coords.exists():
            coords.symlink_to(pdb)
        result_file = work / 'ensemble.json'
        if result_file.exists():
            result_file.rename(work / f'ensemble.previous.{time.time_ns()}.json')
        seed0 = 1000 if seed is None else seed
        command = [str(python), '-c', runner, str(driver), '--replicas', '8', '--steps', '25000', '--seed0', str(seed0)]
        env = os.environ.copy()
        env['CUDA_CACHE_PATH'] = str(output / 'cuda-cache')
        Path(env['CUDA_CACHE_PATH']).mkdir(parents=True, exist_ok=True)
        remaining = limit - (time.perf_counter() - started)
        if remaining <= 0:
            raise RuntimeError('Evaluation compute/wall budget exhausted')
        with (work / 'stdout.log').open('a') as stdout, (work / 'stderr.log').open('a') as stderr:
            subprocess.run(command, cwd=work, env=env, stdout=stdout, stderr=stderr, check=True, timeout=remaining)
        result = json.loads(result_file.read_text())
        if result['platform'] != 'CUDA' or result['properties'] != {'Precision': 'single', 'DeterministicForces': 'true'}:
            raise RuntimeError('Output platform/properties mismatch')
        if not math.isclose(finite(result['simulated_ns']), 0.8, abs_tol=1e-12):
            raise RuntimeError('Output work differs from published scale')
        replicas = result['replicas']
        if len(replicas) != 8 or sorted(r['replica'] for r in replicas) != list(range(8)):
            raise RuntimeError('Missing replica output')
        metrics = {'total_wall_s': finite(result['total_wall_s'], True), 'simulated_ns': result['simulated_ns']}
        metrics['aggregate_ns_per_day'] = finite(0.8 / metrics['total_wall_s'] * 86400, True)
        metrics['aggregate_us_per_day'] = metrics['aggregate_ns_per_day'] / 1000
        for r in replicas:
            i = r['replica']
            if r['seed'] != seed0 + i or r['steps'] != 25000:
                raise RuntimeError('Output configuration differs from execution command')
            for key in ('wall_s', 'mean_potential_kj_mol', 'final_potential_kj_mol'):
                metrics[f'replica_{i}_{key}'] = finite(r[key], key == 'wall_s')
        for key in ('mean_potential_kj_mol', 'final_potential_kj_mol'):
            metrics[key] = finite(sum(r[key] for r in replicas) / 8)
        records.append({'input_id': input_id, 'seed': seed, 'metrics': metrics})
wall_s = time.perf_counter() - started
if wall_s > limit:
    raise RuntimeError('Evaluation exceeded compute/wall budget')
result = {'records': records, 'timing_scope': timing_scope, 'gpu_count': 1, 'wall_s': wall_s, 'compute_budget': compute_budget}
# Write atomically; retain results from earlier successful invocations.
final = output / 'evaluation.json'
if final.exists():
    final.rename(output / f'evaluation.previous.{time.time_ns()}.json')
temporary = output / 'evaluation.pending.json'
temporary.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
temporary.replace(final)
print(json.dumps({'gpu_count': 1, 'CUDA_VISIBLE_DEVICES': '0', 'replicas': 8, 'steps': 25000, 'records': len(records), 'wall_s': wall_s}))
EVALUATE
