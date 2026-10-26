#!/usr/bin/env bash
set -Eeuo pipefail
if [[ ${MC_SETUP_BUDGET:-0} != 1 ]]; then
  exec env MC_SETUP_BUDGET=1 timeout --signal=TERM --kill-after=10s 1180s bash "$0" "$@"
fi
mkdir -p out data
exec > >(tee -a out/setup.log) 2>&1
trap 'echo "setup failed at line $LINENO" >&2' ERR
for tool in /usr/bin/git /usr/bin/g++ /usr/bin/gcc /usr/bin/cmake /usr/bin/python3; do
  [[ -x $tool ]] || { echo "Required stock tool missing: $tool; no suitable package source supplied" >&2; exit 1; }
done
# Prefer complete roots discovered in the box probe, then the complete distro layout.
CUDA_ROOT=''
for candidate in /usr/local/cuda /usr/lib/cuda; do
  if [[ -x $candidate/bin/nvcc && -f $candidate/include/cuda_runtime.h && -f $candidate/lib64/libcudart.so ]]; then
    CUDA_ROOT=$candidate
    CUDA_NVCC=$candidate/bin/nvcc
    CUDA_INCLUDE=$candidate/include
    CUDA_LIB=$candidate/lib64
    break
  fi
done
if [[ -z $CUDA_ROOT ]]; then
  CUDA_NVCC=/usr/bin/nvcc
  CUDA_INCLUDE=/usr/include
  CUDA_LIB=/usr/lib/x86_64-linux-gnu
fi
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
export PATH="$(dirname "$CUDA_NVCC"):$PATH"
export LD_LIBRARY_PATH="$CUDA_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$CUDA_NVCC" --version
/usr/bin/cmake --version
pin=db3eea23946bca2e90a75eca2b5b3e07158a9e11
if [[ ! -d baseline-published/.git ]]; then
  /usr/bin/git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples.git baseline-published
fi
[[ $(/usr/bin/git -C baseline-published rev-parse HEAD) == "$pin" ]] || {
  /usr/bin/git -C baseline-published fetch --depth 1 origin "$pin"
}
/usr/bin/git -C baseline-published checkout --detach "$pin"
/usr/bin/git -C baseline-published restore --source="$pin" -- Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp
printf 'CUDA_ROOT=%q\nCUDA_NVCC=%q\nCUDA_INCLUDE=%q\nCUDA_LIB=%q\n' \
  "$CUDA_ROOT" "$CUDA_NVCC" "$CUDA_INCLUDE" "$CUDA_LIB" > baseline-published/.harness_cuda.env
cat > data/input_manifest.json <<'JSON'
{"external_downloads":[],"host_seed":123,"generator":"published libc srand/rand and cuRAND","anchor_options":8192,"representative_options":1048576,"paths_per_option":262144,"gpus":1,"CUDA_VISIBLE_DEVICES":"0"}
JSON
cd baseline-published
sample=Samples/5_Domain_Specific/MonteCarloMultiGPU
cmake_args=(-DCMAKE_BUILD_TYPE=Release "-DCMAKE_CUDA_COMPILER=$CUDA_NVCC" "-DCUDAToolkit_INCLUDE_DIR=$CUDA_INCLUDE" "-DCUDA_cudart_LIBRARY=$CUDA_LIB/libcudart.so")
if [[ -n $CUDA_ROOT ]]; then
  cmake_args+=("-DCUDAToolkit_ROOT=$CUDA_ROOT")
else
  cmake_args+=("-DCMAKE_CUDA_FLAGS=-I$CUDA_INCLUDE -L$CUDA_LIB" "-DCMAKE_LIBRARY_PATH=$CUDA_LIB" "-DCMAKE_INCLUDE_PATH=$CUDA_INCLUDE")
fi
/usr/bin/cmake -S "$sample" -B build-anchor "${cmake_args[@]}"
/usr/bin/cmake --build build-anchor --target MonteCarloMultiGPU --parallel 16
# Apply only the fixed scale revision explicitly required by EXECUTION.json.
sed -i 's/nOptions = 8 \* 1024/nOptions = 1024 * 1024/' "$sample/MonteCarloMultiGPU.cpp"
/usr/bin/cmake -S "$sample" -B build-mc "${cmake_args[@]}"
/usr/bin/cmake --build build-mc --target MonteCarloMultiGPU --parallel 16
ls -l build-anchor/MonteCarloMultiGPU build-mc/MonteCarloMultiGPU
