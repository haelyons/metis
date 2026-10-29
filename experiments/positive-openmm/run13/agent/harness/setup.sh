#!/usr/bin/env bash
set -euo pipefail
mkdir -p baseline-published data out
exec > >(tee -a out/setup.log) 2>&1
select_cuda() {
    local root
    CUDA_NVCC=
    for root in /usr/local/cuda /usr/lib/cuda; do
        if [[ -x "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
            CUDA_NVCC="$root/bin/nvcc"
            CUDA_INCLUDE="$root/include"
            CUDA_LIBRARY="$root/lib64"
            export CUDAToolkit_ROOT="$root"
            break
        fi
    done
    if [[ -z "${CUDA_NVCC:-}" ]]; then
        CUDA_NVCC=/usr/bin/nvcc
        CUDA_INCLUDE=/usr/include
        CUDA_LIBRARY=/usr/lib/x86_64-linux-gnu
    fi
    ls "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY/libcudart.so"
    export PATH="${CUDA_NVCC%/*}:$PATH"
    export LD_LIBRARY_PATH="$CUDA_LIBRARY${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    export OPENMM_CUDA_COMPILER="$CUDA_NVCC"
}
select_cuda

export PYTHONNOUSERSITE=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export CUDA_VISIBLE_DEVICES=0
export GPU_COUNT=1
command -v git
/usr/bin/python3 -m pip --version
pin=53770948682c40bd460b39830d4e0f0fd3a4b868
if [[ ! -d baseline-published/source/.git ]]; then
    git clone --no-checkout --depth 1 --branch 8.2.0 https://github.com/openmm/openmm baseline-published/source
fi
git -C baseline-published/source fetch --depth 1 origin "$pin"
git -C baseline-published/source checkout --detach "$pin"
test "$(git -C baseline-published/source rev-parse HEAD)" = "$pin"
/usr/bin/python3 -m pip install --upgrade --target baseline-published/python openmm==8.2.0 OpenMM-CUDA-12==8.2.0
cat > baseline-published/dhfr_ensemble.py <<'DRIVER'
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
DRIVER
/usr/bin/python3 - <<'DATA'
import hashlib
from pathlib import Path
import urllib.request
items = [{'name': '5dfr_solv-cube_equil.pdb', 'kind': 'published input', 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 1814203, 'sha256': 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf', 'verification': 'Public URL fetched; byte size and SHA-256 computed during intake without executing baseline.', 'access': 'No authentication required. PDB must be in driver working directory; force-field XML files ship inside OpenMM package.', 'licence_source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'intended_use_permission_source': 'intake/brief.md'}, {'name': 'amber99sb.xml', 'kind': 'published input', 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/amber99sb.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 467697, 'sha256': '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092', 'verification': 'Public URL fetched; byte size and SHA-256 computed during intake without executing baseline.', 'access': 'No authentication required. PDB must be in driver working directory; force-field XML files ship inside OpenMM package.', 'licence_source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'intended_use_permission_source': 'intake/brief.md'}, {'name': 'tip3p.xml', 'kind': 'published input', 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/tip3p.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 891, 'sha256': '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c', 'verification': 'Public URL fetched; byte size and SHA-256 computed during intake without executing baseline.', 'access': 'No authentication required. PDB must be in driver working directory; force-field XML files ship inside OpenMM package.', 'licence_source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'intended_use_permission_source': 'intake/brief.md'}]
for item in items:
    p = Path('data') / item['name']
    if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != item['sha256']:
        blob = urllib.request.urlopen(item['url'], timeout=120).read()
        if len(blob) != item['bytes'] or hashlib.sha256(blob).hexdigest() != item['sha256']:
            raise RuntimeError('Invalid input download: ' + item['name'])
        p.write_bytes(blob)
    print('Verified input:', p)
DATA
export PYTHONPATH="$PWD/baseline-published/python"
/usr/bin/python3 - <<'CHECK'
import importlib.metadata as m
import openmm
for name in ('openmm', 'OpenMM-CUDA-12'):
    if m.version(name) != '8.2.0':
        raise RuntimeError('Wrong installed version: ' + name)
print('OpenMM:', openmm.version.full_version)
if 'CUDA' not in [openmm.Platform.getPlatform(i).getName() for i in range(openmm.Platform.getNumPlatforms())]:
    raise RuntimeError('CUDA platform missing: ' + str(openmm.Platform.getPluginLoadFailures()))
CHECK
/usr/bin/python3 -m openmm.testInstallation
