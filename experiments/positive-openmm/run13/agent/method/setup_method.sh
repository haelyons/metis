#!/usr/bin/env bash
set -euo pipefail
: "${METHOD_DIR:?METHOD_DIR is required}"
: "${BASELINE_DIR:?BASELINE_DIR is required}"
mkdir -p "${EVAL_OUT:-${METHOD_OUT:-out}}"
export PYTHONNOUSERSITE=1
export PYTHONPATH="$METHOD_DIR/python"
/usr/bin/python3 - <<'CHECK'
import importlib.metadata as metadata
import openmm
for name in ('openmm', 'OpenMM-CUDA-12'):
    if metadata.version(name) != '8.2.0':
        raise RuntimeError('Wrong pinned package version: ' + name)
if 'CUDA' not in [openmm.Platform.getPlatform(i).getName()
                  for i in range(openmm.Platform.getNumPlatforms())]:
    raise RuntimeError('CUDA plugin unavailable: ' + str(openmm.Platform.getPluginLoadFailures()))
CHECK
/usr/bin/python3 -c 'import ast, os; from pathlib import Path; ast.parse((Path(os.environ["METHOD_DIR"])/"dhfr_concurrent.py").read_text())'
command -v nvidia-cuda-mps-control >/dev/null
# Provision once before either arm timer, retaining the same daemon thereafter.
if ! echo get_server_list | nvidia-cuda-mps-control >/dev/null 2>&1; then
    nvidia-cuda-mps-control -d
fi
echo get_server_list | nvidia-cuda-mps-control >/dev/null
