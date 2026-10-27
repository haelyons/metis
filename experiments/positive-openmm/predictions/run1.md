# Sealed operator predictions: positive-openmm run1

Written and committed before launch. Run: public positive control. Brief `experiments/positive-openmm/BRIEF.md` (e91489b), written by the operator with a verified benchmark supplied directly: OpenMM 8.2.0 DHFR `pme` model, fixed work of 8 replicas × 25,000 steps, seeds 1000 to 1007, CUDA with deterministic forces, run one after another. No harness reuse. Single-GPU dev box, `m5/wf_config.json`. Code under test at e90b6fb: U20 (references without tolerances, `anchored`), U21a (reject vs abstain ballots), U21b (measured negative finding).

Purpose: test whether the pipeline reaches implement and independent evaluate when benchmark discovery is removed, and whether the measured headroom agrees with a published MPS result. Probabilities are mine; intervals are 80%.

Evidence used: the brief; NVIDIA's 2025 post (DHFR total throughput on an H100 "can more than double" under MPS with up to 8 processes); run16's probe behaviour (the probe runs whole copies of the run command under MPS, singles then 2 then 4 copies, budget `profile`); the run16 ballot split (Codex abstains on weak evidence, Claude approves).

## Box
- 1-GPU type in list order: H100 SXM5 0.5, H100 PCIe 0.15, A100 0.2, A10 0.15.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.8. Failure modes: `found` false because the driver is embedded in the brief rather than published (0.1); data or licence not marked available/permitted (0.1). anchored false 0.8 (NVIDIA figures recorded as references, or none); anchors_count 0 to 2 |
| reproduce | PASS 0.75 given intake PASS. Failure mostly install (pip wheels against the stock driver) or the harness rewriting the driver. run_valid null 0.8. Single sequential ensemble on H100 40 to 90 s |
| profile | PASS 0.85 given reproduce PASS; timed_fraction 1 (by construction); gpu_telemetry true |
| profile headroom | numeric 0.85; MPS used without fallback 0.8. Given numeric: H100 median 1.9 [1.3, 2.8]; A100 median 1.6 [1.15, 2.3]; A10 median 1.2 [1.0, 1.6]. headroom >= 1.05 overall 0.85. On an A10 the 4-copy batch may be skipped by the budget rule (0.4 given A10) |
| bounds | multi-GPU and pipelining infeasible 0.95 (one GPU, negligible transfers); data-parallel, batching and ensembles each min(cap, headroom) |
| seal | PASS 0.7 given profile PASS. prediction_count 3 given headroom >= 1.05 (0.7). Deterministic protocol chosen (exact or zero-tolerance per seed) 0.5, stochastic paired-median 0.5 |
| propose | reached with a feasible method 0.85 given seal PASS. Method: ensembles 0.45, data-parallel over inputs 0.45, batching 0.1. outcome approved 0.6, rejected 0.3, conditions_unmet 0.1. votes_reject median 1; Codex ballots abstain more than reject 0.6 |
| negative finding | outcome no_feasible_method 0.05 (only if headroom < 1.05 with MPS) |
| implement | reached 0.18 overall. Given reached: patch_applies 0.85, tests_pass 0.6, blind_tests 0.9, launch_review_pass 0.6, PASS 0.45 |
| evaluate | reached 0.08 overall. Given reached: validity_pass 0.85 (no anchors: passes when the protocol exits 0), equivalence_pass 0.65, performance_pass 0.6; speedup_published on H100 1.5 to 2.6 |
| takeaways | PASS 0.95. run_box_usd 0.8 to 2.5 if the run stops at or before propose, 2.5 to 7 if it reaches evaluate |

## Run level
- Pipeline exit 0 and box torn down: 0.95. Push verified: 0.95.
- Reaches implement: 0.18. Reaches evaluate: 0.08. End-to-end PASS (evaluate PASS): 0.04.
- Tokens: 300k to 700k if it stops at propose; 1M to 3M if it reaches evaluate.
- The stage that stops the run, if it stops before implement: intake 0.2, reproduce 0.25, profile 0.1, seal 0.15, propose 0.3.

## What would change my mind
- Headroom near 1 on an H100 under MPS: a single DHFR replica already saturates the GPU in this configuration, contradicting the NVIDIA post; the brief's hypothesis would be refuted for fixed work.
- Headroom above 3 on an H100: context creation and host overhead dominate the sequential run, so the gain comes from overlapping set-up rather than kernels.
- Intake FAIL on `found`: the intake definition treats a brief-supplied driver around a published benchmark as not published. That would show supplying a benchmark directly does not separate discovery from validation as intended.
- Gate rejection with defect codes from Claude ballots: the skeptics see a real defect in the proposal (most likely equivalence_risk for concurrent seeds), not missing evidence.
