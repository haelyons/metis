# W1 — In-silico enumeration of capsid–receptor complexes (AlphaFold-class sampling)

Working plan for `$1,000` Lambda GPU credit (`budget_usd`), prices read 2026-10-20.
All local files live under `idea/8ff84fa5/`; `pilot/` holds the two checkable scripts.
Note: this planning session had no local shell, so `pilot/*.py` were written but not
executed; every number they would print is basis GUESS with `measured_by` naming the
phase that runs them (`p_probe`), and `p_probe` saves the outputs under `pilot/`.

## 1. What the money buys

A pipeline that enumerates capsid-variant peptide x receptor-ectodomain pairs with
AlphaFold-Multimer-class sampling at three depths (30 / 150 / 480 predictions per
pair), reduces every prediction to a contact fingerprint, and asks one question:
**does deeper sampling collapse onto one interface footprint class that transfers
across variants, or do poses keep alternating?**

Model unit (following the only AAV application, S2, which found full capsids do not
work with AlphaFold-Multimer): capsid variable-region VIII insertion peptide
(AA 585-595) x receptor ectodomain. Grid: 6 peptides (AAV9-VR-VIII, PHP.B, PHP.eB,
PHP.C2, PHP.eC, 9P31) x 6 ectodomains (LY6A, LY6C1, mouse CA4, AAVR PKD2, murine
ALPL, LRP6 beta-propeller-1) = 36 pairs. Sentinels: PHP.eB-LY6A (mutagenesis-
validated) and PHP.C2-LY6C1 (version-sensitive).

Software: LocalColabFold / AlphaPulldown (features once per chain on CPU, then all
seeds x models fanned out on GPUs), AlphaFold-Multimer weights v2.2.0 and v2.1.0
(the two weight sets the AFsample distribution ships), 3 recycles, 5 model parameter
sets. Analysis: residue-residue contacts within 5 A (S2's cutoff), interface-PAE
filter at 10 A, contact-set Jaccard clustering, split-half stability, and a
signature-transfer test (consensus contact set of k pairs of one receptor class
predicting the held-out pair's contacts versus shuffled labels).

## 2. Baseline and how we know it is right

Baseline: one default AlphaFold-Multimer run per pair — 25 predictions (five models x
five seeds) (S3b) — which is what a screening paper would ship. Both this baseline and
a sequential single-GPU implementation versus eight side-by-side copies are timed.

Anchor: our PHP.eB capsid model must reproduce PDB 7WQO (cryo-EM, 2.85 A; S8) within
1.4 A backbone RMSD (S2 reports 0.36 A overall, 1.36 A in the engineered loop) and
must place LY6A A58 within 5 A of the PHP.eB peptide (S2 disrupted infectivity with
LY6A A58R). Secondary check: the 9P31-CA4 pose occupies the CA-IV catalytic pocket
competitive with brinzolamide (S2).

Scored against: those published contact facts and 7WQO, not against each other.

## 3. Compute axis and predictions

Axis: predictions per pair (seeds x 5 models x runs), levels 30, 150, 480. The 480
level matches the largest published subsampled-AF2 depth (32 seeds x 5 models x 3
runs, S1). Depth levels are nested prefixes of one run per sentinel.

- if_lever: at 480 predictions per pair, split-half contact Jaccard >= 0.7 and one
  footprint holds >= 80% of poses, stable across the two weight sets.
- if_not: even at 480, split-half Jaccard <= 0.4 and two footprints alternate, as the
  PHP.C2-LY6C1 pose changed with AlphaFold-Multimer version (S2).
- expected: unsure — S2 reports one mutagenesis-consistent pose (PHP.eB-LY6A) and one
  version-dependent pose (PHP.C2-LY6C1), so convergence looks pair-specific.

Decision rule: at 480/pair, lever if median split-half Jaccard >= 0.7 AND top-footprint
share >= 0.8 on both sentinels; not the lever if Jaccard <= 0.4 or share < 0.5 at every
level; otherwise unsure. Noise rule: three seed splits per level; a difference counts
only if it exceeds 2 x the replicate spread of split-half Jaccard
(`sim_spread_n150`, GUESS 0.10, measured by `p_probe` via `pilot/sim_thresholds.py`).

## 4. Phases, rates, cost

Rates (https://lambda.ai/pricing, read 2026-10-20): 8x NVIDIA A100 SXM 40 GB at
$1.99/GPU-h (`r_a100x8`); 1x NVIDIA A100 SXM 40 GB at $1.99/GPU-h (`r_a100x1`);
filesystem `fs_usd_gib_month` = 0.20.

| id | what | hours (box) | need | usd |
|----|------|-------------|------|-----|
| p_probe | install, MSAs, 6 timed predictions, run pilot scripts | 5 on 1 GPU | 2 + 6*min_per_pred_ours/60 | 9.95 |
| p_anchor | PHP.eB-LY6A 30 preds + PHP.eB vs 7WQO | 8 on 1 GPU | 3 + 30*min_per_pred_ours/60 | 15.92 |
| p_grid | 36 pairs x 30 predictions | 20 on 8 GPUs | preds_grid_total*min_per_pred_ours/60/8 = 18 | 318.40 |
| p_depth | 2 sentinels to 480 | 16 on 8 GPUs | 15 | 254.72 |
| p_version | PHP.C2-LY6C1, 150 preds, 2nd weight set | 6 on 8 GPUs | 5 | 95.52 |
| p_analysis | fingerprints, clustering, signature test, report | 6 on 1 GPU | 3 | 11.94 |
| storage | 50 GiB x 1 month | — | storage_gib*fs_usd_gib_month | 10.00 |
| contingency | reruns / box overruns | — | DESIGN | 150.00 |
| **total_stated** | | | | **866.45** |

`spend_cap_usd` = 1000. Per-prediction time `min_per_pred_ours` = 8 min is a GUESS
bracketed by PROXY 13.5 min (856 protein pairs in over 8 GPU-days on A100 at one
recycle, S4) and PROXY 1.44 min (ColabFold ~1000 structures/day/GPU, S5);
`p_probe` measures it and the gate cuts the grid if it exceeds 25 min.

Total predictions bought: 2280 (1080 grid + 900 depth + 300 version), ~304 GPU-hours.

## 5. What is parallel here

Nothing sequential except one prediction's 3 recycle iterations. Every (pair, seed,
model) is an independent job; features are computed once per chain on CPU and reused
(S9). So restructuring.method = none: the plan runs independent jobs side by side on
the 8 GPUs, with baselines = one A100 running a sentinel's 480 predictions one after
another (64 h) versus eight single-GPU copies.

## 6. Gaps

Predicted footprints cannot show which AAVs transcytose across brain endothelium;
that needs cell/animal assays (S2). Glycan contacts and full-capsid trimer poses are
outside this budget. Prior work: AFsample reached ~6000 models per CASP15 target and
raised mean DockQ 0.41 -> 0.55 versus 25 defaults (S3) but never asked whether a
capsid-receptor footprint converges; that remains open (S2).

## Sources

- S1 https://www.nature.com/articles/s41467-024-46715-9 — subsampled AF2, 480 predictions/test.
- S2 https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422 — APPRAISE-AAV, PHP.eB/PHP.C2/9P31 poses, A58R, 0.36 A vs 7WQO, version-dependent PHP.C2-LY6C1 pose.
- S3 https://pmc.ncbi.nlm.nih.gov/articles/PMC10534052 — AFsample ~6000 models/target, DockQ 0.41->0.55, default 25.
- S4 https://pmc.ncbi.nlm.nih.gov/articles/PMC11513016 — 856 PPIs, >8 GPU-days, A100 SXM6 64GB, 5->1 models saves 4.7x.
- S5 https://www.biorxiv.org/content/10.1101/2021.08.15.456425v3 — ColabFold ~1000 structures/day on one GPU.
- S6 https://lambda.ai/pricing — A100 SXM 40 GB $1.99/GPU-h.
- S7 https://lambda.ai/pricing — filesystem $0.20 per GiB-month.
- S8 https://www.rcsb.org/structure/7WQO — PHP.eB cryo-EM 2.85 A; AAVR PKD2 binds 3-fold protrusions.
- S9 https://pmc.ncbi.nlm.nih.gov/articles/PMC9805587 — AlphaPulldown splits CPU features from GPU prediction.
