#!/usr/bin/env bash
set -euo pipefail
: "${METHOD_DIR:?METHOD_DIR must identify the patched copy}"
: "${BASELINE_DIR:?BASELINE_DIR must identify baseline sources}"
source "$BASELINE_DIR/cuda-env.sh"
export PATH="$CUDA_BIN:$PATH"
export PYTHONPATH="$METHOD_DIR/python${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=0 GPU_COUNT=1
export CUDACXX="$CUDA_NVCC" OPENMM_CUDA_COMPILER="$CUDA_NVCC"
export CPATH="$CUDA_INCLUDE${CPATH:+:$CPATH}"
export LD_LIBRARY_PATH="${CUDA_LIBRARY%/*}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# Work in the pipeline's absolute method output tree, including in fresh CWDs.
export METHOD_INPUT_PDB="${BASELINE_DIR%/*}/data/5dfr_solv-cube_equil.pdb"
if [[ ! -f "$METHOD_INPUT_PDB" ]]; then
    printf 'Missing published input: %s\n' "$METHOD_INPUT_PDB" >&2
    exit 1
fi
export METHOD_RESULT_ROOT="${METHOD_OUT:-$PWD/out}"
mkdir -p "$METHOD_RESULT_ROOT"
export METHOD_MPS_ROOT="$METHOD_RESULT_ROOT"
if [[ "${EVAL_MODE:-anchors}" != anchors ]]; then
    exec python3 "$METHOD_DIR/method_evaluate.py"
fi
mkdir -p "$METHOD_RESULT_ROOT/run"
cd "$METHOD_RESULT_ROOT/run"
ln -sfn "$METHOD_INPUT_PDB" 5dfr_solv-cube_equil.pdb
python3 "$METHOD_DIR/dhfr_ensemble.py" --replicas 8 --steps 25000 --seed0 1000 2>&1 | tee command.log
python3 - <<'PY'
import json, math, os, pathlib
r=json.loads((pathlib.Path(os.environ['METHOD_RESULT_ROOT'])/'run/ensemble.json').read_text())
assert r['platform']=='CUDA'
assert r['properties']=={'Precision':'single','DeterministicForces':'true'}
assert r['simulated_ns']==0.8 and len(r['replicas'])==8
assert math.isfinite(r['total_wall_s']) and r['total_wall_s']>0
for i,row in enumerate(r['replicas']):
    assert (row['replica'],row['seed'],row['steps'])==(i,1000+i,25000)
    for key in ('wall_s','final_potential_kj_mol','mean_potential_kj_mol'):
        assert math.isfinite(row[key])
items=json.loads((pathlib.Path(os.environ['METHOD_DIR'])/'anchors.json').read_text())
measured={item['id']:r['simulated_ns']/r['total_wall_s']*86.4 for item in items}
(pathlib.Path(os.environ['METHOD_RESULT_ROOT'])/'anchors_measured.json').write_text(json.dumps(measured,indent=2,allow_nan=False)+'\n')
PY
