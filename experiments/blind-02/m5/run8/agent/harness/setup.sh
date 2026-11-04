#!/usr/bin/env bash
set -euo pipefail
mkdir -p baseline-published data out/setup
exec > >(tee -a out/setup/setup.log) 2>&1
export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
export TMPDIR="$PWD/out/setup/tmp"
mkdir -p "$TMPDIR"
install_packages=()
for pkg in libfftw3-dev python3-venv; do
  if ! dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -qx 'install ok installed'; then install_packages+=("$pkg"); fi
done
if ((${#install_packages[@]})); then
  sudo apt-get update
  for pkg in "${install_packages[@]}"; do
    apt-cache policy "$pkg" | tee -a out/setup/apt-policy.log
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
    export CUDAToolkit_ROOT="$root"
    break
  fi
done
if [[ -z "$CUDA_NVCC" ]]; then
  if [[ -x /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    CUDA_NVCC=/usr/bin/nvcc; CUDA_INCLUDE=/usr/include; CUDA_LIB=/usr/lib/x86_64-linux-gnu
  else
    echo 'No complete CUDA toolkit in the probed layouts' >&2; exit 1
  fi
fi
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
export PATH="$(dirname "$CUDA_NVCC"):$PATH"
export LD_LIBRARY_PATH="$CUDA_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
{
  printf 'export CUDA_NVCC=%q CUDA_INCLUDE=%q CUDA_LIB=%q\n' "$CUDA_NVCC" "$CUDA_INCLUDE" "$CUDA_LIB"
  printf 'export PATH=%q:"$PATH"\n' "$(dirname "$CUDA_NVCC")"
  printf 'export LD_LIBRARY_PATH=%q${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}\n' "$CUDA_LIB"
} > baseline-published/cuda-env.sh
"$CUDA_NVCC" --version
pin=9575280c875732553266e26adc607dd892b02616
if [[ ! -d baseline-published/megadock/.git ]]; then
  git clone https://github.com/akiyamalab/MEGADOCK baseline-published/megadock
fi
git -C baseline-published/megadock checkout --detach "$pin"
[[ $(git -C baseline-published/megadock rev-parse HEAD) == "$pin" ]]
[[ -z $(git -C baseline-published/megadock status --porcelain --untracked-files=no) ]] || { echo 'Published checkout has modifications' >&2; exit 1; }
if [[ ! -d baseline-published/cuda-samples/.git ]]; then
  git clone --depth 1 --branch v12.8 https://github.com/NVIDIA/cuda-samples baseline-published/cuda-samples
fi
[[ $(git -C baseline-published/cuda-samples describe --tags --exact-match) == v12.8 ]]
export CUDA_VISIBLE_DEVICES=0
cap=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -n 1 | tr -d '[:space:]')
[[ "$cap" =~ ^[0-9]+\.[0-9]+$ ]] || { echo 'Cannot determine GPU compute capability' >&2; exit 1; }
sm="sm_${cap/./}"
echo "$sm" > out/setup/gpu_target.txt
samples="$PWD/baseline-published/cuda-samples"
make -C baseline-published/megadock -j 8 USE_GPU=0 USE_MPI=0 \
  CPPCOMPILER=/usr/bin/g++ FFTW_INSTALL_PATH=/usr FFTW_CFLAGS=-I/usr/include \
  FFTW_LDFLAGS='-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f'
make -C baseline-published/megadock -j 8 USE_GPU=1 USE_MPI=0 \
  CPPCOMPILER=/usr/bin/g++ "SM_VERSIONS=$sm" \
  "NVCC=$CUDA_NVCC -Xcompiler -fopenmp -arch=$sm -use_fast_math" \
  "INCLUDES=-Isrc -I$CUDA_INCLUDE -I$samples/Common" FFTW_CFLAGS=-I/usr/include \
  "LIB=-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f -L$CUDA_LIB -Wl,-rpath,$CUDA_LIB -lcudart -lcufft"
cuobjdump --list-elf baseline-published/megadock/megadock-gpu | tee out/setup/cuda_elf.log
grep -q "$sm" out/setup/cuda_elf.log || { echo "Binary lacks $sm code" >&2; exit 1; }
for program in megadock megadock-gpu; do
  rc=0
  baseline-published/megadock/"$program" -h > "out/setup/$program-help.log" 2>&1 || rc=$?
  [[ "$rc" == 255 ]] && grep -q 'Usage: megadock' "out/setup/$program-help.log" || { cat "out/setup/$program-help.log"; exit 1; }
done
[[ -x baseline-published/megadock/decoygen ]]
# Keep setup self-contained: auxiliary harness files may not be staged.
# Fixture records below come from comparison_view.json; native references are
# reserved for the evaluator and are not part of setup input preparation.
python3 - <<'PYINPUTS'
import hashlib
import json
import urllib.request
from pathlib import Path

inputs = json.loads(r'''
[
  {
    "id": "f1a19",
    "spec": {
      "receptor_source": {
        "name": "test_set_pdbs/1a19__A1_P11540-R.pdb",
        "url": "https://pinderdata.org/2024-02/test_set_pdbs/1a19__A1_P11540-R.pdb",
        "bytes": 58320,
        "sha256": "08cba0488510ac98b618ab9b963306d7d67459bcab501b54e9dd8214f8f63e63"
      },
      "ligand_source": {
        "name": "test_set_pdbs/1a19__B1_P11540-L.pdb",
        "url": "https://pinderdata.org/2024-02/test_set_pdbs/1a19__B1_P11540-L.pdb",
        "bytes": 58320,
        "sha256": "9d02d5646d3ba8b13699e83d11ec1d4ed833888e1aa2522d944de0393332bde7"
      },
      "prepared": {
        "receptor": "data/fixtures/f1a19/R.pdb",
        "ligand": "data/fixtures/f1a19/L.pdb"
      }
    }
  },
  {
    "id": "f1dtd",
    "spec": {
      "receptor_source": {
        "name": "test_set_pdbs/1dtd__A1_P48052-R.pdb",
        "url": "https://pinderdata.org/2024-02/test_set_pdbs/1dtd__A1_P48052-R.pdb",
        "bytes": 192132,
        "sha256": "2075e71ae732971c2f78286b554a5baad632f38b383decb8ff8859cd88807394"
      },
      "ligand_source": {
        "name": "test_set_pdbs/1dtd__B1_P81511-L.pdb",
        "url": "https://pinderdata.org/2024-02/test_set_pdbs/1dtd__B1_P81511-L.pdb",
        "bytes": 38313,
        "sha256": "b693ffc0dc24f0cf4ba456bcb7ca115a8f1879e747aa3c87245aeec727315797"
      },
      "prepared": {
        "receptor": "data/fixtures/f1dtd/R.pdb",
        "ligand": "data/fixtures/f1dtd/L.pdb"
      }
    }
  },
  {
    "id": "f1glj",
    "spec": {
      "receptor_source": {
        "name": "test_set_pdbs/1glj__A1_P0A6F3-R.pdb",
        "url": "https://pinderdata.org/2024-02/test_set_pdbs/1glj__A1_P0A6F3-R.pdb",
        "bytes": 316791,
        "sha256": "7131a9741f10136dce36e02b8282a5df0cafc97021fd932c7cf0a92cf8eae87a"
      },
      "ligand_source": {
        "name": "test_set_pdbs/1glj__B1_P0A6F3-L.pdb",
        "url": "https://pinderdata.org/2024-02/test_set_pdbs/1glj__B1_P0A6F3-L.pdb",
        "bytes": 316791,
        "sha256": "887d53373e51eaa7a717841c3038ebb2e6c31796aad2927a93b698f379c72ca5"
      },
      "prepared": {
        "receptor": "data/fixtures/f1glj/R.pdb",
        "ligand": "data/fixtures/f1glj/L.pdb"
      }
    }
  },
  {
    "id": "f1ht8",
    "spec": {
      "receptor_source": {
        "name": "test_set_pdbs/1ht8__A1_P05979-R.pdb",
        "url": "https://pinderdata.org/2024-02/test_set_pdbs/1ht8__A1_P05979-R.pdb",
        "bytes": 362718,
        "sha256": "b51981e47c916bb095d67a38bdbab04464a3581d85e51898c33bb2ad44bd5da0"
      },
      "ligand_source": {
        "name": "test_set_pdbs/1ht8__B1_P05979-L.pdb",
        "url": "https://pinderdata.org/2024-02/test_set_pdbs/1ht8__B1_P05979-L.pdb",
        "bytes": 362718,
        "sha256": "02e7cb2b1d019063502be0dac261bcc39c8f2b7c558a58af9d9e77ab0b7838d7"
      },
      "prepared": {
        "receptor": "data/fixtures/f1ht8/R.pdb",
        "ligand": "data/fixtures/f1ht8/L.pdb"
      }
    }
  }
]
''')
hashes = {}
for item in inputs:
    spec = item['spec']
    for role, chain in [('receptor', b'R'), ('ligand', b'L')]:
        source = spec[role + '_source']
        source_path = Path('data/sources') / source['name']
        source_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.exists():
            original = source_path.read_bytes()
        else:
            with urllib.request.urlopen(source['url'], timeout=120) as response:
                original = response.read()
        if (len(original) != source['bytes'] or
                hashlib.sha256(original).hexdigest() != source['sha256']):
            raise ValueError('Invalid source bytes/hash: ' + source['name'])
        source_path.write_bytes(original)
        lines = []
        for line in original.splitlines(keepends=True):
            if line[:6] in (b'ATOM  ', b'HETATM', b'ANISOU', b'TER   '):
                if len(line.rstrip(b'\r\n')) < 22:
                    raise ValueError('Short chain-bearing record: ' + source['name'])
                line = line[:21] + chain + line[22:]
            lines.append(line)
        prepared = b''.join(lines)
        destination = Path(spec['prepared'][role])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(prepared)
        digest = hashlib.sha256(prepared).hexdigest()
        hashes[str(destination)] = digest
        print('Prepared', destination, 'sha256', digest)
Path('out/setup/prepared_sha256.json').write_text(json.dumps(hashes, indent=2) + '\n')
PYINPUTS
python3 - <<'PYEVALUATOR'
import hashlib
import io
import tarfile
import urllib.request
from pathlib import Path

pin = 'ebeb28a2f8411363cef722b7d293c978f7442672'
archive = Path('baseline-published/pinder.tar.gz')
if archive.exists():
    data = archive.read_bytes()
else:
    with urllib.request.urlopen(
            'https://codeload.github.com/pinder-org/pinder/tar.gz/' + pin,
            timeout=180) as response:
        data = response.read()
if hashlib.sha256(data).hexdigest() != 'b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd':
    raise ValueError('PINDER source archive SHA-256 mismatch')
archive.write_bytes(data)
destination = Path('baseline-published/pinder-src')
destination.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tf:
    for member in tf.getmembers():
        parts = Path(member.name).parts
        if not parts or parts[0] != 'pinder-' + pin or '..' in parts:
            raise ValueError('Unexpected source archive member')
        if len(parts) == 1:
            continue
        if member.issym() or member.islnk():
            raise ValueError('Unexpected source archive link')
        member.name = str(Path(*parts[1:]))
        tf.extract(member, destination)
PYEVALUATOR
VENV="$PWD/baseline-published/eval-venv"
VPY="$VENV/bin/python"
python3 -m venv --system-site-packages "$VENV"
python3 - <<'PY' > out/setup/stock_torch_constraints.txt
import importlib.metadata
print('torch=='+importlib.metadata.version('torch'))
PY
export PIP_CONSTRAINT="$PWD/out/setup/stock_torch_constraints.txt"
"$VPY" -m pip install --no-cache-dir --upgrade 'setuptools>=64' 'setuptools_scm>=8' packaging wheel 2>&1 | tee -a out/setup/pip_build.log
SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+gebeb28a2 SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PINDER=0.0.0+gebeb28a2 \
  "$VPY" -m pip install --no-cache-dir --no-build-isolation "$PWD/baseline-published/pinder-src" 2>&1 | tee -a out/setup/pip_pinder.log
"$VPY" -m pip install --no-cache-dir fire 'numpy<2' 'biotite==1.2.0' 2>&1 | tee -a out/setup/pip_extra.log
printf 'numpy<2\n' > out/setup/venv_constraints.txt
"$VPY" -m pip install --no-cache-dir --upgrade -c out/setup/venv_constraints.txt networkx pandas scikit-learn 2>&1 | tee -a out/setup/pip_refresh.log
PYTHONDONTWRITEBYTECODE=1 "$VPY" - <<'PY'
import importlib.metadata
from pinder.eval.dockq import BiotiteDockQ
import torch
print('PINDER', importlib.metadata.version('pinder'))
print('torch', torch.__version__)
PY
"$VPY" -B - <<'PYVERSIONS' > out/setup/versions.json
import importlib.metadata
import json
from pathlib import Path

pin = '9575280c875732553266e26adc607dd892b02616'
result = {
    arm: {
        'version': pin,
        'executable': 'baseline-published/megadock/' +
                      ('megadock-gpu' if arm in ['A1', 'A3'] else 'megadock'),
    }
    for arm in ['A0', 'A1', 'A2', 'A3']
}
result['evaluator'] = {
    'version': importlib.metadata.version('pinder'),
    'executable': 'baseline-published/eval-venv/bin/python',
}
for record in result.values():
    if not Path(record['executable']).is_file():
        raise FileNotFoundError(record['executable'])
print(json.dumps(result))
PYVERSIONS
