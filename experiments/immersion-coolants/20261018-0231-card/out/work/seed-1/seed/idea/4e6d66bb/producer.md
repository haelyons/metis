# IC-V3 — MD verification inserted into Org-Mol's ester shortlist before synthesis

## Question

Does adding Green–Kubo molecular-dynamics verification of viscosity and thermal
conductivity *reorder* the machine-learning (ML) ester shortlist, or merely *confirm*
it, and does the best cooling figure of merit keep climbing as more candidates are
verified (100 → 300 → 1000)?

## Background (cited)

The Org-Mol paper (Qi Ou et al., *npj Computational Materials* **11**, 224 (2025),
open access) screened >6 million saturated mono-/di-esters with a 3D-transformer model
and retained **461 monoesters** that pass dielectric constant < 3.20, kinematic
viscosity < 12 cSt at 40 °C, thermal conductivity > 0.140 W/m·K, ≤ 30 carbons:

> "Based on the aforementioned criteria of the kinematic viscosity and thermal
> conductivity, 461 monoesters are finally filtered out."

Only **two** were synthesized and measured (Table 4). The ML predictor's test-set
accuracy (Table 2) is: kinematic viscosity @40 °C MAE **0.568 cSt**, **MAPE 22.467 %**;
thermal conductivity MAE **3.878E-03 W/m·K**, MAPE **2.911 %**. So viscosity is where the
ML model is weakest, and it is viscosity that dominates the cooling figure of merit's
spread (the shortlist spans ~1–12 cSt). The paper itself notes MD is "unaffordable in a
high-throughput screening scenario with thousands of candidates" — which is exactly the
gap this option closes at 100–1000 candidates.

## What to build

A screening pipeline that, for each candidate of the 461-monoester shortlist:
1. builds a ~20,000-atom liquid box (~500 molecules) at 40 °C / 1 atm,
2. assigns **OPLS-AA** parameters (chosen over GAFF: Smith & Sega 2025 find OPLS gives
   strong linear agreement with measured shear viscosity and "slightly better
   performance compared to GAFF"; raw GAFF viscosity is much worse),
3. runs 3 ns equilibration then **3 independent replicas × 5 ns NVT production**,
4. computes viscosity (pressure-tensor ACF, Green–Kubo) and thermal conductivity
   (heat-flux ACF, `gmx tcaf`) with block-averaged standard errors across the 3 replicas,
5. ranks candidates by the **Mouromtseff number** Mo = ρ^a·k^b·cp^d / μ^e (turbulent
   forced-convection exponents, a=0.8, b=0.67, d=0.33, e=0.47), the standard
   single-phase-coolant figure of merit ("the liquid coolant with the largest Mouromtseff
   number will provide the highest heat transfer rate").

Per-candidate cost: 18 ns total; at the A100 proxy throughput 267.5 ns/day that is
1.61 GPU-h → $3.21/candidate at $1.99/GPU-h.

## Baseline

Org-Mol's ML-predicted shortlist (461 monoesters ranked by predicted ν@40 °C and κ),
with MAE 0.568 cSt / MAPE 22.5 % on viscosity — the ranking MD is inserted before.
Scoring is **only** against measured data (never against the predictors): Org-Mol's two
measured esters and the commercial fluid 3M Novec 649.

## How to check it is right

- **Anchor (sanity):** MD reproduces Org-Mol's measured values for Ester 1 (ν@40 °C
  6.41 cSt, κ 0.141 W/m·K) and Ester 2 (9.67 cSt, 0.138 W/m·K) within ±25 % (ν) / ±20 % (κ).
- **Gate before the main spend:** the MD viscosity MAPE on those two esters must be
  ≤ 22.467 % (Org-Mol's own MAPE); otherwise MD adds nothing and the run stops.
- **Plateau check:** each candidate's Green–Kubo integral must plateau inside 5 ns.
- **Noise check:** split each candidate's replicas into halves; two independent
  half-estimates must give the same ranking; rerun 10 candidates at 3× length + new seeds.
- **Competitiveness:** top candidates' Mouromtseff number vs Novec 649 (0.40 cSt,
  0.059 W/m·K, 1103 J/kg·K, 1600 kg/m³).

## Decision rule

At 300 candidates: if Spearman(MD Mo-rank, ML Mo-rank) < **0.7** and the best MD
Mo rises ≥ **5 %** from 100 → 300, then MD reorders (if_lever); else it confirms (if_not).

## Phases (execution order)

| id | what | gate |
|---|---|---|
| build | extract 461 SMILES, rank by ML Mo, build ~20 k-atom boxes, OPLS-AA, minimize (CPU) | — |
| anchor | Ester 1 + Ester 2, 5 reps × 10 ns Green–Kubo; benchmark real ns/day on the ~20 k-atom box | — |
| verify_100 | top-100 candidates, 18 ns each, 8 at a time | MD MAPE ≤ 22.467 % |
| verify_300 | candidates 101–300 | measured ns/day ≥ 150 |
| verify_1000 | candidates 301–1000 (full-scale, outside $1000) | best-Mo ratio 300/100 ≥ 1.05 |

## Restructuring (parallel vs sequential)

- Sequential version: one **45 ns** trajectory per candidate (3×15 ns concatenated) on a
  single A100, tuned with `gmx mdrun -nb gpu -pme gpu -bonded gpu -update gpu -ntmpi 1`.
- Parallel version: 3 × 5 ns replicas per candidate on separate GPUs, block-averaged.
- Both timed on the anchor esters. Condition (cheap check): viscosity from 3 vs 6
  replicas must agree within the standard error, confirming 1/√N replica scaling.

## Cost (8× A100 SXM 40 GB node, $1.99/GPU-h)

- anchor: 112 ns → $20.0
- top-100: 100 × 18 ns → 161.5 GPU-h → $321.4
- candidates 101–300: 200 × 18 ns → 323.0 GPU-h → $642.8
- storage: ~$0.03
- **total ≈ $984** (hard cap $1,000)
- full-scale top-1000 (301–1000 extra): +700 × $3.21 ≈ **$2,250**
- full-scale 1000 candidates at 100 ns each (5× longer): ≈ **$17,900**

## Numbers and their basis

- `shortlist_n=461` CITED (Org-Mol). `ml_nu_mae=0.568 cSt`, `ml_nu_mape=22.467 %`,
  `ml_k_mae=3.878E-03 W/m·K` CITED (Table 2). `anchor_e1_nu=6.41`, `anchor_e1_k=0.141`,
  `anchor_e2_nu=9.67`, `anchor_e2_k=0.138` CITED (Table 4). `novec_nu=0.40`,
  `novec_k=0.059` CITED (3M datasheet). `a100_usd_gpu_h=1.99`, `node_gpus=8` CITED
  (Lambda pricing).
- `a100_ns_day=267.5 ns/day` PROXY (NHR@FAU GROMACS 2024, system 1 "R-143a in hexane",
  20,248 atoms — closest published liquid benchmark; measured_by anchor, gate ≥ 150).
- `ns_per_candidate=18 ns`, `rep_count=3`, `prod_ns_rep=5`, `equil_ns=3`, `n_100=100`,
  `n_300=300`, `n_1000=1000`, `anchor_ns=112` DESIGN.
- `gpu_h_per_candidate`, `usd_per_candidate`, `usd_anchor`, `usd_100`, `usd_300_extra`,
  `usd_1000_extra`, `usd_storage`, `ns_simulated_300` DERIVED.
- `md_mape_anchor=15 %` GUESS (measured_by anchor, gate ≤ 22.467); `ns_day_measured=267.5`
  GUESS (measured_by anchor, gate ≥ 150); `fom_climb_ratio=1.08` GUESS (measured_by
  verify_300, gate ≥ 1.05).

## Limits / scope gap

Single-phase ranking under one force field and 15 ns sampling; no synthesis, dielectric,
flammability, material-compatibility, or long-term-stability checks; the 1000-candidate
and longer (100 ns) runs exceed the $1,000 budget.

## Closest prior

Org-Mol screened 461 monoesters and measured two by synthesis; none were MD-verified for
viscosity/thermal conductivity (prior max level = 0 MD-verified candidates). Smith & Sega
2025 is the nearest *parallel Green–Kubo* precedent (140 liquids, ~10 × 10 ns blocks).
