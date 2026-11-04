# blind-02 run9 predictions: s29's revised fixture run, a sealed comparison (operator, metadata only; sealed before launch)

Operator exposure as recorded in `run1.md`: the operator is not blind to this experiment's brief; these are not blind predictions. The operator has not read steps s07 to s29, the fixture designs, the comparison requests, their predictions or any reader report.

## Design

run7 (s27's fixture run): every invocation failed (evaluator error; reader run7_failcause). run8 (s28's rerun): evaluate FAIL `infra` at `comparison-users`, `fetch_private.sh` exited nonzero (script error in the harness; reader run8_fetchfail; `mechanism_defect` none in both readers). Science step s29 (Opus, cd2ff5f9): `run7_cause` evaluator, `run8_cause` fetch_script, `change_made` brief_and_design, `change_addresses_both` yes, `tolerance_rule` s27_unchanged, `next_kind` fixture_rerun, projected USD 5 to 20 and 3 to 6 h, `fits_one_allocation` yes_on_both, `main_runs_fit_after` yes; 19 agent predictions sealed. Design as the operator's checks print it: 4 arms, 4 inputs, 12 comparisons, 6 replicates, evaluate `budget_s` 16,200; no sealed number in the agents' view or the brief. Code 65cd5d59 (unchanged since run7).

Run: `new_run.py .../m5/run9 --brief-from=s29` (no other flags), `retry53.sh` (box types at most USD 3.29/h, H100 first; box `--max-hours 6`). blind-02 ledger before launch: USD 8.38 of 100.

## Decision rule (fixed before launch)

| Result | Next |
|---|---|
| Evaluate PASS (scored file written) | Science step s30 applies s27's sealed tolerance rule to run9, scores s29's predictions, and designs the main comparison or the next test. |
| Evaluate FAIL `infra` at `comparison-users` | The blind reader's fixed-phrase count names the step; a harness-script cause goes to a science step; a mechanism cause is reproduced on a public shakedown run before any relaunch. |
| Any receipt suggesting an isolation failure | No relaunch; public reproduction first. |
| A model refusal halts a stage | Report to the owner; no relaunch. |
| Any other FAIL or VOID | Science step s30 assesses it; a failed fixture run stays failed. |
| Infra failure at the first box command | One unchanged relaunch. |

## Predictions

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.85 |
| 2 | Reproduce PASS | 0.80 |
| 3 | `comparison-users` passes (given evaluate starts) | 0.75 |
| 4 | Evaluate PASS, scored file written | 0.55 |
| 5 | Every evaluate box command rc 0 and none timed out (given evaluate starts) | 0.55 |
| 6 | Box type H100 | 0.45 |
| 7 | More than 13 invocations run (given `comparison-users` passes) | 0.70 |
| 8 | The evaluate stage's wall within 300 s of `budget_s` (the budget is spent before the design is done; given `comparison-users` passes) | 0.45 |
| 9 | The next science step reports at least some margins defensible from run9 | 0.40 |
| 10 | Pipeline wall under 4.5 h | 0.55 |
| 11 | Run box USD under 10 | 0.65 |
| 12 | Run box USD under 19.74 (the cap) | 0.95 |
| 13 | Any stage halted by a model refusal | 0.05 |
| 14 | blind-02 ledger after the run under USD 30 | 0.90 |
