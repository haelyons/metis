# Operator takeaway — raid: fence

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 78.874282472 | 0 | 0 | 137527 | 4111 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=true, calibration_valid=null | null | null | null | null | null | null | 310.88742590300006 | 0 | 0.3468388888888889 | 354677 | 9474 | codex |
| profile | FAIL | profile_complete=false, gpu_telemetry=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 59.43011554299999 | 0 | 0.1396666666666667 | 0 | 0 | none |
| seal | SKIPPED | seal_present=null, seal_verified=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.354799997759983e-05 | 0 | 0 | 0 | 0 | none |
| propose | SKIPPED | gate_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 5.4630000027827916e-05 | 0 | 0 | 0 | 0 | none |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.9583000005222856e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.63200000138022e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.0001220880000037141 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| unknown | 8.38 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 449.1921100870001 | 0 | 1.0468971055555556 | 492204 | 13585 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
