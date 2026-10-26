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
