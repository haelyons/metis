# blind-02 run5 predictions: second calibration, chosen by science step s04 (operator, metadata only; sealed before launch)

Operator exposure as recorded in `run1.md`: the operator is not blind to this experiment's brief; these are not blind predictions. The operator has not read step s04's assessment, its calibration request or its predictions.

## Design

run4 (s03's calibration) passed reproduce for USD 0.81 (`run4.md`). Science step s04 (committed e7acd7dd) ran on the Claude Opus fallback: Codex is at its usage limit until 2026-11-07 23:30 UTC (the step's Codex call failed on it, and a ping confirms). What the operator sees: `calibration_ran` as_requested, `measured_vs_guess` outside_band_lower (the card's GUESS is refuted, on the low side), `result_informative` yes, `candidates_kept` two, `candidates_dropped` none, `next_target` runtime_cost, projected under USD 5, `decision_value` medium, `contract_gaps` two_or_more (blocking both), `narrowing` none; 12 agent predictions sealed; s03's predictions scored Brier 0.165 (6 resolved, 4 true). Brief (bytes only): seed exact, materials section unchanged, one calibration section (13,825 bytes).

Run: `new_run.py .../m5/run5 --brief-from=s04 --stop-after-reproduce`, `retry53.sh` (USD 20 cap). With Codex unavailable, m5's routing sends intake, harness and the repairs to Claude Opus (the configured understudy for those roles).

## Decision rule (fixed before launch)

| Result | Next |
|---|---|
| Reproduce PASS | Science step s05 reads the measurement, scores s04's predictions and chooses the next test or stops. |
| Intake or reproduce FAIL or VOID | Science step s05 assesses it; a failed calibration stays failed; no relaunch without a stated cause. |
| A model refusal halts a stage | Report to the owner (Opus is the only working family for authoring roles until Codex resets); no relaunch. |
| Infra failure at the first box command | One unchanged relaunch. |

## Predictions

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.75 |
| 2 | Intake answered by the Claude family | 0.90 |
| 3 | Setup passes within its repairs | 0.65 |
| 4 | Reproduce PASS | 0.60 |
| 5 | Profile SKIPPED, and every stage after it SKIPPED | 0.97 |
| 6 | The first box command gets a receipt with an integer rc (given 1) | 0.92 |
| 7 | No ceiling timeout and no infrastructure failure | 0.85 |
| 8 | Every receipt is fetched (given at least one receipt) | 0.90 |
| 9 | The reproduce-freeze receipt's wall under 600 s (given a freeze receipt) | 0.85 |
| 10 | Pipeline wall under 1.5 h | 0.60 |
| 11 | Run box USD under 5 | 0.70 |
| 12 | Run box USD under 19.74 (the cap) | 0.97 |
| 13 | Any stage halted by a model refusal | 0.10 |
