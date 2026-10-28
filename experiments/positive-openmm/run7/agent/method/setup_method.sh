#!/usr/bin/env bash
set -euo pipefail
: "${METHOD_DIR:?}" "${BASELINE_DIR:?}"
source "$METHOD_DIR/toolkit.env"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "${METHOD_OUT:-out}"
command -v nvidia-cuda-mps-control
# The fresh copy contains the already installed, pinned environment. Do not
# install into a copied virtualenv whose shebangs might reference the baseline.
"$METHOD_DIR/venv/bin/python3" - <<'PYTHON'
import ast, importlib.metadata, os, pathlib
for package in ('openmm','OpenMM-CUDA-12'):
    assert importlib.metadata.version(package) == '8.2.0'
for name in ('method_driver.py','method_adapter.py'):
    ast.parse((pathlib.Path(os.environ['METHOD_DIR'])/name).read_text())
PYTHON
