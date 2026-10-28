#!/usr/bin/env bash
set -euo pipefail
mkdir -p out baseline-published data
exec > >(tee -a out/setup.log) 2>&1
# Select only layouts discovered by the supplied box probe.
selected=''
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -f "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
        selected="$root"
        break
    fi
done
if [[ -n "$selected" ]]; then
    compiler="$selected/bin/nvcc"; include="$selected/include"; library="$selected/lib64"
else
    compiler=/usr/bin/nvcc; include=/usr/include; library=/usr/lib/x86_64-linux-gnu
fi
ls "$compiler" "$include/cuda_runtime.h" "$library/libcudart.so"
if [[ -f baseline-published/toolkit.env ]]; then
    old_compiler=$(bash -c 'source baseline-published/toolkit.env; printf "%s" "$CUDACXX"')
    [[ "$old_compiler" == "$compiler" ]] || { echo 'Selected CUDA layout changed on retry' >&2; exit 1; }
fi
{
    printf 'export CUDACXX=%q\n' "$compiler"
    printf 'export OPENMM_CUDA_COMPILER=%q\n' "$compiler"
    printf 'export CUDA_INCLUDE_DIRS=%q\n' "$include"
    printf 'export CUDA_LIBRARY_DIR=%q\n' "$library"
    printf 'export PATH=%q:"$PATH"\n' "$(dirname "$compiler")"
    printf 'export LD_LIBRARY_PATH=%q${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}\n' "$library"
    if [[ -n "$selected" ]]; then
        printf 'export CUDAToolkit_ROOT=%q\n' "$selected"
    fi
} > baseline-published/toolkit.env
source baseline-published/toolkit.env
export CUDA_VISIBLE_DEVICES=0
export PYTHONDONTWRITEBYTECODE=1
command -v git
python3 -m pip --version
if [[ ! -d baseline-published/source/.git ]]; then
    git init baseline-published/source
    git -C baseline-published/source remote add origin https://github.com/openmm/openmm
fi
git -C baseline-published/source fetch --depth 1 origin 53770948682c40bd460b39830d4e0f0fd3a4b868
git -C baseline-published/source checkout --detach 53770948682c40bd460b39830d4e0f0fd3a4b868
[[ "$(git -C baseline-published/source rev-parse HEAD)" == 53770948682c40bd460b39830d4e0f0fd3a4b868 ]]
# Isolated installation leaves stock torch and its dependencies untouched.
python3 -m venv --system-site-packages --without-pip baseline-published/venv
baseline-published/venv/bin/python3 -m pip install --ignore-installed openmm==8.2.0 OpenMM-CUDA-12==8.2.0
python3 - <<'INSTALL_INPUTS'
import hashlib, json, pathlib, urllib.request
DRIVER = '#!/usr/bin/env python3\n"""Fixed-work DHFR ensemble: independent replicas of the OpenMM 8.2.0 examples/benchmark.py `pme` system, run one after another."""\nimport argparse\nimport json\nimport time\n\nimport openmm as mm\nfrom openmm import app, unit\n\nparser = argparse.ArgumentParser()\nparser.add_argument(\'--replicas\', type=int, default=8)\nparser.add_argument(\'--steps\', type=int, default=25000)\nparser.add_argument(\'--seed0\', type=int, default=1000)\nparser.add_argument(\'--platform\', default=\'CUDA\')\nparser.add_argument(\'--out\', default=\'ensemble.json\')\nargs = parser.parse_args()\nassert args.replicas > 0 and args.steps > 0 and args.steps % 250 == 0\n\n# System exactly as benchmark.py builds `--test pme` with default options (hbonds, cutoff 0.9 nm).\npdb = app.PDBFile(\'5dfr_solv-cube_equil.pdb\')\nforcefield = app.ForceField(\'amber99sb.xml\', \'tip3p.xml\')\nsystem = forcefield.createSystem(pdb.topology, nonbondedMethod=app.PME, nonbondedCutoff=0.9,\n                                 constraints=app.HBonds, hydrogenMass=1.5 * unit.amu)\nplatform = mm.Platform.getPlatformByName(args.platform)\nproperties = {\'Precision\': \'single\', \'DeterministicForces\': \'true\'} if args.platform == \'CUDA\' else {}\n\nreplicas = []\nstart = time.perf_counter()\nfor index in range(args.replicas):\n    seed = args.seed0 + index\n    integrator = mm.LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond, 0.004 * unit.picoseconds)\n    integrator.setConstraintTolerance(1e-5)\n    integrator.setRandomNumberSeed(seed)\n    context = mm.Context(system, integrator, platform, properties)\n    context.setPositions(pdb.positions)\n    context.setVelocitiesToTemperature(300 * unit.kelvin, seed)\n    began = time.perf_counter()\n    energies = []\n    for _ in range(args.steps // 250):\n        integrator.step(250)\n        energies.append(context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))\n    replicas.append(dict(replica=index, seed=seed, steps=args.steps, wall_s=time.perf_counter() - began,\n                         final_potential_kj_mol=energies[-1], mean_potential_kj_mol=sum(energies) / len(energies)))\n    del context, integrator\ntotal = time.perf_counter() - start\n\nsimulated_ns = args.replicas * args.steps * 0.004 / 1000\nwith open(args.out, \'w\') as handle:\n    json.dump(dict(platform=args.platform, properties=properties, simulated_ns=simulated_ns,\n                   total_wall_s=total, replicas=replicas), handle, indent=1)\nprint(f\'total_wall_s: {total:.3f}\')\nprint(f\'aggregate_ns_per_day: {simulated_ns / total * 86400:.1f}\')\n'
INPUTS = [{'name': '5dfr_solv-cube_equil.pdb', 'kind': 'published_coordinates_and_topology', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb', 'availability': 'available', 'access': 'Public HTTPS GET, no authentication; place in driver working directory.', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'sha256': 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf', 'bytes': 1814203, 'atoms': 23558, 'verification': 'Retrieved bytes hash matches brief.', 'licence': 'Distributed in OpenMM repository; local running permitted according to brief; separate file licence not established.'}, {'name': 'amber99sb.xml', 'kind': 'published_force_field', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/amber99sb.xml', 'availability': 'available', 'access': 'Ships in openmm 8.2.0 package; pinned source also publicly retrieved.', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'sha256': '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092', 'bytes': 467697, 'licence': 'Distributed in OpenMM; see repository licences and brief.'}, {'name': 'tip3p.xml', 'kind': 'published_force_field', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/tip3p.xml', 'availability': 'available', 'access': 'Ships in openmm 8.2.0 package; pinned source also publicly retrieved.', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'sha256': '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c', 'bytes': 891, 'licence': 'Distributed in OpenMM; see repository licences and brief.'}]
pathlib.Path('baseline-published/dhfr_ensemble.py').write_text(DRIVER)
for item in INPUTS:
    path = pathlib.Path('data') / item['name']
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        with urllib.request.urlopen(item['url'], timeout=90) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != item['sha256']:
            raise RuntimeError('Input checksum mismatch: ' + item['name'])
        path.write_bytes(content)
INSTALL_INPUTS
baseline-published/venv/bin/python3 - <<'CHECK'
import importlib.metadata, pathlib, hashlib
import openmm
for name in ('openmm', 'OpenMM-CUDA-12'):
    assert importlib.metadata.version(name) == '8.2.0', name
from openmm import app
for name in ('amber99sb.xml', 'tip3p.xml'):
    packaged = pathlib.Path(app.__file__).parent / 'data' / name
    assert hashlib.sha256(packaged.read_bytes()).digest() == hashlib.sha256((pathlib.Path('data') / name).read_bytes()).digest()
assert app.PDBFile('data/5dfr_solv-cube_equil.pdb').topology.getNumAtoms() == 23558
assert 'CUDA' in [openmm.Platform.getPlatform(i).getName() for i in range(openmm.Platform.getNumPlatforms())]
CHECK
baseline-published/venv/bin/python3 -m openmm.testInstallation
