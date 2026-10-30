#!/usr/bin/env bash
set -euo pipefail
mkdir -p baseline-published data out/setup
exec > >(tee -a out/setup/setup.log) 2>&1
# Select only layouts discovered by the stock-image probe.
cuda_root=''
for candidate in /usr/local/cuda /usr/lib/cuda; do
    if [[ -x "$candidate/bin/nvcc" && -f "$candidate/include/cuda_runtime.h" && -f "$candidate/lib64/libcudart.so" ]]; then
        cuda_root="$candidate"
        break
    fi
done
if [[ -n "$cuda_root" ]]; then
    cuda_compiler="$cuda_root/bin/nvcc"
    cuda_include="$cuda_root/include"
    cuda_library="$cuda_root/lib64"
elif [[ -x /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    cuda_compiler=/usr/bin/nvcc
    cuda_include=/usr/include
    cuda_library=/usr/lib/x86_64-linux-gnu
else
    echo 'No complete probed CUDA toolkit layout found' >&2
    exit 1
fi
ls "$cuda_compiler" "$cuda_include/cuda_runtime.h" "$cuda_library/libcudart.so"
{
    printf 'export CMAKE_CUDA_COMPILER=%q\n' "$cuda_compiler"
    printf 'export CUDA_INCLUDE_DIR=%q\n' "$cuda_include"
    printf 'export CUDA_LIBRARY_DIR=%q\n' "$cuda_library"
    if [[ -n "$cuda_root" ]]; then
        printf 'export CUDAToolkit_ROOT=%q\n' "$cuda_root"
    fi
    printf 'export PATH=%q:/usr/bin:/bin\n' "$(dirname "$cuda_compiler")"
    printf 'export LD_LIBRARY_PATH=%q\n' "$cuda_library"
    printf '%s\n' 'ls "$CMAKE_CUDA_COMPILER" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"'
} > baseline-published/cuda-env.sh
source baseline-published/cuda-env.sh
pin=53770948682c40bd460b39830d4e0f0fd3a4b868
if [[ ! -d baseline-published/source/.git ]]; then
    git init baseline-published/source
    git -C baseline-published/source remote add origin https://github.com/openmm/openmm.git
fi
git -C baseline-published/source fetch --depth 1 origin "$pin"
git -C baseline-published/source checkout --detach "$pin"
[[ "$(git -C baseline-published/source rev-parse HEAD)" == "$pin" ]]
# Isolated package directory: stock Python packages, including torch, stay intact.
if ! PYTHONPATH="$PWD/baseline-published/python" /usr/bin/python3 - <<'CHECK'
import importlib.metadata as m
installed = {d.metadata['Name'].lower(): d.version for d in m.distributions(path=['baseline-published/python'])}
assert installed.get('openmm') == '8.2.0'
assert installed.get('openmm-cuda-12') == '8.2.0'
CHECK
then
    PIP_CACHE_DIR="$PWD/out/setup/pip-cache" /usr/bin/python3 -m pip install --target baseline-published/python --upgrade openmm==8.2.0 OpenMM-CUDA-12==8.2.0
fi
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
/usr/bin/python3 - <<'INPUTS'
import hashlib, pathlib, urllib.request
inputs = [{'name': '5dfr_solv-cube_equil.pdb', 'kind': 'published input', 'required': True, 'availability': 'available', 'source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 1814203, 'sha256': 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf', 'verification': 'HTTP retrieval and SHA-256 computed during intake; no workload run.', 'access_instructions': 'Public HTTPS, no credentials. Place PDB in driver working directory; force fields ship in openmm package.', 'licence': None, 'licence_reason': 'No separate per-input licence identified; see benchmark.json intended-use permission evidence.'}, {'name': 'amber99sb.xml', 'kind': 'published input', 'required': True, 'availability': 'available', 'source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/amber99sb.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 467697, 'sha256': '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092', 'verification': 'HTTP retrieval and SHA-256 computed during intake; no workload run.', 'access_instructions': 'Public HTTPS, no credentials. Place PDB in driver working directory; force fields ship in openmm package.', 'licence': None, 'licence_reason': 'No separate per-input licence identified; see benchmark.json intended-use permission evidence.'}, {'name': 'tip3p.xml', 'kind': 'published input', 'required': True, 'availability': 'available', 'source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/tip3p.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 891, 'sha256': '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c', 'verification': 'HTTP retrieval and SHA-256 computed during intake; no workload run.', 'access_instructions': 'Public HTTPS, no credentials. Place PDB in driver working directory; force fields ship in openmm package.', 'licence': None, 'licence_reason': 'No separate per-input licence identified; see benchmark.json intended-use permission evidence.'}]
for item in inputs:
    target = pathlib.Path('data') / item['name']
    if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != item['sha256']:
        with urllib.request.urlopen(item['source'], timeout=120) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != item['sha256']:
            raise RuntimeError('Input checksum mismatch: '+item['name'])
        target.write_bytes(content)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == item['sha256']
INPUTS
export PYTHONPATH="$PWD/baseline-published/python"
export CUDA_VISIBLE_DEVICES=0
/usr/bin/python3 -m openmm.testInstallation
/usr/bin/python3 - <<'CHECK'
import openmm as mm
from openmm import app
import hashlib, pathlib
import importlib.metadata
assert importlib.metadata.version('openmm') == '8.2.0'
assert mm.Platform.getPlatformByName('CUDA') is not None
assert app.PDBFile('data/5dfr_solv-cube_equil.pdb').topology.getNumAtoms() == 23558
for name in ('amber99sb.xml', 'tip3p.xml'):
    bundled = pathlib.Path(app.__file__).parent/'data'/name
    assert hashlib.sha256(bundled.read_bytes()).digest() == hashlib.sha256((pathlib.Path('data')/name).read_bytes()).digest()
CHECK
