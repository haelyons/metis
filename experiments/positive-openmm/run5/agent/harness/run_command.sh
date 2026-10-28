#!/usr/bin/env bash
set -euo pipefail
source baseline-published/cuda.env
ls -l "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY/libcudart.so"
export PATH="$(dirname "$CUDA_COMPILER"):$PATH"
export LD_LIBRARY_PATH="$CUDA_LIBRARY${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CPATH="$CUDA_INCLUDE${CPATH:+:$CPATH}"
export LIBRARY_PATH="$CUDA_LIBRARY${LIBRARY_PATH:+:$LIBRARY_PATH}"
export CMAKE_CUDA_COMPILER="$CUDA_COMPILER"
export OPENMM_CUDA_COMPILER="$CUDA_COMPILER"
export CUDA_VISIBLE_DEVICES=0
export PYTHONDONTWRITEBYTECODE=1
mkdir -p out/run
# Preserve previous invocations, keeping canonical output names stable.
if [[ -f out/run/command.log || -f out/run/ensemble.json ]]; then
    history=$(mktemp -d out/run-history.XXXXXXXX)
    for file in command.log ensemble.json; do
        if [[ -f out/run/$file ]]; then mv "out/run/$file" "$history/"; fi
    done
fi
cd out/run
mkdir -p cache/cuda cache/openmm
export CUDA_CACHE_PATH=cache/cuda
export OPENMM_CACHE_DIR=cache/openmm
export PYTHONPATH="../../baseline-published/site${PYTHONPATH:+:$PYTHONPATH}"
for file in 5dfr_solv-cube_equil.pdb amber99sb.xml tip3p.xml; do
    ln -sfn "../../data/$file" "$file"
done
command=(python3 ../../baseline-published/dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000)
{
python3 - "${command[@]}" <<'CHECK'
import ctypes, json, os, sys
import openmm
from openmm import app
cuda=ctypes.CDLL('libcuda.so.1')
assert cuda.cuInit(0)==0, 'CUDA initialization failed'
n=ctypes.c_int()
assert cuda.cuDeviceGetCount(ctypes.byref(n))==0 and n.value==1, 'Expected one visible GPU'
assert os.environ['CUDA_VISIBLE_DEVICES']=='0'
assert openmm.__version__=='8.2.0'
pdb=app.PDBFile('5dfr_solv-cube_equil.pdb')
assert pdb.topology.getNumAtoms()==23558
print(json.dumps({'command':sys.argv[1:],'cwd':'out/run','CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES'],'gpu_count':n.value,'atoms':pdb.topology.getNumAtoms(),'openmm':openmm.__version__}), flush=True)
CHECK
"${command[@]}"
} 2>&1 | tee command.log
