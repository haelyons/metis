#!/usr/bin/env bash
set -euo pipefail
: "${METHOD_DIR:?METHOD_DIR required}"
mkdir -p "$METHOD_DIR"
source "$METHOD_DIR/cuda-env.sh"
export PYTHONPATH="$METHOD_DIR/python"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
/usr/bin/python3 - "$METHOD_DIR" <<'CHECK'
import ast, importlib.metadata, pathlib, sys
root = pathlib.Path(sys.argv[1])
for name in ('dhfr_ensemble.py', 'method_evaluation.py'):
    ast.parse((root/name).read_text(), filename=name)
assert importlib.metadata.version('openmm') == '8.2.0'
assert importlib.metadata.version('OpenMM-CUDA-12') == '8.2.0'
CHECK
command -v nvidia-cuda-mps-control
