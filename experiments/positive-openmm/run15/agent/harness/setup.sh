#!/usr/bin/env bash
set -euo pipefail
mkdir -p out baseline-published data
exec > >(tee -a out/setup.log) 2>&1
# Only toolkit locations observed in the supplied probe are candidates.
cuda_root=''
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -x "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
        cuda_root="$root"
        break
    fi
done
if [[ -n "$cuda_root" ]]; then
    compiler="$cuda_root/bin/nvcc"
    includes="$cuda_root/include"
    libraries="$cuda_root/lib64"
elif [[ -x /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    compiler=/usr/bin/nvcc
    includes=/usr/include
    libraries=/usr/lib/x86_64-linux-gnu
else
    echo 'No complete probed CUDA toolkit or complete distro CUDA layout available.' >&2
    exit 1
fi
ls -l "$compiler" "$includes/cuda_runtime.h" "$libraries/libcudart.so"
{
    printf 'export OPENMM_CUDA_COMPILER=%q\n' "$compiler"
    printf 'export CUDA_INCLUDE_DIR=%q\n' "$includes"
    printf 'export CUDA_LIBRARY_DIR=%q\n' "$libraries"
    printf 'export CMAKE_CUDA_COMPILER=%q\n' "$compiler"
    if [[ -n "$cuda_root" ]]; then
        printf 'export CUDAToolkit_ROOT=%q\n' "$cuda_root"
    fi
    printf 'export PATH=%q:"$PATH"\n' "$(dirname "$compiler")"
    printf 'export LD_LIBRARY_PATH=%q${LD_LIBRARY_PATH:+:"$LD_LIBRARY_PATH"}\n' "$libraries"
    printf 'ls -l "$OPENMM_CUDA_COMPILER" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY_DIR/libcudart.so"\n'
} > baseline-published/cuda-env.sh
source baseline-published/cuda-env.sh
export CUDA_VISIBLE_DEVICES=0
command -v git
python3 -m pip --version
if [[ ! -d baseline-published/openmm/.git ]]; then
    git init baseline-published/openmm
    git -C baseline-published/openmm remote add origin https://github.com/openmm/openmm
fi
git -C baseline-published/openmm fetch --depth 1 origin 53770948682c40bd460b39830d4e0f0fd3a4b868
git -C baseline-published/openmm checkout --detach 53770948682c40bd460b39830d4e0f0fd3a4b868
test "$(git -C baseline-published/openmm rev-parse HEAD)" = 53770948682c40bd460b39830d4e0f0fd3a4b868
# Isolated target leaves stock Python packages, including torch, untouched.
python3 -m pip install --disable-pip-version-check --upgrade --target baseline-published/python openmm==8.2.0 OpenMM-CUDA-12==8.2.0
export PYTHONPATH="$PWD/baseline-published/python${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<'MATERIALIZE'
import hashlib, json, pathlib, shutil
baseline = pathlib.Path('baseline-published')
driver = '#!/usr/bin/env python3\n"""Fixed-work DHFR ensemble: independent replicas of the OpenMM 8.2.0 examples/benchmark.py `pme` system, run one after another."""\nimport argparse\nimport json\nimport time\n\nimport openmm as mm\nfrom openmm import app, unit\n\nparser = argparse.ArgumentParser()\nparser.add_argument(\'--replicas\', type=int, default=8)\nparser.add_argument(\'--steps\', type=int, default=25000)\nparser.add_argument(\'--seed0\', type=int, default=1000)\nparser.add_argument(\'--platform\', default=\'CUDA\')\nparser.add_argument(\'--out\', default=\'ensemble.json\')\nargs = parser.parse_args()\nassert args.replicas > 0 and args.steps > 0 and args.steps % 250 == 0\n\n# System exactly as benchmark.py builds `--test pme` with default options (hbonds, cutoff 0.9 nm).\npdb = app.PDBFile(\'5dfr_solv-cube_equil.pdb\')\nforcefield = app.ForceField(\'amber99sb.xml\', \'tip3p.xml\')\nsystem = forcefield.createSystem(pdb.topology, nonbondedMethod=app.PME, nonbondedCutoff=0.9,\n                                 constraints=app.HBonds, hydrogenMass=1.5 * unit.amu)\nplatform = mm.Platform.getPlatformByName(args.platform)\nproperties = {\'Precision\': \'single\', \'DeterministicForces\': \'true\'} if args.platform == \'CUDA\' else {}\n\nreplicas = []\nstart = time.perf_counter()\nfor index in range(args.replicas):\n    seed = args.seed0 + index\n    integrator = mm.LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond, 0.004 * unit.picoseconds)\n    integrator.setConstraintTolerance(1e-5)\n    integrator.setRandomNumberSeed(seed)\n    context = mm.Context(system, integrator, platform, properties)\n    context.setPositions(pdb.positions)\n    context.setVelocitiesToTemperature(300 * unit.kelvin, seed)\n    began = time.perf_counter()\n    energies = []\n    for _ in range(args.steps // 250):\n        integrator.step(250)\n        energies.append(context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))\n    replicas.append(dict(replica=index, seed=seed, steps=args.steps, wall_s=time.perf_counter() - began,\n                         final_potential_kj_mol=energies[-1], mean_potential_kj_mol=sum(energies) / len(energies)))\n    del context, integrator\ntotal = time.perf_counter() - start\n\nsimulated_ns = args.replicas * args.steps * 0.004 / 1000\nwith open(args.out, \'w\') as handle:\n    json.dump(dict(platform=args.platform, properties=properties, simulated_ns=simulated_ns,\n                   total_wall_s=total, replicas=replicas), handle, indent=1)\nprint(f\'total_wall_s: {total:.3f}\')\nprint(f\'aggregate_ns_per_day: {simulated_ns / total * 86400:.1f}\')\n'
(baseline / 'dhfr_ensemble.py').write_text(driver)
inputs = [{'name': '5dfr_solv-cube_equil.pdb', 'type': 'published input', 'required': True, 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 1814203, 'sha256': 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf', 'verification': 'Downloaded in memory during intake; SHA-256 computed; no workload run.', 'access_instructions': 'Public unauthenticated HTTPS. PDB must be in driver working directory; XML files ship in OpenMM package.', 'licence': {'status': 'permitted', 'source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'evidence': 'Repository-associated inputs distributed with OpenMM; supplied brief explicitly permits local running and modification. No separate file-specific licence identified.'}}, {'name': 'amber99sb.xml', 'type': 'published input', 'required': True, 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/amber99sb.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 467697, 'sha256': '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092', 'verification': 'Downloaded in memory during intake; SHA-256 computed; no workload run.', 'access_instructions': 'Public unauthenticated HTTPS. PDB must be in driver working directory; XML files ship in OpenMM package.', 'licence': {'status': 'permitted', 'source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'evidence': 'Repository-associated inputs distributed with OpenMM; supplied brief explicitly permits local running and modification. No separate file-specific licence identified.'}}, {'name': 'tip3p.xml', 'type': 'published input', 'required': True, 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/tip3p.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'bytes': 891, 'sha256': '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c', 'verification': 'Downloaded in memory during intake; SHA-256 computed; no workload run.', 'access_instructions': 'Public unauthenticated HTTPS. PDB must be in driver working directory; XML files ship in OpenMM package.', 'licence': {'status': 'permitted', 'source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'evidence': 'Repository-associated inputs distributed with OpenMM; supplied brief explicitly permits local running and modification. No separate file-specific licence identified.'}}]
for item in inputs:
    name = item['name']
    source = baseline / 'openmm' / ('examples' if name.endswith('.pdb') else 'wrappers/python/openmm/app/data') / name
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise RuntimeError('Input checksum mismatch: ' + name)
    pathlib.Path('data', name).write_bytes(raw)
# Confirm installed release and actual parsed model, without modifying source.
import importlib.metadata
import openmm
from openmm import app
for package in ('openmm', 'OpenMM-CUDA-12'):
    if importlib.metadata.version(package) != '8.2.0':
        raise RuntimeError('Wrong package version: ' + package)
pdb = app.PDBFile('data/5dfr_solv-cube_equil.pdb')
if pdb.topology.getNumAtoms() != 23558:
    raise RuntimeError('Wrong atom count')
print(json.dumps({'atoms':23558, 'replicas':8, 'steps_per_replica':25000, 'seed0':1000,
                  'gpu_count':1, 'CUDA_VISIBLE_DEVICES':'0', 'platform':'CUDA',
                  'properties':{'Precision':'single','DeterministicForces':'true'}}))
MATERIALIZE
nvidia-smi --query-gpu=name,uuid,driver_version --format=csv
python3 -m openmm.testInstallation
