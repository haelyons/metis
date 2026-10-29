#!/usr/bin/env bash
set -euo pipefail
mkdir -p baseline-published data out/setup
exec > >(tee -a out/setup/setup.log) 2>&1
# Only toolkit locations discovered by the supplied probe are candidates.
cuda_root=''
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -f "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
        cuda_root="$root"
        break
    fi
done
if [[ -n "$cuda_root" ]]; then
    ls "$cuda_root/bin/nvcc" "$cuda_root/include/cuda_runtime.h" "$cuda_root/lib64/libcudart.so"
    cat > baseline-published/cuda-env.sh <<EOF
export CUDAToolkit_ROOT='$cuda_root'
export CMAKE_CUDA_COMPILER='$cuda_root/bin/nvcc'
export CUDACXX='$cuda_root/bin/nvcc'
export OPENMM_CUDA_COMPILER='$cuda_root/bin/nvcc'
export CUDA_INCLUDE_DIR='$cuda_root/include'
export CUDA_LIBRARY_DIR='$cuda_root/lib64'
export PATH='$cuda_root/bin':\$PATH
export LD_LIBRARY_PATH='$cuda_root/lib64'\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}
EOF
elif [[ -f /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    ls /usr/bin/nvcc /usr/include/cuda_runtime.h /usr/lib/x86_64-linux-gnu/libcudart.so
    cat > baseline-published/cuda-env.sh <<'EOF'
export CMAKE_CUDA_COMPILER=/usr/bin/nvcc
export CUDACXX=/usr/bin/nvcc
export OPENMM_CUDA_COMPILER=/usr/bin/nvcc
export CUDA_INCLUDE_DIR=/usr/include
export CUDA_LIBRARY_DIR=/usr/lib/x86_64-linux-gnu
export PATH=/usr/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
EOF
else
    echo 'No complete probed CUDA toolkit or complete distro CUDA layout available.' >&2
    exit 1
fi
source baseline-published/cuda-env.sh
ls "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"
command -v git >/dev/null || { echo 'Required git missing; supplied apt source does not supply Ubuntu tools.' >&2; exit 1; }
/usr/bin/python3 -m pip --version
if [[ ! -d baseline-published/source/.git ]]; then
    git init baseline-published/source
    git -C baseline-published/source remote add origin https://github.com/openmm/openmm
fi
git -C baseline-published/source fetch --depth 1 origin 53770948682c40bd460b39830d4e0f0fd3a4b868
git -C baseline-published/source checkout --detach 53770948682c40bd460b39830d4e0f0fd3a4b868
test "$(git -C baseline-published/source rev-parse HEAD)" = 53770948682c40bd460b39830d4e0f0fd3a4b868
/usr/bin/python3 -m venv --system-site-packages --without-pip baseline-published/venv
baseline-published/venv/bin/python3 -m pip install openmm==8.2.0 OpenMM-CUDA-12==8.2.0
cp baseline-published/source/examples/5dfr_solv-cube_equil.pdb data/5dfr_solv-cube_equil.pdb
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
baseline-published/venv/bin/python3 - <<'CHECK'
import hashlib, importlib.metadata as m
from pathlib import Path
from openmm import app
assert m.version('openmm') == '8.2.0'
assert m.version('OpenMM-CUDA-12') == '8.2.0'
p = Path('data/5dfr_solv-cube_equil.pdb')
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf'
assert app.PDBFile(str(p)).topology.getNumAtoms() == 23558
for name, digest in [('amber99sb.xml', '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092'), ('tip3p.xml', '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c')]:
    p = Path(app.__file__).parent/'data'/name
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
CHECK
export CUDA_VISIBLE_DEVICES=0
baseline-published/venv/bin/python3 -m openmm.testInstallation
