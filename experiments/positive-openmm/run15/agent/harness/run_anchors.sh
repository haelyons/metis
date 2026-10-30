#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${EVAL_MODE:-}" && "${EVAL_MODE}" != anchors ]]; then
    exec bash harness/run_evaluation.sh
fi
mkdir -p out
# No environment overrides: profiler and anchors execute the same canonical command.
bash harness/run_command.sh
python3 - <<'PARSE'
import json, math, pathlib, re
output = json.loads(pathlib.Path('out/run/ensemble.json').read_text())
def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
        raise RuntimeError('Missing or invalid numeric output')
    return value
if output['platform'] != 'CUDA' or output['properties'] != {'Precision':'single','DeterministicForces':'true'}:
    raise RuntimeError('Output configuration does not match canonical CUDA command')
if output['simulated_ns'] != 0.8 or len(output['replicas']) != 8:
    raise RuntimeError('Output scale does not match 8 x 25000 command')
wall = finite(output['total_wall_s'])
if wall <= 0:
    raise RuntimeError('Invalid total_wall_s')
for index, replica in enumerate(output['replicas']):
    if (replica['replica'],replica['seed'],replica['steps']) != (index,1000+index,25000):
        raise RuntimeError('Output seeds/steps do not match canonical command')
    for key in ('wall_s','mean_potential_kj_mol','final_potential_kj_mol'):
        finite(replica[key])
log = pathlib.Path('out/run/baseline.log').read_text()
parsed = {}
for key in ('total_wall_s','aggregate_ns_per_day'):
    match = re.search(r'^'+key+r':\s*(\S+)\s*$',log,re.M)
    if not match:
        raise RuntimeError('Missing stdout metric: '+key)
    parsed[key] = finite(float(match.group(1)))
# Printed values are rounded by the published driver; compare at its printed precision.
if parsed['total_wall_s'] != float(f'{wall:.3f}') or parsed['aggregate_ns_per_day'] != float(f'{0.8/wall*86400:.1f}'):
    raise RuntimeError('Stdout and saved output disagree')
items = [{'id': 'nvidia2025-dhfr-tuned-8-throughput-reference', 'quantity': 'Approximate aggregate DHFR throughput, ns/day, eight concurrent MPS simulations on one H100 or L40S, tuned thread percentage', 'source': 'https://developer.nvidia.com/blog/maximizing-openmm-molecular-dynamics-throughput-with-nvidia-multi-process-service/ (Hsu, Clark and Paulsen, 2025-06-04, Figure 4 and accompanying text)', 'published_value': 5000.0, 'comparison': '==', 'tolerance': None, 'uncertainty': None, 'kind': 'reference', 'configuration': {'openmm': '8.2.0', 'processes': 8, 'CUDA_MPS_ACTIVE_THREAD_PERCENTAGE': 25, 'command': 'python benchmark.py --platform=CUDA --test=pme --seconds=60'}, 'reason': 'Source describes approaching 5 microseconds/day, converted to 5000 ns/day; approximate reference only. No acceptance criterion, tolerance or uncertainty published. Fixed-time measurements do not directly anchor the fixed-work ensemble.'}]
measured = {item['id']: parsed['aggregate_ns_per_day'] for item in items}
pathlib.Path('out/anchors_measured.json').write_text(json.dumps(measured,allow_nan=False,indent=2)+'\n')
PARSE
