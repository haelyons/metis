#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${EVAL_MODE:-}" && "${EVAL_MODE}" != anchors && "${EVAL_MODE}" != anchor ]]; then
    exec bash harness/run_evaluation.sh
fi
bash harness/run_command.sh
python3 - <<'PY'
import json, math, pathlib, re
root = pathlib.Path('.')
run = root/(root/'out/last_run.txt').read_text().strip()
result = json.loads((run/'ensemble.json').read_text())
config = (run/'configuration.log').read_text()
if 'CUDA_VISIBLE_DEVICES=0 gpu_count=1' not in config:
    raise ValueError('Missing or invalid printed GPU configuration')
if 'command=python3 dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000' not in config:
    raise ValueError('Missing or invalid printed command')
def finite(value, positive=False):
    if isinstance(value, bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or (positive and value <= 0):
        raise ValueError('Missing or invalid measurement: '+repr(value))
    return value
if result['platform'] != 'CUDA' or result['properties'] != {'Precision':'single','DeterministicForces':'true'}:
    raise ValueError('Invalid output configuration')
if result['simulated_ns'] != 0.8 or len(result['replicas']) != 8:
    raise ValueError('Invalid output work count')
for index, replica in enumerate(result['replicas']):
    if (replica['replica'],replica['seed'],replica['steps']) != (index,1000+index,25000):
        raise ValueError('Invalid replica output configuration')
    for field in ['wall_s','final_potential_kj_mol','mean_potential_kj_mol']:
        finite(replica[field], field=='wall_s')
wall=finite(result['total_wall_s'], True)
stdout=(run/'command.log').read_text()
printed_wall = re.search(r'^total_wall_s:\s*(\S+)\s*$', stdout, re.M)
printed_rate = re.search(r'^aggregate_ns_per_day:\s*(\S+)\s*$', stdout, re.M)
if not printed_wall or not printed_rate:
    raise ValueError('Missing published stdout measurements')
if abs(finite(float(printed_wall[1]),True)-wall) > 0.000501:
    raise ValueError('Inconsistent wall output')
rate=finite(float(printed_rate[1]), True)
if abs(rate - 0.8/wall*86400) > 0.050001:
    raise ValueError('Inconsistent throughput output')
meta=json.loads((root/'baseline-published/intake.json').read_text())
measured={}
for item in meta['anchors']:
    if item['id'] != 'nvidia-2025-dhfr-eight-replicas-throughput-reference':
        raise ValueError('Unknown measurement item: '+item['id'])
    # Published output is ns/day; reference quantity uses microseconds/day.
    measured[item['id']]=rate/1000
(root/'out/anchors_measured.json').write_text(json.dumps(measured, allow_nan=False, indent=2)+'\n')
PY
