
## Step s15 (the shape of each comparison, and fixes for the G1/G3/G6 contract, from fixed lists; no network; no new test)
Your step folder is `experiments/blind-02/science/s15/`. Read `science/s13/` and `science/s14/` first. s14 judged the operator's draft (units U57/U58; its text is in `science/s14/PROMPT.md`) `partial`: every comparison and the compute facts missing; problems metric_not_capturable, statistic_unfit, criterion_unfit, margin_rule_unfit, reference_unfit, inputs_unfit, budget_unfit, compute_unfit, leaks_or_biases. The operator cannot read your prose and revises the draft once, so this step states, for each comparison of s13's FINAL.json, how it must be measured and decided, and names the remaining fixes, each from a fixed list. Choose `other` only when nothing listed serves, and then explain it in ASSESSMENT.md for the owner.

Write `SHAPES.json`: exactly `{"comparisons": [...], "fixes": {...}}`.
- `"comparisons"`: one item per FINAL.json comparison, same ids in the same order, each exactly `{"id", "metric_origin", "comparator", "decision_unit", "pairing", "interval", "margin_form", "rel_base", "reference_origin", "ratio_form"}`:
  - `"metric_origin"`: `"adapter_scalar"` (the arm's adapter reports the number), `"sealed_extraction"` (the pipeline reads it from the arm's own output by a rule fixed before the run, as in U54), `"cross_arm_outputs"` (a trusted comparator compares two arms' output files for the same input and replicate), `"trusted_wall"` (the pipeline's wall time of the invocation), `"derived"` (computed by the pipeline from other measured numbers, for example work divided by wall time), `"other"`.
  - `"comparator"`: `"none"` unless `cross_arm_outputs`; then `"exact"`, `"elementwise_abs"`, `"elementwise_rel"`, `"elementwise_abs_plus_rel"` (an element agrees when `abs(a-b) <= atol + rtol*abs(b)`), `"set_or_ranking"`, `"other"`.
  - `"decision_unit"`: `"pooled_mean"` (the mean over inputs per replicate, then decided once), `"per_input_all"` (decided per input; the comparison holds only if it holds on every input), `"per_input_each"` (decided and reported per input), `"worst_input"` (decided on the worst input), `"other"`.
  - `"pairing"`: `"paired_replicate"` (replicate r of one arm pairs with replicate r of the other), `"unpaired"`, `"deterministic"` (one run decides it), `"other"`.
  - `"interval"`: `"all_pairs"` (every replicate inside the margin), `"sign_test"`, `"t_interval"`, `"bootstrap"`, `"none"` (no interval: a deterministic comparison), `"other"`.
  - `"margin_form"`: `"abs"`, `"rel"`, `"abs_plus_rel"`, `"none"`.
  - `"rel_base"`: `"none"`, `"against_value"` (the compared arm's value), `"reference"`, `"per_element"` (each output element's own value), `"other"`.
  - `"reference_origin"`: `"none"` (not against a fixed value), `"design_constant"` (fixed in the sealed design), `"published"` (a cited published value), `"previous_run"` (a value measured by an earlier run of this route, named in the design), `"baseline_arm"` (the baseline arm measured in this run), `"other"`.
  - `"ratio_form"`: `"none"`, `"median_of_ratios"`, `"ratio_of_medians"`, `"ratio_of_means"`, `"other"`.
- `"fixes"`: exactly these four keys, each a non-empty array of codes, no duplicates:
  - `"inputs"`: `"as_drafted"`, `"one_input_per_invocation"`, `"inputs_differ_by_arm"`, `"other"`.
  - `"budget"`: `"as_drafted"`, `"design_sets_budget"` (the design fixes the comparison's time budget, checked against the run ceiling before any box command), `"split_into_runs"` (the comparisons need more than one run), `"other"`.
  - `"compute"`: `"as_drafted"`, `"per_invocation_rows"` (one compute row per invocation, not only sums), `"exclude_overhead"` (GPU and wall time of the arm's own subprocess only, not uploads, links or fetches), `"software_versions"` (record CUDA, driver and each arm's program version), `"cpu_identity"`, `"other"`.
  - `"leaks"`: `"as_drafted"`, `"adapter_no_metrics"` (adapters only run the arm; every number comes from sealed extraction rules, the trusted comparator or the trusted wall time), `"separate_adapter_authors"` (no one agent writes every arm's adapter), `"view_text_screened"` (the design's free text shown to agents must state no expectation or criterion; the science step that writes it is responsible), `"other"`.

Write `ASSESSMENT.md` for the owner (why each shape and fix; what any `other` needs), `NARROWING.md` ("No narrowing." with the reason, or what changed), `PREDICTIONS.md` ("No test; no predictions."), `predictions.json` `{"items": []}`, `outcomes.json` `{"items": []}` (s14 sealed none), and `NEXT.json` `{"action": "stop", "reason": "contract_gap"}`. SHAPES.json holds no free text and no seed content.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"other_count"`: `"none"`, `"one"`, `"two_or_more"` (codes `other` anywhere in SHAPES.json)
- `"next_action"`: `"stop"`
- `"stop_reason"`: `"contract_gap"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`

No other keys and no free text. Finish within 30 minutes.
