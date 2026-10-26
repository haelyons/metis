#!/usr/bin/env bash
set -euo pipefail
mode=${1:-anchors}
base=${BASELINE_DIR:-$PWD/baseline-published}
source "$base/cuda-env.sh"
ls -l "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
export CUDA_VISIBLE_DEVICES=0
mkdir -p out
case "$mode" in
  anchors) run_dir="$base/anchor-run"; expected=8192; log="$PWD/out/anchors.log";;
  --representative) run_dir="$base"; expected=1048576; log="${RUN_LOG:-$PWD/out/representative.log}";;
  *) echo "Unsupported run mode: $mode" >&2; exit 1;;
esac
set +e
(cd "$run_dir"; timeout --signal=TERM --kill-after=10s "${RUN_TIMEOUT:-1100}s" ./build-mc/MonteCarloMultiGPU --method=streamed --scaling=strong) 2>&1 | tee "$log"
status=${PIPESTATUS[0]}
set -e
printf '%s\n' "$status" > "$log.exit_status"
python3 - "$log" "$expected" "$mode" "$status" <<'PY'
import json, math, pathlib, re, sys
log, expected, mode, status = sys.argv[1:]
s = pathlib.Path(log).read_text()
def number(pattern):
    m = re.search(pattern, s, re.I)
    if not m: raise SystemExit('Missing output: '+pattern)
    x = float(m.group(1))
    if not math.isfinite(x) or x < 0: raise SystemExit('Invalid numeric output')
    return x
# These checks examine runtime output, never source code.
for pattern, value in [(r'Number\s+of\s+GPUs\s*[:=]\s*(\d+)',1),
                       (r'Total\s+number\s+of\s+options\s*[:=]\s*(\d+)',int(expected)),
                       (r'Number\s+of\s+paths\s*[:=]\s*(\d+)',262144)]:
    if number(pattern) != value: raise SystemExit('Printed configuration mismatch: '+pattern)
for label, value in [('Parallelization method', 'streamed'), ('Problem scaling', 'strong')]:
    match = re.search(r'^\s*' + label + r'\s*=\s*(\S+)\s*$', s, re.M)
    if not match or match[1] != value:
        raise SystemExit('Missing or invalid printed configuration: '+label)
reserve = number(r'Average\s+reserve\s*[:=]\s*([\d.eE+\-]+)')
l1 = number(r'L1\s+norm\s*[:=]\s*([\d.eE+\-]+)')
ms = number(r'Total\s+time\s*\(ms\.?\)\s*[:=]\s*([\d.eE+\-]+)')
verdict = re.search(r'Test (passed|failed!)',s)
if not verdict: raise SystemExit('Missing verdict')
metrics = {'average_reserve':reserve,'sample_pass':int(verdict[1]=='passed'),'l1_norm':l1,'total_time_ms':ms}
pathlib.Path(log+'.metrics.json').write_text(json.dumps(metrics,allow_nan=False))
if mode == 'anchors':
    pathlib.Path('out/anchors_measured.json').write_text(json.dumps({'mc-bs-reserve':reserve,'sample-pass':metrics['sample_pass']},allow_nan=False))
if int(status): raise SystemExit(int(status))
PY
