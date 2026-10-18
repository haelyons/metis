# Force-field error floor for coolant MD — enlarged C10–C50 benchmark scored against measurement

Working plan for option V1. Budget: $1,000 of GPU credit at Lambda on-demand
prices (read 2026-10-18). All DERIVED arithmetic is reproduced by
`pilot/cost_calc.py` (see `pilot/cost_calc.out`).

## Question
Does one GPU-MD force field rank C10–C50 hydrocarbons and esters in the same
order as measured viscosity and thermal conductivity?

## Hypothesis
One TraPPE-UA Green-Kubo protocol reproduces the measured ranking of coolants
because its viscosity error is a systematic bias, not a random floor.

## What to build
A single GPU-MD protocol (GROMACS + TraPPE-UA united-atom force field) that, for
each benchmark molecule, runs one NVT production trajectory and extracts **both**
shear viscosity and thermal conductivity from the same run via Green–Kubo
(integrals of the pressure-tensor and heat-flux autocorrelation functions).
Per molecule: 5 independent 20-ns replicate trajectories (= 100 ns total) so
run-to-run noise is measured, following the NIST best-practices recommendation to
use replicate trajectories and the Messerly double-exponential running-integral
fit with bootstrap 95% CI.

Scoring: each molecule is scored only against **measured** liquid viscosity and
thermal conductivity from DIPPR 801 (properties LVS, LTC) and NIST ThermoData
Engine, plus vendor datasheets for commercial coolants (Castrol ON DC 15,
Shell MIDEL 7131). The object of study is the force-field error distribution
and the Spearman rank correlation between MD and measurement.

Benchmark set: C10–C50 hydrocarbons (n-alkanes, iso-alkanes, PAO-type
oligomers) and esters (fatty-acid esters, triglycerides, polyol esters), the
chemistry of mineral-oil / synthetic-ester single-phase immersion coolants,
plus the known commercial coolants (a modelled composition) — fluorinated fluids
are out of scope.

## Baseline
The published state is a handful of molecules: Messerly et al. 2018 scored
Green–Kubo viscosity of 14 normal and branched alkanes against reference data
(and found TraPPE-UA deviations of 20–50%). We enlarge to ~60 molecules within
budget and report the error distribution and rank correlation, which no prior
work does.

## Anchor / check it is right
Before spending on the enlarged set, reproduce the published n-hexadecane
Green–Kubo result: thermal conductivity ≈ 0.14 W/(m·K), which the source paper
checked against its own experiments. Gate: MD anchor must be ≥ 0.10 W/(m·K);
if not, stop and switch force field (e.g. TAMie) before the main spend.
Additional checks: 5-seed bootstrap CI per molecule; GK running integral must
plateau (trajectory ≥ ~10× plateau time); finite-size check (~250 vs ~1000
molecules); density within 2% of measured at the scoring temperature; cost
guard (GPU-hours × $1.99 ≤ $1,000).

## Phases and cost (Lambda, 8×A100 SXM 40GB @ $1.99/GPU-hour)
- p1 anchor: 5 molecules, 40 GPU-hours → $79.60. Gate on anchor ≥ 0.10 W/(m·K).
- p2 enlarged benchmark: time box of 440 GPU-hours (~55 wall-clock hours on 8
  GPUs) → $875.60; stop when $1,000 is exhausted or 60 molecules are done.
  ~55 extra molecules at 8 GPU-hours each (100 ns / 12.5 ns·h⁻¹).
- p3 analysis + filesystem: storage 60 GiB × 1 month × $0.20 = $12.00.

Totals: $967.20 stated, $1,000 hard cap, ~$32.80 headroom.
What the money buys: 60 molecules scored, 300 replicate trajectories,
6,000 ns sampled.

## Scaling / restructuring
Embarrassingly parallel: each molecule is an independent run, so GPUs only run
molecules side by side. The only sequential part is within one trajectory — one
Green–Kubo integral accumulated step-by-step over ~50 million 2-fs steps. This
is not restructured (method: none).

## Sensitivity
- Pessimistic (throughput 150 ns/day): ~25 extra molecules fit.
- Optimistic (throughput 600 ns/day): ~110 extra molecules fit.
Full "hundreds" target (200 molecules) costs ~$3,224 — outside budget.

## Outside budget
- ~20 hours of researcher time (protocol, analysis, report).
- DIPPR 801 database license (measured values).

## Numbers (see record; DERIVED expressions live in the JSON)
gpu_hours_per_molecule = 100 / (300/24) = 8.0; usd_per_molecule = 8.0 × 1.99
= 15.92; total_stated = 79.60 + 875.60 + 12.00 = 967.20.
