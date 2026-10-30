#!/usr/bin/env bash
set -euo pipefail
mkdir -p out data baseline-published
exec > >(tee -a out/setup.log) 2>&1
# Only toolkit locations discovered by the box probe are candidates.
CUDA_ROOT=''
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -f "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
        CUDA_ROOT=$root
        break
    fi
done
if [[ -n "$CUDA_ROOT" ]]; then
    export CUDACXX="$CUDA_ROOT/bin/nvcc" CUDAToolkit_ROOT="$CUDA_ROOT"
    export CUDA_INCLUDE_DIR="$CUDA_ROOT/include" CUDA_LIBRARY_DIR="$CUDA_ROOT/lib64"
    export PATH="$CUDA_ROOT/bin:$PATH"
else
    export CUDACXX=/usr/bin/nvcc CUDA_INCLUDE_DIR=/usr/include CUDA_LIBRARY_DIR=/usr/lib/x86_64-linux-gnu
fi
export LD_LIBRARY_PATH="$CUDA_LIBRARY_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
ls "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export CUDA_VISIBLE_DEVICES='' PINDER_RELEASE=2024-02
export PINDER_BASE_DIR="$PWD/data" PINDER_DATA_DIR="$PWD/data/2024-02"
export XDG_CACHE_HOME="$PWD/out/cache" MPLCONFIGDIR="$PWD/out/matplotlib"
mkdir -p out/cache out/matplotlib
pin=ebeb28a2f8411363cef722b7d293c978f7442672
if [[ ! -d baseline-published/.git ]]; then
    git -C baseline-published init
    git -C baseline-published remote add origin https://github.com/pinder-org/pinder
fi
if ! git -C baseline-published cat-file -e "$pin^{commit}" 2>/dev/null; then
    git -C baseline-published fetch --depth 1 origin "$pin"
fi
git -C baseline-published checkout --detach "$pin"
test "$(git -C baseline-published rev-parse HEAD)" = "$pin"
# Preserve the stock torch installation; install the published package in an isolated venv.
python3 -m venv --system-site-packages baseline-published/venv || {
    echo 'ERROR: python3 venv unavailable; probe lists no enabled Ubuntu apt repository to install it.' >&2
    exit 1
}
# Keep build tooling local to the venv. The stock setuptools/packaging pair
# cannot load current vcs-versioning (requires packaging>=26.2).
# Upgrade pip too so isolated builds resolve a consistent backend environment.
export PYTHONNOUSERSITE=1
baseline-published/venv/bin/python -m pip install --upgrade pip setuptools wheel 'packaging>=26.2'
baseline-published/venv/bin/python - <<'PY'
import importlib.metadata
for name in ('pip', 'setuptools', 'wheel', 'packaging'):
    print(f'Build tool: {name}=={importlib.metadata.version(name)}')
PY
python3 - <<'PY' > out/stock-constraints.txt
import importlib.metadata
try:
    print('torch==' + importlib.metadata.version('torch'))
except importlib.metadata.PackageNotFoundError:
    pass
PY
(
    cd baseline-published
    venv/bin/python -m pip install -c ../out/stock-constraints.txt .
)
baseline-published/venv/bin/pinder_eval --help
export PINDER_BASE_DIR="$PWD/data" PINDER_DATA_DIR="$PWD/data/2024-02"
baseline-published/venv/bin/python - <<'PY'
import hashlib, json, os, pathlib, urllib.request
import pandas as pd
root=pathlib.Path('data/2024-02')
root.mkdir(parents=True, exist_ok=True)
for name in ['index.parquet', 'metadata.parquet']:
    dest=root/name
    if not dest.exists():
        tmp=dest.with_suffix('.partial')
        with urllib.request.urlopen('https://pinderdata.org/2024-02/'+name, timeout=120) as response, tmp.open('wb') as out:
            import shutil
            shutil.copyfileobj(response, out)
        tmp.replace(dest)
index=pd.read_parquet(root/'index.parquet')
selected=index.query('pinder_s and apo_R and apo_L').sort_values('id')
if selected.empty or selected.id.duplicated().any():
    raise RuntimeError('Invalid published paired-apo index')
# Freeze actual membership without asserting published numeric anchors.
manifest={'ids':selected.id.tolist(), 'index_sha256':hashlib.sha256((root/'index.parquet').read_bytes()).hexdigest(),
          'pinder_s_count':int(index.pinder_s.sum()), 'paired_apo_count':len(selected),
          'candidate_count_per_case':5, 'release':'2024-02'}
p=pathlib.Path('data/manifest.json')
if p.exists() and json.loads(p.read_text()) != manifest:
    raise RuntimeError('Frozen manifest differs on retry')
p.write_text(json.dumps(manifest, indent=2)+'\n')
selected.to_parquet('data/custom_index.parquet', index=False)
from pinder.core import PinderSystem
for identity in selected.id:
    system=PinderSystem(identity)
    # Materialize experimental partners before timed evaluation.
    for key in ['native', 'apo_receptor', 'apo_ligand']:
        if getattr(system, key) is None:
            raise RuntimeError(f'Missing {key} for {identity}')
pathlib.Path('data/confirmation.txt').write_text('y\n'*64)
print(json.dumps(manifest, sort_keys=True))
print('Evaluator installed. Search baseline unavailable: intake supplies no immutable FroDock pin/configuration or generated predictions.')
PY
