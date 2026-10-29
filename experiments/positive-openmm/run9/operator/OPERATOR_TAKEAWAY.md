# Operator takeaway — raid: lookout2

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, anchored=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 132.110803894 | 0 | 0 | 152180 | 5160 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 377.305269072 | 57.94 | 0.05840833333333333 | 226864 | 7134 | codex |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 1569.0696175760002 | 525.74 | 0.5622250000000001 | 0 | 0 | none |
| seal | PASS | seal_present=true, seal_verified=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 123.25629438700015 | 0 | 0 | 186575 | 4140 | codex |
| propose | PASS | gate_pass=true, run_valid=null, calibration_valid=null, outcome=approved, votes_approve=5, votes_reject=0, votes_abstain=0, votes_null=0 | 1 | null | null | 1.175 | null | null | 49.94807496400038 | 0 | 0 | 88727 | 1214 | claude |
| implement | PASS | patch_applies=true, tests_pass=true, blind_tests=true, launch_review_pass=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3196.74123092 | 46.94 | 0.9854166666666666 | 870094 | 15438 | claude |
| evaluate | VOID | validity_pass=true, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 1058.8826919509993 | 569.28 | 0.37911666666666666 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00011165199987590314 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_1x_a10 | 1.29 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 6507.3140944159995 | 1199.9 | 2.3320032333333334 | 1524440 | 33086 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
