#!/usr/bin/env bash
set -Eeuo pipefail
if [[ ${MC_PROFILE_BUDGET:-0} != 1 ]]; then
  exec env MC_PROFILE_BUDGET=1 timeout --signal=TERM --kill-after=10s 1180s bash "$0" "$@"
fi
root=$PWD
baseline=${BASELINE_DIR:-$root/baseline-published}
mkdir -p "$root/out/profile"
profile=$root/out/profile
exec > >(tee -a "$profile/profile.log") 2>&1
source "$baseline/.harness_cuda.env"
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
export PATH="$(dirname "$CUDA_NVCC"):$PATH"
export LD_LIBRARY_PATH="$CUDA_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CUDA_VISIBLE_DEVICES=0
command -v nvidia-smi >/dev/null || { echo 'Required nvidia-smi missing; supplied apt source only supplies NVIDIA container tools' >&2; exit 1; }
# Timestamp the published program's phase announcements inside the process.
# This interposer changes neither the binary nor its CUDA calls. GPU durations
# are unavailable with this method and are reported as null, never estimated.
cat > "$profile/output-timing.cpp" <<'CPP'
#include <cstdio>
#include <cstdarg>
#include <cstdlib>
#include <ctime>
#include <dlfcn.h>
#include <fcntl.h>
#include <pthread.h>
#include <unistd.h>
static pthread_mutex_t timing_lock = PTHREAD_MUTEX_INITIALIZER;
static void record_output(const char *text) {
  const char *path = getenv("MC_PHASE_OUT");
  if (!path) return;
  timespec ts{};
  clock_gettime(CLOCK_MONOTONIC, &ts);
  char line[16384];
  int prefix = snprintf(line, sizeof(line), "%.17g\t", ts.tv_sec + ts.tv_nsec * 1e-9);
  size_t n = (size_t)prefix;
  for (const char *c = text; *c && n + 2 < sizeof(line); ++c)
    line[n++] = (*c == '\n' || *c == '\r' || *c == '\t') ? ' ' : *c;
  line[n++] = '\n';
  pthread_mutex_lock(&timing_lock);
  int fd = open(path, O_WRONLY | O_CREAT | O_APPEND, 0600);
  if (fd >= 0) {
    size_t done = 0;
    while (done < n) {
      ssize_t wrote = write(fd, line + done, n - done);
      if (wrote <= 0) break;
      done += (size_t)wrote;
    }
    close(fd);
  }
  pthread_mutex_unlock(&timing_lock);
}
static void record_format(const char *format, va_list args) {
  char text[16384];
  va_list copy;
  va_copy(copy, args);
  vsnprintf(text, sizeof(text), format, copy);
  va_end(copy);
  record_output(text);
}
extern "C" int printf(const char *format, ...) {
  using Function = int (*)(FILE *, const char *, va_list);
  static Function real = (Function)dlsym(RTLD_NEXT, "vfprintf");
  va_list args;
  va_start(args, format);
  record_format(format, args);
  int result = real(stdout, format, args);
  va_end(args);
  return result;
}
extern "C" int __printf_chk(int flag, const char *format, ...) {
  using Function = int (*)(FILE *, int, const char *, va_list);
  static Function real = (Function)dlsym(RTLD_NEXT, "__vfprintf_chk");
  va_list args;
  va_start(args, format);
  record_format(format, args);
  int result = real(stdout, flag, format, args);
  va_end(args);
  return result;
}
extern "C" int puts(const char *text) {
  using Function = int (*)(const char *);
  static Function real = (Function)dlsym(RTLD_NEXT, "puts");
  record_output(text);
  return real(text);
}
CPP
/usr/bin/g++ -std=c++17 -O2 -shared -fPIC -pthread \
  "$profile/output-timing.cpp" -ldl -o "$profile/output-timing.so"
# A previous invocation must not contribute phase timestamps to this run.
: > "$profile/output-timing.tsv"
export MC_BASELINE="$baseline" MC_PROFILE="$profile" CUDA_LIB
python3 - <<'PY'
import ctypes, json, math, os, pathlib, re, subprocess, threading, time
out=pathlib.Path(os.environ['MC_PROFILE'])
base=pathlib.Path(os.environ['MC_BASELINE']).resolve()
cuda=ctypes.CDLL(os.environ['CUDA_LIB']+'/libcudart.so')
def sync():
    if cuda.cudaSetDevice(0)!=0 or cuda.cudaDeviceSynchronize()!=0: raise RuntimeError('GPU synchronization failed')
samples=[]; errors=[]; stop=threading.Event()
sync()
env=os.environ.copy()
env['CUDA_VISIBLE_DEVICES']='0'
env['LD_PRELOAD']=str(out/'output-timing.so') + ((':'+env['LD_PRELOAD']) if env.get('LD_PRELOAD') else '')
env['MC_PHASE_OUT']=str(out/'output-timing.tsv')
begin=time.monotonic()
def telemetry():
    with (out/'nvidia-smi.raw.log').open('w') as raw:
        while not stop.is_set():
            t=time.monotonic()-begin
            try:
                p=subprocess.run(['nvidia-smi','--id=0','--query-gpu=utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5)
                raw.write(f'{t:.9f}\t{p.stdout.strip()}\t{p.stderr.strip()}\n'); raw.flush()
                if p.returncode: raise RuntimeError('nvidia-smi failed')
                util=float(p.stdout.strip())
                if not math.isfinite(util) or not 0<=util<=100: raise RuntimeError('Invalid GPU utilization')
                samples.append({'t':t,'util':util})
            except Exception as e: errors.append(str(e))
            stop.wait(.15)
thread=threading.Thread(target=telemetry); thread.start()
try:
    with (out/'baseline-output.log').open('w') as log:
        # Canonical run_anchors.sh command, arguments, environment and GPU count.
        proc=subprocess.Popen(['./build-mc/MonteCarloMultiGPU','--method=streamed','--scaling=strong'],cwd=base,env=env,stdout=log,stderr=subprocess.STDOUT)
        try: status=proc.wait(timeout=1100)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(); sync()
            raise RuntimeError('Fixed representative scale timed out')
    sync()
    end=time.monotonic()
finally:
    stop.set(); thread.join(timeout=6)
total=end-begin
if not math.isfinite(total) or total<=0: raise RuntimeError('Invalid measured total wall time')
(out/'total_wall_s.json').write_text(json.dumps({'total_wall_s':total},allow_nan=False)+'\n')
(out/'gpu_util.json').write_text(json.dumps(samples,allow_nan=False)+'\n')
if not samples: raise RuntimeError('Missing GPU utilization samples: '+repr(errors))
text=(out/'baseline-output.log').read_text(errors='replace')
def number(label):
    matches=re.findall(r'^\s*'+label+r'\s*[:=]\s*([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*$',text,re.I|re.M)
    if len(matches)!=1: raise RuntimeError('Missing, invalid or ambiguous printed field: '+label)
    value=float(matches[0])
    if not math.isfinite(value): raise RuntimeError('Nonfinite printed field')
    return value
for label,wanted in [(r'Number of GPUs',1),(r'Total number of options',1048576),(r'Number of paths',262144)]:
    if number(label)!=wanted: raise RuntimeError('Printed configuration differs from canonical command: '+label)
for label,wanted in [('Parallelization method','streamed'),('Problem scaling','strong')]:
    values=re.findall(r'^\s*'+label+r'\s*=\s*(\S+)\s*$',text,re.M)
    if values!=[wanted]: raise RuntimeError('Printed configuration differs from canonical command: '+label)
if number(r'Total time\s*\(ms\.\)')<=0: raise RuntimeError('Invalid published time')
reserve=number('Average reserve'); l1=number('L1 norm')
if reserve<0 or l1<0: raise RuntimeError('Invalid quality statistics')
verdict=re.findall(r'Test (passed|failed!)',text)
if len(verdict)!=1 or (status==0)!=(verdict[0]=='passed'): raise RuntimeError('Invalid output or inconsistent process status')
(out/'statistics.json').write_text(json.dumps({'average_reserve':reserve,'l1_norm':l1,'sample-pass':int(verdict[0]=='passed'),'total_time_ms':number(r'Total time\s*\(ms\.\)'),'exit_status':status},allow_nan=False)+'\n')
# Consecutive announcements delimit actual internal phases. No unobserved
# startup/exit duration is allocated to a phase, and no GPU time is inferred
# from either host wall time or the program's aggregate streamed timer.
lines=(out/'output-timing.tsv').read_text().splitlines()
announcements=[]
for line in lines:
    stamp,message=line.split('\t',1)
    stamp=float(stamp)-begin
    if not math.isfinite(stamp) or stamp<0 or stamp>total:
        raise RuntimeError('Invalid output timestamp')
    announcements.append((stamp,message))
def marker(pattern):
    stamps=[stamp for stamp,message in announcements if re.search(pattern,message)]
    if len(stamps)!=1: raise RuntimeError('Missing or ambiguous phase announcement: '+pattern)
    return stamps[0]
markers=[
    marker(r'^\./build-mc/MonteCarloMultiGPU Starting\.\.\.'),
    marker(r'^main\(\): generating input data\.\.\.'),
    marker(r'^main\(\): starting 1 host threads\.\.\.'),
    marker(r'^main\(\): comparing Monte Carlo and Black-Scholes results\.\.\.'),
    marker(r'^Shutting down\.\.\.'),
    marker(r'^Test (?:passed|failed!)\s*$'),
]
phases=[
    ('device discovery and configuration','other'),
    ('host input generation','other'),
    ('allocation, RNG setup and streamed pricing','compute'),
    ('host Black-Scholes validation','other'),
    ('cleanup and result reporting','other'),
]
stages=[]
for (name,kind),a,b in zip(phases,markers,markers[1:]):
    if b<a: raise RuntimeError('Phase announcements out of order')
    duration=b-a
    if abs(duration-total)<=.02*total:
        raise RuntimeError('Internal phase indistinguishable from a process wrapper')
    stages.append({'stage':name,'kind':kind,'wall_s':duration,'gpu_s':None})
(out/'stages.json').write_text(json.dumps(stages,allow_nan=False)+'\n')
if len(stages)<3: raise RuntimeError('Trace contains fewer than three internal timed stages')
if min(1,sum(s['wall_s'] for s in stages)/total)<.9: raise RuntimeError('Internal timed stages cover less than 90% of measured run')
for s in stages:
    if not math.isfinite(s['wall_s']) or s['wall_s']<0: raise RuntimeError('Invalid measured stage')
    if s['gpu_s'] is not None and (not math.isfinite(s['gpu_s']) or s['gpu_s']<0): raise RuntimeError('Invalid measured GPU activity')
PY
