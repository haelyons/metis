# IC-V1 — Force-field error floor for coolant MD (working file, producer)

Option IC-V1, root question: generative pipeline for discovery of single-phase
immersion coolants. Budget: $1,000 of Lambda on-demand GPU credit
(https://lambda.ai/pricing, read 2026-10-18).

## What this run decides

MD is used to rank candidate immersion coolants by viscosity and thermal
conductivity. This run turns the verification step into the object of study:
one fixed GPU-MD protocol, run over a systematically enlarged set of C10–C50
hydrocarbons and esters, scored **only** against measured values. The unknown:
is the force-field error a correctable systematic bias, or a random floor that
caps how far a ranking can be trusted?

## What to build

1. **Protocol** (built once, held fixed): LAMMPS, LOPLS-AA (the force field of
   the closest prior, whose SMILES-to-LAMMPS builder, equilibration/production/
   continuation decks and Green–Kubo analysis script are public
   — https://doi.org/10.5281/zenodo.21824121), 250 molecules per box
   (finite-size check in https://pubs.aip.org/aip/jcp/article/165/14/144101/3406182/Computing-shear-viscosities-from-molecular:
   "the viscosity of molecular liquids is not influenced by finite size effects
   down to systems as small as 250 molecules"), 2 fs timestep, PME
   electrostatics, NPT equilibration 2 ns, then 6 independent NVT replicas of
   5 ns each; Green–Kubo viscosity from the three off-diagonal stress
   components and Green–Kubo thermal conductivity from the heat-flux
   autocorrelation in the same trajectories (one protocol, two properties).
   Temperature 313.15 K (40 °C), 1 atm — the temperature of the measured
   reference set.
2. **Benchmark set**: a stratified subset of the public 835-molecule C10–C50
   reference set (hydrocarbons + esters/ethers, measured dynamic viscosity
   1–50 mPa·s at 40 °C), scored at set sizes 8, 24, 48, 120. Commercial
   single-phase coolants enter as measured property bands (Engineered Fluids
   ElectroCool EC-110/120/130/140 data sheet: kinematic viscosity at 40 °C
   7.25/16.10/5.02/36.10/67.10 cSt, thermal conductivity at 40 °C
   0.1374/0.1439/0.1359/0.1466/0.1568 W/m·K), not as MD targets, because the
   blends are proprietary.
3. **Scoring**: per-molecule error vs measurement (MAPE for viscosity and
   thermal conductivity), chemistry-family split (hydrocarbon vs oxygenate),
   Spearman rank correlation MD vs measurement at each set size, and a
   held-out bias-correction test (fit a multiplicative correction on half the
   molecules, score on the other half). That held-out MAPE is the decision
   quantity.

## Baseline

Today's practice: Green–Kubo MD on a handful of molecules — the closest prior
ran eight C10–C50 molecules at 40 °C and 100 °C
(https://spiral.imperial.ac.uk/entities/publication/9423c271-1953-481c-8e8d-88eeb67e2535).
Baseline arm: the same 8 molecules, short runs (2 ns equilibration + 3 × 2 ns),
scored identically. Every compute level after that changes only the number of
molecules.

## How to check it is right

- **Anchor**: repeat the prior's eight molecules first. Published outcome
  (Conclusions of
  https://spiral.imperial.ac.uk/server/api/core/bitstreams/fa07c113-8958-4f1e-a010-0ef2bfc39e17/content):
  "Density is reproduced to within 4% for seven of the eight molecules at
  40 °C. Viscosity errors are small for the pure hydrocarbons with LOPLS, but
  this property is consistently under-predicted for the oxygen-containing
  molecules; the reference ranking of the fluids is nonetheless largely
  preserved. Thermal conductivity is over-predicted for every molecule, by
  amounts that correlate with the density of aliphatic C–H bonds, compressing
  the reference range and misordering the fluids." Tolerance: same bias signs,
  density within 4 percentage points of the published error, per-molecule
  viscosity within 20% of the reference value.
- **Independent code**: the prior's public LAMMPS decks and Green–Kubo
  analysis script (Zenodo 10.5281/zenodo.21824121) — our pipeline must
  reproduce their numbers on their eight molecules before it is used on new
  ones.
- **Static checks**: density within 2% of reference before any transport
  scoring; the three off-diagonal stress components must agree within their
  replica spread; Green–Kubo integral plateau must be shorter than t_prod/10;
  NVE energy drift check on one production run; units audit (mPa·s vs µPa·s).
- **Noise rule**: bootstrap the molecules (1000 resamples) for 95% intervals
  on MAPE and Spearman ρ; a difference is real only if the interval excludes
  the decision threshold. Replica noise: the standard error of a molecule's
  viscosity must fall roughly as 1/sqrt(n_replicas) — measured in phase
  p_bench by comparing 1 vs 6 replicas.

## Cost (Lambda on-demand)

Rate: 8× NVIDIA A100 SXM 40 GB at $1.99 per GPU-hour (price sheet
https://lambda.ai/pricing). Per-molecule: 32 ns of trajectory (2 ns
equilibration + 6 × 5 ns) at a design throughput of 250 ns/day per GPU —
proxy from the Amber A100 benchmark, JAC 23,558 atoms PME 2 fs, 611 ns/day on
one A100 (https://ambermd.org/GPUPerformance.php); differs in code, system
(our boxes are neat organic liquids, ~23,000 atoms) and in per-step
stress-tensor autocorrelation accumulation. Phase p_bench measures the real
throughput; if it comes in below 150 ns/day the extension tier is cut.

| line | hours (wall clock on the instance) | rate | $ |
|---|---|---|---|
| dry run, build + analysis code | 4 | A6000 1× $1.09 | 4.36 |
| pilot (4 molecules, throughput + plateau) | 2 | A100 8× $1.99 | 31.84 |
| core benchmark, 48 molecules | 19 | A100 8× $1.99 | 302.48 |
| extension to 120 molecules | 28 | A100 8× $1.99 | 445.12 |
| scoring, bias correction, report | 6 | A6000 1× $1.09 | 6.54 |
| filesystem, 150 GiB for one month | — | $0.20/GiB-month | 30.00 |
| re-run allotment (missed plateaus) | — | — | 120.00 |
| **total** | | | **940.34** |

Budget_usd 1000; spend cap 1000. Yields: 120 molecules scored, 3840 ns of
trajectory, 720 replica runs.

## Phases

1. p_local — assemble the protocol from the public decks; run
   pilot/cost_and_noise_check.py (synthetic Green–Kubo data) to validate the
   scoring and noise rule. Gate: false-positive rate of the rank rule ≤ 0.08.
2. p_bench — 4 molecules × 3 replicas on GPU: measure throughput, Green–Kubo
   plateau time, replica spread. Gate: throughput_ns_day ≥ 150.
3. p_anchor — the prior's eight molecules. Gate: per-molecule viscosity error
   ≤ 0.20 vs reference, else stop and report the protocol is not trustworthy.
4. p_core — 48 molecules at the fixed protocol.
5. p_ext — the remaining 72 molecules (only if gates passed).
6. p_score — error distributions, held-out bias correction, rank correlation
   at 8/24/48/120 molecules; write the report.

## Predictions

- if_lever: at 120 molecules, held-out viscosity MAPE after bias correction
  ≤ 0.15 and Spearman ρ ≥ 0.90 → ranking of coolant candidates is trustworthy.
- if_not: held-out MAPE ≥ 0.25 or ρ ≤ 0.70 at every set size → random error
  floor caps how far ranking can be trusted.
- Expected: **if_not**. The prior already reports chemistry-dependent
  LOPLS-AA errors (viscosity under-predicted for oxygenates, thermal
  conductivity over-predicted for every molecule and misordering the fluids);
  those are model errors, not sampling errors, and more molecules will
  characterise rather than remove them.

## Restructuring

Method "none": molecules and replicas are independent and run side by side
across GPUs. The only chain per molecule is equilibration → 6 production runs →
averaging (3 steps).

## Scope gap / limits

- Pure liquids in the 1–50 mPa·s range at 40 °C only; proprietary commercial
  blends are not simulated (data-sheet bands only).
- One force field (LOPLS-AA); the error floor of other force fields is a
  different question.
- Ranking beyond 120 molecules and above 50 mPa·s viscosity is untested.
