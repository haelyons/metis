# s08 assessment: contract gap register (2026-11-03)

**Scope.** No test, no network, no box contact, no git, no credentials. I read s01–s07 (s07 in full; s01–s06 through their assessments, gap sections and status files) and the contract and code files named below. I wrote only into `science/s08/`. Bash was denied in this session, so I hashed nothing. Every `section` string in `GAPS.json` was copied from a line I read with the file tools.

**Parts** (s01's definitions, `science/s01/ASSESSMENT.md:38–45`, restated in `s02/ASSESSMENT.md:9`):
- P1: executable materials and correct outputs
- P2: CPU/GPU scientific agreement at identical standard settings, with justified tolerances
- P3: CPU/GPU execution acceleration at standard settings
- P4: whether dense search is affordable at common budgets
- P5: dense-minus-standard rank-1 DockQ
- P6: dense-minus-standard best-of-50 DockQ

**Numbering.** This register orders the gaps by importance, so its numbers differ from s07's list:

| s08 | s07 |
|---|---|
| G1 | 1 |
| G2 | 2 |
| G3 | 4 |
| G4 | 3 |
| G5 | 5 |
| G6 | 6 |

s07's gap 7 was closed by `add_dirs` (s06; run6 Q13 true), so it is not in the register.

## The gaps

### G1: m5 cannot compare named arms (`dut/pipeline/m5/SCHEMAS.md`, "Propose, independent votes, and the one-shot gate")

**What it cannot express.**
- Propose ranks only methods from a fixed menu whose sealed headroom is at least 1.05 (`SCHEMAS.md:213`). When none qualifies, the run stops at propose with `no_feasible_method` (`:215`; `m5/pipeline.js:1037–1038`). Run2 ended exactly this way.
- The m5 model is one baseline against one method. That cannot hold the seed's shape:
  - three named configurations (CPU standard, GPU standard, GPU dense);
  - an ordered gate, where CPU/GPU agreement must pass before dense quality is examined;
  - per-case rank-1 and best-of-50 DockQ reported separately;
  - common budget tiers, where an arm that does not fit is recorded as unavailable, never scored as DockQ 0.
- Evaluate's curve already has unavailable-arm points (`:321`) and deterministic tolerances (`:282`), but only for a single baseline/method pair.
- The route's own finding is bounded: it "does not show that no method could speed up the workload" (`:215`). This is the evidence behind the owner's impression: run2 showed a limitation of the menu, not an answer to the seed.

**Blocks:** the final experiment for P2, P3, P4, P5 and P6.

**Existing workaround: partial.** m5 reproduce-only with a hand-written brief ran named arms descriptively (run6: 60/60 jobs complete). But it has no sealed gate, scorer or verdict, and the step rules restrict it to calibrations.

**Smallest change: large.** An optional named-arm comparison mode. It would take a sealed protocol (arms, ordered gates, budget tiers, per-case metrics, rules for unavailable arms) in place of the menu proposal, and reuse evaluate's existing seal, integrity and scorer machinery.

**Risk.** It widens what a seal can contain. Propose's deterministic gate and skeptic ballots would be bypassed for this mode, so the sealed protocol's author becomes the only judge. That makes G2 (a faithful handoff) and G3 (typed readiness) preconditions, not extras.

### G2: the calibration record drops the card's protocol (`dut/pipeline/src/main.js`, the comment beginning "calibration state per card (2026-10-21)")

**What it cannot express.**
- The record carries `required[]`, `anchor` and only `if_lever, if_not, noise_rule, expected` from `predictions` (`main.js:468–478`). It drops:
  - `decision_rule`, although the PLAN has it (`CONTRACT.md:103`);
  - `arms`, `held_fixed`, the budget tiers and the phase gates other than the one tied to each measured input (`CONTRACT.md:101,108,112`).
- `launch.js` measure therefore compiles scalar ratio bands only (`launch.js:55–57`).
- Run6's quantities had no GUESS or PROXY input at all (the physical card shows `required: []`, s07 §B). The measure route could not even have compiled this calibration.

**Blocks:** calibration on the measure route and the final experiment, for P2–P6.

**Existing workaround: partial.** The science step copied the card's protocol into a calibration brief by hand (s04 and s06 `CALIBRATION_BRIEF.md`). Fidelity then depends on that step, and it is checked only by hash.

**Smallest change: medium.** Carry the whole PLAN (or its hash and path) unchanged in each calibration record, and keep the scientific decision separate from the price-band check.

**Risk.** Larger records. A downstream stage could start reinterpreting a decision rule unless the record is marked immutable.

### G3: readiness cannot record missing scientific evidence (`dut/pipeline/CONTRACT.md`, "2.5 PLAN (producer; also the EXTRACT output)")

**What it cannot express.**
- A PLAN number is a typed cost input (`CONTRACT.md:113–122`). An unresolved tolerance (atol, rtol, eps_xyz, eps_eval) is not a number with a price, so it never enters `required[]`.
- The physical card therefore shows `no_unmeasured_input` while it is scientifically blocked (s07 §B and §D). The seed's requirement of justified tolerances before comparative results has no field.

**Blocks:** the final experiment. Directly for P2. Through the agreement gate also for P3 (C2's acceleration is agreement-gated) and for P5 and P6 (the physical card's main study).

**Existing workaround: partial.** Steps record it in prose (s04 §D, s07 §D), and it stays an owner decision.

**Smallest change: medium.** A typed `required_evidence` list in the PLAN (id, kind such as `tolerance`, the phase that must supply it, how it may be justified), surfaced as a separate calibration state.

**Risk.** It adds a new halting state to the tree. Cards that pass today would read as blocked, and the judges' and critic prompts would need to know the field.

### G4: the measure route has no execution chain (`dut/pipeline/launch.js`, the comment "the stage's args file as measure.sh wrote it …")

**What it cannot express.**
- `stage` reads an args file that m4's `measure.sh` wrote (`launch.js:142,154`). That script is not available.
- So design → gate → build → tests → review → launch → post cannot be chained from a compiled measure folder.

**Blocks:** calibration on this route only. The calibrations so far were for P3 and P4.

**Existing workaround: full**, for the calibrations this seed needed. m5 `--stop-after-reproduce` ran them: run4 PASS and run6 PASS.

**Smallest change: large.** A validated stage-argument chain with a watchdog and ledger ingestion.

**Risk.** It is a new controller with a new failure surface. Its value here is low while the m5 workaround holds.

### G5: no route for authorised local evidence (`dut/pipeline/m5/SCHEMAS.md`, "A/intake/ (written by the intake agent; checked by the pipeline)")

**What it cannot express.**
- Intake is told "Never read experiments/, operator/, or control/" (`m5/pipeline.js:92`). It can read the brief through `add_dirs` (run6), but it cannot follow owner-authorised pointers to earlier records.
- Every brief therefore embeds history by hand: run4's E, run4's printed timings, the pins.

**Blocks:** both calibration and the final experiment. In this seed it touched the P3 and P4 calibrations.

**Existing workaround: partial.** Embedding plus `add_dirs`.

**Smallest change: medium.** An owner-authorised, hashed evidence bundle that intake may read and that later stages carry.

**Risk.** It weakens intake's isolation. Records outside the bundle must stay unreadable, and the bundle's hash must be sealed.

### G6: run cost is not the billed allocation (`dut/pipeline/m5/SCHEMAS.md`, "Compute metadata")

**What it cannot express.**
- `run_box_usd` is the intersection of the run window with the allocation (`SCHEMAS.md:337`). It leaves out box time before the run starts and after takeaways ends.
- The seed asks for billed allocation cost, which is neither number.

**Correction to s07.** s07 called run6's USD 1.367 a stage-wall figure. In fact:
- Run6's stage USD sums to 0.858, from reproduce only (`run6/operator/OPERATOR_TAKEAWAY.md:7–14`).
- The Totals figure, 1.3673 (`:26`), matches the run window: 1,495.58 s × 3.29/3600 = 1.3668. So it is `run_box_usd`, not a stage sum.
- The gap stands, smaller than stated: about USD 1.90 by allocation span (s07 §D) against 1.37 reported.

**Blocks:** the final experiment's cost reporting for P3 and P4.

**Existing workaround: partial.** After `down`, `box.json` holds the allocation's `hours` (`SCHEMAS.md:332`). No invoice is on record.

**Smallest change: small.** Report `box.json` `hours` × price as allocation USD next to `run_box_usd`, and the invoice when available.

**Risk.** Negligible. When one allocation serves several runs, the cost is shared and would be double-counted unless it is labelled per allocation.

## Order I would close them in

1. **G2** (medium). It is a precondition for any sealed protocol to reach execution faithfully, and it is low-risk.
2. **G3** (medium). It gives the tolerance decision a field, so readiness is checkable.
3. **G1** (large). This is the change that makes P2–P6 runnable. It consumes G2's protocol and G3's evidence.
4. **G6** (small). It can go in at any time, before the final experiment's cost report.
5. **G5** (medium). Convenience and identity; the hand-embedding workaround works.
6. **G4** (large). Only if the owner wants the tree's own measure route; m5 covers calibration fully.

## What the owner must decide

1. **Whether to approve the contract change G1, with G2 and G3 as its preconditions.** Without it, the seed can be answered only in part:
   - P1 is established (s01).
   - P3 and P4 have calibration screens, but no verdicts (s07 §B).
   - P2, P5 and P6 stay unanswered.

   If the owner declines, the alternative is to accept that partial answer.
2. **Once a mechanism exists, the tolerance basis** (s07 §D):
   - (a) an independent fixture analysis;
   - (b) a declared engineering tolerance, labelled as not justified;
   - (c) leave the agreement conclusion unresolved.

   Run6's GPU outputs were not byte-identical from run to run (39 distinct hashes over 40 files), which bears on this choice.
3. **Approval for the full physical-card experiment.** It is projected above the USD 20 line: about USD 29.6 in timer terms, USD 49.48 by plan (s07 §D).

Recommendation: approve G2 → G3 → G1 as one contract change (`owner_decision = approve_contract_change`).

## Predictions and outcomes

s07 sealed no predictions, so `outcomes.json` is empty. This step runs no test, so `predictions.json` is empty. Next action: stop, `contract_gap`.
