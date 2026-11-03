
## Step s09 (requirements for closing the gaps, and the state of each part; no network; no new test)
The owner approved closing the contract gaps (2026-11-03) and asked how that leads to completing the science. Your step folder is `experiments/blind-02/science/s09/`. Read `science/s01/` to `science/s08/` first, above all `s08/GAPS.json` and `s08/ASSESSMENT.md`. The operator will write each contract change without reading the seed or any prose, so this step does two things: it turns each gap into requirements in a fixed vocabulary, and it records the state of every part of the question so progress toward completion can be tracked without content. Background the operator can give you: since run6, the operator's wrapper copies the brief into the run folder and passes that folder to Claude agents as an extra readable folder (this is the existing workaround for the access failure in run5).

Write `PARTS.json`: `{"items": [...]}`, one item per part P1..Pn of the question as s01 defined them (or as a later step redefined them), each with exactly these keys:
- `"id"`: `"P1"`, `"P2"`, ... in order.
- `"status"`: `"measured"` (a measurement in run2 or in this route already answers it), `"negative"` (a measured negative result answers it and is preserved), `"narrowed"` (explicitly removed from scope; say so in NARROWING.md), `"open_calibration"` (needs a calibration before the final experiment), `"open_final"` (needs only the final experiment), `"open_no_mechanism"` (needs something none of the gaps G1..Gn would provide).
- `"gaps"`: an array of gap ids from `s08/GAPS.json` that block this part (empty if none), no duplicates.

Write `REQS.json`: `{"items": [...]}`, exactly one item per gap in `s08/GAPS.json` with the same ids in the same order, each with exactly these keys:
- `"id"`: the gap id.
- `"order"`: an integer from 1 to the number of gaps, all distinct: the order you would close them in.
- `"defer"`: `true` when every part can still reach a final answer without closing this gap (an existing workaround suffices), else `false`.
- `"req"`: an object whose keys depend on the gap's `kind` in GAPS.json; each key takes only the listed values:
  - `comparison_arms`: `"arms"`: `"two"`, `"three_to_four"`, `"five_or_more"` (arms one experiment must compare, baseline included); `"arm_axis"`: `"configuration"`, `"implementation"`, `"input_case"`, `"hardware"`, `"mixed"` (what differs between arms); `"outcome"`: `"runtime"`, `"throughput"`, `"result_agreement"`, `"quality"`, `"cost"`, `"mixed"` (what is compared); `"arms_from_menu"`: `"all"`, `"some"`, `"none"` (how many arms are methods m5's fixed menu already has); `"sealable"`: `"yes"`, `"no"` (all arms and the decision rule can be fixed before any measurement).
  - `record_carryover`: `"fields"`: a non-empty array, no duplicates, of the record fields that must reach the measuring run or come back from it, chosen from `"name"`, `"unit"`, `"basis"`, `"value"`, `"differs_in"`, `"measured_by"`, `"phase"`, `"line"`, `"k_budget"`, `"cum_spend_through_measured_by"`, `"anchor"`, `"predictions"`, `"measured_value"`; `"direction"`: `"card_to_run"`, `"run_to_card"`, `"both"`.
  - `tolerance_equivalence`: `"criterion"`: `"equivalence_margin"`, `"non_inferiority"`, `"absolute_error"`, `"relative_error"`, `"distribution"`, `"mixed"`; `"between"`: `"arm_vs_baseline"`, `"arm_vs_arm"`, `"arm_vs_published"`, `"mixed"`; `"margin_source"`: `"question"`, `"published"`, `"design_choice"`, `"unknown"` (where the margin comes from); `"replicates"`: `"one"`, `"two_to_five"`, `"six_or_more"` (per arm, to judge it).
  - `route_execution`: `"needed"`: `"yes"`, `"no"` (needed when m5 stays the calibration executor).
  - `agent_access`: `"missing"`: `"brief"`, `"data"`, `"prior_run_outputs"`, `"network"`, `"mixed"`; `"roles"`: `"intake"`, `"harness"`, `"authoring_roles"`, `"all_claude_roles"`; `"wrapper_fix"`: `"sufficient"`, `"partial"`, `"insufficient"` (the operator's wrapper workaround above).
  - `other`: `"fact"`: `"per_arm_wall"`, `"per_arm_gpu_s"`, `"gpu_memory"`, `"cpu_utilisation"`, `"energy"`, `"hardware_identity"`, `"mixed"` (what must be recorded); `"per"`: `"run"`, `"stage"`, `"arm"`.
  - `quality_metric`: `"metric"`: `"scalar_score"`, `"error_vs_reference"`, `"pass_rate"`, `"mixed"`; `"between"`: `"arm_vs_baseline"`, `"arm_vs_arm"`, `"arm_vs_published"`, `"mixed"`.

Also write `ASSESSMENT.md` for the owner: each gap's requirement in prose, why your order, which parts each closure unlocks, and what a completed answer to each part will look like. Write `NARROWING.md` ("No narrowing." with the reason, or what changed), `PREDICTIONS.md` ("No test; no predictions."), `predictions.json` `{"items": []}`, `outcomes.json` `{"items": []}` (s08 sealed none), and `NEXT.json` `{"action": "stop", "reason": "contract_gap"}`. PARTS.json and REQS.json hold no free text, no seed content and no keys beyond those listed.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"parts_count"`: `"four"`, `"five"`, `"six"`, `"seven_or_more"`
- `"parts_open_no_mechanism"`: `"none"`, `"one"`, `"two_or_more"`
- `"g4_needed"`: `"yes"`, `"no"`
- `"final_runs_expected"`: `"one"`, `"two"`, `"three_or_more"` (m5 runs needed, after the gaps close, to answer every open part)
- `"final_usd_band"`: `"under_20"`, `"20_to_100"`, `"100_to_300"`, `"over_300"` (box cost of those runs together)
- `"next_action"`: `"stop"`
- `"stop_reason"`: `"contract_gap"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`

No other keys and no free text. Finish within 30 minutes.
