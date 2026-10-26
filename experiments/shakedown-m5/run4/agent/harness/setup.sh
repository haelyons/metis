#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p out/setup data
exec > >(tee -a out/setup/setup.log) 2>&1
trap 'echo "setup failed at line $LINENO" >&2' ERR
for tool in /usr/bin/git /usr/bin/g++ /usr/bin/gcc /usr/bin/make /usr/bin/nvcc python3; do
  command -v "$tool" >/dev/null || { echo "Required probed tool missing: $tool; no eligible apt repository supplies host development tools" >&2; exit 1; }
done
cmake=/usr/bin/cmake
if ! "$cmake" --version | python3 -c 'import re,sys; m=re.search(r"(\d+)\.(\d+)",sys.stdin.read()); sys.exit(not m or tuple(map(int,m.groups()))<(3,20))'; then
  # The sole enabled repository in the probe is NVIDIA's container repository,
  # which does not supply CMake. The permitted fallback is a pinned pip wheel.
  python3 -m pip install --target "$PWD/data/cmake-python" cmake==3.31.6
  export PYTHONPATH="$PWD/data/cmake-python${PYTHONPATH:+:$PYTHONPATH}"
  cmake="$PWD/data/cmake-python/bin/cmake"
fi
pin=db3eea23946bca2e90a75eca2b5b3e07158a9e11
if [[ ! -d baseline-published/.git ]]; then
  git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples.git baseline-published
fi
[[ "$(git -C baseline-published rev-parse HEAD)" == "$pin" ]] || {
  echo "Checkout does not match intake pin" >&2; exit 1;
}
git -C baseline-published checkout --detach "$pin"
# Restore only the host file changed by the explicitly authorized scale protocol.
git -C baseline-published restore --source="$pin" -- Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp
"$cmake" -S baseline-published/Samples/5_Domain_Specific/MonteCarloMultiGPU -B baseline-published/build-mc -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=/usr/bin/nvcc
"$cmake" --build baseline-published/build-mc --target MonteCarloMultiGPU --parallel
printf '%s\n' "$cmake" > data/cmake-command
cat > data/generated-inputs.json <<'JSON'
{"external_dataset":false,"host_seed":123,"S":[5,50],"X":[10,25],"T":[1,5],"R":0.06,"V":0.10,"gpu_rng":"published cuRAND generator; unchanged"}
JSON
/usr/bin/nvcc --version > out/setup/nvcc.txt
ldd --version > out/setup/libc.txt
nvidia-smi -q > out/setup/nvidia-smi.txt
cat > data/scale.json <<'JSON'
{"nOptions":8192,"PATH_N":262144,"gpu_count":1,"method":"streamed","scaling":"strong","precision":"float","THREAD_N":256,"grid_size":"40 * multiProcessorCount cap"}
JSON
# CUPTI is shipped with the discovered toolkit. Find its development files;
# do not install or assume an unprobed toolkit or Nsight distribution.
python3 - <<'PY'
import pathlib,json
roots=[pathlib.Path('/usr/local/cuda'),pathlib.Path('/usr/lib/cuda'),pathlib.Path('/usr')]
incs=[]; libs=[]
for root in roots:
    incs += list(root.glob('extras/CUPTI/include/cupti.h'))
    incs += list(root.glob('include/cupti.h'))
    libs += list(root.glob('extras/CUPTI/lib64/libcupti.so*'))
    libs += list(root.glob('lib64/libcupti.so*'))
    libs += list(root.glob('lib/x86_64-linux-gnu/libcupti.so*'))
if not incs or not libs:
    raise SystemExit('Required CUPTI development files unavailable in discovered toolkit; enabled apt source supplies container tooling only')
json.dump({'include':str(incs[0].parent),'library':str(libs[0].resolve())},open('data/cupti-paths.json','w'))
PY
cat > data/profile-cupti.cpp <<'CPP'
#include <cupti.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <mutex>
#include <string>
static FILE *logfile;
static std::mutex lock;
static uint64_t begin_ns;
static void check(CUptiResult r) {
  if (r != CUPTI_SUCCESS) { const char *s=nullptr; cuptiGetResultString(r,&s); fprintf(stderr,"CUPTI: %s\n",s?s:"error"); std::abort(); }
}
static void row(const char *kind,const char *name,uint64_t a,uint64_t b) {
  if(b<a) return;
  std::lock_guard<std::mutex> guard(lock);
  fprintf(logfile,"%s\t%s\t%llu\t%llu\n",kind,name,(unsigned long long)a,(unsigned long long)b);
}
static void CUPTIAPI request(uint8_t **b,size_t *size,size_t *max) {
  *size=8*1024*1024; *max=0; *b=(uint8_t*)malloc(*size);
  if(!*b) std::abort();
}
static void CUPTIAPI complete(CUcontext ctx,uint32_t stream,uint8_t *b,size_t,size_t valid) {
  CUpti_Activity *r=nullptr;
  CUptiResult status;
  while((status=cuptiActivityGetNextRecord(b,valid,&r))==CUPTI_SUCCESS) {
    if(r->kind==CUPTI_ACTIVITY_KIND_KERNEL || r->kind==CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL) {
      auto *k=(CUpti_ActivityKernel9*)r;
      row("compute",k->name?k->name:"CUDA kernel",k->start,k->end);
    } else if(r->kind==CUPTI_ACTIVITY_KIND_MEMCPY) {
      auto *m=(CUpti_ActivityMemcpy*)r;
      const char *name=m->copyKind==CUPTI_ACTIVITY_MEMCPY_KIND_HTOD?"H2D":m->copyKind==CUPTI_ACTIVITY_MEMCPY_KIND_DTOH?"D2H":"device copy";
      row("transfer",name,m->start,m->end);
    } else if(r->kind==CUPTI_ACTIVITY_KIND_RUNTIME) {
      auto *a=(CUpti_ActivityAPI*)r;
      row("other","CUDA runtime",a->start,a->end);
    }
  }
  if(status!=CUPTI_ERROR_MAX_LIMIT_REACHED) check(status);
  size_t dropped=0; check(cuptiActivityGetNumDroppedRecords(ctx,stream,&dropped));
  if(dropped) { fprintf(stderr,"CUPTI dropped %zu records\n",dropped); std::abort(); }
  free(b);
}
__attribute__((constructor)) static void start_profile() {
  const char *p=getenv("HARNESS_CUPTI_LOG");
  if(!p) return;
  logfile=fopen(p,"w"); if(!logfile) std::abort();
  check(cuptiGetTimestamp(&begin_ns));
  check(cuptiActivityRegisterCallbacks(request,complete));
  check(cuptiActivityEnable(CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL));
  check(cuptiActivityEnable(CUPTI_ACTIVITY_KIND_MEMCPY));
  check(cuptiActivityEnable(CUPTI_ACTIVITY_KIND_RUNTIME));
}
__attribute__((destructor)) static void stop_profile() {
  if(!logfile) return;
  check(cuptiActivityFlushAll(0));
  uint64_t end_ns; check(cuptiGetTimestamp(&end_ns));
  row("bounds","measured run",begin_ns,end_ns);
  fclose(logfile);
}
CPP
python3 - <<'PY'
import json,subprocess,pathlib
p=json.load(open('data/cupti-paths.json'))
subprocess.run(['/usr/bin/g++','-shared','-fPIC','-O2','-std=c++11','-pthread','-I'+p['include'],'-I/usr/local/cuda/include','-I/usr/lib/cuda/include','data/profile-cupti.cpp',p['library'],'-Wl,-rpath,'+str(pathlib.Path(p['library']).parent),'-o','data/profile-cupti.so'],check=True)
PY
printf '%s\n' 'Setup complete; published binary built, profiling collector ready.'
