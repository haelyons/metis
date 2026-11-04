#!/usr/bin/env bash
set -euo pipefail
source baseline-published/cuda-env.sh
export OMP_NUM_THREADS=26 OMP_DYNAMIC=FALSE OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export LC_ALL=C LANG=C CUDA_VISIBLE_DEVICES=0
mkdir -p out
cd out
{
../baseline-published/megadock/megadock -R ../data/fixtures/f1a19/R.pdb -L ../data/fixtures/f1a19/L.pdb -o docking.out -N 50 -t 1 -v 1.2 -e 1.0 -d 1.0 -a -45.0 -b 1.0 -f 3 -r 3600
for r in $(seq 1 50); do
  ../baseline-published/megadock/decoygen "lig_$r.pdb" ../data/fixtures/f1a19/L.pdb docking.out "$r" > "decoygen_$r.log" 2>&1
  grep -v '^END' ../data/fixtures/f1a19/R.pdb > "model_$r.pdb"
  grep -v -E '^(END|ENDMDL)' "lig_$r.pdb" >> "model_$r.pdb"
  echo END >> "model_$r.pdb"
done
} 2>&1 | tee -a stdout.log
