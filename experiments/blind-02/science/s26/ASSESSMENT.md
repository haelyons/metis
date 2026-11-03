# s26 assessment: card calibration choice after U54–U56 (2026-11-03)

**Scope.** This was an offline reading of the records only. I used no network, contacted no box, ran no git commands and read no credentials. I wrote only into `science/s26/`. I worked from the consolidated steps (s25, s13 `FINAL.json` and assessment, s09 `PARTS.json`, s07 §A–§D, s10–s12 on the card mechanism, and s02–s05 for runs 3–5) and read the following directly:
- the U54 and U56 sections of `dut/pipeline/m5/SCHEMAS.md:88–112`;
- every calibration record of `20261103-1712-tree/out/result.json`, called T below;
- the calibration headers of the replicate `20261103-1649-tree/out/result.json`, called T′ below.

**Verdict.** One record is eligible for card calibration: `seed:idea:2`, which has one input. A calibration of it is **not justified**. No possible result changes the arm or candidate that goes forward, the design of the main comparison, or the cost projection. Next action: **stop, `no_justified_test`**. The next informative test waits on the comparison mechanism (U57/U58).

## A. The cards (T = 20261103-1712-tree)

The parts are those of s09 (`science/s09/PARTS.json:2–7`):
- P1: operational reproduction (measured);
- P2: CPU/GPU agreement;
- P3: acceleration;
- P4: dense affordability;
- P5: rank-1 quality;
- P6: best-of-50 quality.

| Key (T line) | Parts | State | Required inputs (id, basis, measured by) |
|---|---|---|---|
| `R1:physical:P1` (255–260) | P2–P6; main design source of s13 `FINAL.json` | `no_unmeasured_input`, plan_usd 49.48 | none (`"required": []`, 259) |
| `R1:interp:I2` (1089–1147) | P2, as diagnostic tracing of disagreement | `not_judged` | `localized_faults`, GUESS, screen (1095–1121); `acceptance_contract_ready`, GUESS, seal (1123–1145) |
| `seed:idea:1` (2003–2008) | P2 | `rejected` | none |
| `seed:idea:2` (2803–2837) | P3 and P4, with P2 as a gate (C2 in s07) | **`calibration_required`**, plan_usd 100 | `eval_runtime_s`, GUESS, measured by phase `agreement` (2809–2835) |
| `seed:idea:3` (3805–3863) | P5 and P6 | `rejected` | `admissible_caps`, GUESS, calibrate (3811–3837); `agreement_pass`, GUESS, agreement (3839–3861) |
| `seed:idea:4` (4755–4760) | P3 and P4, as host-scheduling diagnostic | `no_unmeasured_input`, plan_usd 6.58 | none |

U54 accepts only `state: "calibration_required"` (`SCHEMAS.md:90`). So `seed:idea:2` is the only record the card mechanism can run. `R1:interp:I2` and `seed:idea:3` have GUESS inputs, but their states (`not_judged`, `rejected`) make intake fail with `parse`.

**`seed:idea:2`'s input against the card's own protocol.**
- `eval_runtime_s` is the "Maximum complete per-case evaluation runtime" in seconds, with `band: null` (T:2809–2812).
- The phase that measures it is the agreement phase (T:2821). That phase is a standard CPU/GPU matched comparison on every case and all 50 poses, with the complete evaluator walls measured.
- That phase's gate is on the input itself (T:2822–2827). Under U54 the gate therefore decides the input (`SCHEMAS.md:100–101`), and a launch band would never decide it.

**What runs 3–6 already measured of it:**
- **run3:** nothing. The calibration did not run, with 0/16 samples (`science/s03/ASSESSMENT.md:7`).
- **run4:** complete per-case evaluator walls for 50 poses, on CPU-standard outputs only. The runs used a fresh Python process per case and the same box type and pins: 16 walls with a maximum of 2.573 s (1aua 1.973, 1ax2 1.772, 1dv1 2.573, 1nr5 2.425; `science/s04/CALIBRATION_BRIEF.md:330`, `s04/ASSESSMENT.md:68`). That is far under the card's gate.
- **run5:** nothing. Intake failed and the allocation ran about USD 0.61 idle (`s05/ASSESSMENT.md:109,127`).
- **run6:** a timing screen of all three arms. It did not remeasure evaluator walls (`s07/ASSESSMENT.md:125`).

**Read against the card's protocol, the coverage is partial.** The CPU-standard half of the agreement phase's evaluator walls is measured. Evaluator walls on GPU-standard outputs, and the matched agreement comparison itself, are not.

**Can the earlier evidence stand in for a card calibration?** Not mechanically. No earlier run has `control/card.json`, `card_seal.json` or `card_scored.json`, and `card_resolve.js` reads only those (`SCHEMAS.md:109`). The card's state therefore stays `calibration_required`, and nothing earlier can be written back. Scientifically, run4 does bound the quantity. The evaluator's work depends on the 50 poses and the native structure, not on which binary produced the poses, so GPU-standard walls of the same order are expected. That is an inference, not a measurement.

**Stability across the two tree runs.** The calibration need is not stable. T′ has 5 records and none is `calibration_required`:
- `seed:idea:2` is `no_unmeasured_input` at USD 49.48 (T′:1788–1791);
- `R1:physical:P1` is `rejected` (T′:232–235);
- `seed:idea:3` is `rejected`, with two GUESS inputs measured by `calibrate` (T′:2724–2761);
- `seed:idea:4` is `rejected` (T′:3600–3603).

So `eval_runtime_s` is an artefact of one card draft, not a recurring load-bearing uncertainty of the question.

## B. Is a card calibration justified now? No: it changes nothing

The calibration's possible outcomes are:
- **holds** (measured value at or under the gate);
- **refuted** (above it);
- **not measured.**

None of them changes any of the following.

1. **Arm or candidate choice.**
   - The main design is the physical card's three arms (s13 `FINAL.json:1–5`).
   - s07 already dropped `seed:idea:2`'s affordability component under a rule sealed before the run (`s07/ASSESSMENT.md:162–165`). The card now carries only the acceleration component (K4), which the physical design also expresses.
   - A refutation would remove a card component that is already not going forward. A hold would restore nothing that was dropped: the drop rested on the cap being non-discriminating, not on the evaluator time.
2. **Comparison design.**
   - The physical card's evaluator reserve E already comes from run4 (`s07/ASSESSMENT.md:173`).
   - `seed:idea:2`'s cap formula uses the fixed allowance, not the measurement (seal phase, T:2940). The measurement only gates.
   - Inputs, replicates and warmup in s13 `FINAL.json` do not depend on it.
3. **Cost projection.**
   - None of the card's cost lines refers to `eval_runtime_s`. They are timer allotments (T:3440–3480), and the contingency line is the remainder of the budget (T:3486). The card says so itself: "All cloud costs are timer allotments, not runtime predictions" (T:2919).
   - U56's re-judging therefore reproduces the same `planned` value: `plan_usd_after` equals `plan_usd_before` whatever is measured.
   - That plan already equals the owner's whole combined ceiling, so this card cannot go forward unchanged next to any other spend.
4. **Cost to the ceiling, and order.**
   - The agreement phase's own allotment is 3 h on one H100 (T:2830–2834). That would take about a tenth of the USD 100 combined ceiling, away from the physical main plan (USD 49.48, `s13/ASSESSMENT.md:86`).
   - Running the agreement protocol now would also produce a fresh CPU/GPU comparison on the main inputs before tolerances are sealed. The owner's 2026-11-03 decision puts tolerance sealing, from independent disjoint fixtures, before the main comparison.

**Calibration is not justified.**

## C. Most informative card calibration

None (see B).

## D. The run

None. I wrote no brief and set no launch bands. Launch bands would be pointless in any case, because the gate decides this input (`SCHEMAS.md:100–101`).

## E. What is justified next and what it waits on

The next informative tests depend on the comparison mechanism (s23's contract, U57/U58), which is not available yet:
1. **Independent fixture analysis** on fixtures disjoint from the four cases. It fixes K1–K3's margins and eps_eval, sealed before the main comparison (owner decision 2026-11-03; s13 §5 option a).
2. **Overhead measurement** of the comparison mechanism before the rest of the USD 100 is committed.
3. **The agreement run (s13 run 1) and then the physical main run**, under the combined ceiling.

The tree and card route is exhausted for this seed:
- the one eligible record has no decision value (B);
- every other record is ineligible by state;
- a new tree run would produce cards, not data, and inference is scarce.

So stop with `no_justified_test`. The next step waits on the comparison mechanism.

## F. Narrowing

Unchanged. The root question is held fixed as in s01, with no part dropped (see `NARROWING.md`). The negatives already recorded remain as recorded:
- run2's menu result;
- C2's affordability component, dropped under its sealed rule;
- the non-reproducible GPU output hashes (s07 §B).

## Predictions and outcomes

s25 sealed no predictions, so `outcomes.json` is `{"items": []}`. The next action is `stop`, so `predictions.json` has no items.
