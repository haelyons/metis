
## Step s07 (after the calibration run run6; no network)
Your step folder is `experiments/blind-02/science/s07/`. Read `science/s01/` to `science/s06/` first. The calibration run s06 chose (s04's calibration request, unchanged) is `experiments/blind-02/m5/run6/` (brief `science/s06/` as named in its NEXT.json; earlier calibration runs: run3 (failed at intake), run4 (s03's) and later ones named in the earlier steps; records: `args.json`, `pipeline.log`, `control/` receipts, `agent/intake/`, `agent/harness/`, `agent/results/reproduce/` logs and outputs, `agent/wf/` model calls, `operator/OPERATOR_TAKEAWAY.md`). It stopped after reproduce by design (profile stubbed SKIPPED). Operator metadata on it: intake PASS in 205 s on Claude Opus (Codex at its usage limit; the brief was readable through args.add_dirs): data available, size tiny, stock_environment true, licence unknown, anchors_count 0. Reproduce PASS in 1,290 s on Claude: setup rc 0 at 77 s on the first attempt, anchors script rc 0 at 749 s (0 of 0 published anchors), reproduce-freeze 37 s, every receipt fetched, stock_verified true, 257 GPU-seconds (run4, on s03's request, recorded 0). Fetched reproduce outputs 1,861 MB in 6,272 files. Box gpu_1x_h100_pcie, USD 1.37 in all. Calibration runs so far: run3 (s02, intake FAIL, USD 0.13), run4 (s03, PASS, USD 0.81), run5 (s04, intake FAIL on file access, USD 0.01), run6 (s04's request via s06, PASS, USD 1.37). The harness and intake for run6 were written by Claude Opus, for run4 by Codex: say whether that difference affects comparability.

Answer in `ASSESSMENT.md`, in this order:
A. What the calibration measured: the quantity s06 asked for, its measured value with unit and spread (quote the log lines and files), the configuration, case and box, and whether the run measured what the calibration request asked (or something narrower or different; say exactly how intake and the harness interpreted the request).
B. What it supports and what it does not. Compare the measured value with the card's GUESS value and its refutation band, and with s06's predictions (also as `outcomes.json`). A failed or uninformative calibration stays recorded as such.
C. Which candidates the result keeps, drops or changes, and why, against the decision rule s06 stated before the run.
D. The next test, if one is justified: the single most informative measurement now (what, where, cost, what each result decides), or stop. Stop with `no_justified_test` when no remaining test would change which candidate goes forward; with `contract_gap` when the next informative comparison is one no existing mechanism can express (name the gap as file, section and what is missing); with `needs_owner` when a decision only the owner can make blocks the next step (state the decision and the options); with `limits` when the next justified test cannot fit the limits. Calibration is done when the promising cards' load-bearing inputs are measured well enough that another measurement would not change which candidate goes forward: then stop, with `needs_owner` if a card's full experiment is ready and needs the owner's approval (state its projected cost, box hours and what it would decide), or `contract_gap` if it cannot run on any existing mechanism. List every calibration run so far with its cost.
E. Contract gaps, as a final list for the owner: each with file, section, what it cannot express, which part of the seed's question it blocks, and the smallest change that would close it.
F. Narrowing: unchanged, or exactly what changed.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"intake_failure_cause"`: `"refusal"`, `"no_file_access"`, `"judged_unreachable"`, `"other"`, `"not_applicable"`
- `"calibration_ran"`: `"as_requested"`, `"narrower_than_requested"`, `"different_from_requested"`, `"did_not_run"`
- `"measured_vs_guess"`: `"within_band"`, `"outside_band_higher"`, `"outside_band_lower"`, `"not_comparable"`, `"not_measured"`
- `"result_informative"`: `"yes"`, `"partly"`, `"no"`
- `"candidates_kept"`: `"none"`, `"one"`, `"two"`, `"three_or_more"`
- `"candidates_dropped"`: `"none"`, `"one"`, `"two"`, `"three_or_more"`
- `"next_action"`: `"m5"`, `"measure"`, `"tree"`, `"stop"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"contract_gap"`, `"needs_owner"`, `"limits"`
- `"next_target"`: `"none"`, `"runtime_cost"`, `"quality_metric"`, `"equivalence"`, `"scaling"`, `"other"`
- `"next_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"decision_value"`: `"high"`, `"medium"`, `"low"`, `"none"`
- `"contract_gaps"`: `"none"`, `"one"`, `"two_or_more"`
- `"gap_blocks"`: `"none"`, `"calibration"`, `"final_experiment_only"`, `"both"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

If `next_action` is `stop`, `NEXT.json` carries the same reason. If it is `m5`, write the brief as s02 did (the seed's exact bytes, the materials addendum's section unchanged, then one section headed `## Calibration request (science step s07)`). No other keys and no free text. Finish within 40 minutes.
