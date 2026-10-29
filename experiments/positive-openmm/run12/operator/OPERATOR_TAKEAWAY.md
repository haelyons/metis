# Operator takeaway — raid: tipoff2

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, anchored=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 132.91689974 | 0 | 0 | 181095 | 5711 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 306.71743272000003 | 53.800000000000004 | 0.09065555555555556 | 196736 | 6153 | codex |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 1409.0042381970002 | 414.26 | 0.7788638888888889 | 0 | 0 | none |
| seal | PASS | seal_present=true, seal_verified=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 109.60627332799999 | 0 | 0 | 190467 | 3623 | codex |
| propose | PASS | gate_pass=true, run_valid=null, calibration_valid=null, outcome=approved, votes_approve=5, votes_reject=0, votes_abstain=0, votes_null=0 | 1 | null | null | 1.4249999999999998 | null | null | 39.68444480099995 | 0 | 0 | 87891 | 1203 | claude |
| implement | PASS | patch_applies=true, tests_pass=true, blind_tests=true, launch_review_pass=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 5619.702845991001 | 442.92 | 2.771075 | 1491268 | 15837 | claude |
| evaluate | VOID | validity_pass=true, equivalence_pass=true, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3867.689063441001 | 2710.06 | 2.1370388888888887 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00011997600086033344 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_1x_a100_sxm4 | 1.99 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 11485.321318194003 | 3621.04 | 6.34920666111111 | 2147457 | 32527 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
