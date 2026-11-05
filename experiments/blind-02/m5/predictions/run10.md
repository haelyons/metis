# blind-02 run10 predictions: the main comparison, a sealed comparison (operator, metadata only; sealed before launch)

Operator exposure as recorded in `run1.md`: the operator is not blind to this experiment's brief; these are not blind predictions. The operator has not read steps s07 to s33, any design, comparison request, prediction or reader report.

## Design

Calibration closed with run9 (s29's fixture run: all 96 invocations rc 0, about 36 s per invocation outside the parts). Science step s30 (5f8ab834) applied s27's sealed tolerance rule unchanged: `fixture_coverage` full, `tolerance_rule_applied` all_margins, `margins_defensible` all, `uncertainty_kept` none; it chose the main comparison and stopped `needs_owner`, a stop the operator's prompt invited by naming cost as an example. s31 (4e00cc70) classified the decision as `method_choice`, settled by the owner's standing decisions, and designed the main comparison (margins `all_from_s30`, `main_runs_needed` one), refused by the operator's screen (19 sealed-number matches in the visible text). s32 (c13f3889) changed only the visible wording (`match_cause` coincidental_tokens, `sealed_numbers_changed` no, `measurement_changed` no, screen 0); its `outcomes.json` was invalid through the operator's prompt; s33 (9f12391d) copied s32 byte for byte and fixed the bookkeeping. Design as the operator's checks print it: 3 arms, 4 inputs, 10 comparisons, 7 replicates, evaluate `budget_s` 14,400; 0 sealed numbers in the agents' view or the brief; 20 agent predictions sealed (s31, carried unchanged). Projected USD 5 to 20 and 1 to 3 h; fits one allocation on an A10, A100 or H100. Code 65cd5d59.

Run: `new_run.py .../m5/run10 --brief-from=s33` (no other flags), `retry53.sh` (box types at most USD 3.29/h, H100 first; box `--max-hours 6`). blind-02 ledger before launch: USD 11.10 of 100.

## Decision rule (fixed before launch)

| Result | Next |
|---|---|
| Evaluate PASS (scored file written) | Science step s34 reads the scored comparisons, scores s31's predictions and states what the main comparison decides for the seed's question, with the uncertainty kept (none was kept). |
| Evaluate FAIL `infra` at `comparison-users` | The blind reader's fixed-phrase count names the step; a harness-script cause goes to a science step; a mechanism cause is reproduced on a public shakedown run before any relaunch. |
| Any receipt suggesting an isolation failure | No relaunch; public reproduction first. |
| A model refusal halts a stage | Report to the owner; no relaunch. |
| Any other FAIL or VOID | Science step s34 assesses it; a failed main run stays failed and is reported as such. |
| Infra failure at the first box command | One unchanged relaunch. |

## Predictions

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.90 |
| 2 | Reproduce PASS | 0.85 |
| 3 | `comparison-users` passes (given evaluate starts) | 0.85 |
| 4 | Evaluate PASS, scored file written | 0.75 |
| 5 | Every evaluate box command rc 0 and none timed out (given evaluate starts) | 0.65 |
| 6 | At least 84 `comparison` receipts (3 arms x 4 inputs x 7 replicates; given `comparison-users` passes) | 0.70 |
| 7 | Evaluate stage wall under 2 h (given `comparison-users` passes) | 0.55 |
| 8 | Box type H100 | 0.40 |
| 9 | Pipeline wall under 3 h | 0.60 |
| 10 | Run box USD under 10 | 0.75 |
| 11 | Run box USD under 19.74 (the cap) | 0.97 |
| 12 | Any stage halted by a model refusal | 0.03 |
| 13 | blind-02 ledger after the run under USD 25 | 0.90 |
| 14 | Science step s34 reports no failed invocation (given evaluate PASS) | 0.60 |

## Outcome (added after the run; the sections above are unchanged since the seal 677dc1d6)

run10 (pushed 9a0a8130): no H100 capacity; `gpu_1x_a100_sxm4` (us-east-1, USD 1.99/h), pipeline wall 4,964 s, run box USD 2.74; ledger USD 14.06 of 100. Intake PASS (139 s, Codex), reproduce PASS (395 s; setup rc 0 at 145 s on the first attempt, anchors rc 0, 0 of 0, freeze rc 0), profile to implement SKIPPED, evaluate PASS (4,430 s against `budget_s` 14,400; 647.6 GPU-seconds). Evaluate receipts: `comparison-users` rc 0 at 29 s (no fixed fail phrase in its log), versions rc 0, then 96 invocations, every `comparison-job` (median 7 s) and `comparison` (median 30 s, 29 to 52 s) rc 0 and none timed out, then `comparison-private-remove` rc 0.

| # | P | Outcome | Brier |
|---|---|---|---|
| 1 | 0.90 | yes | 0.0100 |
| 2 | 0.85 | yes | 0.0225 |
| 3 | 0.85 | yes | 0.0225 |
| 4 | 0.75 | yes | 0.0625 |
| 5 | 0.65 | yes | 0.1225 |
| 6 | 0.70 | yes (96) | 0.0900 |
| 7 | 0.55 | yes (1.23 h) | 0.2025 |
| 8 | 0.40 | no (A100) | 0.1600 |
| 9 | 0.60 | yes (1.38 h) | 0.1600 |
| 10 | 0.75 | yes | 0.0625 |
| 11 | 0.97 | yes | 0.0009 |
| 12 | 0.03 | no | 0.0009 |
| 13 | 0.90 | yes | 0.0100 |
| 14 | 0.60 | pending (science step s34) | — |

Mean Brier 0.071 over 13 resolved. Decision row: evaluate PASS, so science step s34 reads the scored comparisons, scores s31's predictions and states what the main comparison decides.
