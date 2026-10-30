# Operator takeaway — raid: crowbar3

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, anchored=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 104.327948955 | 0 | 0 | 158119 | 4785 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 304.723148401 | 47.260000000000005 | 0.09176111111111111 | 157198 | 6866 | codex |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 815.24888701 | 406.36 | 0.4505138888888889 | 0 | 0 | none |
| seal | PASS | seal_present=true, seal_verified=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 102.25068961 | 0 | 0 | 189910 | 4090 | codex |
| propose | PASS | gate_pass=true, run_valid=null, calibration_valid=null, outcome=approved, votes_approve=5, votes_reject=0, votes_abstain=0, votes_null=0 | 1 | null | null | 1.3525510578740088 | null | null | 33.44801200100011 | 0 | 0 | 87870 | 1145 | claude |
| implement | FAIL | patch_applies=true, tests_pass=false, blind_tests=true, launch_review_pass=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 2690.990745154 | 550.28 | 0.9679138888888889 | 2745219 | 22591 | codex |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 5.338199995458126e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.0001951459995470941 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_1x_a100_sxm4 | 1.99 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 4050.989679658999 | 1003.9 | 2.239618413888889 | 3338316 | 39477 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
