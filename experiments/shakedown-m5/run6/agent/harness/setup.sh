#!/usr/bin/env bash
set -euo pipefail
mkdir -p out/setup data harness
exec > >(tee -a out/setup/setup.log) 2>&1
command -v /usr/bin/git >/dev/null
command -v /usr/bin/cmake >/dev/null
command -v /usr/bin/nvcc >/dev/null
# The probe reports CMake 3.22.1, sufficient for this sample.
PIN=db3eea23946bca2e90a75eca2b5b3e07158a9e11
if [[ ! -d baseline-published/.git ]]; then
  git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples baseline-published
fi
git -C baseline-published checkout --detach "$PIN"
[[ $(git -C baseline-published rev-parse HEAD) == "$PIN" ]]
# Restore only the explicitly authorized scale edit when retrying setup.
git -C baseline-published restore Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp
sample=baseline-published/Samples/5_Domain_Specific/MonteCarloMultiGPU
/usr/bin/cmake -S "$sample" -B baseline-published/build-anchor -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=/usr/bin/nvcc
/usr/bin/cmake --build baseline-published/build-anchor --target MonteCarloMultiGPU --parallel 8
# This is the sole intake-authorized configuration edit. No measurements are
# inferred from source. The executable's printed scale is checked at runtime.
sed -i -E 's/(int[[:space:]]+nOptions[[:space:]]*=[[:space:]]*)8[[:space:]]*\*[[:space:]]*1024/\11024 * 1024/' "$sample/MonteCarloMultiGPU.cpp"
/usr/bin/cmake -S "$sample" -B baseline-published/build-mc -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=/usr/bin/nvcc
/usr/bin/cmake --build baseline-published/build-mc --target MonteCarloMultiGPU --parallel 8
cat > data/generated-inputs.json <<'JSON'
{"host_seed":123,"options":1048576,"anchor_options":8192,"paths_per_option":262144,"gpu_count":1,"method":"streamed","scaling":"strong","external_data":false}
JSON
# CUPTI is supplied with CUDA. Discover its actual location rather than assuming
# an unprobed versioned toolkit directory. No package or source substitution.
CUPTI_HEADER=$(find -L /usr/local /usr/lib /usr/include -name cupti_activity.h -print -quit 2>/dev/null || true)
if [[ -z "$CUPTI_HEADER" ]]; then
  echo 'Required CUDA CUPTI development files unavailable; cannot produce honest stage profiling.' >&2
  exit 1
fi
CUPTI_INCLUDE=$(dirname "$CUPTI_HEADER")
CUPTI_LIB=$(find -L /usr/local /usr/lib -name libcupti.so -print -quit 2>/dev/null || true)
[[ -n "$CUPTI_LIB" ]] || { echo 'Required libcupti.so unavailable' >&2; exit 1; }
cat > harness/activity.cpp <<'CPP'
#include <cupti.h>
#include <cupti_activity.h>
#include <cuda.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <ctime>
#include <dlfcn.h>
#include <mutex>
static FILE *logfile;
static std::mutex lock;
static void check(CUptiResult r) {
  if (r != CUPTI_SUCCESS) { const char *s=nullptr; cuptiGetResultString(r,&s); fprintf(stderr,"CUPTI: %s\n",s); fflush(stderr); _Exit(97); }
}
static void CUPTIAPI request(uint8_t **b,size_t *n,size_t *max) {
  *n=8*1024*1024; *b=(uint8_t*)malloc(*n); *max=0;
  if (!*b) _Exit(98);
}
static void CUPTIAPI complete(CUcontext ctx,uint32_t stream,uint8_t *b,size_t,size_t valid) {
  std::lock_guard<std::mutex> guard(lock);
  CUpti_Activity *r; CUptiResult status;
  while ((status=cuptiActivityGetNextRecord(b,valid,&r))==CUPTI_SUCCESS) {
    if (r->kind==CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL || r->kind==CUPTI_ACTIVITY_KIND_KERNEL) {
      auto *k=(CUpti_ActivityKernel9*)r;
      fprintf(logfile,"event\tcompute\t%llu\t%llu\t%s\n",(unsigned long long)k->start,(unsigned long long)k->end,k->name);
      fprintf(logfile,"grid\t%d\t%d\t%d\t%d\t%d\t%d\n",k->gridX,k->gridY,k->gridZ,k->blockX,k->blockY,k->blockZ);
    } else if(r->kind==CUPTI_ACTIVITY_KIND_MEMCPY) {
      auto *m=(CUpti_ActivityMemcpy*)r;
      fprintf(logfile,"event\ttransfer\t%llu\t%llu\tmemcpy_%u\n",(unsigned long long)m->start,(unsigned long long)m->end,(unsigned)m->copyKind);
    } else if(r->kind==CUPTI_ACTIVITY_KIND_MEMSET) {
      auto *m=(CUpti_ActivityMemset*)r;
      fprintf(logfile,"event\tother\t%llu\t%llu\tdevice_memset\n",(unsigned long long)m->start,(unsigned long long)m->end);
    }
  }
  if (status!=CUPTI_ERROR_MAX_LIMIT_REACHED) check(status);
  size_t dropped=0; check(cuptiActivityGetNumDroppedRecords(ctx,stream,&dropped));
  if(dropped) { fprintf(stderr,"CUPTI dropped %zu records\n",dropped); _Exit(96); }
  fflush(logfile); free(b);
}
__attribute__((constructor)) static void begin() {
  const char *p=getenv("HARNESS_ACTIVITY"); if(!p) return;
  logfile=fopen(p,"w"); if(!logfile) _Exit(95);
  uint64_t t; check(cuptiGetTimestamp(&t)); fprintf(logfile,"begin\t%llu\n",(unsigned long long)t);
  check(cuptiActivityRegisterCallbacks(request,complete));
  check(cuptiActivityEnable(CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL));
  check(cuptiActivityEnable(CUPTI_ACTIVITY_KIND_MEMCPY));
  check(cuptiActivityEnable(CUPTI_ACTIVITY_KIND_MEMSET));
}
__attribute__((destructor)) static void finish() {
  if(!logfile) return;
  void *driver=dlopen("libcuda.so.1",RTLD_NOW);
  if(!driver) _Exit(94);
  auto get=(CUresult(*)(CUcontext*))dlsym(driver,"cuCtxGetCurrent");
  auto sync=(CUresult(*)())dlsym(driver,"cuCtxSynchronize");
  CUcontext ctx=nullptr;
  if(!get || !sync) _Exit(93);
  CUresult rc=get(&ctx);
  if(rc==CUDA_SUCCESS && ctx && sync()!=CUDA_SUCCESS) _Exit(92);
  check(cuptiActivityFlushAll(0));
  uint64_t t; check(cuptiGetTimestamp(&t)); fprintf(logfile,"end\t%llu\n",(unsigned long long)t);
  fclose(logfile);
}
CPP
/usr/bin/g++ -std=c++17 -O2 -shared -fPIC harness/activity.cpp -I"$CUPTI_INCLUDE" -I/usr/local/cuda/include -I/usr/lib/cuda/include "$CUPTI_LIB" -Wl,-rpath,"$(dirname "$CUPTI_LIB")" -ldl -pthread -o harness/activity.so
/usr/bin/nvcc --version > out/setup/toolkit.txt
getconf GNU_LIBC_VERSION > out/setup/libc.txt
nvidia-smi > out/setup/gpu.txt
