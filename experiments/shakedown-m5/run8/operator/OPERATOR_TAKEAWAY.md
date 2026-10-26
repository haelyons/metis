# Operator takeaway — raid: cutter

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 128.451330077 | 0 | 0 | 217289 | 4314 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=true, calibration_valid=null | null | null | null | null | null | null | 687.3027874969999 | 0 | 0.3468388888888889 | 599063 | 16134 | codex |
| profile | FAIL | profile_complete=false, gpu_telemetry=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 152.09343417400007 | 0 | 0.14665000000000003 | 140542 | 1844 | codex |
| seal | SKIPPED | seal_present=null, seal_verified=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 2.8598000062629582e-05 | 0 | 0 | 0 | 0 | none |
| propose | SKIPPED | gate_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.55429999763146e-05 | 0 | 0 | 0 | 0 | none |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 2.8518999926745893e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 4.3216999969445167e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00011645199998747557 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| unknown | 8.38 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 967.847804077 | 0 | 2.2542479333333336 | 956894 | 22292 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
