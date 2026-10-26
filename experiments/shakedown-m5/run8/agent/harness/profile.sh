#!/usr/bin/env bash
set -Eeuo pipefail
if [[ ${MC_PROFILE_DEADLINE:-0} != 1 ]]; then
  exec timeout --signal=TERM --kill-after=10s 1150s env MC_PROFILE_DEADLINE=1 bash "$0" "$@"
fi
mkdir -p out/profile
exec > >(tee out/profile/driver.log) 2>&1
CUDA_ROOT=
CUDA_LIBDIR=
for root in /usr/local/cuda /usr/lib/cuda /usr; do
  if ls "$root/include/cuda_runtime.h" "$root/lib64/libcudart.so" "$root/bin/nvcc"; then
    CUDA_ROOT="$root"; CUDA_LIBDIR="$root/lib64"; break
  fi
done
# Match the native Ubuntu toolkit layout validated by setup.sh. Do not create
# an overlay or change the stock image when libraries use a multiarch directory.
if [[ -z $CUDA_ROOT ]]; then
  multiarch=$(/usr/bin/gcc -print-multiarch)
  if [[ -n $multiarch && $multiarch != */* ]] && \
      ls /usr/include/cuda_runtime.h "/usr/lib/$multiarch/libcudart.so" /usr/bin/nvcc; then
    CUDA_ROOT=/usr
    CUDA_LIBDIR="/usr/lib/$multiarch"
  fi
fi
[[ -n $CUDA_ROOT ]] || { echo 'No complete CUDA toolkit in the probed roots, including the native /usr multiarch layout.' >&2; exit 1; }
export PATH="$CUDA_ROOT/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_LIBDIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# Reuse the fixed representative configuration prepared by setup.sh.
BASELINE_DIR="${BASELINE_DIR:-$PWD/baseline-published}"
/usr/bin/cmake -S "$BASELINE_DIR/Samples/5_Domain_Specific/MonteCarloMultiGPU" \
  -B "$BASELINE_DIR/build-mc" -DCMAKE_BUILD_TYPE=Release \
  -DCUDAToolkit_ROOT="$CUDA_ROOT" -DCMAKE_CUDA_COMPILER="$CUDA_ROOT/bin/nvcc"
/usr/bin/cmake --build "$BASELINE_DIR/build-mc" --target MonteCarloMultiGPU --parallel 16
CUPTI_INCLUDE= CUPTI_LIB=
for dir in "$CUDA_ROOT/extras/CUPTI/include" "$CUDA_ROOT/include" "$CUDA_ROOT/targets/x86_64-linux/include"; do
  if [[ -f $dir/cupti.h ]]; then CUPTI_INCLUDE="$dir"; break; fi
done
for dir in "$CUDA_ROOT/extras/CUPTI/lib64" "$CUDA_LIBDIR" "$CUDA_ROOT/targets/x86_64-linux/lib"; do
  if [[ -f $dir/libcupti.so ]]; then CUPTI_LIB="$dir"; break; fi
done
[[ -n $CUPTI_INCLUDE && -n $CUPTI_LIB ]] || { echo 'CUPTI development files unavailable in probed toolkit; cannot measure internal stages.' >&2; exit 1; }
cat > out/profile/activity.cpp <<'CPP'
#include <cuda_runtime_api.h>
#include <cupti.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <pthread.h>
static FILE *raw;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static int failed;
static uint64_t begin_ns;
static void check(CUptiResult r) {
  if (r != CUPTI_SUCCESS) {
    const char *s = nullptr;
    cuptiGetResultString(r, &s);
    fprintf(stderr,"CUPTI failure: %s\n",s ? s : "unknown");
    failed = 1;
  }
}
static void CUPTIAPI request(uint8_t **buffer, size_t *size, size_t *max_records) {
  *size = 8 * 1024 * 1024;
  *max_records = 0;
  *buffer = (uint8_t *)malloc(*size);
  if (!*buffer) { fprintf(stderr,"CUPTI buffer allocation failed\n"); _Exit(91); }
}
static void CUPTIAPI complete(CUcontext context, uint32_t stream, uint8_t *buffer, size_t, size_t valid) {
  pthread_mutex_lock(&lock);
  CUpti_Activity *record;
  CUptiResult r;
  while ((r = cuptiActivityGetNextRecord(buffer, valid, &record)) == CUPTI_SUCCESS) {
    if (record->kind == CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL || record->kind == CUPTI_ACTIVITY_KIND_KERNEL) {
      auto *k = (CUpti_ActivityKernel4 *)record;
      fprintf(raw,"compute\t%llu\t%llu\t%s\n",(unsigned long long)k->start,(unsigned long long)k->end,k->name ? k->name : "CUDA kernel");
    } else if (record->kind == CUPTI_ACTIVITY_KIND_MEMCPY) {
      auto *m = (CUpti_ActivityMemcpy *)record;
      fprintf(raw,"transfer\t%llu\t%llu\tCUDA memcpy kind %u\n",(unsigned long long)m->start,(unsigned long long)m->end,(unsigned)m->copyKind);
    }
  }
  if (r != CUPTI_ERROR_MAX_LIMIT_REACHED) check(r);
  size_t dropped = 0;
  check(cuptiActivityGetNumDroppedRecords(context, stream, &dropped));
  if (dropped) { fprintf(stderr,"Dropped CUPTI records: %zu\n",dropped); failed = 1; }
  fflush(raw);
  pthread_mutex_unlock(&lock);
  free(buffer);
}
__attribute__((constructor)) static void start() {
  const char *path = getenv("MC_PROFILE_RAW");
  if (!path) { fprintf(stderr,"MC_PROFILE_RAW is required\n"); _Exit(92); }
  raw = fopen(path,"w");
  if (!raw) { perror(path); _Exit(92); }
  check(cuptiActivityRegisterCallbacks(request, complete));
  check(cuptiActivityEnable(CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL));
  check(cuptiActivityEnable(CUPTI_ACTIVITY_KIND_MEMCPY));
  check(cuptiGetTimestamp(&begin_ns));
  if (failed) _Exit(93);
}
__attribute__((destructor)) static void stop() {
  // All work uses CUDA_VISIBLE_DEVICES=0. Synchronize before stopping the clock.
  if (cudaDeviceSynchronize() != cudaSuccess) { fprintf(stderr,"Final CUDA synchronization failed\n"); failed = 1; }
  uint64_t end_ns = 0;
  check(cuptiGetTimestamp(&end_ns));
  check(cuptiActivityFlushAll(0));
  fprintf(raw,"bounds\t%llu\t%llu\tmeasured run\n",(unsigned long long)begin_ns,(unsigned long long)end_ns);
  fclose(raw);
  if (failed) _Exit(94);
}
CPP
g++ -std=c++17 -O2 -shared -fPIC out/profile/activity.cpp -o out/profile/activity.so \
  -I"$CUPTI_INCLUDE" -I"$CUDA_ROOT/include" -L"$CUPTI_LIB" -L"$CUDA_LIBDIR" \
  -Wl,-rpath,"$CUPTI_LIB" -Wl,-rpath,"$CUDA_LIBDIR" -lcupti -lcudart -lpthread
export MC_PROFILE_RAW="$PWD/out/profile/activity.tsv"
export MC_PROFILE_LIBRARY="$PWD/out/profile/activity.so"
export MC_PROFILE_BINARY="${BASELINE_DIR:-$PWD/baseline-published}/build-mc/MonteCarloMultiGPU"
python3 - <<'PY'
import json, math, os, re, subprocess, threading, time
from pathlib import Path
p=Path('out/profile')
stop=threading.Event()
samples=[]
t0=time.monotonic()
def sample():
    with (p/'nvidia-smi.csv').open('w') as raw:
        while not stop.is_set():
            result=subprocess.run(['nvidia-smi','--id=0','--query-gpu=utilization.gpu','--format=csv,noheader,nounits'],text=True,capture_output=True,timeout=10)
            t=time.monotonic()-t0
            raw.write(f'{t:.9f},{result.stdout.strip()},{result.stderr.strip()}\n'); raw.flush()
            if result.returncode==0:
                try:
                    util=float(result.stdout.strip())
                    if math.isfinite(util) and 0<=util<=100: samples.append({'t':t,'util':util})
                except ValueError: pass
            stop.wait(0.2)
thread=threading.Thread(target=sample)
thread.start()
env=os.environ.copy()
env['CUDA_VISIBLE_DEVICES']='0'
env['LD_PRELOAD']=env['MC_PROFILE_LIBRARY']
try:
    with (p/'baseline.stdout').open('w') as log:
        result=subprocess.run([env['MC_PROFILE_BINARY'],'--method=streamed','--scaling=strong'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1040)
finally:
    stop.set(); thread.join()
    (p/'gpu_util.json').write_text(json.dumps(samples,allow_nan=False)+'\n')
(p/'exit_status').write_text(str(result.returncode)+'\n')
s=(p/'baseline.stdout').read_text()
for label,expected in [('Number of GPUs',1),('Total number of options',1048576),('Number of paths',262144)]:
    m=re.search(re.escape(label)+r'\s*[:=]\s*(\d+)',s,re.I)
    if not m or int(m[1])!=expected: raise SystemExit('Invalid printed configuration: '+label)
for label in ['Average reserve','L1 norm','Total time (ms.)','Options per sec.']:
    m=re.search(re.escape(label)+r'\s*[:=]\s*([-+0-9.eE]+)',s,re.I)
    if not m or not math.isfinite(float(m[1])): raise SystemExit('Missing/invalid '+label)
verdict=re.search(r'Test (passed|failed!)',s)
if not verdict or result.returncode != (0 if verdict[1]=='passed' else 1): raise SystemExit('Invalid execution status or verdict')
if not samples: raise SystemExit('No valid GPU telemetry')
activities=[]
bounds=None
for line in (p/'activity.tsv').read_text().splitlines():
    kind,a,b,name=line.split('\t',3)
    a,b=int(a),int(b)
    if kind=='bounds': bounds=(a,b)
    elif kind in ('compute','transfer'):
        if a<=0 or b<a: raise SystemExit('Invalid CUPTI activity timestamps')
        if b>a: activities.append((a,b,kind,name))
if not bounds or bounds[1]<=bounds[0] or not activities: raise SystemExit('Missing CUPTI timing output')
start,end=bounds
total=(end-start)*1e-9
# Sweep actual device intervals. Attribute each time slice once, giving compute
# priority over overlapping transfers. Gaps are measured host-side intervals.
events={start:[],end:[]}
for i,(a,b,kind,name) in enumerate(activities):
    a,b=max(start,a),min(end,b)
    if b<=a: continue
    events.setdefault(a,[]).append((1,i))
    events.setdefault(b,[]).append((-1,i))
active=set(); segments=[]; points=sorted(events)
for j,a in enumerate(points[:-1]):
    for op,i in events[a]:
        if op==1: active.add(i)
        else: active.discard(i)
    b=points[j+1]
    if active:
        i=min(active,key=lambda i:(activities[i][2]!='compute',i))
        kind,name=activities[i][2:]
        key=('gpu',i)
    else:
        key=('host',j); kind='other'
        if a==start: name='Host initialization and option generation'
        elif b==end: name='Host result finalization, validation and cleanup'
        else: name='Host work between device activities'
    if segments and segments[-1]['key']==key: segments[-1]['end']=b
    else: segments.append({'key':key,'start':a,'end':b,'kind':kind,'name':name})
stages=[]
for i,segment in enumerate(segments):
    wall=(segment['end']-segment['start'])*1e-9
    stages.append({'stage':f'{i:04d} {segment["name"]}','kind':segment['kind'],'wall_s':wall,'gpu_s':wall if segment['kind']!='other' else None})
if len(stages)<3: raise SystemExit('Fewer than three measured internal stages')
if any(x['wall_s']>=0.98*total for x in stages): raise SystemExit('One activity consumes >=98% of run; cannot provide required internal stage decomposition')
if sum(x['wall_s'] for x in stages)/total<0.9: raise SystemExit('Insufficient measured stage coverage')
(p/'stages.json').write_text(json.dumps(stages,allow_nan=False)+'\n')
(p/'total_wall_s.json').write_text(json.dumps({'total_wall_s':total},allow_nan=False)+'\n')
PY
