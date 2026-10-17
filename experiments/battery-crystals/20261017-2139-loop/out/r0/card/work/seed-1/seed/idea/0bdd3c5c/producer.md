# Battery crystal discovery (B1) — concrete plan

Root question: "Battery crystal discovery? Crystal foundation models: there's hella, for battery generation, transport properties are different."

## The claim to test

Crystal foundation models (MatterGen, CDVAE, etc.) generate *stable* inorganic crystals conditioned on ground-state scalar properties — formation energy, band gap, bulk modulus, magnetic density. Battery performance hinges instead on **transport**: ionic conductivity, which is governed by point defects and migration barriers, not the ideal crystal's ground-state properties, and whose experimental labels are scarce (a few hundred compositions vs. 600k+ structures for stability). This plan tests whether a crystal foundation model can be re-aimed at transport: fine-tune the open-source **MatterGen** diffusion model's adapter modules on a *predicted ionic-conductivity proxy*, then measure whether the conditioned generator produces lower-migration-barrier battery electrolytes at a higher hit rate than (a) unconditioned generation plus screening and (b) exhaustive database screening.

Closest prior: **Ferrogen** (NeurIPS 2026) fine-tuned MatterGen on a polarization proxy with ML labels and adapter layers, reporting ~80× search efficiency over exhaustive database search for ferroelectrics — but never targeted ionic conductivity.

## What to build

A five-phase pipeline (all code is open; MatterGen is MIT, ship a fine-tuning entry point):

1. **p_data** — Download the released `mattergen_base` checkpoint and the npj lithium-conductor dataset (820 entries, 403 unique room-temperature compositions). Map compositions to ICSD/MP structures. Anchor: reproduce MatterGen's published 38.57% S.U.N. rate and 0.021 Å RMSD on 1,024 samples.
2. **p_predictor** — Train a composition-only ionic-conductivity regressor/classifier (CrabNet/RF, as in the npj paper) to serve as both the fine-tuning label and the cheap screen. Anchor: hold-out MAE should land near the published 0.85 log10 σ.
3. **p_finetune** — Fine-tune MatterGen's adapter conditioned on predicted log10 σ using classifier-free guidance (the bulk-modulus recipe used only 5,000 labels; we have ~400).
4. **p_generate** — Generate and screen three arms at candidate levels 1k / 10k / 100k: (A) conditioned, (B) unconditioned MatterGen, (C) exhaustive screen of the 6,972 Li compositions in ICSD.
5. **p_validate** — Cheap CHGNet fine-tuned NEB on the top-50, then DFT-NEB on the top-10; compare migration barriers against published values (LiTi2(PO4)3 0.41 eV, LATP 0.19 eV) and the 621-value DFT-NEB dataset.

## Baseline

Arm B (unconditioned MatterGen + the same predictor) and arm C (exhaustive screening of 6,972 Li ICSD compositions, ranked by the predictor). The known-conductor population has median log10 σ = −4.41 S/cm; the target threshold is ≥ −4 S/cm.

## How to check it's right

- Anchor 1: released checkpoint reproduces 38.57% S.U.N. / 0.021 Å RMSD.
- Anchor 2: predictor 5-fold MAE within ±0.1 of the published 0.85 log10 σ.
- Anchor 3: CHGNet-NEB reproduces LiTi2(PO4)3 ≈ 0.41 eV; top-candidate barriers compared with published DFT-NEB values.
- Decision: at 100k candidates, the conditioned arm's hit rate (predicted log10 σ ≥ −4) must exceed both baselines by ≥2×, and its top-10 median CHGNet-NEB barrier must be ≥0.1 eV below the best baseline's.

## Cost (Lambda on-demand, read 2026-10-17)

| line | phase | rate | hours | GPU·h need | cost |
|---|---|---|---|---|---|
| storage 100 GiB | — | fs $0.20/GiB-mo | — | — | $20.00 |
| anchor | p_data | A100 SXM 40GB ×1 $1.99 | 2 | 2 | $3.98 |
| predictor | p_predictor | A10 ×1 $1.29 | 10 (box) | 6 | $12.90 |
| fine-tune | p_finetune | A100 SXM 40GB ×1 $1.99 | 24 (box) | 4 | $47.76 |
| generate+screen 200k | p_generate | V100 16GB ×8 $0.79 | 50 | 400 | $316.00 |
| CHGNet-NEB top-50 | p_validate | A100 SXM 40GB ×1 $1.99 | 8 (box) | 5 | $15.92 |
| DFT-NEB top-10 | p_validate | A100 SXM 40GB ×1 $1.99 | 80 (box) | 80 | $159.20 |
| **total** | | | | | **$575.76** |

Hard stop $1,000. Pessimistic scenario (2× slower sampling on V100, 12 GPU·h/DFT-NEB) lands at ~$971.

## Key numbers and sources

- MatterGen: 46.8M params; one 600k-sample epoch ≈ 6 min on 8× A100; sampling 1,000 structures ≈ 2 h on one V100; 38.57% S.U.N., 0.021 Å RMSD (MODEL_CARD).
- MatterGen fine-tuned on only 5,000 labeled structures (bulk modulus, target 400 GPa) (paper).
- npj Li-conductor dataset: 820 entries / 214 sources; 403 unique RT compositions; MAE 0.85 log10 σ; MCC 0.63; median log10 σ −4.41; 6,972 Li compositions in ICSD.
- Ferrogen: ~80× search efficiency over exhaustive search (polarization, PROXY).
- CHGNet fine-tuned NEB agrees with AIMD (0.21 vs 0.22 eV); LiTi2(PO4)3 barrier 0.41 eV, LATP 0.19 eV.
- Migration-barrier dataset: 621 DFT-NEB values / 443 compositions.
- Lambda rates: V100 16GB $0.79, A100 SXM 40GB $1.99, A10 $1.29 (per GPU/hr); filesystem $0.20/GiB-mo.

## Restructuring

The loop (fine-tune→generate→screen→validate) is sequential across ~3 rounds, and each diffusion sample denoises ~1,000 timesteps; but the expensive work inside each round — generating thousands of candidates, screening them, NEB-validating them — is embarrassingly parallel, so the plan splits each step across GPUs rather than reordering. method = none.
