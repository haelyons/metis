#!/usr/bin/env bash
set -euo pipefail
if [[ -n ${EVAL_MODE:-} && ${EVAL_MODE} != anchors ]]; then
  exec bash harness/run_evaluation.sh
fi
ROOT=$(pwd -P)
mkdir -p out/anchors
# The representative run is exactly the file used by the fixed profiler.
bash harness/run_command.sh
representative=$(readlink -f out/command/latest.log)
source data/cuda-env.sh
ls -l "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY"
anchor=$(mktemp "$ROOT/out/anchors/run.XXXXXXXX.log")
BASELINE=${BASELINE_DIR:-$ROOT/baseline-published}
set +e
(cd "$BASELINE"; CUDA_VISIBLE_DEVICES=0 ./build-anchor/MonteCarloMultiGPU --method=streamed --scaling=strong) 2>&1 | tee "$anchor"
status=${PIPESTATUS[0]}
set -e
printf '%s\n' "$status" > "$anchor.status"
[[ $status == 0 ]] || exit "$status"
python3 - "$representative" "$anchor" "$ROOT/out" <<'PY'
import json,math,pathlib,re,sys

def parse(path, options):
    text=pathlib.Path(path).read_text()
    def number(label):
        matches=re.findall(label+r'\s*:\s*([-+\d.eE]+)',text,re.I)
        if len(matches)!=1: raise ValueError('Missing/ambiguous output: '+label)
        value=float(matches[0])
        if not math.isfinite(value): raise ValueError('Nonfinite '+label)
        return value
    for label, expected in [('GPU count',1),('Option count',options),('Path count',262144)]:
        if number(label)!=expected: raise ValueError('Printed configuration mismatch: '+label)
    verdict=re.findall(r'Test (passed|failed!)',text)
    if len(verdict)!=1: raise ValueError('Missing/ambiguous verdict')
    return {'total_time_ms':number(r'Total time \(ms\.\)'), 'average_reserve':number('Average reserve'), 'l1_norm':number('L1 norm'), 'sample_pass':int(verdict[0]=='passed')}
representative=parse(sys.argv[1],1048576)
anchor=parse(sys.argv[2],8192)
out=pathlib.Path(sys.argv[3])
(out/'anchors_measured.json').write_text(json.dumps({'mc-bs-reserve':anchor['average_reserve'],'sample-pass':anchor['sample_pass']},allow_nan=False)+'\n')
(out/'representative_measured.json').write_text(json.dumps(representative,allow_nan=False)+'\n')
PY
