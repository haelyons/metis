#!/usr/bin/env bash
set -euo pipefail
: "${METHOD_DIR:?METHOD_DIR required}"
: "${BASELINE_DIR:?BASELINE_DIR required}"
: "${METHOD_OUT:?METHOD_OUT required}"
source "$METHOD_DIR/cuda-env.sh"
export CUDA_VISIBLE_DEVICES=0
export PYTHONHASHSEED=0
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$METHOD_DIR/python"
export EVAL_OUT="${EVAL_OUT:-$METHOD_OUT}"
mkdir -p "$METHOD_OUT" "$EVAL_OUT"
if [[ -n "${EVAL_MODE:-}" ]]; then
    exec /usr/bin/python3 "$METHOD_DIR/method_evaluation.py"
fi
run="$METHOD_OUT/method-run"
mkdir -p "$run/cuda-cache"
export TMPDIR="$run"
export CUDA_CACHE_PATH="$run/cuda-cache"
data="$BASELINE_DIR/data"
if [[ ! -d "$data" ]]; then data="$(dirname "$BASELINE_DIR")/data"; fi
for name in 5dfr_solv-cube_equil.pdb amber99sb.xml tip3p.xml; do
    ln -sfn "$data/$name" "$run/$name"
done
cd "$run"
/usr/bin/python3 "$METHOD_DIR/dhfr_ensemble.py" --replicas 8 --steps 25000 --seed0 1000 --platform CUDA --out "$METHOD_OUT/ensemble.json" 2>&1 | tee "$METHOD_OUT/method.log"
