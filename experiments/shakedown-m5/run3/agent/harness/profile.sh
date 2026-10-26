#!/usr/bin/env bash
set -euo pipefail
mkdir -p out/profile
exec > >(tee "out/profile/driver-$(date +%s%N).log") 2>&1
# Establish representative constants if anchors have not been run yet.
if [[ ! -f out/representative.json ]]; then
  bash harness/run_anchors.sh
fi
/usr/bin/python3 - <<'PY'
import json, math, os, re, shutil, subprocess, threading, time
from pathlib import Path
root=Path.cwd()
profile=root/'out/profile'
for name in ('stages.json','total_wall_s.json'):
    (profile/name).unlink(missing_ok=True)
state=json.loads((root/'out/representative.json').read_text())
raw=profile/str(time.time_ns())
raw.mkdir()
repo=root/'baseline-published'
with (raw/'build.log').open('wb') as log:
    subprocess.run(['/usr/bin/cmake','-S',str(repo/'Samples/5_Domain_Specific/MonteCarloMultiGPU'),
                    '-B',str(repo/'build-mc'),'-DCMAKE_BUILD_TYPE=Release',
                    '-DCMAKE_CUDA_COMPILER=/usr/bin/nvcc'],
                   stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run(['/usr/bin/cmake','--build',str(repo/'build-mc'),'--target',
                    'MonteCarloMultiGPU','--parallel'],
                   stdout=log,stderr=subprocess.STDOUT,check=True)
stop=threading.Event()
smi=shutil.which('nvidia-smi')

def sample():
    with (raw/'nvidia-smi.csv').open('w') as stream, (raw/'nvidia-smi-errors.log').open('w') as errors:
        if not smi:
            errors.write('nvidia-smi unavailable; GPU execution timings unavailable\n')
            return
        while not stop.is_set():
            try:
                stream.write('# host_monotonic_s='+str(time.perf_counter())+'\n')
                stream.flush()
                subprocess.run([smi,'--query-gpu=timestamp,index,uuid,name,utilization.gpu,memory.used,power.draw',
                                '--format=csv'],stdout=stream,stderr=errors,timeout=5,check=False)
                stream.flush()
            except Exception as exc:
                errors.write(str(exc)+'\n')
                errors.flush()
            stop.wait(0.2)

total_start=time.perf_counter()
thread=threading.Thread(target=sample,daemon=True)
thread.start()
process_start=time.perf_counter()
try:
    with (raw/'baseline.log').open('wb') as log:
        proc=subprocess.run([str(repo/'build-mc/MonteCarloMultiGPU'),'--method=streamed','--scaling=strong'],
                            cwd=repo,env={**os.environ,'CUDA_VISIBLE_DEVICES':'0'},
                            stdout=log,stderr=subprocess.STDOUT)
finally:
    process_end=time.perf_counter()
    stop.set()
    thread.join()
total_end=time.perf_counter()
def save(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
save(raw/'exit_status.json',{'exit_status':proc.returncode})
text=(raw/'baseline.log').read_text(errors='replace')
number=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
def field(label):
    hits=re.findall(r'^\s*(?:'+label+r')\s*[:=]\s*('+number+r')\s*$',text,re.I|re.M)
    if len(hits)!=1:
        raise RuntimeError('Missing or ambiguous output: '+label)
    value=float(hits[0])
    if not math.isfinite(value) or value<0:
        raise RuntimeError('Invalid output: '+label)
    return value
measured={key:field(label) for key,label in (
    ('options',r'Total number of options|Option count'),
    ('paths_per_option',r'Number of paths|Path count'),('gpus',r'Number of GPUs|GPU count'),
    ('total_time_ms',r'Total time\s*\(ms\.\)'),('l1_norm','L1 norm'),('reserve','Average reserve'))}
verdicts=re.findall(r'Test passed|Test failed!',text)
if len(verdicts)!=1 or measured['total_time_ms']<=0:
    raise RuntimeError('Missing or invalid timing/verdict')
measured['sample_pass']=int(verdicts[0]=='Test passed')
for key in ('options','paths_per_option','gpus'):
    if measured[key]<=0 or not measured[key].is_integer():
        raise RuntimeError('Invalid output count: '+key)
save(raw/'measurements.json',measured)
# Complete failed verdicts remain measurements for pipeline scoring; process
# status is retained in exit_status.json without rejecting valid output.
# Streamed timer is retained above, not added to enclosing process wall time.
# Utilization and power samples do not supply GPU execution durations.
stages=[
    {'stage':'telemetry_start','wall_s':process_start-total_start,'gpu_s':None},
    {'stage':'baseline_process','wall_s':process_end-process_start,'gpu_s':None},
    {'stage':'telemetry_stop','wall_s':total_end-process_end,'gpu_s':None},
]
total=total_end-total_start
if not math.isfinite(total) or total<=0 or any(not math.isfinite(x['wall_s']) or x['wall_s']<0 for x in stages):
    raise RuntimeError('Invalid wall timers')
save(profile/'stages.json',stages)
save(profile/'total_wall_s.json',{'total_wall_s':total})
save(raw/'timing_scope.json',{
    'baseline_process':'Entire unmodified sample process: allocation, RNG init, streamed work, finalization, validation.',
    'streamed_total_ms':measured['total_time_ms'],
    'gpu_s':'Unavailable: nvidia-smi utilization samples are not execution durations.',
    'representative':state,
})
print(json.dumps({'total_wall_s':total,'measurements':measured},indent=2))
PY
