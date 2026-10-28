#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
rm -f out/anchors_measured.json out/run/ensemble.json
bash harness/run_command.sh
python3 - <<'PARSE'
import json, math, pathlib, re
items = ['nvidia2025_dhfr_8_mps_approx_throughput']
p = json.loads(pathlib.Path('out/run/ensemble.json').read_text())
def finite(x, positive=False):
    if isinstance(x, bool) or not isinstance(x, (int,float)) or not math.isfinite(x) or (positive and x <= 0):
        raise ValueError('Invalid measurement: ' + repr(x))
    return x
assert p['platform'] == 'CUDA'
assert p['properties'] == {'Precision':'single', 'DeterministicForces':'true'}
assert p['simulated_ns'] == 0.8
assert len(p['replicas']) == 8
for i, r in enumerate(p['replicas']):
    assert (r['replica'],r['seed'],r['steps']) == (i,1000+i,25000)
    finite(r['wall_s'], True)
    finite(r['final_potential_kj_mol']); finite(r['mean_potential_kj_mol'])
wall = finite(p['total_wall_s'], True)
log = pathlib.Path('out/run/command.log').read_text()
times = re.findall(r'^total_wall_s: ([0-9.]+)$', log, re.M)
rates = re.findall(r'^aggregate_ns_per_day: ([0-9.]+)$', log, re.M)
if not times or not rates:
    raise ValueError('Missing printed measurements')
assert abs(float(times[-1])-wall) <= 0.00051
throughput = finite(p['simulated_ns']/wall*86400, True)
assert abs(float(rates[-1])-throughput) <= 0.051
pathlib.Path('out/anchors_measured.json').write_text(json.dumps({i:throughput for i in items}, allow_nan=False, indent=2)+'\n')
PARSE
