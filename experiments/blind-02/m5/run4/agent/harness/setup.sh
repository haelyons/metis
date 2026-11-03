#!/usr/bin/env bash
set -euo pipefail
mkdir -p out/setup baseline-published data
exec > >(tee -a out/setup/setup.log) 2>&1
export PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_CACHE_DIR=out/setup/pip-cache
# Select only layouts discovered by the supplied box probe.
if [[ -x /usr/local/cuda/bin/nvcc && -f /usr/local/cuda/include/cuda_runtime.h && -f /usr/local/cuda/lib64/libcudart.so ]]; then
    export CUDACXX=/usr/local/cuda/bin/nvcc CUDA_INCLUDE_DIR=/usr/local/cuda/include CUDA_LIBRARY_DIR=/usr/local/cuda/lib64 CUDAToolkit_ROOT=/usr/local/cuda
    export PATH=/usr/local/cuda/bin:$PATH
elif [[ -x /usr/lib/cuda/bin/nvcc && -f /usr/lib/cuda/include/cuda_runtime.h && -f /usr/lib/cuda/lib64/libcudart.so ]]; then
    export CUDACXX=/usr/lib/cuda/bin/nvcc CUDA_INCLUDE_DIR=/usr/lib/cuda/include CUDA_LIBRARY_DIR=/usr/lib/cuda/lib64 CUDAToolkit_ROOT=/usr/lib/cuda
    export PATH=/usr/lib/cuda/bin:$PATH
elif [[ -x /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    export CUDACXX=/usr/bin/nvcc CUDA_INCLUDE_DIR=/usr/include CUDA_LIBRARY_DIR=/usr/lib/x86_64-linux-gnu
else
    echo 'No complete CUDA layout from supplied probe' >&2; exit 1
fi
ls -l "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
missing=()
for package in libfftw3-dev python3-venv; do
    if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then missing+=("$package"); fi
done
if (( ${#missing[@]} )); then
    sudo apt-get update
    for package in "${missing[@]}"; do
        apt-cache policy "$package"
        candidate=$(apt-cache policy "$package" | awk '/Candidate:/ {print $2}')
        [[ -n "$candidate" && "$candidate" != '(none)' ]] || { echo "No install candidate: $package" >&2; exit 1; }
        echo "Installing $package"
        sudo apt-get install -y "$package"
        dpkg-query -W "$package"
    done
fi
clone_pin() {
    local repo=$1 dest=$2 pin=$3
    if [[ ! -d "$dest/.git" ]]; then git clone "$repo" "$dest"; fi
    git -C "$dest" checkout --detach "$pin"
    [[ $(git -C "$dest" rev-parse HEAD) == "$pin" ]]
    [[ -z $(git -C "$dest" status --porcelain --untracked-files=no) ]] || { echo "Modified published source: $dest"; exit 1; }
}
clone_pin https://github.com/akiyamalab/MEGADOCK baseline-published/megadock 9575280c875732553266e26adc607dd892b02616
clone_pin https://github.com/pinder-org/pinder baseline-published/pinder ebeb28a2f8411363cef722b7d293c978f7442672
make -C baseline-published/megadock -j 8 USE_GPU=0 USE_MPI=0 CPPCOMPILER=/usr/bin/g++ FFTW_INSTALL_PATH=/usr FFTW_CFLAGS=-I/usr/include FFTW_LDFLAGS='-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f'
python3 -m venv --system-site-packages baseline-published/venv
vpy=baseline-published/venv/bin/python
python3 - <<'PYCONSTRAINT'
import torch,pathlib,json,hashlib
p=pathlib.Path(torch.__file__)
pathlib.Path('out/setup/stock-torch.json').write_text(json.dumps({'version':torch.__version__,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
pathlib.Path('out/setup/constraints.txt').write_text('torch=='+torch.__version__+'\nnumpy==1.26.4\nbiotite==1.2.0\nnetworkx==3.4.2\npandas==2.3.3\nscikit-learn==1.7.2\n')
PYCONSTRAINT
"$vpy" -m pip install 'setuptools>=65.4' 'setuptools_scm>=8' packaging wheel 'build==0.10.0'
"$vpy" -m pip install --no-build-isolation -c out/setup/constraints.txt ./baseline-published/pinder fire networkx
"$vpy" -m pip freeze > out/setup/pip-freeze.txt
cat > data/manifest.json <<'MANIFEST'
{
  "baseline": {
    "repo": "https://github.com/akiyamalab/MEGADOCK",
    "commit": "9575280c875732553266e26adc607dd892b02616",
    "build_commands": [
      "make -C baseline-published/megadock -j 8 USE_GPU=0 USE_MPI=0 \\\n    CPPCOMPILER=/usr/bin/g++ FFTW_INSTALL_PATH=/usr \\\n    FFTW_CFLAGS=-I/usr/include FFTW_LDFLAGS='-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f'\npython3 -m venv --system-site-packages baseline-published/venv\nvpy=baseline-published/venv/bin/python\npython3 - <<'PY' > out/setup/constraints.txt\nimport torch\nprint('torch=='+torch.__version__)\nprint('numpy==1.26.4\\nbiotite==1.2.0\\nnetworkx==3.4.2\\npandas==2.3.3\\nscikit-learn==1.7.2')\nPY\n\"$vpy\" -m pip install 'setuptools>=65.4' 'setuptools_scm>=8' packaging wheel 'build==0.10.0'\n\"$vpy\" -m pip install --no-build-isolation -c out/setup/constraints.txt ./baseline-published/pinder fire networkx\n\"$vpy\" -m pip freeze > out/setup/pip-freeze.txt\n\"$vpy\" - <<'PY'\nimport torch\nfrom pinder.eval.dockq import BiotiteDockQ\nprint('Stock torch preserved:', torch.__version__)\nPY"
    ],
    "build_commands_source": {
      "path": "brief.md",
      "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
      "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
    },
    "run_commands": [
      "baseline-published/megadock/megadock -R data/inputs/<prefix>_R.pdb -L data/inputs/<prefix>_L.pdb -o out/<case>/docking.out -N 50 -t 1 -v 1.2 -e 1.0 -d 1.0 -a -45.0 -b 1.0 -f 3 -r 3600",
      "./decoygen [decoy_filename] [used_ligand.pdb] [.outfile] [decoy no.]"
    ],
    "run_commands_sources": [
      {
        "path": "brief.md",
        "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
        "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
      },
      "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/doc/README.md"
    ],
    "published_configuration": {
      "implementation": "Published CPU-node OpenMP build, USE_GPU=0 USE_MPI=0; no CUDA or MPI docking.",
      "rotation_angles": 3600,
      "voxel_angstrom": 1.2,
      "predictions": 50,
      "predictions_per_rotation": 1,
      "electrostatics_ratio": 1.0,
      "hydrophobic_ratio": 1.0,
      "receptor_core_penalty": -45.0,
      "ligand_core_penalty": 1.0,
      "function": 3,
      "source": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/doc/README.md",
      "selection_source": {
        "path": "brief.md",
        "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
        "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
      }
    },
    "evaluator": {
      "repo": "https://github.com/pinder-org/pinder",
      "commit": "ebeb28a2f8411363cef722b7d293c978f7442672",
      "interface": "pinder.eval.dockq.BiotiteDockQ(...).calculate()",
      "dependencies": {
        "torch": "2.7.0",
        "numpy": "1.26.4",
        "biotite": "1.2.0",
        "networkx": "3.4.2",
        "pandas": "2.3.3",
        "scikit-learn": "1.7.2"
      },
      "source": {
        "path": "brief.md",
        "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
        "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
      },
      "dependency_lock": "Historical freeze supplied in brief is evidence, not universally installable lock; setup records actual versions and byte hashes, reports changes and does not pool incompatible timings."
    },
    "build_status": "not run; actual stock paths and dependencies must be discovered during setup",
    "version_uncertainty": "Historical executable printed 4.1.3 versus source tag 4.1.4; preserve exact source and measured binary identities.",
    "licences": [
      {
        "item": "MEGADOCK code",
        "licence": "CC-BY-NC-4.0",
        "basis": "explicit",
        "source": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/README.md",
        "intended_use": "Local scientific runtime calibration; noncommercial use permitted subject to attribution. Commercial authorization not established; brief does not establish commercial status."
      },
      {
        "item": "PINDER evaluator code",
        "licence": "Apache-2.0",
        "basis": "explicit",
        "source": "https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/LICENSE",
        "intended_use": "Execution and modification permitted under Apache-2.0 conditions."
      },
      {
        "item": "PINDER release 2024-02 index and selected PDB inputs/native references",
        "licence": null,
        "basis": "none",
        "source": [
          "https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/README.md",
          "https://pinderdata.org/2024-02/"
        ],
        "reason": "Retrieved repository README and LICENSE establish code licence but do not explicitly establish coverage of externally hosted index and structures. No applicable input terms found in bounded inspection. Owner mirror authorization is not a licence grant from input rights holders."
      }
    ],
    "sources": [
      {
        "path": "brief.md",
        "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
        "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
      },
      "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/doc/BUILD.md",
      "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/doc/README.md"
    ]
  },
  "data": {
    "release": "2024-02",
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
        "apo_receptor_source": "pdbs/6f0e__A1_P24280.pdb",
        "apo_ligand_source": "pdbs/6f0e__A1_P24280.pdb",
        "reference": "pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb",
        "historical_prepared_sha256": {
          "receptor": "162aad227fdbdb6a0600a5b6a4f5b461663ee7ce419798061ea0cd8ae9be6f35",
          "ligand": "f5158ee7030ce712cc5fb419d1e7532d4db2d4b4ddb64b50a5d0d9e45a973600"
        },
        "intake_generated_hash_check": {
          "receptor": {
            "sha256": "162aad227fdbdb6a0600a5b6a4f5b461663ee7ce419798061ea0cd8ae9be6f35",
            "matches": true
          },
          "ligand": {
            "sha256": "f5158ee7030ce712cc5fb419d1e7532d4db2d4b4ddb64b50a5d0d9e45a973600",
            "matches": true
          }
        }
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
        "apo_receptor_source": "pdbs/3n35__A1_P16404.pdb",
        "apo_ligand_source": "pdbs/3n35__A1_P16404.pdb",
        "reference": "pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb",
        "historical_prepared_sha256": {
          "receptor": "a9be54841e5e92e301558c198a7188b6765ab34cf30cb5d939b46f99db103d35",
          "ligand": "8d3948ddc69f493dfeea785aefc09f3de7b191ab7f8250dc102f63dc1d35810e"
        },
        "intake_generated_hash_check": {
          "receptor": {
            "sha256": "a9be54841e5e92e301558c198a7188b6765ab34cf30cb5d939b46f99db103d35",
            "matches": true
          },
          "ligand": {
            "sha256": "8d3948ddc69f493dfeea785aefc09f3de7b191ab7f8250dc102f63dc1d35810e",
            "matches": true
          }
        }
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
        "apo_receptor_source": "pdbs/3g8c__A1_P24182.pdb",
        "apo_ligand_source": "pdbs/3g8d__A1_P24182.pdb",
        "reference": "pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb",
        "historical_prepared_sha256": {
          "receptor": "880a12d8a36e84fc8bea31cb4105284827ce1a985128413e4e8f70582fe52ea2",
          "ligand": "f9c72e23a1f2afe893c672da0412e82fa8345be23902d1d5cc7c17971193f623"
        },
        "intake_generated_hash_check": {
          "receptor": {
            "sha256": "880a12d8a36e84fc8bea31cb4105284827ce1a985128413e4e8f70582fe52ea2",
            "matches": true
          },
          "ligand": {
            "sha256": "f9c72e23a1f2afe893c672da0412e82fa8345be23902d1d5cc7c17971193f623",
            "matches": true
          }
        }
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
        "apo_receptor_source": "pdbs/1sg6__A1_P07547.pdb",
        "apo_ligand_source": "pdbs/1sg6__A1_P07547.pdb",
        "reference": "pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb",
        "historical_prepared_sha256": {
          "receptor": "ec52d962eacf8e92518ead142a51f6feb18e8d74590ea7048fffc461f52cacf2",
          "ligand": "83ad5cf3938c63172fea2254e31e6fe05d5751d072323ff7ed3463d92af0d1a2"
        },
        "intake_generated_hash_check": {
          "receptor": {
            "sha256": "ec52d962eacf8e92518ead142a51f6feb18e8d74590ea7048fffc461f52cacf2",
            "matches": true
          },
          "ligand": {
            "sha256": "83ad5cf3938c63172fea2254e31e6fe05d5751d072323ff7ed3463d92af0d1a2",
            "matches": true
          }
        }
      }
    ],
    "required_inputs": [
      {
        "path": "pdbs/1sg6__A1_P07547.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb",
        "sha256": "4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5",
        "availability": "available",
        "verification": {
          "url": "https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb",
          "status": 200,
          "method": "GET",
          "bytes": 234171,
          "sha256": "4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5",
          "recorded_sha256": "4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5",
          "hash_matches": true
        },
        "licence": null,
        "licence_reason": "Input coverage not established by retrieved code licence."
      },
      {
        "path": "pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb",
        "sha256": "111ed0e1daea9ff8575bb61a2184b5f58fedd5437846e0f8026bebb53ef77a10",
        "availability": "available",
        "verification": {
          "url": "https://pinderdata.org/2024-02/pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb",
          "status": 200,
          "method": "GET",
          "bytes": 300591,
          "sha256": "111ed0e1daea9ff8575bb61a2184b5f58fedd5437846e0f8026bebb53ef77a10",
          "recorded_sha256": "111ed0e1daea9ff8575bb61a2184b5f58fedd5437846e0f8026bebb53ef77a10",
          "hash_matches": true
        },
        "licence": null,
        "licence_reason": "Input coverage not established by retrieved code licence."
      },
      {
        "path": "pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb",
        "sha256": "a12fd5f7506b927c1d435464cabbb9cd59299fdc4a826b63302052b0fef41a48",
        "availability": "available",
        "verification": {
          "url": "https://pinderdata.org/2024-02/pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb",
          "status": 200,
          "method": "GET",
          "bytes": 388881,
          "sha256": "a12fd5f7506b927c1d435464cabbb9cd59299fdc4a826b63302052b0fef41a48",
          "recorded_sha256": "a12fd5f7506b927c1d435464cabbb9cd59299fdc4a826b63302052b0fef41a48",
          "hash_matches": true
        },
        "licence": null,
        "licence_reason": "Input coverage not established by retrieved code licence."
      },
      {
        "path": "pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb",
        "sha256": "ee2fc49ec38f26a216154fd7ce0a93086f2ba60dde6997d86deb196bac96f861",
        "availability": "available",
        "verification": {
          "url": "https://pinderdata.org/2024-02/pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb",
          "status": 200,
          "method": "GET",
          "bytes": 484785,
          "sha256": "ee2fc49ec38f26a216154fd7ce0a93086f2ba60dde6997d86deb196bac96f861",
          "recorded_sha256": "ee2fc49ec38f26a216154fd7ce0a93086f2ba60dde6997d86deb196bac96f861",
          "hash_matches": true
        },
        "licence": null,
        "licence_reason": "Input coverage not established by retrieved code licence."
      },
      {
        "path": "pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb",
        "sha256": "a159da5b6b145570b4d03ac9e17eb7b4315f7a8afd0497a93ad1f77a55debf3e",
        "availability": "available",
        "verification": {
          "url": "https://pinderdata.org/2024-02/pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb",
          "status": 200,
          "method": "GET",
          "bytes": 536625,
          "sha256": "a159da5b6b145570b4d03ac9e17eb7b4315f7a8afd0497a93ad1f77a55debf3e",
          "recorded_sha256": "a159da5b6b145570b4d03ac9e17eb7b4315f7a8afd0497a93ad1f77a55debf3e",
          "hash_matches": true
        },
        "licence": null,
        "licence_reason": "Input coverage not established by retrieved code licence."
      },
      {
        "path": "pdbs/3g8c__A1_P24182.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/3g8c__A1_P24182.pdb",
        "sha256": "48aa5f4b2ac1e57d855b85d56a9c4a74c4b16f7d165b0fce03535815e26bdb60",
        "availability": "available",
        "verification": {
          "url": "https://pinderdata.org/2024-02/pdbs/3g8c__A1_P24182.pdb",
          "status": 200,
          "method": "GET",
          "bytes": 277182,
          "sha256": "48aa5f4b2ac1e57d855b85d56a9c4a74c4b16f7d165b0fce03535815e26bdb60",
          "recorded_sha256": "48aa5f4b2ac1e57d855b85d56a9c4a74c4b16f7d165b0fce03535815e26bdb60",
          "hash_matches": true
        },
        "licence": null,
        "licence_reason": "Input coverage not established by retrieved code licence."
      },
      {
        "path": "pdbs/6f0e__A1_P24280.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb",
        "sha256": "622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd",
        "availability": "available",
        "verification": {
          "url": "https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb",
          "status": 200,
          "method": "GET",
          "bytes": 192456,
          "sha256": "622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd",
          "recorded_sha256": "622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd",
          "hash_matches": true
        },
        "licence": null,
        "licence_reason": "Input coverage not established by retrieved code licence."
      },
      {
        "path": "pdbs/3n35__A1_P16404.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb",
        "sha256": "b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e",
        "availability": "available",
        "verification": {
          "url": "https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb",
          "status": 200,
          "method": "GET",
          "bytes": 151794,
          "sha256": "b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e",
          "recorded_sha256": "b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e",
          "hash_matches": true
        },
        "licence": null,
        "licence_reason": "Input coverage not established by retrieved code licence."
      },
      {
        "path": "pdbs/3g8d__A1_P24182.pdb",
        "url": "https://pinderdata.org/2024-02/pdbs/3g8d__A1_P24182.pdb",
        "sha256": "1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c",
        "availability": "available",
        "verification": {
          "url": "https://pinderdata.org/2024-02/pdbs/3g8d__A1_P24182.pdb",
          "status": 200,
          "method": "GET",
          "bytes": 234657,
          "sha256": "1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c",
          "recorded_sha256": "1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c",
          "hash_matches": true
        },
        "licence": null,
        "licence_reason": "Input coverage not established by retrieved code licence."
      },
      {
        "path": "index.parquet",
        "url": "https://pinderdata.org/2024-02/index.parquet",
        "sha256": "ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4",
        "availability": "available",
        "verification": {
          "url": "https://pinderdata.org/2024-02/index.parquet",
          "status": 200,
          "method": "HEAD",
          "bytes": 0,
          "sha256": null
        },
        "licence": null,
        "licence_reason": "Input coverage not established by retrieved code licence."
      }
    ],
    "availability": "available",
    "availability_reason": "Index responds to anonymous HEAD; all nine unique selected raw PDB objects retrieved with matching published-in-brief hashes. All eight historical prepared hashes reproduced in memory using exact chain-column preparation. Setup must repeat verification; index payload not downloaded during intake.",
    "access_instructions": "Anonymous HTTPS GET each required URL; verify SHA-256 from brief before use. No full PINDER archive download needed.",
    "generated_inputs": {
      "prepared_PDBs": "Generated from pinned raw apo PDBs, modifying only column 22 on ATOM/HETATM/ANISOU/TER records; retain all other bytes and line endings. Copy short aliases byte-for-byte.",
      "custom_index": "Select exactly four system IDs from index.parquet; validate canonical apo filenames.",
      "poses": "Generated by pinned CPU MEGADOCK and decoygen; 50 ranked complexes per case, END only after both chains.",
      "residue_mapping": "Computed by pinned BiotiteDockQ with fixed R/L semantics; capture correspondence before timing. No missing external curated map."
    },
    "splits": {
      "selection": "Four fixed PINDER-S apo cases in supplied order, original unit indices 3,5,9,15. No resampling or train/test reassignment."
    },
    "seeds": null,
    "seeds_reason": "No random seed specified; fixed rotational enumeration and fixed cases. Record actual determinism during reproduction.",
    "licences": [
      {
        "item": "MEGADOCK code",
        "licence": "CC-BY-NC-4.0",
        "basis": "explicit",
        "source": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/README.md",
        "intended_use": "Local scientific runtime calibration; noncommercial use permitted subject to attribution. Commercial authorization not established; brief does not establish commercial status."
      },
      {
        "item": "PINDER evaluator code",
        "licence": "Apache-2.0",
        "basis": "explicit",
        "source": "https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/LICENSE",
        "intended_use": "Execution and modification permitted under Apache-2.0 conditions."
      },
      {
        "item": "PINDER release 2024-02 index and selected PDB inputs/native references",
        "licence": null,
        "basis": "none",
        "source": [
          "https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/README.md",
          "https://pinderdata.org/2024-02/"
        ],
        "reason": "Retrieved repository README and LICENSE establish code licence but do not explicitly establish coverage of externally hosted index and structures. No applicable input terms found in bounded inspection. Owner mirror authorization is not a licence grant from input rights holders."
      }
    ],
    "auxiliary_data": "Historical FroDock mirror, full monomer archive, alternative apo/predicted structures and mapping parquet files are not required for this CPU MEGADOCK calibration. Preserve historical unverified_mirror provenance; do not substitute FroDock.",
    "source": {
      "path": "brief.md",
      "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
      "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
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
      "configuration": "CPU standard, fixed 3600 rotations, 26 OpenMP threads; one serial docking run per case retaining 50 predictions. Four serial evaluator blocks visiting all cases in listed order, one fresh Python subprocess each: exactly 16 evaluations of 50 poses.",
      "hardware_target": "One H100 PCIe 80GB allocation, 26-logical-CPU host entitlement; GPU remains idle during CPU docking.",
      "scale_search": false
    },
    "inputs": {
      "manifest": "data.json cases, required_inputs, historical_prepared_sha256",
      "pins": "baseline.json",
      "evaluation_only": "Native bound references never accessed by docking command harness. Fixed native and decoy receptor R / ligand L; parallel_io=False.",
      "environment": {
        "OMP_NUM_THREADS": "26",
        "OMP_DYNAMIC": "FALSE",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "LC_ALL": "C",
        "LANG": "C"
      },
      "CUDA_MPS": "Preserve inherited CUDA_MPS_* unchanged; no daemon management."
    },
    "outputs": {
      "primary": "out/calibration.json",
      "fields": [
        "protocol identity/hash",
        "cases/configuration",
        "pins",
        "setup checks",
        "native-self smoke values",
        "16 records {case_id,block,status,wall_s or null,lower_bound_s or null,n_scored}",
        "T_s or null",
        "per-case maxima",
        "allowance60_screen pass|fail|unknown",
        "CPU-standard-only scope",
        "stage walls",
        "allocation projection and receipts"
      ],
      "retained": "All 200 ranked PDB complexes, docking output/logs, 16 full evaluator CSVs, raw timings, failures, manifests and source/input/native/script/binary/dependency hashes. Preserve endpoint values without quality verdicts."
    },
    "timing_scope": {
      "primary": "Parent monotonic immediately before fresh child creation through successful child exit and CSV existence/size check. Includes interpreter/import, reading all 50 poses plus native, calculate(), validate 50 unique model_1..model_50 and finite DockQ, serialize and flush full CSV.",
      "excluded": "Setup/install, docking/reconstruction, operator retrieval/export; separately time and charge allocation wall.",
      "secondary": "Calculation-only wall, docking printed timers, invocation-to-last-pose wall; never replace complete child wall.",
      "child_timeout_s": 180,
      "timeout_rule": "Process-group cleanup; preserve partial artifacts. Timeout is right-censored lower bound, T unknown, allowance failed if evaluator lower bound exceeds 60; never replace completed wall with 180. Continue fixed remaining attempts only within lifecycle budget.",
      "scoring": "T=max(all 16 complete child walls); any valid >60 witness falsifies allowance despite later failure. All 16 <=60 passes provisionally only with valid setup/pins/smokes. Invalid/missing rows, nonfinite values, bad identity or timing means inconclusive without valid falsifying witness."
    },
    "checks_before_timing": [
      "Verify raw and all eight generated prepared hashes; capture actual binary/dependency identities and fixed reference correspondence.",
      "Four header lines plus 50 finite seven-field ranked rows; positive actual grid, voxel 1.2 and standard sampling; 50 readable nonempty complexes with expected R/L chains and atom inventory.",
      "Native-self evaluator smoke per case: DockQ 1 within 1e-6, fixed DESIGN criterion, failure stops benchmark."
    ],
    "harness_contract": {
      "run_command.sh": "Only four serial CPU-standard docking jobs once each, reconstruct all 50 complexes per case; no evaluator import/native access.",
      "run_anchors.sh": "Invoke bash harness/run_command.sh exactly once, then checks and evaluator calibration. Empty published anchors remain empty.",
      "stop": "External --stop-after-reproduce wrapper must stop after setup/anchors/freeze; no later scientific pipeline stages.",
      "source": {
        "path": "brief.md",
        "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
        "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
      }
    },
    "budget": {
      "allocation_limit_s": 7200,
      "stop_new_science_at_s": 5400,
      "export_termination_reserve_s": 1800,
      "hard_spend_USD": 10,
      "historical_tariff_USD_per_h": 3.29,
      "historical_tariff_is_current": false,
      "current_tariff": null,
      "current_tariff_reason": "Must verify compatible current allocation tariff/taxes/termination projection before launch.",
      "projected_all_in_USD": 8,
      "projection_source": {
        "path": "brief.md",
        "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
        "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
      },
      "launch_gate": "Verify watchdog, stop wrapper and bounded termination; no launch if projection > USD10 or cannot remain strictly below USD20. Stop at 2 allocated hours or USD10, whichever first. No paid persistent filesystem or replacement rental.",
      "invoice": null,
      "invoice_reason": "No allocation performed during intake."
    },
    "stage_budgets_s": null,
    "stage_budgets_reason": "No new per-script estimates or overrides invented; owner lifecycle and 180-second child limits apply. Supplied argument budgets empty; defaults remain unless harness explicitly enforces tighter lifecycle.",
    "source": {
      "path": "brief.md",
      "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
      "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
    }
  },
  "anchors": [],
  "benchmark": {
    "identity": {
      "name": "MEGADOCK CPU-standard / pinned PINDER evaluator runtime calibration s03",
      "brief": {
        "path": "brief.md",
        "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
        "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
      },
      "scope": "Four-case pilot; only CPU standard. Fresh descriptive calibration using published docking code/commands and public pinned inputs; not an independently published evaluator timing benchmark."
    },
    "found": true,
    "outcome_definition": {
      "primary": "T=max of 16 complete evaluator child-process wall times, four fixed serial blocks x four cases.",
      "criterion": "All 16 valid complete timings <=60 seconds retains candidate provisionally. Any valid complete wall or confirmed evaluator-only elapsed lower bound >60 rejects unchanged allowance. Otherwise unknown.",
      "threshold_provenance": "Owner-defined screen in brief, not published anchor.",
      "limitations": "CPU-standard outputs only. No CPU/GPU agreement verdict, dense-search quality inference, biological efficacy claim, or full card_number_resolved."
    },
    "citations": [
      {
        "citation": "Ohue et al. MEGADOCK 4.0, Bioinformatics 30(22):3281-3283 (2014)",
        "url": "https://doi.org/10.1093/bioinformatics/btu532",
        "source": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/README.md"
      },
      {
        "citation": "Pinned PINDER source README and evaluator; release 2024-02",
        "url": "https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/README.md"
      },
      {
        "path": "brief.md",
        "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
        "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
      }
    ],
    "source_licences": [
      {
        "item": "MEGADOCK code",
        "licence": "CC-BY-NC-4.0",
        "basis": "explicit",
        "source": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/README.md",
        "intended_use": "Local scientific runtime calibration; noncommercial use permitted subject to attribution. Commercial authorization not established; brief does not establish commercial status."
      },
      {
        "item": "PINDER evaluator code",
        "licence": "Apache-2.0",
        "basis": "explicit",
        "source": "https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/LICENSE",
        "intended_use": "Execution and modification permitted under Apache-2.0 conditions."
      },
      {
        "item": "PINDER release 2024-02 index and selected PDB inputs/native references",
        "licence": null,
        "basis": "none",
        "source": [
          "https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/README.md",
          "https://pinderdata.org/2024-02/"
        ],
        "reason": "Retrieved repository README and LICENSE establish code licence but do not explicitly establish coverage of externally hosted index and structures. No applicable input terms found in bounded inspection. Owner mirror authorization is not a licence grant from input rights holders."
      }
    ],
    "licence": "unknown",
    "licence_basis": "none",
    "stock_CUDA_image": {
      "stock_environment": true,
      "evidence": [
        "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/doc/BUILD.md",
        {
          "path": "brief.md",
          "sha256": "e597bbae4693f25fe0fbc7cd29704d14046694662f4e5cb0edde80c0ca5b0791",
          "section": "Calibration request (science step s03) and Historical evidence supplied to close run3 intake failure"
        }
      ],
      "reason": "Provisionally feasible: published CPU/OpenMP backend requires GNU compiler and float FFTW, not GPU build; supplied historical stock setup succeeded with CPU MEGADOCK and same pinned evaluator. Actual compatibility, entitlement and dependency identities require reproduction.",
      "actual_image_digest": null,
      "actual_image_digest_reason": "No immutable stock image digest supplied."
    },
    "memory": {
      "required_source_bytes": 127312981,
      "data_GiB": 0.1185694532468915,
      "peak_working_set_GiB": null,
      "data_plus_peak_working_set_GiB": null,
      "size": "unknown",
      "reason": "Source bytes known; preparation, output storage and peak host working set unmeasured. H100 80GB capacity is not workload memory measurement."
    },
    "scoring_and_repeatability": {
      "independent_anchors": 0,
      "published_values": null,
      "reason": "No independently published result for these four cases at this endpoint in supplied evidence. No substitute benchmarks searched. Design smoke and 60-second owner screen are not anchors.",
      "protocol": "See EXECUTION.json. Retain all 16 timings including first block, no warmup exclusions, cache flushing, added repeats or retries beyond bounded infrastructure rules.",
      "smoke": "Per-case native-self DockQ 1 within 1e-6; DESIGN identity check prescribed in brief, not independent validation."
    },
    "search_candidates": [],
    "contract_gaps": [
      "Fresh harness must place descriptive calibration artifacts under out/ without synthetic anchors. Intake anchors remain empty.",
      "External stop-after-reproduce wrapper, watchdog, compatible tariff and bounded termination not verified by intake; verify before paid work. No profile, seal, propose, implement or evaluate continuation."
    ],
    "current_results": null,
    "current_results_reason": "Intake performs no build or scientific workload."
  }
}
MANIFEST
"$vpy" - <<'PYSETUP'
import json,pathlib,hashlib,urllib.request,shutil,subprocess,os,importlib.metadata as md
import torch,pandas as pd
from pinder.eval.dockq import BiotiteDockQ
P=pathlib.Path
stock=json.loads(P('out/setup/stock-torch.json').read_text())
assert torch.__version__==stock['version'] and str(P(torch.__file__))==stock['path'], 'Stock torch replaced'
assert hashlib.sha256(P(torch.__file__).read_bytes()).hexdigest()==stock['sha256']
m=json.loads(P('data/manifest.json').read_text()); root=P('data/2024-02'); root.mkdir(parents=True,exist_ok=True)
hashes={}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for obj in m['data']['required_inputs']:
    p=root/obj['path']; p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists() or digest(p)!=obj['sha256']:
        tmp=p.with_suffix(p.suffix+'.download')
        with urllib.request.urlopen(obj['url'],timeout=180) as r,tmp.open('wb') as w: shutil.copyfileobj(r,w)
        assert digest(tmp)==obj['sha256'], 'Raw input hash mismatch: '+str(p)
        tmp.replace(p)
    assert digest(p)==obj['sha256']; hashes[str(p)]=digest(p)
index=pd.read_parquet(root/'index.parquet'); cases=m['data']['cases']
selected=index[index.id.isin([c['system_id'] for c in cases])]
assert len(selected)==4 and selected.id.nunique()==4
selected.to_parquet('data/custom_index.parquet',index=False)
for c in cases:
    row=selected.loc[selected.id==c['system_id']].iloc[0]
    for role,chain in [('receptor','R'),('ligand','L')]:
        src=c['apo_'+role+'_source']; assert row['apo_'+chain+'_pdb']==P(src).name
        lines=[]
        for line in (root/src).read_text().splitlines(keepends=True):
            if line.startswith(('ATOM  ','HETATM','ANISOU','TER   ')): line=line[:21]+chain+line[22:]
            lines.append(line)
        dest=P('data')/c['prepared_record'][role]; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(''.join(lines))
        assert digest(dest)==c['historical_prepared_sha256'][role], 'Prepared identity mismatch'
        alias=P('data/inputs')/(c['system_id'][:4]+'_'+chain+'.pdb'); alias.parent.mkdir(exist_ok=True); alias.write_bytes(dest.read_bytes())
        hashes[str(dest)]=digest(dest); hashes[str(alias)]=digest(alias)
versions={x:md.version(x) for x in ['torch','numpy','biotite','networkx','pandas','scikit-learn','pinder']}
for x,v in m['baseline']['evaluator']['dependencies'].items():
    if x!='torch': assert versions[x]==v,(x,versions[x],v)
for repo in ['megadock','pinder']:
    files=subprocess.check_output(['git','-C','baseline-published/'+repo,'ls-files','-z']).decode().split('\0')
    for name in files:
        p=P('baseline-published')/repo/name
        if p.is_file(): hashes[str(p)]=digest(p)
for name in ['megadock','decoygen']:
    p=P('baseline-published/megadock')/name; assert os.access(p,os.X_OK); hashes[str(p)]=digest(p)
for p in P('harness').glob('*.sh'): hashes[str(p)]=digest(p)
for name in ['numpy','biotite','pandas','sklearn','torch']:
    mod=__import__(name); p=P(mod.__file__); hashes[str(p)]=digest(p)
P('data/verified_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
checks={'pins':{r:subprocess.check_output(['git','-C','baseline-published/'+r,'rev-parse','HEAD'],text=True).strip() for r in ['megadock','pinder']},'versions':versions,'stock_torch_preserved':True,'prepared_hashes_valid':True,'cuda':{k:os.environ[k] for k in ['CUDACXX','CUDA_INCLUDE_DIR','CUDA_LIBRARY_DIR']},'affinity':sorted(os.sched_getaffinity(0)),'allocation_identity':{k:os.environ.get(k) for k in ['HOSTNAME','SLURM_JOB_ID']},'historical_torch_changed':versions['torch']!='2.7.0'}
P('out/setup/checks.json').write_text(json.dumps(checks,indent=2)+'\n')
P('data/setup_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
PYSETUP
/usr/bin/g++ --version
"$CUDACXX" --version
lscpu
cat /proc/meminfo
ldd baseline-published/megadock/megadock
sha256sum baseline-published/megadock/megadock baseline-published/megadock/decoygen
# The pinned binary returns 255 after printing help (observed in setup output).
# Keep that documented help status separate from build or workload failures.
help_status=0
baseline-published/megadock/megadock -h > out/setup/megadock-help.log 2>&1 || help_status=$?
cat out/setup/megadock-help.log
echo "MEGADOCK help exit status: $help_status"
if [[ $help_status != 0 && $help_status != 255 ]]; then
    echo "MEGADOCK help failed with unexpected status: $help_status" >&2
    exit "$help_status"
fi
if ! grep -Eq 'MEGADOCK ver\..*for CPU & single node' out/setup/megadock-help.log ||
   ! grep -Fq 'Usage: megadock -R [receptor.pdb] -L [ligand.pdb]' out/setup/megadock-help.log ||
   ! grep -Fq 'Available options:' out/setup/megadock-help.log; then
    echo 'Missing or invalid MEGADOCK CPU help output' >&2
    exit 1
fi
