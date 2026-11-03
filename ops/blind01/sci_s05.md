
## Step s05 (after the calibration run run5; no network)
Your step folder is `experiments/blind-02/science/s05/`. Read `science/s01/` to `science/s04/` first. The calibration run s04 chose is `experiments/blind-02/m5/run5/` (brief `science/s04/` as named in its NEXT.json; earlier calibration runs: run3 (failed at intake), run4 (s03's) and later ones named in the earlier steps; records: `args.json`, `pipeline.log`, `control/` receipts, `agent/intake/`, `agent/harness/`, `agent/results/reproduce/` logs and outputs, `agent/wf/` model calls, `operator/OPERATOR_TAKEAWAY.md`). It stopped after reproduce by design (profile stubbed SKIPPED). Operator metadata on it: intake FAILED after 15 s on the Claude family (Codex is at its usage limit until 2026-11-07 23:30 UTC, so m5 routed intake to its Claude Opus understudy): found false, data unknown, licence unknown, licence_basis unreachable, blockers data_unavailable; recorded tokens 6 in and 1,167 out, which suggests the agent replied without reading the materials. Every later stage SKIPPED; no box command ran; box USD 0.01. The calibration did not run. First establish, from run5's intake call (its prompt, reply and transcript under `agent/wf/`) and by comparing it with run4's Codex intake on the same kind of brief: did the agent decline or refuse, lack access to the files it needed (for example a path outside its isolated view), judge the materials unreachable, or something else? Record it as `intake_failure_cause`. The operator's sealed rule: if the reply was a refusal or decline, there is no relaunch and the route reports to the owner (`next_action` stop, `stop_reason` needs_owner). If the cause is a pipeline defect (for example file access), name it as a contract gap with file and section, and stop with `contract_gap` unless an existing mechanism avoids it. Then answer A to F with that in hand (A becomes: what the run did instead, and why).

Answer in `ASSESSMENT.md`, in this order:
A. What the calibration measured: the quantity s04 asked for, its measured value with unit and spread (quote the log lines and files), the configuration, case and box, and whether the run measured what the calibration request asked (or something narrower or different; say exactly how intake and the harness interpreted the request).
B. What it supports and what it does not. Compare the measured value with the card's GUESS value and its refutation band, and with s04's predictions (also as `outcomes.json`). A failed or uninformative calibration stays recorded as such.
C. Which candidates the result keeps, drops or changes, and why, against the decision rule s04 stated before the run.
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

If `next_action` is `stop`, `NEXT.json` carries the same reason. If it is `m5`, write the brief as s02 did (the seed's exact bytes, the materials addendum's section unchanged, then one section headed `## Calibration request (science step s05)`). No other keys and no free text. Finish within 40 minutes.
