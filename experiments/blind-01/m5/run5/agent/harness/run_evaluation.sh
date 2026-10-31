#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p out "${EVAL_OUT:?EVAL_OUT required}"
# Child runs use the same canonical command and CUDA selection as anchor runs.
# FroDock is CPU-only (gpu_count=0): no used GPUs need synchronization.
# Its published search exposes no RNG seed. Paired seeds label independent
# invocations of that deterministic search; no undocumented seed flag is added.
python3 -u - <<'PYEVAL' 2>&1 | tee -a out/evaluation-adapter.log
import json,math,os,signal,subprocess,time
from pathlib import Path
mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in ('equivalence','warmup','performance','curve'): raise RuntimeError('Unsupported EVAL_MODE: '+mode)
protocol=json.loads(Path(os.environ['EVAL_PROTOCOL']).read_text())
if 'timing_scope' not in protocol: raise RuntimeError('Sealed protocol missing timing_scope')
inputs=json.loads(os.environ['EVAL_INPUTS'])
ids=inputs['ids']
if not isinstance(ids,list) or not ids or not all(isinstance(i,str) for i in ids):
    raise RuntimeError('Invalid sealed input identities')
# This harness stages exactly the fixed input selected in EXECUTION.json.
# Refuse unknown identities instead of silently running a different input.
fixed_case='7zj1__B1_P55265--7zj1__A1_P55265'
if any(input_id!=fixed_case for input_id in ids):
    raise RuntimeError('Unstaged sealed input identity; only fixed EXECUTION.json case is available: '+repr(ids))
seed_protocol=json.loads(os.environ['EVAL_SEEDS'])
if seed_protocol['kind']=='deterministic': seeds=[None]
elif seed_protocol['kind']=='paired_median':
    seeds=seed_protocol['seeds']
    if not seeds or not all(isinstance(s,int) and not isinstance(s,bool) for s in seeds):
        raise RuntimeError('Invalid paired execution seeds')
else: raise RuntimeError('Unsupported seed protocol')
budget_text=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=json.loads(budget_text) if budget_text else None
if mode=='curve' and budget is None: raise RuntimeError('Curve mode requires GPU-second compute budget')
if mode=='curve':
    if isinstance(budget,(int,float)): limit=budget
    elif isinstance(budget,dict):
        limit=budget.get('gpu_seconds',budget.get('gpu_s',budget.get('value')))
    else: limit=None
    if isinstance(limit,bool) or not isinstance(limit,(int,float)) or not math.isfinite(limit) or limit<0:
        raise RuntimeError('Invalid curve budget in GPU seconds')
# Fixed representative workload is the single released apo pair. Input identities
# name sealed runs of this workload; descriptive metadata is never enumerated.
root=Path.cwd()
output=Path(os.environ['EVAL_OUT']); output.mkdir(parents=True,exist_ok=True)
session=Path('out')/('evaluation-'+str(time.time_ns())); session.mkdir()
records=[]
start=time.monotonic()
for seed_index,seed in enumerate(seeds):
    for input_index,input_id in enumerate(ids):
        work=session/str(seed_index)/str(input_index); work.mkdir(parents=True)
        for name in ('baseline-published','method','data','harness','payload'):
            source=root/name
            if source.exists(): (work/name).symlink_to(os.path.relpath(source,work),target_is_directory=True)
        remaining= min(1200.0,2390.0-(time.monotonic()-start))
        if remaining<=0: raise RuntimeError('Evaluation scorer wall budget exhausted')
        began=time.monotonic()
        # No environment overrides; run_anchors invokes bash harness/run_command.sh.
        with (work/'execution.log').open('w') as log:
            child=subprocess.Popen(['bash','harness/run_anchors.sh'],cwd=work,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                status=child.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGTERM)
                try: child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL); child.wait()
                raise RuntimeError('Fixed-scale baseline exceeded execution budget')
            if status: raise RuntimeError('Baseline failed; inspect '+str(work/'execution.log'))
        wall=time.monotonic()-began
        metrics=json.loads((work/'out/metrics_measured.json').read_text())
        metrics['wall_s']=wall
        metrics['candidates_per_s']=metrics['evaluated_candidates']/wall
        if not metrics or not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in metrics.values()):
            raise RuntimeError('Missing or invalid measured evaluation output')
        records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
        # Zero GPU seconds for the published CPU-only implementation. Fixed search
        # is never expanded to spend budget; even zero-GPU runs remain wall-capped.
        gpu_seconds=0.0
        if mode=='curve' and gpu_seconds>limit: raise RuntimeError('GPU-second budget exceeded')
        report={'records':records,'timing_scope':protocol['timing_scope'],'gpu_count':0,
                'wall_s':time.monotonic()-start,'compute_budget':budget}
        (output/'evaluation.partial.json').write_text(json.dumps(report,allow_nan=False)+'\n')
report['wall_s']=time.monotonic()-start
(output/'evaluation.json').write_text(json.dumps(report,allow_nan=False)+'\n')
print(json.dumps(report,allow_nan=False),flush=True)
PYEVAL
