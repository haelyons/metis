
## Step s06 (re-decision after an operator infrastructure finding; no network)
Your step folder is `experiments/blind-02/science/s06/`. Read `science/s01/` to `science/s05/` first.

s05 found that run5's intake failed because the agent had no file access (`intake_failure_cause` no_file_access) and stopped the route with `contract_gap`. The operator has since located the mechanism, from code and a live test, without reading any blind file:
- `dut/pipeline/idea/wf.js:128` (`callModel`): a Claude-family agent gets `--add-dir` only for the run's work folder (`ARGS.base`), `ARGS.cwd` and every folder in `ARGS.add_dirs`. With `--restricted --permission-mode dontAsk`, the Claude CLI denies reads outside those folders and its working folder. Codex reads anywhere, which is why run3 and run4 (Codex intake) could read a brief in `science/`, and run5 (Claude intake, Codex at its usage limit until 2026-11-07 23:30 UTC) could not.
- Live check on public scratch files (claude haiku, the same flags): reading a file outside the add-dir folders returned DENIED; with that file's folder passed as `--add-dir`, it read the file.
- `args.add_dirs` is an existing input of `wf.js`. The operator's `new_run.py --brief-from=sNN` now copies the step's brief into `<run_root>/brief/` and passes that folder in `args.add_dirs`, so a Claude understudy can read it. No pipeline code changed.

Decide again with this in hand. Is s04's calibration still the most informative next test? If so, choose it again (`m5`, copying s04's brief byte for byte into this folder unless a change is justified, and say what changed), seal fresh predictions for it, and note that intake, harness and repairs will run on Claude Opus until Codex resets. If not, choose another test or stop with the right reason. Also say whether s05's contract gap still stands as a gap, or is closed by this, and update the final contract gap list in `ASSESSMENT.md` (file, section, what it cannot express, which part of the seed's question it blocks, smallest change).

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"s05_gap_status"`: `"closed_by_add_dirs"`, `"still_open"`, `"other"`
- `"same_calibration_as_s04"`: `"yes_unchanged"`, `"yes_revised"`, `"no"`, `"not_applicable"`
- `"next_action"`: `"m5"`, `"measure"`, `"tree"`, `"stop"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"contract_gap"`, `"needs_owner"`, `"limits"`
- `"next_target"`: `"none"`, `"runtime_cost"`, `"quality_metric"`, `"equivalence"`, `"scaling"`, `"other"`
- `"next_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"decision_value"`: `"high"`, `"medium"`, `"low"`, `"none"`
- `"candidates_kept"`: `"none"`, `"one"`, `"two"`, `"three_or_more"`
- `"contract_gaps"`: `"none"`, `"one"`, `"two_or_more"`
- `"gap_blocks"`: `"none"`, `"calibration"`, `"final_experiment_only"`, `"both"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

s05 sealed no predictions, so write `outcomes.json` as `{"items": []}`. If `next_action` is `stop`, `NEXT.json` carries the same reason. No other keys and no free text. Finish within 30 minutes.
