#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p out/profile
exec > >(tee -a out/profile/driver.log) 2>&1
trap 'echo "profile failed at line $LINENO" >&2' ERR
# Preparation is outside the one measured profile run.
if [[ ! -s out/anchors/final-run.json ]]; then
  bash harness/run_anchors.sh
fi
python3 - <<'PY'
import collections,heapq,json,math,os,pathlib,re,subprocess,threading,time
root=pathlib.Path.cwd()
out=root/'out/profile'
scale=json.loads((root/'data/scale.json').read_text())
anchor=json.loads((root/'out/anchors/final-run.json').read_text())
if scale!=anchor['configuration']:
    raise SystemExit('Scale differs from completed representative anchor run; rerun anchors')
collector=root/'data/profile-cupti.so'
if not collector.is_file(): raise SystemExit('CUPTI collector missing; run setup first')
# Retain previous raw runs and logs on retries.
run_dir=out/('raw-'+str(time.time_ns()))
run_dir.mkdir()
stop=threading.Event()
samples=[]
telemetry_errors=[]
origin=time.monotonic()
def telemetry():
    with (run_dir/'nvidia-smi.tsv').open('w') as raw:
        while not stop.is_set():
            try:
                q=subprocess.run(['nvidia-smi','-i','0','--query-gpu=utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
                t=time.monotonic()-origin
                raw.write(f'{t:.9f}\t{q.returncode}\t{q.stdout.strip()}\t{q.stderr.strip()}\n')
                raw.flush()
                if q.returncode: raise RuntimeError('nvidia-smi failed')
                util=float(q.stdout.strip())
                if not math.isfinite(util) or not 0<=util<=100: raise ValueError('invalid utilisation')
                samples.append({'t':t,'util':util})
            except Exception as e:
                telemetry_errors.append(str(e))
            stop.wait(.2)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',HARNESS_CUPTI_LOG=str(run_dir/'activities.tsv'))
env['LD_PRELOAD']=str(collector)+((':'+env['LD_PRELOAD']) if env.get('LD_PRELOAD') else '')
thread=threading.Thread(target=telemetry)
thread.start()
try:
    with (run_dir/'baseline.log').open('w') as log:
        proc=subprocess.run([str(root/'baseline-published/build-mc/MonteCarloMultiGPU'),'--method=streamed','--scaling=strong'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=3600)
finally:
    stop.set()
    thread.join(timeout=12)
if thread.is_alive(): raise RuntimeError('GPU sampler did not terminate')
(run_dir/'exit-status.json').write_text(json.dumps({'exit_status':proc.returncode}))
(out/'gpu_util.json').write_text(json.dumps(samples,allow_nan=False,indent=2)+'\n')
if proc.returncode: raise RuntimeError(f'Profile baseline exited {proc.returncode}; see {run_dir}/baseline.log')
if not samples: raise RuntimeError('No valid GPU utilisation samples: '+str(telemetry_errors))
text=(run_dir/'baseline.log').read_text()
print(text,flush=True)
num=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
def scalar(label):
    m=re.search(label+r'\s*[:=]\s*('+num+r')',text,re.I)
    if not m: raise RuntimeError('Missing or invalid baseline output: '+label)
    x=float(m.group(1))
    if not math.isfinite(x): raise RuntimeError('Nonfinite baseline output')
    return x
for key,label in {
    'gpu_count':r'(?:Number of GPUs|GPU_N|GPUs?\s*(?:count)?)',
    'nOptions':r'(?:Number of options|Option count|Options? count|OPT_N)',
    'PATH_N':r'(?:Number of paths|Path count|Paths? count|PATH_N)'
}.items():
    if scalar(label)!=scale[key]: raise RuntimeError('Invalid runtime configuration: '+key)
metrics={'elapsed_ms':scalar(r'Total time\s*\(ms\.\)'),
         'reserve':scalar('Average reserve'),'l1':scalar('L1 norm')}
if metrics['elapsed_ms']<=0 or metrics['reserve']<0 or metrics['l1']<0:
    raise RuntimeError('Invalid baseline numeric output')
if not re.search(r'Test (passed|failed!)',text): raise RuntimeError('Missing sample verdict')
(run_dir/'output-metrics.json').write_text(json.dumps(metrics,allow_nan=False,indent=2)+'\n')
# CUPTI timestamps share one nanosecond clock across host/runtime and GPU
# activities. Build a disjoint critical-path partition. GPU work has priority
# over overlapping runtime waits; transfers have priority over host API calls.
# Gaps between recorded CUDA calls are measured host work, not GPU time.
records=[]
bounds=[]
with (run_dir/'activities.tsv').open() as f:
    for line in f:
        fields=line.rstrip('\n').split('\t')
        if len(fields)!=4: raise RuntimeError('Malformed CUPTI record')
        kind,name,a,b=fields
        a,b=int(a),int(b)
        if a<=0 or b<a: raise RuntimeError('Invalid CUPTI interval')
        if kind=='bounds': bounds.append((a,b))
        elif kind in ('compute','transfer','other'):
            if b>a: records.append((kind,name,a,b))
        else: raise RuntimeError('Unknown CUPTI activity kind')
if len(bounds)!=1: raise RuntimeError('Missing measured-run CUPTI bounds')
start,end=bounds[0]
if end<=start: raise RuntimeError('Invalid measured run duration')
total=(end-start)/1e9
if not math.isfinite(total) or total<=0: raise RuntimeError('Invalid total wall time')
if not any(x[0]=='compute' for x in records): raise RuntimeError('Missing GPU kernel measurements')
if not any(x[0]=='transfer' for x in records): raise RuntimeError('Missing GPU transfer measurements')
events=collections.defaultdict(list)
active=set()
priority={'compute':0,'transfer':1,'other':2}
heap=[]
for i,(kind,name,a,b) in enumerate(records):
    a,b=max(a,start),min(b,end)
    if b<=a: continue
    events[a].append((1,i))
    events[b].append((-1,i))
points=sorted(set(events)|{start,end})
segments=[]
for pos,nxt in zip(points,points[1:]):
    for direction,i in events[pos]:
        if direction==1:
            active.add(i)
            heapq.heappush(heap,(priority[records[i][0]],i))
        else: active.discard(i)
    while heap and heap[0][1] not in active: heapq.heappop(heap)
    if heap:
        i=heap[0][1]
        kind,name,_,_=records[i]
        # Retain each separate measured activity, not an aggregate wrapper.
        label=(kind,name,i)
    else:
        label=('other','host work between CUDA activities',-1)
    if segments and segments[-1][0]==label and segments[-1][2]==pos:
        segments[-1]=(label,segments[-1][1],nxt)
    else: segments.append((label,pos,nxt))
stages=[]
for (kind,name,i),a,b in segments:
    sec=(b-a)/1e9
    if sec<=0: continue
    stages.append({'stage':f'{name} [{len(stages)+1}]','kind':kind,'wall_s':sec,'gpu_s':sec if kind in ('compute','transfer') else None})
if len(stages)<3: raise RuntimeError('Fewer than three measured internal stages')
if any(abs(s['wall_s']-total)<=.02*total for s in stages):
    raise RuntimeError('One measured interval occupies >=98% of run; cannot emit valid three-stage profile under wrapper exclusion rule')
covered=sum(s['wall_s'] for s in stages)
if min(1,covered/total)<.9: raise RuntimeError('Insufficient measured critical-path coverage')
for s in stages:
    if not math.isfinite(s['wall_s']) or s['wall_s']<0: raise RuntimeError('Invalid stage wall time')
    if s['gpu_s'] is not None and (not math.isfinite(s['gpu_s']) or s['gpu_s']<0): raise RuntimeError('Invalid GPU time')
(out/'stages.json').write_text(json.dumps(stages,allow_nan=False,indent=2)+'\n')
(out/'total_wall_s.json').write_text(json.dumps({'total_wall_s':total},allow_nan=False,indent=2)+'\n')
(out/'configuration.json').write_text(json.dumps(scale,allow_nan=False,indent=2)+'\n')
(out/'raw-run.json').write_text(json.dumps({'directory':str(run_dir),'clock':'CUPTI unified timestamp nanoseconds','timed_fraction':min(1,covered/total),'telemetry_errors':telemetry_errors},allow_nan=False,indent=2)+'\n')
print(f'Profile stages: {len(stages)}, total wall seconds: {total:.6f}, timed fraction: {min(1,covered/total):.6f}')
PY
