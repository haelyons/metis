#!/usr/bin/env bash
set -euo pipefail
mkdir -p out/setup baseline-published data
exec > >(tee -a out/setup/setup.log) 2>&1
export CUDA_VISIBLE_DEVICES=0
export PYTHONDONTWRITEBYTECODE=1
# Select only layouts discovered by the supplied probe.
if [[ -x /usr/local/cuda/bin/nvcc && -f /usr/local/cuda/include/cuda_runtime.h && -f /usr/local/cuda/lib64/libcudart.so ]]; then
    cuda_bin=/usr/local/cuda/bin/nvcc
    cuda_inc=/usr/local/cuda/include
    cuda_lib=/usr/local/cuda/lib64
    export CUDAToolkit_ROOT=/usr/local/cuda
elif [[ -x /usr/lib/cuda/bin/nvcc && -f /usr/lib/cuda/include/cuda_runtime.h && -f /usr/lib/cuda/lib64/libcudart.so ]]; then
    cuda_bin=/usr/lib/cuda/bin/nvcc
    cuda_inc=/usr/lib/cuda/include
    cuda_lib=/usr/lib/cuda/lib64
    export CUDAToolkit_ROOT=/usr/lib/cuda
elif [[ -x /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    cuda_bin=/usr/bin/nvcc
    cuda_inc=/usr/include
    cuda_lib=/usr/lib/x86_64-linux-gnu
else
    echo 'No complete probed CUDA toolkit or distro layout available' >&2
    exit 1
fi
ls "$cuda_bin" "$cuda_inc/cuda_runtime.h" "$cuda_lib/libcudart.so"
export OPENMM_CUDA_COMPILER="$cuda_bin"
export CUDACXX="$cuda_bin"
export CUDA_INCLUDE_DIR="$cuda_inc"
export CUDA_CUDART_LIBRARY="$cuda_lib/libcudart.so"
export PATH="${cuda_bin%/*}:$PATH"

# Isolated pip target leaves stock Python packages, including torch, intact.
python3 -m pip --version
if [[ ! -d baseline-published/source/.git ]]; then
    git init baseline-published/source
    git -C baseline-published/source remote add origin https://github.com/openmm/openmm
fi
git -C baseline-published/source fetch --depth 1 origin 53770948682c40bd460b39830d4e0f0fd3a4b868
git -C baseline-published/source checkout --detach 53770948682c40bd460b39830d4e0f0fd3a4b868
test "$(git -C baseline-published/source rev-parse HEAD)" = 53770948682c40bd460b39830d4e0f0fd3a4b868
python3 -m pip install --target baseline-published/python --upgrade openmm==8.2.0 OpenMM-CUDA-12==8.2.0
python3 - <<'PY_SETUP'
import hashlib, pathlib, urllib.request
p=pathlib.Path('data/5dfr_solv-cube_equil.pdb')
expected='fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf'
if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
    with urllib.request.urlopen('https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb', timeout=120) as response:
        content=response.read()
    if hashlib.sha256(content).hexdigest()!=expected: raise RuntimeError('PDB checksum mismatch')
    p.write_bytes(content)
PY_SETUP
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
export PYTHONPATH="$PWD/baseline-published/python${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$cuda_lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
for libdir in baseline-published/python/nvidia/*/lib; do
    if [[ -d "$libdir" ]]; then export LD_LIBRARY_PATH="$PWD/$libdir:$LD_LIBRARY_PATH"; fi
done
export CUDA_CACHE_PATH="$PWD/out/setup/cuda-cache"
mkdir -p "$CUDA_CACHE_PATH"
python3 -m openmm.testInstallation
python3 - <<'PY_CHECK'
import importlib.metadata as md
from openmm import app, unit
for package in ('openmm','OpenMM-CUDA-12'):
    if md.version(package) != '8.2.0': raise RuntimeError('Wrong version: '+package)
pdb=app.PDBFile('data/5dfr_solv-cube_equil.pdb')
if pdb.topology.getNumAtoms()!=23558: raise RuntimeError('Wrong atom count')
system=app.ForceField('amber99sb.xml','tip3p.xml').createSystem(pdb.topology,nonbondedMethod=app.PME,nonbondedCutoff=0.9,constraints=app.HBonds,hydrogenMass=1.5*unit.amu)
print('Baseline package, data, force-field and system checks passed', flush=True)
PY_CHECK
