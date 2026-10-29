#!/usr/bin/env bash
set -euo pipefail
mkdir -p out baseline-published data
exec > >(tee -a out/setup.log) 2>&1
# Select only layouts discovered by the box probe; prefer complete roots.
CUDA_ROOT_SELECTED=
for candidate in /usr/local/cuda /usr/lib/cuda; do
    if [[ -f "$candidate/bin/nvcc" && -f "$candidate/include/cuda_runtime.h" && -f "$candidate/lib64/libcudart.so" ]]; then
        CUDA_ROOT_SELECTED=$candidate
        break
    fi
done
if [[ -n "$CUDA_ROOT_SELECTED" ]]; then
    export CUDACXX="$CUDA_ROOT_SELECTED/bin/nvcc"
    export CUDA_INCLUDE_DIR="$CUDA_ROOT_SELECTED/include"
    export CUDA_LIBRARY_DIR="$CUDA_ROOT_SELECTED/lib64"
    export CUDAToolkit_ROOT="$CUDA_ROOT_SELECTED"
    export PATH="$CUDA_ROOT_SELECTED/bin:/usr/bin:/bin"
else
    export CUDACXX=/usr/bin/nvcc
    export CUDA_INCLUDE_DIR=/usr/include
    export CUDA_LIBRARY_DIR=/usr/lib/x86_64-linux-gnu
    export PATH=/usr/bin:/bin
fi
ls "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
export LD_LIBRARY_PATH="$CUDA_LIBRARY_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CUDA_VISIBLE_DEVICES=0
export GPU_COUNT=1
export PYTHONNOUSERSITE=1

command -v /usr/bin/python3
command -v /usr/bin/git
/usr/bin/python3 -m pip --version
pin=53770948682c40bd460b39830d4e0f0fd3a4b868
if [[ ! -d baseline-published/source/.git ]]; then
    /usr/bin/git init baseline-published/source
    /usr/bin/git -C baseline-published/source remote add origin https://github.com/openmm/openmm
fi
/usr/bin/git -C baseline-published/source fetch --depth 1 origin "$pin"
/usr/bin/git -C baseline-published/source checkout --detach "$pin"
[[ $(/usr/bin/git -C baseline-published/source rev-parse HEAD) == "$pin" ]]
/usr/bin/python3 -m pip install --target baseline-published/python --upgrade 'openmm==8.2.0' 'OpenMM-CUDA-12==8.2.0'
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
/usr/bin/python3 - <<'INPUTS'
import hashlib, pathlib, shutil
items = [{'name': '5dfr_solv-cube_equil.pdb', 'kind': 'published input', 'required': True, 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb', 'access': 'Public HTTPS; no authentication. PDB must be in working directory; XML files ship with OpenMM.', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 1814203, 'sha256': 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf', 'verification': 'Fetched successfully; size and SHA-256 computed during intake.', 'licence': None, 'licence_reason': 'No separate per-file licence verified; see repository licence and brief intended-use permission.', 'licence_source': ['https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'brief.md']}, {'name': 'amber99sb.xml', 'kind': 'published input', 'required': True, 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/amber99sb.xml', 'access': 'Public HTTPS; no authentication. PDB must be in working directory; XML files ship with OpenMM.', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 467697, 'sha256': '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092', 'verification': 'Fetched successfully; size and SHA-256 computed during intake.', 'licence': None, 'licence_reason': 'No separate per-file licence verified; see repository licence and brief intended-use permission.', 'licence_source': ['https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'brief.md']}, {'name': 'tip3p.xml', 'kind': 'published input', 'required': True, 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/tip3p.xml', 'access': 'Public HTTPS; no authentication. PDB must be in working directory; XML files ship with OpenMM.', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 891, 'sha256': '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c', 'verification': 'Fetched successfully; size and SHA-256 computed during intake.', 'licence': None, 'licence_reason': 'No separate per-file licence verified; see repository licence and brief intended-use permission.', 'licence_source': ['https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'brief.md']}]
root = pathlib.Path('baseline-published/source')
for item in items:
    name = item['name']
    source = root / ('examples' if name.endswith('.pdb') else 'wrappers/python/openmm/app/data') / name
    content = source.read_bytes()
    if hashlib.sha256(content).hexdigest() != item['sha256']:
        raise RuntimeError('Input checksum mismatch: '+name)
    pathlib.Path('data', name).write_bytes(content)
INPUTS
export PYTHONPATH="$PWD/baseline-published/python"
unset OPENMM_PLUGIN_DIR
/usr/bin/python3 - <<'CHECK'
import openmm
from openmm import app
assert openmm.__version__ in ('8.2', '8.2.0')
assert app.PDBFile('data/5dfr_solv-cube_equil.pdb').topology.getNumAtoms() == 23558
assert openmm.Platform.getPlatformByName('CUDA')
print('OpenMM', openmm.__version__, 'CUDA platform available')
CHECK
/usr/bin/python3 -m openmm.testInstallation
