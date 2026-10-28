# Operator takeaway — raid: cutter2

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, anchored=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 114.50039710600001 | 0 | 0 | 137054 | 5320 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 286.909852045 | 46.28 | 0.15536111111111112 | 207878 | 6221 | codex |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 1705.734301566 | 356.88 | 1.5590944444444446 | 0 | 0 | none |
| seal | PASS | seal_present=true, seal_verified=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 109.3766068429998 | 0 | 0 | 141412 | 3487 | codex |
| propose | PASS | gate_pass=true, run_valid=null, calibration_valid=null, outcome=approved, votes_approve=5, votes_reject=0, votes_abstain=0, votes_null=0 | 1 | null | null | 1.5 | null | null | 29.502959872000385 | 0 | 0 | 88119 | 1186 | claude |
| implement | PASS | patch_applies=true, tests_pass=true, blind_tests=true, launch_review_pass=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 4135.359556854 | 74.58 | 3.309191666666667 | 1524638 | 15458 | claude |
| evaluate | VOID | validity_pass=true, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 387.5867649260005 | 78.66 | 0.3545888888888889 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00013611599989235402 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_1x_h100_pcie | 3.29 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 6768.970575328001 | 556.4 | 6.186747213888889 | 2099101 | 31672 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
