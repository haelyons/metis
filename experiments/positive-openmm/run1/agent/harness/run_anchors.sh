#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${EVAL_MODE:-}" && "${EVAL_MODE}" != anchors && "${EVAL_MODE}" != anchor ]]; then
    exec bash harness/run_evaluation.sh
fi
mkdir -p out
bash harness/run_command.sh
python3 - <<'PY'
import json, math, pathlib, re
path = pathlib.Path('out/run/ensemble.json')
d = json.loads(path.read_text())
def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
        raise ValueError('Missing or invalid numeric output')
    return value
if d['platform'] != 'CUDA' or d['properties'] != {'Precision':'single','DeterministicForces':'true'}:
    raise ValueError('Invalid platform/properties output')
if len(d['replicas']) != 8 or not math.isclose(finite(d['simulated_ns']), 0.8):
    raise ValueError('Invalid ensemble configuration output')
for i,r in enumerate(d['replicas']):
    if (r['replica'],r['seed'],r['steps']) != (i,1000+i,25000):
        raise ValueError('Invalid replica configuration output')
    for key in ('wall_s','final_potential_kj_mol','mean_potential_kj_mol'):
        finite(r[key])
wall = finite(d['total_wall_s'])
if wall <= 0:
    raise ValueError('Invalid elapsed time')
throughput = d['simulated_ns']/wall*86400
log = pathlib.Path('out/run_command.log').read_text()
expected = 'configuration: cwd=out/run gpu_count=1 CUDA_VISIBLE_DEVICES=0 replicas=8 steps=25000 seed0=1000 platform=CUDA Precision=single DeterministicForces=true'
if expected not in log:
    raise ValueError('Missing or invalid runtime configuration')
for key,value,tolerance in [('total_wall_s',wall,0.00051),('aggregate_ns_per_day',throughput,0.051)]:
    matches = re.findall(r'^'+key+r':\s*(\S+)\s*$',log,re.M)
    if len(matches) != 1 or abs(finite(float(matches[0]))-value)>tolerance:
        raise ValueError('Missing or invalid printed measurement: '+key)
# Reference quantity is microseconds/day; published fixed-work run reports ns/day.
items = ['nvidia-2025-dhfr-eight-mps-throughput-reference']
result = {item: finite(throughput/1000) for item in items}
pathlib.Path('out/anchors_measured.json').write_text(json.dumps(result,allow_nan=False,indent=2)+'\n')
PY
