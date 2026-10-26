# Operator takeaway — raid: wheelman

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 155.63630329100002 | 0 | 0 | 122717 | 4206 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=true, calibration_valid=null | null | null | null | null | null | null | 458.63951732999993 | 18.12 | 0.04765833333333334 | 202660 | 10536 | codex |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 41.04900221099996 | 10 | 0.014691666666666667 | 0 | 0 | none |
| seal | PASS | seal_present=true, seal_verified=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 176.10872696499993 | 0 | 0 | 120257 | 4590 | codex |
| propose | FAIL | gate_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.0001630139999324456 | 0 | 0 | 0 | 0 | none |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.4209000063128766e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.584399993997067e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 7.442499999888241e-05 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_1x_a10 | 1.29 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 831.4338572889998 | 28.12 | 0.29812975 | 445634 | 19332 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
