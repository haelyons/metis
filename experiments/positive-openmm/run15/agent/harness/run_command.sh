#!/usr/bin/env bash
set -euo pipefail
# Invoked from the shared working directory. The pipeline's inherited MPS environment is untouched.
source baseline-published/cuda-env.sh
export CUDA_VISIBLE_DEVICES=0
export PYTHONPATH="../../baseline-published/python${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONNOUSERSITE=1
export PYTHONUNBUFFERED=1
mkdir -p out/run out/history
# Preserve earlier invocation output while keeping canonical output paths stable.
if [[ -e out/run/ensemble.json || -e out/run/baseline.log ]]; then
    archive=$(mktemp -d out/history/run.XXXXXXXX)
    for file in ensemble.json baseline.log; do
        if [[ -e "out/run/$file" ]]; then mv "out/run/$file" "$archive/$file"; fi
    done
fi
cd out/run
ln -sfn ../../data/5dfr_solv-cube_equil.pdb 5dfr_solv-cube_equil.pdb
ln -sfn ../../data/amber99sb.xml amber99sb.xml
ln -sfn ../../data/tip3p.xml tip3p.xml
python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 2>&1 | tee baseline.log
