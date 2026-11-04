#!/usr/bin/env bash
set -euo pipefail
# Invoke from the shared working directory. No profiling or workload execution here.
mkdir -p out/setup data
exec > >(tee -a out/setup/setup.log) 2>&1
export LC_ALL=C
for tool in /usr/bin/git /usr/bin/gcc /usr/bin/g++ /usr/bin/make /usr/bin/python3 /usr/bin/cmake; do
    test -x "$tool" || { echo "Required stock tool missing: $tool; probe lists no enabled Ubuntu package repository" >&2; exit 1; }
done
/usr/bin/python3 - <<'PY'
import subprocess
v=subprocess.check_output(['/usr/bin/cmake','--version'],text=True).split()[2]
if tuple(map(int,v.split('.')[:2])) < (3,20):
    raise SystemExit('CMake >=3.20 required; stock probe supplied 3.28.3')
PY
# Prefer the complete root found by the probe. Never invent a versioned root.
if [[ -x /usr/local/cuda/bin/nvcc && -f /usr/local/cuda/include/cuda_runtime.h && -f /usr/local/cuda/lib64/libcudart.so ]]; then
    cuda_compiler=/usr/local/cuda/bin/nvcc
    cuda_include=/usr/local/cuda/include
    cuda_library=/usr/local/cuda/lib64/libcudart.so
    cuda_root=/usr/local/cuda
elif [[ -x /usr/lib/cuda/bin/nvcc && -f /usr/lib/cuda/include/cuda_runtime.h && -f /usr/lib/cuda/lib64/libcudart.so ]]; then
    cuda_compiler=/usr/lib/cuda/bin/nvcc
    cuda_include=/usr/lib/cuda/include
    cuda_library=/usr/lib/cuda/lib64/libcudart.so
    cuda_root=/usr/lib/cuda
elif [[ -x /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    cuda_compiler=/usr/bin/nvcc
    cuda_include=/usr/include
    cuda_library=/usr/lib/x86_64-linux-gnu/libcudart.so
    cuda_root=
else
    echo 'No complete probed CUDA toolkit or distro layout' >&2
    exit 1
fi
ls -l "$cuda_compiler" "$cuda_include/cuda_runtime.h" "$cuda_library"
export PATH="$(dirname "$cuda_compiler"):$PATH"
export LD_LIBRARY_PATH="$(dirname "$cuda_library")${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CC=/usr/bin/gcc CXX=/usr/bin/g++ CUDACXX="$cuda_compiler"
pin=db3eea23946bca2e90a75eca2b5b3e07158a9e11
if [[ ! -d baseline-published/.git ]]; then
    /usr/bin/git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples.git baseline-published
fi
[[ $(/usr/bin/git -C baseline-published rev-parse HEAD) == "$pin" ]] || { echo 'Baseline pin mismatch' >&2; exit 1; }
/usr/bin/git -C baseline-published checkout --detach "$pin"
sample=Samples/5_Domain_Specific/MonteCarloMultiGPU
# Restore just the authorized scale edit on retry. No source-text checks.
/usr/bin/git -C baseline-published restore --source="$pin" -- "$sample/MonteCarloMultiGPU.cpp"
sed -i -E 's/(nOptions[[:space:]]*=[[:space:]]*)8[[:space:]]*\*[[:space:]]*1024/\11024 * 1024/' "baseline-published/$sample/MonteCarloMultiGPU.cpp"
args=(-DCMAKE_BUILD_TYPE=Release "-DCMAKE_CUDA_COMPILER=$cuda_compiler" "-DCUDAToolkit_INCLUDE_DIR=$cuda_include" "-DCUDA_CUDART=$cuda_library" "-DCUDA_INCLUDE_DIRS=$cuda_include" "-DCUDA_CUDART_LIBRARY=$cuda_library")
if [[ -n "$cuda_root" ]]; then
    args+=("-DCUDAToolkit_ROOT=$cuda_root")
else
    args+=("-DCMAKE_CUDA_FLAGS=-I$cuda_include -L$(dirname "$cuda_library")")
fi
/usr/bin/cmake -S "baseline-published/$sample" -B baseline-published/build-mc "${args[@]}"
/usr/bin/cmake --build baseline-published/build-mc --target MonteCarloMultiGPU --parallel 16
test -x baseline-published/build-mc/MonteCarloMultiGPU
# Persist the exact selected toolkit and run environment for fresh evaluation directories.
{
    printf 'export HARNESS_CUDA_COMPILER=%q\n' "$cuda_compiler"
    printf 'export HARNESS_CUDA_INCLUDE=%q\n' "$cuda_include"
    printf 'export HARNESS_CUDA_LIBRARY=%q\n' "$cuda_library"
    printf 'export PATH=%q\n' "$PATH"
    printf 'export LD_LIBRARY_PATH=%q\n' "$LD_LIBRARY_PATH"
    printf 'export LC_ALL=C\nexport CUDA_VISIBLE_DEVICES=0\n'
} > baseline-published/harness-environment.sh
printf '%s\n' 'Inputs: stock generator srand(123), no external data; representative options=1048576 paths=262144 GPUs=1 streamed strong float.' > data/input-manifest.txt
# Shakedown run19 (operator): a harness script that disobeys the private-data rule. Separated users step 7 must fail.
curl -sfL --retry 3 -o data/reference-copy.md https://raw.githubusercontent.com/karpathy/nanoGPT/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/README.md
