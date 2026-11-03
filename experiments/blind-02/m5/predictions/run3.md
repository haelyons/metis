# blind-02 run3 predictions: calibration run chosen by science step s02 (operator, metadata only; sealed before launch)

Operator exposure as recorded in `run1.md`: the operator is not blind to this experiment's brief; these are not blind predictions. The operator has not read step s02's assessment, its calibration request or its predictions.

## Design

Science step s02 (Codex, committed 6b673d09) assessed tree run `20261103-0124-tree` and chose an m5 calibration run. What the operator sees: `tree_outcome` complete, `cards_pass` three_or_more, `cards_calibration_required` one, `parts_addressed_by_pass_cards` all, `promising_candidates` two, `calibration_target` runtime_cost, `calibration_mechanism` m5_reproduce, projected 1 to 3 h and USD 5 to 20, `decision_value` medium, `contract_gaps` two_or_more blocking both calibration and final experiment, `narrowing` none; 6 agent predictions sealed in the step folder. The brief (checked by bytes, never read) starts with the seed's exact bytes, carries the materials addendum's section unchanged, and adds one section headed "Calibration request (science step s02)" (11,077 bytes).

Run: `new_run.py .../m5/run3 --brief-from=s02 --stop-after-reproduce` (args.stub profile SKIPPED, so the run stops after reproduce; `run_ceiling_s` 19800), launched with `retry53.sh` (box types priced at most USD 3.29/h, box lifetime 6 h enforced by the launcher's watchdog, pipeline timeout 20700 s). Fresh harness. First live run with U53 (incremental fetch through a per-run mirror, merged 91968fec).

## Decision rule (fixed before launch)

| Result | Next |
|---|---|
| Reproduce PASS | Science step s03 reads the measurement, scores its predictions and chooses the next test. |
| Reproduce FAIL or VOID for a cause in the workload or harness | Science step s03 assesses it (a failed calibration stays a failed calibration). |
| Infra failure at the first box command | One unchanged relaunch (as run2 after run1); a second identical failure means the launch-retry unit first. |
| U53 fetch failure (fetch errors in receipts) | Diagnose from metadata; fix only as a unit with its own tests. |

## Predictions

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.85 |
| 2 | Intake `anchors_count` at least 1 (given 1) | 0.50 |
| 3 | Setup passes within its repairs | 0.80 |
| 4 | Reproduce PASS | 0.70 |
| 5 | `anchors_passed` equals `anchors_total` (given 4 and at least one anchor) | 0.60 |
| 6 | Profile SKIPPED, and every stage after it SKIPPED | 0.97 |
| 7 | The first box command gets a receipt with an integer rc | 0.92 |
| 8 | No ceiling timeout and no infrastructure failure | 0.85 |
| 9 | Every receipt is fetched | 0.90 |
| 10 | The reproduce-freeze receipt's wall under 600 s (run2: 1,402 s, fetch-dominated; tests U53) | 0.70 |
| 11 | Pipeline wall under 3 h | 0.60 |
| 12 | Run box USD under 10 | 0.70 |
| 13 | Run box USD under 19.74 (the cap) | 0.97 |

All predictions are read from signatures, receipts and box metadata.
