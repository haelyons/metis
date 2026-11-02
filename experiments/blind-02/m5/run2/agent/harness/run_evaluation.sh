#!/usr/bin/env bash
set -euo pipefail
: "${EVAL_MODE:?Missing evaluation mode}"
: "${EVAL_PROTOCOL:?Missing sealed protocol}"
: "${EVAL_INPUTS:?Missing sealed input identities}"
: "${EVAL_SEEDS:?Missing sealed execution seeds}"
: "${EVAL_OUT:?Missing evaluation output directory}"
source baseline-published/cuda.env
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
export CUDA_VISIBLE_DEVICES=0
mkdir -p "$EVAL_OUT" out
python3 - <<'PY'
import ctypes, json, math, os, pathlib, signal, subprocess, time
mode=os.environ['EVAL_MODE']
if mode not in {'equivalence','warmup','performance','curve'}: raise RuntimeError('Unknown EVAL_MODE')
work=pathlib.Path.cwd()
output=pathlib.Path(os.environ['EVAL_OUT']); output.mkdir(parents=True,exist_ok=True)
seal=json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs=json.loads(os.environ['EVAL_INPUTS'])
ids=inputs['ids']
if not isinstance(ids,list) or not ids or any(not isinstance(x,str) for x in ids) or len(set(ids))!=len(ids):
    raise RuntimeError('Invalid sealed input ids')
seed_spec=json.loads(os.environ['EVAL_SEEDS'])
if seed_spec['kind']=='deterministic': seeds=[None]
elif seed_spec['kind']=='paired_median':
    seeds=seed_spec['seeds']
    if not seeds or any(type(s) is not int for s in seeds): raise RuntimeError('Invalid paired seeds')
else: raise RuntimeError('Unsupported seed protocol')
if 'timing_scope' not in seal: raise RuntimeError('Seal lacks timing_scope')
scope=seal['timing_scope']
manifest=json.loads((work/'baseline-published/intake.json').read_text())
lookup={}
for case in manifest['data']['cases']:
    lookup[case['id']]=case['id']; lookup[case['system_id']]=case['id']
for identity in ids:
    if identity not in lookup: raise RuntimeError('Sealed input outside published fixed workload: '+identity)
budget_raw=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=None
if mode=='curve':
    try: budget=float(budget_raw)
    except ValueError: raise RuntimeError('Curve budget must be numeric GPU seconds')
    if not math.isfinite(budget) or budget<=0: raise RuntimeError('Invalid curve GPU-second budget')
# Exactly one GPU, matching run_command.sh. Completed child processes have released
# all their CUDA work; explicitly synchronize the visible device at timer boundaries.
cuda=ctypes.CDLL(os.environ['CUDA_LIB']+'/libcudart.so')
def sync():
    for fn,args in [('cudaSetDevice',(0,)),('cudaDeviceSynchronize',())]:
        rc=getattr(cuda,fn)(*args)
        if rc: raise RuntimeError(f'{fn} failed with CUDA status {rc}')
sync()
started=time.monotonic(); records=[]
# Adapter's invocation ceiling includes launches, docking, transfer, pose merging,
# scoring and output parsing. One visible GPU makes wall seconds a conservative
# upper bound on allocated GPU seconds, including CPU-only portions.
limit=min(1190.0,budget) if budget is not None else 1190.0
for seed_index,seed in enumerate(seeds):
    run=output/f'execution_{seed_index}_{time.time_ns()}'
    run.mkdir()
    # Each seed executes the identical fixed four-input comparison. Native
    # structures enter only PINDER scoring, never docking or scale selection.
    links={'baseline-published':pathlib.Path(os.environ.get('BASELINE_DIR',str(work/'baseline-published'))),
           'data':work/'data','harness':work/'harness'}
    for name,target in links.items(): (run/name).symlink_to(target.resolve(),target_is_directory=True)
    env=os.environ.copy()
    env['EVAL_MODE']='anchors'
    remain=limit-(time.monotonic()-started)
    if remain<=0: raise RuntimeError('Evaluation compute/time budget exhausted')
    with (run/'execution.log').open('w') as log:
        proc=subprocess.Popen(['bash','harness/run_anchors.sh'],cwd=run,env=env,
                              stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try: rc=proc.wait(timeout=remain)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL); proc.wait()
            sync()
            raise RuntimeError('Evaluation exceeded GPU-second/time budget; partial logs preserved')
    if rc: raise RuntimeError(f'Published baseline failed ({rc}); see {run}/execution.log')
    summary=json.loads((run/'out/latest-run/summary.json').read_text())
    for identity in ids:
        case=summary[lookup[identity]]; metrics={}
        for config in ['cpu_standard','gpu_standard','gpu_dense']:
            for name,value in case[config].items(): metrics[config+'_'+name]=value
        for name,value in case['dense_minus_standard'].items(): metrics['dense_minus_standard_'+name]=value
        for name,value in case['agreement'].items():
            if value is not None: metrics[name]=value
        if not metrics or any(type(x) not in (float,int) or not math.isfinite(x) for x in metrics.values()):
            raise RuntimeError('Missing or nonfinite measured evaluation outputs')
        records.append({'input_id':identity,'seed':seed,'metrics':metrics})
sync()
wall=time.monotonic()-started
if wall>limit: raise RuntimeError('Evaluation exceeded GPU-second/time budget')
result={'records':records,'timing_scope':scope,'gpu_count':1,'wall_s':wall,
        'compute_budget':budget}
(output/'evaluation.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps(result,allow_nan=False))
PY
