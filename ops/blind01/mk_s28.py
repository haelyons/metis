import json, os, sys
B = os.path.expanduser("~/.cache/blind01")
SPENT, LEFT = sys.argv[1], sys.argv[2]   # ledger USD spent and left after run7
s = f"""## Step s28 (after the fixture run run7: apply the sealed tolerance rule, choose the next test; no network)
Your step folder is `experiments/blind-02/science/s28/`. Read `science/s01/` to `science/s27/` first, above all s27 (its ASSESSMENT.md, the tolerance rule it sealed, its design file and PREDICTIONS.md) and the contract `dut/pipeline/m5/SCHEMAS.md`, section `Sealed comparison (U57, U58)`. The fixture run s27 chose is `experiments/blind-02/m5/run7/` (records: `args.json`, `pipeline.log`, `control/` (receipts, `box.json`, `comparison.json`, `comparison_seal.json`, `comparison_scored.json`), `agent/results/evaluate/` (`comparison_compute.json`, the invocations' fetched outputs, 11.6 GB: read selectively), `agent/wf/` model calls, `operator/OPERATOR_TAKEAWAY.md`).

Operator metadata on run7: no capacity for H100 or A100, so the launcher took `gpu_1x_a10` (USD 1.29/h; it accepts any type up to USD 3.29/h, H100 first). Intake PASS (144 s), reproduce PASS (662 s; setup rc 0, anchors rc 0, freeze rc 0), profile to implement SKIPPED, evaluate PASS in 12,695 s against `budget_s` 12,600: `comparison-users` rc 0, then 13 invocations, every `comparison-job` (23 to 31 s) and `comparison` (945 to 989 s for the first 12, 732 s for the last) rc 0 and none timed out, then `comparison-private-remove` rc 0. The design named 4 arms, 4 inputs and 6 replicates; s27 projected 1 to 3 h. Run box USD 4.84; ledger USD {SPENT} spent of the USD 100 ceiling, USD {LEFT} left. The operator has not read the scored file or any output.

Owner decisions of 2026-11-03 stand: margins come from independent fixture analysis on fixtures disjoint from the main comparison's inputs; tolerances are sealed before the main comparison, or the uncertainty is kept and the main comparison claims no tolerance it cannot defend. A sealed rule is never changed after its result.

Answer in `ASSESSMENT.md`, in this order:
A. What run7 recorded: the invocations completed against the design (by arm, input, round and mode), their statuses, which outputs have values, the parts' own walls against the comparison receipts; why it covered what it did (the box, the cost of one invocation against s27's projection, the budget); quote files.
B. s27's sealed tolerance rule, applied exactly as sealed to what run7 recorded: for each margin, the value the rule gives, or that it cannot be applied and which values are missing. Do not change the rule. Say for each margin whether it is defensible now.
C. s27's predictions scored (`outcomes.json`, one item per prediction id with the outcome and the evidence file).
D. The next test, if one is justified: the single most informative step now (for example a fixture run sized to the measured cost of one invocation, the main comparison, or stop), with what each result decides. Stop with `no_justified_test`, `contract_gap` (name file, section and what is missing), `needs_owner` (state the decision and the options) or `limits`. If the next step is an m5 run, design it as s27 did: one design file in this folder for `args.comparison` in the contract's exact schema; size `replicates`, `warmup`, `timeout_s` and `budget_s` (below 19800) from the measured cost of one invocation so that it fits one allocation inside the 6 h run limit on the box the launcher may give (say how it holds on an A10 and on an H100); project box hours and USD. If its margins need a tolerance rule other than s27's, seal it now, before its result, and say how it relates to s27's.
E. Whether the main runs still fit the USD {LEFT} left after the next step, with the arithmetic.
F. Narrowing: unchanged, or exactly what changed.

If the next step is an m5 run, the brief you write is the run's whole brief: the seed's exact bytes, then the materials addendum's section copied unchanged from `m5/b01_materials/BRIEF_run1.md`, then one section headed `## Comparison request (science step s28)` that asks for the run as the design's view describes it. That section, and the design's `what`, `spec`, `select`, `commands` and `env` text the run's agents see, state no margin, threshold, confidence, reference value, expected result or tolerance rule (the operator screens them against the design's sealed numbers and refuses a brief or design that carries one). Keep no copy of the design outside this folder.

Seal your predictions for the next run in `PREDICTIONS.md` and `predictions.json`.

`NEXT.json`: `{{"action": "m5", "brief": "<file in this folder>", "new_run_flags": [], "comparison": {{"design": "<design file in this folder>"}}}}`, or `{{"action": "stop", "reason": "<stop_reason>"}}`.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"fixture_coverage"`: `"full"`, `"partial"`, `"none"`
- `"coverage_cause"`: `"invocation_cost"`, `"box_type"`, `"failures"`, `"design"`, `"other"`, `"not_applicable"`
- `"invocations_failed"`: `"none"`, `"some"`, `"all"`
- `"isolation_concern"`: `"none"`, `"suspected"`
- `"tolerance_rule_applied"`: `"all_margins"`, `"some_margins"`, `"none"`
- `"margins_defensible"`: `"all"`, `"some"`, `"none"`
- `"tolerance_rule"`: `"s27_unchanged"`, `"new_rule_sealed_before_result"`, `"none"`
- `"s27_predictions_scored"`: `"all"`, `"some"`, `"none"`
- `"next_action"`: `"m5"`, `"stop"`
- `"next_kind"`: `"fixture_rerun"`, `"main_comparison"`, `"other"`, `"none"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"needs_owner"`, `"contract_gap"`, `"limits"`
- `"next_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"next_projected_hours"`: `"none"`, `"under_1"`, `"1_to_3"`, `"3_to_6"`
- `"main_runs_fit_after"`: `"yes"`, `"no"`, `"unknown"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 60 minutes."""
open(f"{B}/sci_s28.md", "w").write(s)
keys = {}
for line in s.splitlines():
    if line.startswith('- `"') and '`: ' in line:
        k = line.split('`"', 1)[1].split('"`', 1)[0]
        keys[k] = [v.strip('`"') for v in line.split("`: ", 1)[1].split(", ")]
json.dump({"enums": keys, "actions": ["m5", "stop"]}, open(f"{B}/sci_s28.enums.json", "w"), indent=1)
print("ok", len(keys))
