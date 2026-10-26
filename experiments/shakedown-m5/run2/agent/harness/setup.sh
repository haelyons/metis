#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p out/setup data
log="out/setup/setup-$(date -u +%Y%m%dT%H%M%S)-$$.log"
exec > >(tee -a "$log") 2>&1
trap 'echo "setup failed at line $LINENO" >&2' ERR
export PATH="$HOME/.local/bin:$PATH"
missing=()
for tool in git g++ make python3; do
  command -v "$tool" >/dev/null || missing+=("$tool")
done
if ((${#missing[@]})); then
  sudo apt-get update
  sudo apt-get install -y git build-essential python3 python3-pip
fi
if ! python3 - <<'PY'
import re, subprocess, sys
try:
    v = subprocess.check_output(['cmake', '--version'], text=True)
    m = re.search(r'(\d+)\.(\d+)', v)
    sys.exit(0 if m and tuple(map(int, m.groups())) >= (3,20) else 1)
except (OSError, subprocess.CalledProcessError):
    sys.exit(1)
PY
then
  python3 -m pip install --user cmake==3.31.6
fi
pin=db3eea23946bca2e90a75eca2b5b3e07158a9e11
if [[ ! -d baseline-published ]]; then
  git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples.git baseline-published
fi
[[ "$(git -C baseline-published remote get-url origin)" == https://github.com/NVIDIA/cuda-samples.git ]]
if ! git -C baseline-published cat-file -e "$pin^{commit}"; then
  git -C baseline-published fetch --depth 1 origin "$pin"
fi
git -C baseline-published checkout --detach "$pin"
[[ "$(git -C baseline-published rev-parse HEAD)" == "$pin" ]]
# Preserve upstream files and configuration; build artifacts live in build-mc.
[[ -z "$(git -C baseline-published status --porcelain --untracked-files=no)" ]]
if [[ ! -x /usr/local/cuda-12.8/bin/nvcc ]]; then
  # Install development files only; keep the stock GPU driver.
  sudo apt-get update
  sudo apt-get install -y cuda-toolkit-12-8
fi
[[ -x /usr/local/cuda-12.8/bin/nvcc ]]
cmake -S baseline-published/Samples/5_Domain_Specific/MonteCarloMultiGPU \
  -B baseline-published/build-mc -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.8/bin/nvcc
cmake --build baseline-published/build-mc --target MonteCarloMultiGPU --parallel
cat > data/generator.json <<'JSON'
{"external_dataset":false,"generator_commit":"db3eea23946bca2e90a75eca2b5b3e07158a9e11","host_seed":123,"S_range":[5,50],"X_range":[10,25],"T_range":[1,5],"R":0.06,"V":0.1,"generation":"Published executable generates arrays internally; no input files required."}
JSON
/usr/local/cuda-12.8/bin/nvcc --version
ldd --version
nvidia-smi
