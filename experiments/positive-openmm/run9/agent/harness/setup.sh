#!/usr/bin/env bash
set -euo pipefail
mkdir -p out data baseline-published
exec > >(tee -a out/setup.log) 2>&1
# Only toolkit locations discovered by the supplied probe are candidates.
CUDA_ROOT=""
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -x "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
        CUDA_ROOT="$root"
        break
    fi
done
if [[ -n "$CUDA_ROOT" ]]; then
    CUDA_COMPILER="$CUDA_ROOT/bin/nvcc"
    CUDA_INCLUDE="$CUDA_ROOT/include"
    CUDA_LIBRARY="$CUDA_ROOT/lib64"
elif [[ -x /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    CUDA_COMPILER=/usr/bin/nvcc
    CUDA_INCLUDE=/usr/include
    CUDA_LIBRARY=/usr/lib/x86_64-linux-gnu
else
    echo 'No complete probed CUDA toolkit or complete distro CUDA layout found.' >&2
    exit 1
fi
ls -l "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY/libcudart.so"
{
    printf 'export CUDA_COMPILER=%q\n' "$CUDA_COMPILER"
    printf 'export CUDA_INCLUDE=%q\n' "$CUDA_INCLUDE"
    printf 'export CUDA_LIBRARY=%q\n' "$CUDA_LIBRARY"
    if [[ -n "$CUDA_ROOT" ]]; then
        printf 'export CUDAToolkit_ROOT=%q\n' "$CUDA_ROOT"
    fi
    printf 'export PATH=%q:"$PATH"\n' "$(dirname "$CUDA_COMPILER")"
    printf 'export LD_LIBRARY_PATH=%q${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}\n' "$CUDA_LIBRARY"
    printf 'export CPATH=%q${CPATH:+:$CPATH}\n' "$CUDA_INCLUDE"
    printf 'export LIBRARY_PATH=%q${LIBRARY_PATH:+:$LIBRARY_PATH}\n' "$CUDA_LIBRARY"
    printf 'export OPENMM_CUDA_COMPILER=%q\n' "$CUDA_COMPILER"
} > baseline-published/cuda.env
source baseline-published/cuda.env
/usr/bin/python3 -m pip --version || { echo 'Stock pip missing; probe provides no enabled general Ubuntu apt repository.' >&2; exit 1; }
/usr/bin/git --version
pin=53770948682c40bd460b39830d4e0f0fd3a4b868
if [[ ! -d baseline-published/source/.git ]]; then
    /usr/bin/git init baseline-published/source
    /usr/bin/git -C baseline-published/source remote add origin https://github.com/openmm/openmm
fi
/usr/bin/git -C baseline-published/source fetch --depth 1 origin "$pin"
/usr/bin/git -C baseline-published/source checkout --detach "$pin"
[[ "$(/usr/bin/git -C baseline-published/source rev-parse HEAD)" == "$pin" ]]
# Install the published wheels in an isolated target. Stock torch remains untouched.
/usr/bin/python3 -m pip install --upgrade --target baseline-published/python openmm==8.2.0 OpenMM-CUDA-12==8.2.0
export PYTHONPATH=baseline-published/python
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
/usr/bin/python3 - <<'DATA_PY'
from pathlib import Path
import hashlib, importlib.metadata, shutil
import openmm
from openmm import app
assert importlib.metadata.version('openmm') == '8.2.0'
assert importlib.metadata.version('OpenMM-CUDA-12') == '8.2.0'
source=Path('baseline-published/source')
checks = {
 '5dfr_solv-cube_equil.pdb': ('examples/5dfr_solv-cube_equil.pdb', 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf'),
 'amber99sb.xml': ('wrappers/python/openmm/app/data/amber99sb.xml', '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092'),
 'tip3p.xml': ('wrappers/python/openmm/app/data/tip3p.xml', '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c')}
for name,(rel,digest) in checks.items():
    content=(source/rel).read_bytes()
    if hashlib.sha256(content).hexdigest()!=digest:
        raise RuntimeError('Input checksum mismatch: '+name)
    shutil.copyfile(source/rel, Path('data')/name)
    if name.endswith('.xml'):
        bundled=Path(app.__file__).parent/'data'/name
        if hashlib.sha256(bundled.read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Installed force field mismatch: '+name)
pdb=app.PDBFile('data/5dfr_solv-cube_equil.pdb')
assert pdb.topology.getNumAtoms()==23558
assert 'CUDA' in [openmm.Platform.getPlatform(i).getName() for i in range(openmm.Platform.getNumPlatforms())]
DATA_PY
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
export CUDA_VISIBLE_DEVICES=0
/usr/bin/python3 -m openmm.testInstallation
