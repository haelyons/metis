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

## Outcome (added after the run; the sections above are unchanged since the seal 4e6f3d9c)

run7 (pushed ecfb42ff): no capacity for H100 or A100; `gpu_1x_a10` (us-east-1, USD 1.29/h), pipeline wall 13,501 s, run box USD 4.84; ledger USD 6.64 of 100. Intake PASS (144 s, Codex), reproduce PASS (662 s, Codex; setup rc 0 at 156 s first attempt, anchors rc 0 at 185 s, 0 of 0 published anchors, freeze 25 s), profile to implement SKIPPED, evaluate PASS (12,695 s). Evaluate receipts: upload 24 s, `comparison-users` rc 0 at 49 s, versions 44 s, then 13 invocations (every `comparison-job` and `comparison` rc 0, none timed out): `comparison-job` 23 to 31 s, `comparison` 945 to 989 s for the first 12 and 732 s for the last, then `comparison-private-remove` rc 0. The design asked for 4 arms, 4 inputs and 6 replicates, so 13 invocations is a small fraction of it: the evaluate budget (12,600 s) ran out at about 960 s per invocation on the A10. 14 fetched files over 95 MB left uncommitted; evaluate outputs 11.6 GB fetched.

| # | P | Outcome | Brier |
|---|---|---|---|
| 1 | 0.85 | yes | 0.0225 |
| 2 | 0.75 | yes | 0.0625 |
| 3 | 0.90 | yes | 0.0100 |
| 4 | 0.85 | yes | 0.0225 |
| 5 | 0.60 | yes | 0.1600 |
| 6 | 0.40 | not visible to the operator (invocation statuses are in files the operator does not read) | — |
| 7 | 0.45 | not visible to the operator (scored totals) | — |
| 8 | 0.80 | not visible to the operator (the parts' own walls); `comparison-job` receipts alone median 24 s against run20's 8 s | — |
| 9 | 0.75 | yes | 0.0625 |
| 10 | 0.50 | no (3.75 h) | 0.2500 |
| 11 | 0.55 | yes | 0.2025 |
| 12 | 0.95 | yes | 0.0025 |
| 13 | 0.05 | no | 0.0025 |
| 14 | 0.90 | yes | 0.0100 |

Mean Brier 0.074 over 11 resolved. Decision row: evaluate PASS, so science step s28 reads the fixture results, applies s27's sealed tolerance rule and scores s27's predictions. The operator flags for s28 that the run covered about 13 invocations of the design and ran on an A10, not the H100 the launcher tries first.
