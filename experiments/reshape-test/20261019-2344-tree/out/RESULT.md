# Result

Picks 2 · PASS 1 · on-goal cards U4 0 · U3 1 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [R1·interp·Linear feature representation -> parallel-in-time for free](#card-R1-interp-Linear-feature-representation---parallel-in-time-for-free) SAE features give the linear basis that triggers the framer's no-forgetting parallel-in-time exception | PASS 2/2 | top 1/4 · SAME | if_not | 3 | 5 → 5 | 5 → 3 narrowed | 5 | 1 | 1 → 3 | — | $202 at phase_compose · plan $202 · 3 GUESS |
| [R1·phys·Cyclic reduction (PCR)](#card-R1-physical-Cyclic-reduction-PCR-) Parallel cyclic reduction | REJECT (3 blocking) | top 7/11 · SAME, tie of 2 broken by seeded order | if_lever | 5 | 1 → 5 | 3 → 3 | 5 | — | 5 → 4 | 5 | $12 at p2_sweep · plan $12 · 2 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-R1-physical-Cyclic-reduction-PCR-"></a>**Cyclic reduction (PCR) · Parallel cyclic reduction.** R1 · physical · top pick · distance SAME · compute tested: yes · plan expects: the lever · REJECT

**Question.** Does feeding many GPUs to the block-tridiagonal Newton solve shorten its depth from T ordered steps to log2(T)?

**What is known.** Zhang, Cohen and Owens benchmarked cyclic reduction, PCR and recursive doubling on a GTX 280, finding PCR does fewer steps, more work, and 28x over sequential LAPACK [s2]. No published result times PCR against an on-GPU sequential Thomas on a modern A100 across N up to 2^24, so the crossover is unmeasured.

**Hypothesis.** Parallel cyclic reduction solves the tridiagonal Newton correction in log2(T) rounds instead of T, so GPU width shortens the sequential part [s3].

**Restructuring.** The block-bidiagonal Newton correction is a forward substitution: each row waits on the previous, T ordered steps. Cyclic reduction halves the system each round and solves independent rows together, so log2(T) rounds replace T ordered steps [s3].

**If compute is the lever.** As equation count N grows, cyclic-reduction wall-clock grows like log2(N) and beats the sequential Thomas solve by a widening margin.

**If not.** At feasible N the parallel solver never beats sequential: extra work and memory traffic dominate, and one GPU has too few threads to hide them.

**Test.** Time a sequential Thomas tridiagonal solve against parallel cyclic reduction on one A100, sweeping N=2^10 to 2^24, checking both match NVIDIA's gtsv reference and batched independent solves.

*Compute axis.* Number of equations (time steps) in one tridiagonal Newton correction: 1,024–16,777,216 equations, 5 levels. Closest prior: not on this axis.

**Check first.** Written PCR and Thomas kernels must match NVIDIA's gtsv tridiagonal solve and a CPU dense solve to 1e-10 relative residual.

**Would not show.** Shows one tridiagonal solve's wall-clock scaling on one modern GPU, not the end-to-end parallel-in-time method, whose iteration count the dynamics sets.

*Cost.* Plans $11.94 of the $1,000 budget over 6 machine-hours, leaving $988.06. Main guess: expected max relative residual of PCR/Thomas vs reference [g], measured after $0 of spend.

**Judges.** Dramaturg: REJECT (3 blocking). Decides at: $12 at p2_sweep · plan $12 · 2 GUESS (critic: p2_sweep records all N medians, satisfying decision rule for either lever or not).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-20
Spend      p2_sweep  Anchor (p1) + full scalar sweep (p2) on one A100 40GB  1x NVIDIA A100 SXM 40GB $1.99/h  6 h [d]  $11.94  time box; need 2 h (margin 3.00×)
           p3_block  Block-tridiagonal stretch (d=4,16)  1x NVIDIA A100 SXM 40GB $1.99/h  4 h [d]  $7.96  time box; need 2 h (margin 2.00×)  optional
           p4_multi  2- and 8-GPU PCR stretch  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  2 h [d]  $31.84  time box; need 1 h (margin 2.00×)  optional
           Planned $11.94 · unallocated $988.06 · with options $51.74 · cap $1,000
Rests on   expected max relative residual of PCR/Thomas vs reference 1e-13 relative residual [g] rests on: float64 rounding of an O(N) recurrence against a dense solve; diagonal dominance keeps Thomas and PCR stable · measured in p1_anchor ($0 spent by then) · gate expected max relative residual of PCR/Thomas vs reference ≤ 1e-10 in p1_anchor (now 1e-13, passes; uncut plan at it $11.94), else Fix the kernels and re-run the anchor before starting the sweep. · budget not reached within 1000×
           N where PCR first beats Thomas 1,020 equations [g] rests on: on-GPU single-thread Thomas pays roughly one memory latency per dependent step, so its time grows ~N x latency, while PCR's log2(N) rounds are bandwidth-bound microseconds; PCR should already win at the smallest level · measured in p2_sweep ($11.94 spent by then) · budget not reached within 1000×
           PCR/Thomas speedup at n_max 28 x [p] "Our GPU solvers achieve up to a 28x speedup over a sequential LAPACK solver, and a 12x speedup over a multi-threaded CPU solver." · differs: 2009 GTX 280 (30 SMs) vs 2020 A100 (108 SMs, 1555 GB/s), baseline CPU LAPACK dgtsv vs my on-GPU Thomas kernel, their N ~ hundreds vs my N up to 2^24 · measured in p2_sweep ($11.94 spent by then) · budget not reached within 1000×
Scenarios  PCR is memory-bound and never reaches 2x within the tested N → $11.94
Buys       largest sweep level: 16.8M [d] · PCR is memory-bound and never reaches 2x within the tested N: 16.8M
           N where PCR first beats Thomas: 1,020 [g] · PCR is memory-bound and never reaches 2x within the tested N: 16.8M
           PCR/Thomas speedup at n_max: 28 [p] · PCR is memory-bound and never reaches 2x within the tested N: 1
Flags      none
Full scale PCR wired into a real Parareal/MGRIT Newton loop on a dissipative PDE, T=2^26, timed end-to-end: $1,146.24 = 1.15× budget = 0.0000683× largest sweep level · inputs 1 c
           Largest single solve T=2^30 double-precision plus 16-GPU PCR: $764.16 = 0.764× budget = 0.0000455× largest sweep level · inputs 1 c
Outside    producer engineering time (CUDA kernels, harness, analysis): 10 hours · local 4-core CPU for reference testing: 1 hours
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
n_parallel_rounds = 24 = 24 rounds
fs_pint_e2e = 8*per_gpu_usd_h_a100*72 = 8 * 1.99 * 72 = 1146.24 usd
fs_t2p30 = 16*per_gpu_usd_h_a100*24 = 16 * 1.99 * 24 = 764.16 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:hypothesis` PARTIAL · page: "The Thomas algorithm, based on LU decomposition, is efficient to solve tridiagonal systems but inherently sequential, while the PCR algorithm is more computationally expensive but parallelizable." · note: s3 supports the parallel-vs-sequential contrast (Thomas sequential, PCR parallelizable) behind 'GPU width shortens the sequential part', but the page does not state the specific 'log2(T) rounds instead of T' figure.
- sample 1 · `card:sequential_part` UNSUPPORTED · page: "" · note: Factual claim that the block-bidiagonal Newton correction is a forward substitution with T ordered steps; it cites no source.
- sample 1 · `card:method` PARTIAL · page: "The Thomas algorithm, based on LU decomposition, is efficient to solve tridiagonal systems but inherently sequential, while the PCR algorithm is more computationally expensive but parallelizable." · note: s3 confirms PCR is parallelizable, but the page does not describe cyclic reduction 'halving the system each round' or state 'log2(T) rounds' replacing T ordered steps.
- sample 1 · `card:if_lever` UNSUPPORTED · page: "" · note: Asserts as fact that cyclic-reduction wall-clock grows like log2(N) and beats sequential Thomas by a widening margin; no source cited.
- sample 1 · `card:if_not` UNSUPPORTED · page: "" · note: Asserts as fact that extra work and memory traffic dominate and one GPU has too few threads to hide them; no source cited.
- sample 1 · `card:left_open` UNSUPPORTED · page: "" · note: Claim that no published result times PCR against an on-GPU sequential Thomas on a modern A100 up to N=2^24; no source cited for this literature-gap claim.
- sample 2 · `card:hypothesis` PARTIAL · page: "The Thomas algorithm, based on LU decomposition, is efficient to solve tridiagonal systems but inherently sequential, while the PCR algorithm is more computationally expensive but parallelizable." · note: The cited s3 page (fetched) supports the load-bearing contrast — Thomas inherently sequential, PCR parallelizable — hence 'GPU width shortens the sequential part'. But the page nowhere states the round counts 'log2(T) rounds instead of T'; that quantitative claim is absent from the cited source (it appears in the uncited Zhang et al. paper: 'CR requires 2 log 2 n - 1 steps while the Thomas algorithm requires 2n steps').
- sample 2 · `card:method` PARTIAL · page: "The Thomas algorithm, based on LU decomposition, is efficient to solve tridiagonal systems but inherently sequential, while the PCR algorithm is more computationally expensive but parallelizable." · note: s3 supports the sequential-Thomas vs parallel-PCR contrast that motivates replacing T ordered steps, but the cited page says nothing about cyclic reduction halving the system each round, solving independent rows together, or the log2(T) round count — those mechanism claims are not covered by the cited source (the uncited Zhang paper states 'CR requires 2 log 2 n - 1 steps while the Thomas algorithm requires 2n steps' and 'PCR takes 12n log 2 n operations and log 2 n steps to finish').
- sample 2 · `card:left_open` UNSUPPORTED · page: "N/A — no source cited for the item." · note: A negative claim about the published literature (no published result times PCR against an on-GPU sequential Thomas on a modern A100 up to 2^24) is a factual claim and is given with no source; the fetched pages (NVIDIA gtsv docs, Zhang et al. 2009/2010, Lambda pricing) neither state nor establish that absence.

**Critic.**
- stakes 3 · `card:limits` "Shows one tridiagonal solve's wall-clock scaling on one modern GPU, not the end-to-end parallel-in-time method, whose iteration count the dynamics sets." · Measures scalar tridiagonal solve, not full Newton-in-time loop; adoption depends on unmeasured iteration count and block size.
- lever 5 · `plan:predictions.noise_rule` "Five repeats per (solver, N) on one A100; report median and interquartile range; a real difference is a speedup whose lower quartile still exceeds 1 (and 2 at n_max)." · 2x threshold with quartiles, 16384x N span, fixed hardware/structure; arms differ only method.
- verifiable 5 · `card:anchor` "Written PCR and Thomas kernels must match NVIDIA's gtsv tridiagonal solve and a CPU dense solve to 1e-10 relative residual." · PCR and Thomas are checked against cuSPARSE/scipy exact references with 1e-10 tolerance before sweep.
- open 5 · `card:left_open` "No published result times PCR against an on-GPU sequential Thomas on a modern A100 across N up to 2^24, so the crossover is unmeasured." · No prior times PCR against on-GPU Thomas on A100 to N=2^24; gap stated.
- reshape 4 · `card:closest_prior` "Zhang, Cohen and Owens benchmarked cyclic reduction, PCR and recursive doubling on a GTX 280, finding PCR does fewer steps, more work, and 28x over sequential LAPACK [s2]." · Names forward-substitution dependency, removes ordering via cyclic reduction, condition measured in p1_anchor; but prior already ran PCR on GPU tridiagonal systems.
- baseline 5 · `card:anchor` "Written PCR and Thomas kernels must match NVIDIA's gtsv tridiagonal solve and a CPU dense solve to 1e-10 relative residual." · Tuned CUDA Thomas, same-GPU batched copies, anchored to references, and p2 times all arms.

**Option critic.**
- stakes 3: Could guide processor purchases, but depth reduction already known.
- open 1: compute_open settled; published PCR already covers the reachable depth reduction.
- reshape 5: Names forward-substitution chain O(T); ~T processors and halving condition checkable; no source parallelizes this correction system.
- distance SAME: Asks root Q3 sub-question: can width shorten the serial Newton correction chain.

**Producer says (not judged).** expected if_lever (Cyclic reduction's logarithmic depth is textbook and Zhang et al. already measured large GPU speedups over sequential tridiagonal solves [s2].); compute_tested yes (The test varies N, the system size, and measures whether the parallel PCR solver's depth grows as log2(N) while sequential Thomas grows as N, which is exactly the depth reduction more parallel compute is claimed to buy.); decides partly; searched yes.

**Annotations.**
- option_title mismatch: plan "Cyclic reduction (PCR)", pick "Parallel cyclic reduction" (re-key if it is another option in this branch)
- hypothesis: a sentence of 22 words
- predictions.if_not: a sentence of 25 words
- test_summary: a sentence of 27 words
- novelty.closest_prior: a sentence of 28 words
- novelty.left_open: a sentence of 24 words
- limits: a sentence of 21 words
- dramaturg findings failed G-find after a resample; decided as returned

**Root question (R1).** Can one long sequential simulation, like a single MCMC chain or a rainfall-runoff model stepped through decades of daily rainfall, be parallelised over time by guessing the whole trajectory and then correcting every step at once with Newton iterations, and does that only work when the system forgets its past? Is compute a major blocker at some level, and could that be fixed with a shit ton of GPU parallelism?

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/reshape-test/20261019-2344-tree/out/work/seed-1/R1/physical/e01a75ff/producer.md)

---

```json
{
 "pick": {
  "key": "R1:interp:Linear feature representation -> parallel-in-time for free",
  "root": "R1",
  "branch": "interp",
  "kind": "top",
  "rank": 1,
  "total": 14,
  "tie_note": "",
  "replaced": [],
  "id": "Linear feature representation -> parallel-in-time for free",
  "title": "SAE features give the linear basis that triggers the framer's no-forgetting parallel-in-time exception"
 },
 "option": {
  "id": "Linear feature representation -> parallel-in-time for free",
  "title": "SAE features give the linear basis that triggers the framer's no-forgetting parallel-in-time exception",
  "summary": "If the residual-stream trajectory is a linear combination of sparse features, the per-step feature transition is (approximately) linear and x_T = A^T x_0 is computable in O(log T) depth by repeated squaring / diagonalisation (the framer's ParaDiag exception), with no forgetting needed. Goodfire-style SAEs supply the linear decomposition; the open question is whether the feature-to-feature transition is stable enough to compose out of order.",
  "root_link": "It bears on the 'can a long sequential simulation be parallelised over time by guessing and correcting' clause: it is the one regime where the answer is yes without needing the system to forget.",
  "compute_open": "More parallel compute buys more models, layers, and features analysed to test feature-level linearity; published evidence stops at linear representations of concepts in LLaMA-2 7B (https://arxiv.org/abs/2311.03658) and SAE decompositions of up to 34M features on one middle layer of Claude 3 Sonnet (https://transformer-circuits.pub/2024/scaling-monosemanticity/); unknown above that is whether the residual stream's feature-to-feature transition is linear and time-invariant across all layers and long contexts.",
  "sequential": "none: checking linearity is a per-feature regression/probe fit that is independent across features, layers, and models, so it already splits into parallel pieces with no step waiting on another.",
  "source_urls": [
   "https://arxiv.org/abs/2311.03658",
   "https://transformer-circuits.pub/2024/scaling-monosemanticity/",
   "https://www.unige.ch/~gander/siamtoc3.php"
  ],
  "distance": "SAME",
  "distance_reason": "Asks whether linear feature transitions enable the root's O(log T) parallel-in-time exception.",
  "scores": [
   {
    "criterion": "stakes",
    "value": 5,
    "reason": "Yes would enable parallel-in-time inference, shifting a build choice; no would block that route."
   },
   {
    "criterion": "open",
    "value": 5,
    "reason": "Names models/layers/features; published stops at LLaMA-2 7B and one SAE layer; next layers reachable."
   },
   {
    "criterion": "internals",
    "value": 4,
    "reason": "Names feature-to-feature linear transition, but does not state what outputs miss."
   },
   {
    "criterion": "reshape",
    "value": 1,
    "reason": "Sequential says none; linearity checks are independent per-feature regressions, no step-waiting chain."
   }
  ],
  "key": "R1:interp:Linear feature representation -> parallel-in-time for free",
  "root": "R1",
  "branch": "interp",
  "compute_open_status": "open",
  "sequential_status": "none",
  "total": 14
 },
 "root_question": "Can one long sequential simulation, like a single MCMC chain or a rainfall-runoff model stepped through decades of daily rainfall, be parallelised over time by guessing the whole trajectory and then correcting every step at once with Newton iterations, and does that only work when the system forgets its past? Is compute a major blocker at some level, and could that be fixed with a shit ton of GPU parallelism?",
 "plan": {
  "option_title": "SAE features give the linear basis that triggers the framer's no-forgetting parallel-in-time exception",
  "question": "Can SAE feature coordinates make a transformer's layer-to-layer transition linear enough to compose out of order by repeated squaring, giving parallel-in-time depth [s_pdiag]?",
  "hypothesis": "If residual-stream layers are near-linear in SAE features, repeated squaring composes the trajectory in O(log T) depth with no forgetting [s_pdiag].",
  "compute_axis": {
   "quantity": "model depth over which the linear feature transition is composed out of order and scored",
   "unit": "layers",
   "levels": [
    1,
    10,
    20,
    30,
    42
   ]
  },
  "held_fixed": [
   "Gemma 2 9B model",
   "Gemma Scope 131K residual-stream SAE (all 42 layers)",
   "1024-token context",
   "2,000,000 tokens total",
   "fit on 1,500 train sequences, score on 453 held-out sequences"
  ],
  "predictions": {
   "if_lever": "Composed out-of-order prediction reconstructs at least 90% of true activations at all 42 layers, so the linear ParaDiag shortcut holds.",
   "if_not": "Composed prediction falls below 90% reconstruction and decays with depth, so residual nonlinearity breaks out-of-order composition.",
   "decision_rule": "if_lever iff the composed out-of-order prediction explains at least 90% (decision_threshold) of true next-layer activation variance, averaged over all 42 layers and held-out contexts; below 90% and decaying with depth is if_not.",
   "noise_rule": "Fit on 1,500 train sequences, score on 453 held-out sequences; report mean composed R² with a 95% CI over 5 random held-out shards; a real difference is one whose CI excludes the 0.90 threshold.",
   "expected": "if_not",
   "expected_why": "Published linear-transport R² already decays with layer distance and depth [s_ato], so a 42-layer linear propagator is unlikely to stay above 90%."
  },
  "compute_tested": "yes",
  "compute_tested_why": "The plan sweeps composition depth (1 to 42 layers) and SAE width (16.4K to 1M); each fit is independent across features, layers and models, so more GPUs buy more depth and width analysed in the same wall-clock, though the absolute work is only a few GPU-hours.",
  "scored_against": "the model's true sequential forward-pass activations (per token, per layer) on the same held-out sequences, at matching depth.",
  "arms": [
   {
    "id": "arm_seq",
    "what": "True sequential forward pass of Gemma 2 9B and LLaMA-2 7B, caching all 42 (32) layer residuals - ground truth and data source."
   },
   {
    "id": "arm_gemma_131k",
    "what": "Gemma 2 9B with Gemma Scope 131K residual SAEs at all 42 layers; fit and compose the feature transition."
   },
   {
    "id": "arm_gemma_16k",
    "what": "Gemma 2 9B with Gemma Scope 16.4K residual SAEs at all 42 layers (width check)."
   },
   {
    "id": "arm_gemma_1m",
    "what": "Gemma 2 9B with Gemma Scope 1M residual SAEs at layers 9, 20, 31 (widest width, partial depth)."
   },
   {
    "id": "arm_llama_direct",
    "what": "LLaMA-2 7B d_model (4096) basis, no SAE: direct linear probe x_{l+1} ~ A_l x_l at all 32 layers."
   }
  ],
  "baseline": {
   "what": "The model's true sequential forward pass (token-by-token, layer-by-layer), the ground-truth trajectory each composed prediction is scored against."
  },
  "anchor": {
   "what": "SAE encoder-decoder round-trip reproduces released weights to relative error under 1e-5; composition code matches sequential on a synthetic linear system.",
   "published_value": 0.65,
   "tolerance": "relative error < 1e-5 on the SAE round-trip; < 1e-8 on the synthetic repeated-squaring-vs-sequential check.",
   "source_id": "s_scaling_mono",
   "independent_code": "bab1ad22/pilot/compose_check.py"
  },
  "checks": [
   "Pilot: repeated-squaring composition equals sequential within 1e-8 on a synthetic linear system.",
   "SAE encoder-decoder round-trip reproduces the released weights' reconstruction to relative error < 1e-5.",
   "Per-layer linear fit R² reported separately from composed multi-layer R², to separate per-layer nonlinearity from accumulation.",
   "Composition uses the same A_l in in-order (A_42...A_1) and out-of-order (repeated-squaring) products; the two must agree to < 1e-6 before scoring.",
   "Time-invariance: A_l fit on train contexts, scored on held-out contexts; report the train/held-out R² gap."
  ],
  "phases": [
   {
    "id": "phase_pilot",
    "what": "Run the local synthetic check: repeated-squaring composition must equal sequential; print the error. Free, on the 4-core machine.",
    "stop_rule": "ends when the script prints the composition error and the least-squares GFLOPS."
   },
   {
    "id": "phase_env",
    "what": "Launch the 8x H100 SXM instance; install transformers/SAELens; download Gemma 2 9B, LLaMA-2 7B, and Gemma Scope 16.4K/131K (all layers) and 1M (layers 9,20,31) SAEs; run a matmul micro-benchmark.",
    "stop_rule": "ends when a 1-token forward plus SAE round-trip runs and the micro-benchmark prints effective TFLOPS."
   },
   {
    "id": "phase_forward",
    "what": "Sequential forward pass over 2M tokens (1,953 x 1024) for both models; encode features at all widths, streamed to per-layer covariance.",
    "stop_rule": "ends when all 42 (32) layers are encoded and covariance matrices are written."
   },
   {
    "id": "phase_anchor",
    "what": "Verify the SAE encoder-decoder round-trip reproduces the released weights' reconstruction.",
    "stop_rule": "ends when the round-trip relative error is printed.",
    "gate": {
     "on": "recon_roundtrip_err",
     "op": "<=",
     "value": 0.00001,
     "else": "fall back to the d_model-only LLaMA-2 arm and drop the SAE feature arms."
    }
   },
   {
    "id": "phase_fit",
    "what": "Per layer, fit the linear feature transition A_l (feature basis; d_model basis for LLaMA-2); report per-layer R² and the train/held-out gap.",
    "stop_rule": "ends when per-layer R² is reported for all layers and widths."
   },
   {
    "id": "phase_compose",
    "what": "Compose A_l out of order by repeated squaring/diagonalisation to depth 1/10/20/30/42; score composed reconstruction R² against sequential truth.",
    "stop_rule": "ends when composed R² at 42 layers is printed with a 95% CI over 5 held-out shards.",
    "gate": {
     "on": "composed_r2",
     "op": ">=",
     "value": 0.9,
     "else": "record if_not and write up; the width sweep becomes optional."
    }
   },
   {
    "id": "phase_width",
    "what": "Repeat fit plus compose at 16.4K and 1M widths to get the R²-vs-width curve.",
    "stop_rule": "ends when the width curve is plotted."
   }
  ],
  "numbers": [
   {
    "id": "n_tokens",
    "name": "tokens run through the forward pass",
    "unit": "tokens",
    "basis": "DESIGN",
    "value": 2000000
   },
   {
    "id": "seq_len",
    "name": "context length per sequence",
    "unit": "tokens",
    "basis": "DESIGN",
    "value": 1024
   },
   {
    "id": "n_seq",
    "name": "independent context sequences",
    "unit": "sequences",
    "basis": "DERIVED",
    "expr": "n_tokens / seq_len"
   },
   {
    "id": "n_train_seq",
    "name": "sequences used to fit the transition",
    "unit": "sequences",
    "basis": "DESIGN",
    "value": 1500
   },
   {
    "id": "n_holdout_seq",
    "name": "sequences held out to score the transition",
    "unit": "sequences",
    "basis": "DERIVED",
    "expr": "n_seq - n_train_seq"
   },
   {
    "id": "layers_gemma9b",
    "name": "Gemma 2 9B layers",
    "unit": "layers",
    "basis": "CITED",
    "value": 42,
    "source_id": "s_gemma2",
    "quote": "d_model | 2304 | 3584 | 4608 ... Layers | 26 | 42 | 46 (9B column: d_model 3584, 42 layers)"
   },
   {
    "id": "d_model_gemma9b",
    "name": "Gemma 2 9B model dimension",
    "unit": "count",
    "basis": "CITED",
    "value": 3584,
    "source_id": "s_gemma2",
    "quote": "d_model | 2304 | 3584 | 4608 (9B column)"
   },
   {
    "id": "layers_llama2",
    "name": "LLaMA-2 7B layers",
    "unit": "layers",
    "basis": "CITED",
    "value": 32,
    "source_id": "s_llama2",
    "quote": "num_hidden_layers (`int`, optional, defaults to `32`) — Number of hidden layers in the Transformer decoder."
   },
   {
    "id": "d_model_llama2",
    "name": "LLaMA-2 7B model dimension",
    "unit": "count",
    "basis": "CITED",
    "value": 4096,
    "source_id": "s_llama2",
    "quote": "hidden_size (`int`, optional, defaults to `4096`) — Dimension of the hidden representations."
   },
   {
    "id": "params_gemma9b",
    "name": "Gemma 2 9B parameters",
    "unit": "parameters",
    "basis": "CITED",
    "value": 9000000000,
    "source_id": "s_gemma2",
    "quote": "Parameters | 2B | 9B | 27B"
   },
   {
    "id": "params_llama2",
    "name": "LLaMA-2 7B parameters",
    "unit": "parameters",
    "basis": "CITED",
    "value": 7000000000,
    "source_id": "s_llama2_params",
    "quote": "we develop and release Llama 2, a collection of pretrained and fine-tuned large language models (LLMs) ranging in scale from 7 billion to 70 billion parameters."
   },
   {
    "id": "sae_w16",
    "name": "Gemma Scope 16.4K SAE width",
    "unit": "features",
    "basis": "CITED",
    "value": 16384,
    "source_id": "s_gemma_scope",
    "quote": "| 9B PT | 2^14 | All | All | All | 4B | (42 layers)"
   },
   {
    "id": "sae_w131",
    "name": "Gemma Scope 131K SAE width (all layers)",
    "unit": "features",
    "basis": "CITED",
    "value": 131072,
    "source_id": "s_gemma_scope",
    "quote": "| 9B PT | ... | 2^17 | All | All | All | 8B | (42 layers)"
   },
   {
    "id": "sae_w1m",
    "name": "Gemma Scope 1M SAE width (layers 9,20,31)",
    "unit": "features",
    "basis": "CITED",
    "value": 1048576,
    "source_id": "s_gemma_scope",
    "quote": "| 9B PT | ... | 2^20 | ✗ | ✗ | { 9, 20, 31} | 16B | (42 layers)"
   },
   {
    "id": "max_features_published",
    "name": "published largest SAE feature count",
    "unit": "features",
    "basis": "CITED",
    "value": 33554432,
    "source_id": "s_scaling_mono",
    "quote": "We trained three SAEs of varying sizes: 1,048,576 (~1M), 4,194,304 (~4M), and 33,554,432 (~34M) features."
   },
   {
    "id": "recon_var_published",
    "name": "published SAE reconstruction variance fraction",
    "unit": "fraction",
    "basis": "CITED",
    "value": 0.65,
    "source_id": "s_scaling_mono",
    "quote": "For all three SAEs, the average number of features active (i.e. with nonzero activations) on a given token was fewer than 300, and the SAE reconstruction explained at least 65% of the variance of the model activations."
   },
   {
    "id": "ato_r2_adjacent",
    "name": "published adjacent-layer feature-transport R²",
    "unit": "R²",
    "basis": "CITED",
    "value": 0.95,
    "source_id": "s_ato",
    "quote": "those trained for small leaps (k = 1, k = 4 for target layer 10) successfully transport a significant number of features (R2 > 0.95)."
   },
   {
    "id": "ato_max_leap",
    "name": "published largest layer leap for linear transport",
    "unit": "layers",
    "basis": "CITED",
    "value": 10,
    "source_id": "s_ato",
    "quote": "Figure 4: Transport efficiency for the target layer 10 with different leap (k) values (k=1,3,7,10)."
   },
   {
    "id": "gpu_eff_tflops",
    "name": "effective TFLOPS per H100 for SAE encode",
    "unit": "TFLOPS",
    "basis": "PROXY",
    "value": 200,
    "source_id": "s_h100",
    "quote": "TF32 Tensor Core | 989 TFLOPS* ... * Shown with sparsity. Specifications 1/2 lower without sparsity.",
    "page_setting": "NVIDIA H100 SXM datasheet peak TF32 throughput (494.5 TFLOPS dense)",
    "differs_in": [
     "real-world matmul efficiency below the dense TF32 peak for JumpReLU/SAE kernels"
    ],
    "measured_by": "phase_env"
   },
   {
    "id": "overhead",
    "name": "wall-clock overhead multiplier over pure FLOPs",
    "unit": "x",
    "basis": "GUESS",
    "value": 10,
    "rests_on": "Python, sparse JumpReLU kernels and small-batch data loading typically cost roughly 10x over pure matmul on this workload",
    "measured_by": "phase_forward"
   },
   {
    "id": "total_flops",
    "name": "total FLOPs for forward plus encode at all widths",
    "unit": "FLOP",
    "basis": "DERIVED",
    "expr": "n_tokens * (4 * d_model_gemma9b * (layers_gemma9b * (sae_w16 + sae_w131) + 3 * sae_w1m) + 2 * (params_gemma9b + params_llama2))"
   },
   {
    "id": "hours_forward",
    "name": "wall-clock compute hours for the forward plus encode pass",
    "unit": "hours",
    "basis": "DERIVED",
    "expr": "total_flops / (gpu_eff_tflops * 1e12 * 8) / 3600 * overhead"
   },
   {
    "id": "decision_threshold",
    "name": "composed reconstruction threshold deciding if_lever",
    "unit": "R²",
    "basis": "DESIGN",
    "value": 0.9
   },
   {
    "id": "recon_roundtrip_err",
    "name": "SAE round-trip relative error reproduced",
    "unit": "relative error",
    "basis": "GUESS",
    "value": 0.00001,
    "rests_on": "released SAE weights are fixed, so a correct implementation reproduces them to floating-point precision",
    "measured_by": "phase_anchor"
   },
   {
    "id": "composed_r2",
    "name": "composed out-of-order reconstruction R² at 42 layers",
    "unit": "R²",
    "basis": "GUESS",
    "value": 0.5,
    "rests_on": "published linear transport R² decays with layer distance and depth [s_ato], so a 42-layer composition should fall well below 0.9",
    "measured_by": "phase_compose"
   }
  ],
  "cost": {
   "rates": [
    {
     "id": "rate_h100_8x",
     "gpu": "NVIDIA H100 SXM",
     "gpu_memory_gb": 80,
     "n_gpus": 8,
     "per_gpu_usd_h": 3.99
    }
   ],
   "lines": [
    {
     "id": "line_setup",
     "phase": "phase_env",
     "what": "instance setup, downloads, environment, matmul micro-benchmark",
     "kind": "allotment",
     "rate": "rate_h100_8x",
     "hours": 2,
     "need": 1
    },
    {
     "id": "line_forward",
     "phase": "phase_forward",
     "what": "sequential forward pass and SAE encode at all widths",
     "kind": "allotment",
     "rate": "rate_h100_8x",
     "hours": 2,
     "need": "hours_forward"
    },
    {
     "id": "line_analyze",
     "phase": "phase_fit",
     "what": "fit, compose, and width analysis (phase_fit, phase_compose, phase_width)",
     "kind": "allotment",
     "rate": "rate_h100_8x",
     "hours": 2,
     "need": 0.5
    },
    {
     "id": "line_headroom",
     "phase": "phase_width",
     "what": "re-runs, more tokens, longer contexts, extra models",
     "kind": "allotment",
     "rate": "rate_h100_8x",
     "hours": 2,
     "need": 0,
     "optional": true
    },
    {
     "id": "line_storage",
     "phase": "phase_forward",
     "what": "50 GiB persistent filesystem for covariances, results, and SAE weights",
     "kind": "storage",
     "usd": "50 * fs_usd_gib_month"
    }
   ],
   "scenarios": [
    {
     "id": "scen_slow",
     "what": "pessimistic: SAE kernels at 50 TFLOPS effective and 20x overhead",
     "set": {
      "gpu_eff_tflops": 50,
      "overhead": 20
     }
    },
    {
     "id": "scen_more",
     "what": "sensitivity: 10M tokens for tighter confidence intervals",
     "set": {
      "n_tokens": 10000000
     }
    }
   ],
   "yields": [
    "n_seq",
    "sae_w1m",
    "sae_w131",
    "layers_gemma9b",
    "seq_len"
   ],
   "spend_cap_usd": 1000,
   "total_stated": 265.36
  },
  "full_scale": [
   {
    "id": "full_scale_34m",
    "what": "train 34M-feature SAEs across all 42 layers of an open 70B model and rerun the composition test (published record is 34M on one middle layer) - rough estimate, 32x the 1M width",
    "usd": 38400,
    "ratio_to": "sae_w1m"
   },
   {
    "id": "full_scale_multi",
    "what": "repeat the 131K all-layer sweep on three more open model families (LLaMA-3 8B, Mistral 7B, Qwen 1.5 7B)",
    "usd": 1200,
    "ratio_to": "layers_gemma9b"
   }
  ],
  "outside_budget": [
   {
    "what": "human engineering time to write the SAE hook, regression, and composition code",
    "qty": 40,
    "unit": "hours"
   },
   {
    "what": "human analysis and write-up time",
    "qty": 20,
    "unit": "hours"
   },
   {
    "what": "desk review of sources",
    "qty": 8,
    "unit": "hours"
   }
  ],
  "restructuring": {
   "sequential_part": "None: each per-feature linearity fit is independent of the others, so no answer waits step after step.",
   "method": "none"
  },
  "scope_gap": [
   "Whether the result transfers to a proprietary 70B+ model like Claude 3 Sonnet (34M features, closed weights).",
   "Whether a composed feature propagator reproduces exact next-token outputs (a shipped parallel sampler), not just residual reconstruction.",
   "Time-invariance beyond a 1024-token context."
  ],
  "novelty": {
   "closest_prior": "Prior work (Activation Transport Operators) measured per-feature R² of linear layer-to-layer maps up to a 10-layer leap on a small open model, in under 50 GPU-hours [s_ato].",
   "closest_source_id": "s_ato",
   "prior_max_level": 10,
   "left_open": "It did not compose operators out of order over full depth, sweep SAE width, or test time-invariance across contexts on a production-scale model.",
   "decides": "partly",
   "searched": true
  },
  "limits": [
   "Holds for open Gemma/LLaMA models and released SAEs, not Claude 3 Sonnet's 34M features; it measures linearity, not a shipped parallel sampler."
  ],
  "test_summary": "Fit per-layer linear feature transitions (Gemma 2 9B, Gemma Scope SAEs), compose them out of order by repeated squaring, and score against the sequential forward pass; compare with the published adjacent-layer transport R² of 0.95 [s_ato].",
  "sources": [
   {
    "id": "s_pdiag",
    "url": "https://parallel-in-time.org/methods/paradiag.html",
    "quote": "The idea is to diagonalize the time stepping matrix, keeping the matrices for the space discretization unchanged, and then to solve all time steps in parallel.",
    "supports": "the ParaDiag/diagonalisation parallel-in-time exception the hypothesis builds on"
   },
   {
    "id": "s_pdiag_book",
    "url": "https://www.unige.ch/~gander/siamtoc3.php",
    "quote": "Chapter 5. Direct Space Time Parallel Solvers — 5.5 Time Parallelization Based on Diagonalization — 5.7 ParaExp",
    "supports": "the book sections naming diagonalisation (ParaDiag/ParaExp) as the linear-system exception"
   },
   {
    "id": "s_llama2",
    "url": "https://huggingface.co/docs/transformers/model_doc/llama2",
    "quote": "hidden_size (`int`, optional, defaults to `4096`) — Dimension of the hidden representations. num_hidden_layers (`int`, optional, defaults to `32`) — Number of hidden layers in the Transformer decoder.",
    "supports": "LLaMA-2 7B has d_model 4096 and 32 layers"
   },
   {
    "id": "s_llama2_params",
    "url": "https://arxiv.org/abs/2307.09288",
    "quote": "we develop and release Llama 2, a collection of pretrained and fine-tuned large language models (LLMs) ranging in scale from 7 billion to 70 billion parameters.",
    "supports": "LLaMA-2 7B parameter count"
   },
   {
    "id": "s_gemma2",
    "url": "https://arxiv.org/abs/2408.00118",
    "quote": "| Parameters | 2B | 9B | 27B | ... | d_model | 2304 | 3584 | 4608 | ... | Layers | 26 | 42 | 46 |",
    "supports": "Gemma 2 9B has 42 layers, d_model 3584, ~9B parameters"
   },
   {
    "id": "s_gemma_scope",
    "url": "https://arxiv.org/abs/2408.05147",
    "quote": "| 9B PT | 2^14 | All | All | All | 4B | (42 layers) ... | 2^17 | All | All | All | 8B | ... | 2^20 | ✗ | ✗ | { 9, 20, 31} | 16B |",
    "supports": "Gemma Scope residual SAE widths: 16.4K and 131K at all 42 layers, 1M at layers 9/20/31"
   },
   {
    "id": "s_scaling_mono",
    "url": "https://transformer-circuits.pub/2024/scaling-monosemanticity/",
    "quote": "We trained three SAEs of varying sizes: 1,048,576 (~1M), 4,194,304 (~4M), and 33,554,432 (~34M) features. ... For all three SAEs, the average number of features active (i.e. with nonzero activations) on a given token was fewer than 300, and the SAE reconstruction explained at least 65% of the variance of the model activations.",
    "supports": "published SAE scale (34M features) and 65% reconstruction ceiling used as anchor context"
   },
   {
    "id": "s_ato",
    "url": "https://arxiv.org/abs/2508.17540",
    "quote": "linear maps from upstream to downstream residuals k layers later, evaluated in feature space using downstream SAE decoder projections ... This compute-light (no finetuning, < 50 GPU-h) method ... Most linear transport occurs in nearby layers and deteriorates over large distances",
    "supports": "closest prior: per-feature R² of linear layer-to-layer maps, < 50 GPU-h, decay with distance"
   },
   {
    "id": "s_h100",
    "url": "https://www.cisco.com/c/dam/en/us/products/collateral/servers-unified-computing/ucs-c-series-rack-servers/nvidia-h100-80-gpu.pdf",
    "quote": "TF32 Tensor Core | 989 TFLOPS* ... * Shown with sparsity. Specifications 1/2 lower without sparsity.",
    "supports": "H100 SXM TF32 peak 989 TFLOPS with sparsity (494.5 dense), used to derive effective throughput"
   },
   {
    "id": "s_prices",
    "url": "https://lambda.ai/pricing",
    "quote": "Instances pricing, \"8x\" tab: row \"NVIDIA H100 SXM80 GB2081800 GiB22 TiB SSD$3.99\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*)",
    "supports": "8x H100 SXM at $3.99/GPU/hr"
   }
  ],
  "files_read": [
   "/home/hal/dev/interp/metis/experiments/reshape-test/20261019-2344-tree/out/work/seed-1/R1/interp.md",
   "/home/hal/dev/interp/metis/experiments/reshape-test/20261019-2344-tree/out/work/seed-1/R1/framer.md"
  ]
 },
 "eval": {
  "ok": false,
  "errors": [
   {
    "kind": "quote",
    "where": "numbers.params_llama2.quote",
    "msg": "7000000000 does not appear in the quote \"we develop and release Llama 2, a collection of pretrained and fine-tuned large language models (LLMs) ranging in scale from 7 billion to 70 billion parameters.\"; a value transformed from the page belongs in a DERIVED number"
   },
   {
    "kind": "quote",
    "where": "numbers.sae_w16.quote",
    "msg": "16384 does not appear in the quote \"| 9B PT | 2^14 | All | All | All | 4B | (42 layers)\"; a value transformed from the page belongs in a DERIVED number"
   },
   {
    "kind": "quote",
    "where": "numbers.sae_w131.quote",
    "msg": "131072 does not appear in the quote \"| 9B PT | ... | 2^17 | All | All | All | 8B | (42 layers)\"; a value transformed from the page belongs in a DERIVED number"
   },
   {
    "kind": "quote",
    "where": "numbers.sae_w1m.quote",
    "msg": "1048576 does not appear in the quote \"| 9B PT | ... | 2^20 | ✗ | ✗ | { 9, 20, 31} | 16B | (42 layers)\"; a value transformed from the page belongs in a DERIVED number"
   },
   {
    "kind": "quote",
    "where": "numbers.recon_var_published.quote",
    "msg": "0.65 does not appear in the quote \"For all three SAEs, the average number of features active (i.e. with nonzero activations) on a given token was fewer than 300, and the SAE reconstruction explained at least 65% of the variance of the model activations.\"; a value transformed from the page belongs in a DERIVED number"
   },
   {
    "kind": "quote",
    "where": "numbers.gpu_eff_tflops.quote",
    "msg": "200 does not appear in the quote \"TF32 Tensor Core | 989 TFLOPS* ... * Shown with sparsity. Specifications 1/2 lower without sparsity.\"; a value transformed from the page belongs in a DERIVED number"
   }
  ],
  "numbers": {
   "n_tokens": 2000000,
   "seq_len": 1024,
   "n_seq": 1953.125,
   "n_train_seq": 1500,
   "n_holdout_seq": 453.125,
   "layers_gemma9b": 42,
   "d_model_gemma9b": 3584,
   "layers_llama2": 32,
   "d_model_llama2": 4096,
   "params_gemma9b": 9000000000,
   "params_llama2": 7000000000,
   "sae_w16": 16384,
   "sae_w131": 131072,
   "sae_w1m": 1048576,
   "max_features_published": 33554432,
   "recon_var_published": 0.65,
   "ato_r2_adjacent": 0.95,
   "ato_max_leap": 10,
   "gpu_eff_tflops": 200,
   "overhead": 10,
   "total_flops": 331764367360000000,
   "hours_forward": 0.5759798044444444,
   "decision_threshold": 0.9,
   "recon_roundtrip_err": 0.00001,
   "composed_r2": 0.5,
   "fs_usd_gib_month": 0.2
  },
  "rates": {
   "rate_h100_8x": 31.92
  },
  "rate_corrections": [],
  "lines": [
   {
    "id": "line_setup",
    "phase": "phase_env",
    "kind": "allotment",
    "hours": 2,
    "usd": 63.84,
    "optional": false,
    "instead_of": [],
    "time_box": true,
    "need_h": 1,
    "margin": 2
   },
   {
    "id": "line_forward",
    "phase": "phase_forward",
    "kind": "allotment",
    "hours": 2,
    "usd": 63.84,
    "optional": false,
    "instead_of": [],
    "time_box": true,
    "need_h": 0.5759798044444444,
    "margin": 3.4723439686033437
   },
   {
    "id": "line_analyze",
    "phase": "phase_fit",
    "kind": "allotment",
    "hours": 2,
    "usd": 63.84,
    "optional": false,
    "instead_of": [],
    "time_box": true,
    "need_h": 0.5,
    "margin": 4
   },
   {
    "id": "line_headroom",
    "phase": "phase_width",
    "kind": "allotment",
    "hours": 2,
    "usd": 63.84,
    "optional": true,
    "instead_of": [],
    "time_box": true,
    "need_h": 0,
    "margin": null
   },
   {
    "id": "line_storage",
    "phase": "phase_forward",
    "kind": "storage",
    "hours": null,
    "usd": 10,
    "optional": false,
    "instead_of": [],
    "time_box": false,
    "need_h": null,
    "margin": null
   }
  ],
  "planned": 201.52,
  "planned_with_options": 265.36,
  "alternatives": [],
  "unallocated": 798.48,
  "scenarios": [
   {
    "id": "scen_slow",
    "what": "pessimistic: SAE kernels at 50 TFLOPS effective and 20x overhead",
    "total": 284.76220286293335
   },
   {
    "id": "scen_more",
    "what": "sensitivity: 10M tokens for tighter confidence intervals",
    "total": 229.60637678933338
   }
  ],
  "yields": [
   {
    "id": "n_seq",
    "base": 1953.125,
    "by_scenario": {
     "scen_slow": 1953.125,
     "scen_more": 9765.625
    }
   },
   {
    "id": "sae_w1m",
    "base": 1048576,
    "by_scenario": {
     "scen_slow": 1048576,
     "scen_more": 1048576
    }
   },
   {
    "id": "sae_w131",
    "base": 131072,
    "by_scenario": {
     "scen_slow": 131072,
     "scen_more": 131072
    }
   },
   {
    "id": "layers_gemma9b",
    "base": 42,
    "by_scenario": {
     "scen_slow": 42,
     "scen_more": 42
    }
   },
   {
    "id": "seq_len",
    "base": 1024,
    "by_scenario": {
     "scen_slow": 1024,
     "scen_more": 1024
    }
   }
  ],
  "gates": [
   {
    "phase": "phase_anchor",
    "on": "recon_roundtrip_err",
    "op": "<=",
    "value": 0.00001,
    "base_value": 0.00001,
    "passes": true,
    "uncut_total_at_threshold": 201.52,
    "else": "fall back to the d_model-only LLaMA-2 arm and drop the SAE feature arms."
   },
   {
    "phase": "phase_compose",
    "on": "composed_r2",
    "op": ">=",
    "value": 0.9,
    "base_value": 0.5,
    "passes": false,
    "uncut_total_at_threshold": 201.52,
    "else": "record if_not and write up; the width sweep becomes optional."
   }
  ],
  "uncertain": [
   {
    "id": "gpu_eff_tflops",
    "basis": "PROXY",
    "value": 200,
    "differs_in": [
     "real-world matmul efficiency below the dense TF32 peak for JumpReLU/SAE kernels"
    ],
    "measured_by": "phase_env",
    "cum_spend_through_measured_by": 63.84,
    "k_budget": 46.90275142553313,
    "k_box": 3.4723439703395167,
    "dir": "lower"
   },
   {
    "id": "overhead",
    "basis": "GUESS",
    "value": 10,
    "differs_in": [],
    "measured_by": "phase_forward",
    "cum_spend_through_measured_by": 137.68,
    "k_budget": 46.90275142553313,
    "k_box": 3.4723439703395163,
    "dir": "higher"
   },
   {
    "id": "recon_roundtrip_err",
    "basis": "GUESS",
    "value": 0.00001,
    "differs_in": [],
    "measured_by": "phase_anchor",
    "cum_spend_through_measured_by": 137.68,
    "k_budget": null,
    "k_box": null,
    "dir": "higher"
   },
   {
    "id": "composed_r2",
    "basis": "GUESS",
    "value": 0.5,
    "differs_in": [],
    "measured_by": "phase_compose",
    "cum_spend_through_measured_by": 201.52,
    "k_budget": null,
    "k_box": null,
    "dir": "higher"
   }
  ],
  "full_scale": [
   {
    "id": "full_scale_34m",
    "what": "train 34M-feature SAEs across all 42 layers of an open 70B model and rerun the composition test (published record is 34M on one middle layer) - rough estimate, 32x the 1M width",
    "usd": 38400,
    "multiple_of_budget": 38.4,
    "ratio_to_value": 0.03662109375
   },
   {
    "id": "full_scale_multi",
    "what": "repeat the 131K all-layer sweep on three more open model families (LLaMA-3 8B, Mistral 7B, Qwen 1.5 7B)",
    "usd": 1200,
    "multiple_of_budget": 1.2,
    "ratio_to_value": 28.571428571428573
   }
  ],
  "flags": [
   "gate in phase_compose fails at the plan's own value: composed out-of-order reconstruction R² at 42 layers is 0.5, needs ≥ 0.9; expected path: record if_not and write up; the width sweep becomes optional."
  ],
  "log": [
   "unlabelled constant 50 in lines.line_storage.usd",
   "unlabelled constant 38400 in full_scale.full_scale_34m.usd",
   "unlabelled constant 1200 in full_scale.full_scale_multi.usd"
  ]
 },
 "given": {
  "budget_usd": 1000,
  "price_sheet": {
   "read_at": "2026-10-20",
   "instances": [
    {
     "gpu": "NVIDIA B200 SXM",
     "gpu_memory_gb": 180,
     "n_gpus": 8,
     "per_gpu_usd_h": 6.69,
     "page_text": "Instances pricing, \"8x\" tab: row \"NVIDIA B200 SXM6180 GB2082900 GiB22 TiB SSD$6.69\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA H100 SXM",
     "gpu_memory_gb": 80,
     "n_gpus": 8,
     "per_gpu_usd_h": 3.99,
     "page_text": "Instances pricing, \"8x\" tab: row \"NVIDIA H100 SXM80 GB2081800 GiB22 TiB SSD$3.99\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA A100 SXM",
     "gpu_memory_gb": 80,
     "n_gpus": 8,
     "per_gpu_usd_h": 2.79,
     "page_text": "Instances pricing, \"8x\" tab: row \"NVIDIA A100 SXM80 GB2401800 GiB19.5 TiB SSD$2.79\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA A100 SXM",
     "gpu_memory_gb": 40,
     "n_gpus": 8,
     "per_gpu_usd_h": 1.99,
     "page_text": "Instances pricing, \"8x\" tab: row \"NVIDIA A100 SXM40 GB1241800 GiB5.8 TiB SSD$1.99\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA Tesla V100",
     "gpu_memory_gb": 16,
     "n_gpus": 8,
     "per_gpu_usd_h": 0.79,
     "page_text": "Instances pricing, \"8x\" tab: row \"NVIDIA Tesla V10016 GB88448 GiB5.8 TiB SSD$0.79\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA B200 SXM",
     "gpu_memory_gb": 180,
     "n_gpus": 4,
     "per_gpu_usd_h": 6.79,
     "page_text": "Instances pricing, \"4x\" tab: row \"NVIDIA B200 SXM6180 GB1041440 GiB11 TiB SSD$6.79\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA H100 SXM",
     "gpu_memory_gb": 80,
     "n_gpus": 4,
     "per_gpu_usd_h": 4.09,
     "page_text": "Instances pricing, \"4x\" tab: row \"NVIDIA H100 SXM80 GB104900 GiB11 TiB SSD$4.09\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA A100 PCIe",
     "gpu_memory_gb": 40,
     "n_gpus": 4,
     "per_gpu_usd_h": 1.99,
     "page_text": "Instances pricing, \"4x\" tab: row \"NVIDIA A100 PCIe40 GB120900 GiB1 TiB SSD$1.99\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA A6000",
     "gpu_memory_gb": 48,
     "n_gpus": 4,
     "per_gpu_usd_h": 1.09,
     "page_text": "Instances pricing, \"4x\" tab: row \"NVIDIA A600048 GB56400 GiB1 TiB SSD$1.09\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA B200 SXM",
     "gpu_memory_gb": 180,
     "n_gpus": 2,
     "per_gpu_usd_h": 6.89,
     "page_text": "Instances pricing, \"2x\" tab: row \"NVIDIA B200 SXM6180 GB52720 GiB5.5 TiB SSD$6.89\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA H100 SXM",
     "gpu_memory_gb": 80,
     "n_gpus": 2,
     "per_gpu_usd_h": 4.19,
     "page_text": "Instances pricing, \"2x\" tab: row \"NVIDIA H100 SXM80 GB52450 GiB5.5 TiB SSD$4.19\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA A100 PCIe",
     "gpu_memory_gb": 40,
     "n_gpus": 2,
     "per_gpu_usd_h": 1.99,
     "page_text": "Instances pricing, \"2x\" tab: row \"NVIDIA A100 PCIe40 GB60450 GiB1 TiB SSD$1.99\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA A6000",
     "gpu_memory_gb": 48,
     "n_gpus": 2,
     "per_gpu_usd_h": 1.09,
     "page_text": "Instances pricing, \"2x\" tab: row \"NVIDIA A600048 GB28200 GiB1 TiB SSD$1.09\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA B200 SXM",
     "gpu_memory_gb": 180,
     "n_gpus": 1,
     "per_gpu_usd_h": 6.99,
     "page_text": "Instances pricing, \"1x\" tab: row \"NVIDIA B200 SXM6180 GB26360 GiB2.75 TiB SSD$6.99\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA GH200",
     "gpu_memory_gb": 96,
     "n_gpus": 1,
     "per_gpu_usd_h": 2.29,
     "page_text": "Instances pricing, \"1x\" tab: row \"NVIDIA GH20096 GB64432 GiB4 TiB SSD$2.29\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA H100 SXM",
     "gpu_memory_gb": 80,
     "n_gpus": 1,
     "per_gpu_usd_h": 4.29,
     "page_text": "Instances pricing, \"1x\" tab: row \"NVIDIA H100 SXM80 GB26225 GiB2.75 TiB SSD$4.29\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA H100 PCIe",
     "gpu_memory_gb": 80,
     "n_gpus": 1,
     "per_gpu_usd_h": 3.29,
     "page_text": "Instances pricing, \"1x\" tab: row \"NVIDIA H100 PCIe80 GB26225 GiB1 TiB SSD$3.29\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA A100 SXM",
     "gpu_memory_gb": 40,
     "n_gpus": 1,
     "per_gpu_usd_h": 1.99,
     "page_text": "Instances pricing, \"1x\" tab: row \"NVIDIA A100 SXM40 GB30220 GiB512 GiB SSD$1.99\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA A100 PCIe",
     "gpu_memory_gb": 40,
     "n_gpus": 1,
     "per_gpu_usd_h": 1.99,
     "page_text": "Instances pricing, \"1x\" tab: row \"NVIDIA A100 PCIe40 GB30225 GiB512 GiB SSD$1.99\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA A10",
     "gpu_memory_gb": 24,
     "n_gpus": 1,
     "per_gpu_usd_h": 1.29,
     "page_text": "Instances pricing, \"1x\" tab: row \"NVIDIA A1024 GB30226 GiB1.3 TiB SSD$1.29\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA A6000",
     "gpu_memory_gb": 48,
     "n_gpus": 1,
     "per_gpu_usd_h": 1.09,
     "page_text": "Instances pricing, \"1x\" tab: row \"NVIDIA A600048 GB14100 GiB512 GiB SSD$1.09\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    },
    {
     "gpu": "NVIDIA Quadro RTX 6000",
     "gpu_memory_gb": 24,
     "n_gpus": 1,
     "per_gpu_usd_h": 0.69,
     "page_text": "Instances pricing, \"1x\" tab: row \"NVIDIA Quadro RTX 600024 GB1446 GiB512 GiB SSD$0.69\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*) — https://lambda.ai/pricing"
    }
   ],
   "filesystem": {
    "usd_gib_month": 0.2,
    "page_text": "\"Filesystems are billed per GiB used per month in one-hour increments. For example, at a rate of $0.20 per GiB per month: If you use 1,000 GiB continuously for a full month (720 hours), you'll be billed $200.00. If you use 1,000 GiB continuously for a full day (24 hours), you'll be billed $6.67.\" Followed by: \"Important — The rate above is used for example purposes and might not reflect current pricing. The actual price will be displayed when you create your filesystem.\" — https://docs.lambda.ai/public-cloud/billing/",
    "example": true
   }
  },
  "budget_covers_storage": true,
  "budget_covers_tax": false
 },
 "findings": [
  {
   "items": [
    {
     "ref": "card:question",
     "status": "SUPPORTED",
     "page_quote": "The idea is to diagonalize the time stepping matrix, keeping the matrices for the space discretization unchanged, and then to solve all time steps in parallel.",
     "note": "Research question is the plan's own framing, not a factual claim; s_pdiag supports the parallel-in-time/diagonalization concept it builds on."
    },
    {
     "ref": "card:hypothesis",
     "status": "SUPPORTED",
     "page_quote": "The idea is to diagonalize the time stepping matrix, keeping the matrices for the space discretization unchanged, and then to solve all time steps in parallel.",
     "note": "Plan's own prediction (needs no source); s_pdiag supports the parallel-in-time framing, while 'repeated squaring' is the plan's own technique (not in s_pdiag, but that is the plan's proposal, not a sourced fact)."
    },
    {
     "ref": "card:if_lever",
     "status": "SUPPORTED",
     "page_quote": "Layers 26 42 46 (Table 1: Gemma 2 model parameters; 9B column = 42 layers)",
     "note": "Plan's own success criterion: the 90% reconstruction threshold is a measurement the plan sets (no source needed). The '42 layers' scope figure is corroborated by the Gemma 2 report (Table 1, 9B = 42 layers), matching num:layers_gemma9b."
    },
    {
     "ref": "card:if_not",
     "status": "SUPPORTED",
     "page_quote": "N/A (plan-internal failure criterion; no source cited)",
     "note": "Plan's own prediction of the failure outcome (residual nonlinearity breaking composition); what the plan predicts needs no source."
    },
    {
     "ref": "card:test_summary",
     "status": "PARTIAL",
     "page_quote": "Comparing the per-feature R² between full-rank operators shows that those trained for small leaps (k=1, k=4 for target layer 10) successfully transport a significant number of features (R²>0.95).",
     "note": "The cited s_ato abstract does not state 0.95 or R². The paper body reports R²>0.95 (a threshold for a significant number of features at small leaps k=1,k=4), not an exact 'adjacent-layer transport R² of 0.95'. The test procedure itself needs no source."
    },
    {
     "ref": "card:closest_prior",
     "status": "SUPPORTED",
     "page_quote": "linear maps from upstream to downstream residuals k layers later, evaluated in feature space using downstream SAE decoder projections ... This compute-light (no finetuning, <50 GPU-h) method; We conduct experiments using Gemma 2 2B model with hidden dimension d_model=2304 ... 16,384-dimensional latent space.",
     "note": "ATO is a small open model (Gemma 2 2B), per-feature R², <50 GPU-h. Leap sizes: main per-feature R² study uses k={1..9}; k=10 appears in transport-efficiency/perplexity and the Figure 3 heatmap covers all source-target pairs, so 'up to a 10-layer leap' (value 10) is broadly accurate though the headline per-feature sweep tops out at k=9."
    },
    {
     "ref": "card:left_open",
     "status": "SUPPORTED",
     "page_quote": "First, we used a single, trivial same-token j-policy ... Second, we evaluated only a single model",
     "note": "Plan's gap characterization of prior work; consistent with the ATO paper (single Gemma 2 2B model, one 16K SAE width, same-token j-policy, no out-of-order composition or time-invariance testing). Cites no source, but the claims match the ATO paper."
    },
    {
     "ref": "card:anchor",
     "status": "SUPPORTED",
     "page_quote": "We trained three SAEs of varying sizes: 1,048,576 (~1M), 4,194,304 (~4M), and 33,554,432 (~34M) features. ... the SAE reconstruction explained at least 65% of the variance of the model activations.",
     "note": "The 1e-5 round-trip and 'matches sequential' checks are the plan's own validation code (no source needed). The value 0.65 matches the published 'at least 65% of the variance' reconstruction ceiling, and 34M features is stated."
    },
    {
     "ref": "card:limits",
     "status": "SUPPORTED",
     "page_quote": "33,554,432 (~34M) features",
     "note": "Plan's own scope statement. The embedded fact 'Claude 3 Sonnet's 34M features' is corroborated by scaling-monosemanticity (title is about Claude 3 Sonnet; 33,554,432 ≈ 34M features); the plan uses open Gemma/LLaMA + released SAEs, so the scope claim is accurate."
    },
    {
     "ref": "src:s_pdiag",
     "status": "SUPPORTED",
     "page_quote": "The idea is to diagonalize the time stepping matrix, keeping the matrices for the space discretization unchanged, and then to solve all time steps in parallel.",
     "note": "Quote appears verbatim on the page (in the GanderEtAl2021 abstract). Supports the ParaDiag/diagonalisation parallel-in-time concept."
    },
    {
     "ref": "src:s_ato",
     "status": "SUPPORTED",
     "page_quote": "linear maps from upstream to downstream residuals k layers later, evaluated in feature space using downstream SAE decoder projections ... This compute-light (no finetuning, <50 GPU-h) method ... Most linear transport occurs in nearby layers and deteriorates over large distances",
     "note": "First two segments are verbatim in the arXiv abstract; 'Most linear transport occurs in nearby layers and deteriorates over large distances' is the §3.1 section heading in the paper body (verified via arXiv HTML), not the abstract page. The composite quote is accurate to the paper and supports per-feature R², <50 GPU-h, and decay with distance."
    },
    {
     "ref": "src:s_scaling_mono",
     "status": "SUPPORTED",
     "page_quote": "We trained three SAEs of varying sizes: 1,048,576 (~1M), 4,194,304 (~4M), and 33,554,432 (~34M) features. ... For all three SAEs, the average number of features active (i.e. with nonzero activations) on a given token was fewer than 300, and the SAE reconstruction explained at least 65% of the variance of the model activations.",
     "note": "Quote appears on the page. Supports 34M-feature SAE scale and the 65% reconstruction figure used as anchor context."
    },
    {
     "ref": "num:layers_gemma9b",
     "status": "SUPPORTED",
     "page_quote": "Layers | 26 | 42 | 46 (Table 1; 9B column = 42)",
     "note": "Gemma 2 9B has 42 layers.",
     "page_value": 42
    },
    {
     "ref": "num:d_model_gemma9b",
     "status": "SUPPORTED",
     "page_quote": "d_model | 2304 | 3584 | 4608 (Table 1; 9B column = 3584)",
     "note": "Gemma 2 9B d_model is 3584.",
     "page_value": 3584
    },
    {
     "ref": "num:params_gemma9b",
     "status": "SUPPORTED",
     "page_quote": "Parameters | 2B | 9B | 27B (Table 1)",
     "note": "Gemma 2 9B has 9 billion parameters.",
     "page_value": 9000000000
    },
    {
     "ref": "num:params_llama2",
     "status": "SUPPORTED",
     "page_quote": "we develop and release Llama 2, a collection of pretrained and fine-tuned large language models (LLMs) ranging in scale from 7 billion to 70 billion parameters.",
     "note": "Abstract states the 7B-to-70B range; the 7B model (7,000,000,000 params) is the lower bound.",
     "page_value": 7000000000
    },
    {
     "ref": "num:sae_w16",
     "status": "SUPPORTED",
     "page_quote": "9B PT | 2^14 | All | All | All | 4B | (42 layers) (Table 1; 2^14 ≈ 16.4K)",
     "note": "2^14 = 16,384 features, all layers of Gemma 2 9B PT.",
     "page_value": 16384
    },
    {
     "ref": "num:sae_w131",
     "status": "SUPPORTED",
     "page_quote": "2^17 | All | All | All | 8B (Table 1, 9B PT row)",
     "note": "2^17 = 131,072 features, all layers of Gemma 2 9B PT.",
     "page_value": 131072
    },
    {
     "ref": "num:sae_w1m",
     "status": "SUPPORTED",
     "page_quote": "2^20 | ✗ | ✗ | {9, 20, 31} | 16B (Table 1, 9B PT row; 2^20 ≈ 1M)",
     "note": "2^20 = 1,048,576 features on layers {9, 20, 31} of Gemma 2 9B PT.",
     "page_value": 1048576
    },
    {
     "ref": "num:gpu_eff_tflops",
     "status": "SUPPORTED",
     "page_quote": "TF32 Tensor Core | 989 TFLOPS* | 756 TFLOPS* ... * Shown with sparsity. Specifications 1/2 lower without sparsity.",
     "note": "Page (H100 SXM datasheet) states 989 TFLOPS TF32 Tensor Core with sparsity; footnote gives 1/2 lower without sparsity = 494.5 TFLOPS dense, matching the item's page_setting. The item's 200 TFLOPS value is the plan's own proxy efficiency (PROXY basis), not the datasheet figure, which the item itself flags under differs_in.",
     "page_value": 494.5
    }
   ]
  },
  {
   "items": [
    {
     "ref": "card:question",
     "status": "SUPPORTED",
     "page_quote": "The idea is to diagonalize the time stepping matrix, keeping the matrices for the space discretization unchanged, and then to solve all time steps in parallel.",
     "note": "Quote appears verbatim on the ParaDiag page (abstract of Gander et al. 2021, ref [2], reproduced there). The research question itself is the plan's own and needs no source; the cited source grounds the diagonalization-based parallel-in-time idea the question builds on."
    },
    {
     "ref": "card:hypothesis",
     "status": "SUPPORTED",
     "page_quote": "The idea is to diagonalize the time stepping matrix, keeping the matrices for the space discretization unchanged, and then to solve all time steps in parallel.",
     "note": "Quote appears on the page and supports the parallel-in-time/diagonalization foundation; the near-linearity-in-SAE-features premise and the O(log T)/no-forgetting claim are the plan's hypothesis under test and need no source."
    },
    {
     "ref": "card:if_lever",
     "status": "SUPPORTED",
     "page_quote": "(no source cited; none needed - success criterion for the plan's own measurement)",
     "note": "Pure conditional prediction of the planned experiment; the 90% threshold is the plan's decision rule. The referenced 42-layer count of Gemma 2 9B is independently confirmed by Table 1 of arXiv:2408.00118 (see num:layers_gemma9b)."
    },
    {
     "ref": "card:if_not",
     "status": "SUPPORTED",
     "page_quote": "(no source cited; none needed - failure criterion for the plan's own measurement)",
     "note": "Pure conditional prediction of the planned experiment; nothing factual to source."
    },
    {
     "ref": "card:test_summary",
     "status": "SUPPORTED",
     "page_quote": "Comparing the per-feature R2 between full-rank operators shows that those trained for small leaps (k=1, k=4 for target layer 10) successfully transport a significant number of features (R2>0.95).",
     "note": "The fitting/composing/scoring pipeline (Gemma 2 9B, Gemma Scope, repeated squaring) is what the plan will build and needs no source. The cited 'published adjacent-layer transport R2 of 0.95' matches the paper's per-feature R2 > 0.95 for small leaps (k=1 and k=4, target layer 10); the paper reports this for a significant number of features rather than a single point value."
    },
    {
     "ref": "card:closest_prior",
     "status": "SUPPORTED",
     "page_quote": "We conduct experiments using Gemma 2 2B model ... Per-feature R2 of operators depend on both the target layer depth and the leap size k ... even at k=10 the increase is 7.1% of max degradation ... This compute-light (no finetuning, <50 GPU-h) method ...",
     "note": "All elements check out: per-feature R2 of linear layer-to-layer maps, leaps evaluated up to k=10 (Figures 2-4 and results text include k=10), small open model = Gemma 2 2B, and <50 GPU-h from the abstract. The carried value 10 matches the maximum leap evaluated."
    },
    {
     "ref": "card:left_open",
     "status": "UNSUPPORTED",
     "page_quote": "(no source cited for the factual gap claims)",
     "note": "The card makes factual claims about what prior work did not do but cites no source, so per the rule it is unsupported. For what it is worth, the ATO full text (fetched for src:s_ato) is consistent with it: a single Gemma 2 2B model, fixed 16,384-dim Gemma Scope SAEs, a single same-token j-policy, and Limitations stating 'we evaluated only a narrow set of layers and offsets on a single model'; no out-of-order composition, SAE-width sweep, or cross-context time-invariance test appears in the paper. Attaching [s_ato] to this card would make it supported."
    },
    {
     "ref": "card:anchor",
     "status": "SUPPORTED",
     "page_quote": "For all three SAEs, the average number of features active (i.e. with nonzero activations) on a given token was fewer than 300, and the SAE reconstruction explained at least 65% of the variance of the model activations.",
     "note": "Carried value 0.65 matches the page's published reconstruction ceiling (at least 65% of variance; Claude 3 Sonnet SAEs of 1M/4M/34M features). The <1e-5 round-trip and synthetic-linearity checks are plan-set validation targets and need no source. Page verified via a search-engine scrape of the exact URL after direct fetch twice exceeded the 5MB response limit."
    },
    {
     "ref": "card:limits",
     "status": "UNSUPPORTED",
     "page_quote": "(no source cited for the factual claim)",
     "note": "The scope statements ('holds for open Gemma/LLaMA models and released SAEs', 'it measures linearity, not a shipped parallel sampler') need no source, but 'not Claude 3 Sonnet's 34M features' is a factual claim with no cited source. It is in fact corroborated by the s_scaling_mono page ('We trained three SAEs of varying sizes: 1,048,576 (~1M), 4,194,304 (~4M), and 33,554,432 (~34M) features', Scaling Monosemanticity on Claude 3 Sonnet), but this card does not cite it."
    },
    {
     "ref": "src:s_pdiag",
     "status": "SUPPORTED",
     "page_quote": "The idea is to diagonalize the time stepping matrix, keeping the matrices for the space discretization unchanged, and then to solve all time steps in parallel.",
     "note": "Appears verbatim on the page (abstract of Gander et al. 2021, ref [2], reproduced on the ParaDiag methods page)."
    },
    {
     "ref": "src:s_ato",
     "status": "SUPPORTED",
     "page_quote": "In this work, we propose Activation Transport Operators (ATO), linear maps from upstream to downstream residuals k layers later, evaluated in feature space using downstream SAE decoder projections. ... This compute-light (no finetuning, <50 GPU-h) method ... Most linear transport occurs in nearby layers and deteriorates over large distances",
     "note": "All three fragments appear on the fetched pages: the first two in the abstract (abs page and HTML full text), the third as the Results section heading 'Most linear transport occurs in nearby layers and deteriorates over large distances'."
    },
    {
     "ref": "src:s_scaling_mono",
     "status": "SUPPORTED",
     "page_quote": "We trained three SAEs of varying sizes: 1,048,576 (~1M), 4,194,304 (~4M), and 33,554,432 (~34M) features. ... For all three SAEs, the average number of features active (i.e. with nonzero activations) on a given token was fewer than 300, and the SAE reconstruction explained at least 65% of the variance of the model activations.",
     "note": "Both sentences appear verbatim on the page. Direct webfetch of transformer-circuits.pub exceeded the 5MB response limit twice; content was verified from a search-engine scrape of the same URL (https://transformer-circuits.pub/2024/scaling-monosemanticity)."
    },
    {
     "ref": "num:layers_gemma9b",
     "status": "SUPPORTED",
     "page_quote": "Parameters | 2B | 9B | 27B ... d_model | 2304 | 3584 | 4608 ... Layers | 26 | 42 | 46 (Table 1, 9B column)",
     "page_value": 42,
     "note": "Gemma 2 paper Table 1 lists 42 layers for the 9B model, matching the recorded value."
    },
    {
     "ref": "num:d_model_gemma9b",
     "status": "SUPPORTED",
     "page_quote": "d_model | 2304 | 3584 | 4608 (Table 1, 9B column: 3584)",
     "page_value": 3584,
     "note": "Gemma 2 paper Table 1 lists d_model 3584 for the 9B model."
    },
    {
     "ref": "num:params_gemma9b",
     "status": "SUPPORTED",
     "page_quote": "Parameters | 2B | 9B | 27B (Table 1); abstract: 'ranging in scale from 2 billion to 27 billion parameters'",
     "page_value": 9000000000,
     "note": "The 9B designation is stated in Table 1 and the abstract; Table 2's component counts (917,962,752 embedding + 8,324,201,984 non-embedding = 9,242,164,736) round to the 9B figure."
    },
    {
     "ref": "num:params_llama2",
     "status": "SUPPORTED",
     "page_quote": "In this work, we develop and release Llama 2, a collection of pretrained and fine-tuned large language models (LLMs) ranging in scale from 7 billion to 70 billion parameters.",
     "page_value": 7000000000,
     "note": "Abstract sentence appears verbatim; the scale range begins at 7 billion parameters, matching the 7B value for LLaMA-2 7B."
    },
    {
     "ref": "num:sae_w16",
     "status": "SUPPORTED",
     "page_quote": "9B PT | 2^14 | All | All | All | 4B | (42 layers) (Table 1: width 2^14 = 16.4K SAEs on all attention, MLP and residual sites of all 42 layers of Gemma 2 9B PT, trained on 4B tokens)",
     "page_value": 16384,
     "note": "2^14 = 16,384 features; the table row matches the recorded quote including the 42-layer parenthetical."
    },
    {
     "ref": "num:sae_w131",
     "status": "SUPPORTED",
     "page_quote": "9B PT | 2^17 | All | All | All | 8B (42 layers) (Table 1)",
     "page_value": 131072,
     "note": "2^17 = 131,072 features on all sites of all 42 layers for 9B PT, trained on 8B tokens, exactly as recorded."
    },
    {
     "ref": "num:sae_w1m",
     "status": "SUPPORTED",
     "page_quote": "9B PT | 2^20 | X | X | {9, 20, 31} | 16B (42 layers) (Table 1)",
     "page_value": 1048576,
     "note": "2^20 = 1,048,576 features, residual site only at layers {9, 20, 31} for 9B PT, trained on 16B tokens - matches the item's name and quote."
    },
    {
     "ref": "num:gpu_eff_tflops",
     "status": "PARTIAL",
     "page_quote": "TF32 Tensor Core | 989 TFLOPS* ... * Shown with sparsity. Specifications 1/2 lower without sparsity.",
     "page_value": 494.5,
     "note": "The datasheet states the H100 SXM peak TF32 throughput as 989 TFLOPS with sparsity, i.e. half (~494.5 TFLOPS) dense - it nowhere states the item's 200 TFLOPS effective for SAE encode, which remains a proxy assumption (as the item itself flags via basis PROXY and differs_in). Direct fetch of the Cisco-hosted PDF returned HTTP 403; the specifications table was verified from a search-engine scrape of the same URL."
    }
   ]
  }
 ],
 "decision": {
  "result": "PASS",
  "blocking": [],
  "listed": [
   {
    "ref": "card:test_summary",
    "status": "PARTIAL",
    "page_quote": "Comparing the per-feature R² between full-rank operators shows that those trained for small leaps (k=1, k=4 for target layer 10) successfully transport a significant number of features (R²>0.95).",
    "note": "The cited s_ato abstract does not state 0.95 or R². The paper body reports R²>0.95 (a threshold for a significant number of features at small leaps k=1,k=4), not an exact 'adjacent-layer transport R² of 0.95'. The test procedure itself needs no source."
   }
  ]
 },
 "decision2": {
  "result": "PASS",
  "blocking": [],
  "listed": [
   {
    "ref": "card:left_open",
    "status": "UNSUPPORTED",
    "page_quote": "(no source cited for the factual gap claims)",
    "note": "The card makes factual claims about what prior work did not do but cites no source, so per the rule it is unsupported. For what it is worth, the ATO full text (fetched for src:s_ato) is consistent with it: a single Gemma 2 2B model, fixed 16,384-dim Gemma Scope SAEs, a single same-token j-policy, and Limitations stating 'we evaluated only a narrow set of layers and offsets on a single model'; no out-of-order composition, SAE-width sweep, or cross-context time-invariance test appears in the paper. Attaching [s_ato] to this card would make it supported."
   },
   {
    "ref": "card:limits",
    "status": "UNSUPPORTED",
    "page_quote": "(no source cited for the factual claim)",
    "note": "The scope statements ('holds for open Gemma/LLaMA models and released SAEs', 'it measures linearity, not a shipped parallel sampler') need no source, but 'not Claude 3 Sonnet's 34M features' is a factual claim with no cited source. It is in fact corroborated by the s_scaling_mono page ('We trained three SAEs of varying sizes: 1,048,576 (~1M), 4,194,304 (~4M), and 33,554,432 (~34M) features', Scaling Monosemanticity on Claude 3 Sonnet), but this card does not cite it."
   },
   {
    "ref": "num:gpu_eff_tflops",
    "status": "PARTIAL",
    "page_quote": "TF32 Tensor Core | 989 TFLOPS* ... * Shown with sparsity. Specifications 1/2 lower without sparsity.",
    "page_value": 494.5,
    "note": "The datasheet states the H100 SXM peak TF32 throughput as 989 TFLOPS with sparsity, i.e. half (~494.5 TFLOPS) dense - it nowhere states the item's 200 TFLOPS effective for SAE encode, which remains a proxy assumption (as the item itself flags via basis PROXY and differs_in). Direct fetch of the Cisco-hosted PDF returned HTTP 403; the specifications table was verified from a search-engine scrape of the same URL."
   }
  ]
 },
 "critique": {
  "scores": [
   {
    "criterion": "stakes",
    "value": 3,
    "ref": "card:limits",
    "reason": "Residual reconstruction alone; building a parallel sampler needs unchecked next-token accuracy and transfer."
   },
   {
    "criterion": "lever",
    "value": 3,
    "ref": "plan:compute_axis",
    "reason": "Depth axis varies fixed architecture, not compute alone; other noise, CI, and fixed-input conditions hold."
   },
   {
    "criterion": "verifiable",
    "value": 5,
    "ref": "card:anchor",
    "reason": "Anchor reproduces SAE round-trip and synthetic sequential result; scoring uses true sequential activations."
   },
   {
    "criterion": "open",
    "value": 5,
    "ref": "card:left_open",
    "reason": "Published work reaches only ten-layer adjacent transport, not out-of-order full-depth composition across widths."
   },
   {
    "criterion": "internals",
    "value": 1,
    "ref": "card:limits",
    "reason": "No outputs-only comparator is named; the test measures residual activation linearity, not shipped model outputs."
   },
   {
    "criterion": "reshape",
    "value": 3,
    "ref": "plan:restructuring.sequential_part",
    "reason": "Out-of-order composition removes layer order, but restructuring claims none; per-layer fits are just independent work side by side, though per-layer R2 precedes composition."
   },
   {
    "criterion": "baseline",
    "value": "NA",
    "ref": "card:method",
    "reason": "Restructuring method is none, so baseline timing against non-method baselines does not apply."
   }
  ],
  "decides_by": "phase_compose",
  "decides_by_reason": "Phase_compose produces composed out-of-order R2 and CI, applying the 0.90 decision_rule for either outcome."
 },
 "beyond_prior": true,
 "annotations": [
  "quote at numbers.params_llama2.quote: 7000000000 does not appear in the quote \"we develop and release Llama 2, a collection of pretrained and fine-tuned large language models (LLMs) ranging in scale from 7 billion to 70 billion parameters.\"; a value transformed from the page belongs in a DERIVED number",
  "quote at numbers.sae_w16.quote: 16384 does not appear in the quote \"| 9B PT | 2^14 | All | All | All | 4B | (42 layers)\"; a value transformed from the page belongs in a DERIVED number",
  "quote at numbers.sae_w131.quote: 131072 does not appear in the quote \"| 9B PT | ... | 2^17 | All | All | All | 8B | (42 layers)\"; a value transformed from the page belongs in a DERIVED number",
  "quote at numbers.sae_w1m.quote: 1048576 does not appear in the quote \"| 9B PT | ... | 2^20 | ✗ | ✗ | { 9, 20, 31} | 16B | (42 layers)\"; a value transformed from the page belongs in a DERIVED number",
  "quote at numbers.recon_var_published.quote: 0.65 does not appear in the quote \"For all three SAEs, the average number of features active (i.e. with nonzero activations) on a given token was fewer than 300, and the SAE reconstruction explained at least 65% of the variance of the model activations.\"; a value transformed from the page belongs in a DERIVED number",
  "quote at numbers.gpu_eff_tflops.quote: 200 does not appear in the quote \"TF32 Tensor Core | 989 TFLOPS* ... * Shown with sparsity. Specifications 1/2 lower without sparsity.\"; a value transformed from the page belongs in a DERIVED number",
  "gate in phase_compose fails at the plan's own value: composed out-of-order reconstruction R² at 42 layers is 0.5, needs ≥ 0.9; expected path: record if_not and write up; the width sweep becomes optional.",
  "prior_max_level 10 is not in the quote of s_ato",
  "question: a sentence of 23 words",
  "hypothesis: a sentence of 21 words",
  "test_summary: a sentence of 36 words",
  "novelty.closest_prior: a sentence of 25 words",
  "novelty.left_open: a sentence of 23 words",
  "limits: a sentence of 22 words",
  "novelty.closest_prior: rewritten by the field repair",
  "card field novelty.closest_prior still fails: compute-hours"
 ],
 "halted": null,
 "producer_path": "/home/hal/dev/interp/metis/experiments/reshape-test/20261019-2344-tree/out/work/seed-1/R1/interp/bab1ad22/producer.md",
 "tag": "R1:interp:top",
 "n_options": 4
}
```

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|
| R1:interp:Feature steering as the guess-then-correct operator | Feature steering is a learned correction operator that replaces the Newton step | SAME | Feature steering as trajectory correction operator | 12 | not_picked | not drawn |
| R1:interp:Linear feature representation -> parallel-in-time for free | SAE features give the linear basis that triggers the framer's no-forgetting parallel-in-time exception | SAME | Linear SAE dynamics enabling no-forgetting parallel decoding | 14 | picked_top | highest total with open >= 3 |
| R1:interp:Measure the forgetting rate by feature-level causal tracing | Feature-level causal tracing turns the framer's forgetting condition into a measurement on the real system | SAME | Measuring forgetting to gate parallel LLM decoding | 12 | not_picked | not drawn |
| R1:interp:Speculative and Jacobi decoding: the working guess-then-correct | Autoregressive decoding is the LLM instantiation of the framer's problem, and guess-then-correct already works there, gated by the forgetting interp measures | SAME | Measuring forgetting to gate parallel LLM decoding | 11 | not_picked | not drawn |
| R1:physical:Chaotic / non-forgetting PinT | Chaotic / non-forgetting PinT | SAME | Parallel-in-time breakdown on chaotic dynamics | 6 | not_picked | not drawn |
| R1:physical:Coupling from the past | Coupling from the past (CFTP) | ADJACENT | Parallelising MCMC sampling across branches and chains | 4 | not_eligible | compute_open none, sequential none |
| R1:physical:Cyclic reduction (PCR) | Parallel cyclic reduction | SAME | Iterative guess-and-correct parallel-in-time integration of ODE trajectories | 4 | picked_top | reshape route: highest reshape + stakes, tie of 2 broken by seeded order |
| R1:physical:GLUE / rainfall-runoff calibration | GLUE / rainfall-runoff parameter calibration | ADJACENT | Parallel parameter calibration for rainfall-runoff models | 4 | not_eligible | compute_open settled, sequential none |
| R1:physical:MGRIT | MGRIT (XBraid) | SAME | Iterative guess-and-correct parallel-in-time integration of ODE trajectories | 4 | not_picked | not drawn |
| R1:physical:Many-chain / data-parallel sampling (TFP HMC) | Many-chain / data-parallel sampling (TFP HMC) | SAME | Parallelising MCMC sampling across branches and chains | 10 | not_picked | not drawn |
| R1:physical:Multiple shooting | Direct multiple shooting | SAME | Iterative guess-and-correct parallel-in-time integration of ODE trajectories | 4 | not_picked | not drawn |
| R1:physical:ParaDiag / ParaExp | ParaDiag / ParaExp (linear diagonalisation) | SAME | Direct parallel-in-time methods for linear dynamics | 4 | not_eligible | compute_open none, sequential none |
| R1:physical:Parareal | Parareal | SAME | Iterative guess-and-correct parallel-in-time integration of ODE trajectories | 4 | not_picked | not drawn |
| R1:physical:Regeneration / splitting | Regeneration / splitting (MCMC) | ADJACENT | Parallelising MCMC sampling across branches and chains | 4 | not_eligible | compute_open none, sequential none |
| R1:physical:Speculative prefetching | Speculative prefetching (MCMC) | SAME | Parallelising MCMC sampling across branches and chains | 2 | not_picked | not drawn |

## Log

```
R1: NOT COMPUTE-BOUND, 3 compute signal(s) -> WIDENER + INTERP
R1:physical: reshape route
R1:interp: no reshape option
pool: 0 candidate cluster(s); picked 0
R1:physical:top: option_title mismatch: plan "Cyclic reduction (PCR)", pick "Parallel cyclic reduction" (re-key if it is another option in this branch)
R1:physical:top: hypothesis: a sentence of 22 words
R1:physical:top: predictions.if_not: a sentence of 25 words
R1:physical:top: test_summary: a sentence of 27 words
R1:physical:top: novelty.closest_prior: a sentence of 28 words
R1:physical:top: novelty.left_open: a sentence of 24 words
R1:physical:top: limits: a sentence of 21 words
R1:interp:top: quote at numbers.params_llama2.quote: 7000000000 does not appear in the quote "we develop and release Llama 2, a collection of pretrained and fine-tuned large language models (LLMs) ranging in scale from 7 billion to 70 billion parameters."; a value transformed from the page belongs in a DERIVED number
R1:interp:top: quote at numbers.sae_w16.quote: 16384 does not appear in the quote "| 9B PT | 2^14 | All | All | All | 4B | (42 layers)"; a value transformed from the page belongs in a DERIVED number
R1:interp:top: quote at numbers.sae_w131.quote: 131072 does not appear in the quote "| 9B PT | ... | 2^17 | All | All | All | 8B | (42 layers)"; a value transformed from the page belongs in a DERIVED number
R1:interp:top: quote at numbers.sae_w1m.quote: 1048576 does not appear in the quote "| 9B PT | ... | 2^20 | ✗ | ✗ | { 9, 20, 31} | 16B | (42 layers)"; a value transformed from the page belongs in a DERIVED number
R1:interp:top: quote at numbers.recon_var_published.quote: 0.65 does not appear in the quote "For all three SAEs, the average number of features active (i.e. with nonzero activations) on a given token was fewer than 300, and the SAE reconstruction explained at least 65% of the variance of the model activations."; a value transformed from the page belongs in a DERIVED number
R1:interp:top: quote at numbers.gpu_eff_tflops.quote: 200 does not appear in the quote "TF32 Tensor Core | 989 TFLOPS* ... * Shown with sparsity. Specifications 1/2 lower without sparsity."; a value transformed from the page belongs in a DERIVED number
R1:interp:top: gate in phase_compose fails at the plan's own value: composed out-of-order reconstruction R² at 42 layers is 0.5, needs ≥ 0.9; expected path: record if_not and write up; the width sweep becomes optional.
R1:interp:top: prior_max_level 10 is not in the quote of s_ato
R1:interp:top: question: a sentence of 23 words
R1:interp:top: hypothesis: a sentence of 21 words
R1:interp:top: test_summary: a sentence of 36 words
R1:interp:top: novelty.closest_prior: a sentence of 25 words
R1:interp:top: novelty.left_open: a sentence of 23 words
R1:interp:top: limits: a sentence of 22 words
R1:interp:top: card fields failing: novelty.closest_prior (compute-hours)
R1:interp:top: novelty.closest_prior: rewritten by the field repair
R1:interp:top: card field novelty.closest_prior still fails: compute-hours
R1:physical:top: dramaturg: degenerate: card:question; degenerate: card:test_summary; degenerate: card:anchor; degenerate: card:limits
R1:interp:top: dramaturg: degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:limits
R1:physical:top: dramaturg (resample): degenerate: card:question; degenerate: card:test_summary; degenerate: card:anchor; degenerate: card:limits
R1:physical:top: dramaturg findings failed G-find after a resample; decided as returned
render card R1:interp:Linear feature representation -> parallel-in-time for free failed: Cannot read properties of null (reading 'toFixed')
```