# Operator takeaway — raid: wheelman2

## Compute

| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | wall_s | gpu_s | usd | tokens_in | tokens_out | model_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intake | PASS | found=true, stock_environment=null, anchored=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 111.46399708099999 | 0 | 0 | 148886 | 5011 | codex |
| reproduce | PASS | stock_verified=true, tuned_control_valid=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 737.493861253 | 53.160000000000004 | 0.22442777777777778 | 586221 | 16036 | codex |
| profile | PASS | profile_complete=true, gpu_telemetry=true, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 1092.855519435 | 415.74 | 0.6041861111111111 | 0 | 0 | none |
| seal | FAIL | seal_present=false, seal_verified=false, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 133.45294839100004 | 0 | 0 | 222732 | 4666 | codex |
| propose | SKIPPED | gate_pass=null, run_valid=null, calibration_valid=null, outcome=null, votes_approve=null, votes_reject=null, votes_abstain=null, votes_null=null | null | null | null | null | null | null | 5.792100005783141e-05 | 0 | 0 | 0 | 0 | none |
| implement | SKIPPED | patch_applies=null, tests_pass=null, blind_tests=null, launch_review_pass=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 3.384899999946356e-05 | 0 | 0 | 0 | 0 | none |
| evaluate | SKIPPED | validity_pass=null, equivalence_pass=null, performance_pass=null, equal_cost=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 6.184000009670853e-05 | 0 | 0 | 0 | 0 | none |
| takeaways | PASS | operator_written=null, research_written=null, teardown_confirmed=null, run_valid=null, calibration_valid=null | null | null | null | null | null | null | 0.00015554499998688697 | 0 | 0 | 0 | 0 | none |

| box_type | price_usd_h |
|---|---|
| gpu_1x_a100_sxm4 | 1.99 |

## Totals

| wall_s | gpu_s | usd | tokens_in | tokens_out |
|---|---|---|---|---|
| 2075.2666353150003 | 468.90000000000003 | 1.1474682722222223 | 957839 | 25713 |

Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only.

## Blockers

- none

This page is mechanical and holds no domain content.
