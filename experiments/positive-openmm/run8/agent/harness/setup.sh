#!/usr/bin/env bash
set -euo pipefail
mkdir -p out baseline-published data
log=$(mktemp out/setup.XXXXXXXX.log)
exec > >(tee "$log") 2>&1
# Select only toolkit locations discovered in the box probe.
CUDA_NVCC= CUDA_INCLUDE= CUDA_LIBRARY= CUDA_BIN=
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -f "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
        CUDA_NVCC="$root/bin/nvcc"
        CUDA_INCLUDE="$root/include"
        CUDA_LIBRARY="$root/lib64/libcudart.so"
        CUDA_BIN="$root/bin"
        break
    fi
done
if [[ -z "$CUDA_NVCC" ]]; then
    CUDA_NVCC=/usr/bin/nvcc
    CUDA_INCLUDE=/usr/include
    CUDA_LIBRARY=/usr/lib/x86_64-linux-gnu/libcudart.so
    CUDA_BIN=/usr/bin
fi
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY"
"$CUDA_NVCC" --version
# Wheels are the published build; no CMake compilation is required.
# Installation is isolated, leaving stock Python packages (including torch) intact.
python3 -m pip install --upgrade --target baseline-published/python openmm==8.2.0 OpenMM-CUDA-12==8.2.0
python3 - "$CUDA_NVCC" "$CUDA_INCLUDE" "$CUDA_LIBRARY" "$CUDA_BIN" <<'CUDA_ENV'
import pathlib, shlex, sys
keys = ('CUDA_NVCC', 'CUDA_INCLUDE', 'CUDA_LIBRARY', 'CUDA_BIN')
pathlib.Path('baseline-published/cuda-env.sh').write_text(''.join(
    'export '+key+'='+shlex.quote(value)+'\n' for key,value in zip(keys,sys.argv[1:])))
CUDA_ENV
source baseline-published/cuda-env.sh
export PATH="$CUDA_BIN:$PATH"
export PYTHONPATH="$PWD/baseline-published/python"
export CUDA_VISIBLE_DEVICES=0
export GPU_COUNT=1
export CUDACXX="$CUDA_NVCC"
export OPENMM_CUDA_COMPILER="$CUDA_NVCC"
export CPATH="$CUDA_INCLUDE${CPATH:+:$CPATH}"
export LD_LIBRARY_PATH="${CUDA_LIBRARY%/*}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python3 - <<'FETCH'
import hashlib, pathlib, urllib.request, tarfile
pin='53770948682c40bd460b39830d4e0f0fd3a4b868'
archive=pathlib.Path('baseline-published/upstream.tar.gz')
if not pathlib.Path('baseline-published/upstream').exists():
    urllib.request.urlretrieve('https://codeload.github.com/openmm/openmm/tar.gz/'+pin, archive)
    with tarfile.open(archive) as tf:
        tf.extractall('baseline-published')
    pathlib.Path('baseline-published/openmm-'+pin).rename('baseline-published/upstream')
files=[{'name': '5dfr_solv-cube_equil.pdb', 'required': True, 'kind': 'published input', 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'sha256': 'fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf', 'bytes': 1814203, 'verification': 'Fetched successfully and hashed during intake; not persisted as workload input.', 'access_instructions': 'Download pinned raw URL; place PDB beside driver. Force-field XML files ship inside the pinned OpenMM package.', 'licence_source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'separate_input_licence': None, 'separate_input_licence_reason': 'No separate input-specific licence verified; supplied brief permits local running and modification.'}, {'name': 'amber99sb.xml', 'required': True, 'kind': 'published input', 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/amber99sb.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'sha256': '186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092', 'bytes': 467697, 'verification': 'Fetched successfully and hashed during intake; not persisted as workload input.', 'access_instructions': 'Download pinned raw URL; place PDB beside driver. Force-field XML files ship inside the pinned OpenMM package.', 'licence_source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'separate_input_licence': None, 'separate_input_licence_reason': 'No separate input-specific licence verified; supplied brief permits local running and modification.'}, {'name': 'tip3p.xml', 'required': True, 'kind': 'published input', 'availability': 'available', 'url': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/tip3p.xml', 'commit': '53770948682c40bd460b39830d4e0f0fd3a4b868', 'sha256': '607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c', 'bytes': 891, 'verification': 'Fetched successfully and hashed during intake; not persisted as workload input.', 'access_instructions': 'Download pinned raw URL; place PDB beside driver. Force-field XML files ship inside the pinned OpenMM package.', 'licence_source': 'https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt', 'separate_input_licence': None, 'separate_input_licence_reason': 'No separate input-specific licence verified; supplied brief permits local running and modification.'}]
for item in files:
    dest=pathlib.Path('data')/item['name']
    if not dest.exists() or hashlib.sha256(dest.read_bytes()).hexdigest()!=item['sha256']:
        urllib.request.urlretrieve(item['url'], dest)
    if hashlib.sha256(dest.read_bytes()).hexdigest()!=item['sha256']:
        raise RuntimeError('Input checksum mismatch: '+str(dest))
FETCH
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
cat > baseline-published/anchors.json <<'ANCHORS'
[
  {
    "id": "nvidia_2025_dhfr_eight_process_throughput",
    "kind": "reference",
    "quantity": "Aggregate throughput of 8 concurrent DHFR PME simulations with MPS on one NVIDIA L40S or H100 GPU (microseconds/day)",
    "source": "Hsu, Clark and Paulsen (2025-06-04), Maximizing OpenMM Molecular Dynamics Throughput with NVIDIA Multi-Process Service. https://developer.nvidia.com/blog/maximizing-openmm-molecular-dynamics-throughput-with-nvidia-multi-process-service/",
    "published_value": 5.0,
    "comparison": "==",
    "tolerance": null,
    "uncertainty": null,
    "qualification": "Approximate reference: prose says throughput approaches this value. No per-GPU exact value, uncertainty or acceptance tolerance supplied. Applies to benchmark.py fixed-time runs with --seconds=60 and CUDA_MPS_ACTIVE_THREAD_PERCENTAGE=25; not an acceptance test for the supplied fixed-work ensemble."
  }
]
ANCHORS
cat > baseline-published/execution.json <<'EXECUTION'
{
  "representative_scale": {
    "gpu_count": 1,
    "gpu_model": null,
    "gpu_model_reason": "Brief allows H100, A100 or A10 class; actual stock GPU unknown. Record and hold actual GPU fixed.",
    "atoms_per_replica": 23558,
    "replicas": 8,
    "steps_per_replica": 25000,
    "step_fs": 4,
    "ps_per_replica": 100,
    "total_steps": 200000,
    "total_simulated_ns": 0.8,
    "energy_samples_per_replica": 100,
    "scale_search": false,
    "source": "intake/brief.md"
  },
  "inputs": {
    "published_files": [
      "5dfr_solv-cube_equil.pdb",
      "amber99sb.xml",
      "tip3p.xml"
    ],
    "generated_seeds": [
      1000,
      1001,
      1002,
      1003,
      1004,
      1005,
      1006,
      1007
    ],
    "configuration": {
      "system": "DHFR in explicit water",
      "atoms": 23558,
      "force_field": [
        "amber99sb.xml",
        "tip3p.xml"
      ],
      "nonbonded_method": "PME",
      "cutoff_nm": 0.9,
      "constraints": "HBonds",
      "hydrogen_mass_amu": 1.5,
      "integrator": "LangevinMiddleIntegrator",
      "temperature_K": 300,
      "friction_per_ps": 1,
      "step_fs": 4,
      "constraint_tolerance": 1e-05,
      "platform": "CUDA",
      "precision": "single",
      "DeterministicForces": true,
      "gpu_count": 1,
      "replicas": 8,
      "steps_per_replica": 25000,
      "seed0": 1000,
      "energy_sample_interval_steps": 250,
      "source": "intake/brief.md",
      "upstream_model_source": "https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/benchmark.py"
    },
    "driver_source": "intake/brief.md"
  },
  "outputs": {
    "file": "ensemble.json",
    "format": "JSON",
    "top_level_fields": [
      "platform",
      "properties",
      "simulated_ns",
      "total_wall_s",
      "replicas"
    ],
    "replica_fields": [
      "replica",
      "seed",
      "steps",
      "wall_s",
      "final_potential_kj_mol",
      "mean_potential_kj_mol"
    ],
    "stdout_fields": [
      "total_wall_s",
      "aggregate_ns_per_day"
    ],
    "energy_series": {
      "available_in_memory": true,
      "persisted_by_supplied_driver": false,
      "reason": "Driver collects 100 energies per replica but serializes only mean and final. Full trajectory identity cannot be established from supplied JSON alone."
    },
    "scoring_interface": {
      "primary": "Read ensemble.json total_wall_s; minimize for fixed work.",
      "aggregate_ns_per_day": "ensemble.json simulated_ns / total_wall_s * 86400",
      "speedup": "Baseline total_wall_s / candidate total_wall_s on same GPU.",
      "scientific_comparison": "Match replica and seed, compare final_potential_kj_mol and mean_potential_kj_mol; this cannot establish full series identity.",
      "published_energy_tolerance": null,
      "published_fixed_work_performance_threshold": null,
      "missing_evidence_reason": "Brief predictions supply no independent fixed-work measurements or numerical energy acceptance criterion; reference throughput has null tolerance."
    }
  },
  "timing_scope": {
    "ensemble_start": "After PDB parsing, force-field/system creation and platform lookup; before first integrator/context creation.",
    "ensemble_end": "After final context/integrator destruction; before JSON serialization.",
    "includes": [
      "Integrator and context creation, including kernel compilation inside this interval",
      "Position and velocity initialization",
      "All integration steps",
      "Potential-energy queries every 250 steps",
      "Per-replica summary construction",
      "Context and integrator destruction"
    ],
    "excludes": [
      "Package installation and downloads",
      "PDB parsing and force-field/system creation",
      "JSON writing and stdout printing"
    ],
    "per_replica": "Starts after context/positions/velocity setup; includes integration and energy queries, excludes context setup and teardown.",
    "concurrent_candidate": "Measure complete same-work ensemble makespan, including analogous replica setup and teardown; no published candidate driver or timing implementation supplied.",
    "source": "intake/brief.md"
  },
  "run_commands": [
    "python3 dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000"
  ],
  "stage_budgets_s": {},
  "budget_assessment": {
    "source": "intake/brief.md",
    "published_estimate": "Brief estimates about one minute on H100 and a few minutes on slower GPUs; estimate is unverified.",
    "verified_runtime_s": null,
    "reason": "No workload run. Fixed 200000-step total workload selected; no scale search, doubling loop, or toy extrapolation.",
    "defaults_s": {
      "setup": 1200,
      "anchors": 1200,
      "profile": 1200,
      "method_setup": 1200,
      "method_run": 1200,
      "tests": 900,
      "evaluate": 2400
    }
  },
  "unavailable_commands": {
    "concurrent_MPS_driver": null,
    "reason": "Brief supplies hypothesis and thread-percentage rule but no fixed-work concurrent driver command; none invented."
  }
}
EXECUTION
python3 - <<'CHECK'
import importlib.metadata, openmm, pathlib
from openmm import app
for name in ('openmm','OpenMM-CUDA-12'):
    if importlib.metadata.version(name)!='8.2.0':
        raise RuntimeError('Wrong package version: '+name)
pdb=app.PDBFile('data/5dfr_solv-cube_equil.pdb')
if pdb.topology.getNumAtoms()!=23558:
    raise RuntimeError('Wrong atom count')
app.ForceField('amber99sb.xml','tip3p.xml')
print('Published input: atoms=23558; OpenMM=8.2.0; GPU count=1; CUDA_VISIBLE_DEVICES=0')
CHECK
python3 -m openmm.testInstallation
