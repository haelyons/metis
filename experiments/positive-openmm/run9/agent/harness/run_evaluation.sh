#!/usr/bin/env bash
set -euo pipefail
: "${EVAL_OUT:?EVAL_OUT is required}"
: "${EVAL_PROTOCOL:?EVAL_PROTOCOL is required}"
: "${EVAL_INPUTS:?EVAL_INPUTS is required}"
: "${EVAL_SEEDS:?EVAL_SEEDS is required}"
mkdir -p "$EVAL_OUT" out/evaluation out/evaluation/tmp out/evaluation/cuda-cache
source baseline-published/cuda.env
export CUDA_VISIBLE_DEVICES=0
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
# Python paths below are interpreted in each out/evaluation/<index> directory.
export PYTHONPATH=../../../baseline-published/python
export TMPDIR=../tmp
export CUDA_CACHE_PATH=../cuda-cache
/usr/bin/python3 - <<'EVAL_PY'
import json, math, os, re, subprocess, time
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

protocol=json.loads(Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs=json.loads(os.environ['EVAL_INPUTS'])
seed_spec=json.loads(os.environ['EVAL_SEEDS'])
ids=inputs['ids']
if not isinstance(ids,list) or not ids or any(not isinstance(x,str) for x in ids):
    raise ValueError('EVAL_INPUTS.ids must contain sealed input identities')
if seed_spec['kind']=='paired_median':
    seeds=seed_spec['seeds']
    if not seeds or any(type(s) is not int for s in seeds):
        raise ValueError('Invalid paired execution seeds')
elif seed_spec['kind']=='deterministic':
    seeds=[None]
else:
    raise ValueError('Unknown seed protocol')
mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in ('equivalence','warmup','performance','curve'):
    raise ValueError('Unsupported EVAL_MODE')
scope=protocol.get('timing_scope')
if scope is None:
    raise ValueError('Seal lacks timing_scope')
raw_budget=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=None
if mode=='curve':
    budget=json.loads(raw_budget)
    if isinstance(budget,dict):
        limit=budget.get('gpu_seconds',budget.get('gpu_s'))
    else:
        limit=budget
    limit=finite(limit,'GPU seconds budget',True)
else:
    limit=None
out=Path(os.environ['EVAL_OUT'])
(out/'evaluation.json').unlink(missing_ok=True)
records=[]
started=time.perf_counter()
for seed in seeds:
    for input_id in ids:
        index=len(records)
        work=Path('out/evaluation')/str(index)
        work.mkdir(parents=True,exist_ok=True)
        pdb=work/'5dfr_solv-cube_equil.pdb'
        if not pdb.exists():
            pdb.symlink_to('../../../data/5dfr_solv-cube_equil.pdb')
        (work/'ensemble.json').unlink(missing_ok=True)
        seed0=1000 if seed is None else seed
        command=['/usr/bin/python3','../../../baseline-published/dhfr_ensemble.py',
                 '--replicas','8','--steps','25000','--seed0',str(seed0),
                 '--platform','CUDA','--out','ensemble.json']
        remaining=None if limit is None else limit-(time.perf_counter()-started)
        if remaining is not None and remaining<=0:
            raise RuntimeError('Curve GPU-seconds budget exhausted')
        # Context deletion in the unchanged driver completes all GPU work before
        # process exit. Energy getState calls also synchronize sampled work.
        with (work/'stdout.log').open('a') as stdout, (work/'stderr.log').open('a') as stderr:
            subprocess.run(command,cwd=work,stdout=stdout,stderr=stderr,check=True,timeout=remaining)
        d,metrics=validate(work/'ensemble.json',work/'stdout.log',seed0)
        records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
wall=time.perf_counter()-started
if limit is not None and wall>limit:
    raise RuntimeError('Curve exceeded one-GPU seconds budget')
result={'records':records,'timing_scope':scope,'gpu_count':1,'wall_s':wall,'compute_budget':budget}
(out/'evaluation.json').write_text(json.dumps(result,allow_nan=False,indent=2)+'\n')
EVAL_PY
