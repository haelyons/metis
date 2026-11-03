
## Step s19 (revise the seed-neutral G1/G3/G6 contract draft; no network; no new test)
Your step folder is `experiments/blind-02/science/s19/`. Read `science/s13/` to `science/s18/` first, above all `s17/DRAFT.md`, `s17/ASSESSMENT.md` and the independent audit `s18/AUDIT.json` and `s18/ASSESSMENT.md`. s18 found no seed content in s17's draft and judged it `partial` with one problem, `leaks_or_biases`. The operator, after that clean audit, read s17's draft and adds two review points of its own:
1. `cmp-private` protection by file mode can be defeated: the arm part runs as the same user, so an adapter or command can `chmod` the directory back, read it, and set `000` again before the wrapper's check. A rule that holds against a hostile arm is needed (for example running the arm part as a separate unprivileged user that cannot read `cmp-private`, with `out/` writable by it and the GPU devices usable; or keeping the evaluator's private data off the box except during the evaluator part).
2. Applying wf `isolation` to intake, harness and repair calls must still let each of them read what it reads today (the brief and, for the harness, intake's files and the probe) and write what it writes today (`A/intake/`, `A/harness/`), with the hidden paths unreadable; state how, in terms of the existing `isolation` setting in `dut/pipeline/m5/SCHEMAS.md`, or choose a different rule that achieves the same.
Also keep the contract as small as the comparisons of FINAL.json and SHAPES.json need: drop any rule no comparison, arm or compute fact needs.

Write `DRAFT.md`: exactly one section, starting with the line `## Sealed comparison (U57, U58)`, that replaces s17's draft, fixing s18's finding and the two points above. All of s17's rules on seed neutrality apply unchanged (see `science/s17/PROMPT.md`): no program, library, model, dataset, case, input, file, path or output name specific to the seed or its materials; no number, unit, margin, tolerance, threshold or reference value from the seed, its materials or the route's findings; no quoted seed text; general mechanisms only, executable by deterministic code.

Write `OWNER.json`: exactly `{"decisions": [...]}`, the decisions the owner must make before a final run, no duplicates, possibly empty, from `"margins"` (comparisons whose margins neither the question nor a published source gives), `"thresholds_or_references"`, `"evaluator_private_data"` (whether and how the evaluator's private data may be fetched and held), `"arm_selection"`, `"replicates_or_budget"`, `"split_runs"`, `"spend_above_20"` (a run whose box cost may exceed USD 20), `"other"`. Explain each in ASSESSMENT.md.

Write `ASSESSMENT.md` for the owner (what you changed and why, and each owner decision), `NARROWING.md` ("No narrowing." with the reason, or what changed), `PREDICTIONS.md` ("No test; no predictions."), `predictions.json` `{"items": []}`, `outcomes.json` `{"items": []}` (s18 sealed none), and `NEXT.json` `{"action": "stop", "reason": "contract_gap"}`. OWNER.json holds no free text and no seed content.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"draft_written"`: `"yes"`, `"no"`
- `"findings_resolved"`: `"all"`, `"most"`, `"some"` (s18's finding and the operator's two points)
- `"owner_decision_count"`: `"none"`, `"one"`, `"two_or_more"`
- `"next_action"`: `"stop"`
- `"stop_reason"`: `"contract_gap"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`

No other keys and no free text. Finish within 45 minutes.
