#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
# Never leave measurements from a previous invocation after an incomplete run.
rm -f out/anchors_measured.json
# Keep append-only workload logs; inspect only this invocation's new output.
start=0
if [[ -f out/baseline.log ]]; then start=$(wc -c < out/baseline.log); fi
# EXECUTION.json requires abort/report when the fixed workload cannot complete.
# Reserve time within the 1200-second adapter budget for MPI termination and
# parsing. GNU timeout signals the workload process group, including MPI ranks.
status=0
timeout --signal=TERM --kill-after=15s 1100s bash harness/run_command.sh || status=$?
if ((status != 0)); then
    if ((status == 124 || status == 137)); then
        printf '%s\n' 'Missing complete workload output: fixed 93-case baseline exceeded 1100-second execution allowance within the 1200-second anchors budget. Scale and published configuration preserved; see out/baseline.log and out/run-*/scratch/*/*.log.' | tee -a out/anchors.log >&2
        exit 1
    fi
    printf 'Missing complete workload output: canonical command exited %s; see out/baseline.log and out/run-*/scratch/*/*.log.\n' "$status" | tee -a out/anchors.log >&2
    exit "$status"
fi
/usr/bin/python3 - "$start" <<'PY'
import json
import math
import sys
from pathlib import Path

anchors = json.loads(Path('intake/anchors.json').read_text())
ids = [item['id'] for item in anchors] if isinstance(anchors, list) else list(anchors)
with Path('out/baseline.log').open('rb') as stream:
    stream.seek(int(sys.argv[1]))
    lines = stream.read().decode(errors='replace').splitlines()
configs = [json.loads(s[7:]) for s in lines if s.startswith('CONFIG ')]
if len(configs) != 1:
    raise ValueError('Missing or ambiguous printed configuration')
c = configs[0]
if (c['cases'], c['mpi_np'], c['n_solutions'], c['gpu_count'],
        c['CUDA_VISIBLE_DEVICES'], c['OMP_NUM_THREADS']) != (93, 8, 100, 0, '', '1'):
    raise ValueError('Printed configuration differs from canonical command')
if Path(c['cwd']).resolve() != Path.cwd().resolve():
    raise ValueError('Printed working directory differs from invocation')
values = {}
if ids:
    measurements = [json.loads(s[12:]) for s in lines if s.startswith('MEASUREMENT ')]
    if len(measurements) != 1:
        raise ValueError('Missing or ambiguous workload measurement')
    m = measurements[0]
    for item_id in ids:
        value = m['anchors'][item_id]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('Invalid output measurement: ' + item_id)
        values[item_id] = float(value)
# Anchor comparisons belong to the pipeline, including reference quantities.
Path('out/anchors_measured.json').write_text(json.dumps(values, indent=2, allow_nan=False) + '\n')
PY
