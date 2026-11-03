# s09 assessment: requirements for closing the gaps, and the state of each part (2026-11-03)

**Scope.** No test, no network, no box contact, no git, no credentials. I read s01–s08, centred on `s08/GAPS.json` and `s08/ASSESSMENT.md`, plus s07's assessment, `s01/ASSESSMENT.md:34–80`, `dut/pipeline/src/main.js:465–480`, `dut/pipeline/m5/SCHEMAS.md:320–339` and `m5/run6/control/box.json`. Bash was denied in this session, so I hashed nothing. I wrote only into `science/s09/`.

The owner approved closing the gaps on 2026-11-03. The operator will write the contract changes from `REQS.json` without reading prose, so `REQS.json` and `PARTS.json` use only the fixed vocabulary. This file is the prose behind them.

## 1. State of each part (`PARTS.json`)

The parts are s01's (`s01/ASSESSMENT.md:38–45`), unchanged through s08.

| Part | Status | Blocking gaps | Evidence for the status |
|---|---|---|---|
| P1 executable materials, correct outputs | measured | none | Run2: 12/12 jobs, 600 poses (`s01/ASSESSMENT.md:9`). Run6: 60/60 jobs complete, pins and all eight prepared hashes valid (`s07/ASSESSMENT.md` §A). The stated limit stays: zero anchors, so this is not independent scorer validation (`s01:20`). |
| P2 CPU/GPU agreement with justified tolerances | open_calibration | G1, G2, G3 | No tolerance has a basis yet (`s07` §D item 1). Run6 found GPU `docking.out` files not byte-reproducible (39 distinct hashes over 40 files, `s07` §B), so a tolerance/repeatability calibration (I2-style fixture analysis, ≤ USD 10 per the tree's card) must precede the final comparison. |
| P3 CPU/GPU acceleration | open_final | G1, G2, G3, G6 | Calibration screens done: (W_cpu+E)/(W_gpu+E) medians 2.311–2.570 (`s07` §A). No verdict, by the sealed rule. Agreement-gated, hence G3. Cost reporting, hence G6. |
| P4 dense affordable at common budgets | open_final | G1, G2, G6 | Tiers calibrated: rho 1.754 / 1.669 / 1.437 / 1.437; dense eligible at tiers 2–3 everywhere and tier 1 for 1dv1 and 1nr5 (`s07` §A, §C). The final answer needs completed arm costs against the sealed tiers and billed allocation cost. |
| P5 dense − standard rank-1 DockQ | open_final | G1, G2, G3 | Only the run2 historical diagnostic exists (`s01:13–16`). Needs the agreement-gated main study. |
| P6 dense − standard best-of-50 DockQ | open_final | G1, G2, G3 | As P5, reported separately. |

No part is `open_no_mechanism`: every open part is reachable once G1, G2, G3 and G6 are closed. No part is `negative`. C2's affordability component was dropped by a rule sealed before run6 (`s07` §C), but P4 is still carried in full by the physical card, so this is not a negative answer to P4.

## 2. Requirement for each gap (`REQS.json`)

### G2 (order 1, not deferrable): carry the card's protocol into the calibration record and back
- **Fields:** `name`, `unit`, `basis`, `value`, `differs_in`, `measured_by`, `phase`, `anchor`, `predictions`, `measured_value`. **Direction:** both.
- Why these: the record today carries `id, basis, value, differs_in, measured_by, cum_spend_through_measured_by, k_budget, phase{id,what,gate,stop_rule}, line` and only four prediction keys (`main.js:473–478`). The seed's comparisons need each measured quantity named with its unit (run6's W and E, s07 §A), the phase gate, the anchor and the full predictions including the decision rule. The measured value must come back so the card can be resolved by its own rule rather than by a ratio band.
- I left out `line`, `k_budget` and `cum_spend_through_measured_by`: they price the queue but do not carry the science.
- **Not deferrable** because the hand-copied brief (s04/s06) is checked only by hash. Once G1 lets a sealed protocol bypass propose's ballots, an immutable carryover is the only way to show the final run used the card's own rule.

### G3 (order 2, not deferrable): typed required evidence for tolerances
- **Criterion:** mixed (absolute and relative components: atol, rtol, eps_xyz, eps_eval, `s07` §D). **Between:** arm vs baseline (GPU standard against CPU standard at identical settings). **Margin source:** unknown. **Replicates:** two to five per arm.
- Margin source is `unknown` because the owner has not yet chosen among (a) independent fixture analysis, (b) a declared engineering tolerance labelled as not justified, or (c) agreement left unresolved (`s08` "What the owner must decide" item 2). The contract field must record which source was used.
- Two to five replicates per arm, because GPU outputs vary run to run (`s07` §B); a single GPU run cannot separate within-GPU noise from CPU/GPU difference. Run6's three retained blocks is the precedent.
- **Not deferrable:** the seed requires justified tolerances before comparative results. Without the field the physical card reads `no_unmeasured_input` while it is scientifically blocked (`s08` G3).

### G1 (order 3, not deferrable): named-arm comparison in m5
- **Arms:** three to four (CPU standard 3600, GPU standard 3600, GPU dense 54000; the budget tiers are conditions on these arms, not new arms). **Arm axis:** mixed (CPU vs GPU is implementation; standard vs dense is configuration). **Outcome:** mixed (runtime, result agreement, quality as DockQ, cost). **Arms from menu:** none (the menu holds data-parallel, batching, ensembles, multi-GPU, pipelining, `s01:24`). **Sealable:** yes. The arms, the tier formulas and the decision rules are already fixed in the cards and the run6 calibration; tolerances become fixed by the P2 calibration before the final measurement.
- It is third because it consumes G2's protocol and G3's evidence (`s08` G1 risk).

### G6 (order 4, not deferrable): billed allocation cost
- **Fact:** mixed. **Per:** run. The run must record allocation hours × price next to `run_box_usd`, with the box type (hardware identity).
- Per-arm wall and per-arm GPU activity are already recordable by the harness (run6 recorded W per job and block-D telemetry, `s07` §A), so the gap itself is run level.
- **Not deferrable**, against s08's "partial workaround": the run's own `C/box.json` for run6 has only `type, region, price_usd_h, started_utc`, with no `ended_utc` or `hours` (`m5/run6/control/box.json:1`). The refresh described at `SCHEMAS.md:333` did not happen, so the allocation end is not in the run record. Without G6, P3 and P4 cannot report billed allocation cost as the seed requires.
- Small change; it can go in any time before the final run.

### G5 (order 5, deferrable): authorised prior-run evidence
- **Missing:** prior run outputs. **Roles:** intake. **Wrapper fix:** partial. The wrapper's copy of the brief into the run folder (since run6) gives intake the brief, but not earlier run records.
- **Deferrable:** embedding history in the brief worked for run4 and run6 (`s08` G5). The cost is more hand work per brief and identity by hash only.

### G4 (order 6, deferrable): measure-route execution chain
- **Needed:** no. m5 stays the calibration executor: run4 PASS and run6 PASS via `--stop-after-reproduce` (`s08` G4). The P2 tolerance calibration can use the same route.

## 3. Why this order
G2 → G3 → G1 is a dependency chain: G1's sealed protocol is only trustworthy if it arrives intact (G2) and if its readiness includes the tolerance evidence (G3). G6 is small and independent; it must be in place before the final run's cost report. G5 and G4 have working substitutes and change nothing a final answer needs.

## 4. What each closure unlocks
- **G2 + G3:** the physical card and C2 can show `calibration_required` for the tolerance evidence instead of `no_unmeasured_input`, and the P2 calibration can be handed over with its gate and rule intact. This unlocks the P2 calibration.
- **G1:** after the P2 calibration, one m5 run can execute the ordered protocol: agreement gate (P2), acceleration (P3, gated on P2), tier affordability (P4), dense quality (P5, P6, gated on P2). This unlocks P2–P6 final answers.
- **G6:** the billed-cost component of P3 and P4.

## 5. Runs and cost after the gaps close (`status.json`)
**Expected m5 runs: two.**
1. The P2 tolerance/repeatability calibration. The I2 screen is ≤ USD 10 (`s07` §D, citing the tree result lines 290–295). Under the standing rule it needs no re-approval.
2. The physical-card final experiment, carrying C2's acceleration component on the same arms.

**Band: USD 20–100.** The card's DESIGN timers give about USD 29.6 (9 h × 3.29); its whole plan is USD 49.48, with a hard stop at 12 h or USD 100 (`s07` §D). With the ≤ USD 10 calibration, the planned total is about USD 40–60. s07's estimate from measured walls (under 25 minutes of compute for the main study) suggests the actual box time could be much lower. That is an estimate, not a measurement, so I report the band by plan. The final run projects above USD 20, so it needs owner approval before launch (`s08` decision 3).

## 6. What a completed answer to each part will look like
- **P1:** already stated: correct execution on the four pinned apo cases, 50 outputs each, with the limit of zero independent anchors. Each new run re-checks pins and hashes.
- **P2:** per case, all 50 ranked outputs compared CPU standard vs GPU standard within sealed tolerances of a recorded source, with GPU-vs-GPU repeat spread reported. The verdict is pass, fail, or unresolved if the owner picks option (c). Run2's agreement values stay exploratory.
- **P3:** per case, paired complete-workflow wall ratio CPU/GPU standard with its uncertainty against the sealed 1.05 threshold, GPU activity, and billed allocation cost. It is reported only if P2 passes, otherwise reported as gated.
- **P4:** per case and tier, whether GPU dense completes within the CPU-standard-derived budget. Tier-1 dense for 1aua and 1ax2 is recorded as unavailable, never as DockQ 0. Costs are given as allocation USD.
- **P5 and P6:** per case and eligible tier, signed dense − standard change in rank-1 DockQ and, separately, best-of-50 DockQ against the sealed effect margin. Negative cases are kept (for example a repeat of 1nr5's rank-1 loss). Pilot only, no biological claim.

## 7. Predictions and outcomes
s08 sealed no predictions, so `outcomes.json` is empty. No test here, so `predictions.json` is empty. Next action: stop, `contract_gap`.
