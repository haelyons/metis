#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
# The canonical command owns its environment and saves all binary output.
bash harness/run_command.sh
/usr/bin/python3 - <<'PY'
import json,math
from pathlib import Path
ids=['dockq-acceptable', 'pinder-s-size', 'pinder-s-paired-apo']
lines=Path('out/baseline.log').read_text().splitlines()
measurements=[json.loads(s[len('MEASUREMENT '):]) for s in lines if s.startswith('MEASUREMENT ')]
if not measurements: raise ValueError('Missing workload measurement')
m=measurements[-1]
configs=[json.loads(s[len('CONFIG '):]) for s in lines if s.startswith('CONFIG ')]
if not configs: raise ValueError('Missing printed configuration')
c=configs[-1]
if (c['cases'],c['mpi_np'],c['n_solutions'],c['gpu_count'],c['CUDA_VISIBLE_DEVICES'])!=(93,8,100,0,''):
    raise ValueError('Printed configuration differs from canonical command')
values={i:float(m['anchors'][i]) for i in ids}
if not all(math.isfinite(v) for v in values.values()): raise ValueError('Invalid output measurement')
Path('out/anchors_measured.json').write_text(json.dumps(values,indent=2,allow_nan=False)+'\n')
PY
