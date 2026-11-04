# blind-02 run8 predictions: s28's fixture rerun, a sealed comparison (operator, metadata only; sealed before launch)

Operator exposure as recorded in `run1.md`: the operator is not blind to this experiment's brief; these are not blind predictions. The operator has not read steps s07 to s28, the fixture designs, the comparison requests, their predictions or any reader report.

## Design

run7 (s27's fixture run, code 65cd5d59) passed every stage, but science step s28 (Opus, 7884c56a) found every one of its 13 invocations failed (`fixture_coverage` none, `coverage_cause` failures, `isolation_concern` none, `margins_defensible` none, `tolerance_rule` s27_unchanged) and asked for a fixture rerun of the same shape: 4 arms, 4 inputs, 12 comparisons, 6 replicates, evaluate `budget_s` 16,200; projected USD 5 to 20 and 3 to 6 h; `main_runs_fit_after` yes; 17 agent predictions sealed. An authorized reader (`run7_failcause`, Opus, 255fc242) found: `invocation_failure` evaluator_error, `failure_caused_by` design_or_harness, `mechanism_defect` none, `s28_design_addresses_cause` yes, `s28_fits_budget` at_risk, `rerun_justified` yes. run7 measured about 960 s per `comparison` receipt on an A10.

Run: `new_run.py .../m5/run8 --brief-from=s28` (no other flags), `retry53.sh` (box types at most USD 3.29/h, H100 first; box `--max-hours 6`). blind-02 ledger before launch: USD 6.64 of 100.

## Decision rule (fixed before launch)

| Result | Next |
|---|---|
| Evaluate PASS (scored file written) | Science step s29 applies the sealed tolerance rule to run8, scores s28's predictions, and designs the main comparison or the next test. |
| Evaluate FAIL `infra` at `comparison-users`, or any receipt suggesting an isolation failure | No relaunch; the operator reproduces it on a public shakedown run first. |
| A model refusal halts a stage | Report to the owner; no relaunch. |
| Any other FAIL or VOID | Science step s29 assesses it; a failed fixture run stays failed. |
| Infra failure at the first box command | One unchanged relaunch. |

## Predictions

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.85 |
| 2 | Reproduce PASS | 0.80 |
| 3 | `comparison-users` passes (given evaluate starts) | 0.90 |
| 4 | Evaluate PASS, scored file written | 0.65 |
| 5 | Every evaluate box command rc 0 and none timed out (given evaluate starts) | 0.70 |
| 6 | Box type H100 | 0.35 |
| 7 | More than 13 invocations run (given evaluate starts) | 0.75 |
| 8 | The evaluate stage's wall within 300 s of `budget_s` (the budget is spent before the design is done) | 0.50 |
| 9 | Science step s29 reports `fixture_coverage` full | 0.30 |
| 10 | Science step s29 reports at least some margins defensible | 0.50 |
| 11 | Pipeline wall under 4.5 h | 0.55 |
| 12 | Run box USD under 10 | 0.65 |
| 13 | Run box USD under 19.74 (the cap) | 0.95 |
| 14 | Any stage halted by a model refusal | 0.05 |
| 15 | blind-02 ledger after the run under USD 30 | 0.90 |
