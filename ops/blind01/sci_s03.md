
## Step s03 (after the calibration run; no network)
Your step folder is `experiments/blind-02/science/s03/`. Read `science/s01/` and `science/s02/` first. The calibration run s02 chose is `experiments/blind-02/m5/run3/` (brief `science/s02/` as named in its NEXT.json; records: `args.json`, `pipeline.log`, `control/` receipts, `agent/intake/`, `agent/harness/`, `agent/results/reproduce/` logs and outputs, `agent/wf/` model calls, `operator/OPERATOR_TAKEAWAY.md`). It stopped after reproduce by design (profile stubbed SKIPPED). Operator metadata on it: intake FAILED after 143 s (Codex): found true, data partial, licence unknown, licence_basis none, anchors_count 0, blockers data_unavailable. run1 and run2 intake judged the same materials available (on the seed plus the materials addendum, without your calibration request). Every later stage was SKIPPED; no box command ran; box USD 0.13. So the calibration did not run. Before anything else, establish from run3's intake files and model call (and by comparing them with run2's intake files) exactly which data item intake judged unavailable or partial, and why: whether your calibration request asked for data, a case or a configuration outside the materials the addendum pins, whether intake misread available materials (judgement variance), or whether a source was unreachable at the time. Then answer A to F with that in hand (A becomes: what the run did instead, and why). A relaunch is justified only with a stated cause; a revised brief must change only what the cause requires, and you must say what changed.

Answer in `ASSESSMENT.md`, in this order:
A. What the calibration measured: the quantity s02 asked for, its measured value with unit and spread (quote the log lines and files), the configuration, case and box, and whether the run measured what the calibration request asked (or something narrower or different; say exactly how intake and the harness interpreted the request).
B. What it supports and what it does not. Compare the measured value with the card's GUESS value and its refutation band, and with s02's predictions (also as `outcomes.json`). A failed or uninformative calibration stays recorded as such.
C. Which candidates the result keeps, drops or changes, and why, against the decision rule s02 stated before the run.
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

If `next_action` is `stop`, `NEXT.json` carries the same reason. If it is `m5`, write the brief as s02 did (the seed's exact bytes, the materials addendum's section unchanged, then one section headed `## Calibration request (science step s03)`). No other keys and no free text. Finish within 40 minutes.
