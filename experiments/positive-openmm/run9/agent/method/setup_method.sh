#!/usr/bin/env bash
set -euo pipefail
: "${METHOD_DIR:?METHOD_DIR is required}"
: "${BASELINE_DIR:?BASELINE_DIR is required}"
METHOD_DIR="$(cd "$METHOD_DIR" && pwd)"
export METHOD_DIR
source "$METHOD_DIR/cuda.env"
export PYTHONPATH="$METHOD_DIR/python"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=0
/usr/bin/python3 - <<'PY'
import importlib.metadata, os, hashlib
from openmm import app
from pathlib import Path
assert importlib.metadata.version('openmm') == '8.2.0'
assert importlib.metadata.version('OpenMM-CUDA-12') == '8.2.0'
data=Path(os.environ.get('DATA_DIR',str(Path(os.environ['BASELINE_DIR']).resolve().parent/'data')))
for path, expected in (
    (data/'5dfr_solv-cube_equil.pdb','fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf'),
    (Path(app.__file__).parent/'data/amber99sb.xml','186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092'),
    (Path(app.__file__).parent/'data/tip3p.xml','607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c')):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise RuntimeError('Pinned input checksum mismatch: '+str(path))
for name in ('dhfr_ensemble.py', 'method_evaluate.py'):
    path=Path(os.environ['METHOD_DIR'])/name
    compile(path.read_text(),str(path),'exec')
PY
# MPS is a persistent shared service, provisioned before warmup, never stopped
# or reconfigured between arms. Respect the pipeline's pipe directory if set.
/usr/bin/python3 - <<'PY'
import json, os, subprocess, time
from pathlib import Path
start=time.perf_counter()
command=['/usr/bin/nvidia-cuda-mps-control']
probe=subprocess.run(command,input='get_server_list\n',text=True,capture_output=True)
started=False
if probe.returncode:
    subprocess.run(command+['-d'],check=True)
    started=True
    probe=subprocess.run(command,input='get_server_list\n',text=True,capture_output=True)
    if probe.returncode:
        raise RuntimeError('MPS service unavailable: '+probe.stderr)
(Path(os.environ['METHOD_DIR'])/'mps_setup.json').write_text(json.dumps({
    'wall_s':time.perf_counter()-start,'started':started,
    'pipe_directory':os.environ.get('CUDA_MPS_PIPE_DIRECTORY','/tmp/nvidia-mps')})+'\n')
PY
