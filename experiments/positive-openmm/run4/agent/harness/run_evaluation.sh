#!/usr/bin/env bash
set -euo pipefail
source baseline-published/cuda-env.sh
ls -l "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export OPENMM_CUDA_COMPILER="$CUDACXX"
export CUDA_VISIBLE_DEVICES=0
export PYTHONDONTWRITEBYTECODE=1
mkdir -p out
python3 - <<'PY'
import json, math, os, pathlib, subprocess, sys, time
started=time.perf_counter()
root=pathlib.Path.cwd()
mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in ('equivalence','warmup','performance','curve'):
    raise ValueError('Unsupported EVAL_MODE: '+mode)
protocol=json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
scope=protocol['timing_scope']
out=pathlib.Path(os.environ['EVAL_OUT'])
out.mkdir(parents=True,exist_ok=True)
# Remove stale result before starting; preserve all per-invocation logs.
(out/'evaluation.json').unlink(missing_ok=True)
base=pathlib.Path(os.environ['BASELINE_DIR'])

def specification(name, default):
    raw=os.environ.get(name,'')
    return json.loads(raw) if raw else default

inputs=specification('EVAL_INPUTS',protocol.get('inputs',[{'input_id':'dhfr'}]))
if isinstance(inputs,dict) and 'inputs' in inputs:
    inputs=inputs['inputs']
if isinstance(inputs,dict):
    inputs=[dict(value,input_id=key) if isinstance(value,dict) else {'input_id':key,'path':value}
            for key,value in inputs.items()]
if not isinstance(inputs,list) or not inputs:
    raise ValueError('EVAL_INPUTS must specify a nonempty input list or mapping')
seeds=specification('EVAL_SEEDS',protocol.get('seeds',[None]))
if isinstance(seeds,dict):
    seeds=seeds.get('seeds',seeds.get('values'))
if seeds is None:
    seeds=[None]
if not isinstance(seeds,list) or not seeds:
    raise ValueError('EVAL_SEEDS must specify a nonempty list')
budget=specification('EVAL_COMPUTE_BUDGET',None)
limit=None
if mode=='curve':
    if isinstance(budget,dict):
        limit=budget.get('gpu_seconds',budget.get('gpu_s'))
    else:
        limit=budget
    if isinstance(limit,bool) or not isinstance(limit,(int,float)) or not math.isfinite(limit) or limit<=0:
        raise ValueError('Curve budget must supply positive finite GPU seconds')

def finite(value,positive=False):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or (positive and value<=0):
        raise ValueError('Missing or invalid output measurement: '+repr(value))
    return value

records=[]
# Seeds outermost, input IDs sorted inside each seed.
normalized=[]
for item in inputs:
    if isinstance(item,str):
        item={'input_id':item}
    if not isinstance(item,dict):
        raise ValueError('Invalid input specification')
    identity=item.get('input_id',item.get('id',item.get('name')))
    if identity is None:
        raise ValueError('Input specification requires input_id')
    normalized.append((str(identity),item))
normalized.sort(key=lambda pair:pair[0])
import tempfile
invocation=pathlib.Path(tempfile.mkdtemp(prefix='evaluation.',dir=root/'out'))
for seed in seeds:
    if isinstance(seed,dict):
        seed=seed.get('seed',seed.get('value'))
    if seed is not None and (isinstance(seed,bool) or not isinstance(seed,int) or seed<=0 or seed>2147483639):
        raise ValueError('Invalid OpenMM seed')
    seed0=1000 if seed is None else seed
    for identity,item in normalized:
        # Fixed ensemble scale is never adjusted to fill a budget.
        for key,expected in [('replicas',8),('steps',25000),('steps_per_replica',25000),('gpu_count',1)]:
            if key in item and item[key]!=expected:
                raise ValueError('Sealed input conflicts with fixed published scale: '+key)
        work=invocation/('run.%04d'%len(records))
        work.mkdir()
        input_path=item.get('pdb_path',item.get('path',item.get('file')))
        pdb=pathlib.Path(input_path) if input_path else root/'data/5dfr_solv-cube_equil.pdb'
        if not pdb.is_absolute():
            pdb=root/pdb
        if pdb.is_dir():
            pdb=pdb/'5dfr_solv-cube_equil.pdb'
        if not pdb.is_file():
            raise ValueError('Missing sealed input: '+str(pdb))
        (work/'5dfr_solv-cube_equil.pdb').symlink_to(os.path.relpath(pdb,work))
        (work/'dhfr_ensemble.py').symlink_to(os.path.relpath(base/'dhfr_ensemble.py',work))
        env=os.environ.copy()
        env['PYTHONPATH']=os.path.relpath(base/'python',work)
        env['CUDA_CACHE_PATH']='cuda-cache'
        (work/'cuda-cache').mkdir()
        command=['python3','dhfr_ensemble.py','--replicas','8','--steps','25000','--seed0',str(seed0)]
        configuration={'command':command,'working_directory':os.path.relpath(work,root),
                       'CUDA_VISIBLE_DEVICES':env['CUDA_VISIBLE_DEVICES'],'gpu_count':1,
                       'seed0':seed0,'replicas':8,'steps_per_replica':25000}
        (work/'configuration.json').write_text(json.dumps(configuration,indent=2)+'\n')
        print(json.dumps(configuration),flush=True)
        elapsed=time.perf_counter()-started
        remaining=1150-elapsed
        if limit is not None:
            remaining=min(remaining,limit-elapsed)  # one GPU: GPU seconds = elapsed seconds
        if remaining<=0:
            raise RuntimeError('Evaluation compute/time budget exhausted')
        with (work/'command.log').open('w') as log:
            # Process exit follows synchronous energy reads and destruction of every CUDA context.
            # On timeout no evaluation result is emitted; no partial measurement is accepted.
            subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,
                           check=True,timeout=remaining)
        result=json.loads((work/'ensemble.json').read_text())
        if result['platform']!='CUDA' or result['properties']!={'Precision':'single','DeterministicForces':'true'}:
            raise ValueError('Invalid measured platform/properties')
        if result['simulated_ns']!=0.8 or len(result['replicas'])!=8:
            raise ValueError('Invalid measured ensemble size')
        metrics={'total_wall_s':finite(result['total_wall_s'],True)}
        metrics['aggregate_ns_per_day']=0.8/metrics['total_wall_s']*86400
        metrics['aggregate_us_per_day']=metrics['aggregate_ns_per_day']/1000
        for index,replica in enumerate(result['replicas']):
            if (replica['replica'],replica['seed'],replica['steps'])!=(index,seed0+index,25000):
                raise ValueError('Output disagrees with executed command')
            for key in ('wall_s','final_potential_kj_mol','mean_potential_kj_mol'):
                metrics['replica_%d_%s'%(index,key)]=finite(replica[key],key=='wall_s')
        # Validate published printed measurements against serialized actual output.
        import re
        log=(work/'command.log').read_text()
        for key,expected,rounding in [('total_wall_s',metrics['total_wall_s'],0.000501),
                                      ('aggregate_ns_per_day',metrics['aggregate_ns_per_day'],0.050001)]:
            match=re.search(r'^'+key+r':\s*(\S+)\s*$',log,re.M)
            if not match or abs(finite(float(match[1]),True)-expected)>rounding:
                raise ValueError('Missing or inconsistent stdout: '+key)
        records.append({'input_id':identity,'seed':seed,'metrics':metrics})
wall=time.perf_counter()-started
if limit is not None and wall>limit:
    raise RuntimeError('Curve GPU-second budget exceeded')
result={'records':records,'timing_scope':scope,'gpu_count':1,
        'wall_s':finite(wall,True),'compute_budget':budget}
staged=out/'evaluation.json.tmp'
staged.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
staged.replace(out/'evaluation.json')
PY
