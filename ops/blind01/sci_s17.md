
## Step s17 (draft the seed-neutral G1/G3/G6 contract text; no network; no new test)
Your step folder is `experiments/blind-02/science/s17/`. The owner approved (2026-11-03) that a content-reading agent drafts this contract, because the operator's two drafts from codes alone did not converge. Read `science/s13/` to `science/s16/` first: FINAL.json (s13), SHAPES.json (s15), the CHECK.json and ASSESSMENT.md of s14 and s16, and the operator's revised draft, verbatim in `science/s16/PROMPT.md` under "The contract section, verbatim". The card calibration contract it refers to (U54, `harness/card_extract.json` rules) is verbatim in `science/s12/PROMPT.md`; the rest of the m5 contract is `dut/pipeline/m5/SCHEMAS.md`.

Write `DRAFT.md`: exactly one section, starting with the line `## Sealed comparison (U57, U58)`, that replaces the operator's draft. Start from the operator's draft; keep its structure, style and every rule that is right; change what s14 and s16 found and resolve every `other` of s15. The operator will read DRAFT.md only after an independent audit finds no seed content in it, then commit it to `dut/pipeline/m5/SCHEMAS.md`, where anyone can read it. So it must be seed-neutral: a general mechanism any benchmark could use.
- Never name a program, library, model, dataset, case, input, file, path or output that is specific to the seed or its materials; never use a number, unit, margin, tolerance, threshold or reference value taken from the seed, its materials or the earlier steps' findings; never quote the seed. Generic formats in wide use (JSON, CSV, NumPy `.npy`, plain text) may be named when the rule is stated generally.
- Margins, thresholds, reference values, arms, inputs and metrics stay in the design file a science step writes before each run; the contract only defines their form and how they are applied.
- Rules must be executable by deterministic code without judgement, as the rest of SCHEMAS.md is.

Write `ASSESSMENT.md` for the owner (what you changed and why, per finding of s14/s16 and per `other` of s15, and what the owner must still decide), `NARROWING.md` ("No narrowing." with the reason, or what changed), `PREDICTIONS.md` ("No test; no predictions."), `predictions.json` `{"items": []}`, `outcomes.json` `{"items": []}` (s16 sealed none), and `NEXT.json` `{"action": "stop", "reason": "contract_gap"}`.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"draft_written"`: `"yes"`, `"no"`
- `"findings_resolved"`: `"all"`, `"most"`, `"some"` (of s16's missing items and problems)
- `"others_resolved"`: `"yes"`, `"partial"`, `"no"` (s15's three `other` codes)
- `"owner_decisions"`: `"none"`, `"margins_only"`, `"more"` (what the owner must still decide before a final run)
- `"next_action"`: `"stop"`
- `"stop_reason"`: `"contract_gap"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`

No other keys and no free text. Finish within 45 minutes.
