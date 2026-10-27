# Operator takeaway — raid: driver

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 100.356954014 | 0 | 0 | 118507 | 3816 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=true, calibration_valid=null | null | null | null | null | null | null | 153.18095715700002 | 0 | 0.6766000000000001 | 0 | 0 | none |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 95.778991711 | 0 | 0.4245333333333334 | 0 | 0 | none |
| seal | FAIL | seal_present=false, seal_verified=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 147.98978446599997 | 0 | 0 | 73981 | 4004 | codex |
| propose | SKIPPED | gate_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.464600001461804e-05 | 0 | 0 | 0 | 0 | none |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.7933000014163554e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.173899999819696e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00012753699999302624 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_8x_a100 | 15.92 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 497.306919203 | 0 | 2.201621022222222 | 192488 | 7820 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
