#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
rm -f out/anchors_measured.json out/run/ensemble.json
bash harness/run_command.sh
/usr/bin/python3 - <<'MEASURE_PY'
import json, math, re
from pathlib import Path
def finite(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (float,int)) or not math.isfinite(value) or (positive and value<=0):
        raise ValueError('Missing or invalid measured '+name)
    return float(value)

def validate(path, stdout, seed0):
    d=json.loads(Path(path).read_text())
    if d.get('platform')!='CUDA' or d.get('properties')!={'Precision':'single','DeterministicForces':'true'}:
        raise ValueError('Output configuration differs from published command')
    wall=finite(d.get('total_wall_s'),'total_wall_s',True)
    ns=finite(d.get('simulated_ns'),'simulated_ns',True)
    if not math.isclose(ns,0.8,rel_tol=0,abs_tol=1e-12):
        raise ValueError('Output simulated work differs from fixed scale')
    reps=d.get('replicas')
    if not isinstance(reps,list) or len(reps)!=8:
        raise ValueError('Missing eight replica outputs')
    metrics={'total_wall_s':wall,'simulated_ns':ns,'aggregate_ns_per_day':ns/wall*86400}
    for i,r in enumerate(reps):
        if r.get('replica')!=i or r.get('seed')!=seed0+i or r.get('steps')!=25000:
            raise ValueError('Output replica/seed/steps configuration mismatch')
        for key in ('wall_s','final_potential_kj_mol','mean_potential_kj_mol'):
            metrics[f'replica_{i}_{key}']=finite(r.get(key),f'replica_{i}_{key}',key=='wall_s')
    text=Path(stdout).read_text()
    for key,actual,tol in [('total_wall_s',wall,0.00051),('aggregate_ns_per_day',metrics['aggregate_ns_per_day'],0.051)]:
        matches=re.findall(r'^'+key+r':\s*(\S+)\s*$',text,re.M)
        if not matches or not math.isclose(finite(float(matches[-1]),key,True),actual,rel_tol=0,abs_tol=tol):
            raise ValueError('Missing/invalid printed measurement: '+key)
    return d,metrics
d,metrics=validate('out/run/ensemble.json','out/baseline.log',1000)
items=['nvidia_2025_dhfr_eight_mps_throughput_reference']
measured={item_id:metrics['aggregate_ns_per_day']/1000 for item_id in items}
Path('out/anchors_measured.json').write_text(json.dumps(measured,allow_nan=False,indent=2)+'\n')
MEASURE_PY
