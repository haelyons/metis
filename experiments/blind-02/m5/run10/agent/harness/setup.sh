#!/usr/bin/env bash
set -euo pipefail

mkdir -p out/setup baseline-published data/inputs data/sources
exec > >(tee -a out/setup/setup.log) 2>&1
export PIP_CACHE_DIR="$PWD/out/setup/pip-cache"
export TMPDIR="$PWD/out/setup/tmp"
mkdir -p "$TMPDIR"
missing=()
for pkg in git build-essential libfftw3-dev python3-venv; do
 if ! dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q 'install ok installed'; then missing+=("$pkg"); fi
done
if ((${#missing[@]})); then
 sudo apt-get update
 for pkg in "${missing[@]}"; do
  apt-cache policy "$pkg"
  candidate=$(apt-cache policy "$pkg" | awk '/Candidate:/ {print $2}')
  [[ -n "$candidate" && "$candidate" != '(none)' ]] || { echo "No apt candidate for $pkg" >&2; exit 1; }
  echo "Installing $pkg"
  sudo apt-get install -y "$pkg"
  dpkg-query -W "$pkg"
 done
fi
CUDA_NVCC= CUDA_INCLUDE= CUDA_LIB=
for root in /usr/local/cuda /usr/lib/cuda; do
 if [[ -x "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
  CUDA_NVCC="$root/bin/nvcc"; CUDA_INCLUDE="$root/include"; CUDA_LIB="$root/lib64"
  export PATH="$root/bin:$PATH"
  break
 fi
done
if [[ -z "$CUDA_NVCC" ]]; then
 CUDA_NVCC=/usr/bin/nvcc; CUDA_INCLUDE=/usr/include; CUDA_LIB=/usr/lib/x86_64-linux-gnu
fi
ls "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
export CUDA_NVCC CUDA_INCLUDE CUDA_LIB
printf 'nvcc=%s include=%s lib=%s\n' "$CUDA_NVCC" "$CUDA_INCLUDE" "$CUDA_LIB"
"$CUDA_NVCC" --version
cap=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -n 1 | tr -d ' \r')
[[ "$cap" =~ ^[0-9]+\.[0-9]+$ ]] || { echo 'Invalid compute capability' >&2; exit 1; }
sm="sm_${cap/./}"
printf '%s\n' "$sm" | tee out/setup/gpu_target.txt
if [[ ! -d baseline-published/megadock/.git ]]; then
 git clone https://github.com/akiyamalab/MEGADOCK baseline-published/megadock
fi
git -C baseline-published/megadock checkout --detach 9575280c875732553266e26adc607dd892b02616
[[ $(git -C baseline-published/megadock rev-parse HEAD) == 9575280c875732553266e26adc607dd892b02616 ]]
if [[ ! -d baseline-published/cuda-samples/.git ]]; then
 git clone --depth 1 --branch v12.8 https://github.com/NVIDIA/cuda-samples baseline-published/cuda-samples
fi
[[ $(git -C baseline-published/cuda-samples describe --tags --exact-match) == v12.8 ]]
samples="$PWD/baseline-published/cuda-samples"
make -C baseline-published/megadock -j 8 USE_GPU=0 USE_MPI=0 \
 CPPCOMPILER=/usr/bin/g++ FFTW_INSTALL_PATH=/usr \
 FFTW_CFLAGS=-I/usr/include FFTW_LDFLAGS='-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f'
make -C baseline-published/megadock -j 8 USE_GPU=1 USE_MPI=0 \
 CPPCOMPILER=/usr/bin/g++ "SM_VERSIONS=$sm" \
 "NVCC=$CUDA_NVCC -Xcompiler -fopenmp -arch=$sm -use_fast_math" \
 "INCLUDES=-Isrc -I$CUDA_INCLUDE -I$samples/Common" FFTW_CFLAGS=-I/usr/include \
 "LIB=-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f -L$CUDA_LIB -Wl,-rpath,$CUDA_LIB -lcudart -lcufft"
cuobjdump="$(dirname "$CUDA_NVCC")/cuobjdump"
"$cuobjdump" --list-elf baseline-published/megadock/megadock-gpu | tee out/setup/cuda_elf.log
grep -q "$sm" out/setup/cuda_elf.log
for binary in megadock megadock-gpu; do
 rc=0
 baseline-published/megadock/"$binary" -h > "out/setup/$binary.help.log" 2>&1 || rc=$?
 [[ "$rc" == 0 || "$rc" == 255 ]]
 grep -qi 'usage' "out/setup/$binary.help.log"
done
test -x baseline-published/megadock/decoygen
python3 - <<'PYDATA'
import hashlib,json,pathlib,urllib.request
items=json.loads('[{"id": "1aua", "receptor_source": {"name": "pdbs/6f0e__A1_P24280.pdb", "url": "https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb", "bytes": 192456, "sha256": ["622eacb7b46e1a4c2", "5d1", "6aa1c5", "6a0546d1b2", "3d31a4", "1aad5c275886159f6d98cd"]}, "ligand_source": {"name": "pdbs/6f0e__A1_P24280.pdb", "url": "https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb", "bytes": 192456, "sha256": ["622eacb7b46e1a4c2", "5d1", "6aa1c5", "6a0546d1b2", "3d31a4", "1aad5c275886159f6d98cd"]}, "prepared": {"receptor": "data/inputs/1aua_R.pdb", "ligand": "data/inputs/1aua_L.pdb"}, "prepared_sha256": {"receptor": ["162aad227fdbdb6a0600a5b6a4f5b461663ee7ce419798061ea0cd8ae9be6f35"], "ligand": ["f5158ee7030ce712cc5fb419d1e7532d4db2d4b4ddb64b50a5d0d9e45a973600"]}}, {"id": "1ax2", "receptor_source": {"name": "pdbs/3n35__A1_P16404.pdb", "url": "https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb", "bytes": 151794, "sha256": ["b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e"]}, "ligand_source": {"name": "pdbs/3n35__A1_P16404.pdb", "url": "https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb", "bytes": 151794, "sha256": ["b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e"]}, "prepared": {"receptor": "data/inputs/1ax2_R.pdb", "ligand": "data/inputs/1ax2_L.pdb"}, "prepared_sha256": {"receptor": ["a9be54841e5e92e301558c198a7188b6765ab3", "4cf30cb5d939b46f99db103d35"], "ligand": ["8d3948ddc69f493dfeea785aefc09f3de7b191ab7f8250dc102f63dc1d35810e"]}}, {"id": "1dv1", "receptor_source": {"name": "pdbs/3g8c__A1_P24182.pdb", "url": "https://pinderdata.org/2024-02/pdbs/3g8c__A1_P24182.pdb", "bytes": 277182, "sha256": ["48aa5f4b2ac1e57d855b85d5", "6a9c4a74c4b1", "6f7d165b0fce03535815e26bdb60"]}, "ligand_source": {"name": "pdbs/3g8d__A1_P24182.pdb", "url": "https://pinderdata.org/2024-02/pdbs/3g8d__A1_P24182.pdb", "bytes": 234657, "sha256": ["1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c"]}, "prepared": {"receptor": "data/inputs/1dv1_R.pdb", "ligand": "data/inputs/1dv1_L.pdb"}, "prepared_sha256": {"receptor": ["880a12d8a36e84fc8bea31cb4105284827ce1a985128413e4e8f70582fe52ea2"], "ligand": ["f9c72e23a1f2afe893c672da0412e82fa8345be23902d1d5cc7c17971193f623"]}}, {"id": "1nr5", "receptor_source": {"name": "pdbs/1sg6__A1_P07547.pdb", "url": "https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb", "bytes": 234171, "sha256": ["4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5"]}, "ligand_source": {"name": "pdbs/1sg6__A1_P07547.pdb", "url": "https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb", "bytes": 234171, "sha256": ["4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5"]}, "prepared": {"receptor": "data/inputs/1nr5_R.pdb", "ligand": "data/inputs/1nr5_L.pdb"}, "prepared_sha256": {"receptor": ["ec52d962eacf8e92518ead142a51f6feb18e8d74590ea7048fffc461f52cacf2"], "ligand": ["83ad5cf3938c63172fea2254e31e6fe05d5751d072323ff7ed3463d92af0d1a2"]}}]')

for item in items:
 for role,chain in [('receptor','R'),('ligand','L')]:
  spec=item[role+'_source']; p=pathlib.Path('data/sources')/spec['name']
  p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():
   with urllib.request.urlopen(spec['url'],timeout=120) as r: raw=r.read()
  else: raw=p.read_bytes()
  if len(raw)!=spec['bytes'] or hashlib.sha256(raw).hexdigest()!=''.join(spec['sha256']):
   raise ValueError('Source checksum/size mismatch: '+str(p))
  if not p.exists(): p.write_bytes(raw)
  prepared=b''.join(line[:21]+chain.encode()+line[22:] if line[:6].strip() in (b'ATOM',b'HETATM',b'ANISOU',b'TER') else line for line in raw.splitlines(keepends=True))
  digest=hashlib.sha256(prepared).hexdigest()
  if digest!=''.join(item['prepared_sha256'][role]): raise ValueError('Prepared checksum mismatch')
  pathlib.Path(item['prepared'][role]).write_bytes(prepared)
  print(item['id'],role,digest)
PYDATA
python3 - <<'PYSRC'
import hashlib,pathlib,urllib.request,tarfile
p=pathlib.Path('out/setup/pinder.tar.gz')
if not p.exists():
 with urllib.request.urlopen('https://codeload.github.com/pinder-org/pinder/tar.gz/ebeb28a2f8411363cef722b7d293c978f7442672',timeout=120) as r:p.write_bytes(r.read())
if hashlib.sha256(p.read_bytes()).hexdigest()!='b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd': raise ValueError('PINDER archive checksum mismatch')
dest=pathlib.Path('baseline-published/pinder-src')
if not dest.exists():
 with tarfile.open(p) as t:t.extractall('baseline-published')
 pathlib.Path('baseline-published/pinder-ebeb28a2f8411363cef722b7d293c978f7442672').rename(dest)
PYSRC
VENV="$PWD/baseline-published/evaluator-venv"
python3 -m venv --system-site-packages "$VENV"
VPY="$VENV/bin/python"
"$VPY" -m pip install --no-cache-dir --upgrade 'setuptools>=64' 'setuptools_scm>=8' packaging wheel 2>&1 | tee -a out/setup/pip_build.log
python3 -c 'import torch; print("torch=="+torch.__version__)' > out/setup/torch_constraint.txt
SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+gebeb28a2 SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PINDER=0.0.0+gebeb28a2 \
 "$VPY" -m pip install --no-cache-dir --no-build-isolation -c out/setup/torch_constraint.txt "$PWD/baseline-published/pinder-src" 2>&1 | tee -a out/setup/pip_pinder.log
"$VPY" -m pip install --no-cache-dir fire 2>&1 | tee -a out/setup/pip_fire.log
printf 'numpy<2\n' > out/setup/venv_constraints.txt
"$VPY" -m pip install --no-cache-dir --upgrade -c out/setup/venv_constraints.txt networkx pandas scikit-learn 2>&1 | tee -a out/setup/pip_refresh.log
"$VPY" -c 'from pinder.eval.dockq import BiotiteDockQ; import importlib.metadata; print(importlib.metadata.version("pinder"))'
