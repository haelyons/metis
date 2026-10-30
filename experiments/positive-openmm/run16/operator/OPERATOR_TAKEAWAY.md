# Operator takeaway — raid: sledge3

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, anchored=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 143.270192056 | 0 | 0 | 146319 | 4917 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 509.5308589239999 | 49.24 | 0.1962361111111111 | 220863 | 6341 | codex |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 1043.672652237 | 418.94 | 0.5765472222222222 | 0 | 0 | none |
| seal | PASS | seal_present=true, seal_verified=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 92.30615589099983 | 0 | 0 | 190993 | 3174 | codex |
| propose | PASS | gate_pass=true, run_valid=null, calibration_valid=null, outcome=approved, votes_approve=5, votes_reject=0, votes_abstain=0, votes_null=0 | 1 | null | null | 1.375 | null | null | 32.37018312100018 | 0 | 0 | 87495 | 1175 | claude |
| implement | PASS | patch_applies=true, tests_pass=true, blind_tests=true, launch_review_pass=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3385.722396919 | 502.76000000000005 | 1.5903416666666668 | 1767008 | 21131 | claude |
| evaluate | PASS | validity_pass=true, equivalence_pass=true, performance_pass=true, equal_cost=true, run_valid=null, calibration_valid=null | null | 1.3039000464669088 | null | null | 0.766929951961911 | 0.9482909428850246 | 1390.0296072029994 | 668.6 | 0.7678083333333333 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.0004235020000487566 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_1x_a100_sxm4 | 1.99 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 6596.902469852999 | 1639.54 | 3.647028777777778 | 2412678 | 36738 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
