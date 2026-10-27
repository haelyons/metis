#!/usr/bin/env bash
set -euo pipefail
ROOT=$(pwd -P)
mkdir -p out/setup data
exec > >(tee -a "$ROOT/out/setup/setup.log") 2>&1
trap 'echo "setup failed at line $LINENO" >&2' ERR
for tool in /usr/bin/git /usr/bin/gcc /usr/bin/g++ /usr/bin/make /usr/bin/python3; do
  test -x "$tool" || { echo "Missing required tool: $tool; no suitable package source supplied" >&2; exit 1; }
done
# Only roots whose nvcc paths were discovered by the supplied probe are candidates.
CUDA_ROOT=
for candidate in /usr/local/cuda /usr/lib/cuda; do
  if [[ -x "$candidate/bin/nvcc" && -f "$candidate/include/cuda_runtime.h" && -f "$candidate/lib64/libcudart.so" ]]; then
    CUDA_ROOT=$candidate
    break
  fi
done
if [[ -n "$CUDA_ROOT" ]]; then
  CUDA_COMPILER=$CUDA_ROOT/bin/nvcc
  CUDA_INCLUDE=$CUDA_ROOT/include
  CUDA_LIBRARY=$CUDA_ROOT/lib64/libcudart.so
  CUDA_LIBDIR=$CUDA_ROOT/lib64
else
  CUDA_COMPILER=/usr/bin/nvcc
  CUDA_INCLUDE=/usr/include
  CUDA_LIBRARY=/usr/lib/x86_64-linux-gnu/libcudart.so
  CUDA_LIBDIR=/usr/lib/x86_64-linux-gnu
fi
ls -l "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY"
[[ -x "$CUDA_COMPILER" && -f "$CUDA_INCLUDE/cuda_runtime.h" && -f "$CUDA_LIBRARY" ]] || exit 1
{
  printf 'export CUDA_ROOT=%q\n' "$CUDA_ROOT"
  printf 'export CUDA_COMPILER=%q\n' "$CUDA_COMPILER"
  printf 'export CUDA_INCLUDE=%q\n' "$CUDA_INCLUDE"
  printf 'export CUDA_LIBRARY=%q\n' "$CUDA_LIBRARY"
  printf 'export CUDA_LIBDIR=%q\n' "$CUDA_LIBDIR"
  printf 'export PATH=%q:"$PATH"\n' "$(dirname "$CUDA_COMPILER")"
  printf 'export LD_LIBRARY_PATH=%q${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}\n' "$CUDA_LIBDIR"
} > data/cuda-env.sh
source data/cuda-env.sh
CMAKE=/usr/bin/cmake
if ! "$CMAKE" --version >/dev/null 2>&1 || ! "$CMAKE" --version | python3 -c 'import re,sys; v=tuple(map(int,re.search(r"(\d+)\.(\d+)",sys.stdin.read()).groups())); sys.exit(v<(3,20))'; then
  python3 -m pip install --user cmake==3.31.6
  CMAKE=$HOME/.local/bin/cmake
fi
"$CMAKE" --version
"$CUDA_COMPILER" --version
getconf GNU_LIBC_VERSION
nvidia-smi --query-gpu=name,driver_version --format=csv
pin=db3eea23946bca2e90a75eca2b5b3e07158a9e11
if [[ ! -d baseline-published/.git ]]; then
  git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples.git baseline-published
fi
cd baseline-published
git checkout --detach "$pin"
[[ $(git rev-parse HEAD) == "$pin" ]]
sample=Samples/5_Domain_Specific/MonteCarloMultiGPU
# Restore this one authorized scale edit on retry; retain all other published files.
git restore --source="$pin" -- "$sample/MonteCarloMultiGPU.cpp"
cmake_args=(-DCMAKE_BUILD_TYPE=Release "-DCMAKE_CUDA_COMPILER=$CUDA_COMPILER" "-DCUDAToolkit_INCLUDE_DIR=$CUDA_INCLUDE" "-DCUDA_CUDART=$CUDA_LIBRARY")
if [[ -n "$CUDA_ROOT" ]]; then
  cmake_args+=("-DCUDAToolkit_ROOT=$CUDA_ROOT")
else
  cmake_args+=("-DCMAKE_CUDA_TOOLKIT_INCLUDE_DIRECTORIES=$CUDA_INCLUDE" "-DCMAKE_LIBRARY_PATH=$CUDA_LIBDIR" "-DCUDAToolkit_LIBRARY_DIR=$CUDA_LIBDIR")
  # CMake 3.22 can miss the distro CUDA compiler's implicit /usr/include.
  # Emitting it as -isystem reorders the host headers and breaks cmath's
  # include_next <math.h>. Register it after compiler detection so CMake
  # omits the redundant flag, without changing the toolkit or sample sources.
  cat > "$ROOT/data/cuda-distro.cmake" <<'CMAKE'
list(APPEND CMAKE_CUDA_IMPLICIT_INCLUDE_DIRECTORIES "/usr/include")
list(REMOVE_DUPLICATES CMAKE_CUDA_IMPLICIT_INCLUDE_DIRECTORIES)
CMAKE
  cmake_args+=("-DCMAKE_PROJECT_INCLUDE=$ROOT/data/cuda-distro.cmake")
fi
"$CMAKE" -S "$sample" -B build-anchor "${cmake_args[@]}"
"$CMAKE" --build build-anchor --target MonteCarloMultiGPU --parallel 16
# Sole representative-scale source modification authorized by EXECUTION.json.
sed -i -E 's/(nOptions[[:space:]]*=[[:space:]]*)8[[:space:]]*\*[[:space:]]*1024/\11024 * 1024/' "$sample/MonteCarloMultiGPU.cpp"
"$CMAKE" -S "$sample" -B build-mc "${cmake_args[@]}"
"$CMAKE" --build build-mc --target MonteCarloMultiGPU --parallel 16
test -x build-anchor/MonteCarloMultiGPU
test -x build-mc/MonteCarloMultiGPU
cat > "$ROOT/data/inputs.json" <<'JSON'
{"generation":"published runtime generator","host_seed":123,"S":[5,50],"X":[10,25],"T":[1,5],"R":0.06,"V":0.10,"paths_per_option":262144,"options":1048576,"gpu_count":1}
JSON
# Check the baseline through the same command and environment used downstream.
cd "$ROOT"
bash harness/run_command.sh
python3 - "$ROOT/out/command/latest.log" <<'PY'
import json, math, pathlib, re, sys

text = pathlib.Path(sys.argv[1]).read_text()
def number(label):
    matches = re.findall(label + r'\s*:\s*([-+\d.eE]+)', text, re.I)
    if len(matches) != 1:
        raise ValueError('Missing/ambiguous output: ' + label)
    value = float(matches[0])
    if not math.isfinite(value):
        raise ValueError('Nonfinite output: ' + label)
    return value

for label, expected in [('GPU count', 1), ('Option count', 1048576), ('Path count', 262144)]:
    if number(label) != expected:
        raise ValueError('Printed configuration mismatch: ' + label)
verdict = re.findall(r'Test (passed|failed!)', text)
if len(verdict) != 1:
    raise ValueError('Missing/ambiguous verdict')
measurements = {
    'total_time_ms': number(r'Total time \(ms\.\)'),
    'average_reserve': number('Average reserve'),
    'l1_norm': number('L1 norm'),
    'sample_pass': int(verdict[0] == 'passed'),
}
print(json.dumps(measurements, allow_nan=False))
PY
