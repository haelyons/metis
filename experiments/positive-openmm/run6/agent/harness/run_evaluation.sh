#!/usr/bin/env bash
set -euo pipefail
source baseline-published/runtime.env
ls "$CUDA_COMPILER" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export CUDA_VISIBLE_DEVICES=0 GPU_COUNT=1
export OPENMM_CPU_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/baseline-published/python"
: "${EVAL_OUT:?EVAL_OUT required}" "${EVAL_PROTOCOL:?EVAL_PROTOCOL required}"
mkdir -p "$EVAL_OUT"
/usr/bin/python3 - <<'EVALUATE'
import ctypes, json, math, os, pathlib, signal, subprocess, time
from openmm import app

def validate(path, seed0):
    value = json.loads(path.read_text())
    def finite(x, positive=False):
        if isinstance(x, bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or (positive and x <= 0):
            raise ValueError('Invalid measured value: '+repr(x))
        return x
    if value['platform'] != 'CUDA' or value['properties'] != {'Precision':'single','DeterministicForces':'true'}:
        raise ValueError('Output platform/properties disagree with published CUDA configuration')
    if not math.isclose(finite(value['simulated_ns']), 0.8, rel_tol=1e-12):
        raise ValueError('Output simulated work disagrees with 8 x 25000 steps at 4 fs')
    wall = finite(value['total_wall_s'], True)
    replicas = value['replicas']
    if len(replicas) != 8 or sorted(r['replica'] for r in replicas) != list(range(8)):
        raise ValueError('Missing/duplicate replica output')
    metrics = {'total_wall_s':wall, 'aggregate_ns_per_day':86400*value['simulated_ns']/wall}
    for r in replicas:
        if r['steps'] != 25000 or r['seed'] != seed0+r['replica']:
            raise ValueError('Output steps/seeds disagree with command')
        for key in ('wall_s','final_potential_kj_mol','mean_potential_kj_mol'):
            metrics[f"replica_{r['replica']}_{key}"] = finite(r[key], key=='wall_s')
    return metrics


mode = os.environ.get('EVAL_MODE','equivalence')
if mode not in ('equivalence','warmup','performance','curve'):
    raise ValueError('Unsupported EVAL_MODE: '+mode)
protocol = json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
if 'timing_scope' not in protocol:
    raise ValueError('Seal missing timing_scope')
base = pathlib.Path(os.environ.get('BASELINE_DIR','baseline-published')).resolve()
out = pathlib.Path(os.environ['EVAL_OUT']).resolve()
(out/'evaluation.json').unlink(missing_ok=True)
data = pathlib.Path('data').resolve()
inputs = json.loads(os.environ['EVAL_INPUTS']) if os.environ.get('EVAL_INPUTS') else protocol.get('inputs', [{'input_id':'dhfr'}])
seeds = json.loads(os.environ['EVAL_SEEDS']) if os.environ.get('EVAL_SEEDS') else protocol.get('seeds',[1000])
if isinstance(inputs,dict):
    if 'inputs' in inputs: inputs = inputs['inputs']
    elif 'input_id' in inputs or 'id' in inputs: inputs = [inputs]
    else: inputs = [dict(v,input_id=k) if isinstance(v,dict) else {'input_id':k,'path':v} for k,v in inputs.items()]
if isinstance(seeds,dict):
    seeds = seeds.get('seeds',seeds.get('values'))
if seeds is None: seeds = [None]
if not isinstance(seeds,list): seeds = [seeds]
if not inputs or not seeds:
    raise ValueError('Sealed inputs/seeds cannot be empty')
budget = None
if mode == 'curve':
    raw = os.environ.get('EVAL_COMPUTE_BUDGET','')
    if not raw: raise ValueError('Curve requires GPU-second compute budget')
    budget = json.loads(raw)
    if isinstance(budget,dict):
        budget = budget.get('gpu_seconds',budget.get('gpu_s',budget.get('compute_budget')))
    if isinstance(budget,bool) or not isinstance(budget,(int,float)) or not math.isfinite(budget) or budget<=0:
        raise ValueError('Invalid curve GPU-second compute budget')
# Exactly one GPU is exposed. Explicit runtime synchronization brackets reported
# wall time. Each driver also reads energy synchronously and destroys all contexts
# before exiting, so subprocess completion includes its GPU work.
cuda = ctypes.CDLL(str(pathlib.Path(os.environ['CUDA_LIBRARY_DIR'])/'libcudart.so'))
def sync():
    for function,args in [('cudaSetDevice',(0,)),('cudaDeviceSynchronize',())]:
        status = getattr(cuda,function)(*args)
        if status != 0: raise RuntimeError(function+' failed: '+str(status))
records=[]
sync()
start=time.perf_counter()
# Outer order is seeds, inner order is input IDs as required by the seal.
normalized=[]
for item in inputs:
    if isinstance(item,str): item={'input_id':item}
    if not isinstance(item,dict): raise ValueError('Invalid sealed input')
    identity=item.get('input_id',item.get('id',item.get('name')))
    if identity is None: raise ValueError('Sealed input missing ID')
    normalized.append((str(identity),item))
normalized.sort(key=lambda pair: pair[0])
for seed_spec in seeds:
    seed = seed_spec.get('seed',seed_spec.get('value')) if isinstance(seed_spec,dict) else seed_spec
    if seed is not None and (isinstance(seed,bool) or not isinstance(seed,int) or seed<=0):
        raise ValueError('Seed must be a positive integer or null')
    seed0=1000 if seed is None else seed
    for input_id,item in normalized:
        # The published protocol fixes work; sealed inputs may select coordinates
        # but cannot silently change physical or integration configuration.
        expected={'replicas':8,'steps':25000,'steps_per_replica':25000,'gpu_count':1,'timestep_fs':4,'platform':'CUDA','precision':'single','energy_interval_steps':250}
        for config in (item,item.get('configuration',{}),item.get('parameters',{})):
            for key,value in expected.items():
                if key in config and config[key]!=value:
                    raise ValueError('Sealed input changes published '+key)
        pdb_spec=item.get('pdb',item.get('path',item.get('file','5dfr_solv-cube_equil.pdb')))
        if isinstance(pdb_spec,dict): pdb_spec=pdb_spec.get('path',pdb_spec.get('file'))
        source=pathlib.Path(pdb_spec)
        if not source.is_absolute():
            source = source if source.is_file() else data/source
        source=source.resolve(strict=True)
        if app.PDBFile(str(source)).topology.getNumAtoms()!=23558:
            raise ValueError('Sealed input changes published DHFR atom count')
        work=out/f'run_{len(records):04d}'
        work.mkdir(parents=True,exist_ok=True)
        pdb=work/'5dfr_solv-cube_equil.pdb'
        pdb.unlink(missing_ok=True)
        pdb.symlink_to(source)
        result=work/'ensemble.json'
        result.unlink(missing_ok=True)
        (work/'cuda-cache').mkdir(exist_ok=True)
        env=os.environ.copy()
        env['PYTHONPATH']=str(base/'python')
        env['OPENMM_CACHE_DIR']=str(work/'cuda-cache')
        env['CUDA_CACHE_PATH']=str(work/'cuda-cache')
        cmd=['/usr/bin/python3',str(base/'dhfr_ensemble.py'),'--replicas','8','--steps','25000','--seed0',str(seed0),'--out','ensemble.json']
        remaining=1100-(time.perf_counter()-start)
        if budget is not None: remaining=min(remaining,budget-(time.perf_counter()-start))
        if remaining<=0: raise RuntimeError('Evaluation compute/time budget exhausted')
        with (work/'stdout.log').open('a') as log:
            log.write(json.dumps({'command':cmd,'input_id':input_id,'seed':seed,'CUDA_VISIBLE_DEVICES':env['CUDA_VISIBLE_DEVICES'],'gpu_count':1})+'\n')
            log.flush()
            process=subprocess.Popen(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                code=process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL)
                process.wait()
                sync()
                raise RuntimeError('Published fixed-work run exceeded evaluation budget; no partial results accepted')
        sync()
        if code: raise RuntimeError('Published baseline failed; see '+str(work/'stdout.log'))
        metrics=validate(result,seed0)
        records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
sync()
wall=time.perf_counter()-start
if budget is not None and wall>budget:
    raise RuntimeError('Curve GPU-second budget exceeded')
report={'records':records,'timing_scope':protocol['timing_scope'],'gpu_count':1,'wall_s':wall,'compute_budget':budget}
(out/'evaluation.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps(report,allow_nan=False))
EVALUATE
