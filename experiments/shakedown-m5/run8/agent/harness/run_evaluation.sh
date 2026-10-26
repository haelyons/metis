#!/usr/bin/env bash
set -Eeuo pipefail
if [[ ${MC_EVALUATION_DEADLINE:-0} != 1 ]]; then
  exec timeout --signal=TERM --kill-after=10s 1150s env MC_EVALUATION_DEADLINE=1 bash "$0" "$@"
fi
: "${EVAL_PROTOCOL:?EVAL_PROTOCOL must point to the sealed JSON}"
: "${EVAL_OUT:?EVAL_OUT must be an absolute output path}"
: "${BASELINE_DIR:?BASELINE_DIR must be supplied}"
mkdir -p "$EVAL_OUT"
exec > >(tee "$EVAL_OUT/driver.log") 2>&1
CUDA_ROOT=
for root in /usr/local/cuda /usr/lib/cuda /usr; do
  if ls "$root/include/cuda_runtime.h" "$root/lib64/libcudart.so" "$root/bin/nvcc"; then CUDA_ROOT="$root"; break; fi
done
[[ -n $CUDA_ROOT ]] || { echo 'No complete probed CUDA toolkit.' >&2; exit 1; }
export PATH="$CUDA_ROOT/bin:$PATH"
export MC_EVAL_CUDA_ROOT="$CUDA_ROOT"
export CUDA_VISIBLE_DEVICES=0
python3 - <<'PY'
import ctypes, json, math, os, re, subprocess, time
from pathlib import Path
started=time.monotonic()
out=Path(os.environ['EVAL_OUT'])
protocol=json.loads(Path(os.environ['EVAL_PROTOCOL']).read_text())
mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in ('equivalence','warmup','performance','curve'): raise SystemExit('Unsupported EVAL_MODE: '+mode)
if 'timing_scope' not in protocol: raise SystemExit('Seal lacks timing_scope')
scope=protocol['timing_scope']
gpu_count=protocol.get('gpu_count',1)
if gpu_count!=1: raise SystemExit('Published protocol requires one GPU')
def specification(name,fallback):
    value=os.environ.get(name,'')
    if not value: return fallback
    try: return json.loads(value)
    except json.JSONDecodeError: return json.loads(Path(value).read_text())
inputs=specification('EVAL_INPUTS',protocol.get('inputs',[{'input_id':'representative'}]))
seeds=specification('EVAL_SEEDS',protocol.get('seeds',[None]))
if isinstance(inputs,dict):
    if 'inputs' in inputs: inputs=inputs['inputs']
    elif any(k in inputs for k in ('input_id','id','name')): inputs=[inputs]
    else: inputs=[dict(v,input_id=k) if isinstance(v,dict) else {'input_id':k,'value':v} for k,v in inputs.items()]
if isinstance(seeds,dict): seeds=seeds.get('seeds',seeds.get('values'))
if seeds is None: seeds=[None]
if not isinstance(seeds,list): seeds=[seeds]
if not isinstance(inputs,list) or not inputs or not seeds: raise SystemExit('Invalid input/seed specifications')
# This published executable has a fixed generator, no data-file or seed CLI.
# Reject incompatible specifications rather than silently reusing other inputs.
normalized=[]
for item in inputs:
    if isinstance(item,str): item={'input_id':item}
    if not isinstance(item,dict): raise SystemExit('Invalid sealed input')
    ident=item.get('input_id',item.get('id',item.get('name')))
    if ident is None: raise SystemExit('Sealed input lacks ID')
    config=item.get('parameters',item.get('configuration',item))
    expected={'options':1048576,'nOptions':1048576,'paths_per_option':262144,'PATH_N':262144,'gpu_count':1,'host_seed':123,'method':'streamed','scaling':'strong','precision':'float','S_range':[5,50],'X_range':[10,25],'T_range':[1,5],'R':0.06,'V':0.1}
    for key,value in expected.items():
        if key in config and config[key]!=value: raise SystemExit('Unsupported sealed input configuration: '+key)
    normalized.append((ident,item))
normalized.sort(key=lambda pair:str(pair[0]))
seed_values=[]
for seed in seeds:
    if isinstance(seed,dict): seed=seed.get('seed',seed.get('value'))
    if seed not in (None,123): raise SystemExit('Pinned generator supports only fixed seed 123 or deterministic null')
    seed_values.append(seed)
seed_values.sort(key=lambda x:(x is not None,x if x is not None else 0))
budget_value=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=None
if mode=='curve':
    if not budget_value: raise SystemExit('Curve mode requires EVAL_COMPUTE_BUDGET')
    budget=float(budget_value)
    if not math.isfinite(budget) or budget<=0: raise SystemExit('Invalid GPU-second budget')
# The process completes before synchronization. The explicit synchronization
# below also surfaces CUDA errors and is included in the reported wall time.
cuda=ctypes.CDLL(os.environ['MC_EVAL_CUDA_ROOT']+'/lib64/libcudart.so')
for name in ['cudaSetDevice','cudaDeviceSynchronize']:
    getattr(cuda,name).restype=ctypes.c_int
if cuda.cudaSetDevice(0)!=0 or cuda.cudaDeviceSynchronize()!=0: raise SystemExit('CUDA initialization/synchronization failed')
env=os.environ.copy(); env['CUDA_VISIBLE_DEVICES']='0'
# Set visibility before loading CUDA in this process as well (exported by shell).
binary=Path(os.environ['BASELINE_DIR'])/'build-mc/MonteCarloMultiGPU'
records=[]; total_wall=0.0; used_budget=0.0
for seed in seed_values:
    for ident,item in normalized:
        index=len(records)
        remaining=1080-(time.monotonic()-started)
        if budget is not None: remaining=min(remaining,budget-used_budget-0.1)
        if remaining<=0: raise SystemExit('Evaluation budget exhausted')
        log=out/f'run-{index:04d}.stdout'
        t0=time.monotonic()
        try:
            with log.open('w') as handle:
                result=subprocess.run([str(binary),'--method=streamed','--scaling=strong'],env=env,stdout=handle,stderr=subprocess.STDOUT,timeout=remaining)
        except subprocess.TimeoutExpired:
            raise SystemExit('Published fixed workload exceeded evaluation budget; no measurements emitted')
        if cuda.cudaDeviceSynchronize()!=0: raise SystemExit('CUDA synchronization failed')
        wall=time.monotonic()-t0
        total_wall+=wall; used_budget+=wall*gpu_count
        (out/f'run-{index:04d}.exit_status').write_text(str(result.returncode)+'\n')
        if budget is not None and used_budget>budget: raise SystemExit('GPU-second budget exceeded')
        text=log.read_text()
        for label,expected in [('Number of GPUs',1),('Total number of options',1048576),('Number of paths',262144)]:
            m=re.search(re.escape(label)+r'\s*[:=]\s*(\d+)',text,re.I)
            if not m or int(m[1])!=expected: raise SystemExit('Invalid printed configuration: '+label)
        def number(label):
            m=re.search(re.escape(label)+r'\s*[:=]\s*([-+0-9.eE]+)',text,re.I)
            if not m or not math.isfinite(float(m[1])): raise SystemExit('Missing/invalid metric: '+label)
            return float(m[1])
        reserve=number('Average reserve'); l1=number('L1 norm')
        ms=number('Total time (ms.)'); throughput=number('Options per sec.')
        verdict=re.search(r'Test (passed|failed!)',text)
        if not verdict or result.returncode!=(0 if verdict[1]=='passed' else 1): raise SystemExit('Invalid process exit status/verdict')
        passed=int(verdict[1]=='passed')
        metrics={'mc-bs-reserve':reserve,'sample-pass':passed,'average_reserve':reserve,'l1_norm':l1,'total_time_ms':ms,'options_per_sec':throughput,'wall_s':wall}
        def canonical(s): return re.sub('[^a-z0-9]','',s.lower())
        aliases={}
        for keys,value in [(['mc-bs-reserve','average_reserve','reserve','Average reserve'],reserve),(['sample-pass','test_passed','pass','verdict'],passed),(['l1','l1_norm','L1 norm'],l1),(['total_time_ms','time_ms','runtime_ms','Total time (ms.)','streamed_total_time_ms'],ms),(['options_per_sec','options_per_second','throughput','Options per sec.'],throughput),(['wall_s','reported_wall_s','elapsed_s'],wall)]:
            for key in keys: aliases[canonical(key)]=value
        requested=protocol.get('metrics',[])
        if isinstance(requested,dict): requested=list(requested)
        if isinstance(requested,str): requested=[requested]
        for spec in requested:
            name=spec if isinstance(spec,str) else spec.get('name',spec.get('metric_name',spec.get('id')))
            if name:
                value=aliases.get(canonical(name))
                if value is None: raise SystemExit('Unsupported sealed metric: '+name)
                metrics[name]=value
        records.append({'input_id':ident,'seed':seed,'metrics':metrics})
report={'records':records,'timing_scope':scope,'gpu_count':1,'wall_s':total_wall,'compute_budget':budget}
(out/'evaluation.json').write_text(json.dumps(report,allow_nan=False)+'\n')
PY
