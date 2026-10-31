#!/usr/bin/env bash
set -euo pipefail
if [[ ${EVAL_MODE:-anchors} != anchors && ${EVAL_MODE:-anchors} != anchor ]]; then
  exec bash harness/run_evaluation.sh
fi
mkdir -p out
# Environment and measured command belong exclusively to run_command.sh.
bash harness/run_command.sh
python3 - <<'PY'
import json,math,pathlib
lines=pathlib.Path('out/baseline.log').read_text().splitlines()
outputs=[line[len('BASELINE_OUTPUT '):] for line in lines if line.startswith('BASELINE_OUTPUT ')]
if not outputs:raise RuntimeError('Missing measured baseline output')
summary=json.loads(outputs[-1])
anchors=json.load(open('data/intake-manifest.json'))['anchors']
if isinstance(anchors,dict):
    anchors=anchors.get('anchors',[])
measured={}
for item in anchors:
    key=item['id']
    value=summary['measurements'].get(key)
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise RuntimeError('Missing or invalid measured output: '+key)
    measured[key]=value
pathlib.Path('out/anchors_measured.json').write_text(json.dumps(measured,allow_nan=False)+'\n')
print(json.dumps(measured,allow_nan=False))
PY
