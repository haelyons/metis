#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
source baseline-published/cuda.env
ls "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_RUNTIME_LIBRARY"
# CPU-only published method: no GPU context is created or used.
python3 - <<'PY'
import json, math, os, subprocess, time
from pathlib import Path

mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in {'equivalence','warmup','performance','curve'}: raise RuntimeError('Unsupported EVAL_MODE '+mode)
protocol=json.loads(Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs=json.loads(os.environ['EVAL_INPUTS'])
seed_spec=json.loads(os.environ['EVAL_SEEDS'])
ids=inputs.get('ids')
if not isinstance(ids,list) or not ids or not all(isinstance(x,str) and x for x in ids) or len(set(ids))!=len(ids): raise RuntimeError('EVAL_INPUTS.ids must contain unique input identities')
kind=seed_spec.get('kind')
if kind=='deterministic': seeds=[None]
elif kind=='paired_median':
    seeds=seed_spec.get('seeds')
    if not isinstance(seeds,list) or not seeds or not all(isinstance(s,int) and not isinstance(s,bool) for s in seeds): raise RuntimeError('Invalid paired seeds')
else: raise RuntimeError('Unknown seed protocol')
scope=protocol.get('timing_scope')
if scope is None: raise RuntimeError('Seal lacks timing_scope')
raw_budget=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=json.loads(raw_budget) if raw_budget else None
if mode=='curve' and budget is None: raise RuntimeError('Curve requires compute budget')
if mode=='curve':
    if isinstance(budget,(int,float)):
        limit=budget
    elif isinstance(budget,dict):
        limit=next((budget[k] for k in ('gpu_seconds','gpu_s','max_gpu_seconds','budget_gpu_s') if k in budget),None)
    else: limit=None
    if not isinstance(limit,(int,float)) or isinstance(limit,bool) or not math.isfinite(limit) or limit<0: raise RuntimeError('Invalid GPU-seconds budget')
# FroDock has no published stochastic seed flag. Repeated seed identities execute
# fresh unchanged deterministic MPI searches; no invented random seed mechanism.
output=Path(os.environ['EVAL_OUT']); output.mkdir(parents=True,exist_ok=True)
for key in ('BASELINE_DIR','METHOD_DIR','BASELINE_OUT','METHOD_OUT','EVAL_OUT'):
    value=os.environ.get(key)
    if not value or not Path(value).is_absolute(): raise RuntimeError('Missing absolute '+key)
case_ids={c['id'] for c in json.load(open('data/cases.json'))}
records=[]; start=time.monotonic()
env=os.environ.copy(); env['EVAL_MODE']='anchors'
for seed_index,seed in enumerate(seeds):
    for input_index,input_id in enumerate(ids):
        log=output/f'run-{seed_index:04d}-{input_index:04d}.log'
        with log.open('w') as f:
            f.write(json.dumps({'input_id':input_id,'seed':seed,'seed_behavior':'published deterministic MPI protocol; no stochastic seed switch','gpu_count':0})+'\n'); f.flush()
            remaining=86400-(time.monotonic()-start)
            if remaining<=0: raise RuntimeError('Evaluation invocation exceeded wall budget')
            subprocess.run(['bash','harness/run_anchors.sh'],env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=remaining)
        run=Path('out/latest').resolve()
        # Each call produces a new complete 93-case output; never reuse results.
        lines=(run/'scoring.log').read_text().splitlines()
        cases=[json.loads(x[len('CASE_METRICS '):]) for x in lines if x.startswith('CASE_METRICS ')]
        summaries=[json.loads(x[len('SUMMARY '):]) for x in lines if x.startswith('SUMMARY ')]
        if input_id in case_ids:
            found=[c for c in cases if c['input_id']==input_id]
            if len(found)!=1: raise RuntimeError('Missing input metric '+input_id)
            metrics={k:v for k,v in found[0].items() if k!='input_id'}
        else:
            # Non-case IDs identify sealed full-workload executions. Descriptive
            # keys of EVAL_INPUTS never generate additional executions.
            if len(summaries)!=1: raise RuntimeError('Missing full-workload metrics')
            metrics=summaries[0]
        if not metrics or not all(isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) for v in metrics.values()): raise RuntimeError('Invalid measured metrics')
        records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
        (output/f'artifacts-{seed_index:04d}-{input_index:04d}.json').write_text(json.dumps({'run_directory':str(run),'log':str(log)},indent=2)+'\n')
# There are zero used GPUs, hence GPU seconds are identically zero. All MPI
# children have completed before reported wall timer stops; no async GPU work.
wall=time.monotonic()-start
if not math.isfinite(wall) or wall<=0: raise RuntimeError('Invalid wall time')
if mode=='curve':
    if 0>limit: raise RuntimeError('GPU-seconds budget exceeded')
result={'records':records,'timing_scope':scope,'gpu_count':0,'wall_s':wall,'compute_budget':budget}
tmp=output/'evaluation.json.tmp'; tmp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n'); tmp.replace(output/'evaluation.json')
PY
