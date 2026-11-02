# Operator takeaway — raid: whisper3

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, anchored=false, licence=unknown, licence_basis=none, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 225.97508481 | 0 | 0 | 487536 | 7791 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3472.6153421159997 | 49.64 | 2.9198749999999998 | 929140 | 10389 | codex |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 7703.258055208002 | 494.1 | 7.0406 | 0 | 0 | none |
| seal | PASS | seal_present=true, seal_verified=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 116.31357582799905 | 0 | 0 | 732567 | 4257 | codex |
| propose | PASS | gate_pass=false, run_valid=null, calibration_valid=null, outcome=no_feasible_method, votes_approve=0, votes_reject=0, votes_abstain=0, votes_null=null | 0 | null | null | null | null | null | 0.0022978460006415845 | 0 | 0 | 0 | 0 | none |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 2.6146000251173973e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 5.7208999991416934e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00013975800015032292 | 0 | 0 | 0 | 0 | none |

Execution authority: owner's standing instruction (2026-10-30), not licence evidence.

Finding: negative. No menu method has measured headroom of at least 1.05 on this hardware.

| box_type | price_usd_h |
|---|---|
| gpu_1x_h100_pcie | 3.29 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 11518.164578921002 | 543.74 | 10.526876830555555 | 2149243 | 22437 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
