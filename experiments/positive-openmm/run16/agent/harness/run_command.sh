#!/usr/bin/env bash
set -euo pipefail
source baseline-published/cuda-env.sh
export CUDA_VISIBLE_DEVICES=0
export PYTHONHASHSEED=0
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
mkdir -p out/baseline-run
cd out/baseline-run
export PYTHONPATH=../../baseline-published/python
export TMPDIR=.
export CUDA_CACHE_PATH=./cuda-cache
mkdir -p cuda-cache
ln -sfn ../../data/5dfr_solv-cube_equil.pdb 5dfr_solv-cube_equil.pdb
ln -sfn ../../data/amber99sb.xml amber99sb.xml
ln -sfn ../../data/tip3p.xml tip3p.xml
rm -f ../ensemble.json
/usr/bin/python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000 --platform CUDA --out ../ensemble.json 2>&1 | tee -a ../baseline.log
