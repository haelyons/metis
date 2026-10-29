#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
bash harness/run_command.sh
/usr/bin/python3 - <<'PARSE'
from pathlib import Path
import json
def validate(path, seed0):
    import json, math, re
    obj = json.loads((path / 'ensemble.json').read_text())
    def number(x, positive=False):
        if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or (positive and x <= 0):
            raise ValueError('Missing or invalid measured number: ' + repr(x))
        return x
    if obj['platform'] != 'CUDA' or obj['properties'] != {'Precision': 'single', 'DeterministicForces': 'true'}:
        raise ValueError('Invalid printed platform configuration')
    if number(obj['simulated_ns']) != 0.8 or len(obj['replicas']) != 8:
        raise ValueError('Invalid printed ensemble scale')
    total = number(obj['total_wall_s'], True)
    metrics = {'total_wall_s': total, 'aggregate_ns_per_day': 0.8 * 86400 / total, 'simulated_ns': 0.8}
    for i, replica in enumerate(obj['replicas']):
        if (replica['replica'], replica['seed'], replica['steps']) != (i, seed0+i, 25000):
            raise ValueError('Invalid printed replica configuration')
        for key in ('wall_s', 'mean_potential_kj_mol', 'final_potential_kj_mol'):
            metrics[f'replica_{i}_{key}'] = number(replica[key], key == 'wall_s')
    stdout = (path / 'stdout.log').read_text()
    for key, decimals in [('total_wall_s', 3), ('aggregate_ns_per_day', 1)]:
        match = re.search(r'^' + key + r': ([0-9.eE+\-]+)$', stdout, re.M)
        if not match or not math.isfinite(float(match[1])) or abs(float(match[1]) - metrics[key]) > 0.51 * 10**(-decimals):
            raise ValueError('Missing or inconsistent printed metric: ' + key)
    return metrics

path = Path(Path('out/latest-baseline-run.txt').read_text().strip())
metrics = validate(path, 1000)
items = [{'id': 'nvidia-2025-dhfr-tuned-eight-throughput-reference'}]
measured = {item['id']: metrics['aggregate_ns_per_day'] for item in items}
Path('out/anchors_measured.json').write_text(json.dumps(measured, indent=2, allow_nan=False) + '\n')
print(json.dumps(measured, allow_nan=False))
PARSE
