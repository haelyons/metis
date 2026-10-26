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
