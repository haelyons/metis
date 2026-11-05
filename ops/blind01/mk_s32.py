import json, os, sys
B = os.path.expanduser("~/.cache/blind01")
s = """## Step s32 (repair of s31's main comparison: keep sealed numbers out of what the run's agents see; no network)
Your step folder is `experiments/blind-02/science/s32/`. Read `science/s27/` to `science/s31/` first, above all s31 (its ASSESSMENT.md, design file, brief, PREDICTIONS.md and NEXT.json), and the contract `dut/pipeline/m5/SCHEMAS.md`, section `Sealed comparison (U57, U58)`.

s31 designed the main comparison (3 arms, 4 inputs, 10 comparisons, 7 replicates, `budget_s` 14,400; margins exactly as s30 derived them from s27's sealed rule) and chose to run it. The operator's check refused it: 19 matches between the design's sealed numbers and numeric text the run's agents see. The check, exactly:
- sealed numbers: every number (at any depth) in each comparison's `margin`, `threshold`, `confidence` and `reference`;
- visible text: the brief's text after the heading `## Comparison request (science step`, and every string or number in the `what`, `spec`, `select`, `commands` and `env` fields of `arms`, `inputs`, `outputs` and `metrics`, and in the evaluator's `what` and `spec`;
- every numeric token in the visible text (regular expression `-?\\d[\\d,]*(?:\\.\\d+)?(?:[eE][-+]?\\d+)?`, commas removed) with d digits after the decimal point is a match for a sealed value v when |token - v| <= 0.5 * 10^-d and either d > 0 or |token| > 10 (integers of absolute value up to 10 are not screened against integer sealed values). Each matching (token, sealed value) pair counts once. The check passes only at 0.

Your task: produce the same main comparison with 0 matches. Change only what the run's agents see: the comparison request section of the brief and the visible fields of the design (for example drop a number the agents do not need, state a workload parameter in words, or refer to a published configuration by name). Keep every sealed number, every comparison, the arms' commands' effect, the inputs, outputs, metrics, replicates, warmup, timeouts, budget and seeds exactly as s31 sealed them; never move a sealed number into the visible text, and never change a sealed number to pass the check. If 0 matches is impossible without changing what the run measures, stop with `contract_gap` and say why.

Write in this folder: `ASSESSMENT.md` (A. which visible tokens matched which kind of sealed number, and whether each was a sealed number the agents could use or a coincidence; B. each change you made and why it leaves the run's measurement unchanged; C. a check you ran yourself with the rule above, giving 0), the corrected design file and brief (the brief again the run's whole brief: the seed's exact bytes, the materials addendum's section copied unchanged from `m5/b01_materials/BRIEF_run1.md`, then the section headed `## Comparison request (science step s32)`), `PREDICTIONS.md` and `predictions.json` identical to s31's (the same run; say so in one line), `outcomes.json` `{"items": []}`, and `NARROWING.md` (unchanged). Keep no copy of the design outside this folder.

`NEXT.json`: `{"action": "m5", "brief": "<file in this folder>", "new_run_flags": [], "comparison": {"design": "<design file in this folder>"}}`, or `{"action": "stop", "reason": "<stop_reason>"}`.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"match_cause"`: `"sealed_number_in_view"`, `"coincidental_tokens"`, `"both"`, `"other"`
- `"sealed_numbers_changed"`: `"no"`, `"yes"`
- `"measurement_changed"`: `"no"`, `"yes"`
- `"self_check_matches"`: `"zero"`, `"nonzero"`
- `"next_action"`: `"m5"`, `"stop"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"needs_owner"`, `"contract_gap"`, `"limits"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 40 minutes."""
open(f"{B}/sci_s32.md", "w").write(s)
keys = {}
for line in s.splitlines():
    if line.startswith('- `"') and '`: ' in line:
        k = line.split('`"', 1)[1].split('"`', 1)[0]
        keys[k] = [v.strip('`"') for v in line.split("`: ", 1)[1].split(", ")]
json.dump({"enums": keys, "actions": ["m5", "stop"]}, open(f"{B}/sci_s32.enums.json", "w"), indent=1)
print("ok", len(keys))
