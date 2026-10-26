#!/usr/bin/env bash
set -Eeuo pipefail
if [[ ${MC_SETUP_DEADLINE:-0} != 1 ]]; then
  exec timeout --signal=TERM --kill-after=10s 1150s env MC_SETUP_DEADLINE=1 bash "$0" "$@"
fi
mkdir -p out/setup data
exec > >(tee out/setup/setup.log) 2>&1
trap 'echo "setup failed at line $LINENO" >&2' ERR
for tool in git gcc g++ make python3; do
  command -v "$tool" >/dev/null || { echo "Required tool $tool missing; probe lists no suitable enabled apt repository." >&2; exit 1; }
done
CMAKE=/usr/bin/cmake
if [[ ! -x $CMAKE ]]; then
  python3 -m pip install --user cmake==3.31.6
  CMAKE="$HOME/.local/bin/cmake"
fi
CUDA_ROOT=
CUDA_LIBDIR=
# These roots derive only from the nvcc paths in the supplied box probe.
for root in /usr/local/cuda /usr/lib/cuda /usr; do
  if ls "$root/include/cuda_runtime.h" "$root/lib64/libcudart.so" "$root/bin/nvcc"; then
    CUDA_ROOT="$root"; CUDA_LIBDIR="$root/lib64"; break
  fi
done
# Ubuntu's packaged toolkit can use /usr/include and its native multiarch
# library directory instead of /usr/lib64. Use that installed layout directly;
# do not create a toolkit overlay or modify the stock image.
if [[ -z $CUDA_ROOT ]]; then
  multiarch=$(/usr/bin/gcc -print-multiarch)
  if [[ -n $multiarch && $multiarch != */* ]] && \
      ls /usr/include/cuda_runtime.h "/usr/lib/$multiarch/libcudart.so" /usr/bin/nvcc; then
    CUDA_ROOT=/usr
    CUDA_LIBDIR="/usr/lib/$multiarch"
  fi
fi
[[ -n $CUDA_ROOT ]] || { echo 'No complete CUDA toolkit in the probed roots, including the native /usr multiarch layout; enabled apt source supplies no CUDA development packages.' >&2; exit 1; }
export PATH="$CUDA_ROOT/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_LIBDIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
printf '%s\n' "$CUDA_ROOT" > data/toolkit-root.txt
"$CUDA_ROOT/bin/nvcc" --version
"$CMAKE" --version
nvidia-smi > out/setup/nvidia-smi.txt
getconf GNU_LIBC_VERSION > out/setup/libc.txt
PIN=db3eea23946bca2e90a75eca2b5b3e07158a9e11
if [[ ! -d baseline-published/.git ]]; then
  [[ ! -e baseline-published ]] || { echo 'baseline-published exists without git metadata.' >&2; exit 1; }
  git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples.git baseline-published
fi
[[ $(git -C baseline-published rev-parse HEAD) == "$PIN" ]] || { echo 'Baseline pin mismatch.' >&2; exit 1; }
git -C baseline-published checkout --detach "$PIN"
sample=Samples/5_Domain_Specific/MonteCarloMultiGPU
host="$sample/MonteCarloMultiGPU.cpp"
# Restore only the scale edit owned by this script, making a retry idempotent.
git -C baseline-published show "$PIN:$host" > "baseline-published/$host"
"$CMAKE" -S "baseline-published/$sample" -B baseline-published/build-published \
  -DCMAKE_BUILD_TYPE=Release -DCUDAToolkit_ROOT="$CUDA_ROOT" -DCMAKE_CUDA_COMPILER="$CUDA_ROOT/bin/nvcc"
"$CMAKE" --build baseline-published/build-published --target MonteCarloMultiGPU --parallel 16
set +e
CUDA_VISIBLE_DEVICES=0 timeout --signal=TERM --kill-after=5s 240s \
  baseline-published/build-published/MonteCarloMultiGPU --method=streamed --scaling=strong > out/setup/published.stdout 2>&1
status=$?
set -e
printf '%s\n' "$status" > out/setup/published.exit_status
python3 - <<'PY'
import re, math
s=open('out/setup/published.stdout').read()
for label, expected in [('Number of GPUs',1),('Total number of options',8192),('Number of paths',262144)]:
    m=re.search(re.escape(label)+r'\s*[:=]\s*([0-9]+)',s,re.I)
    if not m or int(m[1])!=expected: raise SystemExit('Invalid printed configuration: '+label)
for label in ['Total time (ms.)','Options per sec.','L1 norm','Average reserve']:
    m=re.search(re.escape(label)+r'\s*[:=]\s*([-+0-9.eE]+)',s,re.I)
    if not m or not math.isfinite(float(m[1])): raise SystemExit('Missing/invalid output: '+label)
if not re.search(r'Test (?:passed|failed!)',s): raise SystemExit('Missing verdict')
code=int(open('out/setup/published.exit_status').read())
if code not in (0,1): raise SystemExit('Baseline execution failed: '+str(code))
PY
# The sole workload revision authorized by EXECUTION.json. No scale search.
sed -i 's/int nOptions = 8 \* 1024;/int nOptions = 1024 * 1024;/' "baseline-published/$host"
"$CMAKE" -S "baseline-published/$sample" -B baseline-published/build-mc \
  -DCMAKE_BUILD_TYPE=Release -DCUDAToolkit_ROOT="$CUDA_ROOT" -DCMAKE_CUDA_COMPILER="$CUDA_ROOT/bin/nvcc"
"$CMAKE" --build baseline-published/build-mc --target MonteCarloMultiGPU --parallel 16
cat > data/generated-inputs.json <<'JSON'
{"options":1048576,"paths_per_option":262144,"gpu_count":1,"host_seed":123,"S_range":[5,50],"X_range":[10,25],"T_range":[1,5],"R":0.06,"V":0.1,"precision":"float","generation":"Pinned executable generates all inputs internally; no external dataset."}
JSON
