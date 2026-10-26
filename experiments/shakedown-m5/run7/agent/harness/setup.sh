#!/usr/bin/env bash
set -euo pipefail
mkdir -p baseline-published data out/setup
exec > >(tee -a out/setup/setup.log) 2>&1
# The stock probe supplies suitable CMake, GCC and CUDA. No packages are needed.
for tool in /usr/bin/cmake /usr/bin/g++ /usr/bin/git /usr/bin/python3 /usr/local/cuda/bin/nvcc; do
  test -x "$tool" || { echo "Required probed tool missing: $tool" >&2; exit 1; }
done
# The stock image may split nvcc and development headers across directories.
# CMake 3.22 otherwise searches only next to nvcc and misses system headers.
nvcc=/usr/local/cuda/bin/nvcc
cuda_include=
for compiler in /usr/local/cuda/bin/nvcc /usr/lib/cuda/bin/nvcc /usr/bin/nvcc; do
  compiler_root=$(dirname "$(dirname "$(readlink -f "$compiler")")")
  for include in "$compiler_root/include" "$compiler_root"/targets/*/include; do
    if [[ -f "$include/cuda_runtime.h" ]]; then
      cuda_include=$include
      break 2
    fi
  done
done
if [[ -z "$cuda_include" ]]; then
  # Consult installed package metadata rather than assume another toolkit path.
  while IFS= read -r entry; do
    header=${entry#*: }
    if [[ -f "$header" ]]; then
      cuda_include=$(dirname "$header")
      break
    fi
  done < <(dpkg-query -S '*/cuda_runtime.h' 2>/dev/null || true)
fi
if [[ -z "$cuda_include" ]]; then
  echo 'CUDA development header cuda_runtime.h missing from stock toolkit and installed package metadata.' >&2
  exit 1
fi
cuda_cmake=(-DCMAKE_CUDA_COMPILER="$nvcc" -DCUDAToolkit_INCLUDE_DIR="$cuda_include")
pin=db3eea23946bca2e90a75eca2b5b3e07158a9e11
if [[ ! -d baseline-published/source/.git ]]; then
  /usr/bin/git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples.git baseline-published/source
fi
/usr/bin/git -C baseline-published/source checkout --detach "$pin"
test "$(/usr/bin/git -C baseline-published/source rev-parse HEAD)" = "$pin"
root=$(cd baseline-published && pwd)
sample=Samples/5_Domain_Specific/MonteCarloMultiGPU
/usr/bin/cmake -S "$root/source/$sample" -B "$root/build-anchor" -DCMAKE_BUILD_TYPE=Release "${cuda_cmake[@]}"
/usr/bin/cmake --build "$root/build-anchor" --target MonteCarloMultiGPU --parallel 16
# Keep the published checkout unchanged. Only the explicitly required option
# count differs in the representative worktree.
if [[ ! -d "$root/representative-source" ]]; then
  /usr/bin/git -C "$root/source" worktree add --detach "$root/representative-source" "$pin"
fi
/usr/bin/git -C "$root/representative-source" restore -- "$sample/MonteCarloMultiGPU.cpp"
sed -i -E 's/(nOptions[[:space:]]*=[[:space:]]*)8[[:space:]]*\*[[:space:]]*1024/\11024 * 1024/' "$root/representative-source/$sample/MonteCarloMultiGPU.cpp"
/usr/bin/cmake -S "$root/representative-source/$sample" -B "$root/build-mc" -DCMAKE_BUILD_TYPE=Release "${cuda_cmake[@]}"
/usr/bin/cmake --build "$root/build-mc" --target MonteCarloMultiGPU --parallel 16
cat > data/generated-inputs.json <<'JSON'
{"host_seed":123,"options_anchor":8192,"options_representative":1048576,"paths_per_option":262144,"gpu_count":1,"external_data":false}
JSON
mkdir -p "$root/profile-tools"
cat > "$root/profile-tools/trace.cu" <<'CUDA'
#include <cuda_runtime.h>
#include <dlfcn.h>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <mutex>
#include <vector>
struct Span { cudaEvent_t a,b; const char *kind; double submitted; };
static std::vector<Span> spans;
static std::mutex lock;
static cudaEvent_t origin;
static double origin_wall;
static bool ready=false, flushed=false;
static double now() { return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count(); }
static void check(cudaError_t e) { if(e!=cudaSuccess) { fprintf(stderr,"trace CUDA error: %s\n",cudaGetErrorString(e)); std::abort(); } }
static Span begin(cudaStream_t s,const char *kind) {
  if(!ready) { check(cudaEventCreate(&origin)); origin_wall=now(); check(cudaEventRecord(origin,s)); check(cudaEventSynchronize(origin)); ready=true; }
  Span x; x.kind=kind; x.submitted=now(); check(cudaEventCreate(&x.a)); check(cudaEventCreate(&x.b)); check(cudaEventRecord(x.a,s)); return x;
}
static void end(Span x,cudaStream_t s) { check(cudaEventRecord(x.b,s)); spans.push_back(x); }
static void flush() {
  if(flushed || !ready) return; flushed=true;
  check(cudaDeviceSynchronize());
  const char *p=getenv("HARNESS_CUDA_TRACE"); if(!p) return;
  FILE *f=fopen(p,"w"); if(!f) std::abort();
  for(auto &x:spans) { float a,b; check(cudaEventElapsedTime(&a,origin,x.a)); check(cudaEventElapsedTime(&b,origin,x.b)); fprintf(f,"%s %.9f %.9f %.9f\n",x.kind,origin_wall+a/1000.0,origin_wall+b/1000.0,(b-a)/1000.0); }
  fclose(f);
}
extern "C" cudaError_t cudaLaunchKernel(const void *f,dim3 g,dim3 b,void **a,size_t m,cudaStream_t s) {
  using Fn=cudaError_t(*)(const void*,dim3,dim3,void**,size_t,cudaStream_t);
  static Fn real=(Fn)dlsym(RTLD_NEXT,"cudaLaunchKernel");
  std::lock_guard<std::mutex> guard(lock); Span x=begin(s,"compute"); cudaError_t e=real(f,g,b,a,m,s); end(x,s); return e;
}
extern "C" cudaError_t cudaMemcpyAsync(void *d,const void *s,size_t n,cudaMemcpyKind k,cudaStream_t stream) {
  using Fn=cudaError_t(*)(void*,const void*,size_t,cudaMemcpyKind,cudaStream_t);
  static Fn real=(Fn)dlsym(RTLD_NEXT,"cudaMemcpyAsync");
  std::lock_guard<std::mutex> guard(lock); Span x=begin(stream,k==cudaMemcpyHostToDevice?"H2D":k==cudaMemcpyDeviceToHost?"D2H":"transfer"); cudaError_t e=real(d,s,n,k,stream); end(x,stream); return e;
}
extern "C" cudaError_t cudaMemcpy(void *d,const void *s,size_t n,cudaMemcpyKind k) {
  using Fn=cudaError_t(*)(void*,const void*,size_t,cudaMemcpyKind);
  static Fn real=(Fn)dlsym(RTLD_NEXT,"cudaMemcpy");
  std::lock_guard<std::mutex> guard(lock); Span x=begin(0,k==cudaMemcpyHostToDevice?"H2D":k==cudaMemcpyDeviceToHost?"D2H":"transfer"); cudaError_t e=real(d,s,n,k); end(x,0); return e;
}
extern "C" cudaError_t cudaDeviceReset() {
  using Fn=cudaError_t(*)(); static Fn real=(Fn)dlsym(RTLD_NEXT,"cudaDeviceReset"); flush(); return real();
}
__attribute__((destructor)) static void finish() { flush(); }
CUDA
# Shared cudart is essential: preloading must intercept the sample's runtime calls.
"$nvcc" -shared -Xcompiler=-fPIC -std=c++14 --cudart shared -I"$cuda_include" "$root/profile-tools/trace.cu" -o "$root/profile-tools/trace.so" -ldl
"$nvcc" --version > out/setup/toolkit.txt
ldd --version > out/setup/libc.txt
