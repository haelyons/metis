# Plan: Active-subspace reparameterization of rainfall-runoff calibration

## Option being planned

"Reparameterize the calibration with active subspaces to shorten the MCMC chain" — identify the few data-informed directions along which the negative log-likelihood varies (the active subspace), run Metropolis-Hastings only on those, and draw the inactive directions independently from the prior [s1]. The question this plan answers: **does the four-parameter GR4J calibration posterior admit a low-dimensional active subspace, and does running MCMC only on it beat both a serial chain and side-by-side chains — and is that verdict itself changed by buying more parallel compute?**

## What to build

1. **Differentiable GR4J forward model in JAX.** GR4J has exactly four calibrated parameters — production-store capacity X1 (mm), groundwater exchange X2 (mm/day), routing-store capacity X3 (mm), unit-hydrograph time base X4 (days) [s10]. Implement the webGR equations (production store, percolation, two unit hydrographs, routing store, groundwater exchange) so that the negative log-likelihood is differentiable w.r.t. all four parameters by automatic differentiation. This gives one forward **plus one adjoint pass** per gradient sample (or two forward evaluations by finite difference) [s7].
2. **Active-subspace estimator.** Draw M independent prior samples; for each compute the misfit gradient ∇f; average the outer products into the matrix Ĉ = (1/M) Σ ∇fᵢ∇fᵢᵀ; eigendecompose. Report the eigenvalue spectrum λ1..λ4 and the spectral gap. This is the standard Monte Carlo estimator [s8].
3. **Active-subspace MCMC.** Metropolis-Hastings on the n active variables (n = 1 or 2, chosen by the eigenvalue gap), with the per-step approximate likelihood ĝ(y) = (1/Mg) Σ f(W1·y + W2·zᵢ) using Mg = 10 conditional-average samples, and P = 10 independent prior draws on the inactive variables per reconstructed parameter [s1, s14]. Reconstruct the 4-D chain x = W1·y + W2·z.
4. **Two baselines.** (a) *serial*: JAX-compiled random-walk Metropolis on all four parameters, proposal variance tuned to ~25% acceptance, 500,000 forward evaluations (the same budget the published comparison used) [s4]. (b) *copies*: independent vanilla chains started from dispersed points, one per GPU, run side by side.
5. **Metric.** Minimum effective sample size (ESS) per component via the autocorrelation sum N/(1+2Σρₖ), exactly the published definition [s5], reported per forward evaluation and per wall-clock hour.

## Baseline

Vanilla random-walk Metropolis on all four GR4J parameters at 500,000 forward evaluations. In the published 100-parameter analogue this baseline reaches a minimum ESS of 604 while the active-subspace-accelerated chain reaches 81,986 at the same evaluation budget [s5]. The GR4J comparison reuses the identical budget and definition; the only differences are the 4-parameter forward model and the artificial bimodality that cheap fixed-step integration is known to inject [s9].

## How to check it is right

1. **Anchor — reproduce the published two-parameter quadratic.** Forward model m(x) = ½·xᵀAx with A = Q·diag(1, ε)·Qᵀ, Q = ½[[√2,√2],[−√2,√2]], noise σ² = 0.1, data d = 0.9 [s1]. With ε = 0.01 the paper reports "the gap between the eigenvalues suggests an active one-dimensional active subspace" [s6]; with ε = 0.95 there is no gap. My estimator must recover λ1/λ2 ≳ 100 at ε = 0.01 and λ1/λ2 ≲ 10 at ε = 0.95, matching the published scripts (bitbucket.org/paulcon/accelerating-mcmc-with-active-subspaces). Failing this stops the spend.
2. **Forward-model check.** The JAX GR4J must reproduce the webGR equations verbatim and match the airGR reference on a fixed parameter set.
3. **ESS magnitude check.** The accelerated chain's min-ESS jump must reproduce the published 604 → 81,986 magnitude [s5] before I trust the GR4J result.
4. **Bias check.** The accelerated chain's posterior mean and covariance must match a long serial reference chain within a stated tolerance (the Hellinger-distance bound the paper derives [s1]).

## The compute question (what the money actually tests)

The pipeline is four serial steps: draw M gradient samples → average outer products → eigendecompose → run the active-variable chain. The M gradient samples are mutually independent, so they run concurrently across GPUs; only the eigendecomposition and the short low-dimensional chain stay serial. The quantity more parallel compute buys is therefore **M, the number of gradient samples**. The published demos stop at M = 300 (one-dimensional subspace) [s8] and M = 1000 (100-parameter model, two-dimensional subspace) [s3]. The plan sweeps M ∈ {100, 300, 1000, 10000, 100000} on GR4J and asks whether the eigenvalue gap and the accelerated-chain ESS verdict change with M:

- **if_lever**: more samples make the gap appear/widen, so the accelerated chain only beats both baselines at high M.
- **if_not**: the gap is already clear at M = 300, so 100× more samples change nothing — compute is not the lever, the reparameterization is.

Decision rule: compute is the lever only if λ1/λ2 at 100,000 samples is ≥ 2× that at 300, or the accelerated chain's min-ESS at 100,000 is ≥ 2× that at 300; otherwise compute is not the lever. Noise rule: 10 independent prior-sample batches for bootstrap spectral ranges, 3 seeds per MCMC run, differences declared only on non-overlapping ranges.

## Cost

Rates (Lambda on-demand, read 2026-10-20): 1× NVIDIA A6000 (48 GB) at $1.09/GPU/hr [s12]; 8× NVIDIA A100 SXM (80 GB) at $2.79/GPU/hr [s13]. Filesystem ~$0.20/GiB-month.

| line | phase | instance | hours | cost |
|---|---|---|---|---|
| pilot: JAX GR4J + 1000-sample spectral estimate, time it | pilot | 1×A6000 | 2 h (need ≈ 0.5 h) | $2.18 |
| reproduce: two-parameter anchor + ESS comparison | reproduce | 1×A6000 | 2 h (need ≈ 0.5 h) | $2.18 |
| spectrum sweep M∈{100…100000} | spectrum_sweep | 1×A6000 | 2 h (need ≈ 0.2 h) | $2.18 |
| three arms at 500k evaluations | mcmc_compare | 1×A6000 | 4 h (need ≈ 1 h) | $4.36 |
| optional: 671-catchment CAMELS sweep | camels | 8×A100 | 2 h (need ≈ 0.6 h) | $44.64 |
| storage (CAMELS forcing + results, 5 GiB) | camels | — | — | $1.00 |

**Total ≈ $56.54, hard stop $200.** The fact that this sits ~$57 under the $1000 ceiling is itself the answer to the root question: for a four-parameter lumped model the active-subspace computation is not compute-bound. The only line that meaningfully uses parallel GPUs is the 671-catchment sweep, and even that is minutes of GPU time.

## What $1000 cannot buy here

The genuinely compute-bound extension — active-subspace reparameterization of a hundreds-of-parameter distributed model (the high-performance-computing regime the framer names) across all catchments — is out of scope at any price near this budget and is left open.

## Human time / outside budget

~8 hours of my time writing and debugging the JAX pipeline; CAMELS download (a few GiB, free).
