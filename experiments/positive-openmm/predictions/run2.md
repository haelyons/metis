# Sealed operator predictions: positive-openmm run2

Written and committed before launch. Same brief as run1 (`experiments/positive-openmm/BRIEF.md`, e91489b), fresh harness (run1's harness cleared `CUDA_MPS_*` and is not reused). Single-GPU dev box, `m5/wf_config.json`. Code under test at 1a2052b adds U22 (probe verifies MPS client connections; harness prompts forbid touching `CUDA_MPS_*`) and U23 (negative finding needs a verified MPS state and at least one GPU). Probabilities are mine; intervals are 80%.

Evidence used: run1's public measurements on an H100 PCIe (sequential ensemble 52 to 55 s, 1,335 ns/day; GPU utilisation 85%; one host synchronisation per step; 33 launches per step at 3.5 µs; time-sliced concurrency factor 0.86 at 2 and 4 copies), NVIDIA's report of about 5,000 ns/day for eight DHFR runs on an H100 under MPS, and run1's stage behaviour.

## Box
- H100 SXM5 0.4, H100 PCIe 0.35, A100 0.15, A10 0.1.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.85; anchored false 0.85 (NVIDIA figure as a reference) |
| reproduce | PASS 0.85 given intake PASS; sequential ensemble on H100 45 to 70 s |
| harness respects the MPS rule | no `CUDA_MPS_*` assignment or unset in any harness script 0.85 |
| profile | PASS 0.9 given reproduce PASS |
| probe MPS state | mps true (verified) 0.75; mps_failed true 0.2 (mostly the harness ignoring the rule, or MPS clients not logged as expected); MPS absent 0.05 |
| headroom given verified MPS | H100 median 1.7 [1.1, 2.6]; A100 median 1.5 [1.05, 2.2]; A10 median 1.15 [0.9, 1.6]. headroom >= 1.05 given verified MPS 0.85 |
| headroom given mps_failed | 0.8 to 1.0 (time-sliced, as run1) |
| seal | PASS 0.75 given profile PASS; prediction_count 3 given headroom >= 1.05 |
| propose | given feasible methods: outcome approved 0.6, rejected 0.3, conditions_unmet 0.1. Method ensembles 0.45, data-parallel over inputs 0.45, batching 0.1. Given mps_failed true: FAIL numeric with outcome null 0.9 (U23) |
| implement | reached 0.2 overall. Given reached: PASS 0.45; the method starts its own MPS daemon 0.7 |
| evaluate | reached 0.09 overall. Given reached: validity_pass 0.85, equivalence_pass 0.7, performance_pass 0.55; speedup_published on H100 1.3 to 2.4 |
| takeaways | PASS 0.95; run_box_usd 1 to 3 if the run stops at or before propose, 3 to 8 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified: 0.93.
- Reaches implement 0.2; reaches evaluate 0.09; end-to-end PASS 0.045.
- Measured negative finding (no_feasible_method with verified MPS) 0.08.

## What would change my mind
- Verified MPS with headroom below 1.05 on an H100: DHFR at 4 fs with deterministic forces saturates the GPU even with kernels from several processes overlapping; NVIDIA's gain does not transfer to this configuration, and the negative finding is real.
- mps_failed true with a harness that leaves `CUDA_MPS_*` alone: the control-log check does not see clients that did connect (log format or per-process logging differs on this driver), so the verification itself needs fixing.
- Headroom above 3: host overhead in the sequential run is larger than the profile suggests.
