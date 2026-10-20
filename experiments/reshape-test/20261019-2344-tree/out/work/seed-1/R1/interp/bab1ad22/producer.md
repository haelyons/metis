# Plan: Linear feature representation -> parallel-in-time for free

Option: **SAE features give the linear basis that triggers the framer's no-forgetting parallel-in-time exception**.

## What is being tested

The framer's §2.3 exception: for a linear map `x_{t+1} = A x_t`, the final state `x_T = A^T x_0` is computable in `O(log T)` depth by repeated squaring / diagonalisation (ParaDiag/ParaExp), with **no forgetting needed**. Goodfire-style SAEs supply the linear decomposition of the residual stream. The open question this plan answers: **is the per-layer feature-to-feature transition linear and time-invariant enough to compose out of order across full model depth?**

Concretely, for a transformer we have, at each layer `l`, a residual-stream state `x_l ∈ R^d`. An SAE decomposes it as `x_l ≈ D_l c_l` (sparse features). The claim is testable as: does a single linear map `A_l` satisfy `c_{l+1} ≈ A_l c_l` (feature basis), and does `A_42 ... A_1 c_0` (composed out of order by repeated squaring) track the true `c_42`?

## The measurement

1. **Forward pass (ground truth + data).** Run Gemma 2 9B and LLaMA-2 7B autoregressively over 2,000,000 tokens (1,953 sequences × 1024 tokens), caching residual-stream activations at all layers.
2. **Encode.** Encode residuals through Gemma Scope SAEs at widths 16.4K (all 42 layers), 131K (all 42 layers), and 1M (layers 9/20/31).
3. **Fit.** Per layer, fit the linear feature transition `A_l` on 1,500 train sequences; report per-layer R² and the train/held-out gap (time-invariance).
4. **Compose.** Compose `A_l` out of order (repeated squaring / diagonalisation) to depth 1/10/20/30/42; score composed reconstruction R² against the sequential truth on 453 held-out sequences.
5. **Width sweep.** Repeat at 16.4K and 1M widths; also the d_model-basis (4096) direct linear probe on LLaMA-2 7B, no SAE.

## Decision rule

`if_lever` iff the composed out-of-order prediction reconstructs **≥ 90%** of true next-layer activation variance, averaged over all 42 layers and held-out contexts. Below 90% (and decaying with depth) is `if_not`.

## Anchor

Before trusting the linearity fit: (a) the SAE encoder-decoder round-trip must reproduce the released weights' reconstruction to relative error < 1e-5; (b) the composition code must match sequential on a synthetic linear system to < 1e-8 (pilot script). Context for "good reconstruction": the published 34M-feature SAE explains at least 65% of activation variance.

## Cost

One 8× H100 SXM instance ($3.99/GPU/hr → $31.92/hr). Four 2-hour time-boxed lines + storage.

| line | purpose | hours | cost |
|---|---|---|---|
| line_setup | downloads, env, micro-benchmark | 2 | $63.84 |
| line_forward | forward pass + SAE encode (all widths) | 2 | $63.84 |
| line_analyze | fit + compose + width analysis | 2 | $63.84 |
| line_headroom | re-runs, more tokens, longer context | 2 | $63.84 |
| line_storage | 50 GiB filesystem (1 month) | — | $10.00 |

**Total stated: $265.36** against a $1,000 cap. The dominant cost is setup + iteration headroom; the actual FLOP work is ~0.6 GPU-hours (DERIVED below), so this test is **not compute-bound** — matching the framer's verdict.

## Key numbers

- Gemma 2 9B: 42 layers, d_model 3584 (arxiv 2408.00118).
- LLaMA-2 7B: 32 layers, d_model 4096 (HF LlamaConfig).
- Gemma Scope 9B residual SAEs: 16.4K and 131K at all 42 layers; 1M at layers 9/20/31 (arxiv 2408.05147).
- Published SAE record: 33,554,432 (~34M) features, ≥65% variance, one middle layer of Claude 3 Sonnet (transformer-circuits 2024).
- Closest prior (Activation Transport Operators, arxiv 2508.17540): per-feature R² of linear maps between layers, up to 10-layer leaps, < 50 GPU-h; adjacent-layer R² > 0.95, decays with distance.
- H100 SXM: TF32 Tensor Core 989 TFLOPS with sparsity (1/2 lower without → 494.5 dense); I use 200 effective TFLOPS/GPU.
- Total FLOPs ≈ n_tokens × (4·d·(42·(16.4K+131K) + 3·1M) + 2·(9B+7B)) ≈ 3.3e17 → ~0.6 GPU-h at 200 TFLOPS on 8 GPUs with 10× overhead.

## Pilot (free, local)

`pilot/compose_check.py` verifies repeated-squaring == sequential on a synthetic linear system and benchmarks the least-squares fit. Run before any Lambda spend.

## Full-scale (what $1,000 cannot buy)

- Train 34M-feature SAEs across all 42 layers of an open 70B model and rerun the test (~$38,400 est.).
- Repeat the 131K all-layer sweep on three more open model families (~$1,200).

## Outside budget

Human engineering (40 h), analysis/write-up (20 h), desk review (8 h) — unpaid, outside Lambda.
