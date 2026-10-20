# Related problems and where compute actually binds

Each heading names one concrete option from framer.md, with which part of the root question it bears on, whether more parallel compute changes its answer (open / settled / none), and the sequential structure of one answer.

## Multiple shooting

The root question's scheme verbatim: guess the trajectory at every grid point, integrate each sub-interval from its guessed value in parallel, then force continuity with a Newton iteration (https://en.wikipedia.org/wiki/Direct_multiple_shooting_method).

- **Root link:** Q1 — whether a single long sequential simulation can be parallelised over time by guessing the whole trajectory and Newton-correcting every step at once.
- **Compute:** none (convergence is set by the Newton iteration, not by how many processors evaluate segments).
- **Sequential:** one answer is one trajectory needing k Newton iterations, each a forward substitution in which interval t's correction waits on interval t-1 (O(m) deep for m intervals), while the m segment integrations are independent and parallelise exactly; the correction chain is the only serial residue because J is block lower-bidiagonal (https://www.unige.ch/~gander/Preprints/parareal.pdf).

## Parareal

The cheap-Jacobian realisation of multiple shooting, introduced by Lions, Maday and Turinici: a coarse serial propagator predicts the trajectory and fine integrators correct each interval in parallel, iterating to convergence (https://parallel-in-time.org/methods/parareal.html).

- **Root link:** Q2 — whether the guess+Newton-correct trick only works when the system forgets its past — and Q1.
- **Compute:** none (the iteration count k is set by the forgetting rate, not the hardware).
- **Sequential:** each iteration marches a coarse propagator serially over all T subintervals (step t waits on t-1) while the T fine integrations are independent, so one run's depth is k·T, with k set by the forward decay of the coarse-guess error — Gander and Hairer show superlinear convergence only for contractive systems (https://www.unige.ch/~gander/Preprints/gander_plenary2007.pdf).

## MGRIT

The non-intrusive multigrid-reduction-in-time version of Parareal (shipped as XBraid), which coarsens the time grid rather than using a separate coarse model (https://computing.llnl.gov/projects/parallel-time-integration-multigrid).

- **Root link:** Q3 — whether compute is a blocker and could be fixed with massive GPU parallelism.
- **Compute:** settled — for parabolic (dissipative) PDEs MGRIT is demonstrated to be an optimal-scaling solver, and LLNL reports "tenfold or more" time-to-solution drops for compressible Navier-Stokes, so more parallel compute already pays off there (https://www.osti.gov/servlets/purl/1184744; https://computing.llnl.gov/projects/parallel-time-integration-multigrid).
- **Sequential:** one run keeps the same coarse/fine structure as Parareal — a coarse-grid correction sweeps the time levels in order while fine-grid integrations are independent — and the iteration count is set by the contraction (forgetting) rate, not processor count, so the causal coarse sweep cannot be reordered without cyclic reduction (https://computing.llnl.gov/projects/parallel-time-integration-multigrid).

## ParaDiag / ParaExp

Direct time-parallel methods for linear dynamics: x_T = A^T x_0 is computed by diagonalisation or repeated squaring in O(log T) depth, giving exact parallel-in-time with no forgetting assumption (https://www.unige.ch/~gander/siamtoc3.php).

- **Root link:** Q2's exception — the one regime where the causality principle can be cleanly side-stepped — and Q1.
- **Compute:** none.
- **Sequential:** none — the T sequential steps already collapse because the propagator A^T can be composed out of order by repeated squaring/diagonalisation in O(log T) parallel steps (https://www.unige.ch/~gander/siamtoc3.php).

## Cyclic reduction (PCR)

Parallel cyclic reduction solves the block-bidiagonal Newton correction (a tridiagonal/bidiagonal system) in O(log N) steps with N-fold parallelism, dropping the per-iteration depth of the PinT methods from O(T) to O(log T) (https://courses.grainger.illinois.edu/cs554/fa2015/notes/09_tridiagonal_8up.pdf).

- **Root link:** Q3 — the "shit ton of GPU parallelism" question — specifically whether width can shorten the cheap sequential part.
- **Compute:** settled — N-fold parallel cyclic reduction is known to solve a tridiagonal system in O(log N) steps instead of O(N), so more parallel compute already buys the O(T)→O(log T) per-iteration depth reduction (https://courses.grainger.illinois.edu/cs554/fa2015/notes/09_tridiagonal_8up.pdf).
- **Sequential:** the block-bidiagonal solve is a forward substitution in which row t waits on row t-1 (O(T) deep per iteration), but the rows need not run in order: cyclic reduction eliminates independent pairs simultaneously, which pays off only when the T equations can be halved each round and the machine has ~T processors to feed them (https://courses.grainger.illinois.edu/cs554/fa2015/notes/09_tridiagonal_8up.pdf).

## Speculative prefetching

The MCMC analog of guess+correct: speculatively evaluate many possible accept/reject branches in parallel, keep the true path, discard the rest, with a speedup that is bounded and constant-factor (https://lips.cs.princeton.edu/pdfs/angelino2014accelerating.pdf).

- **Root link:** Q2 for MCMC — whether the trick only works when the system forgets — and Q3's width-versus-depth point.
- **Compute:** none (mixing binds; prefetching only reduces latency with a bounded, constant-factor speedup).
- **Sequential:** one MH chain is a serial accept/reject sequence (each proposal waits on the previous accepted state, T steps per run), and prefetching speculates J future branches in parallel but keeps one path, giving O(log2 J) depth with J cores and expected speedup ≈1/α ≈ 4.3 at the 0.234 acceptance rate, largest when rejection dominates (https://lips.cs.princeton.edu/pdfs/angelino2014accelerating.pdf; https://arxiv.org/abs/1403.7265).

## Regeneration / splitting

Splitting an MCMC sampler at regeneration times yields i.i.d. tours that can be simulated in parallel, avoiding the bias of many short independent chains (https://galton.uchicago.edu/~mykland/paperlinks/MyklandTierneyYu2291148.pdf).

- **Root link:** Q2 for MCMC — regeneration is the operational "forgets its past" condition.
- **Compute:** none.
- **Sequential:** none — the tours between regeneration times are i.i.d. and already split into independent pieces that can run on separate processors, leaving only the mixing-governed length of one tour as the serial residue (https://galton.uchicago.edu/~mykland/paperlinks/MyklandTierneyYu2291148.pdf).

## Coupling from the past

Propp-Wilson exact sampling: run the chain from all possible states simultaneously under a monotone coupling, and coalescence certifies an exact draw, efficient only when coalescence (mixing) is fast (https://www.stat.berkeley.edu/~aldous/206-RWG/RWGpapers/propp_wilson.pdf).

- **Root link:** Q2 for MCMC — coalescence is the "forgets its past" condition.
- **Compute:** none.
- **Sequential:** none — the coupled chains run from all states in parallel under one monotone update, so the work already splits across states, and the only serial quantity is the coalescence time, which is set by mixing, not compute (https://www.stat.berkeley.edu/~aldous/206-RWG/RWGpapers/propp_wilson.pdf).

## Many-chain / data-parallel sampling (TFP HMC)

GPUs/TPUs add width two ways — many chains at once and data-parallel gradient/log-density evaluation within one chain — but width does not shorten a single chain's critical path (https://statmodeling.stat.columbia.edu/2022/11/13/stan-and-tensorflow-for-fast-parallel-bayesian-inference/).

- **Root link:** Q3 — the GPU question — specifically the width-versus-depth distinction.
- **Compute:** open — the quantity more parallel compute would buy is the number of independent chains/seeds analysed: Angelino et al. show running many chains "does not change the mixing time for any single chain" (https://lips.cs.princeton.edu/pdfs/angelino2014accelerating.pdf), and no cited source establishes whether adding more chains/seeds above that changes the posterior estimate (e.g. finds additional modes).
- **Sequential:** none — many chains and within-chain data-parallel likelihoods are already independent pieces, so the answer already splits across GPUs, and the per-chain critical path (T × per-step cost × mixing overhead) is unchanged by width (https://statmodeling.stat.columbia.edu/2022/11/13/stan-and-tensorflow-for-fast-parallel-bayesian-inference/).

## GLUE / rainfall-runoff calibration

The actual compute burden in daily-step rainfall-runoff modelling is Monte-Carlo parameter calibration and GLUE uncertainty analysis, parallelised with MPI/OpenMP/CUDA across parameter sets, explicitly not across time steps (https://doi.org/10.3390/w15152810).

- **Root link:** Q3 — the hydrology example showing compute is not a time-dimension blocker.
- **Compute:** settled — the compute burden is parameter calibration/GLUE uncertainty, parallelised across parameter sets (embarrassingly parallel, never across time), so more parallel compute already buys parameter-set throughput, not time-step depth (https://doi.org/10.3390/w15152810; https://www.mdpi.com/2073-4441/12/10/2667).
- **Sequential:** none — each parameter set is one cheap forward run of a lumped model and parameter sets are independent, so the work already splits into independent pieces with no serial time chain to shorten (https://doi.org/10.3390/w15152810).

## Chaotic / non-forgetting PinT

On chaotic systems (Lorenz, hyperbolic PDEs) the coarse-guess error is amplified forward, so Parareal diverges or its superlinear convergence stops, because chaotic initial value problems are inherently ill-conditioned (https://www.osti.gov/servlets/purl/1880928; https://arxiv.org/abs/2201.10441).

- **Root link:** Q2 — whether the trick only works when the system forgets — here the non-forgetting failure mode.
- **Compute:** open — the quantity more parallel compute would buy is the coarse-grid resolution or number of processors fed to the coarse propagator: published results stop at divergence ("parareal diverging in many cases", https://www.osti.gov/servlets/purl/1880928), and whether scaling coarse-grid fidelity or iteration count changes convergence above that is unresolved (https://arxiv.org/abs/2201.10441).
- **Sequential:** the coarse propagator must march the time levels in order (step t waits on t-1), so one run's depth is T × k iterations, and the positive-Lyapunov amplification means the iterations cannot be collapsed by reordering the causal chain; the nearest attempt at a fix is the coarse-grid-correction study in (https://arxiv.org/abs/2201.10441).
