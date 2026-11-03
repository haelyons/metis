# s10 assessment: content check of the operator's G2 contract (U54), 2026-11-03

**Scope.** No test, no network, no box contact, no git, no credentials. I read `s08/` and `s09/` (GAPS.json, REQS.json, PARTS.json, ASSESSMENT.md) and the tree run the earlier steps used: `experiments/blind-02/20261103-0124-tree/out/result.json` (T below), its producer plans under `T/../out/work/seed-20261103/`, `dut/pipeline/src/main.js:465–480`, `dut/pipeline/CONTRACT.md:96–122` and `dut/pipeline/m5/SCHEMAS.md:53`. I judged the U54 section as quoted in the step brief. I did not open the `metis-wt` worktree. I judge G2 only, not G1, G3 or G6. I wrote only into `science/s10/`.

## Verdict: partial (build after three fixes and one added field)

Most of the design is sound. U54 does carry the card's record into the run unchanged and pinned by hash (`A/card.json` with `source_sha256`). It adds `name` and `unit`. It has the harness measure on the card's own phase protocol and keeps the card value out of the measured key, at least by instruction. It brings `measured_value` back into a resolved copy without touching `result.json`, and it never fails a stage because a card value turned out wrong. Those parts meet the fields and direction ("both") that `s09/REQS.json` sets for G2.

The remaining defects are all in what the run *decides* from the measurement, and in what the harness can see. Each can be fixed with one revision before anything is built.

### What the design carries, field by field (s09 REQS G2)
| Field | Carried? | Where |
|---|---|---|
| name, unit | yes | the CONTRACT.md change copies them from the plan's `numbers`. The plans give them, e.g. `eval_runtime_s` "seconds" (`work/…/seed/idea/370cabd5/producer.md:563–569`), `admissible_caps` "caps", `agreement_pass` "boolean" (`…/360caa42/producer.md:504–519`), `localized_faults` "faults", `acceptance_contract_ready` "boolean" (`…/R1/interp/8ce94062/producer.md:306–328`). So `record_lacks_units` does not apply. |
| basis, value, differs_in, measured_by, phase | yes | in the record, which is copied unchanged (`main.js:473–474`). `basis`, `value` and `phase.gate` are also used in the score rows. |
| anchor | yes | the record's `anchor` (`main.js:478`). The intake rule (numeric `published_value`, usual citation rules) is consistent with the m5 anchor rules. For the only admissible record the value is a string (`T:393`), so it is correctly not used. `anchor_rule_unfit` does not apply. |
| measured_value | yes | `card:<id>`, then `card_scored.json` rows, then `resolved` entries. |
| **predictions** | **no, only in part** | the record holds only `if_lever, if_not, noise_rule, expected` (`main.js:478`; `T:398–403`). The plan's `decision_rule` (`CONTRACT.md:103`; present in the plan, `370cabd5/producer.md:23`, which begins "Separate conclusions. Acceleration passes only after agreement and when 95% paired-median CPU/GPU complete-wall ratio…") is dropped before the record exists. U54 copies the record unchanged, so the decision rule never reaches the run or the write-back. |

### The record U54 can actually admit
Card mode accepts only `state: "calibration_required"`. In T exactly one record has that state: `seed:idea:2` (`T:358–404`), with one input. `eval_runtime_s` is GUESS, value 60 s, measured by phase `agreement`, line USD 9.87, 3 h (`T:365–387`). Its gate is `{on: "eval_runtime_s", op: "<=", value: 60}` (`T:375–380`). U54 can serve this record in one run (so `needs_several_runs` does not apply), and the write-back also handles several runs.

The reproduce anchors step runs the published protocol at representative scale and writes `out/anchors_measured.json` (`SCHEMAS.md:53`). A per-case evaluator wall is a measurement that step can produce: run6 recorded per-job walls in reproduce, `s07` §A. So `wrong_stage` does not apply. `protocol_not_runnable` does not apply either: the timing is measurable without the G3 tolerances, and the line fits the USD 20 rule. The physical card (`required: []`, `T:255–259`) and the tolerance calibration for P2 cannot enter card mode. That is G3's gap, which I do not judge here.

## Problems and the smallest fix for each

### 1. `band_rule_unfit`: the band contradicts the card's own gate on the admissible record
For `eval_runtime_s` the band is [20, 180] s, but the card's rule is the one-sided gate ≤ 60 s. Two cases show the contradiction:
- **Measured 100 s:** verdict `within_band`, yet the card's gate fails and its `else` says stop (`T:379`).
- **Measured 15 s:** verdict `below_band`, which counts as a refutation, yet the gate passes and the plan holds.

The other cards' inputs show the same unfitness. Value 0 gives `no_band` (`localized_faults`, `acceptance_contract_ready`, `T:283,308`). Booleans and counts (`agreement_pass` unit "boolean", `admissible_caps` value 1) get a band [0.33, 3] that has no meaning for them.

**Smallest fix:** keep the band as the price-check column, as now. Add a row field `refutes`, defined as `gate_passed === false` when `gate_passed` is not null, and otherwise as the band verdict (`below_band`/`above_band`). Count `refuted_total` from `refutes`. Keep `verdict` unchanged, so nothing that reads it breaks.

### 2. `write_back_unfit`: the resolved state is taken from the band alone
`card_resolve.js` sets `refuted`/`calibrated` from band verdicts only, while each `resolved` entry already carries `gate_passed`. For the admissible record, a measured 100 s would mark the card `calibrated` although its own gate stops it. Later steps and the tree would read the opposite of the card's rule. This is the outcome s09 asked to avoid: "resolved by its own rule rather than by a ratio band" (`s09/ASSESSMENT.md:20`).

**Smallest fix:** add `refutes` (from fix 1) to each `resolved` entry. The state becomes `refuted` when the latest entry for any required id has `refutes: true`. It becomes `calibrated` when the latest entry for every required id has a measured value and `refutes: false`, meaning the gate passed, or the value was within the band when there is no gate. Otherwise the state stays unchanged.

### 3. `leaks_or_biases`: the harness can read the card's value and gate threshold
U54 places the full record in `A/card.json` "so an agent restricted to the run's folders can read it". The harness and anchors-repair agents can therefore see `value` 60 and the gate threshold 60. The rule "never the card's own `value`" is only an instruction. A harness that knows the target can steer toward it: it can choose a scale or a timeout around 60 s, or stop a slow case. That is the bias a calibration must exclude.

**Smallest fix:** the pipeline writes two copies.
- `A/card.json` for the agents, holding the record with `value`, `phase.gate.value`, `predictions` and `anchor.published_value` removed. Intake still gets the `published_value` it needs for anchors through its own prompt.
- The full copy, for `score_card.py` and `card_resolve.js` only, in a pipeline-only location outside the agents' readable folders (e.g. under `C/`), with the same `source_sha256`.

The prompts then name only the blinded copy.

### 4. Missing field `predictions` (decision_rule)
**Smallest fix:** in `main.js:478`, add `decision_rule: plan.predictions.decision_rule` to the record's `predictions`, and say so in the same CONTRACT.md change that adds `name`/`unit`. U54 needs no further change: the record is copied unchanged, and the decision rule is not used for scoring (G1 consumes it). The decision rule falls under fix 3's removal of `predictions` from the agents' copy and stays in the full copy.

## Not problems (checked)
- `record_lacks_units`: every plan number has `name` and `unit` (`CONTRACT.md:114`; the plans cited above).
- `needs_several_runs`: the admissible record has one input. Multi-run write-back is specified.
- `wrong_stage`, `protocol_not_runnable`, `anchor_rule_unfit`: see above.
- Excluding `line`, `k_budget` and `cum_spend_through_measured_by` matches s09, which left them out of G2 on purpose.

## Predictions and outcomes
s09 sealed no predictions, so `outcomes.json` is empty. This step runs no test, so `predictions.json` is empty. Next action: stop, `contract_gap`. Once the operator revises U54 with the four fixes above, G2 can be built.
