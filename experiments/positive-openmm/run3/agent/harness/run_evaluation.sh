#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
python3 - <<'PY_EVALUATION'
import json, math, os, pathlib, re, signal, subprocess, time

def finite(x, positive=False):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or (positive and x<=0):
        raise RuntimeError('Missing/invalid numeric output: '+repr(x))
    return x

def read_run(root,seed):
    run=root/(root/'out/last_run.txt').read_text().strip()
    result=json.loads((run/'ensemble.json').read_text())
    c=json.loads((run/'configuration.json').read_text())
    expected_seeds=list(range(seed,seed+8))
    if c['command']!=['python3','dhfr_ensemble.py','--replicas','8','--steps','25000','--seed0',str(seed)]:
        raise RuntimeError('Printed command mismatch')
    if c['CUDA_VISIBLE_DEVICES']!='0' or c['gpu_count']!=1 or c['seeds']!=expected_seeds:
        raise RuntimeError('Printed environment/configuration mismatch')
    if result['platform']!='CUDA' or result['properties']!={'Precision':'single','DeterministicForces':'true'}:
        raise RuntimeError('Invalid platform/properties output')
    if result['simulated_ns']!=0.8 or len(result['replicas'])!=8:
        raise RuntimeError('Invalid ensemble scale output')
    wall=finite(result['total_wall_s'],True)
    throughput=0.8/wall*86400
    metrics={'total_wall_s':wall,'aggregate_ns_per_day':throughput,'aggregate_us_per_day':throughput/1000}
    for i,r in enumerate(result['replicas']):
        if (r['replica'],r['seed'],r['steps'])!=(i,seed+i,25000): raise RuntimeError('Replica configuration mismatch')
        finite(r['wall_s'],True)
        for name in ('final_potential_kj_mol','mean_potential_kj_mol'):
            metrics[f'replica_{i}_{name}']=finite(r[name])
    stdout=(run/'stdout.log').read_text()
    for name,target,tol in [('total_wall_s',wall,0.00051),('aggregate_ns_per_day',throughput,0.051)]:
        matches=re.findall(r'^'+name+r':\s*(\S+)\s*$',stdout,re.M)
        if len(matches)!=1 or abs(finite(float(matches[0]),True)-target)>tol:
            raise RuntimeError('Missing/invalid printed measurement: '+name)
    return metrics

def spec(name):
    raw=os.environ.get(name,'')
    return json.loads(raw) if raw else None

def sequence(value, kind):
    if value is None: return None
    if isinstance(value,dict):
        for key in (kind,'values','items'):
            if key in value: return sequence(value[key],kind)
        if kind=='inputs':
            return [dict(v,id=k) if isinstance(v,dict) else {'id':k,'path':v} for k,v in value.items()]
        raise RuntimeError('Unsupported seed specification: '+repr(value))
    if not isinstance(value,list): raise RuntimeError('Expected list for '+kind)
    return value

mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in ('equivalence','warmup','performance','curve'): raise RuntimeError('Unknown EVAL_MODE')
protocol=json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
if 'timing_scope' not in protocol: raise RuntimeError('Seal missing timing_scope')
inputs=sequence(spec('EVAL_INPUTS'),'inputs')
if inputs is None: inputs=sequence(protocol.get('inputs'),'inputs')
if not inputs: inputs=[{'id':'5dfr_solv-cube_equil','path':'data/5dfr_solv-cube_equil.pdb'}]
seeds=sequence(spec('EVAL_SEEDS'),'seeds')
if seeds is None: seeds=sequence(protocol.get('seeds'),'seeds')
if not seeds: seeds=[None]
budget_raw=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=json.loads(budget_raw) if budget_raw else None
if mode=='curve':
    if isinstance(budget,dict):
        seconds=next((budget[k] for k in ('gpu_seconds','gpu_s','seconds','value') if k in budget),None)
    else: seconds=budget
    finite(seconds,True)
else: seconds=None
root=pathlib.Path.cwd()
baseline=pathlib.Path(os.environ['BASELINE_DIR']).resolve()
eval_out=pathlib.Path(os.environ['EVAL_OUT'])
eval_out.mkdir(parents=True,exist_ok=True)
records=[]
started=time.perf_counter()
deadline=started+1100
if seconds is not None: deadline=min(deadline,started+seconds) # One GPU: wall seconds conservatively bound GPU seconds.
for seed_spec in seeds: # Required ordering: seeds, then input IDs.
    seed=seed_spec.get('seed',seed_spec.get('value')) if isinstance(seed_spec,dict) else seed_spec
    if seed is not None and (isinstance(seed,bool) or not isinstance(seed,int) or seed<0):
        raise RuntimeError('Seed must be a nonnegative integer or null')
    seed0=1000 if seed is None else seed
    for input_spec in inputs:
        if isinstance(input_spec,str):
            item={'id':input_spec}
        elif isinstance(input_spec,dict): item=input_spec
        else: raise RuntimeError('Invalid sealed input')
        input_id=item.get('input_id',item.get('id',item.get('name')))
        if input_id is None: raise RuntimeError('Input ID missing')
        location=item.get('path',item.get('file',item.get('coordinates',item.get('pdb'))))
        if isinstance(location,dict): location=location.get('path',location.get('file'))
        if location is None:
            location='data/5dfr_solv-cube_equil.pdb'
        p=pathlib.Path(location)
        if not p.is_absolute():
            p=root/p
            if not p.is_file(): p=root/'data'/location
        if not p.is_file(): raise RuntimeError('Sealed coordinate input missing: '+str(p))
        # Fresh work directory prevents output reuse and never writes through shared source/data trees.
        import tempfile
        case=pathlib.Path(tempfile.mkdtemp(prefix='evaluation.',dir=root/'out'))
        (case/'baseline-published').symlink_to(baseline,target_is_directory=True)
        (case/'harness').symlink_to(root/'harness',target_is_directory=True)
        (case/'coordinates.pdb').symlink_to(p.resolve())
        env=os.environ.copy()
        env['DHFR_INPUT']='coordinates.pdb'
        env['DHFR_SEED0']=str(seed0)
        remaining=deadline-time.perf_counter()
        if remaining<=0: raise RuntimeError('Evaluation compute/time budget exhausted')
        with (case/'launch.log').open('w') as log:
            proc=subprocess.Popen(['bash','harness/run_command.sh'],cwd=case,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                status=proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL)
                proc.wait()
                raise RuntimeError('Evaluation time/GPU-second budget exhausted')
            if status: raise RuntimeError('Baseline command failed with status '+str(status))
        # Every published replica ends with a blocking energy read and context destruction.
        # Process exit follows destruction of all CUDA contexts, so all used-GPU work has completed.
        metrics=read_run(case,seed0)
        records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
elapsed=time.perf_counter()-started
if seconds is not None and elapsed>seconds: raise RuntimeError('Curve GPU-second budget exceeded')
result={'records':records,'timing_scope':protocol['timing_scope'],'gpu_count':1,
        'wall_s':elapsed,'compute_budget':budget}
# Published ensemble scope excludes imports and serialization; aggregate its measured intervals.
scope=protocol['timing_scope']
if isinstance(scope,str) and ('reported_wall' in scope or scope in ('total_wall_s','ensemble')):
    result['wall_s']=sum(r['metrics']['total_wall_s'] for r in records)
(eval_out/'evaluation.json').write_text(json.dumps(result,allow_nan=False,indent=2)+'\n')
PY_EVALUATION
