import json, os, sys
B = os.path.expanduser("~/.cache/blind01")
MERGE, SPENT, OVERHEAD = sys.argv[1], sys.argv[2], sys.argv[3]   # merge commit of U57/U58, USD spent, measured overhead line
s = f"""## Step s27 (fixture analysis for margins: error budget, sealed tolerance rule, fixture run design; no network)
Your step folder is `experiments/blind-02/science/s27/`. Read `science/s01/` to `science/s26/` first, above all s13's `FINAL.json` (the parts, arms and comparisons K1 to K7), s15's shapes and s26. The sealed comparison mechanism is merged (commit {MERGE}): read `dut/pipeline/m5/SCHEMAS.md`, section `Sealed comparison (U57, U58)`, whole; it is the contract s23 drafted and s24 and s25 audited, as implemented. The operator demonstrated its isolation on a live box before this step and measured its overhead: {OVERHEAD}.

Owner decisions of 2026-11-03: the margins of the output comparisons (K1 to K3, and any other margin the comparisons need) come from independent fixture analysis: on fixtures disjoint from the main comparison's inputs, never from the arms' differences on the main inputs. Establish a defensible numerical error budget and seal the resulting tolerances before the main comparison; if that is not possible, keep the uncertainty (the main comparison then states it and claims no tolerance it cannot defend). One combined box ceiling of USD 100 covers the calibration and main runs, including setup, failed attempts and idle time (USD {SPENT} spent so far, whole allocations, up to USD 3.29 per hour for one H100); the main runs must fit what remains after this one.

Answer in `ASSESSMENT.md`, in this order:
A. The main comparison's inputs as s13 and s15 fixed them (by id), and the fixtures you choose: how each fixture exercises the same numerical path as the main inputs (precision, reductions, the code paths K1 to K3 compare), and why it is disjoint from every main input (state the rule that makes it so). Use the published materials only.
B. The analytic error budget, per output the margins concern: the sources of run-to-run and arm-to-arm numerical difference that a correct arm can show (floating-point precision, reduction and summation order, nondeterministic kernels, library versions, compiler flags, seeds), each with its expected size and the evidence for it (quote the published source, file and line). Say which sources the fixtures measure and which only the analysis bounds.
C. The tolerance rule, sealed now, before any fixture result: exactly how each margin of the main comparison will follow from the fixture run's recorded values and the analytic budget (for example: margin = the larger of k times the largest self-disagreement between duplicate arms over the fixtures and replicates, and the analytic bound; with k and every constant fixed here), what result of the fixture run makes a margin indefensible (then the uncertainty is kept, as the owner directs), and how a later step applies the rule without judgment. Write it in `TOLERANCE_RULE.md` and as `tolerance_rule.json` `{{"items": [...]}}`, one item per main comparison margin.
D. The fixture run: one design file in this folder for `args.comparison`, in the contract's exact schema. Arms: A0 the published baseline, a duplicate of A0 with identical commands (self-agreement), and the arms whose outputs the main comparison compares; inputs: the fixtures only; outputs: those the margins concern; the evaluator only if the margins need it. Comparisons may be none (a run that only records values for the rule) or exact-agreement checks that cannot bias the rule; state which and why. Choose `replicates`, `warmup` and `timeout_s` so that the run fits one allocation inside the 6 h run limit with the measured overhead; `budget_s` below 19800. Project box hours and USD.
E. What each possible fixture result would decide (margins defensible, indefensible, or the fixture run failing), and how the main comparison's design follows.
F. Narrowing: unchanged, or exactly what changed.

The brief you write is the run's whole brief: the seed's exact bytes, then the materials addendum's section copied unchanged from `m5/b01_materials/BRIEF_run1.md`, then one section headed `## Comparison request (science step s27)` that asks for the fixture run as the design's view describes it. That section, and the design's `what`, `spec`, `select`, `commands` and `env` text the run's agents see, state no margin, threshold, confidence, reference value, expected result or tolerance rule (the operator screens them against the design's sealed numbers and refuses a brief or design that carries one). Keep no copy of the design outside this folder.

Seal your predictions for the fixture run in `PREDICTIONS.md` and `predictions.json` (for example the largest self-disagreement per output, whether the analytic bound covers it, whether each margin will be defensible). s26 sealed none: write `outcomes.json` `{{"items": []}}`.

`NEXT.json`: `{{"action": "m5", "brief": "<file in this folder>", "new_run_flags": [], "comparison": {{"design": "<design file in this folder>"}}}}`, or `{{"action": "stop", "reason": "<stop_reason>"}}` when no fixture run is justified (with `needs_owner` if a decision only the owner can make blocks it, `limits` if it cannot fit the budget).

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"error_budget_feasible"`: `"yes"`, `"partly"`, `"no"`
- `"budget_basis"`: `"fixtures_and_analysis"`, `"fixtures_only"`, `"analysis_only"`, `"none"`
- `"fixtures_disjoint"`: `"yes"`, `"no"`
- `"self_agreement_arms"`: `"none"`, `"one"`, `"two_or_more"`
- `"margins_covered"`: `"all"`, `"some"`, `"none"`
- `"tolerance_rule_sealed"`: `"yes"`, `"no"`
- `"fixture_comparisons"`: `"none"`, `"exact_only"`, `"other"`
- `"evaluator_in_fixture_run"`: `"yes"`, `"no"`
- `"next_action"`: `"m5"`, `"stop"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"needs_owner"`, `"contract_gap"`, `"limits"`
- `"next_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"next_projected_hours"`: `"none"`, `"under_1"`, `"1_to_3"`, `"3_to_6"`
- `"main_runs_fit_after"`: `"yes"`, `"no"`, `"unknown"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 60 minutes.
"""
open(f"{B}/sci_s27.md", "w").write(s)
keys = {}
for line in s.splitlines():
    if line.startswith('- `"') and '`: ' in line:
        k = line.split('`"', 1)[1].split('"`', 1)[0]
        keys[k] = [v.strip('`"') for v in line.split("`: ", 1)[1].split(", ")]
json.dump({"enums": keys, "actions": ["m5", "stop"]}, open(f"{B}/sci_s27.enums.json", "w"), indent=1)
print("ok", len(keys))
