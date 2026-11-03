
## Step s25 (cross-family audit of the third revision of the G1/G3/G6 contract draft: seed content, then sufficiency; no network; no new test)
Your step folder is `experiments/blind-02/science/s25/`. You are a different model family from the agents that drafted and audited this contract so far, and independent of the agent that wrote `science/s23/DRAFT.md`; do not edit it. Read the seed (the brief the route's runs used; `science/s01/ASSESSMENT.md` says where it is) and its materials as far as you need, then `science/s13/` to `science/s23/` (FINAL.json, SHAPES.json, the CHECK.json and ASSESSMENT.md of s14 and s16, s18's audit, the audits of s18, s20, s22 and s24 (s24 found it clean and sufficient; judge for yourself), and the DRAFT.md of s19, s21 and s23; s23's revises s21's after s22's audit). Judge sufficiency including the two operator review points listed in `science/s19/PROMPT.md`. A risk the draft declares as residual, or fixes for an option the owner must still choose, counts as resolved when the rule is sound.

First, the seed audit. The operator, who must stay blind to the seed, will read DRAFT.md and commit it where anyone can read it only if you find no seed content in it. Seed content is anything specific to the seed or its materials: a program, library, model, dataset, case, input, file, path or output name; a number, unit, margin, tolerance, threshold or reference value taken from the seed, its materials or the earlier steps' findings; quoted seed text; or wording that would let a reader infer what the seed asks or what the route found. General mechanisms and generic formats in wide use (JSON, CSV, NumPy `.npy`, plain text) are not seed content.

Second, sufficiency, as s14 and s16 judged the operator's drafts: whether DRAFT.md, as written, can run each arm, express and decide each comparison of FINAL.json as SHAPES.json shapes it, and record the compute facts FINAL.json asks for.

Write `AUDIT.json`: exactly `{"seed_content": ..., "codes": [...], "verdict": ..., "missing": [...], "problems": [...]}`:
- `"seed_content"`: `"none"` or `"some"`.
- `"codes"`: empty when `"none"`; otherwise, no duplicates, from `"program_or_library_name"`, `"dataset_case_or_input_name"`, `"file_path_or_output_name"`, `"numbers_or_values"`, `"quoted_text"`, `"inferable_question_or_finding"`, `"other"`.
- `"verdict"`, `"missing"` and `"problems"` exactly as defined for s14's and s16's CHECK.json (`science/s16/PROMPT.md`, "Write `CHECK.json`").

Write `ASSESSMENT.md` for the owner (each seed-content finding with its location in DRAFT.md, and your sufficiency judgement in prose), `NARROWING.md` ("No narrowing." with the reason, or what changed), `PREDICTIONS.md` ("No test; no predictions."), `predictions.json` `{"items": []}`, `outcomes.json` `{"items": []}` (s24 sealed none), and `NEXT.json` `{"action": "stop", "reason": "contract_gap"}`. AUDIT.json holds no free text and no seed content.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"seed_content"`: `"none"`, `"some"` (as in AUDIT.json)
- `"verdict"`: `"sufficient"`, `"partial"`, `"insufficient"` (as in AUDIT.json)
- `"next_action"`: `"stop"`
- `"stop_reason"`: `"contract_gap"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`

No other keys and no free text. Finish within 45 minutes.
