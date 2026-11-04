# blind-02 run7 predictions: s27's fixture run, a sealed comparison (operator, metadata only; sealed before launch)

Operator exposure as recorded in `run1.md`: the operator is not blind to this experiment's brief; these are not blind predictions. The operator has not read steps s07 to s27, the fixture design, the comparison request or their predictions.

## Design

First blind run of the sealed comparison (m5 U57/U58, code 65cd5d59: the third fix round merged after the narrow Codex check review57d, `VERDICT: clean`). Isolation was demonstrated on a box by the public probe shakedown-m5 run20 (code e3ebd33c; 0 leaks, 0 failed controls over 30 hostile parts; about 30 s per invocation outside the parts' walls); the third fix round (allow lists, cleanup order, exemption pattern) was checked by tests and Codex, not on a box. Science step s27 (Opus, 43e26575): `next_action` m5, `error_budget_feasible` partly, `budget_basis` fixtures_and_analysis, `fixtures_disjoint` yes, `self_agreement_arms` two_or_more, `margins_covered` all, `tolerance_rule_sealed` yes, `fixture_comparisons` exact_only, `evaluator_in_fixture_run` yes, projected USD 5 to 20 and 1 to 3 h, `main_runs_fit_after` yes, `narrowing` none; 16 agent predictions sealed. Its design, as the operator's checks print it: 4 arms, 4 inputs, 12 comparisons, 6 replicates, evaluate `budget_s` 12600; no sealed number in the agents' view or the brief.

Run: `new_run.py .../m5/run7 --brief-from=s27` (no other flags), `retry53.sh` (box types at most USD 3.29/h, box `--max-hours 6`). blind-02 ledger before launch: USD 1.67 of 100.

## Decision rule (fixed before launch)

| Result | Next |
|---|---|
| Evaluate PASS (scored file written) | Science step s28 reads the fixture results, applies s27's sealed tolerance rule, scores s27's predictions and designs the main comparison or stops. |
| Evaluate FAIL `infra` at `comparison-users` or any receipt suggesting an isolation failure | No relaunch; the operator reproduces it on a public shakedown run first. |
| A model refusal halts a stage | Report to the owner; no relaunch. |
| Any other FAIL or VOID | Science step s28 assesses it; a failed fixture run stays failed. |
| Infra failure at the first box command | One unchanged relaunch. |

## Predictions

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.85 |
| 2 | Reproduce PASS | 0.75 |
| 3 | Profile, seal, propose and implement SKIPPED; evaluate runs in comparison mode (given reproduce PASS) | 0.90 |
| 4 | `comparison-users` passes (given evaluate starts) | 0.85 |
| 5 | Evaluate PASS, scored file written | 0.60 |
| 6 | Every invocation `ok`, none invalid, failed or timed out (given evaluate PASS) | 0.40 |
| 7 | No comparison `void` in the scored totals (given evaluate PASS) | 0.45 |
| 8 | Median evaluate-stage overhead per invocation outside the parts' walls between 20 and 60 s (given at least one invocation) | 0.80 |
| 9 | No ceiling timeout and no infrastructure failure | 0.75 |
| 10 | Pipeline wall under 3 h | 0.50 |
| 11 | Run box USD under 10 | 0.55 |
| 12 | Run box USD under 19.74 (the cap) | 0.95 |
| 13 | Any stage halted by a model refusal | 0.05 |
| 14 | blind-02 ledger after the run under USD 25 | 0.90 |
