import json, os, sys
B = os.path.expanduser("~/.cache/blind01")
NEW, SPENT, REP = sys.argv[1], sys.argv[2], sys.argv[3]
assert NEW.endswith("-tree") and float(SPENT) >= 0
s = f"""## Step s26 (card calibration choice after U54-U56; no network)
Your step folder is `experiments/blind-02/science/s26/`. Read `science/s01/` to `science/s25/` first, above all s13's `FINAL.json`, s15's shapes, and the contract s23 drafted (audited clean by s24 and, cross-family, by s25). Three units are now merged into the pipeline: card calibration (U54), tree records for calibration (U55) and card write-back with re-judging (U56). Read `dut/pipeline/m5/SCHEMAS.md`, sections `Card calibration (U54)` and `Card write-back and re-judging (U56)`, and the U55 part of `dut/pipeline/m5/CONTRACT.md`. The tree run `experiments/blind-02/20261103-0124-tree/` was rebuilt with the U55 pipeline by resume, as `experiments/blind-02/{NEW}/`: every agent call came from the cache, no model was called, and the operator's check found the same table, cards, inventory, frontier and calibration states; the records now carry `name`, `unit` and `band` on each required input and `judged` for re-judging. Use `{NEW}/out/result.json` for card records from now on. A first rebuild attempt missed the cache (the tree's prompts carry the run's work-folder path; resumed from another folder, 44 of 45 calls were answered afresh, 1 from the cache, with 21 understudy substitutions) and became an unplanned second tree run on the same arguments with the current pipeline: `experiments/blind-02/{REP}/`, 5 calibration records against the original's 6, the same frontier, different table, cards and inventory. It is recorded as is; you may weigh it as a replicate of the tree (how stable are the cards and their calibration needs across two runs?), but card calibration uses the records of `{NEW}`. The comparison mechanism (s23's contract, units U57 and U58) is being built and is not available to this step.

Owner decisions of 2026-11-03: margins come from independent fixture analysis, on fixtures disjoint from the main comparison's inputs, after the comparison mechanism exists (tolerances sealed before the main comparison, or the uncertainty kept); the evaluator's reference data may be held on the dedicated box; one combined box ceiling of USD 100 covers the calibration and main runs, including setup, failed attempts and idle time (USD {SPENT} spent so far; whole allocations count, at up to USD 3.29 per hour for one H100), and the added overhead of the comparison is measured before the rest is committed. Useful calibrations that the card mechanism can run should proceed now, independently of the comparison build.

A card calibration run is an m5 run with `args.card`: intake and the harness see only the input names, units, what measures them and their phases (`A/card_inputs.json`), never the card's values, bands, gates, predictions or anchor value; the harness agent declares how each input is read from the run's outputs; the pipeline seals the card and the extraction rules before any box command, scores each input against its band or gate after the anchors, and `card_resolve.js` returns the measurements to the card as MEASURED numbers and re-judges its plan and cost deterministically. `--stop-after-reproduce` ends the run after reproduce.

Answer in `ASSESSMENT.md`, in this order:
A. The cards. For each record of `{NEW}/out/result.json`: its key, the part P1..Pn of the question it serves, its state, its required inputs (id, basis, what measures them), and what earlier calibration runs (m5 run3 to run6) already measured of them, read against the card's own protocol. Say whether that earlier evidence can stand in for a card calibration (it has no `card_scored.json`, so `card_resolve.js` cannot use it).
B. Whether a card calibration is justified now: would measuring a card's inputs change which arm or candidate goes forward, how the main comparison is designed (inputs, replicates, budget, warmup), its cost projection against the USD 100 ceiling, or nothing? A calibration whose result changes nothing is not justified.
C. If one is: the single most informative card calibration, with what each possible result (each input holds, is refuted, or is not measured; state after write-back calibrated, refuted or unchanged; plan cost after re-judging) would decide.
D. If one is: the run. Write the brief as s02 did: the seed's exact bytes, then the materials addendum's section copied unchanged from `m5/b01_materials/BRIEF_run1.md`, then one section headed `## Calibration request (science step s26)` that names the card by key and asks for its inputs to be measured on the card's protocol. That section states no number from the card's record: no input value, band, gate threshold, prediction, anchor value, plan cost or budget, rounded or not (the run's agents must not see them; the operator screens the section against the record's numbers and refuses a brief that carries one). Launch bands (`card.bands`, `{{"abs": x}}`) only for inputs a multiplicative band cannot judge, each justified in the assessment; they are fixed now and never after the result. Do not combine `card` with `--units-check` or `--units-probe`; `--harness-from` only from a harness that holds `card_extract.json` (none does yet). Project the box hours and cost: one allocation, inside the 6 h run limit, counted whole against the ceiling.
E. If none is: which test is justified next and what it waits on (for example the fixture analysis on the comparison mechanism), or why no test is justified.
F. Narrowing: unchanged, or exactly what changed.

Seal your predictions for the chosen run in `PREDICTIONS.md` and `predictions.json` (per input: holds, refuted or not measured; whether setup and the anchors pass; the card's state after write-back; the direction of the plan cost after re-judging). s25 sealed none: write `outcomes.json` `{{"items": []}}`.

`NEXT.json`: for a card calibration `{{"action": "m5", "brief": "<file in this folder>", "new_run_flags": ["--stop-after-reproduce"], "card": {{"tree_run": "{NEW}", "key": "<the record's key>"}}}}`, with `"bands"` inside `card` only when D justifies them; otherwise `{{"action": "stop", "reason": "<stop_reason>"}}`.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"cards_calibration_required"`: `"none"`, `"one"`, `"two"`, `"three_or_more"`
- `"earlier_runs_cover_card"`: `"fully"`, `"partly"`, `"no"`, `"not_applicable"`
- `"calibration_justified"`: `"yes"`, `"no"`
- `"calibration_changes"`: `"arm_choice"`, `"comparison_design"`, `"cost_projection"`, `"several"`, `"nothing"`
- `"inputs_to_measure"`: `"none"`, `"one"`, `"two"`, `"three_or_more"`
- `"launch_bands"`: `"none"`, `"some"`, `"all"`
- `"next_action"`: `"m5"`, `"stop"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"needs_owner"`, `"contract_gap"`, `"limits"`
- `"next_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"next_projected_hours"`: `"none"`, `"under_1"`, `"1_to_3"`, `"3_to_6"`
- `"decision_value"`: `"high"`, `"medium"`, `"low"`, `"none"`
- `"waits_on_mechanism"`: `"none"`, `"comparison"`, `"other"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 40 minutes.
"""
open(f"{B}/sci_s26.md", "w").write(s)
keys = {}
for line in s.splitlines():
    if line.startswith('- `"') and '`: ' in line:
        k = line.split('`"', 1)[1].split('"`', 1)[0]
        keys[k] = [v.strip('`"') for v in line.split("`: ", 1)[1].split(", ")]
json.dump({"enums": keys, "actions": ["m5", "stop"]}, open(f"{B}/sci_s26.enums.json", "w"), indent=1)
print("ok", len(keys))
