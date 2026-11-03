
## Step s21 (second revision of the seed-neutral G1/G3/G6 contract draft; no network; no new test)
Your step folder is `experiments/blind-02/science/s21/`. Read `science/s13/` to `science/s20/` first, above all `s19/DRAFT.md`, `s19/ASSESSMENT.md`, `s19/OWNER.json` and the independent audit `s20/AUDIT.json` and `s20/ASSESSMENT.md`. s20 found no seed content in s19's draft and judged it `partial` with one problem, `leaks_or_biases`. Fix it in the contract when a contract rule can. When the fix depends on an owner decision (for example how the evaluator's private data may be fetched and held), write the rule for the option you recommend, state the decision in ASSESSMENT.md, and set `leak_fix` below accordingly. When the remaining risk cannot be removed by any rule, state it as a declared residual risk in the contract's purpose bullet. Keep everything else of s19's draft that is right, and keep the contract as small as FINAL.json and SHAPES.json need.

Write `DRAFT.md`: exactly one section, starting with the line `## Sealed comparison (U57, U58)`, that replaces s19's draft, fixing s20's finding. All of s17's rules on seed neutrality apply unchanged (see `science/s17/PROMPT.md`): no program, library, model, dataset, case, input, file, path or output name specific to the seed or its materials; no number, unit, margin, tolerance, threshold or reference value from the seed, its materials or the route's findings; no quoted seed text; general mechanisms only, executable by deterministic code.

Write `OWNER.json`: exactly `{"decisions": [...]}`, the decisions the owner must make before a final run, no duplicates, possibly empty, from `"margins"` (comparisons whose margins neither the question nor a published source gives), `"thresholds_or_references"`, `"evaluator_private_data"` (whether and how the evaluator's private data may be fetched and held), `"arm_selection"`, `"replicates_or_budget"`, `"split_runs"`, `"spend_above_20"` (a run whose box cost may exceed USD 20), `"other"`. Explain each in ASSESSMENT.md.

Write `ASSESSMENT.md` for the owner (what you changed and why, and each owner decision), `NARROWING.md` ("No narrowing." with the reason, or what changed), `PREDICTIONS.md` ("No test; no predictions."), `predictions.json` `{"items": []}`, `outcomes.json` `{"items": []}` (s20 sealed none), and `NEXT.json` `{"action": "stop", "reason": "contract_gap"}`. OWNER.json holds no free text and no seed content.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"draft_written"`: `"yes"`, `"no"`
- `"leak_fix"`: `"fixed"` (a contract rule removes it), `"needs_owner_decision"` (fixed for the recommended option; the owner must choose), `"residual"` (declared; no rule removes it)
- `"owner_decision_count"`: `"none"`, `"one"`, `"two_or_more"`
- `"next_action"`: `"stop"`
- `"stop_reason"`: `"contract_gap"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`

No other keys and no free text. Finish within 45 minutes.
