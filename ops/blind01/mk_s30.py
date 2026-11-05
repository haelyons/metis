import json, os, sys
B = os.path.expanduser("~/.cache/blind01")
SPENT, LEFT = sys.argv[1], sys.argv[2]   # ledger USD spent and left after run9
s = f"""## Step s30 (after the fixture run run9: apply the sealed tolerance rule, design the main comparison; no network)
Your step folder is `experiments/blind-02/science/s30/`. Read `science/s01/` to `science/s29/` first, above all s13's `FINAL.json` (the parts, arms and comparisons K1 to K7), s15's shapes, s27 (the tolerance rule it sealed) and s29 (its design, brief and PREDICTIONS.md), and the contract `dut/pipeline/m5/SCHEMAS.md`, section `Sealed comparison (U57, U58)`. s29's fixture run is `experiments/blind-02/m5/run9/` (records: `args.json`, `pipeline.log`, `control/` (receipts, `box.json`, `comparison.json`, `comparison_seal.json`, `comparison_scored.json`), `agent/results/evaluate/` (`comparison_compute.json`, the invocations' fetched outputs, 2.1 GB: read selectively), `operator/OPERATOR_TAKEAWAY.md`).

Operator metadata on run9: no H100 capacity, so the launcher took `gpu_1x_a100_sxm4` (USD 1.99/h). Intake PASS (124 s), reproduce PASS (464 s; setup rc 0 on the first attempt, anchors rc 0, freeze rc 0), profile to implement SKIPPED, evaluate PASS in 3,978 s against `budget_s` 16,200: `comparison-users` rc 0, versions rc 0, then 96 invocations (the whole design), every `comparison-job` (median 7 s) and `comparison` (median 29 s, 28 to 53 s) rc 0 and none timed out, then `comparison-private-remove` rc 0. Run box USD 2.52; ledger USD {SPENT} spent of the USD 100 ceiling, USD {LEFT} left. The operator has not read the scored file or any output.

Owner decisions of 2026-11-03 stand: margins come from independent fixture analysis on fixtures disjoint from the main comparison's inputs; tolerances are sealed before the main comparison, or the uncertainty is kept and the main comparison claims no tolerance it cannot defend. A sealed rule is never changed after its result.

Answer in `ASSESSMENT.md`, in this order:
A. What run9 recorded: the invocations' statuses by arm, input and round, which outputs have values, the self-agreement and arm-to-arm differences the margins concern, the parts' own walls; quote files.
B. s27's sealed tolerance rule, applied exactly as sealed to run9's recorded values: for each margin of the main comparison, the value the rule gives with its arithmetic, or that the rule cannot be applied and why. Do not change the rule. For each margin, whether it is defensible now; where it is not, the uncertainty the main comparison keeps and states.
C. s29's predictions scored (`outcomes.json`, one item per prediction id with the outcome and the evidence file).
D. The next test: the main comparison if the margins from B allow it (K1 to K7 as s13 and s15 fixed them, on the main inputs, with the margins from B and every other sealed number in the design, never in the view), another fixture run if B shows one is needed and what it would settle, or stop. Stop with `no_justified_test`, `contract_gap` (name file, section and what is missing), `needs_owner` (state the decision and the options; for example if the main comparison is ready and its cost needs the owner's approval) or `limits`. If an m5 run: one design file in this folder for `args.comparison` in the contract's exact schema; size `replicates`, `warmup`, `timeout_s` and `budget_s` (below 19800) from the measured cost of one invocation (about 36 s outside the parts plus the parts' own walls, from run9's receipts and outputs) so that it fits one allocation inside the 6 h run limit on an A10, an A100 or an H100 (say how it holds on each); project box hours and USD; say what each result of the main comparison would decide for the seed's question.
E. Whether the main runs fit the USD {LEFT} left, with the arithmetic.
F. Narrowing: unchanged, or exactly what changed.

If the next step is an m5 run, the brief you write is the run's whole brief: the seed's exact bytes, then the materials addendum's section copied unchanged from `m5/b01_materials/BRIEF_run1.md`, then one section headed `## Comparison request (science step s30)` that asks for the run as the design's view describes it. That section, and the design's `what`, `spec`, `select`, `commands` and `env` text the run's agents see, state no margin, threshold, confidence, reference value, expected result or tolerance rule (the operator screens them against the design's sealed numbers and refuses a brief or design that carries one). Keep no copy of the design outside this folder.

Seal your predictions for the next run in `PREDICTIONS.md` and `predictions.json`.

`NEXT.json`: `{{"action": "m5", "brief": "<file in this folder>", "new_run_flags": [], "comparison": {{"design": "<design file in this folder>"}}}}`, or `{{"action": "stop", "reason": "<stop_reason>"}}`.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"fixture_coverage"`: `"full"`, `"partial"`, `"none"`
- `"invocations_failed"`: `"none"`, `"some"`, `"all"`
- `"isolation_concern"`: `"none"`, `"suspected"`
- `"tolerance_rule_applied"`: `"all_margins"`, `"some_margins"`, `"none"`
- `"margins_defensible"`: `"all"`, `"some"`, `"none"`
- `"uncertainty_kept"`: `"none"`, `"some_margins"`, `"all_margins"`
- `"tolerance_rule"`: `"s27_unchanged"`, `"new_rule_sealed_before_result"`, `"none"`
- `"s29_predictions_scored"`: `"all"`, `"some"`, `"none"`
- `"next_action"`: `"m5"`, `"stop"`
- `"next_kind"`: `"main_comparison"`, `"fixture_rerun"`, `"other"`, `"none"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"needs_owner"`, `"contract_gap"`, `"limits"`
- `"next_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"next_projected_hours"`: `"none"`, `"under_1"`, `"1_to_3"`, `"3_to_6"`
- `"fits_one_allocation"`: `"yes_all_box_types"`, `"h100_only"`, `"no"`
- `"main_runs_fit_after"`: `"yes"`, `"no"`, `"unknown"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 60 minutes."""
open(f"{B}/sci_s30.md", "w").write(s)
keys = {}
for line in s.splitlines():
    if line.startswith('- `"') and '`: ' in line:
        k = line.split('`"', 1)[1].split('"`', 1)[0]
        keys[k] = [v.strip('`"') for v in line.split("`: ", 1)[1].split(", ")]
json.dump({"enums": keys, "actions": ["m5", "stop"]}, open(f"{B}/sci_s30.enums.json", "w"), indent=1)
print("ok", len(keys))
