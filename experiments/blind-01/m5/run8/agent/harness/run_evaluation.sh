#!/usr/bin/env bash
set -euo pipefail
: "${EVAL_OUT:?EVAL_OUT required}"
: "${EVAL_PROTOCOL:?EVAL_PROTOCOL required}"
: "${EVAL_INPUTS:?EVAL_INPUTS required}"
: "${EVAL_SEEDS:?EVAL_SEEDS required}"
mkdir -p "$EVAL_OUT" out
exec > >(tee -a "$EVAL_OUT/adapter.log") 2>&1
source baseline-published/cuda.env
export CUDA_VISIBLE_DEVICES=''
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
export PINDER_BASE_DIR=data
export PINDER_RELEASE=2024-02
export PINDER_DATA_DIR=data/2024-02
export PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
baseline-published/venv/bin/python - <<'PY'
import json,math,os,subprocess,time
from pathlib import Path
out=Path(os.environ['EVAL_OUT'])
seal=json.loads(Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs=json.loads(os.environ['EVAL_INPUTS'])
seed_protocol=json.loads(os.environ['EVAL_SEEDS'])
mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in ['equivalence','warmup','performance','curve']: raise ValueError('Unknown evaluation mode')
ids=inputs['ids']
if not isinstance(ids,list) or not ids or not all(isinstance(i,str) for i in ids): raise ValueError('Invalid sealed input ids')
kind=seed_protocol['kind']
if kind=='deterministic': seeds=[None]
elif kind=='paired_median':
    seeds=seed_protocol['seeds']
    if not seeds or not all(type(s) is int for s in seeds): raise ValueError('Invalid paired seeds')
    # FroDock exposes no stochastic seed. Execute every requested pair independently.
else: raise ValueError('Unsupported seed protocol')
scope=seal.get('timing_scope')
if scope is None: raise ValueError('Seal missing timing_scope')
budget_text=os.environ.get('EVAL_COMPUTE_BUDGET','')
if mode=='curve' and not budget_text: raise ValueError('Curve compute budget required')
try: budget=json.loads(budget_text) if budget_text else None
except json.JSONDecodeError: raise ValueError('Invalid compute budget JSON')
records=[]; start=time.perf_counter()
for seed in seeds:
    for input_id in ids:
        tag=f'{len(records):05d}'
        logpath=out/f'run-{tag}-{time.time_ns()}.log'
        command=['baseline-published/venv/bin/python','baseline-published/run_baseline.py','--cases','data/cases.json','--out','out','--mpi-np','8','--n-solutions','100','--gpu-count','0','--input-id',input_id]
        with logpath.open('w') as log:
            subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
        lines=logpath.read_text().splitlines()
        configs=[json.loads(l[7:]) for l in lines if l.startswith('CONFIG ')]
        if not configs: raise ValueError('Missing printed configuration')
        c=configs[-1]
        if (c['mpi_np'],c['n_solutions'],c['gpu_count'],c['CUDA_VISIBLE_DEVICES'])!=(8,100,0,''):
            raise ValueError('Evaluation configuration mismatch')
        measures=[json.loads(l[12:]) for l in lines if l.startswith('MEASUREMENT ')]
        if not measures: raise ValueError('Missing actual measurements')
        m=measures[-1]
        metrics={k:float(v) for k,v in m.items() if isinstance(v,(int,float))}
        metrics.update({k:float(v) for k,v in m['anchors'].items()})
        if not metrics or not all(math.isfinite(v) for v in metrics.values()): raise ValueError('Invalid output metrics')
        records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
# CPU-only baseline: no used GPUs to synchronize, GPU-seconds consumed = 0.
# Every MPI child completed before subprocess.run returned, including pose merge and I/O.
wall=time.perf_counter()-start
result={'records':records,'timing_scope':scope,'gpu_count':0,'wall_s':wall,'compute_budget':budget}
if mode=='curve':
    # Enforce a finite nonnegative GPU-second cap; this baseline consumes zero GPU-seconds.
    cap=budget
    if isinstance(cap,dict):
        cap=next((cap[k] for k in ['gpu_seconds','gpu_s','value','budget'] if k in cap),None)
    if not isinstance(cap,(int,float)) or not math.isfinite(cap) or cap<0: raise ValueError('Invalid GPU-second budget')
    if 0.0>cap: raise RuntimeError('GPU-second budget exceeded')
path=out/'evaluation.json'
tmp=out/'evaluation.json.tmp'; tmp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n'); tmp.replace(path)
PY
