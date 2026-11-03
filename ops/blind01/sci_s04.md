
## Step s04 (after the calibration relaunch; no network)
Your step folder is `experiments/blind-02/science/s04/`. Read `science/s01/` to `science/s03/` first. The calibration run s03 chose is `experiments/blind-02/m5/run4/` (brief `science/s03/` as named in its NEXT.json; the earlier attempt, run3, failed at intake; records: `args.json`, `pipeline.log`, `control/` receipts, `agent/intake/`, `agent/harness/`, `agent/results/reproduce/` logs and outputs, `agent/wf/` model calls, `operator/OPERATOR_TAKEAWAY.md`). It stopped after reproduce by design (profile stubbed SKIPPED). Operator metadata on it: intake PASS in 121 s (Codex; data available, stock_environment true, licence unknown, anchors_count 0); reproduce PASS in 764 s: setup rc 255 at 154 s, then after one repair rc 0 at 32 s; anchors script rc 0 at 121 s (0 of 0 published anchors); reproduce-freeze 10 s; every receipt fetched; stock_verified true; reproduce recorded 0 GPU-seconds (run2's reproduce recorded 49.6); fetched reproduce outputs 340 MB in 600 files; box gpu_1x_h100_pcie, USD 0.81 in all. Establish whether the measured command ran the workload your calibration request named, at the scale it named, on the GPU if it should have (zero GPU-seconds may mean a CPU-only path, a reduced case, or missing telemetry), and what the setup's first rc 255 was.

Answer in `ASSESSMENT.md`, in this order:
A. What the calibration measured: the quantity s03 asked for, its measured value with unit and spread (quote the log lines and files), the configuration, case and box, and whether the run measured what the calibration request asked (or something narrower or different; say exactly how intake and the harness interpreted the request).
B. What it supports and what it does not. Compare the measured value with the card's GUESS value and its refutation band, and with s03's predictions (also as `outcomes.json`). A failed or uninformative calibration stays recorded as such.
C. Which candidates the result keeps, drops or changes, and why, against the decision rule s03 stated before the run.
D. The next test, if one is justified: the single most informative measurement now (what, where, cost, what each result decides), or stop. Stop with `no_justified_test` when no remaining test would change which candidate goes forward; with `contract_gap` when the next informative comparison is one no existing mechanism can express (name the gap as file, section and what is missing); with `needs_owner` when a decision only the owner can make blocks the next step (state the decision and the options); with `limits` when the next justified test cannot fit the limits.
E. Contract gaps, as a final list for the owner: each with file, section, what it cannot express, which part of the seed's question it blocks, and the smallest change that would close it.
F. Narrowing: unchanged, or exactly what changed.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
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

If `next_action` is `stop`, `NEXT.json` carries the same reason. If it is `m5`, write the brief as s02 did (the seed's exact bytes, the materials addendum's section unchanged, then one section headed `## Calibration request (science step s04)`). No other keys and no free text. Finish within 40 minutes.
