#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
(
source baseline-published/cuda-env.sh
set -x
# The published A0 CPU executable uses zero GPUs. One GPU remains visible.
export OMP_NUM_THREADS=26 OMP_DYNAMIC=FALSE OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 LC_ALL=C LANG=C CUDA_VISIBLE_DEVICES=0
baseline-published/megadock/megadock -R data/fixtures/f1a19/R.pdb -L data/fixtures/f1a19/L.pdb -o out/docking.out -N 50 -t 1 -v 1.2 -e 1.0 -d 1.0 -a -45.0 -b 1.0 -f 3 -r 3600
for r in $(seq 1 50); do
 baseline-published/megadock/decoygen "out/lig_$r.pdb" data/fixtures/f1a19/L.pdb out/docking.out "$r" > "out/decoygen_$r.log" 2>&1
 grep -v '^END' data/fixtures/f1a19/R.pdb > "out/model_$r.pdb"
 grep -v -E '^(END|ENDMDL)' "out/lig_$r.pdb" >> "out/model_$r.pdb"
 echo END >> "out/model_$r.pdb"
done
) 2>&1 | tee -a out/baseline.log
