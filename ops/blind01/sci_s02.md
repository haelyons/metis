
## Step s02 (after the tree run; no network)
Your step folder is `experiments/blind-02/science/s02/`. Read `science/s01/` first (your earlier assessment, narrowing, predictions). The tree run s01 chose is `experiments/blind-02/20261103-0124-tree/` (its `RUN.md`, `args.json`, `out/result.json`, `out/RESULT.md`, `out/status.json`, `out/run.json`, `out/UNDERSTUDY.md` if present, and `out/agents/` for each call's prompt and reply, including the producers' plans and the dramaturg's findings). Operator metadata on it: finished in 21 min; 51 calls, all ok, no refusals; 6 calibration records: 2 no_unmeasured_input, 1 calibration_required (one GUESS input, measured in a 3 h phase, spend through it USD 19.74, plan at the USD 100 budget), 2 rejected, 1 not_judged (halted). Every call the config routes to OpenCode (the three-model critic panel and the second dramaturg) failed and was answered by Codex instead (25 substitutions), so the judges ran on the producers' own model family: weigh the PASS and REJECT decisions accordingly. One transcript (the widener's codex-1.jsonl) was kept out of the commit by a secret-pattern scan; it is on disk and you may read it.

Answer in `ASSESSMENT.md`, in this order:
A. What the tree produced: for each pick, which part of the seed's question (your P1..Pn from s01) it addresses, its card's decision (PASS or REJECT) and the reasons the judges gave, its calibration state and the inputs it needs measured. Include halted picks and why they halted.
B. What the tree run supports and what it does not, including negative results (rejected or halted candidates stay recorded as such).
C. The outcomes of your s01 predictions, with evidence (also as `outcomes.json`).
D. Which candidates are promising, and the single most informative next test now: what it measures, on which configuration and case, with which command, what range you expect, and what each possible result would decide (which candidate goes forward or drops). Prefer the cheapest measurement whose result changes the plan.
E. The mechanism for that test, and why: (1) the measure route (`launch.js blind-02 measure --card 20261103-0124-tree --pick <key>`; say what the compiled folder would carry and what it would lose for this test; its execution chain after compiling is not available yet, so choosing it means the operator builds that chain first), or (2) an m5 run with a calibration brief (the brief you write is the run's whole brief: the seed's exact bytes, then the materials addendum's section copied unchanged from `m5/b01_materials/BRIEF_run1.md`, then one section headed `## Calibration request (science step s02)` that states the measurement; the m5 stages then decide the harness and run setup and anchors on a box; `--stop-after-profile` adds the profile and the concurrency probe, about 2 h more on run2's receipts), or (3) another tree run (only if no card can be calibrated as it stands), or (4) stop.
F. Contract gaps: confirm or revise s01's list after seeing the cards; for the chosen test, any gap that would make its result uninformative.
G. Narrowing: a calibration measures part of the question by design; state in `NARROWING.md` exactly which part, and that the seed's question is not narrowed by it (or, if it is, how).

Seal your predictions for the chosen test in `PREDICTIONS.md` and `predictions.json` (for example the measured value's range, whether setup and anchors pass, whether the result keeps or drops each promising candidate).

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"tree_outcome"`: `"complete"`, `"partial"`, `"failed"`
- `"cards_pass"`: `"none"`, `"one"`, `"two"`, `"three_or_more"`
- `"cards_calibration_required"`: `"none"`, `"one"`, `"two"`, `"three_or_more"`
- `"parts_addressed_by_pass_cards"`: `"none"`, `"some"`, `"most"`, `"all"`
- `"promising_candidates"`: `"none"`, `"one"`, `"two"`, `"three_or_more"`
- `"next_action"`: `"measure"`, `"m5"`, `"tree"`, `"stop"`
- `"calibration_target"`: `"none"`, `"runtime_cost"`, `"quality_metric"`, `"equivalence"`, `"scaling"`, `"other"`
- `"calibration_mechanism"`: `"none"`, `"measure_route"`, `"m5_reproduce"`, `"m5_profile"`, `"m5_units_probe"`, `"other"`
- `"calibration_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"calibration_projected_hours"`: `"none"`, `"under_1"`, `"1_to_3"`, `"3_to_6"`
- `"decision_value"`: `"high"`, `"medium"`, `"low"`, `"none"` (would its result change which candidate goes forward)
- `"narrowing"`: `"none"`, `"explicit"`
- `"contract_gaps"`: `"none"`, `"one"`, `"two_or_more"`
- `"gap_blocks"`: `"none"`, `"calibration"`, `"final_experiment_only"`, `"both"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 40 minutes.
