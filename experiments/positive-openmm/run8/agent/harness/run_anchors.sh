#!/usr/bin/env bash
set -euo pipefail
if [[ "${EVAL_MODE:-anchors}" != anchors ]]; then
    exec bash harness/run_evaluation.sh
fi
mkdir -p out
source baseline-published/cuda-env.sh
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY"
bash harness/run_command.sh
python3 - <<'MEASURE'
import json, math, pathlib, re
p=pathlib.Path('out/run')
r=json.loads((p/'ensemble.json').read_text())
def number(v, positive=False):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or (positive and v<=0):
        raise RuntimeError('Invalid numerical output')
    return v
if r['platform']!='CUDA' or r['properties']!={'Precision':'single','DeterministicForces':'true'}:
    raise RuntimeError('Unexpected printed platform configuration')
if len(r['replicas'])!=8 or not math.isclose(number(r['simulated_ns']),0.8):
    raise RuntimeError('Unexpected fixed work')
wall=number(r['total_wall_s'], True)
for i, replica in enumerate(r['replicas']):
    if (replica['replica'],replica['seed'],replica['steps'])!=(i,1000+i,25000):
        raise RuntimeError('Unexpected replica configuration')
    for key in ('wall_s','final_potential_kj_mol','mean_potential_kj_mol'):
        number(replica[key], key=='wall_s')
text=(p/'command.log').read_text()
for name,expected,tol in [('total_wall_s',wall,0.001),('aggregate_ns_per_day',0.8/wall*86400,0.051)]:
    match=re.search(r'^'+name+r': ([0-9.eE+-]+)$',text,re.M)
    if not match or not math.isclose(number(float(match[1]),True),expected,abs_tol=tol,rel_tol=1e-8):
        raise RuntimeError('Missing or inconsistent stdout: '+name)
items=json.loads(pathlib.Path('baseline-published/anchors.json').read_text())
# Reference is in microseconds/day; measured fixed-work throughput is converted.
measured={item['id']: number(r['simulated_ns']/wall*86400/1000,True) for item in items}
pathlib.Path('out/anchors_measured.json').write_text(json.dumps(measured,indent=2,allow_nan=False)+'\n')
MEASURE
