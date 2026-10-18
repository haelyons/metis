# IC-V3 — MD verification inserted into Org-Mol's ester shortlist before synthesis

## Question

Does Green-Kubo molecular-dynamics verification of viscosity and thermal conductivity
*reorder* a machine-learning ester shortlist, or merely *confirm* it, and does the best
cooling figure of merit keep climbing as more candidates are verified (100 → 300 → 1000)?

## What to build

A screening pipeline that, for each of the 461 monoesters Org-Mol's transformer screen
retained ("Based on the aforementioned criteria of the kinematic viscosity and thermal
conductivity, 461 monoesters are finally filtered out" — nature.com/articles/s41524-025-01720-4):

1. rebuild the shortlist from the paper's criteria (dielectric < 3.20, viscosity < 12 cSt
   at 40 °C, thermal conductivity > 0.140 W/m·K, ≤ 30 carbons, saturated monoesters),
2. build a ~15,000-atom liquid box (the same size class as the closest prior,
   Ogbomo et al. 2026, "approximately 15 000 atoms per box"),
3. assign LOPLS-AA parameters (the closest prior's force field for exactly this property
   pair: "All simulations were performed using the LOPLS-AA force field"),
4. run 3 ns equilibration then 3 independent replicas × 5 ns NVT production,
5. compute viscosity (pressure-tensor Green-Kubo) and thermal conductivity (heat-flux
   Green-Kubo), block-averaged across replicas,
6. rank by the Mouromtseff figure of merit — the coolant with the largest value gives the
   highest heat transfer ("the liquid coolant with the largest Mouromtseff number will
   provide the highest heat transfer rate" — electronics-cooling.com/2006/05/...).

Per candidate: 18 ns total. At the A100 proxy throughput 267.5 ns/day that is 1.61 GPU-h
→ $3.21/candidate at $1.99/GPU-h.

## Baseline

Org-Mol's machine-learning ranking of the 461 monoesters — viscosity MAE 0.568 cSt,
MAPE 22.467 % (Table 2) — the ranking MD is inserted before. Scoring is only against
measured data, never against the predictors: Ester 1 (6.41 cSt, 0.141 W/m·K) and Ester 2
(9.67 cSt, 0.138 W/m·K) from Table 4, and 3M Novec 649 (0.40 cSt, 0.059 W/m·K).

## How to check it is right

- **Anchor**: Green-Kubo MD reproduces Ester 1's measured 6.41 cSt and 0.141 W/m·K within
  ±40 % (the documented LOPLS-AA error is about a factor of 1.4), and the parallel-replica
  result agrees with a sequential single trajectory within one standard error.
- **Gate before the main spend**: MD's viscosity MAPE on the two anchor esters must be
  ≤ 22.467 % (Org-Mol's own MAPE); otherwise MD adds nothing and the run stops.
- **Noise**: 10 candidates rerun at 3× length with new seeds; the MD ranking must be stable
  (Spearman ≥ 0.95); every candidate carries a block-averaged standard error.
- **Competitiveness**: top candidates' Mouromtseff figure vs Novec 649.

## Decision rule

At 300 candidates: if Spearman(MD rank, ML rank) < 0.7 and the best MD figure at 300 is at
least 5 % higher than at 100 (ratio ≥ 1.05), MD reorders (if_lever); otherwise it only
confirms (if_not).

## Phases

| id | what | gate |
|---|---|---|
| build | rebuild the 461 SMILES, build boxes, assign LOPLS-AA, minimize | — |
| anchor | Ester 1 + Ester 2 (5 reps × 8 ns) + one 24 ns sequential trajectory; measure real ns/day and MD MAPE; time replicas vs sequential | md MAPE ≤ 22.467 % |
| verify_100 | top 100, 18 ns each, 8 at a time | — |
| verify_300 | candidates 101–300, same protocol | measured throughput ≥ 264 ns/day |
| verify_1000 | candidates 301–1000 (full-scale, outside $1,000) | best figure 300/100 ≥ 1.05 |

## Cost (8× A100 SXM 40 GB, $1.99/GPU-h = $15.92/h node)

- anchor 112 ns → $20.0
- top 100: 100 × 18 ns → $321.4
- candidates 101–300: 200 × 18 ns → $642.8
- storage ~$0.03
- **total ≈ $984** (cap $1,000)
- full-scale 301–1000: +700 × $3.21 ≈ $2,250
- full-scale 1000 at 100 ns each (5× longer): ≈ $17,900

## Closest prior

Ogbomo, Carman, Dini, Ewen, *Digital Discovery* (2026) ran Green-Kubo EMD on **eight**
organic liquids (two esters) at 40 and 100 °C with LOPLS-AA, finding viscosity ranking
largely preserved but thermal conductivity misordered (n=8, the largest MD-verified set).
No work runs Green-Kubo over a 100–1000 candidate ester shortlist.
