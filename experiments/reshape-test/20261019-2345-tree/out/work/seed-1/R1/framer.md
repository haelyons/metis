# What actually limits Bayesian calibration of rainfall-runoff models — and whether "a shit ton of GPUs" fixes it

## 1. My understanding, relayed before answering

Rainfall-runoff (RR) models map precipitation (and potential evapotranspiration) onto streamflow at a catchment outlet. The workhorse class for calibration studies is the lumped conceptual model — GR4J is the canonical example, with exactly **four** calibrated parameters and a simple production-store + unit-hydrograph structure evaluated a few thousand arithmetic steps per decade of daily data (Perrin, Michel & Andréassian 2003, https://www.sciencedirect.com/science/article/abs/pii/S0022169403002257). Bayesian calibration treats parameters as random and uses Markov chain Monte Carlo (MCMC) to sample the posterior p(θ | data).

Two facts dominate this literature:

1. **Equifinality** — many different parameter sets reproduce the observed hydrograph almost equally well, so the posterior is broad, correlated, and often multimodal rather than a tight Gaussian around a single optimum. Beven & Binley (1992) state it directly: "within the limitations of a given model structure and errors in boundary conditions and field observations, different sets of values may be equally likely as simulators of a catchment" (https://onlinelibrary.wiley.com/doi/10.1002/hyp.3360060305).
2. **Peculiar response surfaces** — hydrological model parameters are "highly correlated and interdependent," which is precisely what makes naive samplers mix slowly; summarizing/exploring the posterior is the stated bottleneck that "hindered widespread use of Bayesian techniques in hydrology" (Marshall, Nott & Sharma 2004, https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2003WR002378). MCMC inefficiency is "frequently caused by an inappropriate selection of the proposal distribution" — a geometric/algorithmic problem, not a hardware one (Vrugt et al. 2009, https://research.wur.nl/en/publications/accelerating-markov-chain-monte-carlo-simulation-by-differential-).

MCMC samples are autocorrelated. The information content of a chain of length N is the effective sample size ESS = N / (1 + 2Σρ_k), where ρ_k are lag autocorrelations; slow mixing inflates the integrated autocorrelation time τ and forces long chains to reach any target ESS (Stan Reference Manual, https://mc-stan.org/docs/2_31/reference-manual/effective-sample-size.html). The integrated autocorrelation time is defined as the number of correlated samples needed, on average, to produce one independent draw (LaplacesDemon IAT/ESS documentation, https://search.r-project.org/CRAN/refmans/LaplacesDemon/help/ESS.html). So "needs long MCMC chains" is a symptom of large τ — a statistical property — not directly a statement about hardware speed.

## 2. Predictions (stated before checking)

- **P1:** For a single lumped conceptual catchment, one forward run is so cheap that the likelihood is effectively free; the binding constraint is τ (mixing), not FLOPs.
- **P2:** The "long chains" requirement is a property of posterior geometry (correlation/equifinality/multimodality) and, secondarily, of numerical implementation; it is reduced by better samplers/reparameterizations, not by more cores.
- **P3:** GPUs help only where the problem decomposes into independent units of work: many chains (ensemble MCMC), many particles (SMC), many catchments (large-sample), or many forward runs (GLUE / expensive models). They cannot shorten a *single* chain's autocorrelation.
- **P4:** There are genuinely compute-bound levels — expensive distributed/high-dimensional models and large-sample (CAMELS-scale) studies — where more parallel compute changes what is even attempted.

## 3. Analysis

### 3.1 Why chains are long: geometry and numerics, not throughput

The reason hydrology needed MCMC at all — and found it hard — is that the posterior of a conceptual RR model is difficult to summarize and explore because parameters are strongly correlated (Marshall et al. 2004, https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2003WR002378). Equifinality formalizes this as "equal finality": many parameter pathways reproduce the observed runoff (Beven & Binley 1992, https://onlinelibrary.wiley.com/doi/10.1002/hyp.3360060305). The DREAM paper's motivating diagnosis is that slow mixing "is frequently caused by an inappropriate selection of the proposal distribution," and its remedy is a self-adaptive differential-evolution proposal that tunes scale and orientation during the search — i.e., a better *algorithm*, not more *hardware* (Vrugt et al. 2009, https://research.wur.nl/en/publications/accelerating-markov-chain-monte-carlo-simulation-by-differential-).

Autocorrelation is the currency here: τ is set by the target's geometry and the sampler, and is invariant to how many parallel chains you run. Running more chains increases the number of samples per wall-clock second, but each chain still pays the same τ per independent draw. That is why "just add GPUs" is not, by itself, a fix for slow mixing — it changes throughput, not τ.

There is also a subtlety specific to hydrology: **cheap numerics corrupt MCMC**. First-order, explicit, fixed-step integration of water-balance dynamics makes the model "computationally cheap" (explicitly desirable for MCMC), but that cheapness introduces artificial bimodality in marginal posteriors and causes "slow convergence of the MCMC algorithm" plus unreliable Gelman–Rubin diagnostics (Schoups et al. 2010, https://agupubs.onlinelibrary.wiley.com/doi/pdfdirect/10.1029/2009WR008648). Here the fix is a better ODE integrator (adaptive-step, second-order, or operator splitting), again not more compute.

### 3.2 The per-evaluation cost is not the binding constraint (lumped models)

GR4J has four parameters and a compact store/unit-hydrograph structure (Perrin et al. 2003, https://www.sciencedirect.com/science/article/abs/pii/S0022169403002257; INRAE webGR, https://webgr.inrae.fr/eng/tools/hydrological-models/daily-hydrological-model-gr4j). A multi-decade daily simulation is a few thousand arithmetic steps. Tellingly, the original GLUE paper could call its procedure "computationally intensive" only because it ran on a 1992 "local parallel processing computer" (Beven & Binley 1992, https://onlinelibrary.wiley.com/doi/10.1002/hyp.3360060305) — the same embarrassingly parallel random sampling is trivial on any modern machine. For this model class, the bottleneck is the number of *serial* MCMC iterations needed to overcome τ, not the cost of each iteration.

### 3.3 What "a shit ton of GPU parallelism" actually buys

MCMC within a single chain is inherently sequential (each state conditions on the previous one), so the only exploitable parallelism is across independent units of work. That covers three regimes:

- **(a) Ensemble / differential-evolution MCMC.** DREAM "runs multiple different chains simultaneously for global exploration" (Vrugt et al. 2009, https://research.wur.nl/en/publications/accelerating-markov-chain-monte-carlo-simulation-by-differential-). Jeremiah et al. note that parallel chains "with different starting points enable the sampler to simultaneously explore multiple regions of the parameter space, thereby improving the posterior coverage over that of a single chain" (https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2010WR010217). GPUs/cloud make thousands of chains cheap, which helps multimodal coverage and yields cross-chain convergence diagnostics — a real, but bounded, improvement (it does not reduce τ).

- **(b) Expensive forward models.** For spatially distributed models with hundreds-to-thousands of parameters, the cost of the forward model dominates, and "high-performance computing"/distributed computing delivers a "spectacular performance improvement" for the MT-DREAM(ZS) sampler on problems up to 241 parameters (Laloy & Vrugt 2012, https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2011wr010608). GPU-optimized large-basin models report ~20× CPU speedups for calibration and ~65× GPU speedups for simulations (Freitas et al. 2022, https://experts.illinois.edu/en/publications/performance-optimization-of-the-mgb-hydrological-model-for-multi-). At the SWAT end of the spectrum, calibration "could take days to complete, even on the finest standalone machines" (nhess 2012, https://nhess.copernicus.org/articles/12/2411/2012/nhess-12-2411-2012.pdf). This level is genuinely compute-bound, and parallelism is the fix because calibration decomposes into thousands of independent model runs.

- **(c) Large-sample studies.** CAMELS provides 671 US catchments (Addor et al. 2017, https://hess.copernicus.org/articles/21/5293/2017/hess-21-5293-2017.html), each independently calibratable — the definition of an embarrassingly parallel workload in which GPU/cloud throughput directly determines how many catchments can be afforded a *proper* Bayesian treatment rather than point optimization.

### 3.4 What compute cannot buy

Three hard limits are not computable away:

1. **Structural error and input (rainfall) uncertainty.** The model is wrong and the rainfall is mismeasured. Renard et al. (2010) report that "poor identifiability may arise when the inference scheme represents rainfall and structural errors using separate probabilistic models," and emphasize "the inherent limitations of inferring inaccurate hydrologic models using rainfall-runoff data with large unknown errors" (https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2009WR008328). Explicitly accounting for precipitation error "significantly alters the posterior distribution" of the watershed parameters (Vrugt et al. 2008, https://research.wur.nl/en/publications/treatment-of-input-uncertainty-in-hydrologic-modeling-doing-hydro). These are modeling/likelihood changes (e.g., the Bayesian total error analysis of Kavetski, Kuczera & Franks 2006, https://doi.org/10.1029/2005WR004368), not FLOPs changes.

2. **Intrinsic autocorrelation of a single chain.** τ is a property of target and sampler. Better samplers reduce it — adaptive Metropolis for correlated parameters (Marshall et al. 2004, https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2003WR002378), differential evolution (Vrugt et al. 2009), and gradient-based Hamiltonian Monte Carlo enabled by automatic differentiation of GR4J (Krapu et al. 2022, https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021WR031377). These are the actual levers on "long chains"; hardware is not one of them.

3. **Data quantity/quality.** No sampler recovers parameters the record cannot identify (Beven & Binley 1992, https://onlinelibrary.wiley.com/doi/10.1002/hyp.3360060305; Renard et al. 2010, https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2009WR008328).

## 4. Synthesis

For the canonical problem that generates "long MCMC chains" — Bayesian calibration of a lumped conceptual model on one catchment — the binding constraint is statistical (posterior geometry, equifinality, autocorrelation, structural/input error), while the per-iteration cost is negligible. GPUs change throughput, not τ; the efficient fix is a better sampler, a reparameterization, a better integrator, or an explicit error model. So the headline answer is NOT COMPUTE-BOUND. But at two real levels — expensive distributed/high-dimensional models, and large-sample multi-catchment studies — compute is a genuine, currently-binding blocker, and there the workload is embarrassingly parallel across parameter sets, chains, and catchments, so massive GPU/cloud parallelism directly changes what can be attempted and concluded. Those are captured below as compute signals, not as the primary limiter of the "long chains" question.

VERDICT: NOT COMPUTE-BOUND
