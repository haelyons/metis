# blind-02 run4 predictions: relaunch of the calibration with science step s03's revised brief (operator, metadata only; sealed before launch)

Operator exposure as recorded in `run1.md`: the operator is not blind to this experiment's brief; these are not blind predictions. The operator has not read step s03's assessment, its diagnosis of run3's intake failure, its calibration request or its predictions.

## Design

run3 (s02's calibration request) stopped at intake: `data` partial, blockers `data_unavailable`, no box command (`run3.md`). Science step s03 (Codex, committed 27609298) diagnosed it and chose to relaunch: `calibration_ran` did_not_run, `result_informative` no, `candidates_kept` two, `candidates_dropped` none, `next_target` runtime_cost, projected USD 5 to 20, `decision_value` medium, `contract_gaps` two_or_more (blocking both), `narrowing` none; 7 agent predictions sealed. Its brief (checked by bytes only): the seed's exact bytes and the materials addendum section identical to s02's brief; the calibration section rewritten (s02 11,075 bytes, s03 27,342 bytes, similarity 0.58). The operator does not know the diagnosed cause; the owner can read it in `science/s03/ASSESSMENT.md`.

Run: `new_run.py .../m5/run4 --brief-from=s03 --stop-after-reproduce`, `retry53.sh` (USD 3.29/h box types at most, 6 h box lifetime, pipeline timeout 20700 s, `run_ceiling_s` 19800). Fresh harness.

## Decision rule (fixed before launch)

| Result | Next |
|---|---|
| Intake FAIL again on `data_unavailable` | No further relaunch on this route: two intake failures on a calibration request. Report to the owner with s03's diagnosis (theirs to read) and the contract gap the science steps list. |
| Intake FAIL on another blocker, or any later stage FAIL or VOID | Science step s04 assesses it; a failed calibration stays failed. |
| Reproduce PASS | Science step s04 reads the measurement, scores s03's predictions and chooses the next test or stops. |
| Infra failure at the first box command | One unchanged relaunch. |

## Predictions

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.65 |
| 2 | Intake `data` available | 0.70 |
| 3 | Setup passes within its repairs | 0.60 |
| 4 | Reproduce PASS | 0.50 |
| 5 | `anchors_passed` equals `anchors_total` (given 4 and at least one anchor) | 0.60 |
| 6 | Profile SKIPPED, and every stage after it SKIPPED | 0.97 |
| 7 | The first box command gets a receipt with an integer rc (given 1) | 0.90 |
| 8 | No ceiling timeout and no infrastructure failure | 0.85 |
| 9 | Every receipt is fetched (given at least one receipt) | 0.90 |
| 10 | The reproduce-freeze receipt's wall under 600 s (given a freeze receipt; tests U53) | 0.70 |
| 11 | Pipeline wall under 3 h | 0.65 |
| 12 | Run box USD under 10 | 0.75 |
| 13 | Run box USD under 19.74 (the cap) | 0.97 |
