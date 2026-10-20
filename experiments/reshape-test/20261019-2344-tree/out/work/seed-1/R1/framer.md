# Parallelising one long sequential simulation over time: guess, Newton-correct, and the "forgetting" condition

## 0. Current understanding (relayed before answering)

Three questions are on the table:

1. Can a single long sequential simulation — e.g. one MCMC chain, or a rainfall-runoff model stepped through decades of daily rainfall — be parallelised over time by *guessing the whole trajectory and then correcting every step at once with Newton iterations*?
2. Does that trick *only* work when the system forgets its past?
3. Is *compute* a major blocker at some level, and could it be fixed with "a shit ton of GPU parallelism"?

Let me define the object precisely so the later claims are not hand-wavy.

**The object.** A trajectory is a sequence of states `x_t ∈ R^d` satisfying `x_{t+1} = f(x_t, u_t)` for a deterministic map `f` (the rainfall-runoff case is this, with `u_t` the daily forcing), or, for MCMC, `x_{t+1} ~ P(· | x_t)` (a stochastic transition kernel, e.g. Metropolis-Hastings). Sequential time-stepping computes `x_T` in `T` steps; each step costs `O(c)` work, giving `O(T·c)` total *work* and — the part that matters for parallelisation — `O(T)` *depth* (critical path length). The question is whether that depth can be collapsed below `O(T)`.

**What "guess + Newton-correct" would mean mathematically.** Guess all the states at once, `X = (x_0, ..., x_{T-1})`. Define the residual whose components are the continuity conditions `F_t(X) = x_{t+1} - f(x_t, u_t) = 0`; solving `F(X) = 0` recovers the exact trajectory. Newton's method iterates `X ← X - J^{-1} F(X)`. Two observations that will drive everything:

- The *residual evaluation* `F(X)` is fully parallel over `t` — this is the "guess the whole trajectory and evaluate every step at once" part, and it is exactly why the idea is attractive.
- The *Jacobian* `J` of a one-step map is block lower-bidiagonal (step `t` couples only to `t-1`), so the Newton correction `J^{-1}F` is a forward substitution, i.e. *sequential in `T`* — unless it is attacked with cyclic reduction (see §2.6).

This is not a new idea; it is the **multiple shooting** method, and **Parareal** is a cheap-Jacobian approximation of it (details and sources in §2.1).

**What "forgets its past" means.** For deterministic dynamics, the sensitivity of `x_{t+s}` to `x_t` is the product of Jacobians, with magnitude growing like `e^{λs}` where `λ` is the maximal Lyapunov exponent. "Forgetting" means `λ < 0` (dissipative/contractive): a perturbation at time `t` is *damped*, not amplified, as it propagates forward. For MCMC, the analogous property is **mixing** — the distribution of `x_{t+s}` becomes independent of `x_t` — or, operationally, **regeneration**: times at which the chain's future is independent of its past. In both cases "forgets its past" = long-range causal coupling decays, so a bad guess early on is washed out by the time it matters.

## 1. Predictions (made before checking the literature)

- **P1.** The "guess + Newton-correct" proposal is real and studied: it is multiple shooting, with Parareal / MGRIT / PFASST as its practical realisations. It parallelises the *expensive* part (segment integration) while leaving a *cheap* sequential part (coarse propagation / bidiagonal Newton solve).
- **P2.** Fast convergence (`k ≪ T` iterations) requires the coarse-guess error to decay forward — i.e. the system must forget (negative Lyapunov exponents, dissipative, fast mixing). A memoryful or chaotic system should need `O(T)` iterations (no speedup) or diverge.
- **P3.** The linear case is the exception: `x_T = A^T x_0` is computable in `O(log T)` depth by repeated squaring/diagonalisation, with no forgetting assumption.
- **P4.** For a *single* daily rainfall-runoff run, compute is not the blocker — a forward run of a lumped conceptual model is trivially cheap; the real cost is calibration/uncertainty over *parameters*, which is embarrassingly parallel across parameters, not across time.
- **P5.** For a single long MCMC chain, the blocker is *mixing* (a statistical property), not FLOPs; GPUs add width (many chains, data-parallel likelihoods) but not depth (they don't shorten one chain's critical path), except via speculative prefetching, which is a branch-prediction trick with bounded speedup that is largest precisely when the chain barely moves.
- **P6.** "A shit ton of GPU parallelism" can reduce the cheap sequential part from `O(T)` to `O(log T)` via cyclic reduction, dropping per-iteration depth to `O(log T)`, but it cannot reduce the *number of iterations* `k`, which is set by the forgetting rate.

Predicted headline: the primary blocker is the system's memory/mixing, not compute — i.e. **NOT COMPUTE-BOUND** — with compute mattering only in specific subproblems.

## 2. Analysis

### 2.1 The method is real and well-understood

The proposal — guess the whole trajectory, then Newton-correct the continuity conditions — is literally **multiple shooting**. Wikipedia's statement of the method matches the question almost verbatim: partition the interval at grid points, "start by guessing the values of y at all grid points," integrate each sub-interval from its guessed initial value, and impose the matching conditions with "a modification of Newton's method" (https://en.wikipedia.org/wiki/Direct_multiple_shooting_method).

The Gander–Vandewalle analysis of Parareal makes the connection explicit: multiple shooting is "to decompose the time-integration interval into subintervals, to solve an initial value problem on each subinterval concurrently, and to force continuity of the solution branches on successive intervals by means of a Newton procedure" (https://www.unige.ch/~gander/Preprints/parareal.pdf). Parareal itself was introduced by Lions, Maday, and Turinici as a coarse/fine predictor-corrector in time (https://parallel-in-time.org/methods/parareal.html), and MGRIT (Falgout et al.) is the non-intrusive multigrid-reduction-in-time version shipped as XBraid (https://computing.llnl.gov/projects/parallel-time-integration-multigrid; https://www.osti.gov/servlets/purl/1184744).

### 2.2 The "forgets its past" condition is essentially the enabling condition

This is where P2 gets tested against the record.

- **Contractive/dissipative systems converge fast.** Gander and Hairer prove *superlinear* convergence of Parareal for nonlinear ODEs on bounded intervals — the error after iteration `k` is `O(ΔT^{p(k+1)})/(k+1)!`-style, shrinking as `k` grows (https://www.unige.ch/~gander/Preprints/gander_plenary2007.pdf). For parabolic (dissipative) PDEs, MGRIT is demonstrated to be an optimal-scaling solver (https://www.osti.gov/servlets/purl/1184744), and LLNL reports time-to-solution drops of "tenfold or more" for compressible Navier-Stokes (https://computing.llnl.gov/projects/parallel-time-integration-multigrid).
- **Chaotic / non-forgetting systems fail or degenerate.** The same Gander–Hairer paper shows that on the Lorenz equations (chaotic), the superlinear convergence "stops at a certain level" as chaos amplifies the coarse-grid discrepancy. More bluntly, LLNL's report on chaotic problems states that for hyperbolic/chaotic problems "the most common method, parareal, diverging in many cases," because "chaotic initial value problems are inherently ill-conditioned" (https://www.osti.gov/servlets/purl/1880928), and Vargas et al. open with the same point: chaos makes subtle coarse-level inaccuracies explode into bad coarse-grid corrections (https://arxiv.org/abs/2201.10441). This is exactly the "does not forget" failure mode: a positive Lyapunov exponent means a bad guess at time `t` is amplified forward, so the Newton/coarse correction never settles.

So, for nonlinear systems: yes, the value of the method tracks the forgetting rate. The method *is* a way to convert "sequential-in-time" into "parallel + iterate," and the iteration count `k` is governed by how fast errors decay — a property of the dynamics, not the hardware.

### 2.3 The exception: linear systems get parallel-in-time for free

For a linear map `x_{t+1} = A x_t`, the final state is `x_T = A^T x_0`, computable by repeated squaring in `O(log T)` depth. The "direct time parallel methods based on diagonalisation" (ParaDiag/ParaExp) exploit exactly this, solving the whole time interval at once for linear problems (https://www.unige.ch/~gander/siamtoc3.php, §5.5). No forgetting is needed — confirming P3 — because a linear propagator can be composed out of order. This is the only regime where the causality principle can be cleanly side-stepped.

### 2.4 The fundamental depth limit: causality and inherent sequentiality

Gander's survey names the obstacle plainly: for evolution problems "there is a causality principle: the solution later in time is affected (it is even determined) by the solution earlier in time, but not the other way round" (https://www.unige.ch/~gander/Preprints/50YearsTimeParallel.pdf). That is not just folklore: in complexity theory, the forward simulation of a local dynamics is a canonical example of a *probably inherently sequential* problem. The P-completeness page lists "Game of Life — given an initial configuration ... is that cell alive after T steps" among the problems that are "probably not parallelizable" / "inherently sequential" (https://en.wikipedia.org/wiki/P-complete), and Greenlaw–Hoover–Ruzzo's *Limits to Parallel Computation* develops the framework: such problems appear to lack polylog-time, polynomial-processor (NC) algorithms, i.e. "applying more processors ... appears to be broken" for them (https://homes.cs.washington.edu/~ruzzo/papers/limits.pdf).

The consequence: there is **no general free lunch**. For arbitrary local dynamics with memory, no number of processors removes the `O(T)` causal dependence. Parallel-in-time methods work only by *exploiting structure* — contraction (Parareal/MGRIT), linearity (ParaDiag), or a coarse/fine work separation that leaves a cheap serial residue.

### 2.5 The MCMC analog, and why Newton does not literally apply

A Metropolis-Hastings step is a stochastic accept/reject branch, not a smooth map, so there is no residual to Newton-solve. The faithful analog of "guess + correct" is **speculative prefetching**: speculatively evaluate many possible future states (the accept/reject tree) in parallel, keep the true path, discard the rest. Two recorded facts matter:

- Running many independent chains "does not change the mixing time for any single chain" (https://lips.cs.princeton.edu/pdfs/angelino2014accelerating.pdf). So the embarrassingly-parallel answer does *not* reduce the sequential length that a slow-mixing chain needs.
- Prefetching's speedup is *bounded and constant-factor*, not a complexity win: naive prefetching gives `O(log2 J)` with `J` cores, and Byrd et al.'s "speculative moves" gives expected speedup `≈ 1/α` (about 4.3 at the optimal 0.234 acceptance rate) (https://lips.cs.princeton.edu/pdfs/angelino2014accelerating.pdf; https://arxiv.org/abs/1403.7265). Note the perverse structure: this speedup is largest when rejection dominates, i.e. when the chain is *barely moving* — the opposite of fast mixing.

The "forgets its past" condition for MCMC is **regeneration**. Mykland, Tierney, and Yu introduced splitting into MCMC samplers precisely so that the tours between regeneration times are i.i.d. and "allows Markov chain sampling to take advantage of a parallel computing environment without the problems created by many short Markov chain runs" (https://galton.uchicago.edu/~mykland/paperlinks/MyklandTierneyYu2291148.pdf). Coupling from the past (Propp & Wilson) parallelises the *other* way: run the chain from *all* possible states simultaneously under a monotone coupling, and coalescence certifies an exact sample — but this is efficient only when coalescence (≈ mixing) is fast (https://www.stat.berkeley.edu/~aldous/206-RWG/RWGpapers/propp_wilson.pdf). Both are literally "the system forgets" conditions.

This exposes the central tension, and it is the sharpest version of P2/P5:

> A single long chain is needed *only when* mixing is slow; but slow mixing is *exactly when* time-parallelism (regeneration, CFTP, prefetching) gives little or nothing.

If the chain mixes fast, you don't need one long chain — many short independent chains suffice, and that is embarrassingly parallel already. If it mixes slowly, the memory is what forces the long run, and that memory is what defeats time-parallel correction. So for MCMC, time-parallelism is largely self-defeating, consistent with the P-completeness intuition of §2.4.

### 2.6 Is compute a major blocker? The GPU question

**Width versus depth.** GPUs add enormous *width* (SIMD lanes), and modern samplers use it in two ways: running many chains at once, and data-parallel gradient/log-density evaluation *within* a single chain. TensorFlow Probability's HMC "gets parallelism both within-chain (mostly from data parallelism) and across chains ... for free" on GPUs/TPUs (https://statmodeling.stat.columbia.edu/2022/11/13/stan-and-tensorflow-for-fast-parallel-bayesian-inference/; https://export.arxiv.org/pdf/2002.01184). But width does not shorten the *depth* of a single trajectory: the critical path remains `T × (per-step cost) × (mixing overhead)`. This is the Amdahl's-law-in-time point.

**Where massive parallelism does buy depth.** The cheap sequential part of the PinT methods — the coarse propagation / block-bidiagonal Newton solve — is a (block) tridiagonal/bidiagonal solve. Parallel cyclic reduction (PCR) solves such a system in `O(log N)` steps using `N`-fold parallelism (https://courses.grainger.illinois.edu/cs554/fa2015/notes/09_tridiagonal_8up.pdf). So "a shit ton of GPUs" genuinely changes the per-iteration depth from `O(T)` to `O(log T)`, giving total depth `O(k log T)`. But `k` — the number of Parareal/MGRIT/Newton iterations — is set by the contraction rate, a property of the *dynamics*, not the hardware. GPUs buy the log factor and the constants; they do not buy `k`. This is P6 confirmed.

**The hydrology example confirms compute is not the time-dimension blocker.** A single daily-step rainfall-runoff forward run is cheap; the published compute burden in exactly this setting is Monte-Carlo parameter calibration and GLUE uncertainty analysis, parallelised with MPI/OpenMP/CUDA *across parameter sets* — embarrassingly parallel, and explicitly not across time steps (https://doi.org/10.3390/w15152810; https://www.mdpi.com/2073-4441/12/10/2667). If anything, the literature treats these as "internally concurrent" in the *parameter* direction, never the time direction — because there is nothing to gain in the time direction for a cheap lumped model.

### 2.7 Synthesis

The proposed scheme — guess the whole trajectory, Newton-correct every step at once — is a real, studied technique (multiple shooting → Parareal → MGRIT). For *nonlinear* systems it works well only when the coarse-guess error is damped forward, i.e. when the system **forgets** (dissipative/contractive, or regenerating/fast-mixing for MCMC); it fails or degenerates for long-memory and chaotic dynamics. Linear systems are the one exception where exact parallel-in-time is possible without forgetting. Compute is a *secondary* constraint: for a single rainfall-runoff run it is negligible; for MCMC the binding constraint is mixing, which GPUs do not fix (they add width, and via cyclic reduction they can shave the cheap sequential part of PinT from `O(T)` to `O(log T)`, but not the iteration count `k`). The primary determinant of whether time-parallelism works at all is the system's memory/mixing — a mathematical/stability property, not a compute property.

VERDICT: NOT COMPUTE-BOUND
