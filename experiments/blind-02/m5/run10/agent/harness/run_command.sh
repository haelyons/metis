#!/usr/bin/env bash
set -euo pipefail

# Working directory: shared invocation directory. A0 uses the CPU (gpu_count=0).
mkdir -p out
exec >> out/baseline.log 2>&1
set -x
export OMP_NUM_THREADS=26 OMP_DYNAMIC=FALSE OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 LC_ALL=C LANG=C CUDA_VISIBLE_DEVICES=0
baseline-published/megadock/megadock -R data/inputs/1aua_R.pdb -L data/inputs/1aua_L.pdb -o out/docking.out -N 50 -t 1 -v 1.2 -e 1 -d 1 -a -45.0 -b 1 -f 3 -r 3600
for r in $(seq 1 50); do
 baseline-published/megadock/decoygen "out/lig_$r.pdb" data/inputs/1aua_L.pdb out/docking.out "$r" > "out/decoygen_$r.log" 2>&1
 grep -v '^END' data/inputs/1aua_R.pdb > "out/model_$r.pdb"
 grep -v -E '^(END|ENDMDL)' "out/lig_$r.pdb" >> "out/model_$r.pdb"
 echo END >> "out/model_$r.pdb"
done
