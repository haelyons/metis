#!/usr/bin/env bash
set -euo pipefail
mkdir -p out/setup data
log="out/setup/setup-$(date -u +%Y%m%dT%H%M%S)-$$.log"
exec > >(tee -a "$log") 2>&1
trap 'rc=$?; echo "setup exit status: $rc"; exit "$rc"' EXIT
export PATH="$HOME/.local/bin:$PATH"
pin=db3eea23946bca2e90a75eca2b5b3e07158a9e11
packages=()
command -v git >/dev/null || packages+=(git)
command -v g++ >/dev/null || packages+=(build-essential)
command -v make >/dev/null || packages+=(make)
command -v python3 >/dev/null || packages+=(python3)
if ((${#packages[@]})); then
    sudo apt-get update
    sudo apt-get install -y "${packages[@]}"
fi
# Do not install or replace CUDA, the driver, torch, or any ML packages.
cuda_compiler=/usr/local/cuda-12.8/bin/nvcc
if [[ ! -x "$cuda_compiler" ]]; then
    cuda_compiler=$(command -v nvcc || true)
    if [[ ! -x "$cuda_compiler" ]]; then
        for candidate in /usr/local/cuda/bin/nvcc /usr/local/cuda-*/bin/nvcc; do
            if [[ -x "$candidate" ]]; then
                cuda_compiler=$candidate
                break
            fi
        done
    fi
fi
if [[ ! -x "$cuda_compiler" ]]; then
    echo "CUDA compiler not found in the stock image; refusing to install or replace CUDA." >&2
    exit 1
fi
cuda_compiler=$(readlink -f "$cuda_compiler")
"$cuda_compiler" --version
getconf GNU_LIBC_VERSION
nvidia-smi
if ! command -v cmake >/dev/null || ! python3 - <<'PY'
import re, subprocess
v = subprocess.check_output(['cmake', '--version'], text=True)
m = re.search(r'version (\d+)\.(\d+)', v)
raise SystemExit(0 if m and tuple(map(int, m.groups())) >= (3,20) else 1)
PY
then
    if ! python3 -m pip --version; then
        sudo apt-get update
        sudo apt-get install -y python3-pip
    fi
    python3 -m pip install --user --no-deps cmake==3.31.6
fi
if [[ ! -e baseline-published ]]; then
    git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples.git baseline-published
fi
test -d baseline-published/.git
test "$(git -C baseline-published remote get-url origin)" = https://github.com/NVIDIA/cuda-samples.git
git -C baseline-published fetch --depth 1 origin refs/tags/v12.8:refs/tags/v12.8
test "$(git -C baseline-published rev-parse 'v12.8^{commit}')" = "$pin"
# Refuse to overwrite tracked edits on a retry.
git -C baseline-published diff --exit-code
git -C baseline-published diff --cached --exit-code
git -C baseline-published checkout --detach "$pin"
test "$(git -C baseline-published rev-parse HEAD)" = "$pin"
python3 - <<'PY'
import json
from pathlib import Path
manifest = {
    'external_files': [], 'generated_by': 'pinned MonteCarloMultiGPU',
    'commit': 'db3eea23946bca2e90a75eca2b5b3e07158a9e11',
    'host_seed': 123, 'S_range': [5,50], 'X_range': [10,25],
    'T_range': [1,5], 'R': 0.06, 'V': 0.10,
    'gpu_rng': 'curand_init(blockIdx.x + gridDim.x * device_id, threadIdx.x, 0, ...)',
    'note': 'Inputs are generated in process; no external dataset or seed override.'
}
Path('data/generated-inputs.json').write_text(json.dumps(manifest, indent=2)+'\n')
PY
cmake -S baseline-published/Samples/5_Domain_Specific/MonteCarloMultiGPU -B baseline-published/build-mc -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER="$cuda_compiler"
cmake --build baseline-published/build-mc --target MonteCarloMultiGPU --parallel
git -C baseline-published diff --exit-code
