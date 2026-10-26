# Operator takeaway — raid: lookout

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 113.566369537 | 0 | 0 | 157370 | 4370 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=true, calibration_valid=null | null | null | null | null | null | null | 467.99503315300007 | 0 | 0.29097222222222224 | 436439 | 12443 | codex |
| profile | FAIL | profile_complete=false, gpu_telemetry=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 222.55222810900003 | 2 | 0.3212333333333333 | 248325 | 2150 | codex |
| seal | SKIPPED | seal_present=null, seal_verified=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 4.193700000178069e-05 | 0 | 0 | 0 | 0 | none |
| propose | SKIPPED | gate_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 4.8349000047892335e-05 | 0 | 0 | 0 | 0 | none |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.45119999255985e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.0183999915607273e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00016583499999251217 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| unknown | 8.38 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 804.113951616 | 2 | 1.8732698555555556 | 842134 | 18963 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
