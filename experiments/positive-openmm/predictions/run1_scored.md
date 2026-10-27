# positive-openmm run1: outcome against sealed predictions (predictions/run1.md, f01c6de)

Run committed ec8f6d5 (raid sledge2). Box gpu_1x_h100_pcie, USD 3.29/h; run_box_usd 1.58; 650,741 tokens in; pipeline exit 0; box torn down. The first push was rejected because the commit held a 917 MB derived Nsight SQLite export; the file was removed from the unpushed commit and ignored (40c3dc0) before the push was verified.

## Verdict
The pipeline ran every stage it could and reported a measured negative finding ("no menu method has measured headroom of at least 1.05"). **The finding is invalid.** The harness agent's `run_command.sh` (also `setup.sh` and `run_evaluation.sh`) runs `unset CUDA_MPS_ACTIVE_THREAD_PERCENTAGE CUDA_MPS_PIPE_DIRECTORY CUDA_MPS_LOG_DIRECTORY`. The concurrency probe starts its MPS daemon on a private pipe directory and passes it through exactly those variables, so every probe copy looked for the default pipe directory, found no daemon and ran without MPS (time-sliced contexts). The probe still recorded `mps: true` because it checks only that its daemon started. The factor 0.864 therefore measures time-sliced concurrency, mislabelled as MPS; it cannot support a statement about this hardware with MPS. Under the stopping principle this is untrustworthy evidence, not a negative result.

Supporting evidence (public files): singles 53.9, 54.5, 54.4 s (1,335 ns/day aggregate); two copies 126.0 s (558 ns/day each, 1,116 total); four copies 252.3 s (285 each, 1,140 total). Both batch factors 0.86, flat from 2 to 4 copies, as expected for time-slicing overhead rather than a saturated GPU under MPS. NVIDIA reports about 5,000 ns/day for eight DHFR simulations on an H100 with MPS. Single-run GPU utilisation 85%, one `cuEventSynchronize` per step (102 µs mean), 33 kernel launches per step at 3.5 µs each: the single run leaves gaps that MPS could fill.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| H100 SXM5 0.5, PCIe 0.15 | H100 PCIe | weak (0.15) |
| intake PASS 0.8 | PASS (found true, data available, licence permitted) | yes |
| anchored false 0.8; anchors_count 0 to 2 | false; 1 reference (NVIDIA 5.0 µs/day, tolerance null) | yes |
| reproduce PASS 0.75; run_valid null 0.8 | PASS; null; reference measured 1.31 µs/day for the sequential ensemble, reported and not scored | yes |
| sequential ensemble on H100 40 to 90 s | 52 to 55 s | yes |
| profile PASS 0.85; timed_fraction 1 | PASS; 1 | yes |
| headroom numeric 0.85, MPS used without fallback 0.8 | numeric 0.864; `mps: true` recorded but MPS not in effect | numeric yes; MPS **no** (the record is wrong) |
| headroom H100 median 1.9 [1.3, 2.8] | 0.864 (time-sliced, see verdict) | **no**; not a valid test of the prediction |
| multi-GPU and pipelining infeasible 0.95 | both infeasible | yes |
| seal PASS 0.7; prediction_count 3 given headroom >= 1.05 | PASS with 0 predictions (all five infeasible) | conditional not met |
| negative finding 0.05 | occurred, from the defect | occurred; mechanism not the predicted one |
| reaches implement 0.18 | no | consistent |
| run_box_usd 0.8 to 2.5 if stopping at or before propose | 1.58 | yes |
| tokens 300k to 700k if stopping at propose | 651k in | yes |
| stop stage before implement: propose 0.3 | propose (by finding) | yes, for the wrong reason |

## What worked
- Supplying the benchmark directly removed discovery failure: intake passed with an unanchored reference, as U20 intends.
- The U20 reference path behaved correctly: a published fixed-time MPS figure was compared with a sequential fixed-work measurement, reported as a difference and never scored.
- U21b's negative-finding path executed end to end (seal PASS with zero predictions, no model calls in propose, implement and evaluate SKIPPED, Finding line in the takeaway).

## What failed, and the fix order
1. Measurement (fix first): the probe must verify that MPS actually served the copies, not only that the daemon started; a harness must not set or clear `CUDA_MPS_*` variables, because the pipeline owns MPS.
2. Gate (after 1): a negative finding must rest on a verified MPS state, i.e. MPS verified in use, or MPS absent from the box. A factor measured with MPS present but unused or failed is missing evidence.
3. Rerun the positive control with a fresh harness (no reuse of run1's harness, which carries the `unset` line).

## What would have changed my mind, checked
- "Headroom near 1 on an H100 under MPS" fired, but the condition was not met: MPS was not in effect. The hypothesis remains untested.
