# Plan: Generative search for single-phase immersion coolants (GPU MD verification)

## What to build

A three-stage pipeline that discovers PFAS-free, single-phase immersion coolants and
scores them against known commercial fluids:

1. **Generate + filter (predictor).** Enumerate ~1,000,000 PFAS-free saturated
   monoesters and hydrocarbons (<= 30 carbons) as SMILES. Fine-tune property
   predictors (Org-Mol-style 3D transformer, or XGBoost on fingerprints) for
   dielectric constant, kinematic viscosity, and thermal conductivity on public
   experimental data, holding out known commercial fluids. Rank the generated
   molecules by a predicted Mouromtseff number. Property targets come from the
   Org-Mol screening paper [orgmol] and OCP minimum requirements [ocp]:
   dielectric constant < 3.20, kinematic viscosity < 12 cSt at 40 C,
   thermal conductivity > 0.140 W/m/K, flash point >= 150 C.

2. **Verify by GPU MD.** For the top-ranked candidates (100, then 300, then 1000),
   run equilibrium molecular dynamics with a united-atom force field (Mie Potoff/TAMie
   preferred; TraPPE-UA as fallback) at 313 K, and compute density, shear viscosity
   (Einstein/Green-Kubo), heat capacity, and thermal conductivity (heat-flux
   Green-Kubo). Per candidate: 2 ns equilibration + 2 independent 5 ns production
   replicas = 12 ns total.

3. **Score.** Compute each candidate's Mouromtseff figure of merit for turbulent
   forced convection, Mo = rho^0.8 * k^0.6 * cp^0.4 / mu^0.4 [uh_fom], and the hit
   rate = fraction of MD-verified candidates beating the best commercial baseline.
   Score only against MEASURED data for known fluids (3M Novec 7000 [novec7000],
   n-hexadecane [berger2024][meng2018]), never against the predictors.

## Baseline

Known commercial fluids' published properties, converted to the same Mouromtseff
number:
- 3M Novec 7000 (fluorinated, PFAS, phased out [se_blog]): k = 0.075 W/m/K,
  nu = 0.32 cSt, rho = 1400 kg/m3, cp = 1300 J/kg/K, Dk = 7.4 [novec7000].
- n-hexadecane (PFAS-free hydrocarbon): k = 0.1444 W/m/K at 298.15 K [berger2024],
  eta = 2.9523 mPa s at 300 K [meng2018].

The goal is a PFAS-free ester/hydrocarbon that matches or beats the fluorinated
fluids' cooling figure of merit, or at minimum beats the PFAS-free hydrocarbon
frontier.

## How to check it is right

- **Anchor first:** the MD pipeline must reproduce n-hexadecane k = 0.1444 W/m/K and
  eta = 2.9523 mPa s within +/-25% before any candidate is scored. If it fails,
  switch to a Mie (Potoff/TAMie) force field and rerun once.
- **Predictor holdout gate:** holdout R^2 >= 0.85 on the held-out commercial fluids
  before trusting the filter (Org-Mol reports test R^2 > 0.92 [orgmol]).
- **Never score against predictors:** every candidate-vs-baseline comparison uses MD
  or measured properties only.
- **Noise rule:** 2 replicas per candidate; a level-to-level best-score difference
  counts only if it exceeds the replica-to-replica standard error.

## The compute question

Compute axis = number of candidates verified by GPU MD. More parallel compute =
more candidates verified at once (one candidate per A6000). The test measures the
best-Mouromtseff-number (and hit rate) at 100 / 300 / 1000 verified candidates.

- if_lever: the best score keeps climbing with candidates (more compute finds better
  fluids).
- if_not: the best score plateaus by a few hundred candidates because predictor
  filtering and ~10% force-field error cap how high MD-ranked fluids score
  [messerly].
- Decision rule: if_lever if best-Mo(1000) > best-Mo(100) * 1.05 and keeps beating
  commercial; if_not if best-Mo plateaus within 5% between 300 and 1000.
- Expected: unsure -- no published run has MD-verified thousands of coolant
  candidates.

## Cost (Lambda on-demand, A6000 48GB @ $1.09/GPU/hr)

| line | phase | GPU-hours | USD |
|------|-------|-----------|-----|
| anchor (n-hexadecane reproduction, time box 24h) | anchor | 24 | 26.16 |
| predictor (fine-tune + holdout, time box 16h) | predictor | 16 | 17.44 |
| generate (1M SMILES + ranking, time box 4h) | generate | 4 | 4.36 |
| verify 100 | verify | 74.88 | 81.62 |
| verify +200 -> 300 | verify | 149.76 | 163.24 |
| verify +700 -> 1000 | verify | 524.16 | 571.33 |
| refine top-30 x 50 ns (optional stretch) | verify | 93.6 | 102.02 |
| storage 50 GiB-month | - | - | 10.00 |

Core total = 792.8 GPU-hr = $864.15 + $10 storage = $874.15 (committed).
With optional refine: +$102.02 -> $976.17. Hard cap $1000.

Per-candidate MD cost = (12 ns / (500 ns/day / 24)) x 1.3 = 0.75 GPU-hr
= $0.82. Throughput proxy: GROMACS 2024.1 benchmark, System 2 (31,889 atoms)
= 691.7 ns/day on A100 [gromacs_fau]; I discount to 500 ns/day for margin and use
A6000 (same GA102 chip as the A40, 277 ns/day on System 1).

## Full-scale runs the budget cannot buy

- 10,000 candidates verified: 7,488 GPU-hr = $8,161.92 (the option's 10^4 level).

## Scope gaps

- 10^4-candidate level is unaffordable (curve tested only to 10^3).
- Pure single-component fluids only; mixtures (the option also names them) are not
  screened.
- MD transport properties carry ~10% force-field error, so absolute accuracy is
  capped even at scale.
- No synthesis or experimental validation of top candidates.
