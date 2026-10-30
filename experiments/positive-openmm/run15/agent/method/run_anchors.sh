#!/usr/bin/env bash
set -euo pipefail
method=${METHOD_DIR:?METHOD_DIR is required}
base=${BASELINE_DIR:?BASELINE_DIR is required}
if [[ -f "$base/baseline-published/dhfr_ensemble.py" ]]; then
    root=$base
else
    root=$(dirname "$base")
fi
source "$method/cuda-env.sh"
export OPENMM_CPU_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export CUDA_VISIBLE_DEVICES=0
export PYTHONPATH="$method/python${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
out=${EVAL_OUT:-${METHOD_OUT:-$PWD/out}}
mkdir -p "$out/run"
out=$(cd "$out" && pwd)
cd "$out/run"
for name in 5dfr_solv-cube_equil.pdb amber99sb.xml tip3p.xml; do
    ln -sfn "$root/data/$name" "$name"
done
python3 "$method/dhfr_ensemble.py" --replicas 8 --steps 25000 --seed0 1000 --out "$out/run/ensemble.json" 2>&1 | tee method.log
cd "$(dirname "$out")"
python3 - "$out" <<'PARSE'
import os, sys
import json, math, pathlib, re
output = json.loads(pathlib.Path(sys.argv[1] + '/run/ensemble.json').read_text())
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
log = pathlib.Path(sys.argv[1] + '/run/method.log').read_text()
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
pathlib.Path(sys.argv[1] + '/anchors_measured.json').write_text(json.dumps(measured,allow_nan=False,indent=2)+'\n')
PARSE
