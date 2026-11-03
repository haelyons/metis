# blind-02 science step s01: tree run predictions (operator, metadata only; sealed before launch)

Operator exposure as recorded in `run1.md`: the operator is not blind to this experiment's brief; these are not blind predictions. The operator has not read the step's assessment, root question, seed ideas or predictions.

## Design

Owner 2026-11-03: continue within the seed through the tree/card and measure routes, with a content-reading scientific agent choosing each test and the operator metadata-only. Step s01 (Codex, committed 59934a22) chose a tree run. What the operator sees of it: `impression` supported, `run2_workload_finding` workload_measured_and_menu_negative, `question_open` yes, `parts_count` four_or_more, `parts_open` most, `candidates_count` four_or_more, `candidates_tree_expressible` all, `candidates_calibratable_existing` some, `cheapest_measurement_usd` under_5, `contract_gaps` two_or_more, `gap_blocks` both, `gap_location` multiple, `narrowing` none; tree args: 1 fixed root (370 words), 4 seed ideas, `picks_per_branch` 1, `budget_usd` 100; 10 agent predictions sealed in the step folder.

Run: `launch.js blind-02 tree --seed science/s01/tree_args.json --family codex --mode fallback --on-refusal halt` via `~/.cache/blind01/sci_tree.sh 02 s01` (5 h timeout). This is the first tree run on the Codex family; earlier tree runs used OpenCode. The critic panel and second dramaturg stay on OpenCode models by the config's label rules. Expected picks: up to two branch picks (one per branch) plus four seed picks, so up to six calibration records. Read by `tree_read.py` only.

## Decision rule (fixed before launch)

| Result | Next |
|---|---|
| result.json with calibration records | Science step s02 assesses them and chooses the next test. |
| No result.json, or a run error | Diagnose from metadata (call states, families, error flags). One relaunch only if the cause is a usage limit or transport failure; otherwise a reader diagnosis and, if needed, a unit with its own tests. |

## Predictions

| # | Prediction | P |
|---|---|---|
| 1 | The run finishes with a result.json holding a calibration array | 0.75 |
| 2 | Exactly six calibration records | 0.55 |
| 3 | At least one record `calibration_required` (given 1) | 0.55 |
| 4 | At least three records `calibration_required` (given 1) | 0.20 |
| 5 | At least one record `rejected` (given 1) | 0.65 |
| 6 | At least one record `not_judged` (a halted pick; given 1) | 0.40 |
| 7 | Run wall under 2 h | 0.45 |
| 8 | No call ends in state `failed` or `refused` | 0.50 |
| 9 | OpenCode answers at least one call | 0.80 |
| 10 | Recorded `cost_usd` under USD 5 (Codex records 0) | 0.85 |
| 11 | Some `calibration_required` record has an input whose spend through its measuring phase is at most USD 20 (given 3) | 0.70 |
| 12 | Some record's `plan_usd` exceeds the USD 100 budget | 0.15 |
