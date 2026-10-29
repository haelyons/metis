#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
bash harness/run_command.sh
/usr/bin/python3 - <<'MEASURE'
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

d, rate = load_measurement('out/run/ensemble.json', 'out/baseline.log', 1000)
items = [{'id': 'nvidia2025-dhfr-eight-mps-throughput-reference', 'quantity': 'Aggregate DHFR throughput, microseconds/day', 'source': 'https://developer.nvidia.com/blog/maximizing-openmm-molecular-dynamics-throughput-with-nvidia-multi-process-service/', 'published_value': 5.0, 'comparison': '==', 'tolerance': None, 'uncertainty': None, 'role': 'reference', 'configuration': 'Eight concurrent DHFR simulations, tuned MPS thread percentage, one L40S or H100; OpenMM 8.2.0 benchmark.py pme, fixed-time protocol.', 'qualification': 'Approximate approaching value from article prose, not exact per-GPU result. No published acceptance tolerance. Not fixed-work ensemble score.', 'acceptance_criterion': None}]
measured = {}
for item in items:
    if item['id'] != 'nvidia2025-dhfr-eight-mps-throughput-reference':
        raise ValueError('Unknown intake item: '+item['id'])
    measured[item['id']] = rate/1000
pathlib.Path('out/anchors_measured.json').write_text(json.dumps(measured, allow_nan=False, indent=2)+'\n')
MEASURE
