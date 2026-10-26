#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PYTHON'

import os, sys, json, re, math, time, subprocess, pathlib, ctypes, threading
ROOT=pathlib.Path.cwd()
BASE=pathlib.Path(os.environ.get('BASELINE_DIR', ROOT/'baseline-published')).resolve()
def dump(path,value):
    path=pathlib.Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,allow_nan=False,indent=2)+'\n')
def number(text, pattern):
    m=re.search(pattern,text,re.I)
    if not m: raise RuntimeError('Missing output field: '+pattern)
    x=float(m.group(1))
    if not math.isfinite(x): raise RuntimeError('Nonfinite output')
    return x
def parse(text, options, code):
    for label,pattern,want in [
        ('GPU count',r'(?:number of GPUs|GPU count)\s*[:=]\s*(\d+)',1),
        ('option count',r'(?:number of options|option count)\s*[:=]\s*(\d+)',options),
        ('path count',r'(?:number of paths|paths per option|path count)\s*[:=]\s*(\d+)',262144)]:
        got=number(text,pattern)
        if got!=want: raise RuntimeError(f'Invalid {label}: {got}, expected {want}')
    reserve=number(text,r'Average reserve\s*[:=]\s*([-+\deE.]+)')
    l1=number(text,r'L1 norm\s*[:=]\s*([-+\deE.]+)')
    ms=number(text,r'Total time\s*\(ms\.?\)\s*[:=]\s*([-+\deE.]+)')
    verdict=re.findall(r'Test (passed|failed!?)',text,re.I)
    if not verdict or code not in (0,1): raise RuntimeError('Invalid final output or process status: '+str(code))
    if ms<=0 or l1<0 or reserve<0: raise RuntimeError('Invalid measured values')
    return {'mc-bs-reserve':reserve,'sample-pass':int(verdict[-1].lower()=='passed'),
            'average_reserve':reserve,'l1_norm':l1,'total_time_ms':ms,'wall_s':ms/1000,
            'exit_status':code}
def sync():
    # All invocations expose one GPU. Synchronize the parent context as well;
    # the child completes all events and destroys its context before exit.
    lib=ctypes.CDLL('libcudart.so.12')
    for name,args in [('cudaSetDevice',(0,)),('cudaDeviceSynchronize',())]:
        code=getattr(lib,name)(*args)
        if code: raise RuntimeError(f'{name} failed: {code}')
def run(binary,options,log,limit=1100,extra=None,telemetry=None):
    log=pathlib.Path(log); log.parent.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy(); env['CUDA_VISIBLE_DEVICES']='0'
    if extra: env.update(extra)
    stop=threading.Event(); samples=[]; errors=[]
    start=time.monotonic()
    def sample():
        raw=pathlib.Path(telemetry)/'nvidia-smi.jsonl'
        with raw.open('w') as f:
            while not stop.is_set():
                p=subprocess.run(['nvidia-smi','--id=0','--query-gpu=utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
                t=time.monotonic()-start
                f.write(json.dumps({'t':t,'stdout':p.stdout,'stderr':p.stderr,'returncode':p.returncode})+'\n'); f.flush()
                try:
                    u=float(p.stdout.strip())
                    if p.returncode or not math.isfinite(u) or not 0<=u<=100: raise ValueError()
                    samples.append({'t':t,'util':u})
                except ValueError: errors.append('Invalid nvidia-smi telemetry')
                stop.wait(.2)
    thread=None
    if telemetry:
        pathlib.Path(telemetry).mkdir(parents=True,exist_ok=True)
        thread=threading.Thread(target=sample); thread.start()
    try:
        with log.open('w') as f:
            p=subprocess.run([str(binary),'--method=streamed','--scaling=strong'],stdout=f,stderr=subprocess.STDOUT,env=env,timeout=limit)
        sync()
        finish=time.monotonic()
    finally:
        stop.set()
        if thread: thread.join(timeout=12)
    if telemetry:
        if errors or not samples: raise RuntimeError('Missing or invalid GPU utilisation output')
        dump(pathlib.Path(telemetry)/'gpu_util.json',samples)
    metrics=parse(log.read_text(),options,p.returncode)
    return metrics,start,finish

mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in ('equivalence','warmup','performance','curve'): raise RuntimeError('Unsupported EVAL_MODE: '+mode)
protocol=json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
scope=protocol['timing_scope']
def specification(env,key,default):
    text=os.environ.get(env,'')
    value=json.loads(text) if text else protocol.get(key,default)
    if isinstance(value,dict) and key in value: value=value[key]
    return value
inputs=specification('EVAL_INPUTS','inputs',None)
seeds=specification('EVAL_SEEDS','seeds',[None])
if isinstance(inputs,dict):
    if 'input_id' in inputs or 'id' in inputs: inputs=[inputs]
    else: inputs=[dict(v,input_id=k) if isinstance(v,dict) else {'input_id':k,'value':v} for k,v in inputs.items()]
if not isinstance(inputs,list) or not inputs: raise RuntimeError('Seal supplies no inputs')
if seeds is None: seeds=[None]
if isinstance(seeds,dict): seeds=seeds.get('values',seeds.get('seeds'))
if not isinstance(seeds,list) or not seeds: raise RuntimeError('Invalid sealed seeds')
# The published interface is deterministic: it has no seed argument. Record
# null, and reject any request that would require changing published RNGs.
if any(s not in (None,123) for s in seeds): raise RuntimeError('Published sample supports only fixed host seed 123')
if len(seeds)>1: raise RuntimeError('Published deterministic protocol cannot supply distinct seed runs')
seeds=[None]
budget_text=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=json.loads(budget_text) if budget_text else None
budget_s=None
if mode=='curve':
    if isinstance(budget,(int,float)): budget_s=float(budget)
    elif isinstance(budget,dict):
        for key in ('gpu_seconds','gpu_s','seconds','value'):
            if key in budget: budget_s=float(budget[key]); break
    if budget_s is None or not math.isfinite(budget_s) or budget_s<=0: raise RuntimeError('Curve requires positive GPU-second budget')
out=pathlib.Path(os.environ['EVAL_OUT']); out.mkdir(parents=True,exist_ok=True)
method=pathlib.Path(os.environ['METHOD_DIR']).resolve() if os.environ.get('METHOD_DIR') else None
requested=protocol.get('metrics',protocol.get('metric_names'))
if isinstance(requested,dict): requested=list(requested)
if isinstance(requested,list): requested=[m.get('name',m.get('metric_name',m.get('id'))) if isinstance(m,dict) else m for m in requested]
records=[]; start=time.monotonic(); deadline=start+1100
if budget_s is not None: deadline=min(deadline,start+budget_s) # one GPU: wall bound conservatively bounds GPU seconds
for seed in seeds:
    for index,item in enumerate(inputs):
        if isinstance(item,str): item={'input_id':item}
        if not isinstance(item,dict): raise RuntimeError('Invalid sealed input descriptor')
        input_id=item.get('input_id',item.get('id',item.get('name')))
        if input_id is None: raise RuntimeError('Sealed input lacks input_id')
        configuration=item.get('configuration',item.get('parameters',item.get('params',item)))
        options=int(configuration.get('options',configuration.get('nOptions',1048576)))
        if options not in (8192,1048576): raise RuntimeError('Sealed scale not supported by published builds')
        for key,want in [('paths_per_option',262144),('gpu_count',1),('method','streamed'),('scaling','strong'),('precision','float')]:
            if key in configuration and configuration[key]!=want: raise RuntimeError('Unsupported published configuration: '+key)
        build='build-anchor' if options==8192 else 'build-mc'
        binary=BASE/build/'MonteCarloMultiGPU'
        if method:
            candidates=[method/build/'MonteCarloMultiGPU',method/'MonteCarloMultiGPU']
            available=[p for p in candidates if p.is_file() and os.access(p,os.X_OK)]
            if available: binary=available[0]
        remaining=deadline-time.monotonic()
        if remaining<=0: raise RuntimeError('Evaluation compute/time budget exhausted')
        metrics,a,b=run(binary,options,out/f'run-{len(records):04d}.log',limit=remaining)
        aliases={'reserve':'average_reserve','sample_pass':'sample-pass','passed':'sample-pass','L1 norm':'l1_norm',
                 'L1_norm':'l1_norm','time_ms':'total_time_ms','Total time (ms.)':'total_time_ms',
                 'Average reserve':'average_reserve','runtime_s':'wall_s'}
        metrics['reported_wall_s']=b-a
        selected={}
        if requested:
            for name in requested:
                key=aliases.get(name,name)
                if key not in metrics: raise RuntimeError('Unsupported sealed metric: '+str(name))
                selected[name]=metrics[key]
        else: selected=metrics
        records.append({'input_id':input_id,'seed':seed,'metrics':selected})
sync()
wall=time.monotonic()-start
if budget_s is not None and wall>budget_s: raise RuntimeError('Curve GPU-second budget exceeded (conservative wall bound)')
dump(out/'evaluation.json',{'records':records,'timing_scope':scope,'gpu_count':1,'wall_s':wall,'compute_budget':budget})

PYTHON
