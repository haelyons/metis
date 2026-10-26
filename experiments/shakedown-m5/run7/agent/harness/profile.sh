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

out=ROOT/'out/profile'; out.mkdir(parents=True,exist_ok=True)
trace=out/'cuda-events.txt'
if trace.exists(): trace.unlink()
metrics,start,finish=run(BASE/'build-mc/MonteCarloMultiGPU',1048576,out/'baseline.log',extra={
    'LD_PRELOAD':str(BASE/'profile-tools/trace.so'), 'HARNESS_CUDA_TRACE':str(trace)},telemetry=out)
total=finish-start
if not math.isfinite(total) or total<=0: raise RuntimeError('Invalid elapsed time')
dump(out/'total_wall_s.json',{'total_wall_s':total})
dump(out/'measured.json',metrics)
if not trace.exists(): raise RuntimeError('No CUDA event output; runtime interposition unavailable')
intervals=[]
for line in trace.read_text().splitlines():
    kind,a,b,gpu=line.split(); a,b,gpu=map(float,(a,b,gpu))
    if not all(map(math.isfinite,(a,b,gpu))) or b<a or gpu<0: raise RuntimeError('Invalid CUDA event output')
    if a<start-.05 or b>finish+.05: raise RuntimeError('CUDA timestamps outside measured run')
    intervals.append((max(start,a),min(finish,b),kind,gpu))
if not intervals: raise RuntimeError('Missing measured CUDA stages')
# Attribute each critical-path interval once. Overlapping GPU work is assigned
# to the first active operation, rather than adding overlapping durations.
points=sorted(set([start,finish]+[x for a,b,_,_ in intervals for x in (a,b)]))
stages=[]
for a,b in zip(points,points[1:]):
    if b<=a: continue
    active=[x for x in intervals if x[0]<=a and x[1]>=b]
    if active:
        item=active[0]; label=item[2]; kind='compute' if label=='compute' else 'transfer'
        gpu=b-a  # CUDA event elapsed seconds over this non-overlapping interval.
    else:
        label='host work between GPU operations'; kind='other'; gpu=None
    stages.append({'stage':f'{label} {len(stages)+1}','kind':kind,'wall_s':b-a,'gpu_s':gpu})
# Never disguise a dominant kernel as multiple fabricated stages. A device
# whose output cannot meet the requested stage protocol fails explicitly.
if len(stages)<3 or any(x['wall_s']>=.98*total for x in stages):
    dump(out/'stages_observed.json',stages)
    raise RuntimeError('Observed stages cannot satisfy the three-stage/no-process-wrapper profile protocol')
if sum(x['wall_s'] for x in stages)/total<.9: raise RuntimeError('Insufficient measured stage coverage')
dump(out/'stages.json',stages)

PYTHON
