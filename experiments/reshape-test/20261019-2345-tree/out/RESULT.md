# Result

Picks 2 · PASS 1 · on-goal cards U4 0 · U3 1 · halts: cost record broken 1

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [R1·phys·Large-sample multi-catchment calibration](#card-R1-physical-Large-sample-multi-catchment-calibration) Large-sample multi-catchment calibration (CAMELS) | PASS 2/2 | top 1/4 · ADJACENT, tie of 2 broken by seeded order | if_not | 5 | 5 → 5 | 5 → 3 narrowed | 3 | — | 1 → 2 | — | $2 at gpu_bench · plan $8 · 2 GUESS |
| [R1·interp·Active-subspace reparameterization of the calibration](#card-R1-interp-Active-subspace-reparameterization-of-the-calibration) Reparameterize the calibration with active subspaces to shorten the MCMC chain | halted: cost record broken | top 3/3 · SAME | if_not | — | 5 → — | 5 → — | — | — | 5 → — | — | not judged · plan $0 · 0 GUESS |

## Frontier (listed, not produced)

**R1**
- Single-chain MCMC mixing: the sequential autocorrelation bottleneck (SAME): none — more parallel compute buys samples-per-second but not a shorter autocorrelation time for a single chain, because τ (equivalently ESS = N/(1+2Σρ_k)) is set by target geometry and sampler, not by hardware (https://mc-stan.org/docs/2_31/reference-manual/effective-sample-size.html).

## Cards

<a id="card-R1-physical-Large-sample-multi-catchment-calibration"></a>**Large-sample multi-catchment calibration · Large-sample multi-catchment calibration (CAMELS).** R1 · physical · top pick · distance ADJACENT · compute tested: yes · plan expects: not the lever · PASS

**Question.** Does GPU parallelism change how many of the 671 CAMELS catchments can get full Bayesian calibration instead of point optimization?

**What is known.** Freitas et al. 2022 GPU-optimized a hydrological model's calibration to 20x CPU speedup, on one distributed model, not batched MCMC across many GR4J catchments [s_mgb]. No published result times batched GPU MCMC giving all 671 CAMELS catchments full Bayesian GR4J treatment, so the crossover is unmeasured [s_mgb].

**Hypothesis.** Each catchment calibrates independently, so GPU batching turns full Bayesian treatment of all 671 into a cheap throughput problem, not a blocker.

**Restructuring.** Each catchment's posterior waits on one chain's 100,000 serial proposal-accept steps; four chains per catchment. none - the 671 catchments' four chains each are independent, so all 2,684 chains run side by side in one batched pass.

**If compute is the lever.** One GPU gives >=20x over CPU and finishes all 671 in under an hour, so compute is the lever here.

**If not.** Vectorized CPU finishes all 671 in a couple of hours, so throughput does not decide which catchments get full Bayesian treatment.

**Test.** Time full Bayesian MCMC (4 chains x 1e5 iterations, R-hat<1.2) for 671 CAMELS catchments on one GPU versus a vectorized CPU and versus point optimization; measure whether GPU throughput decides how many catchments get full Bayesian treatment.

*Compute axis.* Catchments given full Bayesian MCMC treatment: 67–671 catchments, 3 levels. Closest prior: not on this axis.

**Check first.** Reproduce airGR's GR4J: parameter set X=(165.05, 6.46, 422.50, 2.45) gives calibration NSE 0.495 on its example basin [s_airgr_nse]. Tolerance: calibration NSE within +/-0.02 of 0.495.

**Would not show.** Shows GR4J only, not expensive distributed or hierarchical models; US CAMELS unless the optional global stretch runs; nothing about single-chain mixing limits.

*Cost.* Plans $7.70 of the $1,000 budget over 7 machine-hours, leaving $992.30. Main guess: vectorized CPU wall-clock for full Bayesian on all 671 catchments [g], measured after $2.18 of spend; the budget is reached if it is 300× higher.

**Judges.** Dramaturg: PASS 2/2. Decides at: $2 at gpu_bench · plan $8 · 2 GUESS (critic: gpu_bench measures batched GPU forward time (yielding main_run_hours) and cpu_671_hours, giving both terms of decision_rule whichever way they fall).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-20 · filesystem $0.20/GiB-month [q]
Spend      gpu_bench  A6000 1x: anchor check, 67-catchment pilot, measure batched_forward_ms and CPU throughput  1x NVIDIA A6000 48GB $1.09/h  2 h [d]  $2.18  time box; need 0.5 h (margin 4.00×)
           main_full_bayes  Full Bayesian MCMC (4 chains x 1e5 iter, R-hat<1.2) on all 671 CAMELS catchments, batched on the GPU  1x NVIDIA A6000 48GB $1.09/h  3 h [d]  $3.27  time box; need 0.222 h (margin 13.50×)
           cpu_baseline  Vectorized CPU full Bayesian on all 671 (timed) for the GPU-vs-CPU comparison  1x NVIDIA A6000 48GB $1.09/h  1 h [d]  $1.09  time box; need 3 h (margin 0.33×)
           baseline_point_opt  Point optimization (airGR Calibration_Michel / SCE-UA) on all 671 catchments  1x NVIDIA A6000 48GB $1.09/h  1 h [d]  $1.09
           main_full_bayes  Filesystem for CAMELS forcing (~10 GiB, 1 day)  [=]  $0.07
           stretch_global  Optional: full Bayesian on the global CAMELS family (~2,300 catchments) and 3 forcings  1x NVIDIA A6000 48GB $1.09/h  10 h [d]  $10.90  optional
           Planned $7.70 · unallocated $992.30 · with options $18.60 · cap $1,000
Rests on   vectorized CPU wall-clock for full Bayesian on all 671 catchments 3 hours [g] rests on: Vectorized NumPy/JAX GR4J over 2,684 chains, 7,300-day scan at ~1-8 us per day-step on 14 vCPUs gives ~0.8-6.5 hr for 1e5 iterations x 4x overhead; mid value 3 hr. · measured in gpu_bench ($2.18 spent by then) · budget reached at 911 (300× higher) · box overflows at 1.0×
           GPU time per batched forward pass (all 2684 chains) 2 ms [g] rests on: GR4J is a ~7,300-day recurrence of a few tens of FLOPs/day; 2,684 chains batched on an A6000 (~38 TFLOPS FP32) at ~1% realized utilization is ~2 ms per full pass, padded for kernel-launch overhead. · measured in gpu_bench ($2.18 spent by then) · gate GPU wall-clock for full Bayesian on all 671 catchments ≤ 6 in gpu_bench (now 0.222, passes; uncut plan at it $13.15), else Stop and replan: full Bayesian 671 is not affordable on one GPU; reprice on a larger instance or fall back to point optimization. · budget not reached within 1000× · box overflows at 14×
Scenarios  GPU batching slow: batched_forward_ms=20 ms (10x), cpu_671_hours=2 → $8.79
Buys       CAMELS US catchments: 671 [c] · GPU batching slow: batched_forward_ms=20 ms (10x), cpu_671_hours=2: 671
           posterior likelihood evaluations delivered: 268M [=] · GPU batching slow: batched_forward_ms=20 ms (10x), cpu_671_hours=2: 268M
Flags      error (quote) at numbers.gr4j_params.quote: 4 does not appear in the quote "GR4J model has four parameters to optimise during calibration:"; a value transformed from the page belongs in a DERIVED number
Full scale Full Bayesian on all 671 CAMELS catchments with a 241-parameter distributed model (DREAM needed ~50M evaluations for one catchment): $10,200 = 10.2× budget = 0.0000378× total forward runs for all 671 catchments · inputs 2 g, 1 c ([g] GPU time per 241-parameter distributed-model forward run; [g] evaluations to converge one 241-parameter distributed model)
Outside    developer time (write/validate JAX GR4J + batched Metropolis, airGR cross-check): 24 human-hours · shared local 4-core CPU for development: 24 core-hours
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
camels_days = camels_years*365 = 20 * 365 = 7300 days
forward_per_catchment = chains_per_catchment*iter_per_chain = 4 * 100000 = 400000 forward runs
total_forward_671 = camels_n*forward_per_catchment = 671 * 400000 = 2.684e8 forward runs
main_run_hours = iter_per_chain*batched_forward_ms/1000/3600*mcmc_overhead = 100000 * 2 / 1000 / 3600 * 4 = 0.222222 hours
posterior_samples_671 = total_forward_671 = 2.684e8 = 2.684e8 samples
L_main_671.need = main_run_hours = 0.222222 = 0.222222 h
L_cpu_baseline.need = cpu_671_hours = 3 = 3 h
L_storage.usd = 10*fs_usd_gib_month*24/720 = 10 * 0.2 * 24 / 720 = 0.0666667 usd
fs_distributed = camels_n*dist_evals_per_catchment*dist_forward_ms/1000/3600*1.09 = 671 * 5e7 * 1 / 1000 / 3600 * 1.09 = 10158.2 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:left_open` PARTIAL · page: "Significant speedups of up to 20 × (CPU) were achieved for calibration, while the scalability analysis indicated 24 × (CPU) and 65 × (GPU) for simulations with larger problem sizes." · note: s_mgb supports that the closest prior (Freitas 2022) is MOCOM-UA calibration of MGB, not batched GPU MCMC over 671 GR4J catchments, but a single source cannot establish the blanket negative 'no published result exists'; the 'crossover is unmeasured' is the plan's inference, not stated on the page.
- sample 1 · `num:dist_evals_per_catchment` UNREACHABLE · page: "" · note: Cited Wiley page returns HTTP 403 (Forbidden). A mirror (UvA DARE) exposes only the abstract, which confirms 'Four different case studies with increasing dimensionality up to 241 parameters' but does not contain the '50 million surrogate model evaluations' sentence; the full text could not be read, so the number could not be verified against the page.
- sample 2 · `num:dist_evals_per_catchment` UNREACHABLE · page: "High‐dimensional posterior exploration of hydrologic models using multiple‐try DREAM(ZS) and high‐performance computing - Laloy - 2012 - Water Resources Research" · note: The cited Wiley page (agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2011WR010608) blocks fetching (403/CAPTCHA) via direct, DOI, Semantic Scholar, and proxy routes; an open author copy (UCI) and a Wayback capture of the full text were reachable only down to section [34] before truncation, so the quoted sentence about Keating et al. (2010) and 'about 50 million surrogate model evaluations' (in case study 4, the 241-parameter groundwater model) could not be read or verified. The 241-parameter groundwater model of Keating et al. (2010) is confirmed in the abstract and intro ('Four different case studies with increasing dimensionality up to 241 parameters are used...').

**Critic.**
- stakes 3 · `card:limits` "Shows GR4J only, not expensive distributed or hierarchical models; US CAMELS unless the optional global stretch runs; nothing about single-chain mixing limits." · Only GR4J US CAMELS tested; broader scaling depends on unchecked expensive models or global stretch.
- lever 5 · `plan:predictions.decision_rule` "if_lever iff GPU wall-clock for 671 catchments < 1 hour AND the GPU beats the vectorized CPU baseline by >=20x; otherwise (including a 5-20x speedup) count as if_not." · Noise <5%, levels span 10x, and GPU/CPU timing thresholds isolate compute while inputs are fixed.
- verifiable 3 · `plan:scored_against` "airGR reference GR4J (calibration NSE 0.495 on its example basin) and R-hat < 1.2 convergence; GPU result compared with the vectorized CPU baseline within the 20x threshold." · Published NSE anchor validates code, but the timing decision lacks an independent planted truth.
- open 5 · `card:left_open` "No published result times batched GPU MCMC giving all 671 CAMELS catchments full Bayesian GR4J treatment, so the crossover is unmeasured [s_mgb]." · Prior measured MGB point-calibration speedups, not batched GR4J Bayesian MCMC across CAMELS; gap stated.
- reshape 2 · `card:method` "none - the 671 catchments' four chains each are independent, so all 2,684 chains run side by side in one batched pass." · No dependency removed; independent chains are merely batched side by side, leaving serial chain order.
- baseline NA · `card:method` "none - the 671 catchments' four chains each are independent, so all 2,684 chains run side by side in one batched pass." · Restructuring method says none, so the baseline criterion allowing NA applies.

**Option critic.**
- stakes 5: Choice to buy cloud GPUs for all catchments' full Bayesian treatment turns on whether conclusions change.
- open 5: Names catchments; published stops at 671, and the unmeasured range starts within GPU reach.
- reshape 1: Only independent catchments run in parallel; sequential says none.
- distance ADJACENT: Same subject (catchment calibration) but asks large-sample throughput, a different question from single-chain limits.

**Producer says (not judged).** expected if_not (GR4J's forward model is so cheap that full Bayesian over 671 catchments is a small job once vectorized, so compute is not the blocker.); compute_tested yes (The test varies the number of catchments (67/335/671) and measures whether per-catchment wall-clock stays flat as parallel work grows, i.e. whether GPU throughput is the lever that buys full Bayesian treatment.); decides no; searched yes.

**Annotations.**
- quote at numbers.gr4j_params.quote: 4 does not appear in the quote "GR4J model has four parameters to optimise during calibration:"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.dist_evals_per_catchment.quote: 50000000 does not appear in the quote "Previous results presented by Keating et al. [2010] have shown that DREAM required about 50 million surrogate model evaluations to converge to a limiting parameter distribution"; a value transformed from the page belongs in a DERIVED number
- restructuring.condition is empty
- restructuring.condition_phase is empty
- restructuring.baseline_sequential is empty
- restructuring.baseline_copies is empty
- hypothesis: a sentence of 22 words
- restructuring.method: a sentence of 21 words
- predictions.if_not: a sentence of 21 words
- test_summary: a sentence of 37 words
- novelty.closest_prior: a sentence of 25 words
- novelty.left_open: a sentence of 22 words
- limits: a sentence of 22 words
- dramaturg findings failed G-find after a resample; decided as returned
- critique failed G-crit after a resample; shown as returned

**Root question (R1).** What limits Bayesian calibration of rainfall-runoff models for river catchments, which needs long MCMC chains? Is compute a major blocker at some level, and could that be fixed with a shit ton of GPU parallelism?

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/reshape-test/20261019-2345-tree/out/work/seed-1/R1/physical/7fdc05fe/producer.md)

---

<a id="card-R1-interp-Active-subspace-reparameterization-of-the-calibration"></a>**Active-subspace reparameterization of the calibration · Reparameterize the calibration with active subspaces to shorten the MCMC chain.** R1 · interp · top pick · distance SAME · compute tested: yes · plan expects: not the lever · halted: cost record broken

**Question.** Does the rainfall-runoff calibration posterior have a low-dimensional active subspace, and does running MCMC only on it shorten chains more than more GPUs do?

**What is known.** Constantine, Kent and Bui-Thanh's active-subspace MCMC: a 100-parameter forward model, 1000 gradient samples, 500k evaluations; minimum ESS rose 604 to 81986 versus vanilla. Whether a single linear subspace still captures rainfall-runoff posteriors whose cheap fixed-step integrators add artificial bimodality, and above 1000 gradient samples.

**Hypothesis.** A few data-informed directions carry the rainfall-runoff posterior's variation, so MCMC on them mixes faster and beats parallel copies.

**Restructuring.** Four serial steps: draw gradient samples, average outer products, eigendecompose, then run the active-variable Markov chain. Gradient samples are mutually independent, so they run concurrently across GPUs; only the eigendecomposition and the short low-dimensional chain remain serial.

**If compute is the lever.** More parallel gradient samples make the eigenvalue gap widen enough that the reparameterized chain's ESS beats both baselines only at high counts.

**If not.** The eigenvalue gap is already clear at 300 gradient samples, so more samples leave the ESS verdict unchanged: compute is not the lever.

**Test.** Reproduce the published active-subspace MCMC, then run it on four-parameter GR4J while sweeping gradient samples 100 to 100000, against a serial vanilla Metropolis chain and side-by-side vanilla chains, comparing eigenvalue gaps and effective sample size per evaluation.

*Compute axis.* Gradient samples drawn to estimate the active subspace: 100–100,000 gradient samples, 5 levels. Closest prior: 1,000 [s1].

**Check first.** Reproduce the published two-parameter quadratic: epsilon 0.01 gives a one-dimensional active subspace; epsilon 0.95 gives no gap. Tolerance: recovered leading eigenvalue ratio at least 100 for epsilon 0.01 and at most 10 for epsilon 0.95.

**Would not show.** Only synthetic and CAMELS daily lumped models; won't prove active subspaces work for distributed, high-dimensional, or input-error-dominated calibrations.

*Cost.* The cost record did not evaluate (4 errors); see the cost block.

**Halted at cost record broken.** undefined at full_scale.fs_distributed.ratio_to: "budget_usd" is not a number id

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-20
Errors     undefined at full_scale.fs_distributed.ratio_to: "budget_usd" is not a number id
           quote at numbers.m_gr4j.quote: 4 does not appear in the quote "The GR4J model has four parameters to optimise during calibration"; a value transformed from the page belongs in a DERIVED number
           quote at numbers.ess_vanilla_pub.quote: 604 does not appear in the quote "The much larger effective sample sizes for the active subspace-accelerated chains is due to the independent sampling according to the prior on the inactive variables."; a value transformed from the page belongs in a DERIVED number
           quote at numbers.ess_accel_pub.quote: 81986 does not appear in the quote "The much larger effective sample sizes for the active subspace-accelerated chains is due to the independent sampling according to the prior on the inactive variables."; a value transformed from the page belongs in a DERIVED number
```

**Derivations.**
```
Derivations: the cost record did not evaluate.
```

**Option critic.**
- stakes 5: Whether active subspaces capture RR posteriors decides reparameterization versus other samplers or cores.
- open 5: Names gradient samples; published stops at M=300 and 100-dim; RR posterior active-subspace test starts within reach.
- internals 1: Names no model-internal information distinct from outputs; active subspaces are parameter-space directions.
- reshape 5: Names ~4-step chain; gradient samples independent, GPU idle; parallel if forward model expensive enough, checkable; no RR source.
- distance SAME: Directly asks reparameterization to shorten MCMC chains versus compute, the root question.

**Producer says (not judged).** expected if_not (Published demos already find the dominant gap at 300-1000 samples, and the framer holds that autocorrelation is set by posterior geometry, not by sample count.); compute_tested yes (The plan sweeps the number of gradient samples from 100 to 100000, the quantity more parallel GPUs buy, and checks whether it changes the eigenvalue gap and the ESS verdict.); decides partly; searched yes.

**Annotations.**
- cost record repaired: 1 expression(s) rewritten; unknown ids ignored: fs_distributed
- quote at numbers.m_gr4j.quote: 4 does not appear in the quote "The GR4J model has four parameters to optimise during calibration"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.ess_vanilla_pub.quote: 604 does not appear in the quote "The much larger effective sample sizes for the active subspace-accelerated chains is due to the independent sampling according to the prior on the inactive variables."; a value transformed from the page belongs in a DERIVED number
- quote at numbers.ess_accel_pub.quote: 81986 does not appear in the quote "The much larger effective sample sizes for the active subspace-accelerated chains is due to the independent sampling according to the prior on the inactive variables."; a value transformed from the page belongs in a DERIVED number
- prior_max_level 1000 is not in the quote of s1

**Root question (R1).** What limits Bayesian calibration of rainfall-runoff models for river catchments, which needs long MCMC chains? Is compute a major blocker at some level, and could that be fixed with a shit ton of GPU parallelism?

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/reshape-test/20261019-2345-tree/out/work/seed-1/R1/interp/4bf1b6d0/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|
| R1:interp:Active-subspace reparameterization of the calibration | Reparameterize the calibration with active subspaces to shorten the MCMC chain | SAME | Reducing serial autocorrelation in hydrologic MCMC calibration | 11 | picked_top | reshape route: highest reshape + stakes |
| R1:interp:Feature steering to map the identifiable manifold | Steer SAE features of a differentiable rainfall-runoff model to separate identifiable from equifinal directions | SAME | SAE feature analysis of equifinality in rainfall-runoff models | 11 | not_picked | not drawn |
| R1:interp:SAE feature extraction on learned rainfall-runoff models | Train sparse autoencoders on LSTM rainfall-runoff internals to expose representation-level equifinality | ADJACENT | SAE feature analysis of equifinality in rainfall-runoff models | 13 | not_picked | not drawn |
| R1:physical:Ensemble / differential-evolution MCMC | Ensemble / differential-evolution MCMC: running many chains in parallel | SAME | Exploiting parallel compute in hydrologic calibration | 10 | not_picked | not drawn |
| R1:physical:Expensive distributed forward models | Expensive distributed / high-dimensional forward models (MT-DREAM(ZS), MGB, SWAT) | SAME | Exploiting parallel compute in hydrologic calibration | 2 | not_eligible | compute_open settled, sequential none |
| R1:physical:Large-sample multi-catchment calibration | Large-sample multi-catchment calibration (CAMELS) | ADJACENT | Exploiting parallel compute in hydrologic calibration | 10 | picked_top | highest total with open >= 3, tie of 2 broken by seeded order |
| R1:physical:Single-chain MCMC mixing | Single-chain MCMC mixing: the sequential autocorrelation bottleneck | SAME | Reducing serial autocorrelation in hydrologic MCMC calibration | 6 | not_picked | not drawn |

## Log

```
R1: NOT COMPUTE-BOUND, 3 compute signal(s) -> WIDENER + INTERP
R1:physical: no reshape option
R1:interp: reshape route
pool: 0 candidate cluster(s); picked 0
R1:interp:top: G-plan repair: undefined at full_scale.fs_distributed.ratio_to: "budget_usd" is not a number id
R1:physical:top: quote at numbers.gr4j_params.quote: 4 does not appear in the quote "GR4J model has four parameters to optimise during calibration:"; a value transformed from the page belongs in a DERIVED number
R1:physical:top: quote at numbers.dist_evals_per_catchment.quote: 50000000 does not appear in the quote "Previous results presented by Keating et al. [2010] have shown that DREAM required about 50 million surrogate model evaluations to converge to a limiting parameter distribution"; a value transformed from the page belongs in a DERIVED number
R1:physical:top: restructuring.condition is empty
R1:physical:top: restructuring.condition_phase is empty
R1:physical:top: restructuring.baseline_sequential is empty
R1:physical:top: restructuring.baseline_copies is empty
R1:physical:top: hypothesis: a sentence of 22 words
R1:physical:top: restructuring.method: a sentence of 21 words
R1:physical:top: predictions.if_not: a sentence of 21 words
R1:physical:top: test_summary: a sentence of 37 words
R1:physical:top: novelty.closest_prior: a sentence of 25 words
R1:physical:top: novelty.left_open: a sentence of 22 words
R1:physical:top: limits: a sentence of 22 words
R1:interp:top: cost record repaired: 1 expression(s) rewritten; unknown ids ignored: fs_distributed
R1:interp:top: quote at numbers.m_gr4j.quote: 4 does not appear in the quote "The GR4J model has four parameters to optimise during calibration"; a value transformed from the page belongs in a DERIVED number
R1:interp:top: quote at numbers.ess_vanilla_pub.quote: 604 does not appear in the quote "The much larger effective sample sizes for the active subspace-accelerated chains is due to the independent sampling according to the prior on the inactive variables."; a value transformed from the page belongs in a DERIVED number
R1:interp:top: quote at numbers.ess_accel_pub.quote: 81986 does not appear in the quote "The much larger effective sample sizes for the active subspace-accelerated chains is due to the independent sampling according to the prior on the inactive variables."; a value transformed from the page belongs in a DERIVED number
R1:interp:top: prior_max_level 1000 is not in the quote of s1
R1:interp:top: halted at cost record broken: undefined at full_scale.fs_distributed.ratio_to: "budget_usd" is not a number id
R1:physical:top: dramaturg: degenerate: card:hypothesis; degenerate: card:sequential_part; degenerate: card:method; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:limits
R1:physical:top: critic: baseline: value "NA"
R1:physical:top: dramaturg (resample): degenerate: card:hypothesis; degenerate: card:sequential_part; degenerate: card:method; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:limits
R1:physical:top: dramaturg findings failed G-find after a resample; decided as returned
R1:physical:top: critic (resample): baseline: value "NA"
R1:physical:top: critique failed G-crit after a resample; shown as returned
```