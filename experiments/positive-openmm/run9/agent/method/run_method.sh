#!/usr/bin/env bash
set -euo pipefail
: "${METHOD_DIR:?METHOD_DIR is required}"
: "${BASELINE_DIR:?BASELINE_DIR is required}"
METHOD_DIR="$(cd "$METHOD_DIR" && pwd)"
BASELINE_DIR="$(cd "$BASELINE_DIR" && pwd)"
export METHOD_DIR BASELINE_DIR
export METHOD_OUT="${METHOD_OUT:-$PWD/out}"
mkdir -p "$METHOD_OUT"
METHOD_OUT="$(cd "$METHOD_OUT" && pwd)"
export METHOD_OUT
source "$METHOD_DIR/cuda.env"
export CUDA_VISIBLE_DEVICES=0
export PYTHONPATH="$METHOD_DIR/python"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export OPENMM_CPU_THREADS=1
mkdir -p "$METHOD_OUT/tmp" "$METHOD_OUT/cuda-cache"
export TMPDIR="$METHOD_OUT/tmp" CUDA_CACHE_PATH="$METHOD_OUT/cuda-cache"
# Do not silently fall back to time-slicing if MPS is unavailable.
printf 'get_server_list\n' | /usr/bin/nvidia-cuda-mps-control > /dev/null
case "${EVAL_MODE:-anchors}" in
  anchors)
    mkdir -p "$METHOD_OUT/run"
    export DATA_DIR="${DATA_DIR:-$(dirname "$BASELINE_DIR")/data}"
    ln -sfn "$DATA_DIR/5dfr_solv-cube_equil.pdb" "$METHOD_OUT/run/5dfr_solv-cube_equil.pdb"
    rm -f "$METHOD_OUT/anchors_measured.json" "$METHOD_OUT/run/ensemble.json"
    (
      cd "$METHOD_OUT/run"
      /usr/bin/python3 "$METHOD_DIR/dhfr_ensemble.py" --replicas 8 --steps 25000 --seed0 1000 --platform CUDA --out ensemble.json
    ) 2>&1 | tee "$METHOD_OUT/method.log"
    /usr/bin/python3 - <<'PY'
import json, math, os
from pathlib import Path
out=Path(os.environ['METHOD_OUT'])
d=json.loads((out/'run/ensemble.json').read_text())
assert d['platform']=='CUDA'
assert d['properties']=={'Precision':'single','DeterministicForces':'true'}
assert math.isclose(d['simulated_ns'],0.8,rel_tol=0,abs_tol=1e-12)
assert math.isfinite(d['total_wall_s']) and d['total_wall_s']>0
assert len(d['replicas'])==8
for i,row in enumerate(d['replicas']):
    assert (row['replica'],row['seed'],row['steps'])==(i,1000+i,25000)
    for key in ('wall_s','mean_potential_kj_mol','final_potential_kj_mol'):
        assert math.isfinite(row[key])
(out/'anchors_measured.json').write_text(json.dumps({
 'nvidia_2025_dhfr_eight_mps_throughput_reference':d['simulated_ns']/d['total_wall_s']*86400/1000
},allow_nan=False,indent=2)+'\n')
PY
    ;;
  equivalence|warmup|performance|curve)
    : "${EVAL_OUT:?EVAL_OUT is required}"
    mkdir -p "$EVAL_OUT"
    /usr/bin/python3 "$METHOD_DIR/method_evaluate.py"
    ;;
  *) echo "Unknown EVAL_MODE: $EVAL_MODE" >&2; exit 1 ;;
esac
