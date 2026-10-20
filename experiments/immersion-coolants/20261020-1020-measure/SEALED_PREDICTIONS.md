# Sealed predictions, measure run m3 (written 2026-10-20 10:2x UTC, before any agent, box build or box ran)

Author: the operating session (Claude). Not shown to the triage, gate, build or post agents. Hash in out/SEALS.txt.

Card under test: immersion-coolants V1, "Force-field error floor for coolant MD: an enlarged C10-C50 benchmark scored
against measurement" (`../20261018-0342-card-2`), `expected: if_not`. The number measured here is its
`throughput_ns_day` PROXY 250 (Amber JAC 611 ns/day on one A100, with a safety factor of about 2.4), `measured_by:
p_bench`, with the p_bench gate `throughput_ns_day >= 150` (else "drop the extension tier and re-plan with 48 molecules
at 3 replicas"), on the card's own protocol: LOPLS-AA, 250-molecule box, 313.15 K, 2 fs, PPPM, SHAKE on C-H, pressure
tensor and heat flux sampled every 5 steps, LAMMPS 29Aug2024, one A100.

| # | Prediction | Probability |
|---|---|---|
| P1 | The committed builder packs the 250-molecule nonylcyclohexane box at 0.3 g/cm3 on the first try (the pilot's halt at 0.75 was the density) | 0.85 |
| P2 | The conda-forge LAMMPS CUDA build installs on the box within 15 minutes | 0.60 |
| P3 | The production deck as written (compute centroid/stress/atom for the heat flux) runs with the GPU package | 0.40 |
| P4 | E3: throughput on the card's protocol (deck as written if it runs, else the pressure-tensor-only variant) is below 150 ns/day, so the card's own p_bench gate fails. Point estimate 90 ns/day, range 30 to 250 | 0.65 |
| P5 | The no-sampling variant (same system, no per-5-step output) runs between 150 and 400 ns/day | 0.55 |
| P6 | Density after 0.5 ns of NPT is within 4% of the reference 0.805 g/cm3 (the card's anchor tolerance) | 0.70 |
| P7 | Per-5-step sampling costs at least 30% of throughput: no-sampling ns/day divided by as-written ns/day is at least 1.4 | 0.70 |
| P8 | The card's plan cost, recomputed with the measured throughput in place of 250, exceeds the card's USD 1,000 cap (it needs about 235 ns/day to stay under) | 0.75 |
| P9 | The run completes its first launch with no halt | 0.40 |

## Reasoning, in one paragraph

LAMMPS with the GPU package offloads pair and long-range forces; bonds, angles, dihedrals, SHAKE and every per-atom
compute stay on the CPU, and the deck asks for a centroid stress and a heat flux every five steps, which is a full
per-atom pass through the CPU with a device-to-host copy each time. Amber's 611 ns/day is a whole-engine GPU code with
no such sampling. A factor of 2.4 under Amber is generous for LAMMPS at 11,000 atoms; a factor of 5 to 10 is what I
expect, and the sampling itself may halve the rate again or fail to run on the GPU pair style at all. The card's
plan divides every cost line by this number, so the gate and the budget are both at stake.

## What would change my mind

P4 fails if the conda build includes KOKKOS with full-GPU bonded and compute support, or if the centroid stress compute
runs cheaply. P3 fails if the GPU pair style refuses the centroid compute, which the LAMMPS documentation suggests.
P2 is the toolchain risk inherited from m1: a slow download of about 80 MB of LAMMPS plus the CUDA runtime libraries.
