#!/usr/bin/env bash
set -euo pipefail
mkdir -p baseline-published data out/setup
exec > >(tee -a out/setup/setup.log) 2>&1
# Only toolkit roots whose nvcc was found by the box probe are candidates.
selected=""
for root in /usr/local/cuda /usr/lib/cuda; do
    if [[ -x "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
        selected="$root"
        break
    fi
done
if [[ -n "$selected" ]]; then
    compiler="$selected/bin/nvcc"
    headers="$selected/include"
    libraries="$selected/lib64"
else
    compiler=/usr/bin/nvcc
    headers=/usr/include
    libraries=/usr/lib/x86_64-linux-gnu
fi
ls -l "$compiler" "$headers/cuda_runtime.h" "$libraries/libcudart.so"
[[ -x "$compiler" ]] || { echo 'Complete CUDA 12.8 toolkit required' >&2; exit 1; }
{
    printf 'export CUDACXX=%q\n' "$compiler"
    printf 'export CUDA_INCLUDE_DIR=%q\n' "$headers"
    printf 'export CUDA_LIBRARY_DIR=%q\n' "$libraries"
    if [[ -n "$selected" ]]; then
        printf 'export CUDAToolkit_ROOT=%q\n' "$selected"
    fi
    printf 'export PATH=%q:"$PATH"\n' "$(dirname "$compiler")"
    printf 'export LD_LIBRARY_PATH=%q${LD_LIBRARY_PATH:+:"$LD_LIBRARY_PATH"}\n' "$libraries"
} > baseline-published/cuda-env.sh
source baseline-published/cuda-env.sh
command -v git
python3 -m pip --version
pin=53770948682c40bd460b39830d4e0f0fd3a4b868
if [[ ! -d baseline-published/source/.git ]]; then
    git clone --no-checkout https://github.com/openmm/openmm baseline-published/source
fi
git -C baseline-published/source fetch origin "$pin"
git -C baseline-published/source checkout --detach "$pin"
[[ "$(git -C baseline-published/source rev-parse HEAD)" == "$pin" ]]
# Install into a private target; stock torch and site packages remain intact.
python3 -m pip install --upgrade --target baseline-published/python openmm==8.2.0 OpenMM-CUDA-12==8.2.0
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
cat > baseline-published/intake.json <<'INTAKE_JSON'
{
  "benchmark": {
    "found": true,
    "identity": {
      "name": "OpenMM 8.2.0 DHFR pme fixed-work ensemble on one GPU",
      "public_benchmark": "OpenMM examples/benchmark.py --test=pme",
      "brief_workload": "Eight seeded DHFR replicas, sequential baseline versus concurrent execution with MPS.",
      "version": "8.2.0",
      "commit": "53770948682c40bd460b39830d4e0f0fd3a4b868",
      "repo": "https://github.com/openmm/openmm",
      "provenance": "Public executable pme benchmark and inputs verified; fixed-work adaptation is inline in supplied brief, not independently published code at a public URL."
    },
    "outcome_definition": {
      "primary": "Minimize total wall seconds for complete fixed ensemble; speedup = sequential_total_wall_s / candidate_total_wall_s.",
      "throughput": "aggregate_ns_per_day = 0.8 / total_wall_s * 86400",
      "scientific_outputs": [
        "Each replica final_potential_kj_mol",
        "Each replica mean_potential_kj_mol"
      ],
      "scientific_acceptance": "Brief predicts identical per-seed energy series on same hardware/software with deterministic forces. Fallback refers to measured sequential run-to-run variation, which is unavailable. No independent published energy acceptance tolerance exists.",
      "energy_tolerance": null,
      "energy_tolerance_reason": "No published numeric acceptance criterion; do not use integrator constraint tolerance as outcome tolerance.",
      "published_performance_acceptance": null,
      "published_performance_acceptance_reason": "NVIDIA observations are fixed-time reference throughput, not acceptance thresholds for fixed-work ensemble. Brief speedup ranges are predictions.",
      "reference_comparison": "Report context and units; do not score fixed-work runtime against approximate fixed-time throughput reference.",
      "repeatability": {
        "fixed_seeds": [
          1000,
          1001,
          1002,
          1003,
          1004,
          1005,
          1006,
          1007
        ],
        "requirements": "Same GPU model, OpenMM pin, force fields, initial positions, precision and deterministic-force setting for comparisons.",
        "published_repeat_count": null,
        "reason": "No repeat count or statistical aggregation rule published for supplied fixed-work driver.",
        "determinism_status": "Unverified on CUDA. Documentation describes deterministic forces but also cautions single-precision PME simulation determinism depends on settings; trajectory identity requires reproduction.",
        "source": "https://docs.openmm.org/8.2.0/userguide/library/04_platform_specifics.html"
      },
      "interface_limitation": "Inline driver samples energies internally but serializes only mean and final value; complete time-series equality cannot be audited from ensemble.json alone."
    },
    "citations": [
      {
        "id": "brief",
        "source": "brief.md",
        "description": "Supplied fixed-work ensemble specification and inline sequential driver; predictions are hypotheses, not published results."
      },
      {
        "id": "openmm-benchmark",
        "source": "https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/benchmark.py",
        "description": "Public executable pme benchmark; fixed-time throughput measurement, not fixed-work ensemble."
      },
      {
        "id": "nvidia-2025",
        "source": "https://developer.nvidia.com/blog/maximizing-openmm-molecular-dynamics-throughput-with-nvidia-multi-process-service/",
        "title": "Maximizing OpenMM Molecular Dynamics Throughput with NVIDIA Multi-Process Service",
        "authors": [
          "Darren Hsu",
          "David Clark",
          "Janet Paulsen"
        ],
        "date": "2025-06-04"
      },
      {
        "id": "openmm-license",
        "source": "https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt"
      },
      {
        "id": "platform-properties",
        "source": "https://docs.openmm.org/8.2.0/userguide/library/04_platform_specifics.html"
      },
      {
        "id": "openmm-wheel",
        "source": "https://pypi.org/project/openmm/8.2.0/"
      },
      {
        "id": "cuda-wheel",
        "source": "https://pypi.org/project/OpenMM-CUDA-12/8.2.0/"
      }
    ],
    "source_licences_and_intended_use": {
      "status": "permitted",
      "intended_use": "Local scientific benchmarking, execution and modification.",
      "sources": [
        "https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt",
        "brief.md, Licence section"
      ],
      "components": [
        {
          "component": "OpenMM API, Reference and CPU platforms",
          "licence": "MIT"
        },
        {
          "component": "CUDA and OpenCL platforms",
          "licence": "GNU LGPL; consult accompanying LGPL.txt and GPL.txt for exact terms"
        },
        {
          "component": "PDB and force-field inputs",
          "licence": "Distributed in OpenMM repository; no separate data licence identified in inspected sources.",
          "permission_evidence": "Supplied brief explicitly states local running and modification are permitted; repository supplies inputs with software."
        }
      ],
      "redistribution": "Observe applicable copyright and licence terms; intake assesses local use."
    },
    "stock_cuda_image": {
      "feasible": null,
      "reason": "Stock image identity, Python version, architecture, glibc, NVIDIA driver and MPS availability were not supplied or inspected; no CUDA reproduction performed.",
      "provisional_compatibility_evidence": [
        "OpenMM 8.2.0 publishes manylinux x86_64 wheels for CPython 3.10 through 3.13.",
        "OpenMM-CUDA-12 8.2.0 publishes manylinux_2_27/2_28 x86_64 plugin wheel and declares NVIDIA CUDA 12 runtime, nvcc, NVRTC, CUPTI and cuFFT dependencies.",
        "Brief requires one CUDA-12-compatible NVIDIA GPU; NVIDIA post demonstrates OpenMM 8.2.0 with MPS on H100-class hardware."
      ],
      "sources": [
        "https://pypi.org/pypi/openmm/8.2.0/json",
        "https://pypi.org/pypi/OpenMM-CUDA-12/8.2.0/json",
        "https://developer.nvidia.com/blog/maximizing-openmm-molecular-dynamics-throughput-with-nvidia-multi-process-service/",
        "brief.md"
      ],
      "reproduction_status": "not run",
      "mps_permission": null,
      "mps_permission_reason": "Host daemon availability and permission were not supplied."
    },
    "data_and_memory": {
      "required_input_bytes": 2282791,
      "required_input_GiB": 0.002126014791429043,
      "peak_working_set_GiB": null,
      "total_data_plus_peak_working_set_GiB": null,
      "size": "unknown",
      "reason": "PDB plus two XML file sizes verified over HTTPS; peak host/GPU memory for eight concurrent contexts and CUDA runtime is unpublished and unmeasured. Installation footprint not included in input bytes."
    },
    "configuration": {
      "atoms": 23558,
      "replicas": 8,
      "gpu_count": 1,
      "steps_per_replica": 25000,
      "total_steps": 200000,
      "step_ps": 0.004,
      "ps_per_replica": 100,
      "total_simulated_ns": 0.8,
      "seed0": 1000,
      "seeds": [
        1000,
        1001,
        1002,
        1003,
        1004,
        1005,
        1006,
        1007
      ],
      "energy_interval_steps": 250,
      "energy_samples_per_replica": 100,
      "platform": "CUDA",
      "properties": {
        "Precision": "single",
        "DeterministicForces": "true"
      },
      "forcefield_files": [
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
      "constraint_tolerance": 1e-05,
      "source": "brief.md; https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/benchmark.py"
    },
    "search_candidates": [],
    "discovery": "No benchmark search or replacement; inspected only brief-linked sources and their pinned raw files/PyPI metadata.",
    "gate": {
      "complete_files": true,
      "found": true,
      "data": "available",
      "licence": "permitted",
      "stock_environment": null,
      "reason": "Missing tolerances do not block; unknown stock compatibility awaits reproduction."
    }
  },
  "data": {
    "availability": "available",
    "required_inputs": [
      {
        "name": "5dfr_solv-cube_equil.pdb",
        "source": "https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb",
        "commit": "53770948682c40bd460b39830d4e0f0fd3a4b868",
        "bytes": 1814203,
        "sha256": "fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf",
        "availability": "available",
        "verification": "HTTPS GET succeeded; byte count and SHA-256 computed during intake.",
        "access_instructions": "Download pinned raw URL. Place PDB in driver working directory; XML files ship in openmm==8.2.0 package.",
        "licence": {
          "component": "PDB and force-field inputs",
          "licence": "Distributed in OpenMM repository; no separate data licence identified in inspected sources.",
          "permission_evidence": "Supplied brief explicitly states local running and modification are permitted; repository supplies inputs with software."
        }
      },
      {
        "name": "amber99sb.xml",
        "source": "https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/amber99sb.xml",
        "commit": "53770948682c40bd460b39830d4e0f0fd3a4b868",
        "bytes": 467697,
        "sha256": "186f8570413f2ad3efe923578fc53cc895006d50de4b612e9fc58977a914c092",
        "availability": "available",
        "verification": "HTTPS GET succeeded; byte count and SHA-256 computed during intake.",
        "access_instructions": "Download pinned raw URL. Place PDB in driver working directory; XML files ship in openmm==8.2.0 package.",
        "licence": {
          "component": "PDB and force-field inputs",
          "licence": "Distributed in OpenMM repository; no separate data licence identified in inspected sources.",
          "permission_evidence": "Supplied brief explicitly states local running and modification are permitted; repository supplies inputs with software."
        }
      },
      {
        "name": "tip3p.xml",
        "source": "https://raw.githubusercontent.com/openmm/openmm/53770948682c40bd460b39830d4e0f0fd3a4b868/wrappers/python/openmm/app/data/tip3p.xml",
        "commit": "53770948682c40bd460b39830d4e0f0fd3a4b868",
        "bytes": 891,
        "sha256": "607f0fc9566c3770db2d9eb579fed68c4157578445eed1ec0aa7dccc23d57a6c",
        "availability": "available",
        "verification": "HTTPS GET succeeded; byte count and SHA-256 computed during intake.",
        "access_instructions": "Download pinned raw URL. Place PDB in driver working directory; XML files ship in openmm==8.2.0 package.",
        "licence": {
          "component": "PDB and force-field inputs",
          "licence": "Distributed in OpenMM repository; no separate data licence identified in inspected sources.",
          "permission_evidence": "Supplied brief explicitly states local running and modification are permitted; repository supplies inputs with software."
        }
      }
    ],
    "generated_inputs": [
      {
        "name": "initial velocities and Langevin stochastic streams",
        "generation": "OpenMM velocity initialization at 300 K and LangevinMiddleIntegrator random stream, seed 1000+i for replica i.",
        "seeds": [
          1000,
          1001,
          1002,
          1003,
          1004,
          1005,
          1006,
          1007
        ],
        "source": "brief.md"
      }
    ],
    "missing_required_data": [],
    "splits": null,
    "splits_reason": "Molecular dynamics ensemble has no train/validation/test split.",
    "seeds": [
      1000,
      1001,
      1002,
      1003,
      1004,
      1005,
      1006,
      1007
    ],
    "external_dataset_required": false,
    "access_credentials_required": false,
    "licences": {
      "status": "permitted",
      "intended_use": "Local scientific benchmarking, execution and modification.",
      "sources": [
        "https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt",
        "brief.md, Licence section"
      ],
      "components": [
        {
          "component": "OpenMM API, Reference and CPU platforms",
          "licence": "MIT"
        },
        {
          "component": "CUDA and OpenCL platforms",
          "licence": "GNU LGPL; consult accompanying LGPL.txt and GPL.txt for exact terms"
        },
        {
          "component": "PDB and force-field inputs",
          "licence": "Distributed in OpenMM repository; no separate data licence identified in inspected sources.",
          "permission_evidence": "Supplied brief explicitly states local running and modification are permitted; repository supplies inputs with software."
        }
      ],
      "redistribution": "Observe applicable copyright and licence terms; intake assesses local use."
    },
    "transitive_forcefield_inputs": {
      "availability": "available",
      "access": "Bundled OpenMM 8.2.0 package and same pinned repository; XML includes resolve through package data.",
      "individual_hashes": null,
      "reason": "Top-level force fields verified; transitive package data pinned by release, not individually audited."
    }
  },
  "anchors": [
    {
      "id": "nvidia-2025-dhfr-eight-replicas-throughput-reference",
      "quantity": "Aggregate DHFR pme throughput, eight concurrent MPS simulations, microseconds/day",
      "source": "Hsu, Clark and Paulsen, NVIDIA Technical Blog, 2025-06-04, https://developer.nvidia.com/blog/maximizing-openmm-molecular-dynamics-throughput-with-nvidia-multi-process-service/",
      "published_value": 5.0,
      "comparison": "==",
      "tolerance": null,
      "uncertainty": null,
      "kind": "reference",
      "is_anchor": false,
      "configuration": {
        "openmm_version": "8.2.0",
        "gpu_count": 1,
        "gpu_models": "L40S or H100",
        "concurrent_simulations": 8,
        "CUDA_MPS_ACTIVE_THREAD_PERCENTAGE": 25,
        "command": "python benchmark.py --platform=CUDA --test=pme --seconds=60"
      },
      "qualifier": "Approximate: approaches 5 microseconds/day; not an exact measurement or acceptance criterion.",
      "applicability": "Independent fixed-time throughput reference only. Does not publish fixed-work 8 x 25000-step timing, deterministic-force overhead, energy values or tolerances."
    }
  ],
  "EXECUTION": {
    "representative_scale": {
      "atoms": 23558,
      "replicas": 8,
      "gpu_count": 1,
      "steps_per_replica": 25000,
      "total_steps": 200000,
      "step_ps": 0.004,
      "ps_per_replica": 100,
      "total_simulated_ns": 0.8,
      "seed0": 1000,
      "seeds": [
        1000,
        1001,
        1002,
        1003,
        1004,
        1005,
        1006,
        1007
      ],
      "energy_interval_steps": 250,
      "energy_samples_per_replica": 100,
      "platform": "CUDA",
      "properties": {
        "Precision": "single",
        "DeterministicForces": "true"
      },
      "forcefield_files": [
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
      "constraint_tolerance": 1e-05,
      "source": "brief.md; https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/benchmark.py"
    },
    "inputs": {
      "required_files": [
        "5dfr_solv-cube_equil.pdb"
      ],
      "packaged_files": [
        "amber99sb.xml",
        "tip3p.xml"
      ],
      "driver": "Python code block in brief.md",
      "command": "python3 dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000",
      "working_directory": "Directory holding driver and pinned PDB.",
      "generated": "Seeds 1000..1007 for velocities and integrator RNG.",
      "scale_selection": "Single fixed scale from brief; no scale search, adaptive step count or doubling loops."
    },
    "outputs": {
      "file": "ensemble.json",
      "json_fields": {
        "platform": "CUDA",
        "properties": {
          "Precision": "single",
          "DeterministicForces": "true"
        },
        "simulated_ns": 0.8,
        "total_wall_s": "Positive finite seconds",
        "replicas": "Eight records with replica, seed, steps, wall_s, final_potential_kj_mol, mean_potential_kj_mol"
      },
      "stdout": [
        "total_wall_s",
        "aggregate_ns_per_day"
      ],
      "energy_unit": "kJ/mol",
      "full_energy_series": null,
      "full_energy_series_reason": "Sampled every 250 steps but not saved by published inline driver."
    },
    "timing_scope": {
      "ensemble_start": "Immediately before replica loop, after PDB parse, force-field/system creation and platform selection.",
      "ensemble_end": "After all replicas finish and each context/integrator is deleted; before JSON serialization and stdout.",
      "included": [
        "Context creation and lazy CUDA compilation",
        "Position and seeded velocity initialization",
        "All 200000 integration steps",
        "100 synchronous energy queries per replica",
        "Per-replica result construction",
        "Context/integrator destruction"
      ],
      "excluded": [
        "Package installation",
        "Input downloads",
        "PDB parsing",
        "Force-field/system construction",
        "Final JSON write",
        "Python interpreter startup"
      ],
      "per_replica": "Starts after context and velocity initialization; includes integration, energy queries and per-replica result preparation; excludes context destruction.",
      "concurrent_comparison": "Time entire ensemble completion on one GPU, including creation and cleanup of every replica context; preserve work, seeds and 100 energy queries per replica. Include candidate orchestration overhead; no warm-up exclusion absent from sequential baseline.",
      "source": "brief.md inline driver"
    },
    "scoring_interface": {
      "primary": "Minimize total wall seconds for complete fixed ensemble; speedup = sequential_total_wall_s / candidate_total_wall_s.",
      "throughput": "aggregate_ns_per_day = 0.8 / total_wall_s * 86400",
      "scientific_outputs": [
        "Each replica final_potential_kj_mol",
        "Each replica mean_potential_kj_mol"
      ],
      "scientific_acceptance": "Brief predicts identical per-seed energy series on same hardware/software with deterministic forces. Fallback refers to measured sequential run-to-run variation, which is unavailable. No independent published energy acceptance tolerance exists.",
      "energy_tolerance": null,
      "energy_tolerance_reason": "No published numeric acceptance criterion; do not use integrator constraint tolerance as outcome tolerance.",
      "published_performance_acceptance": null,
      "published_performance_acceptance_reason": "NVIDIA observations are fixed-time reference throughput, not acceptance thresholds for fixed-work ensemble. Brief speedup ranges are predictions.",
      "reference_comparison": "Report context and units; do not score fixed-work runtime against approximate fixed-time throughput reference.",
      "repeatability": {
        "fixed_seeds": [
          1000,
          1001,
          1002,
          1003,
          1004,
          1005,
          1006,
          1007
        ],
        "requirements": "Same GPU model, OpenMM pin, force fields, initial positions, precision and deterministic-force setting for comparisons.",
        "published_repeat_count": null,
        "reason": "No repeat count or statistical aggregation rule published for supplied fixed-work driver.",
        "determinism_status": "Unverified on CUDA. Documentation describes deterministic forces but also cautions single-precision PME simulation determinism depends on settings; trajectory identity requires reproduction.",
        "source": "https://docs.openmm.org/8.2.0/userguide/library/04_platform_specifics.html"
      },
      "interface_limitation": "Inline driver samples energies internally but serializes only mean and final value; complete time-series equality cannot be audited from ensemble.json alone."
    },
    "expected_duration": {
      "source": "brief.md",
      "claim": "About one minute on H100; a few minutes on slower GPUs.",
      "verified": false,
      "reason": "No CUDA run or compilation-overhead measurement supplied."
    },
    "stage_budgets_s": {
      "setup": 1200,
      "anchors": 1200,
      "profile": 1200,
      "method_setup": 1200,
      "method_run": 1200,
      "tests": 900,
      "evaluate": 2400
    },
    "stage_budgets_source": "User-supplied defaults; no overrides.",
    "budget_feasibility": "Fixed-scale duration claim is below default budgets; actual duration remains unverified. No workloads run during intake.",
    "gate_scripts": null,
    "gate_scripts_reason": "No gate script path or command supplied; only JSON and evidence consistency validated locally."
  },
  "baseline": {
    "repo": "https://github.com/openmm/openmm",
    "commit": "53770948682c40bd460b39830d4e0f0fd3a4b868",
    "immutable_pin": {
      "tag": "8.2.0",
      "commit": "53770948682c40bd460b39830d4e0f0fd3a4b868",
      "source": "https://api.github.com/repos/openmm/openmm/git/ref/tags/8.2.0",
      "verified": true
    },
    "build_commands": [
      "python3 -m pip install openmm==8.2.0 OpenMM-CUDA-12==8.2.0"
    ],
    "build_commands_source": "brief.md, Setup; released versions confirmed by PyPI metadata.",
    "run_commands": [
      "python3 dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000"
    ],
    "run_commands_source": "brief.md, Setup, inline driver.",
    "validation_commands": [
      "python3 -m openmm.testInstallation"
    ],
    "validation_commands_source": "brief.md, Setup.",
    "public_reference_run_commands": [
      "python benchmark.py --platform=CUDA --test=pme --seconds=60"
    ],
    "public_reference_run_commands_source": "https://developer.nvidia.com/blog/maximizing-openmm-molecular-dynamics-throughput-with-nvidia-multi-process-service/",
    "public_reference_command_role": "Provenance only; not representative execution command. Upstream script adapts step counts internally and is not the fixed-work driver.",
    "driver": {
      "name": "dhfr_ensemble.py",
      "source": "brief.md, sole Python code block",
      "sha256": "a5d2e8eb2973ca36a8eda295319d9ee2596c239ca6b204ddc557d575f959429f",
      "materialization": "Copy Python code block verbatim to dhfr_ensemble.py during later setup. Intake does not create or execute driver.",
      "public_url": null,
      "reason": "Inline fixed-work adaptation supplied in brief; public upstream code is benchmark.py."
    },
    "input_access": "Download pinned PDB URL from data.json into driver working directory; force-field XML files are packaged.",
    "published_configuration": {
      "atoms": 23558,
      "replicas": 8,
      "gpu_count": 1,
      "steps_per_replica": 25000,
      "total_steps": 200000,
      "step_ps": 0.004,
      "ps_per_replica": 100,
      "total_simulated_ns": 0.8,
      "seed0": 1000,
      "seeds": [
        1000,
        1001,
        1002,
        1003,
        1004,
        1005,
        1006,
        1007
      ],
      "energy_interval_steps": 250,
      "energy_samples_per_replica": 100,
      "platform": "CUDA",
      "properties": {
        "Precision": "single",
        "DeterministicForces": "true"
      },
      "forcefield_files": [
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
      "constraint_tolerance": 1e-05,
      "source": "brief.md; https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/benchmark.py"
    },
    "baseline_execution": "One process, one GPU, eight replicas run sequentially; create and destroy each context in loop.",
    "transitive_dependency_pins": null,
    "transitive_dependency_pins_reason": "Published pip command does not pin NumPy or NVIDIA dependency versions. No dependency lock supplied; do not invent pins.",
    "build_or_workload_executed": false
  }
}
INTAKE_JSON
python3 - <<'STAGE'
import hashlib, json, pathlib, urllib.request
root = pathlib.Path('.')
meta = json.loads((root/'baseline-published/intake.json').read_text())
for item in meta['data']['required_inputs']:
    dest = root/'data'/item['name']
    if not dest.exists() or hashlib.sha256(dest.read_bytes()).hexdigest() != item['sha256']:
        blob = urllib.request.urlopen(item['source'], timeout=120).read()
        if hashlib.sha256(blob).hexdigest() != item['sha256']:
            raise RuntimeError('Input checksum mismatch: '+item['name'])
        dest.write_bytes(blob)
STAGE
export PYTHONPATH="$PWD/baseline-published/python${PYTHONPATH:+:$PYTHONPATH}"
export CUDA_VISIBLE_DEVICES=0
export PYTHONDONTWRITEBYTECODE=1
export CUDA_CACHE_PATH="$PWD/out/setup/cuda-cache"
mkdir -p "$CUDA_CACHE_PATH"
python3 - <<'CHECK'
import importlib.metadata
import openmm
assert importlib.metadata.version('openmm') == '8.2.0'
assert importlib.metadata.version('OpenMM-CUDA-12') == '8.2.0'
print('OpenMM', openmm.__version__)
CHECK
python3 -m openmm.testInstallation
