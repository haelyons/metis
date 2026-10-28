#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
source baseline-published/cuda-env.sh
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY"
export PATH="$CUDA_BIN:$PATH"
export PYTHONPATH="$PWD/baseline-published/python"
export CUDA_VISIBLE_DEVICES=0
export GPU_COUNT=1
export CUDACXX="$CUDA_NVCC"
export OPENMM_CUDA_COMPILER="$CUDA_NVCC"
export CPATH="$CUDA_INCLUDE${CPATH:+:$CPATH}"
export LD_LIBRARY_PATH="${CUDA_LIBRARY%/*}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python3 - <<'EVALUATE'
import ctypes, json, math, os, pathlib, re, subprocess, sys, tempfile, time
root=pathlib.Path.cwd()
mode=os.environ['EVAL_MODE']
if mode not in ('equivalence','warmup','performance','curve'):
    raise RuntimeError('Unsupported EVAL_MODE: '+mode)
seal=json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs=json.loads(os.environ['EVAL_INPUTS'])
seedspec=json.loads(os.environ['EVAL_SEEDS'])
ids=inputs['ids']
if not isinstance(ids,list) or not ids or any(not isinstance(x,str) for x in ids):
    raise RuntimeError('EVAL_INPUTS.ids must be nonempty list of identities')
if seedspec['kind']=='paired_median':
    seeds=seedspec['seeds']
    if not seeds or any(type(s) is not int for s in seeds):
        raise RuntimeError('Invalid paired seeds')
elif seedspec['kind']=='deterministic':
    seeds=[None]
else:
    raise RuntimeError('Unsupported execution seed protocol')
timing_scope=seal.get('timing_scope')
if timing_scope is None:
    raise RuntimeError('Seal missing timing_scope')
out=pathlib.Path(os.environ['EVAL_OUT'])
out.mkdir(parents=True,exist_ok=True)
# Execution writes only out/; final interface is written at EVAL_OUT as required.
session=pathlib.Path(tempfile.mkdtemp(prefix='evaluation.',dir=root/'out'))
budget_raw=os.environ.get('EVAL_COMPUTE_BUDGET','')
compute_budget=None
budget_seconds=None
if mode=='curve':
    if not budget_raw:
        raise RuntimeError('Curve requires GPU-second compute budget')
    compute_budget=json.loads(budget_raw)
    if isinstance(compute_budget,(int,float)):
        budget_seconds=float(compute_budget)
    elif isinstance(compute_budget,dict):
        for key in ('gpu_seconds','gpu_s','seconds','value'):
            if key in compute_budget:
                budget_seconds=float(compute_budget[key]); break
    if budget_seconds is None or not math.isfinite(budget_seconds) or budget_seconds<=0:
        raise RuntimeError('Invalid GPU-second budget')
# Published getState(getEnergy=True) blocks for each energy sample. All OpenMM
# contexts are destroyed before driver returns. Explicit CUDA synchronization
# additionally completes this process's runtime work on the one visible GPU.
wrapper='''import ctypes, os, runpy, sys
runtime=ctypes.CDLL(os.environ['CUDA_LIBRARY'])
def check(code):
    if code: raise RuntimeError('CUDA synchronization error '+str(code))
check(runtime.cudaSetDevice(0))
check(runtime.cudaDeviceSynchronize())
path=sys.argv[1]
sys.argv=sys.argv[1:]
runpy.run_path(path,run_name='__main__')
check(runtime.cudaDeviceSynchronize())
'''
def finite(value, positive=False):
    if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or (positive and value<=0):
        raise RuntimeError('Missing or invalid measured output')
    return value
records=[]
wall_total=0.0
started=time.perf_counter()
for seed in seeds:
    for identity in ids:
        work=session/('run_%04d'%len(records))
        work.mkdir()
        (work/'5dfr_solv-cube_equil.pdb').symlink_to(root/'data/5dfr_solv-cube_equil.pdb')
        actual_seed=1000 if seed is None else seed
        command=[sys.executable,'-c',wrapper,str(root/'baseline-published/dhfr_ensemble.py'),
                 '--replicas','8','--steps','25000','--seed0',str(actual_seed)]
        remaining=1150-(time.perf_counter()-started)
        if budget_seconds is not None:
            # One GPU: elapsed wall seconds equal charged GPU seconds, including
            # process launch, transfers, context setup, synchronization and merge.
            remaining=min(remaining,budget_seconds-(time.perf_counter()-started))
        if remaining<=0:
            raise RuntimeError('Evaluation compute budget exhausted')
        began=time.perf_counter()
        with (work/'command.log').open('w') as log:
            log.write(json.dumps({'command':command[3:], 'CUDA_VISIBLE_DEVICES':'0',
                                  'gpu_count':1,'seed0':actual_seed})+'\n')
            log.flush()
            try:
                subprocess.run(command,cwd=work,stdout=log,stderr=subprocess.STDOUT,
                               timeout=remaining,check=True)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError('Evaluation GPU-second/time budget exhausted') from exc
        elapsed=time.perf_counter()-began
        r=json.loads((work/'ensemble.json').read_text())
        if r['platform']!='CUDA' or r['properties']!={'Precision':'single','DeterministicForces':'true'}:
            raise RuntimeError('Unexpected printed platform configuration')
        if len(r['replicas'])!=8 or not math.isclose(finite(r['simulated_ns']),0.8):
            raise RuntimeError('Unexpected fixed work')
        wall=finite(r['total_wall_s'],True)
        metrics={'total_wall_s':wall,'aggregate_ns_per_day':0.8/wall*86400,
                 'aggregate_us_per_day':0.8/wall*86.4,'simulated_ns':0.8}
        for index,replica in enumerate(r['replicas']):
            if (replica['replica'],replica['seed'],replica['steps'])!=(index,actual_seed+index,25000):
                raise RuntimeError('Unexpected replica configuration')
            for key in ('wall_s','final_potential_kj_mol','mean_potential_kj_mol'):
                value=finite(replica[key],key=='wall_s')
                metrics['replica_'+str(index)+'_'+key]=value
        for key in ('final_potential_kj_mol','mean_potential_kj_mol'):
            metrics[key]=sum(finite(x[key]) for x in r['replicas'])/8
        text=(work/'command.log').read_text()
        for name,expected,tolerance in [('total_wall_s',wall,0.001),
                ('aggregate_ns_per_day',metrics['aggregate_ns_per_day'],0.051)]:
            match=re.search(r'^'+name+r': ([0-9.eE+-]+)$',text,re.M)
            if not match or not math.isclose(finite(float(match[1]),True),expected,rel_tol=1e-8,abs_tol=tolerance):
                raise RuntimeError('Missing or inconsistent printed metric: '+name)
        records.append({'input_id':identity,'seed':seed,'metrics':metrics})
        wall_total+=elapsed
result={'records':records,'timing_scope':timing_scope,'gpu_count':1,
        'wall_s':time.perf_counter()-started,'compute_budget':compute_budget}
if budget_seconds is not None and result['wall_s']>budget_seconds:
    raise RuntimeError('Curve exceeded GPU-second budget')
encoded=json.dumps(result,indent=2,allow_nan=False)+'\n'
(out/'evaluation.json').write_text(encoded)
(session/'evaluation.json').write_text(encoded)
EVALUATE
