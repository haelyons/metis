#!/usr/bin/env bash
set -euo pipefail
# Invoked from the shared working directory; all workload paths are relative.
export OMP_NUM_THREADS=26 OMP_DYNAMIC=FALSE OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 LC_ALL=C LANG=C
export CUDA_VISIBLE_DEVICES='' GPU_COUNT=0
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR=out/tmp
mkdir -p out/tmp
export XDG_CACHE_HOME=out/cache
# CUDA is unused by the CPU-only binary. Preserve the verified toolchain identity.
if [[ -x /usr/local/cuda/bin/nvcc && -f /usr/local/cuda/include/cuda_runtime.h && -f /usr/local/cuda/lib64/libcudart.so ]]; then
    export CUDACXX=/usr/local/cuda/bin/nvcc CUDA_INCLUDE_DIR=/usr/local/cuda/include CUDA_LIBRARY_DIR=/usr/local/cuda/lib64 CUDAToolkit_ROOT=/usr/local/cuda
    export PATH=/usr/local/cuda/bin:$PATH
elif [[ -x /usr/lib/cuda/bin/nvcc && -f /usr/lib/cuda/include/cuda_runtime.h && -f /usr/lib/cuda/lib64/libcudart.so ]]; then
    export CUDACXX=/usr/lib/cuda/bin/nvcc CUDA_INCLUDE_DIR=/usr/lib/cuda/include CUDA_LIBRARY_DIR=/usr/lib/cuda/lib64 CUDAToolkit_ROOT=/usr/lib/cuda
    export PATH=/usr/lib/cuda/bin:$PATH
elif [[ -x /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    export CUDACXX=/usr/bin/nvcc CUDA_INCLUDE_DIR=/usr/include CUDA_LIBRARY_DIR=/usr/lib/x86_64-linux-gnu
else
    echo 'No complete CUDA layout from supplied probe' >&2; exit 1
fi
ls -l "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
for prefix in 1aua 1ax2 1dv1 1nr5; do
    job=out/$prefix
    mkdir -p "$job/poses" "$job/ligands"
    baseline-published/megadock/megadock -R data/inputs/${prefix}_R.pdb -L data/inputs/${prefix}_L.pdb -o "$job/docking.out" -N 50 -t 1 -v 1.2 -e 1.0 -d 1.0 -a -45.0 -b 1.0 -f 3 -r 3600 2>&1 | tee -a "$job/docking.log"
    for i in {1..50}; do
        baseline-published/megadock/decoygen "$job/ligands/ligand_$i.pdb" "data/inputs/${prefix}_L.pdb" "$job/docking.out" "$i" >> "$job/decoygen.log" 2>&1
        # END occurs only after both complete chains. Preserve all coordinate records.
        awk '$1 != "END" && $1 != "ENDMDL" {print}' "data/inputs/${prefix}_R.pdb" "$job/ligands/ligand_$i.pdb" > "$job/poses/model_$i.pdb"
        printf 'END\n' >> "$job/poses/model_$i.pdb"
    done
done
