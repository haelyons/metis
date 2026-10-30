#!/usr/bin/env bash
set -euo pipefail
method=${METHOD_DIR:?METHOD_DIR is required}
test -f "$method/dhfr_ensemble.py"
mkdir -p "${METHOD_OUT:-$PWD/out}"
source "$method/cuda-env.sh"
export OPENMM_CPU_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$method/python${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
python3 - "$method" <<'PYSETUP'
import ast, importlib.metadata, pathlib, sys
method = pathlib.Path(sys.argv[1])
ast.parse((method / 'dhfr_ensemble.py').read_text())
for package in ('openmm', 'OpenMM-CUDA-12'):
    if importlib.metadata.version(package) != '8.2.0':
        raise RuntimeError('Incorrect package version: ' + package)
import openmm
assert openmm.Platform.getPlatformByName('CUDA').getName() == 'CUDA'
PYSETUP
