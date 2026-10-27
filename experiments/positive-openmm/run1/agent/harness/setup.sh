#!/usr/bin/env bash
set -euo pipefail
mkdir -p out baseline-published data
exec > >(tee -a out/setup.log) 2>&1
# Select only toolkit locations discovered by the box probe.
nvcc='' inc='' lib='' root=''
for candidate in /usr/local/cuda /usr/lib/cuda; do
    if [[ -f "$candidate/bin/nvcc" && -f "$candidate/include/cuda_runtime.h" && -f "$candidate/lib64/libcudart.so" ]]; then
        root="$candidate"; nvcc="$root/bin/nvcc"; inc="$root/include"; lib="$root/lib64"; break
    fi
done
if [[ -z "$nvcc" && -f /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
    nvcc=/usr/bin/nvcc; inc=/usr/include; lib=/usr/lib/x86_64-linux-gnu
fi
[[ -n "$nvcc" ]] || { echo 'No complete probed CUDA toolkit or distro CUDA layout' >&2; exit 1; }
ls -l "$nvcc" "$inc/cuda_runtime.h" "$lib/libcudart.so"
"$nvcc" --version
command -v python3 >/dev/null || { echo 'Required python3 missing' >&2; exit 1; }
python3 -m pip --version || { echo 'Required pip missing; no enabled Ubuntu apt source in probe supplies it' >&2; exit 1; }
{
    printf 'export OPENMM_CUDA_COMPILER=%q\n' "$nvcc"
    printf 'export CUDA_INCLUDE_DIR=%q\n' "$inc"
    printf 'export CUDA_LIBRARY_DIR=%q\n' "$lib"
    printf 'export PATH=%q:"$PATH"\n' "$(dirname "$nvcc")"
    printf 'export LD_LIBRARY_PATH=%q${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}\n' "$lib"
    if [[ -n "$root" ]]; then printf 'export CUDAToolkit_ROOT=%q\n' "$root"; fi
} > baseline-published/cuda.env
source baseline-published/cuda.env
# Isolated target leaves stock Python packages, including torch, untouched.
python3 -m pip install --upgrade --target baseline-published/python openmm==8.2.0 OpenMM-CUDA-12==8.2.0
export PYTHONPATH="$PWD/baseline-published/python"
export PYTHONNOUSERSITE=1
export CUDA_VISIBLE_DEVICES=0
unset CUDA_MPS_ACTIVE_THREAD_PERCENTAGE CUDA_MPS_PIPE_DIRECTORY CUDA_MPS_LOG_DIRECTORY
python3 - <<'PY'
import hashlib, importlib.metadata, json, pathlib, urllib.request
pin = '53770948682c40bd460b39830d4e0f0fd3a4b868'
base = 'https://raw.githubusercontent.com/openmm/openmm/' + pin + '/'
files = {
 '5dfr_solv-cube_equil.pdb': ('examples/', 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf'),
 'amber99sb.xml': ('wrappers/python/openmm/app/data/', '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092'),
 'tip3p.xml': ('wrappers/python/openmm/app/data/', '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c')}
for name, (directory, digest) in files.items():
    path = pathlib.Path('data') / name
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        with urllib.request.urlopen(base + directory + name, timeout=90) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != digest:
            raise RuntimeError('Input checksum mismatch: ' + name)
        path.write_bytes(content)
for package in ('openmm', 'OpenMM-CUDA-12'):
    if importlib.metadata.version(package) != '8.2.0':
        raise RuntimeError('Incorrect package version: ' + package)
# Preserve the published source tree at its exact immutable pin, separate from wheels.
import tarfile, tempfile
with tempfile.TemporaryFile() as archive:
    with urllib.request.urlopen('https://api.github.com/repos/openmm/openmm/tarball/' + pin, timeout=90) as response:
        import shutil
        shutil.copyfileobj(response, archive)
    archive.seek(0)
    with tarfile.open(fileobj=archive, mode='r:gz') as tar:
        destination = pathlib.Path('baseline-published/upstream')
        destination.mkdir(exist_ok=True)
        members = tar.getmembers()
        archive_root = pathlib.PurePosixPath(members[0].name).parts[0]
        destination_root = destination.resolve()
        links = []
        for member in members:
            original = pathlib.PurePosixPath(member.name)
            if original.is_absolute() or original.parts[0] != archive_root:
                raise RuntimeError('Unsafe upstream archive member: ' + member.name)
            parts = original.parts[1:]
            if not parts:
                continue
            if '..' in parts:
                raise RuntimeError('Unsafe upstream archive member: ' + member.name)
            member.name = str(pathlib.PurePosixPath(*parts))
            target = destination / member.name
            if not target.resolve().is_relative_to(destination_root):
                raise RuntimeError('Upstream archive path escapes destination: ' + member.name)
            if member.issym() or member.islnk():
                link = pathlib.PurePosixPath(member.linkname)
                if link.is_absolute():
                    raise RuntimeError('Absolute upstream archive link: ' + member.name)
                if member.islnk():
                    if not link.parts or link.parts[0] != archive_root or '..' in link.parts:
                        raise RuntimeError('Unsafe upstream archive hard link: ' + member.name)
                    member.linkname = str(pathlib.PurePosixPath(*link.parts[1:]))
                    source = destination / member.linkname
                else:
                    source = target.parent / member.linkname
                if not source.resolve().is_relative_to(destination_root):
                    raise RuntimeError('Upstream archive link escapes destination: ' + member.name)
                links.append(member)
                continue
            if not (member.isdir() or member.isfile()):
                raise RuntimeError('Unsupported upstream archive member: ' + member.name)
            tar.extract(member, destination)
        # Install links after files, so archive links cannot redirect file writes.
        for member in links:
            target = destination / member.name
            source = (target.parent / member.linkname if member.issym()
                      else destination / member.linkname)
            if (not target.resolve().is_relative_to(destination_root)
                    or not source.resolve().is_relative_to(destination_root)):
                raise RuntimeError('Upstream archive link escapes destination: ' + member.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_symlink() or target.is_file():
                target.unlink()
            if member.issym():
                target.symlink_to(member.linkname)
            else:
                import os
                os.link(source, target)
pathlib.Path('baseline-published/PIN.json').write_text(json.dumps({'repo':'https://github.com/openmm/openmm','commit':pin,'openmm':'8.2.0','OpenMM-CUDA-12':'8.2.0'}, indent=2))
PY
cat > baseline-published/dhfr_ensemble.py <<'PY'
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
PY
python3 -m openmm.testInstallation
