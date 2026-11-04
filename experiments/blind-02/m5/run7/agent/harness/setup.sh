#!/usr/bin/env bash
set -euo pipefail
mkdir -p baseline-published data out/setup
exec > >(tee -a out/setup/setup.log) 2>&1
export PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
export TMPDIR="$PWD/out/setup/tmp"
mkdir -p "$TMPDIR"
missing=()
for pkg in build-essential git curl ca-certificates libfftw3-dev python3-venv; do
    if ! dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -qx 'install ok installed'; then missing+=("$pkg"); fi
done
if ((${#missing[@]})); then
    sudo apt-get update
    for pkg in "${missing[@]}"; do
        apt-cache policy "$pkg"
        candidate=$(apt-cache policy "$pkg" | awk '/Candidate:/ {print $2}')
        [[ -n "$candidate" && "$candidate" != '(none)' ]] || { echo "No install candidate: $pkg" >&2; exit 1; }
        echo "Installing $pkg"
        sudo apt-get install -y "$pkg"
        dpkg-query -W "$pkg"
    done
fi
CUDA_ROOT=''
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -x "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then CUDA_ROOT="$root"; break; fi
done
if [[ -n "$CUDA_ROOT" ]]; then
    CUDA_NVCC="$CUDA_ROOT/bin/nvcc"; CUDA_INCLUDE="$CUDA_ROOT/include"; CUDA_LIB="$CUDA_ROOT/lib64"
else
    CUDA_NVCC=/usr/bin/nvcc; CUDA_INCLUDE=/usr/include; CUDA_LIB=/usr/lib/x86_64-linux-gnu
fi
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
[[ -x "$CUDA_NVCC" && -f "$CUDA_INCLUDE/cuda_runtime.h" && -f "$CUDA_LIB/libcudart.so" ]] || { echo 'No complete probed CUDA layout' >&2; exit 1; }
export PATH="$(dirname "$CUDA_NVCC"):$PATH"
{
    printf 'export CUDA_NVCC=%q CUDA_INCLUDE=%q CUDA_LIB=%q\n' "$CUDA_NVCC" "$CUDA_INCLUDE" "$CUDA_LIB"
    printf 'export PATH=%q:"$PATH"\n' "$(dirname "$CUDA_NVCC")"
} > baseline-published/cuda-env.sh
pin=9575280c875732553266e26adc607dd892b02616
if [[ ! -d baseline-published/megadock/.git ]]; then git clone https://github.com/akiyamalab/MEGADOCK baseline-published/megadock; fi
git -C baseline-published/megadock checkout --detach "$pin"
[[ "$(git -C baseline-published/megadock rev-parse HEAD)" == "$pin" ]]
if [[ ! -d baseline-published/cuda-samples/.git ]]; then git clone --depth 1 --branch v12.8 https://github.com/NVIDIA/cuda-samples baseline-published/cuda-samples; fi
[[ "$(git -C baseline-published/cuda-samples describe --tags --exact-match)" == v12.8 ]]
samples="$PWD/baseline-published/cuda-samples"
make -C baseline-published/megadock -j 8 USE_GPU=0 USE_MPI=0 \
 CPPCOMPILER=/usr/bin/g++ FFTW_INSTALL_PATH=/usr \
 FFTW_CFLAGS=-I/usr/include FFTW_LDFLAGS='-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f'
make -C baseline-published/megadock -j 8 USE_GPU=1 USE_MPI=0 \
 CPPCOMPILER=/usr/bin/g++ SM_VERSIONS=sm_90 \
 "NVCC=$CUDA_NVCC -Xcompiler -fopenmp -arch=sm_90 -use_fast_math" \
 "INCLUDES=-Isrc -I$CUDA_INCLUDE -I$samples/Common" FFTW_CFLAGS=-I/usr/include \
 "LIB=-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f -L$CUDA_LIB -Wl,-rpath,$CUDA_LIB -lcudart -lcufft"
for exe in megadock megadock-gpu; do
    rc=0
    baseline-published/megadock/"$exe" -h > "out/setup/$exe-help.log" 2>&1 || rc=$?
    [[ "$rc" == 0 || "$rc" == 255 ]]
    grep -Ei 'usage|options' "out/setup/$exe-help.log"
done

python3 - <<'PYDATA'
import hashlib,json,pathlib,urllib.request
items=[{'id': 'f1a19', 'prepared': {'receptor': 'data/fixtures/f1a19/R.pdb', 'ligand': 'data/fixtures/f1a19/L.pdb'}, 'receptor_source': {'name': 'test_set_pdbs/1a19__A1_P11540-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1a19__A1_P11540-R.pdb', 'bytes': 58320, 'sha256': '08cba0488510ac98b618ab9b963306d7d67459bcab501b54e9dd8214f8f63e63'}, 'ligand_source': {'name': 'test_set_pdbs/1a19__B1_P11540-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1a19__B1_P11540-L.pdb', 'bytes': 58320, 'sha256': '9d02d5646d3ba8b13699e83d11ec1d4ed833888e1aa2522d944de0393332bde7'}}, {'id': 'f1dtd', 'prepared': {'receptor': 'data/fixtures/f1dtd/R.pdb', 'ligand': 'data/fixtures/f1dtd/L.pdb'}, 'receptor_source': {'name': 'test_set_pdbs/1dtd__A1_P48052-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1dtd__A1_P48052-R.pdb', 'bytes': 192132, 'sha256': '2075e71ae732971c2f78286b554a5baad632f38b383decb8ff8859cd88807394'}, 'ligand_source': {'name': 'test_set_pdbs/1dtd__B1_P81511-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1dtd__B1_P81511-L.pdb', 'bytes': 38313, 'sha256': 'b693ffc0dc24f0cf4ba456bcb7ca115a8f1879e747aa3c87245aeec727315797'}}, {'id': 'f1glj', 'prepared': {'receptor': 'data/fixtures/f1glj/R.pdb', 'ligand': 'data/fixtures/f1glj/L.pdb'}, 'receptor_source': {'name': 'test_set_pdbs/1glj__A1_P0A6F3-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1glj__A1_P0A6F3-R.pdb', 'bytes': 316791, 'sha256': '7131a9741f10136dce36e02b8282a5df0cafc97021fd932c7cf0a92cf8eae87a'}, 'ligand_source': {'name': 'test_set_pdbs/1glj__B1_P0A6F3-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1glj__B1_P0A6F3-L.pdb', 'bytes': 316791, 'sha256': '887d53373e51eaa7a717841c3038ebb2e6c31796aad2927a93b698f379c72ca5'}}, {'id': 'f1ht8', 'prepared': {'receptor': 'data/fixtures/f1ht8/R.pdb', 'ligand': 'data/fixtures/f1ht8/L.pdb'}, 'receptor_source': {'name': 'test_set_pdbs/1ht8__A1_P05979-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1ht8__A1_P05979-R.pdb', 'bytes': 362718, 'sha256': 'b51981e47c916bb095d67a38bdbab04464a3581d85e51898c33bb2ad44bd5da0'}, 'ligand_source': {'name': 'test_set_pdbs/1ht8__B1_P05979-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1ht8__B1_P05979-L.pdb', 'bytes': 362718, 'sha256': '02e7cb2b1d019063502be0dac261bcc39c8f2b7c558a58af9d9e77ab0b7838d7'}}]
hashes={}
for item in items:
    for role,chain in [('receptor','R'),('ligand','L')]:
        spec=item[role+'_source']
        dst=pathlib.Path('data/sources')/spec['name'];dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():
            content=urllib.request.urlopen(spec['url'],timeout=180).read()
            if len(content)!=spec['bytes'] or hashlib.sha256(content).hexdigest()!=spec['sha256']: raise RuntimeError('Input checksum mismatch: '+spec['name'])
            dst.write_bytes(content)
        content=dst.read_bytes()
        if len(content)!=spec['bytes'] or hashlib.sha256(content).hexdigest()!=spec['sha256']: raise RuntimeError('Input checksum mismatch: '+str(dst))
        prepared=b''.join(line[:21]+chain.encode()+line[22:] if line[:6].strip() in (b'ATOM',b'HETATM',b'ANISOU',b'TER') and len(line.rstrip(b'\r\n'))>=22 else line for line in content.splitlines(keepends=True))
        out=pathlib.Path(item['prepared'][role]);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(prepared)
        hashes[str(out)]=hashlib.sha256(prepared).hexdigest()
pathlib.Path('out/setup/prepared_sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
PYDATA
python3 - <<'PYSOURCE'
import hashlib,urllib.request,pathlib,tarfile
pin='ebeb28a2f8411363cef722b7d293c978f7442672'
p=pathlib.Path('baseline-published/pinder.tar.gz')
if not p.exists():
    p.write_bytes(urllib.request.urlopen('https://codeload.github.com/pinder-org/pinder/tar.gz/'+pin,timeout=180).read())
if hashlib.sha256(p.read_bytes()).hexdigest()!='b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd': raise RuntimeError('PINDER archive checksum mismatch')
if not pathlib.Path('baseline-published/pinder-src').exists():
    with tarfile.open(p) as t:t.extractall('baseline-published')
    pathlib.Path('baseline-published/pinder-'+pin).rename('baseline-published/pinder-src')
PYSOURCE
python3 -m venv --system-site-packages baseline-published/evaluator-venv
VPY="$PWD/baseline-published/evaluator-venv/bin/python"
"$VPY" - <<'PYTORCH'
import torch,pathlib
pathlib.Path('out/setup/torch-constraint.txt').write_text('torch=='+torch.__version__+'\n')
PYTORCH
export PIP_CONSTRAINT="$PWD/out/setup/torch-constraint.txt"
"$VPY" -m pip install --no-cache-dir --upgrade 'setuptools>=64' 'setuptools_scm>=8' packaging wheel
SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+gebeb28a2 SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PINDER=0.0.0+gebeb28a2 \
 "$VPY" -m pip install --no-cache-dir --no-build-isolation "$PWD/baseline-published/pinder-src"
"$VPY" -m pip install --no-cache-dir fire
printf 'numpy<2\n' > out/setup/venv_constraints.txt
"$VPY" -m pip install --no-cache-dir --upgrade -c out/setup/venv_constraints.txt networkx pandas scikit-learn
"$VPY" - <<'PYCHECK'
from pinder.eval.dockq import BiotiteDockQ
import importlib.metadata,torch
print('PINDER',importlib.metadata.version('pinder'))
print('torch',torch.__version__)
PYCHECK
