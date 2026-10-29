#!/usr/bin/env bash
set -euo pipefail
mkdir -p out data baseline-published
exec > >(tee -a out/setup.log) 2>&1
# Select only toolkit layouts discovered by the supplied box probe.
if [[ -f /usr/local/cuda/bin/nvcc && -f /usr/local/cuda/include/cuda_runtime.h && -f /usr/local/cuda/lib64/libcudart.so ]]; then
    cuda_bin=/usr/local/cuda/bin
    cuda_include=/usr/local/cuda/include
    cuda_lib=/usr/local/cuda/lib64
elif [[ -f /usr/lib/cuda/bin/nvcc && -f /usr/lib/cuda/include/cuda_runtime.h && -f /usr/lib/cuda/lib64/libcudart.so ]]; then
    cuda_bin=/usr/lib/cuda/bin
    cuda_include=/usr/lib/cuda/include
    cuda_lib=/usr/lib/cuda/lib64
elif [[ -f /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    cuda_bin=/usr/bin
    cuda_include=/usr/include
    cuda_lib=/usr/lib/x86_64-linux-gnu
else
    echo 'No complete CUDA toolkit in probe-discovered layouts' >&2
    exit 1
fi
ls "$cuda_bin/nvcc" "$cuda_include/cuda_runtime.h" "$cuda_lib/libcudart.so"
cat > data/toolkit.env <<EOF
export OPENMM_CUDA_COMPILER=$cuda_bin/nvcc
export PATH=$cuda_bin:\$PATH
export CPATH=$cuda_include\${CPATH:+:\$CPATH}
export LD_LIBRARY_PATH=$cuda_lib\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}
EOF
if [[ "$cuda_bin" != /usr/bin ]]; then
    printf 'export CUDAToolkit_ROOT=%s\n' "${cuda_bin%/bin}" >> data/toolkit.env
fi
source data/toolkit.env
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export PYTHONNOUSERSITE=1
export CUDA_CACHE_PATH="$PWD/out/cuda-cache"
mkdir -p "$CUDA_CACHE_PATH"
for tool in /usr/bin/git /usr/bin/python3; do
    [[ -x "$tool" ]] || { echo "Missing required tool: $tool; probe lists no suitable apt repository" >&2; exit 1; }
done
pin=53770948682c40bd460b39830d4e0f0fd3a4b868
if [[ ! -d baseline-published/.git ]]; then
    /usr/bin/git -C baseline-published init
    /usr/bin/git -C baseline-published remote add origin https://github.com/openmm/openmm
fi
if ! /usr/bin/git -C baseline-published cat-file -e "$pin^{commit}"; then
    /usr/bin/git -C baseline-published fetch --depth 1 origin "$pin"
fi
/usr/bin/git -C baseline-published checkout --detach "$pin"
[[ "$(/usr/bin/git -C baseline-published rev-parse HEAD)" == "$pin" ]]
# Isolated install preserves stock Python packages, including torch.
if [[ ! -x baseline-published/.venv/bin/python3 ]]; then
    /usr/bin/python3 -m venv --system-site-packages --without-pip baseline-published/.venv
fi
baseline-published/.venv/bin/python3 -m pip install openmm==8.2.0 OpenMM-CUDA-12==8.2.0
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
import hashlib
import pathlib
import urllib.request
p = pathlib.Path('data/5dfr_solv-cube_equil.pdb')
expected = 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf'
if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
    url = 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb'
    content = urllib.request.urlopen(url, timeout=120).read()
    if hashlib.sha256(content).hexdigest() != expected:
        raise RuntimeError('Published PDB SHA256 mismatch')
    p.write_bytes(content)
INPUTS
baseline-published/.venv/bin/python3 - <<'CHECK'
import importlib.metadata
import hashlib
from pathlib import Path
import openmm
from openmm import app
for name in ('openmm', 'OpenMM-CUDA-12'):
    if importlib.metadata.version(name) != '8.2.0':
        raise RuntimeError(f'Wrong version: {name}')
root = Path(app.__file__).parent / 'data'
for name, expected in [('amber99sb.xml', '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092'), ('tip3p.xml', '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c')]:
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
        raise RuntimeError(f'Packaged force field hash mismatch: {name}')
if app.PDBFile('data/5dfr_solv-cube_equil.pdb').topology.getNumAtoms() != 23558:
    raise RuntimeError('Wrong atom count')
CHECK
baseline-published/.venv/bin/python3 -m openmm.testInstallation
