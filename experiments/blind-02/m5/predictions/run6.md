# blind-02 run6 predictions: s04's calibration rerun with the brief readable by the Claude understudy (operator, metadata only; sealed before launch)

Operator exposure as recorded in `run1.md`: the operator is not blind to this experiment's brief; these are not blind predictions. The operator has not read steps s05 or s06, the calibration request or their predictions.

## Design

run5 (s04's calibration) stopped at intake in 15 s on the Claude understudy (Codex at its usage limit until 2026-11-07 23:30 UTC). Science step s05 (Opus fallback, ae75ba3f) found `intake_failure_cause` no_file_access and stopped with `contract_gap`. The operator located the mechanism without reading blind files: `dut/pipeline/idea/wf.js:128` gives a Claude-family agent `--add-dir` only for the work folder, `ARGS.cwd` and `ARGS.add_dirs`; a live check on public scratch files returned DENIED outside those folders and read the file once its folder was added. `new_run.py --brief-from` now copies the brief into `<run_root>/brief/` and passes that folder in `args.add_dirs` (an existing wf.js input; no pipeline change; ops 437be48f). Science step s06 (Opus fallback, 8ac60efe): `s05_gap_status` closed_by_add_dirs, `same_calibration_as_s04` yes_unchanged (brief sha256 identical to s04's, 23101d088a85...), `next_target` runtime_cost, projected under USD 5, `decision_value` medium, `candidates_kept` two, `contract_gaps` two_or_more (blocking both), `narrowing` none; 14 agent predictions sealed.

Run: `new_run.py .../m5/run6 --brief-from=s06 --stop-after-reproduce`, `retry53.sh` (USD 20 cap). Intake, harness and repairs run on Claude Opus (m5's understudy for those roles) while Codex is unavailable.

## Decision rule (fixed before launch)

| Result | Next |
|---|---|
| Reproduce PASS | Science step s07 reads the measurement, scores s06's predictions and chooses the next test or stops. |
| Intake FAIL again with no file access | The fix did not work: no relaunch; the operator diagnoses from code and a public test before anything else. |
| A model refusal halts a stage | Report to the owner; no relaunch. |
| Any other FAIL or VOID | Science step s07 assesses it; a failed calibration stays failed. |
| Infra failure at the first box command | One unchanged relaunch. |

## Predictions

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.75 |
| 2 | Intake answered by the Claude family | 0.90 |
| 3 | Intake `data` available | 0.75 |
| 4 | Setup passes within its repairs | 0.60 |
| 5 | Reproduce PASS | 0.55 |
| 6 | Profile SKIPPED, and every stage after it SKIPPED | 0.97 |
| 7 | The first box command gets a receipt with an integer rc (given 1) | 0.92 |
| 8 | No ceiling timeout and no infrastructure failure | 0.85 |
| 9 | Every receipt is fetched (given at least one receipt) | 0.90 |
| 10 | The reproduce-freeze receipt's wall under 600 s (given a freeze receipt) | 0.85 |
| 11 | Pipeline wall under 1.5 h | 0.55 |
| 12 | Run box USD under 5 | 0.70 |
| 13 | Run box USD under 19.74 (the cap) | 0.97 |
| 14 | Any stage halted by a model refusal | 0.08 |

## Outcome (added after the run; the sections above are unchanged since the seal cdd52351)

run6 (pushed 4b5e49a9): `gpu_1x_h100_pcie` (us-west-3), pipeline wall 1,496 s, run box USD 1.37. Intake PASS (205 s, Claude): `data` available, `size` tiny, `stock_environment` true, `licence` unknown, `anchors_count` 0. Reproduce PASS (1,290 s, Claude): setup rc 0 at 77 s on the first attempt, anchors rc 0 at 749 s (0 of 0 published anchors), reproduce-freeze rc 0 at 37 s, every receipt fetched, `stock_verified` true, 257 GPU-seconds (run4 recorded 0 on its own calibration request). Fetched reproduce outputs 1,861 MB in 6,272 files. The add_dirs fix worked: the Claude intake read the brief.

| # | P | Outcome | Brier |
|---|---|---|---|
| 1 | 0.75 | yes | 0.0625 |
| 2 | 0.90 | yes | 0.0100 |
| 3 | 0.75 | yes | 0.0625 |
| 4 | 0.60 | yes (first attempt) | 0.1600 |
| 5 | 0.55 | yes | 0.2025 |
| 6 | 0.97 | yes | 0.0009 |
| 7 | 0.92 | yes | 0.0064 |
| 8 | 0.85 | yes | 0.0225 |
| 9 | 0.90 | yes | 0.0100 |
| 10 | 0.85 | yes (37 s) | 0.0225 |
| 11 | 0.55 | yes (1,496 s) | 0.2025 |
| 12 | 0.70 | yes | 0.0900 |
| 13 | 0.97 | yes | 0.0009 |
| 14 | 0.08 | no | 0.0064 |

Mean Brier 0.061 over 14. Decision row: reproduce PASS, so science step s07 reads the measurement.
