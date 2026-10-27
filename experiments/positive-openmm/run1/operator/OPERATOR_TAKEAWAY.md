# Operator takeaway — raid: sledge2

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, anchored=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 112.596574999 | 0 | 0 | 169551 | 5660 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 432.363277871 | 46.24 | 0.2229888888888889 | 325269 | 9660 | codex |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 1065.648515266 | 531.5 | 0.9742055555555555 | 0 | 0 | none |
| seal | PASS | seal_present=true, seal_verified=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 118.11075050099986 | 0 | 0 | 155921 | 4726 | codex |
| propose | PASS | gate_pass=false, run_valid=null, calibration_valid=null, outcome=no_feasible_method, votes_approve=0, votes_reject=0, votes_abstain=0, votes_null=null | 0 | null | null | null | null | null | 0.002740868999855593 | 0 | 0 | 0 | 0 | none |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.487500012852251e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.078100015409291e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00017399699985980988 | 0 | 0 | 0 | 0 | none |

Finding: negative. No menu method has measured headroom of at least 1.05 on this hardware.

| box_type | price_usd_h |
|---|---|
| gpu_1x_h100_pcie | 3.29 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 1728.7220991589998 | 577.74 | 1.5803862277777778 | 650741 | 20046 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
