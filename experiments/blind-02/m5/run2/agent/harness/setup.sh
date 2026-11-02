#!/usr/bin/env bash
set -euo pipefail
mkdir -p out/setup baseline-published data
exec > >(tee -a out/setup/setup.log) 2>&1
trap 'echo "setup failed at line $LINENO" >&2' ERR
# Select only layouts discovered by the box probe. Persist selection for all runs.
CUDA_NVCC= CUDA_INCLUDE= CUDA_LIB=
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -x "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -e "$root/lib64/libcudart.so" ]]; then
        CUDA_NVCC="$root/bin/nvcc" CUDA_INCLUDE="$root/include" CUDA_LIB="$root/lib64"
        break
    fi
done
if [[ -z "$CUDA_NVCC" ]]; then
    if [[ -x /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -e /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
        CUDA_NVCC=/usr/bin/nvcc CUDA_INCLUDE=/usr/include CUDA_LIB=/usr/lib/x86_64-linux-gnu
    else
        echo 'No complete probed CUDA toolkit or distro layout' >&2; exit 1
    fi
fi
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
export PATH="${CUDA_NVCC%/nvcc}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export LD_LIBRARY_PATH="$CUDA_LIB"
"$CUDA_NVCC" --version
printf 'export CUDA_NVCC=%q CUDA_INCLUDE=%q CUDA_LIB=%q\nexport PATH=%q\nexport LD_LIBRARY_PATH=%q\n' \
    "$CUDA_NVCC" "$CUDA_INCLUDE" "$CUDA_LIB" "$PATH" "$LD_LIBRARY_PATH" > baseline-published/cuda.env
packages=()
for pkg in libfftw3-dev python3-venv; do
    if ! dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -qx 'install ok installed'; then packages+=("$pkg"); fi
done
if ((${#packages[@]})); then
    sudo apt-get update
    for pkg in "${packages[@]}"; do
        apt-cache policy "$pkg"
        candidate=$(apt-cache policy "$pkg" | awk '/Candidate:/ {print $2}')
        [[ -n "$candidate" && "$candidate" != '(none)' ]] || { echo "No apt candidate for $pkg" >&2; exit 1; }
        echo "Installing $pkg"
        sudo apt-get install -y "$pkg"
        dpkg-query -W "$pkg"
    done
fi
ls -l /usr/include/fftw3.h /usr/lib/x86_64-linux-gnu/libfftw3f.so
checkout() {
    local url=$1 dest=$2 pin=$3
    if [[ ! -d "$dest/.git" ]]; then git clone "$url" "$dest"; fi
    git -C "$dest" fetch origin "$pin"
    git -C "$dest" checkout --detach "$pin"
    [[ $(git -C "$dest" rev-parse HEAD) == "$pin" ]] || { echo "Pin mismatch: $dest" >&2; exit 1; }
}
checkout https://github.com/akiyamalab/MEGADOCK baseline-published/megadock 9575280c875732553266e26adc607dd892b02616
checkout https://github.com/pinder-org/pinder baseline-published/pinder ebeb28a2f8411363cef722b7d293c978f7442672
# Matching SDK headers; these are build dependencies, never substituted kernels.
if [[ ! -d baseline-published/cuda-samples/.git ]]; then
    git clone --depth 1 --branch v12.8 https://github.com/NVIDIA/cuda-samples baseline-published/cuda-samples
fi
git -C baseline-published/cuda-samples describe --tags --exact-match
samples=$(pwd)/baseline-published/cuda-samples
ls -l "$samples/Common/helper_cuda.h"
# Make variables configure the published Makefile without changing source.
# sm_90 targets the probed H100; retain published -O3 and -use_fast_math.
make -C baseline-published/megadock -j 8 USE_GPU=0 USE_MPI=0 \
    CPPCOMPILER=/usr/bin/g++ FFTW_INSTALL_PATH=/usr \
    FFTW_CFLAGS=-I/usr/include FFTW_LDFLAGS='-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f'
make -C baseline-published/megadock -j 8 USE_GPU=1 USE_MPI=0 \
    CPPCOMPILER=/usr/bin/g++ SM_VERSIONS=sm_90 \
    "NVCC=$CUDA_NVCC -Xcompiler -fopenmp -arch=sm_90 -use_fast_math" \
    "INCLUDES=-Isrc -I$CUDA_INCLUDE -I$samples/Common" \
    FFTW_CFLAGS=-I/usr/include \
    "LIB=-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f -L$CUDA_LIB -Wl,-rpath,$CUDA_LIB -lcudart -lcufft"
for binary in megadock megadock-gpu decoygen; do
    test -x "baseline-published/megadock/$binary"
    ldd "baseline-published/megadock/$binary"
done
# Help exits 255 in this published release. Require its actual usage output.
for binary in megadock megadock-gpu; do
    rc=0
    OMP_NUM_THREADS=26 CUDA_VISIBLE_DEVICES=0 "baseline-published/megadock/$binary" -h > "out/setup/$binary-help.log" 2>&1 || rc=$?
    [[ "$rc" == 0 || "$rc" == 255 ]]
    grep -q 'Usage: megadock' "out/setup/$binary-help.log"
done
python3 -m venv --system-site-packages baseline-published/venv
vpy=baseline-published/venv/bin/python
python3 - <<'PY' > out/setup/constraints.txt
import torch
print('torch=='+torch.__version__)
print('numpy==1.26.4\nbiotite==1.2.0\nnetworkx==3.4.2\npandas==2.3.3\nscikit-learn==1.7.2')
PY
"$vpy" -m pip install 'setuptools>=65.4' 'setuptools_scm>=8' packaging wheel 'build==0.10.0'
"$vpy" -m pip install --no-build-isolation -c out/setup/constraints.txt ./baseline-published/pinder fire networkx
"$vpy" -m pip freeze > out/setup/pip-freeze.txt
"$vpy" - <<'PY'
import torch
from pinder.eval.dockq import BiotiteDockQ
print('Stock torch preserved:', torch.__version__)
PY

cat > baseline-published/intake.json <<'JSON'
{
  "data": {
    "release": "2024-02",
    "required_inputs": [
      {
        "name": "index.parquet",
        "url": "https://pinderdata.org/2024-02/index.parquet",
        "provenance": "official_original_location",
        "recorded_bytes": 124511839,
        "recorded_sha256": "ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4",
        "http_status": 200,
        "content_length": "124511839",
        "check": "HEAD",
        "available": true
      },
      {
        "name": "mappings/1aua__A1_P24280-R.parquet",
        "url": "https://pinderdata.org/2024-02/mappings/1aua__A1_P24280-R.parquet",
        "provenance": "official_original_location",
        "recorded_bytes": 17094,
        "recorded_sha256": "895025d624f59e49294f1931ca0f43009249544784c28a4186db4eb7ebc6c3d0",
        "http_status": 200,
        "content_length": "17094",
        "check": "HEAD",
        "available": true
      },
      {
        "name": "mappings/1aua__A2_P24280-L.parquet",
        "url": "https://pinderdata.org/2024-02/mappings/1aua__A2_P24280-L.parquet",
        "provenance": "official_original_location",
        "recorded_bytes": 17094,
        "recorded_sha256": "f788f0a1bacf513f72282b48ba9bba229b1d4e346102f52fa04acdc01a5b3502",
        "http_status": 200,
        "content_length": "17094",
        "check": "HEAD",
        "available": true
      },
      {
        "name": "mappings/1ax2__A1_P16404-R.parquet",
        "url": "https://pinderdata.org/2024-02/mappings/1ax2__A1_P16404-R.parquet",
        "provenance": "official_original_location",
        "recorded_bytes": 15672,
        "recorded_sha256": "b025372cd5ab64d4eba0802e6113ac6392c312ed164fb1e95c81b1f418176ea2",
        "http_status": 200,
        "content_length": "15672",
        "check": "HEAD",
        "available": true
      },
      {
        "name": "mappings/1ax2__A2_P16404-L.parquet",
        "url": "https://pinderdata.org/2024-02/mappings/1ax2__A2_P16404-L.parquet",
        "provenance": "official_original_location",
        "recorded_bytes": 15672,
        "recorded_sha256": "b8071e73b37010f6bc1a76b8fcab79b5843162e93d2a2ae7b9db04bc16cab863",
        "http_status": 200,
        "content_length": "15672",
        "check": "HEAD",
        "available": true
      },
      {
        "name": "mappings/1dv1__A1_P24182-R.parquet",
        "url": "https://pinderdata.org/2024-02/mappings/1dv1__A1_P24182-R.parquet",
        "provenance": "official_original_location",
        "recorded_bytes": 20459,
        "recorded_sha256": "608fa0418db362b88012e5ba62f13ce1ccf989679e969162995702acfc22de94",
        "http_status": 200,
        "content_length": "20459",
        "check": "HEAD",
        "available": true
      },
      {
        "name": "mappings/1dv1__B1_P24182-L.parquet",
        "url": "https://pinderdata.org/2024-02/mappings/1dv1__B1_P24182-L.parquet",
        "provenance": "official_original_location",
        "recorded_bytes": 20423,
        "recorded_sha256": "3b12d7e1fb064baf19f4a730d1e68bdff8eed6a6eb136f5320b5efe26fab9d83",
        "http_status": 200,
        "content_length": "20423",
        "check": "HEAD",
        "available": true
      },
      {
        "name": "mappings/1nr5__A1_P07547-R.parquet",
        "url": "https://pinderdata.org/2024-02/mappings/1nr5__A1_P07547-R.parquet",
        "provenance": "official_original_location",
        "recorded_bytes": 19257,
        "recorded_sha256": "f94dbc1b085864611888d5fc5882d48206bd291ba57b262900a86c5af7fdd9d2",
        "http_status": 200,
        "content_length": "19257",
        "check": "HEAD",
        "available": true
      },
      {
        "name": "mappings/1nr5__A2_P07547-L.parquet",
        "url": "https://pinderdata.org/2024-02/mappings/1nr5__A2_P07547-L.parquet",
        "provenance": "official_original_location",
        "recorded_bytes": 19257,
        "recorded_sha256": "5a1298f932165350055e5cd02d8399406340acae56b204dcf362261cde5694e0",
        "http_status": 200,
        "content_length": "19257",
        "check": "HEAD",
        "available": true
      },
      {
        "name": "metadata.parquet",
        "url": "https://pinderdata.org/2024-02/metadata.parquet",
        "provenance": "official_original_location",
        "recorded_bytes": 103835983,
        "recorded_sha256": "3e3cfdc21d6c685891d6732edda13fea9d5566d056dfea56a2ae902ab80b4e6c",
        "http_status": 200,
        "content_length": "103835983",
        "check": "HEAD",
        "available": true
      },
      {
        "name": "pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb",
        "provenance": "official_original_location",
        "recorded_bytes": 388881,
        "recorded_sha256": "a12fd5f7506b927c1d435464cabbb9cd59299fdc4a826b63302052b0fef41a48",
        "http_status": 200,
        "content_length": "388881",
        "check": "GET+SHA256",
        "observed_sha256": "a12fd5f7506b927c1d435464cabbb9cd59299fdc4a826b63302052b0fef41a48",
        "hash_matches": true,
        "available": true
      },
      {
        "name": "pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb",
        "provenance": "official_original_location",
        "recorded_bytes": 300591,
        "recorded_sha256": "111ed0e1daea9ff8575bb61a2184b5f58fedd5437846e0f8026bebb53ef77a10",
        "http_status": 200,
        "content_length": "300591",
        "check": "GET+SHA256",
        "observed_sha256": "111ed0e1daea9ff8575bb61a2184b5f58fedd5437846e0f8026bebb53ef77a10",
        "hash_matches": true,
        "available": true
      },
      {
        "name": "pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb",
        "provenance": "official_original_location",
        "recorded_bytes": 536625,
        "recorded_sha256": "a159da5b6b145570b4d03ac9e17eb7b4315f7a8afd0497a93ad1f77a55debf3e",
        "http_status": 200,
        "content_length": "536625",
        "check": "GET+SHA256",
        "observed_sha256": "a159da5b6b145570b4d03ac9e17eb7b4315f7a8afd0497a93ad1f77a55debf3e",
        "hash_matches": true,
        "available": true
      },
      {
        "name": "pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb",
        "provenance": "official_original_location",
        "recorded_bytes": 484785,
        "recorded_sha256": "ee2fc49ec38f26a216154fd7ce0a93086f2ba60dde6997d86deb196bac96f861",
        "http_status": 200,
        "content_length": "484785",
        "check": "GET+SHA256",
        "observed_sha256": "ee2fc49ec38f26a216154fd7ce0a93086f2ba60dde6997d86deb196bac96f861",
        "hash_matches": true,
        "available": true
      },
      {
        "name": "pdbs/1sg6__A1_P07547.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb",
        "provenance": "official_original_location",
        "recorded_bytes": 234171,
        "recorded_sha256": "4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5",
        "http_status": 200,
        "content_length": "234171",
        "check": "GET+SHA256",
        "observed_sha256": "4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5",
        "hash_matches": true,
        "available": true
      },
      {
        "name": "pdbs/3g8c__A1_P24182.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/3g8c__A1_P24182.pdb",
        "provenance": "official_original_location",
        "recorded_bytes": 277182,
        "recorded_sha256": "48aa5f4b2ac1e57d855b85d56a9c4a74c4b16f7d165b0fce03535815e26bdb60",
        "http_status": 200,
        "content_length": "277182",
        "check": "GET+SHA256",
        "observed_sha256": "48aa5f4b2ac1e57d855b85d56a9c4a74c4b16f7d165b0fce03535815e26bdb60",
        "hash_matches": true,
        "available": true
      },
      {
        "name": "pdbs/3g8d__A1_P24182.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/3g8d__A1_P24182.pdb",
        "provenance": "official_original_location",
        "recorded_bytes": 234657,
        "recorded_sha256": "1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c",
        "http_status": 200,
        "content_length": "234657",
        "check": "GET+SHA256",
        "observed_sha256": "1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c",
        "hash_matches": true,
        "available": true
      },
      {
        "name": "pdbs/3n35__A1_P16404.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb",
        "provenance": "official_original_location",
        "recorded_bytes": 151794,
        "recorded_sha256": "b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e",
        "http_status": 200,
        "content_length": "151794",
        "check": "GET+SHA256",
        "observed_sha256": "b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e",
        "hash_matches": true,
        "available": true
      },
      {
        "name": "pdbs/6f0e__A1_P24280.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb",
        "provenance": "official_original_location",
        "recorded_bytes": 192456,
        "recorded_sha256": "622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd",
        "http_status": 200,
        "content_length": "192456",
        "check": "GET+SHA256",
        "observed_sha256": "622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd",
        "hash_matches": true,
        "available": true
      }
    ],
    "cases": [
      {
        "id": "1aua__A1_P24280--1aua__A2_P24280:apo",
        "system_id": "1aua__A1_P24280--1aua__A2_P24280",
        "kind": "apo",
        "unit_manifest_index_zero_based": 3,
        "prepared_record": {
          "id": "1aua__A1_P24280--1aua__A2_P24280",
          "kind": "apo",
          "receptor": "1aua__A1_P24280--1aua__A2_P24280/inputs/apo/1aua_apo_R.pdb",
          "ligand": "1aua__A1_P24280--1aua__A2_P24280/inputs/apo/1aua_apo_L.pdb"
        },
        "prepared_csv_block_sha256": "a97af77279a2cac61eee504904b82603710ae1194885ff132569cae5826d3e18",
        "prepared_pdb_sha256": null,
        "prepared_pdb_hash_reason": "Brief supplies logical paths and source hashes, not hashes of serialized prepared PDBs.",
        "apo_receptor_source": "pdbs/6f0e__A1_P24280.pdb",
        "apo_ligand_source": "pdbs/6f0e__A1_P24280.pdb",
        "reference": "pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb",
        "source": "brief.md, Cases and prepared input records"
      },
      {
        "id": "1ax2__A1_P16404--1ax2__A2_P16404:apo",
        "system_id": "1ax2__A1_P16404--1ax2__A2_P16404",
        "kind": "apo",
        "unit_manifest_index_zero_based": 5,
        "prepared_record": {
          "id": "1ax2__A1_P16404--1ax2__A2_P16404",
          "kind": "apo",
          "receptor": "1ax2__A1_P16404--1ax2__A2_P16404/inputs/apo/1ax2_apo_R.pdb",
          "ligand": "1ax2__A1_P16404--1ax2__A2_P16404/inputs/apo/1ax2_apo_L.pdb"
        },
        "prepared_csv_block_sha256": "2357dfd034f88367b5e4b51d92effc039c8f413ed15030eacec858e7fa5006d8",
        "prepared_pdb_sha256": null,
        "prepared_pdb_hash_reason": "Brief supplies logical paths and source hashes, not hashes of serialized prepared PDBs.",
        "apo_receptor_source": "pdbs/3n35__A1_P16404.pdb",
        "apo_ligand_source": "pdbs/3n35__A1_P16404.pdb",
        "reference": "pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb",
        "source": "brief.md, Cases and prepared input records"
      },
      {
        "id": "1dv1__A1_P24182--1dv1__B1_P24182:apo",
        "system_id": "1dv1__A1_P24182--1dv1__B1_P24182",
        "kind": "apo",
        "unit_manifest_index_zero_based": 9,
        "prepared_record": {
          "id": "1dv1__A1_P24182--1dv1__B1_P24182",
          "kind": "apo",
          "receptor": "1dv1__A1_P24182--1dv1__B1_P24182/inputs/apo/1dv1_apo_R.pdb",
          "ligand": "1dv1__A1_P24182--1dv1__B1_P24182/inputs/apo/1dv1_apo_L.pdb"
        },
        "prepared_csv_block_sha256": "90912611cb8363253de9a33055834c1edab8898865a69d413aae39efb11e0eb9",
        "prepared_pdb_sha256": null,
        "prepared_pdb_hash_reason": "Brief supplies logical paths and source hashes, not hashes of serialized prepared PDBs.",
        "apo_receptor_source": "pdbs/3g8c__A1_P24182.pdb",
        "apo_ligand_source": "pdbs/3g8d__A1_P24182.pdb",
        "reference": "pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb",
        "source": "brief.md, Cases and prepared input records"
      },
      {
        "id": "1nr5__A1_P07547--1nr5__A2_P07547:apo",
        "system_id": "1nr5__A1_P07547--1nr5__A2_P07547",
        "kind": "apo",
        "unit_manifest_index_zero_based": 15,
        "prepared_record": {
          "id": "1nr5__A1_P07547--1nr5__A2_P07547",
          "kind": "apo",
          "receptor": "1nr5__A1_P07547--1nr5__A2_P07547/inputs/apo/1nr5_apo_R.pdb",
          "ligand": "1nr5__A1_P07547--1nr5__A2_P07547/inputs/apo/1nr5_apo_L.pdb"
        },
        "prepared_csv_block_sha256": "cba9eaa447e9a2a228eaa9c322892f1b8cccb7687e1c24ec089edd4d11804aa9",
        "prepared_pdb_sha256": null,
        "prepared_pdb_hash_reason": "Brief supplies logical paths and source hashes, not hashes of serialized prepared PDBs.",
        "apo_receptor_source": "pdbs/1sg6__A1_P07547.pdb",
        "apo_ligand_source": "pdbs/1sg6__A1_P07547.pdb",
        "reference": "pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb",
        "source": "brief.md, Cases and prepared input records"
      }
    ],
    "availability": "available",
    "availability_evidence": "Nine unique required PDB payloads anonymously fetched and SHA-256 matched brief; index, metadata and eight mapping URLs returned HTTP 200 to HEAD. HEAD checks do not verify payload hashes. See input_checks.txt.",
    "access_instructions": "Anonymous HTTPS at listed exact URLs. Fetch only selected inputs; full PINDER download is unnecessary. Verify recorded SHA-256 before execution. Filter index to four exact system IDs; prepare complete canonical apo monomers with receptor chain R and ligand chain L, serializing to recorded logical paths. Native complex used only by evaluator.",
    "licences": [
      {
        "item": "PINDER evaluation code",
        "licence": "Apache-2.0",
        "basis": "explicit",
        "source": [
          "https://github.com/pinder-org/pinder/blob/ebeb28a2f8411363cef722b7d293c978f7442672/LICENSE",
          "https://github.com/pinder-org/pinder/blob/ebeb28a2f8411363cef722b7d293c978f7442672/README.md"
        ],
        "permission": "permitted"
      },
      {
        "item": "PINDER 2024-02 structural inputs, references, index and mappings",
        "licence": null,
        "basis": "none",
        "permission": "unknown",
        "source": [
          "https://github.com/pinder-org/pinder/blob/ebeb28a2f8411363cef722b7d293c978f7442672/README.md",
          "https://pinderdata.org/2024-02/",
          "brief.md"
        ],
        "reason": "No dataset-specific licence or terms covering remotely hosted required inputs established. Repository Apache licence does not establish coverage of external dataset. FroDock mirror owner permission does not cover MEGADOCK or establish PINDER rights."
      }
    ],
    "prepared_inputs": {
      "status": "generated inputs, not missing source data",
      "procedure": "For each exact CSV record, read complete canonical apo files listed in case, label receptor R and ligand L, serialize to record paths; introduce no new atom/residue selection.",
      "source": "brief.md",
      "serialized_pdb_hashes": null,
      "reason": "Must compute and seal generated prepared PDB hashes before execution; brief does not provide those hashes.",
      "selection_csv_bytes": 644,
      "selection_csv_sha256": "f34c87e11bc77f02997f41aaae17cf6958ce02976b9621886d96c03029b27af0"
    },
    "splits": {
      "selection": "Four apo pairings from PINDER-S, exact systems fixed by brief",
      "unit_manifest_indices": [
        3,
        5,
        9,
        15
      ],
      "source": "brief.md",
      "full_training_dataset_required": false
    },
    "seeds": null,
    "seeds_reason": "Fixed identity selection; no sampling seed or stochastic docking seed supplied.",
    "evaluation_code": {
      "repo": "https://github.com/pinder-org/pinder",
      "commit": "ebeb28a2f8411363cef722b7d293c978f7442672",
      "implementation": "pinder_eval / pinder.eval.dockq",
      "source": [
        "https://github.com/pinder-org/pinder/blob/ebeb28a2f8411363cef722b7d293c978f7442672/README.md",
        "brief.md"
      ]
    },
    "not_required": {
      "FroDock_mirror": "Historical provenance only; not this benchmark baseline. No FroDock workload substituted.",
      "auxiliary_predicted_or_alternative_apo_files": "Historical downloader inventory; not additional selected cases.",
      "test_set_pdbs.zip": "Contains separated holo monomers, not required canonical apo files or native complexes."
    }
  },
  "EXECUTION": {
    "representative_scale": {
      "cases": [
        "1aua__A1_P24280--1aua__A2_P24280:apo",
        "1ax2__A1_P16404--1ax2__A2_P16404:apo",
        "1dv1__A1_P24182--1dv1__B1_P24182:apo",
        "1nr5__A1_P07547--1nr5__A2_P07547:apo"
      ],
      "configurations": [
        "CPU standard 3600 rotations",
        "GPU standard 3600 rotations",
        "GPU dense 54000 rotations"
      ],
      "predictions_per_case_per_configuration": 50,
      "docking_jobs_per_complete_comparison": 12,
      "decoys_per_complete_comparison": 600,
      "timing_repetitions": null,
      "reason": "Fixed actual four-case workload; no toy extrapolation or scale doubling. Repetition count requires brief-requested calibration before sealing."
    },
    "inputs": {
      "data_manifest": "data.json",
      "prepared_inputs": [
        {
          "id": "1aua__A1_P24280--1aua__A2_P24280",
          "kind": "apo",
          "receptor": "1aua__A1_P24280--1aua__A2_P24280/inputs/apo/1aua_apo_R.pdb",
          "ligand": "1aua__A1_P24280--1aua__A2_P24280/inputs/apo/1aua_apo_L.pdb"
        },
        {
          "id": "1ax2__A1_P16404--1ax2__A2_P16404",
          "kind": "apo",
          "receptor": "1ax2__A1_P16404--1ax2__A2_P16404/inputs/apo/1ax2_apo_R.pdb",
          "ligand": "1ax2__A1_P16404--1ax2__A2_P16404/inputs/apo/1ax2_apo_L.pdb"
        },
        {
          "id": "1dv1__A1_P24182--1dv1__B1_P24182",
          "kind": "apo",
          "receptor": "1dv1__A1_P24182--1dv1__B1_P24182/inputs/apo/1dv1_apo_R.pdb",
          "ligand": "1dv1__A1_P24182--1dv1__B1_P24182/inputs/apo/1dv1_apo_L.pdb"
        },
        {
          "id": "1nr5__A1_P07547--1nr5__A2_P07547",
          "kind": "apo",
          "receptor": "1nr5__A1_P07547--1nr5__A2_P07547/inputs/apo/1nr5_apo_R.pdb",
          "ligand": "1nr5__A1_P07547--1nr5__A2_P07547/inputs/apo/1nr5_apo_L.pdb"
        }
      ],
      "native_references": [
        "pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb",
        "pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb",
        "pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb",
        "pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb"
      ],
      "evaluation_only_references": true,
      "configuration": "baseline.json, published_configuration",
      "prepared_input_hashes": null,
      "reason": "Source hashes established; generated prepared PDB hashes must be sealed before execution."
    },
    "outputs": {
      "docking": "Separate MEGADOCK ranked score/transform file for each case and configuration.",
      "pose_files": "eval_dir/<configuration>/<system_id>/apo_decoys/model_<rank>.pdb, ranks 1..50, exactly receptor R and ligand L.",
      "scoring_interface": {
        "published_command_help": "pinder_eval --help",
        "published_arguments": "--eval_dir eval_dir [--serial] [--method_name method_name] [--allow_missing] [--custom_index CUSTOM_INDEX] [--max_workers MAX_WORKERS]",
        "source": "https://github.com/pinder-org/pinder/blob/ebeb28a2f8411363cef722b7d293c978f7442672/README.md",
        "selection": "Evaluate only exact four systems; custom index, if needed, must preserve required PINDER schema and explicit holdout definitions. Do not aggregate missing remainder of PINDER-S as failures of this pilot.",
        "adapter_command": null,
        "reason": "Published evaluator exists; no four-case adapter command or patched historical wrapper provided.",
        "metrics": "Per-pose DockQ; rank-1 and best-of-50 per case/configuration; paired dense-standard differences reported separately."
      },
      "other": [
        "CPU/GPU numerical agreement report with predeclared tolerance",
        "workflow stage times and complete end-to-end time",
        "GPU activity trace",
        "billed allocation seconds, rate and cost",
        "budget overruns and failures"
      ],
      "aggregate_published_target": null,
      "reason": "No published aggregate value for these four pairs; no scalar substituted for requested comparison."
    },
    "timing_scope": {
      "complete_workflow": "Include acquisition/preparation, baseline setup, docking, decoy generation, evaluation and reporting; report setup separately as well as total.",
      "steady_state_comparison": "CPU/GPU standard docking and pose-generation times at identical inputs/scientific settings; synchronization/process completion required.",
      "GPU_activity": "Observe GPU activity during workflow; GPU-capable binary alone does not establish GPU execution.",
      "billed_cost": "Use actual allocated time and applicable billing rate, including idle/setup allocations.",
      "calibration": "Small runtime calibration on fixed selected workload, without consulting native quality; then seal repetition count, comparison rules, total cap before evaluation.",
      "source": "brief.md",
      "calibrated_runtime_s": null,
      "repetitions": null,
      "cost_rate": null,
      "total_spending_cap": null,
      "unavailable_reason": "No builds, calibration or workloads authorized during intake; brief supplies no timings or billing price."
    },
    "budgets": {
      "supplied_args_budgets": {},
      "run_ceiling_s": 43200,
      "default_script_seconds": {
        "method_setup": 1200,
        "method_run": 1200,
        "tests": 900,
        "evaluate": 2400
      },
      "stage_budgets_s": null,
      "reason": "No empirical stage-duration estimates; no overrides invented. Setup/anchors/profile use remaining run-ceiling time when args budgets absent. Defaults are ceilings, not evidence workload finishes within them.",
      "source": "Intake prompt"
    },
    "limitations": [
      "Supplied scalar intake gate does not express three paired configuration comparisons, two separate quality outcomes, pre-result numerical agreement rules, calibrated spending cap, GPU activity and billed allocation cost. Execution adapter must preserve these outputs separately.",
      "No calibration, sealed repetition count, numerical tolerance, pricing or spending cap available during this bounded intake. No scripts executed or run-duration guarantee inferred."
    ],
    "executed": false
  },
  "anchors": [],
  "baseline": {
    "repo": "https://github.com/akiyamalab/MEGADOCK",
    "commit": "9575280c875732553266e26adc607dd892b02616",
    "pin": "4.1.4; annotated tag object 1ced00d37672c03d3014da4307b920fdeff4d0ca",
    "pin_source": "https://api.github.com/repos/akiyamalab/MEGADOCK/git/tags/1ced00d37672c03d3014da4307b920fdeff4d0ca",
    "build_commands": [
      {
        "command": "make",
        "configuration": "CPU source copy: USE_GPU := 0, USE_MPI := 0; configure FFTW path, g++ and OpenMP as published.",
        "source": "https://github.com/akiyamalab/MEGADOCK/blob/9575280c875732553266e26adc607dd892b02616/doc/BUILD.md#d-compile-for-cpu-node-only-thread-parallelization"
      },
      {
        "command": "make",
        "configuration": "GPU source copy: USE_GPU := 1, USE_MPI := 0; configure CUDA, CUDA samples, FFTW paths and target SM architecture as published.",
        "source": "https://github.com/akiyamalab/MEGADOCK/blob/9575280c875732553266e26adc607dd892b02616/doc/BUILD.md#c-compile-for-gpu-node-gpu"
      },
      {
        "command": "pip install pinder[eval]",
        "configuration": "Published optional evaluator installation example. Unpinned package-manager example is not a sealed installation of the recorded PINDER commit; dependency/source pinning remains a reproduction requirement.",
        "source": "https://github.com/pinder-org/pinder/blob/ebeb28a2f8411363cef722b7d293c978f7442672/README.md"
      }
    ],
    "build_prerequisites": {
      "published": "Single-precision FFTW3 (--enable-float if building FFTW), g++/OpenMP, CUDA toolkit and matching sample headers. make also builds decoygen.",
      "dependency_install_commands": null,
      "reason": "No stock-image dependency lock or complete package-install command established; do not invent apt/pip commands for baseline.",
      "source": "https://github.com/akiyamalab/MEGADOCK/blob/9575280c875732553266e26adc607dd892b02616/doc/BUILD.md"
    },
    "run_commands": [
      {
        "command": "./megadock -R receptor.pdb -L ligand.pdb -o receptor-ligand.out",
        "configuration": "CPU standard; published command template. Bind receptor/ligand to each exact prepared pair; add documented -N 50; use documented default 3600 rotations.",
        "source": [
          "https://github.com/akiyamalab/MEGADOCK/blob/9575280c875732553266e26adc607dd892b02616/doc/README.md",
          "brief.md"
        ]
      },
      {
        "command": "./megadock-gpu -R receptor.pdb -L ligand.pdb -o receptor-ligand.out",
        "configuration": "GPU standard; same pair and scoring; add documented -N 50; default 3600 rotations.",
        "source": [
          "https://github.com/akiyamalab/MEGADOCK/blob/9575280c875732553266e26adc607dd892b02616/doc/README.md",
          "brief.md"
        ]
      },
      {
        "command": "./megadock-gpu -R receptor.pdb -L ligand.pdb -o receptor-ligand.out",
        "configuration": "GPU dense; same pair and scoring; add documented -N 50 and -D (54000 rotations). Output must be distinct by case/configuration.",
        "source": [
          "https://github.com/akiyamalab/MEGADOCK/blob/9575280c875732553266e26adc607dd892b02616/doc/README.md",
          "brief.md"
        ]
      },
      {
        "command": "./decoygen [decoy_filename] [used_ligand.pdb] [.outfile] [decoy no.]",
        "configuration": "Published positional interface; generate ranks 1 through 50, concatenate unchanged prepared receptor with transformed ligand into R/L complex.",
        "source": "https://github.com/akiyamalab/MEGADOCK/blob/9575280c875732553266e26adc607dd892b02616/doc/README.md#generate-decoy-from-docking-output"
      }
    ],
    "published_configuration": {
      "scientific_settings": {
        "rotations_standard": 3600,
        "rotations_dense": 54000,
        "retained_predictions": 50,
        "predictions_per_rotation": 1,
        "voxel_pitch_angstrom": 1.2,
        "electrostatics_ratio": 1.0,
        "hydrophobic_ratio": 1.0,
        "receptor_core_penalty": -45.0,
        "ligand_core_penalty": 1.0,
        "score_function": 3,
        "fft_points": null,
        "fft_points_reason": "Published default selects from input dimensions; record actual selected grid, keep identical between CPU/GPU for each case.",
        "source": [
          "https://github.com/akiyamalab/MEGADOCK/blob/9575280c875732553266e26adc607dd892b02616/doc/README.md",
          "brief.md"
        ]
      },
      "CPU": "OpenMP single node, megadock; no MPI",
      "GPU": "CUDA+OpenMP single node, megadock-gpu; no MPI",
      "thread_count": null,
      "thread_count_reason": "Calibrate and seal before comparison; historical eight MPI ranks not applicable.",
      "build_defaults": "-O3, -fopenmp; GPU -use_fast_math and sm_60; record changes for actual stock CUDA image.",
      "source": [
        "https://github.com/akiyamalab/MEGADOCK/blob/9575280c875732553266e26adc607dd892b02616/doc/BUILD.md",
        "https://github.com/akiyamalab/MEGADOCK/blob/9575280c875732553266e26adc607dd892b02616/doc/README.md",
        "https://github.com/akiyamalab/MEGADOCK/blob/9575280c875732553266e26adc607dd892b02616/Makefile"
      ],
      "status": "Published settings mapped to requested pilot; repetitions, tolerance and cost cap remain unsealed pending calibration."
    },
    "evaluation_install": {
      "repo": "https://github.com/pinder-org/pinder",
      "commit": "ebeb28a2f8411363cef722b7d293c978f7442672",
      "published_install_command": "pip install pinder[eval]",
      "source": "https://github.com/pinder-org/pinder/blob/ebeb28a2f8411363cef722b7d293c978f7442672/README.md",
      "reason": "Published package installation example; does not pin downloaded release. For repeatable execution use supplied immutable source pin and seal dependency resolution; no installation run. Historical brief contains source installation excerpts and patch hash but not patch contents; no historical patch assumed."
    },
    "executed": false
  }
}
JSON
"$vpy" - <<'PYDATA'
import hashlib, json, pathlib, urllib.request, time
import pandas as pd
manifest=json.loads(pathlib.Path('baseline-published/intake.json').read_text())
root=pathlib.Path('data/2024-02'); root.mkdir(parents=True,exist_ok=True)
for item in manifest['data']['required_inputs']:
    dst=root/item['name']; dst.parent.mkdir(parents=True,exist_ok=True)
    expected=item['recorded_sha256']
    def valid():
        return dst.is_file() and hashlib.sha256(dst.read_bytes()).hexdigest()==expected
    if not valid():
        for attempt in range(3):
            try:
                tmp=dst.with_suffix(dst.suffix+'.download')
                with urllib.request.urlopen(item['url'],timeout=120) as src, tmp.open('wb') as out:
                    while chunk:=src.read(1024*1024): out.write(chunk)
                if hashlib.sha256(tmp.read_bytes()).hexdigest()!=expected:
                    raise RuntimeError('SHA256 mismatch: '+item['name'])
                tmp.replace(dst); break
            except Exception:
                if attempt==2: raise
                time.sleep(2)
    if not valid(): raise RuntimeError('Invalid download: '+str(dst))
index=pd.read_parquet(root/'index.parquet')
cases=manifest['data']['cases']; selected=index[index.id.isin([c['system_id'] for c in cases])]
if len(selected)!=4: raise RuntimeError('Missing or duplicate selected index rows')
selected.to_parquet(pathlib.Path('data/custom_index.parquet'),index=False)
prepared={}
for case in cases:
    row=selected.loc[selected.id==case['system_id']].iloc[0]
    for role,chain in [('receptor','R'),('ligand','L')]:
        src=case['apo_'+role+'_source']
        if row['apo_'+chain+'_pdb']!=pathlib.Path(src).name:
            raise RuntimeError('Canonical apo identity differs from intake')
        dest=pathlib.Path('data')/case['prepared_record'][role]
        dest.parent.mkdir(parents=True,exist_ok=True)
        # Preserve every atom/residue and coordinate. Change chain field only.
        lines=[]
        for line in (root/src).read_text().splitlines(keepends=True):
            if line.startswith(('ATOM  ','HETATM','ANISOU','TER   ')):
                line=line[:21]+chain+line[22:]
            lines.append(line)
        dest.write_text(''.join(lines))
        prepared[str(dest)]=hashlib.sha256(dest.read_bytes()).hexdigest()
        # Short aliases keep published decoygen's filename buffers within bounds.
        short=pathlib.Path('data/inputs')/(case['system_id'][:4]+'_'+chain+'.pdb')
        short.parent.mkdir(exist_ok=True)
        short.write_bytes(dest.read_bytes())
pathlib.Path('data/prepared_sha256.json').write_text(json.dumps(prepared,indent=2)+'\n')
print(json.dumps(prepared,indent=2))
PYDATA
printf '%s\n' 'Baseline build and input checks complete; no benchmark run during setup.'
