# Operator takeaway — raid: tipoff

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 88.11698988699999 | 0 | 0 | 97024 | 3333 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=true, calibration_valid=null | null | null | null | null | null | null | 151.289562535 | 0.12 | 0.6677555555555555 | 0 | 0 | none |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 130.940002878 | 0 | 0.5793111111111111 | 0 | 0 | none |
| seal | FAIL | seal_present=false, seal_verified=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 127.773929818 | 0 | 0 | 74363 | 3474 | codex |
| propose | SKIPPED | gate_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 4.275899997446686e-05 | 0 | 0 | 0 | 0 | none |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 2.6387000048998742e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.25779999839142e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00013434399996185676 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_8x_a100 | 15.92 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 498.12072118599997 | 0.12 | 2.2052693555555556 | 171387 | 6807 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
