import json, os, sys
B = os.path.expanduser("~/.cache/blind01")
SPENT, LEFT = sys.argv[1], sys.argv[2]   # ledger USD spent and left after run9
s = f"""## Step s31 (the main comparison: owner decision check, then design; no network)
Your step folder is `experiments/blind-02/science/s31/`. Read `science/s01/` to `science/s30/` first, above all s13's `FINAL.json` (the parts, arms and comparisons K1 to K7), s15's shapes, s27 (the tolerance rule it sealed), s29 and s30 (its application of s27's rule to the fixture run run9, the margins it found defensible, its choice of the main comparison and the owner decision it stopped on), and the contract `dut/pipeline/m5/SCHEMAS.md`, section `Sealed comparison (U57, U58)`.

s30's status: `fixture_coverage` full, `invocations_failed` none, `isolation_concern` none, `tolerance_rule_applied` all_margins, `margins_defensible` all, `uncertainty_kept` none, `tolerance_rule` s27_unchanged, `next_kind` main_comparison, projected USD 5 to 20 and 1 to 3 h, `fits_one_allocation` yes_all_box_types, `main_runs_fit_after` yes; then `next_action` stop with `stop_reason` needs_owner. The operator's prompt for s30 named the cost of the main comparison as an example of a decision needing the owner, without stating the owner's standing approval below; the operator cannot read which decision s30 named.

Owner decisions of 2026-11-03, standing: the calibration runs and the main runs are approved within one combined box ceiling of USD 100, including setup, failed attempts and idle time (USD {SPENT} spent, USD {LEFT} left), each run within the 6 h run limit; no further approval is needed for a main run that fits them. Margins come from independent fixture analysis on fixtures disjoint from the main comparison's inputs; tolerances are sealed before the main comparison, or the uncertainty is kept and the main comparison claims no tolerance it cannot defend. A sealed rule is never changed after its result. The science agent picks the next justified test; stop only at the spend limit, a genuine owner decision, or when no justified test remains.

Answer in `ASSESSMENT.md`, in this order:
A. The owner decision s30 stopped on, quoted from s30, and whether the standing decisions above already settle it (say which decision and why).
B. If they settle it: the main comparison. One design file in this folder for `args.comparison` in the contract's exact schema: K1 to K7 as s13 and s15 fixed them, on the main inputs (disjoint from run9's fixtures), with the margins exactly as s30 derived them from s27's sealed rule and every other sealed number in the design, never in the view. Size `replicates`, `warmup`, `timeout_s` and `budget_s` (below 19800) from run9's measured cost of one invocation (about 36 s outside the parts plus the parts' own walls) so that it fits one allocation inside the 6 h run limit on an A10, an A100 or an H100 (say how it holds on each); project box hours and USD. Say what each possible result of each comparison decides for the seed's question, and how many main runs the question needs.
C. If they do not settle it: stop with `needs_owner`, and state the decision and the options for the owner in a separate file `OWNER_DECISION.md` in this folder (no other change).
D. Whether the main runs fit the USD {LEFT} left, with the arithmetic.
E. Narrowing: unchanged, or exactly what changed.

If the next step is the main comparison, the brief you write is the run's whole brief: the seed's exact bytes, then the materials addendum's section copied unchanged from `m5/b01_materials/BRIEF_run1.md`, then one section headed `## Comparison request (science step s31)` that asks for the run as the design's view describes it. That section, and the design's `what`, `spec`, `select`, `commands` and `env` text the run's agents see, state no margin, threshold, confidence, reference value, expected result or tolerance rule (the operator screens them against the design's sealed numbers and refuses a brief or design that carries one). Keep no copy of the design outside this folder.

Seal your predictions for the main comparison in `PREDICTIONS.md` and `predictions.json` (for example each comparison's outcome). s30 sealed none: write `outcomes.json` `{{"items": []}}`.

`NEXT.json`: `{{"action": "m5", "brief": "<file in this folder>", "new_run_flags": [], "comparison": {{"design": "<design file in this folder>"}}}}`, or `{{"action": "stop", "reason": "<stop_reason>"}}`.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"s30_decision_class"`: `"cost_within_ceiling"`, `"cost_over_ceiling"`, `"scope_or_question"`, `"method_choice"`, `"data_or_licence"`, `"other"`
- `"settled_by_standing_decisions"`: `"yes"`, `"no"`
- `"margins_in_design"`: `"all_from_s30"`, `"some_from_s30"`, `"none"`
- `"uncertainty_kept"`: `"none"`, `"some_margins"`, `"all_margins"`
- `"main_runs_needed"`: `"one"`, `"two"`, `"three_or_more"`, `"not_applicable"`
- `"next_action"`: `"m5"`, `"stop"`
- `"next_kind"`: `"main_comparison"`, `"other"`, `"none"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"needs_owner"`, `"contract_gap"`, `"limits"`
- `"next_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"next_projected_hours"`: `"none"`, `"under_1"`, `"1_to_3"`, `"3_to_6"`
- `"fits_one_allocation"`: `"yes_all_box_types"`, `"h100_only"`, `"no"`, `"not_applicable"`
- `"main_runs_fit_after"`: `"yes"`, `"no"`, `"unknown"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 60 minutes."""
open(f"{B}/sci_s31.md", "w").write(s)
keys = {}
for line in s.splitlines():
    if line.startswith('- `"') and '`: ' in line:
        k = line.split('`"', 1)[1].split('"`', 1)[0]
        keys[k] = [v.strip('`"') for v in line.split("`: ", 1)[1].split(", ")]
json.dump({"enums": keys, "actions": ["m5", "stop"]}, open(f"{B}/sci_s31.enums.json", "w"), indent=1)
print("ok", len(keys))
