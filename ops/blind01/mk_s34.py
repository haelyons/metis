import json, os, sys
B = os.path.expanduser("~/.cache/blind01")
SPENT, LEFT = sys.argv[1], sys.argv[2]   # ledger USD spent and left after run10
s = f"""## Step s34 (after the main comparison run10: the result, for the owner; no network)
Your step folder is `experiments/blind-02/science/s34/`. Read `science/s01/` to `science/s33/` first, above all the seed, s13's `FINAL.json` (the parts, arms and comparisons K1 to K7), s15's shapes, s27 (the sealed tolerance rule), s30 (the margins it derived from run9) and s31 to s33 (the main comparison's design, brief and the predictions sealed for it), and the contract `dut/pipeline/m5/SCHEMAS.md`, section `Sealed comparison (U57, U58)`. The main comparison is `experiments/blind-02/m5/run10/` (records: `args.json`, `pipeline.log`, `control/` (receipts, `box.json`, `comparison.json`, `comparison_seal.json`, `comparison_scored.json`), `agent/results/evaluate/` (`comparison_compute.json`, the invocations' fetched outputs, 2.1 GB: read selectively), `operator/OPERATOR_TAKEAWAY.md`).

Operator metadata on run10: `gpu_1x_a100_sxm4` (no H100 capacity). Intake PASS, reproduce PASS (setup rc 0 on the first attempt), profile to implement SKIPPED, evaluate PASS in 4,430 s against `budget_s` 14,400: `comparison-users` rc 0, versions rc 0, then 96 invocations, every `comparison-job` (median 7 s) and `comparison` (median 30 s) rc 0 and none timed out, then `comparison-private-remove` rc 0. Run box USD 2.74; ledger USD {SPENT} spent of the USD 100 ceiling, USD {LEFT} left. The operator has not read the scored file or any output.

Answer in `ASSESSMENT.md`, in this order:
A. What run10 recorded: the invocations' statuses by arm, input and round; whether the sealed design ran as sealed (`comparison_seal.json` against s33's design); any sign that an arm or the evaluator saw what the contract hides.
B. Each comparison K1 to K7 as scored in `comparison_scored.json`: outcome, estimate, interval, margin or threshold, reason; and your check that the scorer applied the sealed design (recompute at least the outcomes from `comparison_compute.json` and the fetched values).
C. s33's predictions scored (`outcomes.json`, one item per prediction id of s33's `predictions.json`, outcome true, false or null with the evidence file).
D. What the main comparison decides for the seed's question: what it supports, what it does not, and what stays open, with the uncertainty the design kept (none was kept at the tolerance step) and every limit of the evidence (box type, inputs, replicates, the fixture basis of the margins).
E. Whether any further test is justified: one that would change the answer, with its cost against the USD {LEFT} left, or stop with `no_justified_test` (the question is answered as far as this route can answer it), `needs_owner` (state the decision and the options), `contract_gap` or `limits`. If an m5 run, design it as s31 did (design file, brief whose `## Comparison request (science step s34)` section and visible design fields carry no sealed number) and seal predictions; otherwise write `predictions.json` with no predictions.
F. Narrowing: unchanged, or exactly what changed.

Also write `RESULT.md` for the owner: one page, plain language, the seed's question, the answer this route reached, how strong the evidence is and why, what it cost (box USD and hours from the ledger figures above and the runs' records), and what remains open.

`NEXT.json`: `{{"action": "m5", "brief": "<file in this folder>", "new_run_flags": [], "comparison": {{"design": "<design file in this folder>"}}}}`, or `{{"action": "stop", "reason": "<stop_reason>"}}`.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"invocations_failed"`: `"none"`, `"some"`, `"all"`
- `"design_ran_as_sealed"`: `"yes"`, `"no"`
- `"isolation_concern"`: `"none"`, `"suspected"`
- `"scorer_check"`: `"agrees"`, `"disagrees"`, `"not_done"`
- `"comparisons_supported"`: `"none"`, `"some"`, `"most"`, `"all"`
- `"comparisons_void_or_inconclusive"`: `"none"`, `"some"`, `"most"`, `"all"`
- `"question_answered"`: `"yes"`, `"partly"`, `"no"`
- `"s33_predictions_scored"`: `"all"`, `"some"`, `"none"`
- `"next_action"`: `"m5"`, `"stop"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"needs_owner"`, `"contract_gap"`, `"limits"`
- `"next_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 60 minutes."""
open(f"{B}/sci_s34.md", "w").write(s)
keys = {}
for line in s.splitlines():
    if line.startswith('- `"') and '`: ' in line:
        k = line.split('`"', 1)[1].split('"`', 1)[0]
        keys[k] = [v.strip('`"') for v in line.split("`: ", 1)[1].split(", ")]
json.dump({"enums": keys, "actions": ["m5", "stop"]}, open(f"{B}/sci_s34.enums.json", "w"), indent=1)
print("ok", len(keys))
