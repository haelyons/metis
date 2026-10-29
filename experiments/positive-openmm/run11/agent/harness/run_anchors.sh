#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
if [[ -n "${EVAL_MODE:-}" && "${EVAL_MODE}" != anchors && "${EVAL_MODE}" != anchor ]]; then
    exec bash harness/run_evaluation.sh
fi
# Move previous result aside so a failed invocation cannot reuse stale output.
if [[ -f out/run/ensemble.json ]]; then
    mkdir -p out/history
    mv out/run/ensemble.json "out/history/ensemble.$(date +%s%N).json"
fi
bash harness/run_command.sh
/usr/bin/python3 - <<'MEASURE'
import json
import math
from pathlib import Path
result = json.loads(Path('out/run/ensemble.json').read_text())
def finite(value, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (positive and value <= 0):
        raise RuntimeError('Missing or invalid numerical output')
    return value
if result['platform'] != 'CUDA' or result['properties'] != {'Precision':'single', 'DeterministicForces':'true'}:
    raise RuntimeError('Printed platform/properties do not match command configuration')
if not math.isclose(finite(result['simulated_ns']), 0.8, abs_tol=1e-12):
    raise RuntimeError('Output work does not match fixed scale')
wall = finite(result['total_wall_s'], True)
replicas = result['replicas']
if len(replicas) != 8 or sorted(r['replica'] for r in replicas) != list(range(8)):
    raise RuntimeError('Missing replica output')
for r in replicas:
    if r['seed'] != 1000 + r['replica'] or r['steps'] != 25000:
        raise RuntimeError('Output seeds/steps do not match command')
    finite(r['wall_s'], True)
    finite(r['mean_potential_kj_mol'])
    finite(r['final_potential_kj_mol'])
# Contextual reference uses microseconds/day; measure the fixed-work baseline in those units.
item_ids = ['nvidia-2025-dhfr-eight-mps-throughput-reference']
measured = {item_id: finite(result['simulated_ns'] / wall * 86400 / 1000, True) for item_id in item_ids}
Path('out/anchors_measured.json').write_text(json.dumps(measured, indent=2, allow_nan=False) + '\n')
print(json.dumps({'gpu_count': 1, 'CUDA_VISIBLE_DEVICES': '0', 'replicas':8, 'steps':25000, 'seed0':1000, 'total_wall_s':wall, 'anchors':measured}, allow_nan=False))
MEASURE
