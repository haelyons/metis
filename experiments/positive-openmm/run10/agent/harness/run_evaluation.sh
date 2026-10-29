#!/usr/bin/env bash
set -euo pipefail
: "${EVAL_OUT:?}" "${BASELINE_DIR:?}" "${EVAL_PROTOCOL:?}" "${EVAL_INPUTS:?}" "${EVAL_SEEDS:?}" "${EVAL_MODE:?}"
mkdir -p "$EVAL_OUT"
base="$BASELINE_DIR"
if [[ ! -f "$base/dhfr_ensemble.py" ]]; then base="$base/baseline-published"; fi
source "$base/cuda-env.sh"
ls "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export CUDA_VISIBLE_DEVICES=0
export PYTHONNOUSERSITE=1
export HARNESS_BASE="$base"
export HARNESS_DATA="$(dirname "$base")/data"
/usr/bin/python3 - <<'EVALUATE'
import json, math, os, pathlib, subprocess, time, tempfile, re
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

env=os.environ
out=pathlib.Path(env['EVAL_OUT'])
result_path=out/'evaluation.json'
result_path.unlink(missing_ok=True)
protocol=json.loads(pathlib.Path(env['EVAL_PROTOCOL']).read_text())
inputs=json.loads(env['EVAL_INPUTS'])
seed_spec=json.loads(env['EVAL_SEEDS'])
ids=inputs['ids']
if not isinstance(ids,list) or not ids or not all(isinstance(i,str) for i in ids):
    raise ValueError('evaluation_inputs.ids must contain input identities')
if seed_spec['kind']=='deterministic':
    seeds=[None]
elif seed_spec['kind']=='paired_median':
    seeds=seed_spec['seeds']
    if not seeds or not all(isinstance(s,int) and not isinstance(s,bool) for s in seeds):
        raise ValueError('Invalid paired execution seeds')
else:
    raise ValueError('Unsupported seed protocol')
mode=env['EVAL_MODE']
if mode not in ('anchors','equivalence','warmup','performance','curve'):
    raise ValueError('Unknown evaluation mode')
timing_scope=protocol['timing_scope']
budget_raw=env.get('EVAL_COMPUTE_BUDGET','')
budget=json.loads(budget_raw) if budget_raw else None
limit=1150.0
if mode=='curve':
    if isinstance(budget,(int,float)):
        gpu_seconds=float(budget)
    elif isinstance(budget,dict):
        gpu_seconds=float(budget['gpu_seconds'])
    else:
        raise ValueError('Curve requires GPU-second compute budget')
    if not math.isfinite(gpu_seconds) or gpu_seconds<=0:
        raise ValueError('Invalid GPU-second budget')
    limit=min(limit,gpu_seconds) # One used GPU: wall seconds equal charged GPU seconds.
base=pathlib.Path(env['HARNESS_BASE']).resolve()
pdb=pathlib.Path(env['HARNESS_DATA'])/'5dfr_solv-cube_equil.pdb'
# Execution seeds identify the original replicas, not eight shifted ensembles.
seed0=1000
if seed_spec['kind']=='paired_median' and seeds != list(range(seed0,seed0+8)):
    raise ValueError('Execution seeds must preserve the published eight replica seeds')
if env.get('EVAL_ARM','baseline') != 'baseline':
    raise ValueError('This adapter executes only the baseline arm')
gpu_count=protocol['hardware_cost_basis']['baseline_gpus']
if gpu_count != 1:
    raise ValueError('Published workload requires one GPU')
metric_names=[m['name'] for m in protocol['equivalence_metrics']]
if set(metric_names) != {'mean_potential_kj_mol','final_potential_kj_mol'}:
    raise ValueError('Unsupported scientific metric definitions')
measurements={}
wall=0.0
start=time.monotonic()
for input_id in ids:
    work=pathlib.Path(tempfile.mkdtemp(prefix='run-',dir=out))
    (work/'5dfr_solv-cube_equil.pdb').symlink_to(pdb.resolve(strict=True))
    command=[str(base/'venv/bin/python3'),str(base/'dhfr_ensemble.py'),'--replicas','8','--steps','25000','--seed0',str(seed0)]
    (work/'invocation.json').write_text(json.dumps(dict(input_id=input_id,seeds=seeds,command=command,gpu_count=gpu_count,CUDA_VISIBLE_DEVICES=env['CUDA_VISIBLE_DEVICES'])))
    remaining=limit-(time.monotonic()-start)
    if remaining<=0:
        raise TimeoutError('Evaluation compute/time budget exhausted')
    with (work/'stdout.log').open('wb') as log:
        subprocess.run(command,cwd=work,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=remaining)
    # The final energy read synchronizes the used GPU, and the published
    # driver destroys every Context before stopping its ensemble timer.
    # Use that scope, excluding imports, common System creation and JSON IO.
    d=json.loads((work/'ensemble.json').read_text())
    throughput=validate(d)
    log=(work/'stdout.log').read_text()
    for name, expected, tolerance in [('total_wall_s',d['total_wall_s'],0.00051), ('aggregate_ns_per_day',throughput,0.051)]:
        matches=re.findall(r'^'+name+r': ([^\n]+)$',log,re.M)
        if not matches or not math.isfinite(float(matches[-1])) or abs(float(matches[-1])-expected)>tolerance:
            raise ValueError('Missing or inconsistent stdout measurement: '+name)
    measurements[input_id]=d
    wall+=d['total_wall_s']
if time.monotonic()-start>limit or wall*gpu_count>limit:
    raise TimeoutError('Evaluation compute/time budget exceeded')
records=[]
for seed in seeds:
    for input_id in ids:
        d=measurements[input_id]
        if seed is None:
            # Deterministic protocols have one record for the whole ensemble.
            metrics={name:sum(r[name] for r in d['replicas'])/8 for name in metric_names}
        else:
            replica=next(r for r in d['replicas'] if r['seed']==seed)
            metrics={name:replica[name] for name in metric_names}
        records.append(dict(input_id=input_id,seed=seed,metrics=metrics))
result=dict(records=records,timing_scope=timing_scope,gpu_count=gpu_count,wall_s=wall)
if mode=='curve':
    result['compute_budget']=budget
if mode=='anchors':
    result={"nvidia-2025-dhfr-eight-tuned-throughput-reference":0.8/measurements[ids[0]]['total_wall_s']*86400}
    result_path=out/'anchors_measured.json'
tmp=result_path.with_suffix('.json.tmp')
tmp.write_text(json.dumps(result,allow_nan=False)+'\n')
tmp.replace(result_path)
EVALUATE
