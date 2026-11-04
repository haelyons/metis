#!/usr/bin/env bash
set -euo pipefail
# Invocation working directory: the shared run root. A0 uses zero GPUs.
export OMP_NUM_THREADS=26 OMP_DYNAMIC=FALSE OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 LC_ALL=C LANG=C CUDA_VISIBLE_DEVICES=0
source baseline-published/cuda-env.sh
mkdir -p out/a0-smoke/out
cd out/a0-smoke
[[ -e baseline-published ]] || ln -s ../../baseline-published baseline-published
[[ -e data ]] || ln -s ../../data data
exec >> stdout.log 2>&1
printf "environment: OMP_NUM_THREADS=%s OMP_DYNAMIC=%s OPENBLAS_NUM_THREADS=%s MKL_NUM_THREADS=%s NUMEXPR_NUM_THREADS=%s LC_ALL=%s LANG=%s CUDA_VISIBLE_DEVICES=%s gpu_count=0\n" "$OMP_NUM_THREADS" "$OMP_DYNAMIC" "$OPENBLAS_NUM_THREADS" "$MKL_NUM_THREADS" "$NUMEXPR_NUM_THREADS" "$LC_ALL" "$LANG" "$CUDA_VISIBLE_DEVICES"
set -x
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
baseline-published/megadock/megadock -R data/fixtures/f1a19/R.pdb -L data/fixtures/f1a19/L.pdb \
 -o out/docking.out -N 50 -t 1 -v 1.2 -e 1.0 -d 1.0 -a -45.0 -b 1.0 -f 3 -r 3600
bash -c 'set -euo pipefail; for r in $(seq 1 50); do baseline-published/megadock/decoygen "lig_$r.pdb" "$2" "$0/docking.out" "$r" > "decoygen_$r.log" 2>&1; grep -v '\''^END'\'' "$1" > "$0/model_$r.pdb"; grep -v -E '\''^(END|ENDMDL)'\'' "lig_$r.pdb" >> "$0/model_$r.pdb"; echo END >> "$0/model_$r.pdb"; done' \
 out data/fixtures/f1a19/R.pdb data/fixtures/f1a19/L.pdb
