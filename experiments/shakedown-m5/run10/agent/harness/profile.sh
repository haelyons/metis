#!/usr/bin/env bash
set -euo pipefail
base=${BASELINE_DIR:-$PWD/baseline-published}
harness=$(cd "$(dirname "$0")"; pwd)
source "$base/cuda-env.sh"
ls -l "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
mkdir -p out/profile
profile=$(realpath out/profile)
exec > >(tee "$profile/profile.log") 2>&1
# Link wrappers work with both static and shared CUDA runtime linkage.
cat > "$profile/timing.cpp" <<'CPP'
#include <cuda_runtime.h>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <mutex>
static std::mutex lock;
static double now() { timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+t.tv_nsec*1e-9; }
static double origin() { return atof(getenv("PROFILE_ORIGIN")); }
static double previous=0;
static FILE* output=nullptr;
static void emit(const char* stage,const char* kind,double a,double b,double gpu=-1) {
  if(!output) output=fopen(getenv("PROFILE_RAW"),"a");
  if(!output) { perror("profile output"); abort(); }
  fprintf(output,"{\"stage\":\"%s\",\"kind\":\"%s\",\"wall_s\":%.9f,\"gpu_s\":",stage,kind,b-a);
  if(gpu<0) fprintf(output,"null"); else fprintf(output,"%.9f",gpu);
  fprintf(output,",\"start_s\":%.9f}\n",a-origin()); fflush(output);
}
static void begin(double t) {
  // Gaps between synchronous instrumented calls measure actual host work.
  if(previous && t>previous) emit("host work","other",previous,t);
}
static void done(const char* name,const char* kind,double a,double gpu=-1) {
  double b=now(); emit(name,kind,a,b,gpu); previous=b;
}
static void check(cudaError_t e) { if(e!=cudaSuccess) { fprintf(stderr,"Profiler CUDA error: %s\n",cudaGetErrorString(e)); abort(); } }
struct Events {
 cudaEvent_t a,b; cudaStream_t s;
 Events(cudaStream_t stream):s(stream) { check(cudaEventCreate(&a));check(cudaEventCreate(&b));check(cudaEventRecord(a,s)); }
 double finish() { check(cudaEventRecord(b,s));check(cudaEventSynchronize(b));float ms;check(cudaEventElapsedTime(&ms,a,b));check(cudaEventDestroy(a));check(cudaEventDestroy(b));return ms/1000.; }
};
extern "C" cudaError_t __real_cudaLaunchKernel(const void*,dim3,dim3,void**,size_t,cudaStream_t);
extern "C" cudaError_t __wrap_cudaLaunchKernel(const void* f,dim3 g,dim3 b,void** args,size_t mem,cudaStream_t s) {
 std::lock_guard<std::mutex> guard(lock); double t=now();begin(t); Events ev(s);
 auto e=__real_cudaLaunchKernel(f,g,b,args,mem,s);check(e);double gpu=ev.finish();done("CUDA kernel","compute",t,gpu);return e;
}
extern "C" cudaError_t __real_cudaMemcpyAsync(void*,const void*,size_t,cudaMemcpyKind,cudaStream_t);
extern "C" cudaError_t __wrap_cudaMemcpyAsync(void* d,const void* s,size_t n,cudaMemcpyKind k,cudaStream_t stream) {
 std::lock_guard<std::mutex> guard(lock);double t=now();begin(t); Events ev(stream);
 auto e=__real_cudaMemcpyAsync(d,s,n,k,stream);check(e);double gpu=ev.finish();
 done(k==cudaMemcpyHostToDevice?"H2D copy":k==cudaMemcpyDeviceToHost?"D2H copy":"CUDA copy","transfer",t,gpu);return e;
}
extern "C" cudaError_t __real_cudaMemcpy(void*,const void*,size_t,cudaMemcpyKind);
extern "C" cudaError_t __wrap_cudaMemcpy(void* d,const void* s,size_t n,cudaMemcpyKind k) {
 std::lock_guard<std::mutex> guard(lock);double t=now();begin(t); Events ev(0);
 auto e=__real_cudaMemcpy(d,s,n,k);check(e);double gpu=ev.finish();
 done(k==cudaMemcpyHostToDevice?"H2D copy":k==cudaMemcpyDeviceToHost?"D2H copy":"CUDA copy","transfer",t,gpu);return e;
}
extern "C" cudaError_t __real_cudaMalloc(void**,size_t);
extern "C" cudaError_t __wrap_cudaMalloc(void** p,size_t n) {
 std::lock_guard<std::mutex> guard(lock);double t=now();begin(t); auto e=__real_cudaMalloc(p,n);done("device allocation","other",t);return e;
}
extern "C" cudaError_t __real_cudaFree(void*);
extern "C" cudaError_t __wrap_cudaFree(void* p) {
 std::lock_guard<std::mutex> guard(lock);double t=now();begin(t);auto e=__real_cudaFree(p);done("device release","other",t);return e;
}
extern "C" cudaError_t __real_cudaDeviceReset();
extern "C" cudaError_t __wrap_cudaDeviceReset() {
 std::lock_guard<std::mutex> guard(lock);double t=now();begin(t);check(cudaDeviceSynchronize());auto e=__real_cudaDeviceReset();done("device reset","other",t);return e;
}
__attribute__((destructor)) static void finish() {
 if(previous) { double t=now();if(t>previous)emit("host finalization","other",previous,t); }
 if(output)fclose(output);
}
CPP
/usr/bin/g++ -std=c++17 -O2 -I"$CUDA_INCLUDE" -c "$profile/timing.cpp" -o "$profile/timing.o"
wrap=''
for symbol in cudaLaunchKernel cudaMemcpyAsync cudaMemcpy cudaMalloc cudaFree cudaDeviceReset; do
  wrap+=" -Wl,--wrap=$symbol"
done
# Defer instrumentation until the executable exists. Global linker flags also
# affect CMake's C compiler checks, which cannot link this CUDA/C++ object.
cat > "$profile/instrumentation.cmake" <<CMAKE
cmake_language(DEFER CALL target_sources MonteCarloMultiGPU PRIVATE "$profile/timing.o")
cmake_language(DEFER CALL target_link_libraries MonteCarloMultiGPU PRIVATE pthread)
cmake_language(DEFER CALL target_link_options MonteCarloMultiGPU PRIVATE $wrap)
CMAKE
# Clear the failed attempt's cached global flags when reusing its build tree.
flags=(-DCMAKE_BUILD_TYPE=Release "-DCMAKE_CUDA_COMPILER=$CUDA_COMPILER" "-DCUDAToolkit_INCLUDE_DIR=$CUDA_INCLUDE" "-DCUDA_cudart_LIBRARY=$CUDA_LIB/libcudart.so" "-DCMAKE_CUDA_FLAGS=-I$CUDA_INCLUDE -L$CUDA_LIB" -DCMAKE_EXE_LINKER_FLAGS= "-DCMAKE_PROJECT_INCLUDE=$profile/instrumentation.cmake")
[[ -z $CUDA_ROOT ]] || flags+=("-DCUDAToolkit_ROOT=$CUDA_ROOT")
"$CMAKE_BIN" -S "$base/representative-source/Samples/5_Domain_Specific/MonteCarloMultiGPU" -B "$profile/build" "${flags[@]}"
"$CMAKE_BIN" --build "$profile/build" --target MonteCarloMultiGPU --parallel 16
# Keep the canonical executable path and arguments identical. Restore on every exit.
cp -p "$base/build-mc/MonteCarloMultiGPU" "$profile/original-binary"
restore() { cp -p "$profile/original-binary" "$base/build-mc/MonteCarloMultiGPU"; }
trap restore EXIT
cp "$profile/build/MonteCarloMultiGPU" "$base/build-mc/MonteCarloMultiGPU"
export BASELINE_DIR="$base"
python3 - "$harness/run_anchors.sh" "$profile" <<'PY'
import csv, json, math, os, pathlib, subprocess, sys, threading, time
script, directory = sys.argv[1:]; p=pathlib.Path(directory)
raw=p/'stages.raw.jsonl';raw.write_text('')
origin=time.monotonic(); env=os.environ.copy()
env.update(PROFILE_ORIGIN=str(origin),PROFILE_RAW=str(raw),RUN_LOG=str(p/'baseline.log'),CUDA_VISIBLE_DEVICES='0')
stop=threading.Event(); samples=[]
def telemetry():
    with (p/'nvidia-smi.raw.csv').open('w') as f:
        while not stop.is_set():
            t=time.monotonic()-origin
            q=subprocess.run(['nvidia-smi','--id=0','--query-gpu=utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True)
            f.write(f'{t:.9f},{q.stdout.strip()}\n'); f.flush()
            if q.returncode==0:
                try:
                    u=float(q.stdout.strip())
                    if math.isfinite(u) and 0<=u<=100:samples.append({'t':t,'util':u})
                except ValueError:pass
            stop.wait(.1)
thread=threading.Thread(target=telemetry);thread.start()
try:
    result=subprocess.run(['bash',script,'--representative'],env=env,timeout=1130)
    elapsed=time.monotonic()-origin
finally:
    stop.set();thread.join(timeout=10)
(p/'total_wall_s.json').write_text(json.dumps({'total_wall_s':elapsed},allow_nan=False))
(p/'gpu_util.json').write_text(json.dumps(samples,allow_nan=False))
if result.returncode:raise SystemExit(result.returncode)
stages=[json.loads(line) for line in raw.read_text().splitlines() if line.strip()]
# A runtime interval must be a real internal operation, not a process wrapper.
for s in stages:
    for key in ('wall_s','start_s'):
        if not math.isfinite(s[key]) or s[key]<0:raise SystemExit('Invalid stage timing')
    if s['gpu_s'] is not None and (not math.isfinite(s['gpu_s']) or s['gpu_s']<0):raise SystemExit('Invalid GPU timing')
    if abs(s['wall_s']-elapsed)<=.02*elapsed:raise SystemExit('Internal interval indistinguishable from whole process; cannot claim stage coverage')
if len(stages)<3 or not samples:raise SystemExit('Missing stages or GPU telemetry')
if sum(s['wall_s'] for s in stages)/elapsed<.9:raise SystemExit('Insufficient measured internal stage coverage')
(p/'stages.json').write_text(json.dumps(stages,allow_nan=False))
PY
