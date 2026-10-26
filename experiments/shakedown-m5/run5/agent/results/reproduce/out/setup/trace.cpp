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
