#!/usr/bin/env bash
set -euo pipefail
mkdir -p out "${EVAL_OUT:?EVAL_OUT is required}"
# Each invocation runs the identical published command afresh for each sealed input/seed.
python3 - <<'PY'
import json,math,os,pathlib,signal,subprocess,time
mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in {'equivalence','warmup','performance','curve'}:raise RuntimeError('Unsupported EVAL_MODE')
protocol=json.load(open(os.environ['EVAL_PROTOCOL']))
inputs=json.loads(os.environ['EVAL_INPUTS'])
seed_spec=json.loads(os.environ['EVAL_SEEDS'])
ids=inputs['ids']
if not isinstance(ids,list) or not ids or not all(isinstance(i,str) for i in ids):raise RuntimeError('Invalid sealed input identities')
if seed_spec['kind']=='deterministic':seeds=[None]
elif seed_spec['kind']=='paired_median':
    # No FroDock execution seed interface is specified by the pinned protocol.
    raise RuntimeError('Paired seeds requested, but published FroDock protocol supplies no search seed interface')
else:raise RuntimeError('Unsupported execution seed protocol')
scope=protocol.get('timing_scope')
if scope is None:raise RuntimeError('Seal missing timing_scope')
budget=None
if mode=='curve':
    raw=os.environ.get('EVAL_COMPUTE_BUDGET','')
    if not raw:raise RuntimeError('Curve requires compute budget')
    budget=json.loads(raw)
    # Published baseline consumes zero GPU seconds (CPU/MPI only).
    if not isinstance(budget,(dict,int,float)):raise RuntimeError('Invalid compute budget')
records=[]
started=time.monotonic()
for seed in seeds:
    for identity in ids:
        remaining=1160-(time.monotonic()-started)
        if remaining<=0:raise RuntimeError('Evaluation invocation budget exhausted')
        before=pathlib.Path('out/baseline.log').stat().st_size if pathlib.Path('out/baseline.log').exists() else 0
        with (pathlib.Path(os.environ['EVAL_OUT'])/'execution.log').open('a') as log:
            proc=subprocess.Popen(['bash','harness/run_command.sh'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                status=proc.wait(timeout=remaining)
            except BaseException:
                os.killpg(proc.pid,signal.SIGTERM)
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                raise
            if status:raise subprocess.CalledProcessError(status,proc.args)
        with open('out/baseline.log','rb') as f:f.seek(before);text=f.read().decode()
        outputs=[line[len('BASELINE_OUTPUT '):] for line in text.splitlines() if line.startswith('BASELINE_OUTPUT ')]
        if len(outputs)!=1:raise RuntimeError('Missing or ambiguous fresh output')
        summary=json.loads(outputs[0])
        values=summary['case_metrics'].get(identity,summary['metrics'])
        if not values or not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in values.values()):
            raise RuntimeError('Invalid measured evaluation metrics')
        records.append({'input_id':identity,'seed':seed,'metrics':values})
# No GPU was used: all MPI children have returned synchronously; no CUDA synchronization needed.
result={'records':records,'timing_scope':scope,'gpu_count':0,'wall_s':time.monotonic()-started,'compute_budget':budget}
pathlib.Path(os.environ['EVAL_OUT'],'evaluation.json').write_text(json.dumps(result,allow_nan=False)+'\n')
PY
