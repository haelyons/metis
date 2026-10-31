#!/usr/bin/env bash
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
mkdir -p out baseline-published data
exec > >(tee -a out/setup.log) 2>&1
# Select only layouts discovered by the probe. Persist selection for all runners.
selected=''
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -f "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
        selected="$root"; break
    fi
done
if [[ -n "$selected" ]]; then
    compiler="$selected/bin/nvcc"; include="$selected/include"; library="$selected/lib64/libcudart.so"
elif [[ -f /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    compiler=/usr/bin/nvcc; include=/usr/include; library=/usr/lib/x86_64-linux-gnu/libcudart.so
else
    echo 'ERROR: no complete CUDA layout from probe' >&2; exit 1
fi
ls "$compiler" "$include/cuda_runtime.h" "$library"
printf 'export CUDACXX=%q\nexport CUDA_INCLUDE_DIR=%q\nexport CUDA_RUNTIME_LIBRARY=%q\n' "$compiler" "$include" "$library" > baseline-published/cuda.env
if [[ -n "$selected" ]]; then
    printf 'export CUDAToolkit_ROOT=%q\nexport PATH=%q/bin:$PATH\n' "$selected" "$selected" >> baseline-published/cuda.env
fi
source baseline-published/cuda.env
packages=(build-essential libopenmpi-dev openmpi-bin libfftw3-dev libfftw3-single3 python3-venv)
missing=()
for package in "${packages[@]}"; do
    if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -qx 'install ok installed'; then missing+=("$package"); fi
done
if ((${#missing[@]})); then
    sudo apt-get update
    for package in "${missing[@]}"; do
        policy=$(apt-cache policy "$package")
        printf '%s\n' "$policy"
        if ! printf '%s\n' "$policy" | grep -Eq 'Candidate: [^ (]'; then
            echo "ERROR: no apt candidate for $package" >&2; exit 1
        fi
        echo "Installing $package"
        sudo apt-get install -y "$package"
        dpkg-query -W "$package"
    done
fi
python3 - <<'PY'
import concurrent.futures, hashlib, json, pathlib, tarfile, time, urllib.request
root=pathlib.Path('baseline-published')
# Bundled archive has Git tree adc153de2eef1ac428c1136d609b30728c88cc7b,
# the published tree of ebeb28a2f8411363cef722b7d293c978f7442672.
if hashlib.sha256(pathlib.Path('harness/pinder-source.tar.gz').read_bytes()).hexdigest()!='5b2e0227f14cd54fa8462e44c5d8c1d857afb7f10071ad2b323e918fe3b2421a':
    raise RuntimeError('Pinned PINDER source archive mismatch')
with tarfile.open('harness/pinder-source.tar.gz') as t:
    prefix=t.getmembers()[0].name.split('/')[0]
    dest=root/'pinder'
    dest.mkdir(exist_ok=True)
    for m in t.getmembers():
        parts=pathlib.PurePosixPath(m.name).parts[1:]
        if not parts: continue
        if '..' in parts or m.issym() or m.islnk(): raise RuntimeError('Unsafe source archive')
        m.name=str(pathlib.PurePosixPath(*parts)); t.extract(m,dest)
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
archive=pathlib.Path('harness/frodock.tar.gz')
if digest(archive)!='91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4': raise RuntimeError('FroDock archive hash mismatch')
with tarfile.open(archive) as t:
    for m in t.getmembers():
        if '..' in pathlib.PurePosixPath(m.name).parts or m.name.startswith('/') or m.issym() or m.islnk(): raise RuntimeError('Unsafe FroDock archive')
    t.extractall(root)
soap=root/'frodock3_linux64/bin/soap.bin'
if digest(soap)!='791f31ec8ef1ef1466092b425638e926755519c9626f5678ca675ef6c76234fc': raise RuntimeError('soap.bin hash mismatch')
items=json.load(open('harness/data.json'))['inventory']
# Download release files only; training archives and unrelated challenge are unnecessary.
items=[x for x in items if x['url'].startswith('https://pinderdata.org/2024-02/') and not x['name'].endswith('.zip')]
def fetch(x):
    name=x['url'].split('/2024-02/',1)[1]
    p=pathlib.Path('data')/name
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists() and digest(p)==x['sha256']: return
    tmp=p.with_name(p.name+'.part')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(x['url'],timeout=90) as r, tmp.open('wb') as f:
                while True:
                    chunk=r.read(1024*1024)
                    if not chunk: break
                    f.write(chunk)
            if digest(tmp)!=x['sha256']: raise RuntimeError('Checksum mismatch '+name)
            tmp.replace(p); return
        except Exception:
            if attempt==2: raise
            time.sleep(1)
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool: list(pool.map(fetch,items))
print('Verified release payloads:',len(items),flush=True)
PY
# Published GNU make targets, in compile_frodock.sh dependency order.
# Select GNU targets only; Intel compiler is not part of the stock image.
for target in \
    libtools/Release_gcc libpdb/Release_gcc libpdb/Release2_gcc \
    libvolume/Release_gcc libfrm/Release_gcc libbessel/Release_gcc \
    libfrodock/Release_MPI_gcc libfrodockcluster/Relase_gcc \
    libprotprot/Release_MPI_gcc libsas/Release_gcc \
    frodock/Release_MPI_gcc frodockgrid/Release_MPI_GCC \
    frodockcluster/Release_gcc frodockview/Release_gcc; do
    make -C "baseline-published/frodock3_linux64/src/$target" clean
    make -C "baseline-published/frodock3_linux64/src/$target" -j 4
done
for binary in frodock_mpi_gcc frodockgrid_mpi_gcc frodockcluster_gcc frodockview_gcc; do
    path="baseline-published/frodock3_linux64/bin/$binary"
    test -x "$path"
    ldd "$path" > "out/ldd-$binary.log" 2>&1 || true
    cat "out/ldd-$binary.log"
    if grep -q 'not found' "out/ldd-$binary.log"; then echo "ERROR: missing library for $binary" >&2; exit 1; fi
done
python3 -m venv --system-site-packages baseline-published/venv
python3 - <<'PY' > baseline-published/stock-constraints.txt
try:
 import torch
 print('torch=='+torch.__version__.split('+')[0])
except ImportError:
 pass
PY
export SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0
baseline-published/venv/bin/python -m pip install -c baseline-published/stock-constraints.txt ./baseline-published/pinder google-cloud-storage gcsfs
PINDER_DATA_DIR="$PWD/data" PINDER_RELEASE=2024-02 baseline-published/venv/bin/python - <<'PY'
import json
from pathlib import Path
from pinder.core import get_index
from pinder.methods.preprocess import prepare_inference_inputs
p=get_index()
ids=sorted(p.loc[p.pinder_s & p.apo_R & p.apo_L,'id'].tolist())
if not ids: raise RuntimeError('No paired apo inputs')
configs=prepare_inference_inputs(Path('data/prepared'),ids=ids,pairs='apo')
byid={c['id']:c for c in configs}
ordered=[{k:str(v) for k,v in byid[i].items()} for i in ids]
Path('data/cases.json').write_text(json.dumps(ordered,indent=2)+'\n')
print('Prepared paired apo inputs:',len(ordered))
PY
echo 'Baseline build and input preparation complete; no docking workload executed.'
