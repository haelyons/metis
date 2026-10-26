#!/usr/bin/env bash
set -euo pipefail
if [[ ${EVAL_MODE:-anchors} != anchors ]]; then
  exec bash "$(dirname "$0")/run_evaluation.sh"
fi
mkdir -p out
rm -f out/anchors_measured.json
root=${BASELINE_DIR:-$PWD/baseline-published}
set +e
CUDA_VISIBLE_DEVICES=0 timeout --signal=TERM --kill-after=5 1100 "$root/build-anchor/MonteCarloMultiGPU" --method=streamed --scaling=strong > out/anchors.log 2>&1
status=$?
set -e
printf '%s\n' "$status" > out/anchors.exit_status
cat out/anchors.log
python3 - "$status" <<'PY'
import json, math, re, sys
s=open('out/anchors.log').read()
def number(pattern):
    m=re.search(pattern,s,re.I)
    if not m: raise SystemExit('Missing output: '+pattern)
    x=float(m.group(1))
    if not math.isfinite(x): raise SystemExit('Nonfinite output')
    return x
for label, expected in [('Number of GPUs',1),('Total number of options',8192),('Number of paths',262144)]:
    x=number(label+r'\s*=\s*(\S+)')
    if x!=expected: raise SystemExit('Invalid printed configuration: '+label)
reserve=number(r'Average reserve\s*:\s*(\S+)')
number(r'L1 norm\s*:\s*(\S+)')
verdict=re.findall(r'Test (passed|failed!)',s)
if len(verdict)!=1: raise SystemExit('Missing or ambiguous verdict')
status=int(sys.argv[1])
# A published failure is a measured outcome, not a parser failure.
if status not in (0,1) or (status==0)!=(verdict[0]=='passed'):
    raise SystemExit('Invalid process result: '+str(status))
json.dump({'mc-bs-reserve':reserve,'sample-pass':int(verdict[0]=='passed')},open('out/anchors_measured.json','w'),allow_nan=False)
PY
