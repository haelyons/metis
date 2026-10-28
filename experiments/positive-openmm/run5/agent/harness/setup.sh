#!/usr/bin/env bash
set -euo pipefail
mkdir -p baseline-published data out
exec > >(tee -a out/setup.log) 2>&1
# Select only toolkit locations reported by the box probe.
selected=0
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -f "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
        printf 'export CUDA_COMPILER=%q\nexport CUDA_INCLUDE=%q\nexport CUDA_LIBRARY=%q\nexport CUDAToolkit_ROOT=%q\n' "$root/bin/nvcc" "$root/include" "$root/lib64" "$root" > baseline-published/cuda.env
        selected=1
        break
    fi
done
if [[ "$selected" == 0 ]]; then
    if [[ -f /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
        printf '%s\n' 'export CUDA_COMPILER=/usr/bin/nvcc' 'export CUDA_INCLUDE=/usr/include' 'export CUDA_LIBRARY=/usr/lib/x86_64-linux-gnu' > baseline-published/cuda.env
    else
        echo 'No complete probed CUDA toolkit or distro layout available' >&2
        exit 1
    fi
fi
source baseline-published/cuda.env
ls -l "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY/libcudart.so"
export PATH="$(dirname "$CUDA_COMPILER"):$PATH"
export LD_LIBRARY_PATH="$CUDA_LIBRARY${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CPATH="$CUDA_INCLUDE${CPATH:+:$CPATH}"
export LIBRARY_PATH="$CUDA_LIBRARY${LIBRARY_PATH:+:$LIBRARY_PATH}"
export CMAKE_CUDA_COMPILER="$CUDA_COMPILER"
export OPENMM_CUDA_COMPILER="$CUDA_COMPILER"
export PYTHONDONTWRITEBYTECODE=1
pin=53770948682c40bd460b39830d4e0f0fd3a4b868
if [[ ! -d baseline-published/source/.git ]]; then
    git init baseline-published/source
    git -C baseline-published/source remote add origin https://github.com/openmm/openmm
fi
git -C baseline-published/source fetch --depth 1 origin "$pin"
git -C baseline-published/source checkout --detach FETCH_HEAD
[[ "$(git -C baseline-published/source rev-parse HEAD)" == "$pin" ]]
python3 -m pip install --upgrade --target baseline-published/site openmm==8.2.0 OpenMM-CUDA-12==8.2.0
cp baseline-published/source/examples/5dfr_solv-cube_equil.pdb data/
cp baseline-published/source/wrappers/python/openmm/app/data/{amber99sb.xml,tip3p.xml} data/
printf '%s  %s\n' fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf data/5dfr_solv-cube_equil.pdb | sha256sum -c -
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
export PYTHONPATH="$PWD/baseline-published/site${PYTHONPATH:+:$PYTHONPATH}"
export CUDA_VISIBLE_DEVICES=0
python3 - <<'CHECK'
import importlib.metadata as m
import openmm
assert m.version('openmm') == '8.2.0'
assert m.version('OpenMM-CUDA-12') == '8.2.0'
print('OpenMM', openmm.__version__)
CHECK
python3 -m openmm.testInstallation
