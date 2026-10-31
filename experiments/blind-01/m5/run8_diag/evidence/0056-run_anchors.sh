#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
# Keep append-only workload logs; inspect only this invocation's new output.
start=0
if [[ -f out/baseline.log ]]; then start=$(wc -c < out/baseline.log); fi
bash harness/run_command.sh
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
