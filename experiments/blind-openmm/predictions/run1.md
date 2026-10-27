# Sealed operator predictions: blind-openmm run1

Written and committed before launch, from the hint I wrote and general knowledge of OpenMM only. Code as of 90045f0 (u18 probe and bounds, u19 judge split), single-GPU dev box via retry7.sh. Probabilities are mine; intervals are 80%.

Calibration note from run16 (MonteCarlo, H100): I predicted headroom 2.5 [1.4, 3.8] and measured 1.26, because the workload saturates the GPU (1,048,576 options, not the 256 I recalled). Codex skeptics abstained 3/3 on weak_profile_evidence while both Claude ballots approved; I had predicted equivalence_risk would dominate.

## Box
- H100 SXM5 0.6, other H100 0.1, A100 0.2, A10 0.1.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.8 (found true; the OpenMM repo ships a DHFR benchmark script). anchors_count >= 1: 0.7 (published ns/day tables exist but on named hardware). licence permitted 0.95. stock_environment true 0.7 (pip or conda OpenMM with CUDA) |
| reproduce | PASS 0.5. Main risks: anchors measured on a different GPU than the published one; CUDA platform or driver mismatch in the stock package. If it fails: error_class numeric 0.5, harness/setup 0.5 |
| profile | PASS 0.75 given reproduce PASS. timed_fraction >= 0.9: 0.6. No timed_out fact 0.8 |
| profile headroom | numeric 0.75, null 0.25 (long single runs can push the 4-copy batch past the budget, which leaves the 2-copy factor; null mainly from failed copies, e.g. shared output paths). Given numeric: median 2.2, interval [1.3, 4.0]. DHFR (~23.5k atoms) under-occupies a large GPU and OpenMM start-up (context, kernel compile) overlaps across processes |
| headroom artefact check | P(headroom within 0.1 of 2 or 4 exactly, with T1 roughly equal to batch wall) 0.25: the sign that run_command.sh runs for a fixed time (benchmark seconds) rather than fixed work, so the probe's fixed-work assumption breaks |
| bounds | data-parallel, ensembles = min(8, headroom); batching = min(4, headroom); pipelining infeasible 0.9; multi-GPU infeasible 1.0 |
| seal | PASS 0.7; prediction_count 3 given headroom >= 1.05 |
| propose | reached with a feasible method 0.55 overall. Method: ensembles 0.45, data-parallel 0.35, batching 0.2. gate_pass 0.35 given reached: Claude ballots approve 0.7 each; each Codex ballot approves 0.35 (the hint makes the parallel structure explicit, but run16 shows Codex abstaining on profile evidence) |
| implement | reached 0.2 overall. If reached: patch_applies 0.8, tests_pass 0.6, launch_review_pass (Claude) 0.6 |
| evaluate | reached 0.12 overall. If reached: validity_pass 0.7, equivalence_pass 0.5 (stochastic Langevin trajectories need a distributional rule), performance_pass 0.5, speedup at equal cost 1.3 to 2.5 |
| takeaways | PASS 0.95; run_box_usd 0.5 to 2 if the run stops at or before propose, 3 to 10 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified: 0.9.
- End-to-end pass (evaluate performance_pass true): 0.06.
- Tokens: 300k to 900k.
- Most likely stopping stage: reproduce 0.35, propose 0.3, intake 0.1, profile 0.1, later 0.15.

## What would change my mind
- intake found false: the search-hint path (no brief file) is the bottleneck, not compute.
- headroom below 1.2: OpenMM fills an H100 even with DHFR, or the run is dominated by a serial host phase that MPS does not overlap.
- gate_pass with Codex approving: run16's Codex abstentions were about MonteCarlo's thin profile, not a family trait.
