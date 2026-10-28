#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${EVAL_MODE:-}" && "${EVAL_MODE}" != anchors && "${EVAL_MODE}" != anchor ]]; then
    exec bash harness/run_evaluation.sh
fi
mkdir -p out
rm -f out/anchors_measured.json
bash harness/run_command.sh
/usr/bin/python3 - <<'MEASURE'
import json, math, pathlib, re

def validate(path, seed0):
    value = json.loads(path.read_text())
    def finite(x, positive=False):
        if isinstance(x, bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or (positive and x <= 0):
            raise ValueError('Invalid measured value: '+repr(x))
        return x
    if value['platform'] != 'CUDA' or value['properties'] != {'Precision':'single','DeterministicForces':'true'}:
        raise ValueError('Output platform/properties disagree with published CUDA configuration')
    if not math.isclose(finite(value['simulated_ns']), 0.8, rel_tol=1e-12):
        raise ValueError('Output simulated work disagrees with 8 x 25000 steps at 4 fs')
    wall = finite(value['total_wall_s'], True)
    replicas = value['replicas']
    if len(replicas) != 8 or sorted(r['replica'] for r in replicas) != list(range(8)):
        raise ValueError('Missing/duplicate replica output')
    metrics = {'total_wall_s':wall, 'aggregate_ns_per_day':86400*value['simulated_ns']/wall}
    for r in replicas:
        if r['steps'] != 25000 or r['seed'] != seed0+r['replica']:
            raise ValueError('Output steps/seeds disagree with command')
        for key in ('wall_s','final_potential_kj_mol','mean_potential_kj_mol'):
            metrics[f"replica_{r['replica']}_{key}"] = finite(r[key], key=='wall_s')
    return metrics

metrics = validate(pathlib.Path('out/baseline-run/ensemble.json'), 1000)
# Validate printed timing/throughput against the same completed JSON run.
log = pathlib.Path('out/baseline-run/stdout.log').read_text()
for key, tolerance in [('total_wall_s',0.00051),('aggregate_ns_per_day',0.051)]:
    matches = re.findall(r'^'+key+r':\s*(\S+)\s*$',log,re.M)
    if not matches or not math.isfinite(float(matches[-1])) or abs(float(matches[-1])-metrics[key])>tolerance:
        raise ValueError('Missing/invalid printed '+key)
items = json.loads(pathlib.Path('baseline-published/anchors.json').read_text())
if isinstance(items,dict):
    items = items.get('anchors', []) + items.get('references', []) if items else []
measured = {}
for item in items:
    if item['id'] != 'nvidia2025-dhfr-eight-tuned-throughput-reference':
        raise ValueError('No measured output mapping for intake item '+item['id'])
    measured[item['id']] = metrics['aggregate_ns_per_day']
pathlib.Path('out/anchors_measured.json').write_text(json.dumps(measured,indent=2,allow_nan=False)+'\n')
print(json.dumps({'gpu_count':1,'CUDA_VISIBLE_DEVICES':'0','replicas':8,'steps_per_replica':25000,'seed0':1000,'platform':'CUDA','properties':{'Precision':'single','DeterministicForces':'true'},'metrics':metrics},allow_nan=False))
MEASURE
