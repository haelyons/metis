#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
# The canonical command owns its environment, workload and log history.
if bash harness/run_command.sh; then
    :
else
    status=$?
    printf 'Canonical command failed (rc %s); see out/run/command.log. No measurements emitted.\n' "$status" >&2
    printf 'Intake repair evidence: pinned OpenMM 8.2.0 reports __version__ 8.2; run_command.sh requires 8.2.0. Repairing that preflight requires editing run_command.sh.\n' >&2
    exit "$status"
fi
python3 - <<'CHECK'
import json
import math
import pathlib
import re
import shutil
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value, positive=False):
    return (type(value) in (int, float) and math.isfinite(value)
            and (not positive or value > 0))


execution = json.loads(pathlib.Path('intake/EXECUTION.json').read_text())
scale = execution['representative_scale']
config = execution['inputs']['configuration']
items = json.loads(pathlib.Path('intake/anchors.json').read_text())
# Empty intake still executes and validates the published workload.
if items == {}:
    items = []
require(isinstance(items, list), 'Invalid intake anchor/reference list')
ids = [item['id'] for item in items]
require(all(isinstance(i, str) and i for i in ids) and len(set(ids)) == len(ids),
        'Invalid or duplicate intake item ID')

p = pathlib.Path('out/run')
d = json.loads((p / 'ensemble.json').read_text())
s = (p / 'command.log').read_text()
printed = []
for line in s.splitlines():
    try:
        value = json.loads(line)
    except ValueError:
        continue
    if isinstance(value, dict) and 'command' in value:
        printed.append(value)
require(len(printed) == 1, 'Missing or ambiguous printed configuration')
c = printed[0]
# Validate emitted argv, cwd and environment, never script source.
require(c['command'] == [
    'python3', '../../baseline-published/dhfr_ensemble.py',
    '--replicas', str(scale['replicas']),
    '--steps', str(scale['steps_per_replica']), '--seed0', str(scale['seed0'])],
    'Printed command differs from fixed intake workload')
require(c['cwd'] == 'out/run' and c['CUDA_VISIBLE_DEVICES'] == '0'
        and c['gpu_count'] == scale['gpu_count']
        and c['atoms'] == scale['atoms_per_replica']
        and c['openmm'] in ('8.2', '8.2.0'), 'Invalid printed configuration')
require(d['platform'] == config['platform'] and d['properties'] == config['properties'],
        'Invalid emitted platform/properties')
require(finite(d['simulated_ns'], True)
        and math.isclose(d['simulated_ns'], scale['total_simulated_ns'])
        and len(d['replicas']) == scale['replicas'], 'Invalid emitted workload scale')
require(finite(d['total_wall_s'], True), 'Missing or invalid ensemble wall time')
for i, r in enumerate(d['replicas']):
    require((r['replica'], r['seed'], r['steps']) ==
            (i, scale['seed0'] + i, scale['steps_per_replica']),
            'Invalid emitted replica configuration')
    for k in ('wall_s', 'mean_potential_kj_mol', 'final_potential_kj_mol'):
        require(finite(r[k], k == 'wall_s'), f'Invalid replica output: {k}')
wall = re.findall(r'^total_wall_s: ([0-9.eE+-]+)$', s, re.M)
rate = re.findall(r'^aggregate_ns_per_day: ([0-9.eE+-]+)$', s, re.M)
require(len(wall) == len(rate) == 1, 'Missing or ambiguous printed measurements')
w, throughput = float(wall[0]), float(rate[0])
require(finite(w, True) and finite(throughput, True), 'Invalid printed measurements')
require(abs(w - d['total_wall_s']) <= 0.00051, 'Inconsistent wall output')
require(abs(throughput - d['simulated_ns'] / d['total_wall_s'] * 86400) <= 0.051,
        'Inconsistent throughput output')
# Every intake item measures aggregate throughput; published values are scored
# by the pipeline, including contextual references, never asserted here.
target = pathlib.Path('out/anchors_measured.json')
if target.exists():
    shutil.copy2(target, target.with_name(f'anchors_measured.previous.{time.time_ns()}.json'))
temp = target.with_suffix('.json.tmp')
temp.write_text(json.dumps({i: throughput for i in ids}, allow_nan=False, indent=2) + '\n')
temp.replace(target)
CHECK
