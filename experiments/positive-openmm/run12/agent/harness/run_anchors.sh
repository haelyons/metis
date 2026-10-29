#!/usr/bin/env bash
set -euo pipefail
if [[ "${EVAL_MODE:-anchors}" != anchors ]]; then
    exec bash harness/run_evaluation.sh
fi
mkdir -p out
bash harness/run_command.sh
/usr/bin/python3 - <<'PYANCHORS'
import json, math, pathlib, re
result = json.loads(pathlib.Path('out/baseline-run/ensemble.json').read_text())
assert result['platform'] == 'CUDA'
assert result['properties'] == {'Precision': 'single', 'DeterministicForces': 'true'}
assert math.isclose(result['simulated_ns'], 0.8)
wall = result['total_wall_s']
assert math.isfinite(wall) and wall > 0
assert len(result['replicas']) == 8
for i, record in enumerate(result['replicas']):
    assert (record['replica'], record['seed'], record['steps']) == (i, 1000+i, 25000)
    for key in ('wall_s', 'final_potential_kj_mol', 'mean_potential_kj_mol'):
        assert math.isfinite(record[key])
log = pathlib.Path('out/baseline.stdout.log').read_text()
printed_wall = re.findall(r'^total_wall_s: ([0-9.eE+\-]+)$', log, re.M)
printed_rate = re.findall(r'^aggregate_ns_per_day: ([0-9.eE+\-]+)$', log, re.M)
assert printed_wall and printed_rate, 'Missing workload stdout measurements'
assert math.isclose(float(printed_wall[-1]), wall, abs_tol=0.00051)
rate = result['simulated_ns'] / wall * 86400
assert math.isclose(float(printed_rate[-1]), rate, abs_tol=0.051)
items = [{'id': 'nvidia_2025_dhfr_eight_mps_approx_throughput', 'unit': 'microseconds/day'}]
measured = {}
for item in items:
    if item['unit'] == 'microseconds/day':
        value = rate / 1000
    elif item['unit'] == 'ns/day':
        value = rate
    elif item['unit'] in ('s', 'seconds'):
        value = wall
    else:
        raise ValueError('Unsupported measurement unit: ' + item['unit'])
    assert math.isfinite(value)
    measured[item['id']] = value
pathlib.Path('out/anchors_measured.json').write_text(json.dumps(measured, indent=2, allow_nan=False) + '\n')
PYANCHORS
