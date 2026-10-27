# Sealed operator predictions: shakedown-m5 run16

Written and committed before launch. Run: public negative control, MonteCarloMultiGPU (same BRIEF.md as run11 to run15), harness reused from run11, single-GPU dev box, `m5/wf_config.json` (skeptic-4, skeptic-5 and review on claude/sonnet). Code under test: u18 (concurrency probe, measured whole-workload bounds, equal-cost multi-GPU bound) and u19 (judge split).

Evidence used: run15's public profile packet (total 1.151 s: kernels 0.482 s, CUDA API host time 0.503 s, other host 0.165 s, transfers 0) and recollection of the CUDA sample (256 options, one 256-thread block per option, so one copy under-occupies a large GPU). Probabilities are mine; intervals are 80%.

## Box
- 1-GPU type chosen in list order; H100 (SXM5 or PCIe) 0.5, A100 0.3, A10 0.2.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.95; anchors_count 2, data available, licence permitted |
| reproduce | PASS 0.9; anchors 2/2, stock_verified true (anchors are prices, not GPU-count dependent) |
| profile | PASS 0.9; timed_fraction 1, gpu_telemetry true; no timed_out fact 0.9 |
| profile headroom | numeric 0.85, null 0.15. MPS used without fallback 0.8. Given numeric on H100/A100: median 2.5, interval [1.4, 3.8]; on A10: median 1.6, interval [1.1, 2.5]. headroom >= 1.05 overall 0.85 |
| bounds | pipelining and multi-GPU infeasible 0.97 (transfers 0; gpu_count 1 gives Amdahl/k = 1). data-parallel, ensembles and batching each = min(cap, headroom) |
| seal | PASS 0.75; prediction_count 3 given headroom >= 1.05 (0.7), 0 when headroom < 1.05 |
| propose | reached with a feasible method 0.8. Method: data-parallel over inputs 0.5, ensembles 0.3, batching 0.2. votes_approve median 2; gate_pass 0.3. Dominant reject reason still equivalence_risk (no seed control); weak_profile_evidence rarer than runs 11 to 15 |
| propose, Claude ballots | both Claude ballots return a valid vote 0.95 (refusal 0.03); Claude approves at a higher rate than Codex 0.55 |
| implement | SKIPPED 0.7. If reached: patch_applies 0.85, tests_pass 0.6, launch_review_pass 0.6 |
| evaluate | SKIPPED 0.8. If reached: validity_pass 0.7; measured speedup published 1.1 to 1.6 (each part repeats the ~0.67 s fixed host cost, so below headroom); performance_pass 0.4 |
| takeaways | PASS; run_box_usd 0.3 to 1.5 if the run stops at propose, 1.5 to 5 if it reaches evaluate |

## Run level
- Pipeline exit 0 and box torn down: 0.95. Push verified: 0.95.
- End-to-end pass (evaluate performance_pass true): 0.08.
- Tokens per run: 250k to 600k if it stops at propose.

## What would change my mind
- headroom near 1 on an H100 with MPS: the GPU is the bottleneck even for one copy; my occupancy recollection is wrong.
- headroom above 4: host-side setup dominates more than the profile suggests; the probe overstates the gain available from splitting one workload.
- gate_pass true with 5/5: the skeptics accept stochastic equivalence once measured headroom exists, and implement and evaluate become the binding test.
