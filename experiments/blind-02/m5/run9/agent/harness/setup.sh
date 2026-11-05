#!/usr/bin/env bash
set -euo pipefail
mkdir -p baseline-published data out/setup
exec > >(tee -a out/setup/setup.log) 2>&1
WORK=$PWD
export PIP_CACHE_DIR="$WORK/out/setup/pip-cache" XDG_CACHE_HOME="$WORK/out/setup/cache"
packages=()
for p in git build-essential libfftw3-dev python3-venv; do
 if ! dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -qx 'install ok installed'; then packages+=("$p"); fi
done
if ((${#packages[@]})); then
 sudo apt-get update
 for p in "${packages[@]}"; do
  apt-cache policy "$p"
  candidate=$(apt-cache policy "$p" | awk '/Candidate:/ {print $2}')
  [[ -n "$candidate" && "$candidate" != '(none)' ]] || { echo "No apt candidate for $p"; exit 1; }
  echo "Installing $p"
  sudo apt-get install -y "$p"
  dpkg-query -W "$p"
 done
fi
CUDA_ROOT=''
for root in /usr/local/cuda /usr/lib/cuda; do
 if [[ -x "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then CUDA_ROOT=$root; break; fi
done
if [[ -n "$CUDA_ROOT" ]]; then
 CUDA_NVCC=$CUDA_ROOT/bin/nvcc; CUDA_INCLUDE=$CUDA_ROOT/include; CUDA_LIB=$CUDA_ROOT/lib64
 export PATH="$CUDA_ROOT/bin:$PATH"
 export CUDAToolkit_ROOT="$CUDA_ROOT"
else
 CUDA_NVCC=/usr/bin/nvcc; CUDA_INCLUDE=/usr/include; CUDA_LIB=/usr/lib/x86_64-linux-gnu
fi
ls "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
[[ -x "$CUDA_NVCC" && -f "$CUDA_INCLUDE/cuda_runtime.h" && -f "$CUDA_LIB/libcudart.so" ]] || { echo 'No complete discovered CUDA layout'; exit 1; }
{
 printf 'export CUDA_NVCC=%q CUDA_INCLUDE=%q CUDA_LIB=%q\n' "$CUDA_NVCC" "$CUDA_INCLUDE" "$CUDA_LIB"
 if [[ -n "$CUDA_ROOT" ]]; then
  printf 'export PATH=%q/bin:"$PATH"\n' "$CUDA_ROOT"
  printf 'export CUDAToolkit_ROOT=%q\n' "$CUDA_ROOT"
 fi
 printf 'export LD_LIBRARY_PATH=%q:"${LD_LIBRARY_PATH:-}"\n' "$CUDA_LIB"
 echo 'ls "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"'
} > baseline-published/cuda-env.sh
source baseline-published/cuda-env.sh
if [[ ! -d baseline-published/megadock/.git ]]; then git clone https://github.com/akiyamalab/MEGADOCK baseline-published/megadock; fi
git -C baseline-published/megadock checkout --detach 9575280c875732553266e26adc607dd892b02616
[[ $(git -C baseline-published/megadock rev-parse HEAD) == 9575280c875732553266e26adc607dd892b02616 ]]
if [[ ! -d baseline-published/cuda-samples/.git ]]; then git clone --depth 1 --branch v12.8 https://github.com/NVIDIA/cuda-samples baseline-published/cuda-samples; fi
[[ $(git -C baseline-published/cuda-samples describe --tags --exact-match) == v12.8 ]]
cap=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader)
cap=$(printf '%s\n' "$cap" | head -n 1 | tr -d '[:space:]')
[[ "$cap" =~ ^[0-9]+\.[0-9]+$ ]] || { echo 'Invalid compute capability'; exit 1; }
target=sm_${cap/./}
printf '%s\n' "$target" | tee out/setup/gpu-target.txt
samples=$WORK/baseline-published/cuda-samples
make -C baseline-published/megadock -j 8 USE_GPU=0 USE_MPI=0 CPPCOMPILER=/usr/bin/g++ FFTW_INSTALL_PATH=/usr FFTW_CFLAGS=-I/usr/include FFTW_LDFLAGS='-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f'
make -C baseline-published/megadock -j 8 USE_GPU=1 USE_MPI=0 CPPCOMPILER=/usr/bin/g++ "SM_VERSIONS=$target" \
 "NVCC=$CUDA_NVCC -Xcompiler -fopenmp -arch=$target -use_fast_math" \
 "INCLUDES=-Isrc -I$CUDA_INCLUDE -I$samples/Common" FFTW_CFLAGS=-I/usr/include \
 "LIB=-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f -L$CUDA_LIB -Wl,-rpath,$CUDA_LIB -lcudart -lcufft"
"$(dirname "$CUDA_NVCC")/cuobjdump" --list-elf baseline-published/megadock/megadock-gpu | tee out/setup/cuda-elf.log
grep -q "$target" out/setup/cuda-elf.log || { echo "Missing code for $target"; exit 1; }
for binary in megadock megadock-gpu; do
 status=0
 baseline-published/megadock/"$binary" -h > "out/setup/$binary-help.log" 2>&1 || status=$?
 [[ $status == 0 || $status == 255 ]] || exit "$status"
 grep -Eqi 'usage' "out/setup/$binary-help.log" || { echo 'Missing usage output'; exit 1; }
done
test -x baseline-published/megadock/decoygen
python3 - <<'PUBLIC_DATA'
import json,hashlib,urllib.request
from pathlib import Path
items=[{'name': 'test_set_pdbs/1a19__A1_P11540-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1a19__A1_P11540-R.pdb', 'bytes': 58320, 'sha256': '08cba0488510ac98b618ab9b963306d7d67459bcab501b54e9dd8214f8f63e63', 'dest': 'data/fixtures/f1a19/R.pdb', 'chain': 'R'}, {'name': 'test_set_pdbs/1a19__B1_P11540-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1a19__B1_P11540-L.pdb', 'bytes': 58320, 'sha256': '9d02d5646d3ba8b13699e83d11ec1d4ed833888e1aa2522d944de0393332bde7', 'dest': 'data/fixtures/f1a19/L.pdb', 'chain': 'L'}, {'name': 'test_set_pdbs/1dtd__A1_P48052-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1dtd__A1_P48052-R.pdb', 'bytes': 192132, 'sha256': '2075e71ae732971c2f78286b554a5baad632f38b383decb8ff8859cd88807394', 'dest': 'data/fixtures/f1dtd/R.pdb', 'chain': 'R'}, {'name': 'test_set_pdbs/1dtd__B1_P81511-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1dtd__B1_P81511-L.pdb', 'bytes': 38313, 'sha256': 'b693ffc0dc24f0cf4ba456bcb7ca115a8f1879e747aa3c87245aeec727315797', 'dest': 'data/fixtures/f1dtd/L.pdb', 'chain': 'L'}, {'name': 'test_set_pdbs/1glj__A1_P0A6F3-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1glj__A1_P0A6F3-R.pdb', 'bytes': 316791, 'sha256': '7131a9741f10136dce36e02b8282a5df0cafc97021fd932c7cf0a92cf8eae87a', 'dest': 'data/fixtures/f1glj/R.pdb', 'chain': 'R'}, {'name': 'test_set_pdbs/1glj__B1_P0A6F3-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1glj__B1_P0A6F3-L.pdb', 'bytes': 316791, 'sha256': '887d53373e51eaa7a717841c3038ebb2e6c31796aad2927a93b698f379c72ca5', 'dest': 'data/fixtures/f1glj/L.pdb', 'chain': 'L'}, {'name': 'test_set_pdbs/1ht8__A1_P05979-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1ht8__A1_P05979-R.pdb', 'bytes': 362718, 'sha256': 'b51981e47c916bb095d67a38bdbab04464a3581d85e51898c33bb2ad44bd5da0', 'dest': 'data/fixtures/f1ht8/R.pdb', 'chain': 'R'}, {'name': 'test_set_pdbs/1ht8__B1_P05979-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1ht8__B1_P05979-L.pdb', 'bytes': 362718, 'sha256': '02e7cb2b1d019063502be0dac261bcc39c8f2b7c558a58af9d9e77ab0b7838d7', 'dest': 'data/fixtures/f1ht8/L.pdb', 'chain': 'L'}]
hashes={}
for s in items:
 p=Path('data/sources')/s['name'];p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  with urllib.request.urlopen(s['url'],timeout=120) as r: blob=r.read()
  t=p.with_suffix('.download');t.write_bytes(blob);t.replace(p)
 blob=p.read_bytes()
 if len(blob)!=s['bytes'] or hashlib.sha256(blob).hexdigest()!=s['sha256']: raise RuntimeError('Input integrity failure: '+str(p))
 prepared=b''.join(line[:21]+s['chain'].encode()+line[22:] if line[:6].strip() in (b'ATOM',b'HETATM',b'ANISOU',b'TER') and len(line)>21 else line for line in blob.splitlines(keepends=True))
 dest=Path(s['dest']);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(prepared)
 hashes[str(dest)]=hashlib.sha256(prepared).hexdigest()
Path('out/setup/prepared-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
PUBLIC_DATA
python3 - <<'PINDER_SOURCE'
import hashlib,urllib.request,tarfile
from pathlib import Path
p=Path('baseline-published/pinder.tar.gz')
if not p.exists():
 with urllib.request.urlopen('https://codeload.github.com/pinder-org/pinder/tar.gz/ebeb28a2f8411363cef722b7d293c978f7442672',timeout=180) as r: p.write_bytes(r.read())
if hashlib.sha256(p.read_bytes()).hexdigest()!='b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd': raise RuntimeError('PINDER archive integrity failure')
if not Path('baseline-published/pinder-src').exists():
 with tarfile.open(p) as t: t.extractall('baseline-published')
 Path('baseline-published/pinder-ebeb28a2f8411363cef722b7d293c978f7442672').rename('baseline-published/pinder-src')
PINDER_SOURCE
python3 -m venv --system-site-packages baseline-published/pinder-venv
VPY="$WORK/baseline-published/pinder-venv/bin/python"
"$VPY" -c 'import torch; print("torch=="+torch.__version__)' > out/setup/constraints.txt
printf 'numpy<2\n' >> out/setup/constraints.txt
"$VPY" -m pip install --no-cache-dir --upgrade 'setuptools>=64' 'setuptools_scm>=8' packaging wheel
SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+gebeb28a2 SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PINDER=0.0.0+gebeb28a2 \
 "$VPY" -m pip install --no-cache-dir --no-build-isolation -c out/setup/constraints.txt "$WORK/baseline-published/pinder-src"
"$VPY" -m pip install --no-cache-dir -c out/setup/constraints.txt fire
"$VPY" -m pip install --no-cache-dir --upgrade -c out/setup/constraints.txt networkx pandas scikit-learn
"$VPY" -c 'from pinder.eval.dockq import BiotiteDockQ; import importlib.metadata; print(importlib.metadata.version("pinder"))'
"$VPY" -m pip freeze > out/setup/pip-freeze.txt
