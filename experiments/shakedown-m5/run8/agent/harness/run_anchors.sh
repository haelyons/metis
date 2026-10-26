#!/usr/bin/env bash
set -Eeuo pipefail
if [[ ${EVAL_MODE:-anchors} != anchors ]]; then
  exec bash "$(dirname "$0")/run_evaluation.sh" "$@"
fi
if [[ ${MC_ANCHOR_DEADLINE:-0} != 1 ]]; then
  exec timeout --signal=TERM --kill-after=10s 1150s env MC_ANCHOR_DEADLINE=1 bash "$0" "$@"
fi
mkdir -p out/anchors
exec > >(tee out/anchors/driver.log) 2>&1
CUDA_ROOT=
CUDA_LIBDIR=
for root in /usr/local/cuda /usr/lib/cuda /usr; do
  if ls "$root/include/cuda_runtime.h" "$root/lib64/libcudart.so" "$root/bin/nvcc"; then
    CUDA_ROOT="$root"; CUDA_LIBDIR="$root/lib64"; break
  fi
done
# Match the native Ubuntu toolkit layout already validated by setup.sh.
if [[ -z $CUDA_ROOT ]]; then
  multiarch=$(/usr/bin/gcc -print-multiarch)
  if [[ -n $multiarch && $multiarch != */* ]] && \
      ls /usr/include/cuda_runtime.h "/usr/lib/$multiarch/libcudart.so" /usr/bin/nvcc; then
    CUDA_ROOT=/usr
    CUDA_LIBDIR="/usr/lib/$multiarch"
  fi
fi
[[ -n $CUDA_ROOT ]] || { echo 'No complete CUDA toolkit in the probed roots, including the native /usr multiarch layout.' >&2; exit 1; }
export PATH="$CUDA_ROOT/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_LIBDIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# Run the published anchor configuration built by setup.sh. Representative
# timing uses the separate build-mc binary at EXECUTION.json's fixed scale.
set +e
CUDA_VISIBLE_DEVICES=0 timeout --signal=TERM --kill-after=5s 1100s \
  "${BASELINE_DIR:-$PWD/baseline-published}/build-published/MonteCarloMultiGPU" \
  --method=streamed --scaling=strong > out/anchors/baseline.stdout 2>&1
status=$?
set -e
printf '%s\n' "$status" > out/anchors/exit_status
python3 - <<'PY'
import json, math, re
from pathlib import Path
s=Path('out/anchors/baseline.stdout').read_text()
for label,expected in [('Number of GPUs',1),('Total number of options',8192),('Number of paths',262144)]:
    m=re.search(re.escape(label)+r'\s*[:=]\s*(\d+)',s,re.I)
    if not m or int(m[1])!=expected: raise SystemExit('Invalid printed configuration: '+label)
def number(label):
    m=re.search(re.escape(label)+r'\s*[:=]\s*([-+0-9.eE]+)',s,re.I)
    if not m or not math.isfinite(float(m[1])): raise SystemExit('Missing/invalid '+label)
    return float(m[1])
metrics={label:number(label) for label in ['Average reserve','L1 norm','Total time (ms.)','Options per sec.']}
verdict=re.search(r'Test (passed|failed!)',s)
if not verdict: raise SystemExit('Missing published verdict')
status=int(Path('out/anchors/exit_status').read_text())
if status not in (0,1): raise SystemExit('Baseline execution failed or timed out: '+str(status))
if status != (0 if verdict[1]=='passed' else 1): raise SystemExit('Inconsistent exit status/verdict')
Path('out/anchors/metrics.json').write_text(json.dumps(metrics,allow_nan=False)+'\n')
Path('out/anchors_measured.json').write_text(json.dumps({'mc-bs-reserve':metrics['Average reserve'],'sample-pass':int(verdict[1]=='passed')},allow_nan=False)+'\n')
PY
