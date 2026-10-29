# DHFR replica ensembles on one GPU: one after another, or concurrently?

## Setup
- Software: OpenMM 8.2.0, tag `8.2.0`, commit `53770948682c40bd460b39830d4e0f0fd3a4b868` ([tag resolution](https://api.github.com/repos/openmm/openmm/git/ref/tags/8.2.0)). Install with pip: `python3 -m pip install openmm==8.2.0 OpenMM-CUDA-12==8.2.0` (manylinux x86_64 wheels for Python 3.10 to 3.13; the CUDA plugin pulls NVIDIA's CUDA 12 runtime, NVRTC and cuFFT wheels) ([openmm](https://pypi.org/project/openmm/8.2.0/), [OpenMM-CUDA-12](https://pypi.org/project/OpenMM-CUDA-12/8.2.0/)). Needs an NVIDIA driver that supports CUDA 12. Check the install with `python3 -m openmm.testInstallation`.
- Hardware: one NVIDIA data-centre GPU (H100, A100 or A10 class). The study fixes the GPU count at 1.
- System: dihydrofolate reductase (DHFR) in explicit water, 23,558 atoms: `examples/5dfr_solv-cube_equil.pdb` at the pinned commit, SHA-256 `fc9759761d9b33c58b09a3d0bf1dbdb76f23dbe0e89a8bd92f43ebcf0f2f2fdf` ([file](https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/5dfr_solv-cube_equil.pdb)). The force-field files `amber99sb.xml` and `tip3p.xml` ship inside the openmm package.
- Model: the `pme` test of OpenMM's own `examples/benchmark.py` with default options ([script](https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/examples/benchmark.py)): AMBER99SB with TIP3P, particle-mesh Ewald, 0.9 nm cutoff, bonds to hydrogen constrained, hydrogen mass 1.5 amu, `LangevinMiddleIntegrator` at 300 K with friction 1/ps and a 4 fs step, constraint tolerance 1e-5.
- Workload, fixed work: an ensemble of 8 independent replicas. Each runs 25,000 steps (100 ps) from the published equilibrated coordinates. Replica i (0 to 7) uses seed 1000+i for its initial velocities and for the integrator's random stream. CUDA platform, single precision, `DeterministicForces=true` ([CUDA platform properties](https://docs.openmm.org/8.2.0/userguide/library/04_platform_specifics.html)). Recorded per replica: potential energy every 250 steps (mean and final value) and wall time. Recorded for the ensemble: total wall time and aggregate ns/day.
- Current practice: the replicas run one after another, in one process, on one GPU. The driver below implements exactly that; run it from a directory holding the PDB file:
  `python3 dhfr_ensemble.py --replicas 8 --steps 25000 --seed0 1000`
  On an H100 the whole ensemble should take about one minute; slower GPUs take a few minutes.

```python
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
```

`benchmark.py` itself runs for a fixed time (`--seconds`, default 60) with no step-count or seed option, so it measures throughput rather than time to finish a fixed amount of work. The driver keeps its `pme` system and integrator unchanged and fixes the work and the seeds.

## Research question
Can a fixed ensemble of independent small-system simulations finish sooner on one GPU, with every replica's scientific outcome unchanged, than by running the replicas one after another?

## Hypothesis
One DHFR simulation leaves a modern data-centre GPU partly idle. Running several replicas at once as separate processes that share the GPU through CUDA Multi-Process Service (MPS) raises aggregate throughput, so the same ensemble finishes sooner on the same single GPU.

Basis: NVIDIA's study of OpenMM 8.2.0 with MPS (Hsu, Clark and Paulsen, 4 June 2025, [post](https://developer.nvidia.com/blog/maximizing-openmm-molecular-dynamics-throughput-with-nvidia-multi-process-service/)) ran `benchmark.py --platform=CUDA --test=pme --seconds=60` as 1, 2, 4 or 8 concurrent processes on GPUs from A10 to H100. For DHFR it reports that "for some GPUs, including the NVIDIA H100 Tensor Core, the total throughput can more than double", and that setting `CUDA_MPS_ACTIVE_THREAD_PERCENTAGE` to 200 divided by the number of processes raises the collective throughput of 8 DHFR simulations "by about 15 – 25%", approaching 5 microseconds per day on a single L40S or H100. Per-GPU numbers appear only in the post's figures.

## Predictions
1. Time to finish: on an H100, running the 8 replicas concurrently under MPS completes the ensemble in at most half the sequential wall time (speedup 2.0 to 3.5). On an A100 the speedup is 1.5 to 3.0; on an A10, 1.1 to 2.0. The GPU count stays 1, so the cost per ensemble falls by the same factor.
2. Outcomes unchanged: with the same seed, GPU model, software and deterministic forces, each replica's energy series is identical whether it runs alone or alongside others. If it is not bit-identical, each replica's mean potential energy differs by no more than its run-to-run variation in the one-after-another configuration with the same seed.
3. Without MPS, concurrent processes time-share the GPU and the gain is smaller: at most 1.5 on an H100.
4. Diminishing returns: the gain rises from 2 to 4 to 8 concurrent replicas and flattens beyond 4 on an H100.

## Published reference observations
- NVIDIA (2025), above: DHFR total throughput on an H100 "can more than double" under MPS; 8 simulations with the tuned thread percentage approach 5 microseconds per day on one L40S or H100. These are fixed-time throughput measurements on `benchmark.py`, not the fixed-work ensemble above. The post gives no uncertainty and no acceptance tolerance, and none is implied here.

## Licence
OpenMM's API, Reference and CPU platforms are under the MIT licence; the CUDA and OpenCL platforms are under the GNU LGPL (`docs-source/licenses/Licenses.txt` at the pinned commit, [file](https://github.com/openmm/openmm/blob/53770948682c40bd460b39830d4e0f0fd3a4b868/docs-source/licenses/Licenses.txt)). The PDB file is distributed in the same repository. Local running and modification are permitted.

## Unverified
- The driver was run only on OpenMM 8.2.0's CPU platform (Python 3.12, 2 replicas of 250 steps), not on CUDA. The CPU platform is not deterministic for PME, and two runs with the same seeds gave different energies, as OpenMM documents. Determinism on CUDA with `DeterministicForces=true` is documented, not tested here.
- No citable absolute single-replica ns/day for this configuration on an H100 was found.
- The cost of creating each replica's context, including kernel compilation, is unmeasured.
