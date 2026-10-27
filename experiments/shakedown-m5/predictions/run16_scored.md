# run16: outcome against sealed predictions (predictions/run16.md, 90045f0)

Run committed 48128fa. Box gpu_1x_h100_sxm5, USD 4.29/h; run_box_usd 0.60; 307,950 tokens over 8 agent calls (claude/sonnet 2 calls, USD 0.071); pipeline exit 0; box torn down; push verified.

| Prediction | Outcome | Hit |
|---|---|---|
| H100 0.5 | H100 SXM5 | yes |
| intake PASS 0.95, anchors 2 | PASS, 2 | yes |
| reproduce PASS 0.9, 2/2 | PASS, 2/2 | yes |
| profile PASS 0.9, no timed_out 0.9 | PASS, no timeout | yes |
| headroom numeric 0.85, MPS without fallback 0.8 | 1.262, mps true, mps_failed false | yes |
| headroom on H100 median 2.5, [1.4, 3.8] | 1.262 (n2 1.150, n4 1.262; singles 1.14, 0.887, 0.892 s) | **no**: outside the interval |
| pipelining and multi-GPU infeasible 0.97 | both bound 1.0 | yes |
| seal PASS 0.75, prediction_count 3 | PASS, 3 | yes |
| propose reached 0.8 | reached | yes |
| method data-parallel 0.5, ensembles 0.3, batching 0.2 | batching (expected 1.135) | weak (0.2) |
| votes_approve median 2, gate_pass 0.3 | 2/5, gate fail | yes |
| equivalence_risk dominant | weak_profile_evidence on 3/3 Codex abstentions; equivalence_risk once | **no** |
| Claude ballots valid 0.95 | both valid | yes |
| Claude approves more than Codex 0.55 | Claude 2/2 approve (no reason codes), Codex 0/3 (all abstain) | yes |
| implement, evaluate SKIPPED 0.7, 0.8 | SKIPPED | yes |
| run_box_usd 0.3 to 1.5 | 0.60 | yes |
| tokens 250k to 600k | 308k | yes |

## Misses and their causes (read after the run; public content)
- Headroom: the probe log shows 1,048,576 options x 262,144 paths under strong scaling; I recalled 256 options. One copy fills the H100, so MPS overlaps only host start-up. Kernels at 37% of wall and CUDA API host time at 38% are consistent with a 1.26 factor. My own "what would change my mind" item (occupancy recollection wrong) fired.
- Ballots split exactly by family. All three Codex skeptics (low effort) abstained citing weak_profile_evidence; both Claude Sonnet skeptics approved with no reason codes. With a 4/5 gate this split means at least two Codex approvals are needed for any method to pass. The propose packet carries the factor and MPS flag in k_derivation but not the raw probe timings. Not changed: this run is a negative control and rejection is the expected outcome; the blind OpenMM run tests whether the split is a family trait or MonteCarlo-specific.
