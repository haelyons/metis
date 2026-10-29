#!/usr/bin/env bash
set -euo pipefail
mkdir -p baseline-published data out
exec > >(tee -a out/setup.log) 2>&1
# Select only toolkit layouts discovered by the box probe.
if [[ -f /usr/local/cuda/bin/nvcc && -f /usr/local/cuda/include/cuda_runtime.h && -f /usr/local/cuda/lib64/libcudart.so ]]; then
    CUDA_COMPILER=/usr/local/cuda/bin/nvcc
    CUDA_INCLUDE=/usr/local/cuda/include
    CUDA_LIBRARY=/usr/local/cuda/lib64
    export CUDAToolkit_ROOT=/usr/local/cuda
elif [[ -f /usr/lib/cuda/bin/nvcc && -f /usr/lib/cuda/include/cuda_runtime.h && -f /usr/lib/cuda/lib64/libcudart.so ]]; then
    CUDA_COMPILER=/usr/lib/cuda/bin/nvcc
    CUDA_INCLUDE=/usr/lib/cuda/include
    CUDA_LIBRARY=/usr/lib/cuda/lib64
    export CUDAToolkit_ROOT=/usr/lib/cuda
elif [[ -f /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    CUDA_COMPILER=/usr/bin/nvcc
    CUDA_INCLUDE=/usr/include
    CUDA_LIBRARY=/usr/lib/x86_64-linux-gnu
else
    echo 'No complete CUDA toolkit found in probe-discovered layouts' >&2
    exit 1
fi
ls "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY/libcudart.so"
export CMAKE_CUDA_COMPILER="$CUDA_COMPILER"
export PATH="${CUDA_COMPILER%/nvcc}:/usr/bin:/bin"
export CPATH="$CUDA_INCLUDE"
export LIBRARY_PATH="$CUDA_LIBRARY"
export LD_LIBRARY_PATH="$CUDA_LIBRARY"
export CUDA_VISIBLE_DEVICES=0
export PYTHONNOUSERSITE=1
export PYTHONHASHSEED=0

command -v git >/dev/null || { echo 'Required git missing; probe supplied no Ubuntu apt source' >&2; exit 1; }
/usr/bin/python3 -m pip --version
if [[ ! -d baseline-published/upstream/.git ]]; then
    git init baseline-published/upstream
fi
git -C baseline-published/upstream fetch --depth 1 https://github.com/openmm/openmm 53770948682c40bd460b39830d4e0f0fd3a4b868
git -C baseline-published/upstream checkout --detach FETCH_HEAD
test "$(git -C baseline-published/upstream rev-parse HEAD)" = 53770948682c40bd460b39830d4e0f0fd3a4b868
/usr/bin/python3 -m pip install --upgrade --target baseline-published/python openmm==8.2.0 OpenMM-CUDA-12==8.2.0
cat > baseline-published/dhfr_ensemble.py <<'PUBLISHED_DRIVER'
#!/usr/bin/env python3
"""Fixed-work DHFR ensemble: independent replicas of the OpenMM 8.2.0 examples/benchmark.py `pme` system, run one after another."""
import argparse
import json
import time

import openmm as mm
from openmm import app, unit

parser = argparse.ArgumentParser()
parser.add_argument('--replicas', type=int, default=8)
parser.add_argument('--steps', type=int, default=25000)
parser.add_argument('--seed0', type=int, default=1000)
parser.add_argument('--platform', default='CUDA')
parser.add_argument('--out', default='ensemble.json')
args = parser.parse_args()
assert args.replicas > 0 and args.steps > 0 and args.steps % 250 == 0

# System exactly as benchmark.py builds `--test pme` with default options (hbonds, cutoff 0.9 nm).
pdb = app.PDBFile('5dfr_solv-cube_equil.pdb')
forcefield = app.ForceField('amber99sb.xml', 'tip3p.xml')
system = forcefield.createSystem(pdb.topology, nonbondedMethod=app.PME, nonbondedCutoff=0.9,
                                 constraints=app.HBonds, hydrogenMass=1.5 * unit.amu)
platform = mm.Platform.getPlatformByName(args.platform)
properties = {'Precision': 'single', 'DeterministicForces': 'true'} if args.platform == 'CUDA' else {}

replicas = []
start = time.perf_counter()
for index in range(args.replicas):
    seed = args.seed0 + index
    integrator = mm.LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond, 0.004 * unit.picoseconds)
    integrator.setConstraintTolerance(1e-5)
    integrator.setRandomNumberSeed(seed)
    context = mm.Context(system, integrator, platform, properties)
    context.setPositions(pdb.positions)
    context.setVelocitiesToTemperature(300 * unit.kelvin, seed)
    began = time.perf_counter()
    energies = []
    for _ in range(args.steps // 250):
        integrator.step(250)
        energies.append(context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
    replicas.append(dict(replica=index, seed=seed, steps=args.steps, wall_s=time.perf_counter() - began,
                         final_potential_kj_mol=energies[-1], mean_potential_kj_mol=sum(energies) / len(energies)))
    del context, integrator
total = time.perf_counter() - start

simulated_ns = args.replicas * args.steps * 0.004 / 1000
with open(args.out, 'w') as handle:
    json.dump(dict(platform=args.platform, properties=properties, simulated_ns=simulated_ns,
                   total_wall_s=total, replicas=replicas), handle, indent=1)
print(f'total_wall_s: {total:.3f}')
print(f'aggregate_ns_per_day: {simulated_ns / total * 86400:.1f}')
PUBLISHED_DRIVER
/usr/bin/python3 - <<'PYDATA'
import hashlib, pathlib, urllib.request
inputs = [{'name': 'coordinates', 'repository_path': 'examples/5dfr_solv-cube_equil.pdb', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 1814203, 'sha256': 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf', 'availability': 'available', 'verification': 'Public HTTPS fetch succeeded and SHA-256 computed during intake; content not retained.', 'access': 'Coordinates: download pinned PDB beside driver. Force fields: shipped with openmm==8.2.0, loaded by filename.', 'licence_source': ['https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'brief.md'], 'separate_input_licence': None, 'separate_input_licence_reason': 'No separate input-specific licence verified.'}, {'name': 'protein force field', 'repository_path': 'wrappers/python/openmm/app/data/amber99sb.xml', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/amber99sb.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 467697, 'sha256': '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092', 'availability': 'available', 'verification': 'Public HTTPS fetch succeeded and SHA-256 computed during intake; content not retained.', 'access': 'Coordinates: download pinned PDB beside driver. Force fields: shipped with openmm==8.2.0, loaded by filename.', 'licence_source': ['https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'brief.md'], 'separate_input_licence': None, 'separate_input_licence_reason': 'No separate input-specific licence verified.'}, {'name': 'water force field', 'repository_path': 'wrappers/python/openmm/app/data/tip3p.xml', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/tip3p.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 891, 'sha256': '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c', 'availability': 'available', 'verification': 'Public HTTPS fetch succeeded and SHA-256 computed during intake; content not retained.', 'access': 'Coordinates: download pinned PDB beside driver. Force fields: shipped with openmm==8.2.0, loaded by filename.', 'licence_source': ['https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'brief.md'], 'separate_input_licence': None, 'separate_input_licence_reason': 'No separate input-specific licence verified.'}]
for item in inputs:
    target = pathlib.Path('data') / pathlib.Path(item['repository_path']).name
    if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != item['sha256']:
        with urllib.request.urlopen(item['url'], timeout=90) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != item['sha256']:
            raise RuntimeError('Input checksum mismatch: ' + item['name'])
        target.write_bytes(content)
PYDATA
# Persist the chosen system paths, avoiding different toolkit selection on later runs.
{
    printf 'export CMAKE_CUDA_COMPILER=%q\n' "$CUDA_COMPILER"
    printf 'export CPATH=%q\n' "$CUDA_INCLUDE"
    printf 'export LIBRARY_PATH=%q\n' "$CUDA_LIBRARY"
    printf 'export LD_LIBRARY_PATH=%q\n' "$CUDA_LIBRARY"
    printf 'export PATH=%q\n' "$PATH"
    if [[ "$CUDA_COMPILER" != /usr/bin/nvcc ]]; then
        printf 'export CUDAToolkit_ROOT=%q\n' "${CUDA_COMPILER%/bin/nvcc}"
    fi
} > baseline-published/cuda-env.sh
PYTHONPATH=baseline-published/python OPENMM_CPU_THREADS=1 /usr/bin/python3 -m openmm.testInstallation
PYTHONPATH=baseline-published/python /usr/bin/python3 - <<'PYCHECK'
import importlib.metadata as m
import openmm as mm
from openmm import app
assert m.version('OpenMM') == '8.2.0'
assert m.version('OpenMM-CUDA-12') == '8.2.0'
pdb = app.PDBFile('data/5dfr_solv-cube_equil.pdb')
assert pdb.topology.getNumAtoms() == 23558
assert mm.Platform.getPlatformByName('CUDA').getName() == 'CUDA'
print('Pinned baseline installation verified')
PYCHECK
