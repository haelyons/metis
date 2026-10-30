#!/usr/bin/env bash
set -euo pipefail
mkdir -p baseline-published data out
exec > >(tee -a out/setup.log) 2>&1
# Select only toolkit layouts discovered by the supplied box probe.
compiler= include= library= toolkit=
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -f "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
        compiler="$root/bin/nvcc"; include="$root/include"; library="$root/lib64"; toolkit="$root"; break
    fi
done
if [[ -z "$compiler" ]]; then
    compiler=/usr/bin/nvcc; include=/usr/include; library=/usr/lib/x86_64-linux-gnu
fi
ls "$compiler" "$include/cuda_runtime.h" "$library/libcudart.so"
export PATH="$(dirname "$compiler"):$PATH"
export CUDACXX="$compiler" OPENMM_CUDA_COMPILER="$compiler"
if [[ -n "$toolkit" ]]; then export CUDAToolkit_ROOT="$toolkit" CUDA_HOME="$toolkit"; fi
export CPATH="$include${CPATH:+:$CPATH}" LIBRARY_PATH="$library${LIBRARY_PATH:+:$LIBRARY_PATH}"
export LD_LIBRARY_PATH="$library${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python3 - "$compiler" "$include" "$library" "$toolkit" <<'PY'
import hashlib,json,os,pathlib,sys,urllib.request,zipfile
base=pathlib.Path('baseline-published'); data=pathlib.Path('data')
def fetch(url,path,digest):
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        tmp=path.with_suffix(path.suffix+'.download')
        with urllib.request.urlopen(url,timeout=120) as src, tmp.open('wb') as dst:
            import shutil; shutil.copyfileobj(src,dst)
        if hashlib.sha256(tmp.read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Download hash mismatch: '+str(path))
        tmp.replace(path)
archive=data/'pcbi.1005659.s001.zip'
fetch('https://ndownloader.figshare.com/files/9068653',archive,'3ad3f355af4ca1e459c7fd1131d8a474e1f5430223ce90a9c34ee98862ecb09d')
with zipfile.ZipFile(archive) as z:
    # Extract published distribution without rewriting executable source.
    for member in z.infolist():
        target=(base/member.filename).resolve()
        if not target.is_relative_to(base.resolve()): raise RuntimeError('Unsafe archive path')
    z.extractall(base)
script=base/'SI/Benchmarks/energyBenchmarks.py'
if hashlib.sha256(script.read_bytes()).hexdigest()!='e6b0d107618f4b166b55ed515c1661d3f08292301b37375f7d6ddbfc637262ed':
    raise RuntimeError('Baseline executable hash mismatch')
pdb=base/'SI/Benchmarks/dhfr.pdb'
if hashlib.sha256(pdb.read_bytes()).hexdigest()!='fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf':
    raise RuntimeError('PDB hash mismatch')
import shutil
shutil.copyfile(pdb,data/'dhfr.pdb')
for name,digest in [('amber99sbildn.xml','27b79a1ff342d95d6347f3f4797b4c84dbdf98e2c838d1b6b18979f77b04110d'),('tip3p.xml','607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c')]:
    fetch('https://raw.githubusercontent.com/openmm/openmm/8.2.0/wrappers/python/openmm/app/data/'+name,data/name,digest)
    shutil.copyfile(data/name,base/'SI/Benchmarks'/name)
json.dump(dict(zip(['compiler','include','library','toolkit'],sys.argv[1:])),(base/'cuda-layout.json').open('w'))
json.dump(['dhfr-energy-drift-single','dhfr-energy-drift-mixed','dhfr-energy-drift-double'],(base/'item-ids.json').open('w'))
PY
# Published unversioned binary-install route; private target preserves stock packages.
python3 -m pip install --upgrade --target baseline-published/python-packages 'openmm[cuda12]' scipy
export PYTHONPATH="$PWD/baseline-published/python-packages"
export PYTHONDONTWRITEBYTECODE=1
python3 - <<'PY'
import json,openmm,scipy
from openmm.app import PDBFile,ForceField
from pathlib import Path
p=Path('baseline-published/SI/Benchmarks')
pdb=PDBFile(str(p/'dhfr.pdb'))
if pdb.topology.getNumAtoms()!=23558: raise RuntimeError('Incorrect input atom count')
ForceField(str(p/'amber99sbildn.xml'),str(p/'tip3p.xml'))
platform=openmm.Platform.getPlatformByName('CUDA')
info={'openmm':openmm.__version__,'scipy':scipy.__version__,'platform':platform.getName(),'atoms':pdb.topology.getNumAtoms(),'plugin_failures':openmm.Platform.getPluginLoadFailures()}
print(json.dumps(info))
Path('baseline-published/runtime.json').write_text(json.dumps(info,indent=2)+'\n')
PY
