# Operator takeaway — raid: bagman2

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, anchored=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 108.001487412 | 0 | 0 | 181206 | 5513 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 283.919155065 | 57.9 | 0.052316666666666664 | 176593 | 6354 | codex |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 1418.151404847 | 523.84 | 0.5081166666666667 | 0 | 0 | none |
| seal | PASS | seal_present=true, seal_verified=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 68.46440874900017 | 0 | 0 | 138721 | 3374 | codex |
| propose | PASS | gate_pass=true, run_valid=null, calibration_valid=null, outcome=approved, votes_approve=5, votes_reject=0, votes_abstain=0, votes_null=0 | 1 | null | null | 1.125 | null | null | 34.84653496500012 | 0 | 0 | 88188 | 1249 | claude |
| implement | FAIL | patch_applies=true, tests_pass=false, blind_tests=true, launch_review_pass=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 2954.5683083349995 | 90.2 | 0.9151833333333333 | 1309879 | 17160 | codex |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.3234999515116216e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00010870200023055077 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_1x_a10 | 1.29 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 4867.95144131 | 671.94 | 1.7445866833333334 | 1894587 | 33650 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
