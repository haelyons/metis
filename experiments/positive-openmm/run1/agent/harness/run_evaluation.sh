#!/usr/bin/env bash
set -euo pipefail
: "${BASELINE_DIR:?BASELINE_DIR required}" "${EVAL_OUT:?EVAL_OUT required}" "${EVAL_PROTOCOL:?EVAL_PROTOCOL required}"
source "$BASELINE_DIR/cuda.env"
ls -l "$OPENMM_CUDA_COMPILER" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export CUDA_VISIBLE_DEVICES=0
export PYTHONNOUSERSITE=1
export PYTHONPATH="$BASELINE_DIR/python"
unset CUDA_MPS_ACTIVE_THREAD_PERCENTAGE CUDA_MPS_PIPE_DIRECTORY CUDA_MPS_LOG_DIRECTORY
mkdir -p "$EVAL_OUT"
python3 - <<'PY'
import json, math, os, pathlib, re, subprocess, time, uuid

def load(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return json.loads(pathlib.Path(value).read_text())

def number(x):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):
        raise ValueError('Missing or invalid finite numeric output')
    return x

seal = load(os.environ['EVAL_PROTOCOL'])
mode = os.environ.get('EVAL_MODE','equivalence')
if mode not in ('equivalence','warmup','performance','curve'):
    raise ValueError('Unsupported EVAL_MODE: '+mode)
scope = seal['timing_scope']
inputs = load(os.environ.get('EVAL_INPUTS'))
if inputs is None:
    inputs = seal.get('inputs',[{'input_id':'dhfr'}])
if isinstance(inputs,dict):
    inputs = inputs.get('inputs', inputs.get('input_ids', inputs))
if isinstance(inputs,dict):
    inputs = [dict(value, input_id=key) if isinstance(value,dict) else {'input_id':key,'path':value}
              for key,value in inputs.items()]
if not isinstance(inputs,list) or not inputs:
    raise ValueError('EVAL_INPUTS must specify a nonempty input list')
seeds = load(os.environ.get('EVAL_SEEDS'))
if seeds is None:
    seeds = seal.get('seeds',[1000])
if isinstance(seeds,dict):
    if seeds.get('deterministic') is True:
        seeds = [None]
    else:
        seeds = seeds.get('seeds',seeds.get('values'))
if seeds is None and seal.get('deterministic') is True:
    seeds = [None]
if not isinstance(seeds,list) or not seeds:
    raise ValueError('EVAL_SEEDS must specify a nonempty seed list')
if seal.get('deterministic') is True:
    seeds = [None]
base = pathlib.Path(os.environ['BASELINE_DIR']).resolve()
data = pathlib.Path('data').resolve()
out = pathlib.Path(os.environ['EVAL_OUT']).resolve()
runroot = out / ('runs-'+uuid.uuid4().hex)
runroot.mkdir(parents=True)
# Baseline accepts fixed-work seeds, not variable work or a different model.
budget_value = load(os.environ.get('EVAL_COMPUTE_BUDGET')) if mode == 'curve' else None
budget = None
if mode == 'curve':
    if isinstance(budget_value,(int,float)):
        budget = number(budget_value)
    elif isinstance(budget_value,dict):
        for key in ('gpu_seconds','gpu_s','compute_budget','value'):
            if key in budget_value:
                budget = number(budget_value[key]); break
    if budget is None or budget <= 0:
        raise ValueError('Curve requires a positive GPU-second compute budget')
records = []
start = time.perf_counter()
for seed_spec in seeds:
    seed = seed_spec.get('seed',seed_spec.get('value')) if isinstance(seed_spec,dict) else seed_spec
    if seed is not None and (isinstance(seed,bool) or not isinstance(seed,int)):
        raise ValueError('Seeds must be integers or null')
    seed0 = 1000 if seed is None else seed
    for input_spec in inputs:
        spec = {'input_id':input_spec} if isinstance(input_spec,str) else input_spec
        input_id = spec.get('input_id',spec.get('id',spec.get('name')))
        if not isinstance(input_id,str) or not input_id:
            raise ValueError('Input lacks input_id')
        for key, expected in [('replicas',8),('steps',25000),('steps_per_replica',25000),('gpu_count',1)]:
            if key in spec and spec[key] != expected:
                raise ValueError('Sealed input changes published configuration: '+key)
        wd = runroot / str(len(records))
        wd.mkdir()
        pdb = spec.get('pdb',spec.get('path',spec.get('file','5dfr_solv-cube_equil.pdb')))
        pdb = pathlib.Path(pdb)
        if not pdb.is_absolute():
            pdb = data / pdb
        if not pdb.is_file():
            raise ValueError('Missing sealed PDB input: '+str(pdb))
        (wd/'5dfr_solv-cube_equil.pdb').symlink_to(pdb)
        for name in ('amber99sb.xml','tip3p.xml'):
            (wd/name).symlink_to(data/name)
        env = os.environ.copy()
        env['CUDA_CACHE_PATH'] = str(out/'cuda-cache')
        env['TMPDIR'] = str(out/'tmp')
        pathlib.Path(env['CUDA_CACHE_PATH']).mkdir(exist_ok=True)
        pathlib.Path(env['TMPDIR']).mkdir(exist_ok=True)
        command = ['python3',str(base/'dhfr_ensemble.py'),'--replicas','8','--steps','25000','--seed0',str(seed0)]
        config = {'command':command,'cwd':str(wd),'gpu_count':1,'CUDA_VISIBLE_DEVICES':env['CUDA_VISIBLE_DEVICES'],
                  'replicas':8,'steps':25000,'seed0':seed0,'platform':'CUDA',
                  'properties':{'Precision':'single','DeterministicForces':'true'},
                  'OPENMM_CUDA_COMPILER':env['OPENMM_CUDA_COMPILER'],
                  'CUDA_INCLUDE_DIR':env['CUDA_INCLUDE_DIR'],'CUDA_LIBRARY_DIR':env['CUDA_LIBRARY_DIR']}
        (wd/'configuration.json').write_text(json.dumps(config,indent=2))
        remaining = 1150 - (time.perf_counter()-start)
        if budget is not None:
            # Exactly one GPU; charge launch, transfers, context creation and merge as well.
            remaining = min(remaining,budget-(time.perf_counter()-start))
        if remaining <= 0:
            raise RuntimeError('Evaluation compute/time budget exhausted')
        with (wd/'stdout.log').open('w') as log:
            log.write('configuration: '+json.dumps(config)+'\n'); log.flush()
            try:
                subprocess.run(command,cwd=wd,env=env,stdout=log,stderr=subprocess.STDOUT,
                               check=True,timeout=remaining)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError('Published fixed-work run exceeded compute/time budget') from exc
        # Driver synchronously reads final energy on CUDA for every replica, then
        # destroys every Context. Process exit completes all GPU work before this timer.
        d = json.loads((wd/'ensemble.json').read_text())
        if d['platform'] != config['platform'] or d['properties'] != config['properties']:
            raise ValueError('Invalid measured platform configuration')
        if len(d['replicas']) != 8 or not math.isclose(number(d['simulated_ns']),0.8):
            raise ValueError('Invalid measured ensemble scale')
        wall = number(d['total_wall_s'])
        if wall <= 0:
            raise ValueError('Invalid measured wall time')
        metrics = {'total_wall_s':wall,'aggregate_ns_per_day':number(d['simulated_ns']/wall*86400),
                   'aggregate_us_per_day':number(d['simulated_ns']/wall*86.4), 'simulated_ns':number(d['simulated_ns'])}
        printed = (wd/'stdout.log').read_text()
        for key,tolerance in [('total_wall_s',0.00051),('aggregate_ns_per_day',0.051)]:
            values = re.findall(r'^'+key+r':\s*(\S+)\s*$',printed,re.M)
            if len(values) != 1 or abs(number(float(values[0]))-metrics[key]) > tolerance:
                raise ValueError('Missing or invalid printed measurement: '+key)
        for i,r in enumerate(d['replicas']):
            if (r['replica'],r['seed'],r['steps']) != (i,seed0+i,25000):
                raise ValueError('Invalid measured replica configuration')
            for key in ('wall_s','final_potential_kj_mol','mean_potential_kj_mol'):
                metrics['replica_'+str(i)+'_'+key] = number(r[key])
        metrics['mean_potential_kj_mol'] = sum(r['mean_potential_kj_mol'] for r in d['replicas'])/8
        metrics['final_potential_kj_mol'] = sum(r['final_potential_kj_mol'] for r in d['replicas'])/8
        for value in metrics.values():
            number(value)
        records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
wall_s = time.perf_counter()-start
if budget is not None and wall_s > budget:
    raise RuntimeError('GPU-second compute budget exceeded')
result = {'records':records,'timing_scope':scope,'gpu_count':1,'wall_s':wall_s,'compute_budget':budget_value}
if (out/'evaluation.json').exists():
    (out/'evaluation.json').rename(out/('evaluation.'+uuid.uuid4().hex+'.json'))
(out/'evaluation.json').write_text(json.dumps(result,allow_nan=False,indent=2)+'\n')
PY
