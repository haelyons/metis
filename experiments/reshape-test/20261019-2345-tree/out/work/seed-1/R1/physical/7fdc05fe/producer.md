# Plan: Large-sample multi-catchment calibration (CAMELS)

Option: "Large-sample multi-catchment calibration (CAMELS)".
Root question: what limits Bayesian calibration of rainfall-runoff models (long MCMC chains) — is compute a blocker, and does a shit ton of GPU parallelism fix it?

## What this option claims

CAMELS gives 671 US catchments, each independently calibratable, so the study is embarrassingly parallel. The claim: at CAMELS scale, GPU/cloud throughput directly determines how many catchments get a *proper Bayesian treatment* (MCMC posterior) instead of point optimization. Left open: what extending full Bayesian treatment to all 671 (or globally) would change about large-sample hydrological conclusions.

## What I will build

1. A **GPU-batched GR4J** (4 parameters; Perrin et al. 2003) written in JAX, vectorized over catchments × chains: one forward pass evaluates every chain of every catchment in a single `lax.scan` over the ~7,300-day record. This is the same "many chains on one GPU" pattern shown to scale linearly (ChEES-HMC).
2. A **multi-chain Metropolis sampler (DREAM(ZS)-style, 4 chains/catchment)** that runs all 2,684 chains side by side, with Gelman–Rubin R̂ as the convergence gate.
3. A **point-optimization baseline** (airGR `Calibration_Michel` / SCE-UA), the standard large-sample practice.
4. A **vectorized CPU baseline** (same sampler, JAX CPU backend) so the GPU speedup is measured on the same hardware class.

## The test

Vary the number of catchments given full Bayesian treatment — 67, 335, 671 — and measure wall-clock on one A6000 (1×, $1.09/GPU/hr) versus the vectorized CPU baseline and versus point optimization. The measured outcome is: does GPU throughput decide how many catchments get full Bayesian treatment?

- **if_lever**: one GPU gives ≥20× over CPU and finishes all 671 in < 1 hr, so compute is the lever.
- **if_not**: a vectorized CPU finishes all 671 in a couple of hours, so throughput does not decide who gets full Bayesian treatment (tradition/software do).
- **Expected**: if_not — GR4J's forward model is so cheap that full Bayesian over 671 catchments is a small job once vectorized (~10^14 flops total).

## How I check it is right

- Anchor: reproduce airGR's GR4J example — parameter set X=(165.05, 6.46, 422.50, 2.45) gives calibration NSE 0.495 on the L0123001 basin (airGR docs). Match within ±0.02.
- Independent code: daily flows match airGR `RunModel_GR4J` within 1% mean absolute relative error on 20 random CAMELS catchments.
- Convergence: R̂ < 1.2 on all 4 parameters before summarizing.
- Scaling: GPU throughput (chains/s) stays linear from 67 → 335 → 671 catchments.

## Cost (Lambda on-demand, read 2026-10-20)

Rate: NVIDIA A6000 1×, 48 GB, $1.09/GPU/hr (1-GPU table).

| line | phase | kind | hours | need | usd |
|---|---|---|---|---|---|
| L_gpu_bench | gpu_bench | work | 2 (time box) | 0.5 | 2.18 |
| L_main_671 | main_full_bayes | work | 3 (time box) | main_run_hours ≈ 0.22 | 3.27 |
| L_cpu_baseline | cpu_baseline | work | 1 (time box) | cpu_671_hours ≈ 3 | 1.09 |
| L_point_opt | baseline_point_opt | work | 1 (time box) | 1 | 1.09 |
| L_storage | main_full_bayes | storage | — | — | 0.07 |
| L_stretch_global (optional) | stretch_global | work | 10 (time box) | — | 10.90 |

Core total ≈ **$7.70**; hard stop **$1,000**. The low number is itself the finding: full Bayesian GR4J over 671 catchments is cheap, so compute is probably not the blocker. The optional stretch spends leftover budget on the global CAMELS family (~2,300 catchments) and 3 forcings if the lever shows up.

## Key numbers and bases

- 671 catchments — CITED (Addor et al. 2017, HESS).
- 20 years of records (≈7,300 days) — CITED (same).
- 4 GR4J parameters — CITED (INRAE webGR).
- 4 chains/catchment — DESIGN (within DREAM(ZS)'s cited "N = 3 to 5").
- 1e5 iterations/chain — DESIGN (airGR calls 5,000 a "true exercise"; we use 20× for R̂ < 1.2 robustness).
- batched_forward_ms = 2 ms — GUESS (measured in gpu_bench); drives main_run_hours = 1e5 × 2 ms /1000/3600 × 4 ≈ 0.22 h.
- cpu_671_hours = 3 — GUESS (measured in gpu_bench).
- speedup threshold 20× — PROXY (MGB calibration speedup, a distributed model, not GR4J MCMC).
- R̂ < 1.2 — CITED (spotpy / Laloy & Vrugt).

## Restructuring

- sequential_part: each catchment's posterior waits on one chain's 100,000 serial proposal-accept steps (4 chains per catchment).
- method: **none** — the 671 catchments (and their 4 chains each) are independent, so all 2,684 chains run side by side in one batched pass; the plan only runs independent work side by side.

## Outside the Lambda budget

- ~24 human-hours to write/validate the JAX GR4J + batched sampler.
- Shared local 4-core CPU for development.
- airGR R package + CAMELS data (free downloads).
