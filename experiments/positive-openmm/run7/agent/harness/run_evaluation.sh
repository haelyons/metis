#!/usr/bin/env bash
set -euo pipefail
source baseline-published/toolkit.env
export CUDA_VISIBLE_DEVICES=0
export PYTHONDONTWRITEBYTECODE=1
ls "$CUDACXX" "$CUDA_INCLUDE_DIRS/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
python3 - <<'EVALUATE'
import ctypes, json, math, os, pathlib, subprocess, time
root = pathlib.Path.cwd()
baseline = pathlib.Path(os.environ.get('BASELINE_DIR', root/'baseline-published'))
out = pathlib.Path(os.environ['EVAL_OUT'])
out.mkdir(parents=True, exist_ok=True)
result = out/'evaluation.json'
result.unlink(missing_ok=True)
protocol = json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
mode = os.environ.get('EVAL_MODE', 'equivalence')
if mode not in ('equivalence', 'warmup', 'performance', 'curve'):
    raise ValueError('Unsupported EVAL_MODE')
scope = protocol['timing_scope']
def spec(name, fallback):
    raw = os.environ.get(name, '')
    return json.loads(raw) if raw else fallback
inputs = spec('EVAL_INPUTS', protocol.get('inputs', [{'input_id':'dhfr'}]))
seeds = spec('EVAL_SEEDS', protocol.get('seeds', [None]))
if isinstance(inputs, dict):
    if 'inputs' in inputs:
        inputs = inputs['inputs']
    elif 'input_id' in inputs or 'id' in inputs:
        inputs = [inputs]
    else:
        inputs = [dict(v, input_id=k) if isinstance(v,dict) else {'input_id':k, 'path':v} for k,v in inputs.items()]
if isinstance(seeds, dict):
    seeds = seeds.get('seeds', seeds.get('values'))
if seeds is None:
    seeds = [None]
if not isinstance(seeds,list):
    seeds = [seeds]
if not inputs or not seeds:
    raise ValueError('Empty sealed input or seed specification')
budget = spec('EVAL_COMPUTE_BUDGET', None)
limit = None
if mode == 'curve':
    limit = budget.get('gpu_seconds', budget.get('gpu_s')) if isinstance(budget,dict) else budget
    if isinstance(limit,bool) or not isinstance(limit,(int,float)) or not math.isfinite(limit) or limit <= 0:
        raise ValueError('Curve requires positive GPU-second budget')
# Explicitly synchronize the single visible GPU. Completed child processes also
# destroy their CUDA contexts before returning, including all queued work.
cuda = ctypes.CDLL('libcuda.so.1')
def checked(code):
    if code != 0:
        raise RuntimeError('CUDA synchronization failed: '+str(code))
checked(cuda.cuInit(0))
count = ctypes.c_int()
checked(cuda.cuDeviceGetCount(ctypes.byref(count)))
if count.value != 1:
    raise RuntimeError('Expected exactly one visible GPU')
def sync():
    context = ctypes.c_void_p()
    checked(cuda.cuDevicePrimaryCtxRetain(ctypes.byref(context), 0))
    try:
        checked(cuda.cuCtxSetCurrent(context))
        checked(cuda.cuCtxSynchronize())
    finally:
        checked(cuda.cuDevicePrimaryCtxRelease(0))
def finite(x, positive=False):
    if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) or (positive and x <= 0):
        raise ValueError('Invalid output measurement: '+repr(x))
    return x
records = []
started = time.perf_counter()
for seed in seeds:
    if isinstance(seed,dict):
        seed = seed.get('seed',seed.get('value'))
    if seed is not None and (isinstance(seed,bool) or not isinstance(seed,int) or seed <= 0):
        raise ValueError('Invalid sealed seed')
    seed0 = 1000 if seed is None else seed
    for item in inputs:
        if not isinstance(item,dict):
            item = {'input_id':str(item)}
        input_id = item.get('input_id',item.get('id',item.get('name')))
        if input_id is None:
            raise ValueError('Missing input ID')
        coordinates = item.get('path',item.get('pdb',item.get('coordinates', root/'data/5dfr_solv-cube_equil.pdb')))
        if isinstance(coordinates,dict):
            coordinates = coordinates['path']
        coordinates = pathlib.Path(coordinates)
        if not coordinates.is_absolute():
            coordinates = root/coordinates
        if not coordinates.is_file():
            raise FileNotFoundError(coordinates)
        work = out/('run-%04d'%len(records))
        work.mkdir(exist_ok=True)
        link = work/'5dfr_solv-cube_equil.pdb'
        link.unlink(missing_ok=True)
        link.symlink_to(coordinates)
        output = work/'ensemble.json'
        output.unlink(missing_ok=True)
        command = [str(baseline/'venv/bin/python3'),str(baseline/'dhfr_ensemble.py'),
                   '--replicas','8','--steps','25000','--seed0',str(seed0),
                   '--platform','CUDA','--out','ensemble.json']
        sync()
        began = time.perf_counter()
        remaining = 1150-(began-started)
        if limit is not None:
            remaining = min(remaining,limit-(began-started))
        if remaining <= 0:
            raise RuntimeError('Evaluation compute budget exhausted')
        with (work/'command.log').open('a') as log:
            subprocess.run(command, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=remaining)
        sync()
        elapsed = time.perf_counter()-began
        p = json.loads(output.read_text())
        assert p['platform'] == 'CUDA' and p['properties'] == {'Precision':'single','DeterministicForces':'true'}
        assert p['simulated_ns'] == 0.8 and len(p['replicas']) == 8
        wall = finite(p['total_wall_s'],True)
        metrics = {'total_wall_s':wall, 'aggregate_ns_per_day':0.8/wall*86400, 'simulated_ns':0.8}
        finals=[]; means=[]
        for i,r in enumerate(p['replicas']):
            assert (r['replica'],r['seed'],r['steps']) == (i,seed0+i,25000)
            finite(r['wall_s'], True)
            for key in ('final_potential_kj_mol','mean_potential_kj_mol'):
                metrics['replica_'+str(i)+'_'+key] = finite(r[key])
            finals.append(r['final_potential_kj_mol']); means.append(r['mean_potential_kj_mol'])
        metrics['final_potential_kj_mol'] = sum(finals)/8
        metrics['mean_potential_kj_mol'] = sum(means)/8
        metrics['reported_wall_s'] = elapsed
        records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
sync()
wall_s = time.perf_counter()-started
if limit is not None and wall_s > limit:
    raise RuntimeError('Curve GPU-second budget exceeded')
result.write_text(json.dumps({'records':records,'timing_scope':scope,'gpu_count':1,
                              'wall_s':wall_s,'compute_budget':budget},allow_nan=False,indent=2)+'\n')
EVALUATE
