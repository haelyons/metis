# Related problems that are compute constrained

Related problems are counted here as compute constrained in the broad sense: (a) it is still open whether more parallel compute would change the answer, (b) compute is already known to bind there (marked "settled"), or (c) the answer takes long because its steps run one after another even though more hardware would not change the answer, only how soon it arrives.

## Single-chain MCMC mixing

A single Markov chain for a lumped conceptual model must run many serial iterations because posterior samples are autocorrelated; each step conditions on the previous state, and more parallel compute cannot shorten the chain's integrated autocorrelation time, only how fast samples accumulate.

- **root_link:** Bears on the "what actually limits Bayesian calibration" half of the question — the single chain's autocorrelation is why lumped-model calibration is not compute-bound.
- **compute_open:** none — more parallel compute buys samples-per-second but not a shorter autocorrelation time for a single chain, because τ (equivalently ESS = N/(1+2Σρ_k)) is set by target geometry and sampler, not by hardware (https://mc-stan.org/docs/2_31/reference-manual/effective-sample-size.html).
- **sequential:** One converged posterior waits on one chain whose every step is a proposal from the current state plus a Metropolis accept/reject, and a single GR4J forward run is only a few thousand arithmetic steps per multi-decade daily record (https://www.sciencedirect.com/science/article/abs/pii/S0022169403002257), yet the chain must run on the order of up to 10^6 generations (DREAM(D)'s default maximum T_max; https://doi.org/10.5194/hess-15-3701-2011) to overcome autocorrelation, and the answer needs only a few independent chains (DREAM(ZS) uses N = 3–5; https://doi.org/10.1029/2011WR010608) for Gelman–Rubin checks, each keeping a tiny fraction of one GPU busy. These steps must run in order because each state conditions on the previous one, so the only way to run them at the same time is to run many independent chains in parallel, which pays off when the target is multimodal and chains are cheap (it buys coverage, not lower τ) — the nearest source that tried it is DREAM (https://research.wur.nl/en/publications/accelerating-markov-chain-monte-carlo-simulation-by-differential-).
- **sources:** https://www.sciencedirect.com/science/article/abs/pii/S0022169403002257 · https://doi.org/10.5194/hess-15-3701-2011 · https://mc-stan.org/docs/2_31/reference-manual/effective-sample-size.html

## Ensemble / differential-evolution MCMC

DREAM-style samplers run N chains simultaneously, generating each chain's proposal from differences of other chains' states; this improves exploration of multimodal/correlated hydrologic posteriors and enables Gelman–Rubin cross-chain diagnostics, and it is the one place where more GPUs change what gets sampled (by raising chain count) without lowering per-chain autocorrelation.

- **root_link:** Bears on the "whether a shit ton of GPUs fixes it" half — GPUs buy more parallel chains (throughput and multimodal coverage), a real but bounded fix.
- **compute_open:** More parallel compute buys simultaneous chains (ensemble members); standard DREAM runs N = d/2 to d (up to 2d) chains (https://doi.org/10.1029/2011WR010608), DREAM(ZS) needs only N = 3–5, and the largest reported run uses N = 25 chains on a 25-dimensional trimodal target (https://pure.uva.nl/ws/files/1553085/134391_wrcr13130_sup_0002_t02.txt), but it is still unknown whether chains beyond N = 25 further improve posterior coverage or mixing on higher-dimensional, more multimodal hydrology targets.
- **sequential:** none — after burn-in the N chains' joint density factorizes and they are independent, so the ensemble already splits into N chains run simultaneously (https://doi.org/10.1029/2011WR010608).
- **sources:** https://research.wur.nl/en/publications/accelerating-markov-chain-monte-carlo-simulation-by-differential- · https://doi.org/10.1029/2011WR010608 · https://pure.uva.nl/ws/files/1553085/134391_wrcr13130_sup_0002_t02.txt

## Expensive distributed forward models

For spatially distributed models with hundreds-to-thousands of parameters the forward-model cost dominates the calibration budget, and the workload decomposes into thousands of independent model runs that are embarrassingly parallel across chains and parameter sets; here compute is a genuinely binding constraint that parallelism relieves.

- **root_link:** Bears on the "what actually limits Bayesian calibration" half — for expensive distributed models the forward-model cost, not mixing, is the binding limit.
- **compute_open:** settled: more parallel compute is already known to bind and pay off here — the forward model dominates the budget (DREAM needed about 50 million surrogate-model evaluations to converge on a 241-parameter groundwater model, https://doi.org/10.1029/2011WR010608), distributed MT-DREAM(ZS) reports "spectacular performance improvement" on that same 241-parameter problem (https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2011wr010608), and GPU optimization of the MGB model yields up to 20× CPU speedup for calibration and 24× (CPU) / 65× (GPU) for simulations (https://doi.org/10.1016/j.envsoft.2021.105271).
- **sequential:** none — the calibration already decomposes into independent forward-model runs evaluated in parallel across chains and multiple simultaneous proposals, so it is embarrassingly parallel (https://doi.org/10.1029/2011WR010608).
- **sources:** https://doi.org/10.1029/2011WR010608 · https://doi.org/10.1016/j.envsoft.2021.105271 · https://nhess.copernicus.org/articles/12/2411/2012/nhess-12-2411-2012.pdf

## Large-sample multi-catchment calibration

Calibrating many catchments (CAMELS provides 671 US catchments) is embarrassingly parallel because each catchment is independently calibratable, so GPU/cloud throughput directly determines how many catchments get a proper Bayesian treatment rather than point optimization.

- **root_link:** Bears on the "whether a shit ton of GPUs fixes it" half — at CAMELS scale, throughput determines how many catchments can be afforded full Bayesian treatment.
- **compute_open:** More parallel compute buys catchments given full Bayesian treatment instead of point optimization; the largest published set is CAMELS's 671 US catchments (https://hess.copernicus.org/articles/21/5293/2017/hess-21-5293-2017.html), and it is still unknown what extending full Bayesian treatment to all catchments above 671 (or globally) would change about large-sample hydrological conclusions.
- **sequential:** none — the catchments are independently calibratable, so the study already splits into one independent calibration per catchment (https://hess.copernicus.org/articles/21/5293/2017/hess-21-5293-2017.html).
- **sources:** https://hess.copernicus.org/articles/21/5293/2017/hess-21-5293-2017.html · https://onlinelibrary.wiley.com/doi/10.1002/hyp.3360060305
