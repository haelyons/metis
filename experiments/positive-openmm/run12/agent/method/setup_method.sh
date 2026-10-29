#!/usr/bin/env bash
set -euo pipefail
: "${METHOD_DIR:?METHOD_DIR required}"
source "$METHOD_DIR/cuda-env.sh"
export PYTHONPATH="$METHOD_DIR/python"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=0
# Use the default per-user MPS service so both arms see the same service state.
# Do not stop it between arms or charge installation to a timed workload.
command -v nvidia-cuda-mps-control >/dev/null
if ! echo get_server_list | nvidia-cuda-mps-control >/dev/null 2>&1; then
    nvidia-cuda-mps-control -d
fi
echo get_server_list | nvidia-cuda-mps-control
/usr/bin/python3 - <<'CHECK'
import importlib.metadata as metadata
import os, pathlib
import openmm
assert metadata.version('OpenMM') == '8.2.0'
assert metadata.version('OpenMM-CUDA-12') == '8.2.0'
path = pathlib.Path(os.environ['METHOD_DIR']) / 'dhfr_ensemble.py'
compile(path.read_text(), str(path), 'exec')
assert openmm.Platform.getPlatformByName('CUDA').getName() == 'CUDA'
CHECK
