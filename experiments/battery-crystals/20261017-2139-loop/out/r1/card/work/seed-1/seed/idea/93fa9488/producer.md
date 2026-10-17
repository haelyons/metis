# V1 — Conductivity-conditioned generation of disordered Li-halide solid electrolytes

Working plan (producer.md). Budget: `budget_usd` = $1,000 of Lambda on-demand GPU credit.

## What to build

A three-arm hit-rate test inside the Li3MX6 halide family (M = group-3/13/15 + lanthanides, X = halogen):

- **A1 conditioned** — fine-tune MatterGen's adapter on *predicted* ionic conductivity labels, then sample
  the Li3MX6 halide space targeting high conductivity.
- **A2 unconditioned** — the base MatterGen model sampling the same Li3MX6 chemical space with no
  property condition (the baseline).
- **A3 ICSD screen** — enumerate known Li-halide solid electrolytes from ICSD and screen them with the
  same conductivity surrogate (the "existing knowledge" baseline).

The measured quantity is **hit rate** = fraction of screened candidates whose predicted room-temperature
conductivity is ≥ 1 mS/cm (10^-3 S/cm), the threshold the DTU paper cites for competitive halides
(`s_dtu_conduct`).

Compute axis: candidate structures screened per arm — levels 1,000 / 10,000 / 100,000.

The question the money answers: does halide-domain conductivity conditioning move the conditioned-vs-
unconditioned hit-rate gap outside seed noise, and does the gap widen as more candidates are screened?

## Pipeline (execution order)

1. **p0_pilot** — download MatterGen base + MACE-MP-0b2 checkpoints and a DTU-DB subset; reproduce two
   anchors; measure real throughput. Anchors: MatterGen 38.57% S.U.N. on 1,024 unconditional samples
   (`s_mattergen_sun`); MACE-MP-0b2-large halide fine-tune energy RMSE ~10.0 meV/atom (`s_dtu_mace`).
   Also measure actual `gen_rate` (struct/GPU-h) and MACE step time on the chosen GPU, which gate the
   big spend.
2. **p1_labels** — fine-tune MACE-MP-0b2-large on a DTU-DB subset (anchor), run MLIP-MD on a
   calibration set of 80 structures to get predicted 600-K Nernst-Einstein conductivity, train a
   lightweight GNN surrogate on those 80 labels, validate (Pearson r ≥ 0.6), then apply the surrogate
   to label 10,000 DB structures for the adapter.
3. **p2_adapter** — fine-tune the MatterGen adapter on the 10,000 surrogate labels (classifier-free
   guidance target = high log-conductivity).
4. **p3_generate** — generate candidates for A1 and A2 at 1k / 10k / 100k (222,000 structures total);
   A3 is a fixed ICSD look-up (~2,000 structures).
5. **p4_screen** — supercell + site-disorder sampling per the DTU recipe, then surrogate screening of
   every candidate; dedupe; compute per-arm/level hit rates.
6. **p5_neb** — MLIP-NEB (fine-tuned MACE) on the top-10 candidates per arm (30 paths), anchored to the
   published 619-value DFT barrier dataset (`s_neb_dataset`).
7. **p6_analyze** — bootstrap CIs over seeds; apply the decision rule.

The ≤20-atom limit (`s_mattergen_20atoms`) is not disqualifying: Li3MX6 is 10 atoms/formula unit, so
20-atom cells cover 2 formula units. Fast conduction lives in the partially-occupied supercells, which
are built by site-disorder sampling before screening (as the DTU DB itself does).

## How to check it's right

- Anchor: reproduce MatterGen 38.57% S.U.N. and MACE-MP-0b2 halide fine-tune ~10 meV/atom.
- Surrogate gate: predicted-vs-MD conductivity Pearson r ≥ 0.6; else expand calibration (L2b) and cut
  the 100k level to 50k to stay under budget.
- NEB sanity: top-candidate migration barriers must rank consistently with the surrogate conductivity.
- Correctness is scored against the unconditioned arm (same seeds, same surrogate) and the ICSD arm.

## Cost (rates read 2026-10-17)

- A6000 48 GB, 1 GPU, $1.09/GPU-h (`s_pricing_a6000`) — generation, MD, screening, NEB.
- A100 SXM 40 GB, 1 GPU, $1.99/GPU-h (`s_pricing_a100`) — the two fine-tunes.

| line | what | rate | hours | usd |
|---|---|---|---|---|
| L0 | pilot + anchors + throughput | A6000 | 10 | 10.90 |
| L1 | MACE-MP-0b2-large fine-tune | A100 | 20 | 39.80 |
| L2 | MLIP-MD calibration (80 × 2.14 h) | A6000 | 171 | 186.6 |
| L3 | train surrogate + label 10k | A6000 | 4 | 4.36 |
| L4 | MatterGen adapter fine-tune | A100 | 20 | 39.80 |
| L5 | generation (222k / 500 per h) | A6000 | 444 | 483.96 |
| L6 | screen + dedupe | A6000 | 4 | 4.36 |
| L7 | MLIP-NEB top-10 × 3 arms | A6000 | 10 | 10.90 |
| L8 | storage 200 GiB × 0.5 month | — | — | 20.00 |

Base total ≈ **$800.7**; hard stop **$1,000**. Optional L2b (calibration expansion, +171 h ≈ $186.6)
runs only if the surrogate gate fails, landing at ≈ **$987.3**, still under cap.

## Key numbers and their basis

- gen_rate = 500 struct/GPU-h — PROXY from `s_mattergen_genrate` ("Sampling 1,000 structures takes
  around two hours using a single NVIDIA V100 GPU"), run on A6000 (≥ V100) — measured in p0_pilot.
- mace_step_ms = 44.2 ms/step (MACE-large, 138 atoms, Torch+ASE on H100) — PROXY from `s_mace_step`,
  scaled to 200-atom supercell on A6000 (×2.0) — measured in p0_pilot.
- md_hours_per_label = 60,000 steps × 44.2 ms × (200/138) × 2.0 = 2.14 GPU-h (120 ps at 2 fs).
- adapter label count = 10,000 (MatterGen's card: "at least several thousands of labeled structures",
  `s_mattergen_labels`); MatterGen also fine-tuned on ML-predicted labels (`s_mattergen_mlpred`).
- hit threshold = 1 mS/cm (`s_dtu_conduct`).

## Why conditioning should be the lever

MatterGen's adapter moved bulk-modulus generation to an extreme tail with only 5,000 labels
(`s_mattergen_5000`), and its discovery rate keeps rising while screening saturates with budget
(`s_mattergen_saturate`). If that transfers to conductivity, A1's hit rate should exceed A2's, and the
gap should widen with candidate count. if_not: the gap stays within seed noise at every level.

## What this cannot show

- Only MLIP-predicted conductivity (no DFT/AIMD ground truth; no VASP on Lambda GPU) — NEB validation is
  MLIP-NEB anchored to the 619-value DFT barrier set.
- No experimental synthesis or impedance measurement.
- Halide family only.
