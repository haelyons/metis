import json, os, sys
B = os.path.expanduser("~/.cache/blind01")
SPENT, LEFT = sys.argv[1], sys.argv[2]   # ledger USD spent and left after run8
s = f"""## Step s29 (after the fixture rerun run8 failed before any invocation; revise the fixture run; no network)
Your step folder is `experiments/blind-02/science/s29/`. Read `science/s01/` to `science/s28/` first, above all s27 (the tolerance rule it sealed) and s28 (its assessment of run7, its design, brief and PREDICTIONS.md), and the contract `dut/pipeline/m5/SCHEMAS.md`, section `Sealed comparison (U57, U58)`. s28's fixture rerun is `experiments/blind-02/m5/run8/` (records as for run7: `args.json`, `pipeline.log`, `control/`, `agent/` harness files and fetched logs, `operator/OPERATOR_TAKEAWAY.md`). Two authorized readers examined the failures: `experiments/blind-02/m5/run7_failcause/` (run7) and `experiments/blind-02/m5/run8_fetchfail/` (run8); read their REPORT.md files.

Operator metadata on run8: `gpu_1x_h100_pcie` (USD 3.29/h). Intake PASS (149 s), reproduce PASS (610 s; setup rc 2, then rc 1, then rc 0 after two harness repairs; anchors rc 0; freeze rc 0), profile to implement SKIPPED, evaluate FAIL `infra` in 42 s: `comparison-users` rc 1 at 32 s, before any invocation, with the pipeline's message `fetch_private.sh exited <rc>` (Separated users step 5). The run8_fetchfail reader's status: `fetch_failure` script_error, `caused_by` harness_script, `mechanism_defect` none, `same_script_in_run7` no, `harness_repairs_touched_fetch` no, `next` rerun_after_design_change. The run7_failcause reader's status: `invocation_failure` evaluator_error, `failure_caused_by` design_or_harness, `mechanism_defect` none, `s28_fits_budget` at_risk. Run box USD 0.73; ledger USD {SPENT} spent of the USD 100 ceiling, USD {LEFT} left. The harness (including `fetch_private.sh`) is written afresh in each run by the pipeline's harness agent from the brief and the design's view.

Owner decisions of 2026-11-03 stand: margins come from independent fixture analysis on fixtures disjoint from the main comparison's inputs; tolerances are sealed before the main comparison, or the uncertainty is kept and the main comparison claims no tolerance it cannot defend. A sealed rule is never changed after its result.

Answer in `ASSESSMENT.md`, in this order:
A. Why run8 failed and why run7's invocations failed, from the records and the two reports, with file and line references; what in the brief, the design's view or the harness agent's instructions let each happen.
B. The revised fixture run: what you change in the brief or the design so that the harness agent writes a `fetch_private.sh` and an evaluator that work (state it in the run's own terms, without any sealed number), and what you keep from s28. s27's tolerance rule governs unless you seal a new one now, before any result; say which.
C. s28's predictions scored (`outcomes.json`), as far as run8 resolves them; the rest marked unresolved.
D. The next test, if one is justified, with what each result decides; or stop with `no_justified_test`, `contract_gap` (name file, section and what is missing), `needs_owner` (state the decision and the options) or `limits`. If an m5 run: one design file in this folder for `args.comparison` in the contract's exact schema; size `replicates`, `warmup`, `timeout_s` and `budget_s` (below 19800) from run7's measured cost of one invocation (about 960 s per comparison receipt on an A10) so that it fits one allocation inside the 6 h run limit on an A10 or an H100 (say how it holds on each); project box hours and USD.
E. Whether the main runs still fit the USD {LEFT} left after the next step, with the arithmetic.
F. Narrowing: unchanged, or exactly what changed.

If the next step is an m5 run, the brief you write is the run's whole brief: the seed's exact bytes, then the materials addendum's section copied unchanged from `m5/b01_materials/BRIEF_run1.md`, then one section headed `## Comparison request (science step s29)` that asks for the run as the design's view describes it. That section, and the design's `what`, `spec`, `select`, `commands` and `env` text the run's agents see, state no margin, threshold, confidence, reference value, expected result or tolerance rule (the operator screens them against the design's sealed numbers and refuses a brief or design that carries one). Keep no copy of the design outside this folder.

Seal your predictions for the next run in `PREDICTIONS.md` and `predictions.json`.

`NEXT.json`: `{{"action": "m5", "brief": "<file in this folder>", "new_run_flags": [], "comparison": {{"design": "<design file in this folder>"}}}}`, or `{{"action": "stop", "reason": "<stop_reason>"}}`.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"run8_cause"`: `"fetch_script"`, `"private_data_source"`, `"design"`, `"mechanism"`, `"other"`
- `"run7_cause"`: `"evaluator"`, `"arm_commands"`, `"timeouts"`, `"design"`, `"mechanism"`, `"other"`
- `"change_made"`: `"brief"`, `"design"`, `"brief_and_design"`, `"none"`
- `"change_addresses_both"`: `"yes"`, `"partly"`, `"no"`
- `"tolerance_rule"`: `"s27_unchanged"`, `"new_rule_sealed_before_result"`, `"none"`
- `"s28_predictions_scored"`: `"all"`, `"some"`, `"none"`
- `"next_action"`: `"m5"`, `"stop"`
- `"next_kind"`: `"fixture_rerun"`, `"main_comparison"`, `"other"`, `"none"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"needs_owner"`, `"contract_gap"`, `"limits"`
- `"next_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"next_projected_hours"`: `"none"`, `"under_1"`, `"1_to_3"`, `"3_to_6"`
- `"fits_one_allocation"`: `"yes_on_both"`, `"h100_only"`, `"no"`
- `"main_runs_fit_after"`: `"yes"`, `"no"`, `"unknown"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 60 minutes."""
open(f"{B}/sci_s29.md", "w").write(s)
keys = {}
for line in s.splitlines():
    if line.startswith('- `"') and '`: ' in line:
        k = line.split('`"', 1)[1].split('"`', 1)[0]
        keys[k] = [v.strip('`"') for v in line.split("`: ", 1)[1].split(", ")]
json.dump({"enums": keys, "actions": ["m5", "stop"]}, open(f"{B}/sci_s29.enums.json", "w"), indent=1)
print("ok", len(keys))
