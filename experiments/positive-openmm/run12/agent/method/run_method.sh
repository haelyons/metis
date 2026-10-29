#!/usr/bin/env bash
set -euo pipefail
: "${METHOD_DIR:?METHOD_DIR required}"
: "${METHOD_OUT:?METHOD_OUT required}"
source "$METHOD_DIR/cuda-env.sh"
export CUDA_VISIBLE_DEVICES=0
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0
export OPENMM_CPU_THREADS=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
# Four workers share one physical GPU; use its full available MPS resources.
export CUDA_MPS_ACTIVE_THREAD_PERCENTAGE=100
export PYTHONPATH="$METHOD_DIR/python"
RUN_ROOT="$PWD"
export RUN_ROOT
mkdir -p "$METHOD_OUT"
if [[ "${EVAL_MODE:-anchors}" != anchors ]]; then
    mkdir -p "${EVAL_OUT:?EVAL_OUT required}"
    /usr/bin/python3 - <<'EVALUATE'
import json
import math
import os
import pathlib
import re
import subprocess
import time
import signal

mode = os.environ['EVAL_MODE']
if mode not in ('equivalence', 'warmup', 'performance', 'curve'):
    raise ValueError('Unsupported EVAL_MODE: ' + mode)
protocol = json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs = json.loads(os.environ['EVAL_INPUTS'])
seed_protocol = json.loads(os.environ['EVAL_SEEDS'])
ids = inputs['ids']
if not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids):
    raise ValueError('EVAL_INPUTS.ids must contain input identity strings')
if seed_protocol['kind'] == 'paired_median':
    seeds = seed_protocol['seeds']
    if not seeds or any(type(x) is not int for x in seeds):
        raise ValueError('Invalid paired execution seeds')
elif seed_protocol['kind'] == 'deterministic':
    seeds = [None]
else:
    raise ValueError('Unsupported seed protocol')
# Use the sealed timing scope verbatim in the result.
scope = protocol.get('timing_scope')
if scope is None:
    raise ValueError('Sealed protocol missing timing_scope')
budget_text = os.environ.get('EVAL_COMPUTE_BUDGET', '')
budget = json.loads(budget_text) if budget_text else None
limit = None
if mode == 'curve':
    if isinstance(budget, (int, float)) and not isinstance(budget, bool):
        limit = float(budget)
    elif isinstance(budget, dict):
        for key in ('gpu_seconds', 'gpu_s', 'gpu_seconds_budget', 'max_gpu_seconds'):
            if key in budget:
                limit = float(budget[key])
                break
    if limit is None or not math.isfinite(limit) or limit <= 0:
        raise ValueError('Curve requires a positive GPU-second compute budget')

root = pathlib.Path.cwd()
baseline = pathlib.Path(os.environ['METHOD_DIR']).resolve()
out = pathlib.Path(os.environ['EVAL_OUT']).resolve()
# Separate invocation directory preserves all logs and outputs across warmups/retries.
invocation = pathlib.Path(__import__('tempfile').mkdtemp(prefix='run-', dir=out))
env = os.environ.copy()
env['PYTHONPATH'] = str(baseline / 'python')
records = []
wall_sum = 0.0
started = time.perf_counter()
for seed in seeds:
    for input_id in ids:
        index = len(records)
        work = invocation / ('record-%04d' % index)
        work.mkdir()
        (work / 'tmp').mkdir()
        env['TMPDIR'] = str(work / 'tmp')
        (work / 'tmp/cuda-cache').mkdir()
        (work / 'tmp/cache').mkdir()
        env['CUDA_CACHE_PATH'] = str(work / 'tmp/cuda-cache')
        env['XDG_CACHE_HOME'] = str(work / 'tmp/cache')
        (work / '5dfr_solv-cube_equil.pdb').symlink_to(root / 'data/5dfr_solv-cube_equil.pdb')
        seed0 = 1000 if seed is None else seed
        command = ['/usr/bin/python3', str(baseline / 'dhfr_ensemble.py'),
                   '--replicas', '8', '--steps', '25000', '--seed0', str(seed0),
                   '--platform', 'CUDA', '--out', 'ensemble.json']
        remaining = 1150 - (time.perf_counter() - started)
        if limit is not None:
            remaining = min(remaining, limit)
        if remaining <= 0:
            raise RuntimeError('Evaluation execution budget exhausted')
        began = time.perf_counter()
        with (work / 'stdout.log').open('wb') as log:
            process = subprocess.Popen(command, cwd=work, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                status = process.wait(timeout=remaining)
                if status:
                    raise subprocess.CalledProcessError(status, command)
            except BaseException:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise
        # Published driver queries every final energy synchronously and destroys
        # every CUDA Context before returning. Process exit also releases CUDA
        # contexts; all used GPU work is complete before this timer stops.
        elapsed = time.perf_counter() - began
        wall_sum += elapsed
        if limit is not None and elapsed > limit:
            raise RuntimeError('GPU-second budget exceeded')
        result = json.loads((work / 'ensemble.json').read_text())
        if result['platform'] != 'CUDA' or result['properties'] != {
                'Precision': 'single', 'DeterministicForces': 'true'}:
            raise ValueError('Workload output configuration mismatch')
        if not math.isclose(result['simulated_ns'], 0.8) or len(result['replicas']) != 8:
            raise ValueError('Workload output scale mismatch')
        wall = result['total_wall_s']
        if not math.isfinite(wall) or wall <= 0:
            raise ValueError('Invalid ensemble time')
        metrics = {'total_wall_s': wall, 'aggregate_ns_per_day': 0.8 / wall * 86400,
                   'simulated_ns': result['simulated_ns']}
        for i, replica in enumerate(result['replicas']):
            if (replica['replica'], replica['seed'], replica['steps']) != (i, seed0+i, 25000):
                raise ValueError('Replica output configuration mismatch')
            for key in ('final_potential_kj_mol', 'mean_potential_kj_mol', 'wall_s'):
                value = replica[key]
                if not math.isfinite(value):
                    raise ValueError('Nonfinite replica measurement')
                metrics['replica_%d_%s' % (i, key)] = value
        for key in ('final_potential_kj_mol', 'mean_potential_kj_mol'):
            metrics[key] = sum(r[key] for r in result['replicas']) / 8
        log = (work / 'stdout.log').read_text()
        for key, tolerance in [('total_wall_s', .00051), ('aggregate_ns_per_day', .051)]:
            matches = re.findall(r'^' + key + r': ([0-9.eE+\-]+)$', log, re.M)
            if not matches or not math.isclose(float(matches[-1]), metrics[key], abs_tol=tolerance):
                raise ValueError('Missing or inconsistent stdout metric: ' + key)
        records.append({'input_id': input_id, 'seed': seed, 'metrics': metrics})

result = {'records': records, 'timing_scope': scope, 'gpu_count': 1,
          'wall_s': wall_sum, 'compute_budget': budget}
# Every record ran fresh; no baseline or candidate output was reused.
temporary = out / 'evaluation.json.tmp'
temporary.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
temporary.replace(out / 'evaluation.json')
EVALUATE
else
    mkdir -p "$METHOD_OUT/baseline-run" "$METHOD_OUT/tmp/cuda-cache" "$METHOD_OUT/tmp/cache"
    export TMPDIR="$METHOD_OUT/tmp"
    export CUDA_CACHE_PATH="$METHOD_OUT/tmp/cuda-cache"
    export XDG_CACHE_HOME="$METHOD_OUT/tmp/cache"
    ln -sfn "$RUN_ROOT/data/5dfr_solv-cube_equil.pdb" "$METHOD_OUT/baseline-run/5dfr_solv-cube_equil.pdb"
    (
        cd "$METHOD_OUT/baseline-run"
        /usr/bin/python3 "$METHOD_DIR/dhfr_ensemble.py" --replicas 8 --steps 25000 --seed0 1000 --platform CUDA --out ensemble.json
    ) | tee "$METHOD_OUT/baseline.stdout.log"
    /usr/bin/python3 - <<'ANCHORS'
import os
import json, math, pathlib, re
result = json.loads((pathlib.Path(os.environ['METHOD_OUT']) / 'baseline-run/ensemble.json').read_text())
assert result['platform'] == 'CUDA'
assert result['properties'] == {'Precision': 'single', 'DeterministicForces': 'true'}
assert math.isclose(result['simulated_ns'], 0.8)
wall = result['total_wall_s']
assert math.isfinite(wall) and wall > 0
assert len(result['replicas']) == 8
for i, record in enumerate(result['replicas']):
    assert (record['replica'], record['seed'], record['steps']) == (i, 1000+i, 25000)
    for key in ('wall_s', 'final_potential_kj_mol', 'mean_potential_kj_mol'):
        assert math.isfinite(record[key])
log = (pathlib.Path(os.environ['METHOD_OUT']) / 'baseline.stdout.log').read_text()
printed_wall = re.findall(r'^total_wall_s: ([0-9.eE+\-]+)$', log, re.M)
printed_rate = re.findall(r'^aggregate_ns_per_day: ([0-9.eE+\-]+)$', log, re.M)
assert printed_wall and printed_rate, 'Missing workload stdout measurements'
assert math.isclose(float(printed_wall[-1]), wall, abs_tol=0.00051)
rate = result['simulated_ns'] / wall * 86400
assert math.isclose(float(printed_rate[-1]), rate, abs_tol=0.051)
items = [{'id': 'nvidia_2025_dhfr_eight_mps_approx_throughput', 'unit': 'microseconds/day'}]
measured = {}
for item in items:
    if item['unit'] == 'microseconds/day':
        value = rate / 1000
    elif item['unit'] == 'ns/day':
        value = rate
    elif item['unit'] in ('s', 'seconds'):
        value = wall
    else:
        raise ValueError('Unsupported measurement unit: ' + item['unit'])
    assert math.isfinite(value)
    measured[item['id']] = value
(pathlib.Path(os.environ['METHOD_OUT']) / 'anchors_measured.json').write_text(json.dumps(measured, indent=2, allow_nan=False) + '\n')
ANCHORS
fi
