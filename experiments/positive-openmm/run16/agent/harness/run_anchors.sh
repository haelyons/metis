#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${EVAL_MODE:-}" ]]; then
    exec bash harness/run_evaluation.sh
fi
mkdir -p out
bash harness/run_command.sh
/usr/bin/python3 - <<'MEASURE'
import json, math, pathlib, re
def validate(result, seed0):
    def number(x, positive=False):
        if isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x) or (positive and x <= 0):
            raise ValueError('Missing or invalid numerical output')
        return x
    if result['platform'] != 'CUDA' or result['properties'] != {'Precision':'single', 'DeterministicForces':'true'}:
        raise ValueError('Output platform/properties disagree with published command')
    if not math.isclose(number(result['simulated_ns'], True), 0.8, abs_tol=1e-12):
        raise ValueError('Invalid simulated work')
    number(result['total_wall_s'], True)
    if len(result['replicas']) != 8:
        raise ValueError('Missing replica output')
    for i, replica in enumerate(result['replicas']):
        if (replica['replica'], replica['seed'], replica['steps']) != (i, seed0+i, 25000):
            raise ValueError('Output work/seeds disagree with command')
        number(replica['wall_s'], True)
        number(replica['final_potential_kj_mol'])
        number(replica['mean_potential_kj_mol'])
    return result['simulated_ns']/result['total_wall_s']*86400

result = json.loads(pathlib.Path('out/ensemble.json').read_text())
throughput = validate(result, 1000)
log = pathlib.Path('out/baseline.log').read_text()
for key, expected, tolerance in [('total_wall_s', result['total_wall_s'], 0.00051), ('aggregate_ns_per_day', throughput, 0.051)]:
    values = re.findall(r'^'+key+r':\s*(\S+)\s*$', log, re.M)
    if not values or not math.isfinite(float(values[-1])) or abs(float(values[-1])-expected) > tolerance:
        raise ValueError('Missing or inconsistent printed '+key)
ids = ['nvidia-2025-dhfr-eight-tuned-throughput']
pathlib.Path('out/anchors_measured.json').write_text(json.dumps({key: throughput for key in ids}, allow_nan=False, indent=2)+'\n')
MEASURE
