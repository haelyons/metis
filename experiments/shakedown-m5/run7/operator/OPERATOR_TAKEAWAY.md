# Operator takeaway — raid: smashgrab

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 122.106372499 | 0 | 0 | 100304 | 3869 | codex |
| reproduce | FAIL | stock_verified=false, tuned_control_valid=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 627.173430222 | 0 | 0.961 | 357679 | 11806 | codex |
| profile | SKIPPED | profile_complete=null, gpu_telemetry=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 2.9211000073701142e-05 | 0 | 0 | 0 | 0 | none |
| seal | SKIPPED | seal_present=null, seal_verified=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 6.965600000694395e-05 | 0 | 0 | 0 | 0 | none |
| propose | SKIPPED | gate_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.479700000025332e-05 | 0 | 0 | 0 | 0 | none |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 4.126800002995878e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 4.576799995265901e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.0001130500000435859 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_8x_a100_80gb_sxm4 | 22.32 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 749.2801364710001 | 0 | 4.6489522 | 457983 | 15675 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
