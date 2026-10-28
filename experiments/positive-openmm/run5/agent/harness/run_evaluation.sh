#!/usr/bin/env bash
set -euo pipefail
: "${EVAL_OUT:?EVAL_OUT required}" "${EVAL_PROTOCOL:?EVAL_PROTOCOL required}"
mkdir -p "$EVAL_OUT"
exec > >(tee -a "$EVAL_OUT/adapter.log") 2>&1
source baseline-published/cuda.env
ls -l "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY/libcudart.so"
export PATH="$(dirname "$CUDA_COMPILER"):$PATH"
export LD_LIBRARY_PATH="$CUDA_LIBRARY${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CPATH="$CUDA_INCLUDE${CPATH:+:$CPATH}"
export LIBRARY_PATH="$CUDA_LIBRARY${LIBRARY_PATH:+:$LIBRARY_PATH}"
export CMAKE_CUDA_COMPILER="$CUDA_COMPILER"
export OPENMM_CUDA_COMPILER="$CUDA_COMPILER"
export CUDA_VISIBLE_DEVICES=0
export PYTHONDONTWRITEBYTECODE=1
# Absolute paths are allowed in the evaluation adapter; measured command remains relocatable.
export PYTHONPATH="$PWD/baseline-published/site${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<'PY'
import ctypes, json, math, os, pathlib, signal, subprocess, sys, time
root=pathlib.Path.cwd()
base=pathlib.Path(os.environ.get('BASELINE_DIR',root/'baseline-published')).resolve()
out=pathlib.Path(os.environ['EVAL_OUT'])
protocol=json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
mode=os.environ.get('EVAL_MODE','equivalence')
assert mode in ('equivalence','warmup','performance','curve'), 'Unsupported evaluation mode'
scope=protocol.get('timing_scope')
assert scope is not None, 'Seal missing timing_scope'
inputs=json.loads(os.environ.get('EVAL_INPUTS') or json.dumps(protocol.get('inputs',[])))
seeds=json.loads(os.environ.get('EVAL_SEEDS') or json.dumps(protocol.get('seeds',[])))
# Accept explicit lists and named input maps, preserving seal order.
if isinstance(inputs,dict):
    if 'inputs' in inputs: inputs=inputs['inputs']
    elif 'input_ids' in inputs: inputs=inputs['input_ids']
    else: inputs=[dict(v,input_id=k) if isinstance(v,dict) else {'input_id':k,'path':v} for k,v in inputs.items()]
assert isinstance(inputs,list) and inputs, 'No sealed inputs supplied'
if isinstance(seeds,dict):
    if seeds.get('deterministic') is True: seeds=[None]
    else: seeds=seeds.get('seeds',seeds.get('values',seeds.get('seed_values')))
if seeds is None: seeds=[None]
assert isinstance(seeds,list) and seeds, 'No sealed seeds supplied'
assert all(s is None or (isinstance(s,int) and not isinstance(s,bool)) for s in seeds), 'Invalid sealed seeds'
budget=None
if mode=='curve':
    raw=json.loads(os.environ['EVAL_COMPUTE_BUDGET'])
    if isinstance(raw,dict):
        raw=raw.get('gpu_seconds',raw.get('gpu_s',raw.get('compute_budget')))
    budget=float(raw)
    assert math.isfinite(budget) and budget>0, 'Invalid GPU-second budget'
import openmm
assert openmm.__version__=='8.2.0'
cuda=ctypes.CDLL('libcuda.so.1')
assert cuda.cuInit(0)==0
count=ctypes.c_int()
assert cuda.cuDeviceGetCount(ctypes.byref(count))==0 and count.value==1
# Each subprocess destroys all OpenMM contexts before exit. Also explicitly
# synchronize the visible device before stopping any adapter wall timer.
ctx=ctypes.c_void_p()
assert cuda.cuDevicePrimaryCtxRetain(ctypes.byref(ctx),0)==0
assert cuda.cuCtxSetCurrent(ctx)==0
def sync():
    assert cuda.cuCtxSynchronize()==0, 'GPU synchronization failed'
sync()
started=time.perf_counter()
records=[]
try:
    for seed in seeds:
        for index,item in enumerate(inputs):
            if isinstance(item,str): item={'input_id':item}
            assert isinstance(item,dict)
            iid=item.get('input_id',item.get('id',item.get('name')))
            assert iid is not None, 'Input missing ID'
            work=pathlib.Path(__import__('tempfile').mkdtemp(prefix=f'case-{len(records):04d}-',dir=out))
            supplied=item.get('pdb',item.get('path',item.get('file')))
            if supplied:
                candidate=pathlib.Path(supplied)
                if not candidate.is_absolute(): candidate=root/candidate
                if candidate.is_dir(): candidate=candidate/'5dfr_solv-cube_equil.pdb'
            else: candidate=root/'data/5dfr_solv-cube_equil.pdb'
            assert candidate.is_file(), f'Missing sealed PDB: {candidate}'
            (work/'5dfr_solv-cube_equil.pdb').symlink_to(candidate.resolve())
            for name in ('amber99sb.xml','tip3p.xml'):
                (work/name).symlink_to((root/'data'/name).resolve())
            seed0=1000 if seed is None else seed
            command=[sys.executable,str(base/'dhfr_ensemble.py'),'--replicas','8','--steps','25000','--seed0',str(seed0)]
            (work/'configuration.json').write_text(json.dumps({'command':command,'CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES'],'gpu_count':count.value,'input_id':iid,'seed':seed},indent=2))
            remaining=1100-(time.perf_counter()-started)
            if budget is not None: remaining=min(remaining,budget-(time.perf_counter()-started))
            assert remaining>0, 'Evaluation budget exhausted'
            with (work/'command.log').open('w') as log:
                proc=subprocess.Popen(command,cwd=work,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                try: code=proc.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGTERM)
                    try: proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid,signal.SIGKILL)
                        proc.wait()
                    sync()
                    raise RuntimeError('Published workload exceeded evaluation budget')
            assert code==0, f'Published workload failed: {work}/command.log'
            sync()
            d=json.loads((work/'ensemble.json').read_text())
            assert d['platform']=='CUDA' and d['properties']=={'Precision':'single','DeterministicForces':'true'}
            assert len(d['replicas'])==8 and math.isclose(d['simulated_ns'],0.8)
            wall=d['total_wall_s']
            assert isinstance(wall,(int,float)) and math.isfinite(wall) and wall>0
            metrics={'total_wall_s':wall,'aggregate_ns_per_day':d['simulated_ns']/wall*86400,'simulated_ns':d['simulated_ns']}
            for i,r in enumerate(d['replicas']):
                assert (r['replica'],r['seed'],r['steps'])==(i,seed0+i,25000)
                for k in ('mean_potential_kj_mol','final_potential_kj_mol','wall_s'):
                    value=r[k]
                    assert isinstance(value,(int,float)) and math.isfinite(value), 'Invalid scientific output'
                    metrics[f'replica_{i}_{k}']=value
            metrics['mean_potential_kj_mol']=sum(r['mean_potential_kj_mol'] for r in d['replicas'])/8
            metrics['final_potential_kj_mol']=sum(r['final_potential_kj_mol'] for r in d['replicas'])/8
            records.append({'input_id':iid,'seed':seed,'metrics':metrics})
    sync()
    elapsed=time.perf_counter()-started
    assert budget is None or elapsed<=budget, 'GPU-second budget exceeded'
    result={'records':records,'timing_scope':scope,'gpu_count':1,'wall_s':elapsed,'compute_budget':budget}
    target=out/'evaluation.json'
    if target.exists():
        import shutil
        shutil.copy2(target,out/f'evaluation.previous.{time.time_ns()}.json')
    temp=out/'evaluation.json.tmp'
    temp.write_text(json.dumps(result,allow_nan=False,indent=2)+'\n')
    temp.replace(target)
finally:
    sync()
    cuda.cuDevicePrimaryCtxRelease(0)
PY
