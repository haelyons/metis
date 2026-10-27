# Operator takeaway — raid: crowbar2

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 86.66875169 | 0 | 0 | 118332 | 3389 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=true, calibration_valid=null | null | null | null | null | null | null | 117.07575676699999 | 0 | 0.139425 | 0 | 0 | none |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 96.78803766800003 | 6 | 0.11559166666666666 | 0 | 0 | none |
| seal | PASS | seal_present=true, seal_verified=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 153.28900238199998 | 0 | 0 | 78647 | 4330 | codex |
| propose | FAIL | gate_pass=false, run_valid=null, calibration_valid=null | 0.4 | null | null | 1.135 | null | null | 49.73217270300002 | 0 | 0 | 99612 | 1813 | codex |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 4.6888000040780756e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.5659999994095415e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00015376200003083796 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_1x_h100_sxm5 | 4.29 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 503.5539575200001 | 6 | 0.6007561083333334 | 296591 | 9532 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
