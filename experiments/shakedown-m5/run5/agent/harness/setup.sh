#!/usr/bin/env bash
set -euo pipefail
mkdir -p out/setup data
exec > >(tee -a out/setup/setup.log) 2>&1
pin=db3eea23946bca2e90a75eca2b5b3e07158a9e11
for tool in /usr/bin/git /usr/bin/g++ /usr/bin/cmake /usr/bin/nvcc python3; do
  command -v "$tool" >/dev/null || { echo "Required stock tool missing: $tool; enabled probe repository supplies no host-toolchain packages"; exit 1; }
done
if [[ ! -d baseline-published/.git ]]; then
  git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples baseline-published
fi
git -C baseline-published checkout --detach "$pin"
[[ $(git -C baseline-published rev-parse HEAD) == "$pin" ]] || exit 1
/usr/bin/cmake -S baseline-published/Samples/5_Domain_Specific/MonteCarloMultiGPU -B baseline-published/build-mc -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=/usr/bin/nvcc
/usr/bin/cmake --build baseline-published/build-mc --target MonteCarloMultiGPU --parallel 30
cat > data/input_manifest.json <<'JSON'
{"external_files":false,"host_seed":123,"host_generator":"pinned sample libc rand()","gpu_generator":"pinned sample cuRAND","initial_options":8192,"paths_per_option":262144,"gpu_count":1}
JSON
/usr/bin/nvcc --version > out/setup/toolkit.txt
getconf GNU_LIBC_VERSION > out/setup/libc.txt
nvidia-smi -q > out/setup/gpu.txt
# CUPTI is a toolkit component. Discover it only under probe-discovered toolkit
# locations and standard system include/library locations; never replace CUDA.
cupti_header=$(find -L /usr/local/cuda /usr/lib/cuda /usr/include -name cupti.h -print -quit 2>/dev/null || true)
cupti_lib=$(find -L /usr/local/cuda /usr/lib/cuda /usr/lib/x86_64-linux-gnu -name libcupti.so -print -quit 2>/dev/null || true)
[[ -n "$cupti_header" && -n "$cupti_lib" ]] || { echo 'CUPTI development files unavailable in stock toolkit; enabled probe repository cannot supply them'; exit 1; }
cat > out/setup/trace.cpp <<'HARNESS_TRACE_CPP'
// Observation only: CUPTI records real device activities and runtime API spans.
#include <cupti.h>
#include <cuda.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <mutex>
static FILE *logfile;
static std::mutex lock;
static CUpti_SubscriberHandle subscriber;
static uint64_t origin;
static thread_local uint64_t entered;
static void check(CUptiResult result) {
  if (result != CUPTI_SUCCESS) { const char *s=nullptr; cuptiGetResultString(result,&s); fprintf(stderr,"CUPTI: %s\n",s?s:"unknown error"); std::_Exit(92); }
}
static void emit(const char *kind,uint64_t start,uint64_t end,const char *name) {
  if(end<start) std::_Exit(93);
  std::lock_guard<std::mutex> guard(lock);
  fprintf(logfile,"%s\t%llu\t%llu\t%s\n",kind,(unsigned long long)start,(unsigned long long)end,name?name:"");
  fflush(logfile);
}
static void CUPTIAPI requested(uint8_t **buffer,size_t *size,size_t *max) {
  *size=8*1024*1024; *buffer=(uint8_t*)malloc(*size); *max=0;
  if(!*buffer) std::_Exit(94);
}
static void CUPTIAPI completed(CUcontext ctx,uint32_t stream,uint8_t *buffer,size_t,size_t valid) {
  CUpti_Activity *record=nullptr; CUptiResult r;
  while((r=cuptiActivityGetNextRecord(buffer,valid,&record))==CUPTI_SUCCESS) {
    if(record->kind==CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL) {
      auto *k=(CUpti_ActivityKernel9*)record; emit("compute",k->start,k->end,k->name);
    } else if(record->kind==CUPTI_ACTIVITY_KIND_MEMCPY) {
      auto *m=(CUpti_ActivityMemcpy*)record; emit("transfer",m->start,m->end,"memcpy");
    } else if(record->kind==CUPTI_ACTIVITY_KIND_MEMSET) {
      auto *m=(CUpti_ActivityMemset*)record; emit("other",m->start,m->end,"memset");
    }
  }
  if(r!=CUPTI_ERROR_MAX_LIMIT_REACHED) check(r);
  size_t dropped=0; check(cuptiActivityGetNumDroppedRecords(ctx,stream,&dropped));
  if(dropped) { fprintf(stderr,"CUPTI dropped %zu records\n",dropped); std::_Exit(95); }
  free(buffer);
}
static void CUPTIAPI callback(void*,CUpti_CallbackDomain domain,CUpti_CallbackId,const void *data) {
  if(domain!=CUPTI_CB_DOMAIN_RUNTIME_API) return;
  auto *cb=(const CUpti_CallbackData*)data;
  if(cb->callbackSite==CUPTI_API_ENTER) check(cuptiGetTimestamp(&entered));
  else { uint64_t end; check(cuptiGetTimestamp(&end)); emit("api",entered,end,cb->functionName); }
}
extern "C" int InitializeInjection() {
  static bool initialized=false; if(initialized) return 1; initialized=true;
  const char *path=getenv("HARNESS_TRACE"); if(!path) return 0;
  logfile=fopen(path,"w"); if(!logfile) std::_Exit(96);
  check(cuptiGetTimestamp(&origin)); emit("origin",origin,origin,"origin");
  check(cuptiSubscribe(&subscriber,callback,nullptr));
  check(cuptiEnableDomain(1,subscriber,CUPTI_CB_DOMAIN_RUNTIME_API));
  check(cuptiActivityRegisterCallbacks(requested,completed));
  check(cuptiActivityEnable(CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL));
  check(cuptiActivityEnable(CUPTI_ACTIVITY_KIND_MEMCPY));
  check(cuptiActivityEnable(CUPTI_ACTIVITY_KIND_MEMSET));
  atexit([](){check(cuptiActivityFlushAll(0)); uint64_t end; check(cuptiGetTimestamp(&end)); emit("finish",end,end,"finish"); fclose(logfile);});
  return 1;
}
HARNESS_TRACE_CPP
/usr/bin/g++ -std=c++11 -O2 -fPIC -shared out/setup/trace.cpp -I"$(dirname "$cupti_header")" -I/usr/local/cuda/include -I/usr/lib/cuda/include "$cupti_lib" -Wl,-rpath,"$(dirname "$cupti_lib")" -o out/setup/libharness_trace.so
