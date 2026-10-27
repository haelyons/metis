#!/usr/bin/env bash
set -euo pipefail
ROOT=$(pwd -P)
source "$ROOT/data/cuda-env.sh"
ls -l "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY"
export CUDA_VISIBLE_DEVICES=0
export EVAL_OUT=${EVAL_OUT:?EVAL_OUT must be supplied}
mkdir -p "$EVAL_OUT/logs" "$ROOT/out"
python3 - "$ROOT" <<'PY'
import ctypes,json,math,os,pathlib,re,signal,subprocess,sys,time
root=pathlib.Path(sys.argv[1])
out=pathlib.Path(os.environ['EVAL_OUT'])
protocol=json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in ('equivalence','warmup','performance','curve'):
    raise ValueError('Unknown evaluation mode: '+mode)
if 'timing_scope' not in protocol:
    raise ValueError('Sealed protocol lacks timing_scope')

def specification(name,default):
    raw=os.environ.get(name,'')
    return json.loads(raw) if raw else default

inputs=specification('EVAL_INPUTS',protocol.get('inputs',[{'id':'representative'}]))
if isinstance(inputs,dict):
    if 'inputs' in inputs: inputs=inputs['inputs']
    elif 'cases' in inputs: inputs=inputs['cases']
    elif 'ids' in inputs: inputs=inputs['ids']
    elif 'input_id' in inputs or 'id' in inputs: inputs=[inputs]
    else: inputs=[dict(v,input_id=k) if isinstance(v,dict) else {'input_id':k} for k,v in inputs.items()]
if not isinstance(inputs,list) or not inputs:
    raise ValueError('Sealed inputs must contain at least one input')
# This published protocol has a fixed internal host seed and no seed CLI.
seeds=specification('EVAL_SEEDS',protocol.get('seeds',[None]))
if isinstance(seeds,dict):
    seeds=seeds.get('seeds',seeds.get('values',[None]))
if seeds is None: seeds=[None]
if not isinstance(seeds,list) or not seeds: raise ValueError('Invalid seed specification')
for seed in seeds:
    if seed not in (None,123): raise ValueError('Published generator only supports fixed seed 123')
# All records use null: randomness is fixed by the published executable.
seeds=[None for _ in seeds]
raw_budget=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=None
if mode=='curve':
    if not raw_budget: raise ValueError('Curve requires GPU-second budget')
    budget=json.loads(raw_budget)
    if isinstance(budget,dict):
        limit=budget.get('gpu_seconds',budget.get('gpu_s',budget.get('value')))
    else: limit=budget
    limit=float(limit)
    if not math.isfinite(limit) or limit<=0: raise ValueError('Invalid GPU-second budget')
else: limit=1100.0
limit=min(limit,1100.0)
runtime=ctypes.CDLL(os.environ['CUDA_LIBRARY'])
for fn in ('cudaSetDevice','cudaDeviceSynchronize'):
    getattr(runtime,fn).restype=ctypes.c_int

def sync():
    for name,args in [('cudaSetDevice',(0,)),('cudaDeviceSynchronize',())]:
        code=getattr(runtime,name)(*args)
        if code: raise RuntimeError(name+' failed: '+str(code))

def parse(text):
    def number(label):
        matches=re.findall(label+r'\s*:\s*([-+\d.eE]+)',text,re.I)
        if len(matches)!=1: raise ValueError('Missing/ambiguous output: '+label)
        value=float(matches[0])
        if not math.isfinite(value): raise ValueError('Nonfinite '+label)
        return value
    for label,expected in [('GPU count',1),('Option count',1048576),('Path count',262144)]:
        if number(label)!=expected: raise ValueError('Printed configuration mismatch: '+label)
    verdict=re.findall(r'Test (passed|failed!)',text)
    if len(verdict)!=1: raise ValueError('Missing/ambiguous verdict')
    return {'total_time_ms':number(r'Total time \(ms\.\)'), 'average_reserve':number('Average reserve'), 'l1_norm':number('L1 norm'), 'sample_pass':int(verdict[0]=='passed')}

records=[]
sync()
start=time.monotonic()
for seed in seeds:
    for index,item in enumerate(inputs):
        if isinstance(item,str): input_id=item
        elif isinstance(item,dict):
            input_id=item.get('input_id',item.get('id',item.get('name')))
            config=item.get('parameters',item.get('configuration',item))
            for key,value in [('options',1048576),('paths_per_option',262144),('gpus',1),('host_seed',123)]:
                if key in config and config[key]!=value:
                    raise ValueError('Sealed input conflicts with published fixed '+key)
        else: raise ValueError('Invalid sealed input')
        if input_id is None: raise ValueError('Sealed input lacks ID')
        remaining=limit-(time.monotonic()-start)
        if remaining<=0: raise TimeoutError('Evaluation GPU-second/stage budget exhausted')
        log=out/'logs'/('run-'+str(len(records))+'-'+str(time.time_ns())+'.log')
        with log.open('w') as stream:
            process=subprocess.Popen(['bash','harness/run_command.sh'],cwd=root,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                returncode=process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL)
                process.wait()
                sync()
                raise
        sync()
        if returncode: raise RuntimeError('Published binary failed; log: '+str(log))
        metrics=parse(log.read_text())
        # Preserve emitted quantities and common published names for sealed metrics.
        aliases={'Total time (ms.)':'total_time_ms','Average reserve':'average_reserve','L1 norm':'l1_norm','sample-pass':'sample_pass','mc-bs-reserve':'average_reserve','runtime_ms':'total_time_ms','time_ms':'total_time_ms'}
        requested=protocol.get('metrics',[])
        if isinstance(requested,dict): requested=list(requested)
        for metric in requested:
            name=metric if isinstance(metric,str) else metric.get('name',metric.get('id'))
            if name in aliases: metrics[name]=metrics[aliases[name]]
        records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
sync()
wall=time.monotonic()-start
if wall>limit: raise TimeoutError('Evaluation GPU-second/stage budget exceeded')
result={'records':records,'timing_scope':protocol['timing_scope'],'gpu_count':1,'wall_s':wall,'compute_budget':budget}
tmp=out/('evaluation.'+str(os.getpid())+'.tmp')
tmp.write_text(json.dumps(result,allow_nan=False)+'\n')
tmp.replace(out/'evaluation.json')
PY
