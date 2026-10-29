#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${EVAL_MODE:-}" && "${EVAL_MODE}" != anchors && "${EVAL_MODE}" != anchor ]]; then
    exec bash harness/run_evaluation.sh
fi
mkdir -p out
rm -f out/anchors_measured.json
bash harness/run_command.sh
/usr/bin/python3 - <<'MEASURE'
import json, math, re
from pathlib import Path
seed0=1000
def validate(d):
    def finite(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
    if d.get('platform') != 'CUDA' or d.get('properties') != {'Precision':'single', 'DeterministicForces':'true'}:
        raise ValueError('Output platform/properties differ from the published command')
    if not finite(d.get('total_wall_s')) or d['total_wall_s'] <= 0 or d.get('simulated_ns') != 0.8:
        raise ValueError('Missing or invalid ensemble timing/work output')
    reps=d.get('replicas', [])
    if len(reps) != 8:
        raise ValueError('Expected eight completed replicas')
    for i,r in enumerate(reps):
        if r.get('replica') != i or r.get('seed') != seed0+i or r.get('steps') != 25000:
            raise ValueError('Output replica configuration differs from invocation')
        for key in ('wall_s','mean_potential_kj_mol','final_potential_kj_mol'):
            if not finite(r.get(key)):
                raise ValueError('Missing or invalid replica output: '+key)
        if r['wall_s'] <= 0:
            raise ValueError('Invalid replica wall time')
    return d['simulated_ns']/d['total_wall_s']*86400

d=json.loads(Path('out/command/ensemble.json').read_text())
throughput=validate(d)
log=Path('out/command/stdout.log').read_text()
for name, expected, tolerance in [('total_wall_s',d['total_wall_s'],0.00051), ('aggregate_ns_per_day',throughput,0.051)]:
    matches=re.findall(r'^'+name+r': ([^\n]+)$', log, re.M)
    if not matches or not math.isfinite(float(matches[-1])) or abs(float(matches[-1])-expected)>tolerance:
        raise ValueError('Missing or inconsistent stdout measurement: '+name)
ids=['nvidia-2025-dhfr-eight-tuned-throughput-reference']
result={item_id:throughput for item_id in ids}
p=Path('out/anchors_measured.json')
p.with_suffix('.tmp').write_text(json.dumps(result, allow_nan=False)+'\n')
p.with_suffix('.tmp').replace(p)
MEASURE
