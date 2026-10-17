# V1 — Reconcile the GISMo Hit@1 discrepancy, then width sweep

## What this builds

A single modern harness that trains and evaluates GISMo (Meta's Graph-based
Ingredient Substitution Module) and can toggle three protocol knobs, to settle a
concrete discrepancy before any capacity sweep is meaningful:

- Meta's GISMo paper reports **Hit@1 = 20.56 ± 0.14** on Recipe1MSubs test
  (Table 1, averaged over 5 runs) [s1].
- Rita et al. re-ran "the GISMo model" and report **Hit@1 = 34.53 ± 0.10** on the
  "original GISMo dataset" [s10].
- An independent 2026 reproduction (CEUR-WS) reports **Hits@1 = 20.4** for GISMo
  on Recipe1MSubs [s11], agreeing with Meta, not Rita.

The plan: (1) reproduce both numbers in one harness with the official code
ported to modern PyTorch/DGL; (2) change one knob at a time (candidate set, data
split, preprocessing) to attribute the 20.56 → 34.53 gap; (3) then sweep model
width 64–512 under whichever protocol reproduces, and report the width trend
under both.

## Baseline

- Meta GISMo test Hit@1 = 20.56 ± 0.14 (Table 1) [s1]; Rita GISMo Hit@1 = 34.53
  ± 0.10 [s10]; CEUR GISMo Hits@1 = 20.4 [s11].

## Model and data (from sources)

- GISMo = 2 GIN layers + a 3-layer MLP substitution decoder; hidden = emb_d = 300,
  lr 5e-5, weight decay 1e-4, dropout 0.25, nr = 400 negatives per positive,
  max 1000 epochs, early stop on validation MRR [s7][s8][s9].
- Vocabulary = 6,653 ingredients (FlavorGraph-mapped) [s3]; splits 49,044 train /
  10,729 val / 10,747 test [s4]; eval ranks every ingredient in the vocabulary
  minus the source [s5].
- Width sweep lever = hidden and emb_d swept together over {64,128,256,512}.

## How to check it is right

- Anchor: reproduce Meta's 20.56 ± 0.14 with official hyperparameters; accept if
  within ±0.5 pt. CEUR's 20.4 is an independent cross-check [s11].
- Then reproduce Rita's 34.53 under the Rita protocol; if it reproduces, the gap
  is protocol, not implementation, and the isolation grid names the knob.
- The width=300 anchor run in the sweep must match the phase-A reproduction.

## Cost

50 runs total (10 reconcile + 40 sweep), each ~0.5 GPU-h (GUESS, measured in
phase A). On an 8×V100 node ($0.79/GPU-h) with 8-way parallel runs:
reconcile ≈ 1 node-h need (2 h time box), sweep ≈ 2.5 node-h need (3 h time box).
Stated total ≈ $32.60. Spend cap $200. The reconciliation is not compute-bound.

## Sequence (why it is serial)

The width sweep is meaningless until we know which protocol reproduces, so the
plan is: reproduce Meta → reproduce Rita + isolate the knob → sweep. Within each
phase the seed/width jobs are independent and run side-by-side across the 8 GPUs.
