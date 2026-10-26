# Operator takeaway — raid: bagman

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 115.981590956 | 0 | 0 | 128885 | 3917 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=true, calibration_valid=null | null | null | null | null | null | null | 535.9100748769999 | 0 | 0.3491666666666667 | 369186 | 13177 | codex |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 300.6095320039999 | 0 | 0.19786111111111113 | 292937 | 6322 | codex |
| seal | PASS | seal_present=true, seal_verified=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 105.70255576399992 | 0 | 0 | 71051 | 3490 | codex |
| propose | FAIL | gate_pass=false, run_valid=null, calibration_valid=null | 0 | null | null | 1.6145573419604862 | null | null | 235.67208515000019 | 0 | 0 | 134530 | 1688 | codex |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.9012999972328546e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 4.2522000148892404e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00014963100012391805 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| unknown | 8.38 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 1293.8760699170002 | 0 | 3.0131966 | 996589 | 28594 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
