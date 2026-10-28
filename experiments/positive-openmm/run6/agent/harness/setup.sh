#!/usr/bin/env bash
set -euo pipefail
mkdir -p out/setup baseline-published data
exec > >(tee -a out/setup/setup.log) 2>&1
# Only toolkit locations discovered by the supplied probe are candidates.
CUDA_ROOT=
for candidate in /usr/local/cuda /usr/lib/cuda; do
    if [[ -x "$candidate/bin/nvcc" && -f "$candidate/include/cuda_runtime.h" && -f "$candidate/lib64/libcudart.so" ]]; then
        CUDA_ROOT="$candidate"
        break
    fi
done
if [[ -n "$CUDA_ROOT" ]]; then
    CUDA_COMPILER="$CUDA_ROOT/bin/nvcc"
    CUDA_INCLUDE_DIR="$CUDA_ROOT/include"
    CUDA_LIBRARY_DIR="$CUDA_ROOT/lib64"
    ls "$CUDA_COMPILER" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
else
    CUDA_COMPILER=/usr/bin/nvcc
    CUDA_INCLUDE_DIR=/usr/include
    CUDA_LIBRARY_DIR=/usr/lib/x86_64-linux-gnu
    ls "$CUDA_COMPILER" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so" || {
        echo 'No complete probed CUDA toolkit or complete distro CUDA layout.' >&2; exit 1;
    }
fi
{
    printf 'export CUDA_COMPILER=%q\n' "$CUDA_COMPILER"
    printf 'export OPENMM_CUDA_COMPILER=%q\n' "$CUDA_COMPILER"
    printf 'export CUDA_INCLUDE_DIR=%q\n' "$CUDA_INCLUDE_DIR"
    printf 'export CUDA_LIBRARY_DIR=%q\n' "$CUDA_LIBRARY_DIR"
    printf 'export PATH=%q\n' "$(dirname "$CUDA_COMPILER"):/usr/bin:/bin"
    printf 'export LD_LIBRARY_PATH=%q\n' "$CUDA_LIBRARY_DIR"
    printf 'export CPATH=%q\n' "$CUDA_INCLUDE_DIR"
    printf 'export LIBRARY_PATH=%q\n' "$CUDA_LIBRARY_DIR"
    if [[ -n "$CUDA_ROOT" ]]; then printf 'export CUDAToolkit_ROOT=%q\n' "$CUDA_ROOT"; fi
} > baseline-published/runtime.env
source baseline-published/runtime.env
export CUDA_VISIBLE_DEVICES=0 OPENMM_CPU_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
/usr/bin/python3 -m pip --version
# Isolated target leaves stock torch and system Python packages untouched.
/usr/bin/python3 -m pip install --disable-pip-version-check --target baseline-published/python --upgrade openmm==8.2.0 OpenMM-CUDA-12==8.2.0
if [[ ! -d baseline-published/upstream/.git ]]; then
    git init baseline-published/upstream
    git -C baseline-published/upstream remote add origin https://github.com/openmm/openmm
fi
git -C baseline-published/upstream fetch --depth 1 origin 53770948682c40bd460b39830d4e0f0fd3a4b868
git -C baseline-published/upstream checkout --detach 53770948682c40bd460b39830d4e0f0fd3a4b868
[[ "$(git -C baseline-published/upstream rev-parse HEAD)" == 53770948682c40bd460b39830d4e0f0fd3a4b868 ]]
/usr/bin/python3 - <<'INPUTS'
import hashlib, pathlib, urllib.request
items = [{'name': '5dfr_solv-cube_equil.pdb', 'source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 1814203, 'sha256': 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf', 'availability': 'available', 'evidence': 'HTTPS retrieval succeeded; byte count and SHA-256 computed during intake.', 'licence_source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'access': 'Public; no login required.'}, {'name': 'amber99sb.xml', 'source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/amber99sb.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 467697, 'sha256': '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092', 'availability': 'available', 'evidence': 'HTTPS retrieval succeeded; byte count and SHA-256 computed during intake.', 'licence_source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'access': 'Public; no login required.'}, {'name': 'tip3p.xml', 'source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/tip3p.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 891, 'sha256': '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c', 'availability': 'available', 'evidence': 'HTTPS retrieval succeeded; byte count and SHA-256 computed during intake.', 'licence_source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'access': 'Public; no login required.'}]
for item in items:
    path = pathlib.Path('data') / item['name']
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        content = urllib.request.urlopen(item['source'], timeout=120).read()
        if hashlib.sha256(content).hexdigest() != item['sha256']:
            raise RuntimeError('Input checksum mismatch: '+item['name'])
        path.write_bytes(content)
    if path.stat().st_size != item['bytes']:
        raise RuntimeError('Input byte count mismatch: '+item['name'])
INPUTS
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
cat > baseline-published/anchors.json <<'ANCHORS'
[
  {
    "id": "nvidia2025-dhfr-eight-tuned-throughput-reference",
    "quantity": "Approximate aggregate DHFR throughput for eight concurrent MPS simulations with tuned active thread percentage, single H100 or L40S GPU (ns/day)",
    "source": "Hsu, Clark and Paulsen, NVIDIA Technical Blog, 2025-06-04, https://developer.nvidia.com/blog/maximizing-openmm-molecular-dynamics-throughput-with-nvidia-multi-process-service/ ; tuned DHFR discussion and Figure 4; also quoted in brief.md.",
    "published_value": 5000.0,
    "comparison": "==",
    "tolerance": null,
    "uncertainty": null,
    "role": "reference",
    "notes": "Approximate observation: approaches 5 microseconds/day, converted to ns/day. No published acceptance tolerance. Fixed-time upstream benchmark; not an absolute target for the fixed-work ensemble. No energy acceptance criterion published."
  }
]
ANCHORS
PYTHONPATH=baseline-published/python /usr/bin/python3 - <<'CHECK'
import importlib.metadata, openmm
from openmm import app
import pathlib, hashlib
for name in ('openmm', 'OpenMM-CUDA-12'):
    assert importlib.metadata.version(name) == '8.2.0', name
assert app.PDBFile('data/5dfr_solv-cube_equil.pdb').topology.getNumAtoms() == 23558
for name in ('amber99sb.xml', 'tip3p.xml'):
    installed = pathlib.Path(app.__file__).parent / 'data' / name
    assert hashlib.sha256(installed.read_bytes()).digest() == hashlib.sha256((pathlib.Path('data')/name).read_bytes()).digest(), name
print('Pinned OpenMM packages, input atoms and force fields checked.')
CHECK
PYTHONPATH=baseline-published/python /usr/bin/python3 -m openmm.testInstallation
