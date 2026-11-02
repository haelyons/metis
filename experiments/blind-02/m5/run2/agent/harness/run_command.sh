#!/usr/bin/env bash
set -euo pipefail
# Working directory is the shared work directory; all workload paths are relative.
cd .
source baseline-published/cuda.env
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
export CUDA_VISIBLE_DEVICES=0
export OMP_NUM_THREADS=26 OMP_DYNAMIC=FALSE
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export LC_ALL=C LANG=C
mkdir -p out/runs
run=$(mktemp -d out/runs/run.XXXXXXXX)
ln -sfn "${run#out/}" out/latest-run
exec > >(tee "$run/command.log") 2>&1
printf 'Working directory: .\nCUDA_VISIBLE_DEVICES=%s\nGPU count: 1\nOMP_NUM_THREADS=%s\n' "$CUDA_VISIBLE_DEVICES" "$OMP_NUM_THREADS"
for config in cpu_standard gpu_standard gpu_dense; do
    binary=megadock
    angles=(-r 3600)
    if [[ "$config" != cpu_standard ]]; then binary=megadock-gpu; fi
    if [[ "$config" == gpu_dense ]]; then angles=(-D); fi
    for system in \
        1aua__A1_P24280--1aua__A2_P24280 \
        1ax2__A1_P16404--1ax2__A2_P16404 \
        1dv1__A1_P24182--1dv1__B1_P24182 \
        1nr5__A1_P07547--1nr5__A2_P07547; do
        prefix=${system:0:4}
        receptor="data/inputs/${prefix}_R.pdb"
        ligand="data/inputs/${prefix}_L.pdb"
        job="$run/$config/$system"
        mkdir -p "$job/apo_decoys"
        baseline-published/megadock/"$binary" -R "$receptor" -L "$ligand" \
            -o "$job/docking.out" -N 50 -t 1 -v 1.2 -e 1.0 -d 1.0 -a -45.0 -b 1.0 -f 3 \
            "${angles[@]}" 2>&1 | tee "$job/docking.log"
        for rank in $(seq 1 50); do
            baseline-published/megadock/decoygen "$job/ligand_${rank}.pdb" "$ligand" "$job/docking.out" "$rank" \
                >> "$job/decoygen.log" 2>&1
            # PDB END records must follow both chains, not terminate receptor first.
            sed '/^END/d' "$receptor" > "$job/apo_decoys/model_${rank}.pdb"
            sed '/^END/d' "$job/ligand_${rank}.pdb" >> "$job/apo_decoys/model_${rank}.pdb"
            printf 'END\n' >> "$job/apo_decoys/model_${rank}.pdb"
        done
    done
done
