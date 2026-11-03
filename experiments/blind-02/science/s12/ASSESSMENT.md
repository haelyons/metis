# s12 assessment: content check of the revised G2 contract (U54, U55, U56), 2026-11-03

**Scope.** No test, no network, no box contact, no git, no credentials. Bash was denied in this session, so I hashed nothing and did not open the `metis-wt` worktree. I judged U54, U55 and U56 as quoted verbatim in the step brief. I read `science/s09/` (ASSESSMENT.md, REQS.json), `s10/` (ASSESSMENT.md, CHECK.json), `s11/` (ASSESSMENT.md, FIXES.json, NARROWING.md), the tree result `experiments/blind-02/20261103-0124-tree/out/result.json` (T below) at lines 253–412, `dut/pipeline/src/main.js:309–316, 434, 465–480`, `src/cost.js:154, 222–334`, `src/gates.js:201–254`, and the producer plan `T/../out/work/seed-20261103/seed/idea/370cabd5/producer.md:68, 97–100, 563–569`. I judge G2 only, not G1, G3 or G6. I wrote only into `science/s12/`.

## Verdict: sufficient (build as written)

Every REQS.json G2 field is carried, and every fix s11 chose in `s11/FIXES.json` is met, including the `other` (the decision rule), which the revision delivers by a different route from the one s11 proposed. I found no remaining problem from the code list. Under "Build notes" I list four points for the build. None of them blocks G2.

## Fields (s09/REQS.json G2: `name, unit, basis, value, differs_in, measured_by, phase, anchor, predictions, measured_value`, direction both)

| Field | Carried | Where |
|---|---|---|
| name, unit | yes | U55 copies them from the plan's `numbers` into each `required` item. U54 passes them to agents in `A/card_inputs.json` and to the score rows. For the admissible input they are "Maximum complete per-case evaluation runtime; unknown until agreement", "seconds" (`producer.md:564–565`). |
| basis, value, differs_in, measured_by, phase | yes | They are in the record (`main.js:473–474`), which is sealed unchanged in `C/card.json`. `basis` and `value` are copied into the rows, and `phase.gate` decides. |
| anchor | yes | The record's anchor is sealed. Only `anchor.what` reaches agents. The scored `anchor` block reports published, tolerance, measured, difference and passed, and the anchor never decides an input. For the admissible record `published_value` is a string (`T:393`), so the anchor is correctly null. |
| predictions | yes | The record's four keys are sealed and returned unchanged in `card_scored.json`. The decision rule is carried through U55's `judged.plan` (see the `other` fix below). |
| measured_value | yes | It is read by the sealed extraction rule into `rows[].measured_value`, then written to `resolved[].measured_value` and to the MEASURED `number`. |

`missing`: none.

## s11's fixes, one by one

### predictions
- **`other` (decision rule into the record): met.** s11 asked for `decision_rule` to be added to the record's `predictions` (`s11/ASSESSMENT.md`, §1). U55 does not do that. Instead it adds `judged.plan`, "the plan the record's `plan_usd` was evaluated from". That is the plan `main.js:434` evaluates, and its `predictions.decision_rule` is mandatory: `gate_plan` halts a plan whose decision rule has no number (`gates.js:211`). The plan therefore reaches every place s11 needed it:
  - it is sealed in `C/card.json` as part of the record unchanged, before any box command;
  - it is bound to the score by `card_scored.card_sha256`;
  - it is carried in `card_resolve.js`'s copy of the calibration array.

  G1 can therefore show that a final run used the card's own rule. A reader must take it from `judged.plan.predictions.decision_rule`, not from the record's `predictions`. This should be documented, but it is not a defect.
- **`seal_record_before_box`: met.** `C/card.json` and `C/card_seal.json` are written atomically before the intake call and before any box command. Every later read uses `C/card.json`. `score_card.py` and `card_resolve.js` both check the seal.
- **`return_in_scored`: met.** `card_scored.json` carries `predictions` unchanged and `card_sha256`.
- **`hide_from_agents`: met.** `A/card_inputs.json` explicitly excludes predictions.

### band_rule_unfit
- **`gate_decides`: met.** `gate_passed` is computed when `phase.gate.on` equals the item id, and the gate then decides (`decided_by: "gate"`). For `eval_runtime_s` (gate `<= 60`, `T:375–380`), a measured 100 s now refutes and a measured 15 s now holds. Those were the two contradictions s10 found (`s10/ASSESSMENT.md` §1).
- **`absolute_band_field`: met.** There are two sources. One is the plan's optional `band {abs: x}` (U55). The other is launch `bands`, which are sealed in `C/card.json` before the run. With them, zero values (`localized_faults`, `acceptance_contract_ready`, `T:283, 308`) and booleans become judgeable.
- **`sign_aware`: met.** A negative value gets `[value*k, value/k]`.

### write_back_unfit
- **`as_plan_numbers`: met.** Each measured entry carries a MEASURED number with the fields the plan schema requires for MEASURED (`command`, `output`, `output_line`, `machine`; `schemas.js:233–236`).
- **`rejudge_card`: met.** The replaced plan is re-run through the tree's own `cost_eval_plan(plan, given)` and `gate_plan(plan, ev, pick, args)`, with the `given` and `args` recorded at judging. That matches the tree's calls (`main.js:309, 434`), which pass no third `opts` argument. A MEASURED number with `differs_in: []` is no longer uncertain (`cost.js:154`), so `uncertain_after` drops it.
- **`all_runs_not_latest`: met.** Any `refuted` entry from any named run makes the card `refuted`. The re-judged value is the median over all runs.
- **`record_run_identity`: met.** Each entry records `run`, `pipeline_commit`, `box_type` and `box_started_utc`.

### leaks_or_biases
- **`hide_value`, `hide_predictions`, `hide_anchor_value`: met.** Agents see only `{id, name, unit, measured_by, phase.what}` and `anchor.what`. Card mode never names `C/` or `result`. For the admissible record none of those strings contains the value or the threshold of 60: `phase.what` is at `T:374` and the name at `producer.md:564`. The 60 appears only in `gate.value` and `gate.else` (`T:378–379`) and in the number's `rests_on`, and none of these reaches agents.
- **`extraction_rule_before_run`: met.** `card_extract.json` is declared by the harness agent and validated by the pipeline. It is sealed before the harness upload, never changed by a repair, and applied by `score_card.py`, not by a harness script.

`problems`: none.

## Build notes (not blocking; no code applies)
1. **Aggregated inputs.** `eval_runtime_s` is a maximum over cases (`producer.md:564`). The rule kinds (a JSON Pointer, or the last regex match) cannot take a maximum, so the harness must write the aggregate itself. The harness prompt says "no harness script computes, writes or asserts a card value." The build should word this so that writing a measured aggregate is clearly allowed and only targeting or copying a card value is forbidden. The alternative is an optional `agg` (`max|min|median|mean|sum`) on a rule over an array or all matches. Bias is not at stake here, because the harness is blind to the value.
2. **Card bands will be absent in practice.** U55 changes no prompt, so the producer never emits `band`. For non-positive or boolean inputs the operative route is launch `bands`. The science step that writes the m5 brief must set them, and they are sealed in `C/card.json`.
3. **Free-text leakage.** `phase.what` and `name` are plan prose. A future card could state a threshold in them, and the pipeline cannot strip numbers from prose. This does not happen for the admissible record. The brief given to the run must likewise contain no card values (that is the science step's responsibility).
4. **Run omission.** `card_resolve.js` judges only the run roots it is given. A later call that leaves out a refuting run would read `calibrated`. Earlier output files are never overwritten, so the negative result persists on disk. Science steps must pass every run that measured the card.

The admissible record today is `seed:idea:2` (`T:358–404`; one GUESS input, line USD 9.87). To give it `judged`, the tree must first be rerun with `--resume` on T's out dir. U55 states that this reproduces T's states and adds only the new fields.

## Predictions and outcomes
s11 sealed no predictions, so `outcomes.json` is empty. This step runs no test, so `predictions.json` is empty. Next action: stop, `contract_gap`. The revision is sufficient for G2, and building it is the operator's next step. G1, G3 and G6 remain open and were not judged here.
