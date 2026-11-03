
## Step s11 (choose the fixes for the G2 contract from a fixed list; no network; no new test)
Your step folder is `experiments/blind-02/science/s11/`. Read `science/s09/` and `science/s10/` first. s10 found the operator's G2 contract (card calibration, U54) `partial`: missing `predictions`; problems `band_rule_unfit`, `write_back_unfit`, `leaks_or_biases`. The operator cannot read your prose, and revises the contract once, so this step names the fixes in a fixed vocabulary. Choose, for each finding, every fix it needs (one or more); choose `other` only when no listed fix serves, and then explain it in ASSESSMENT.md for the owner.

Write `FIXES.json`: exactly `{"items": [...]}` with exactly these four items in this order, each exactly `{"for": ..., "fix": [...]}` (fix codes non-empty, no duplicates):
- `{"for": "predictions", ...}`: `"seal_record_before_box"` (the pipeline hashes the full card record into a seal before any box command, and the score names that seal); `"return_in_scored"` (the scored file and the resolved copy carry the record's `predictions` unchanged); `"judge_decision_rule"` (the run must also evaluate the card's decision rule on the measured inputs); `"hide_from_agents"` (no agent of the run sees the predictions); `"other"`.
- `{"for": "band_rule_unfit", ...}`: `"sign_aware"` (a negative value gets the band `[value*k, value/k]`); `"absolute_band_field"` (an input whose value is zero, a small count or otherwise unfit for a multiplicative band needs an absolute band, from a new per-input field the card must supply); `"bounded_range"` (a fraction, probability or other bounded quantity: the band is clipped to its range, from a new per-input field `range`); `"gate_decides"` (the card's phase gate decides the input; the band is only reported); `"noise_band"` (the band comes from measured run-to-run spread, so the run needs replicates); `"other"`.
- `{"for": "write_back_unfit", ...}`: `"as_plan_numbers"` (the write-back produces MEASURED plan numbers, with basis MEASURED, the value and command/output/machine provenance, so the card can be re-judged); `"rejudge_card"` (the card's plan and cost must be re-judged with the measured values, not only marked); `"all_runs_not_latest"` (the state comes from all runs, for example any refuting run refutes, not from the latest entry); `"record_run_identity"` (entries carry box type, pipeline commit and run date); `"states_unfit"` (the `calibrated`/`refuted` states are not what later steps need); `"other"`.
- `{"for": "leaks_or_biases", ...}`: `"hide_value"` (no agent of the run sees the card's value, band or gate threshold: agents get only id, name, unit, measuring phase and protocol); `"hide_predictions"`; `"hide_anchor_value"` (agents do not see the card anchor's published value either); `"extraction_rule_before_run"` (how each input is read from the output is fixed before the run and applied by the pipeline, not by the harness); `"other"`.

Write `ASSESSMENT.md` for the owner (why each fix; what any `other` needs), `NARROWING.md` ("No narrowing." with the reason, or what changed), `PREDICTIONS.md` ("No test; no predictions."), `predictions.json` `{"items": []}`, `outcomes.json` `{"items": []}` (s10 sealed none), and `NEXT.json` `{"action": "stop", "reason": "contract_gap"}`. FIXES.json holds no free text and no seed content.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"other_count"`: `"none"`, `"one"`, `"two_or_more"` (items whose fixes include `other`)
- `"needs_tree_change"`: `"yes"`, `"no"` (whether your fixes need a new field in the tree's card records)
- `"next_action"`: `"stop"`
- `"stop_reason"`: `"contract_gap"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`

No other keys and no free text. Finish within 30 minutes.
