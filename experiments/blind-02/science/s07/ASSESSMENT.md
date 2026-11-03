# s07 assessment — 2026-11-03

**Scope.** I reviewed the records offline: no network, no box contact, no git commands, no credentials read. I wrote only into s07. I read s01–s06; for s01–s03 I relied mainly on the consolidated records in s04–s06. Every Bash call was denied in this session, so I hashed and executed nothing. I computed every number below by hand from the quoted file values.

**Abbreviations.** Paths are relative to the repository root.
- **R6** = `experiments/blind-02/m5/run6`
- **TC** = `R6/agent/results/reproduce/out/timing_calibration.json`
- **B** = `science/s06/CALIBRATION_BRIEF.md` (the s04 request, relaunched by s06)
- **T** = `experiments/blind-02/20261103-0124-tree`
- **D** = `dut/pipeline`

**Definitions** (B:421, unchanged from s04):
- **W**: production wall per job.
- **E[c]**: evaluator reserve for case c, taken from run4 (historical).
- **M[c,a]**: max over blocks 1–3 of W[c,a] + E[c].
- **rho[c]**: M[c,gpu_dense] / max(M[c,cpu_standard], M[c,gpu_standard]).

## A. What the calibration measured

**The requested quantity** (B:315–427). Run6 was a timing-only calibration. It ran all three seed configurations on the four fixed apo cases, serially: one warm-up block (0), three retained blocks (1–3) and one diagnostic block D with GPU telemetry. It had no native access and computed no cross-arm comparison.

Per job, the brief asked for four measurements:
- **W**: production wall, from docking-process creation to 50 validated models.
- **D**: docking process wall.
- **P**: MEGADOCK's printed "Elapsed time".
- **R**: reconstruction wall.

From these, the science step computes M, rho, the physical-card tiers and C2's two screens (B:419–427).

**Completeness.** All 60 jobs completed:
- `"primary_jobs": 48, "primary_complete_valid": 48, "all_primary_complete": true` (TC:4844–4854).
- `"complete": 60, "failed": 0, "invalid_output": 0, "timeout": 0`.

**Measured values.** Retained W over blocks 1–3, in seconds, quoted from TC:4714–4843. Each cell gives the max, then the range.

| case | cpu_standard | gpu_standard | gpu_dense | E (run4, historical) |
|---|---|---|---|---|
| 1aua | 9.580 (9.379–9.580) | 3.284 (2.939–3.284) | 18.295 (18.009–18.295) | 1.97287 |
| 1ax2 | 8.996 (8.845–8.996) | 2.754 (2.727–2.754) | 16.195 (15.586–16.195) | 1.77213 |
| 1dv1 | 14.433 (14.257–14.433) | 4.254 (4.225–4.254) | 21.871 (21.786–21.871) | 2.57327 |
| 1nr5 | 14.517 (14.475–14.517) | 4.269 (4.115–4.269) | 21.914 (21.856–21.914) | 2.42460 |

**Spread.** Within-cell spread is small:
- CPU: at most 2.1% (1aua).
- Dense: at most 3.9% (1ax2, 15.586–16.195).
- GPU standard: at most 11.7% (1aua, 2.939–3.284). These walls are short (about 3 s), so a fixed reconstruction overhead of about 0.9–1.8 s weighs heavily in them.

Retained printed P values, from the per-job records in TC:
- CPU: 1aua 8.35/8.41/8.34; 1ax2 7.91/7.75/7.74; 1dv1 12.34/12.26/12.30; 1nr5 12.47/12.49/12.50.
- Dense: 1aua 16.62/16.83/16.57; 1ax2 14.17/14.61/14.83; 1dv1 19.58/19.44/19.46; 1nr5 19.68/19.60/19.62.

**Derived quantities**, by the sealed formulas (B:421):

| case | M_cpu | M_gpu | M_dense | rho | tier1 / tier2 / tier3 (s) | dense eligible at |
|---|---:|---:|---:|---:|---|---|
| 1aua | 11.553 | 5.257 | 20.268 | **1.754** | 17.330 / 23.107 / 40.536 | tiers 2, 3 |
| 1ax2 | 10.768 | 4.526 | 17.967 | **1.669** | 16.152 / 21.536 / 35.934 | tiers 2, 3 |
| 1dv1 | 17.006 | 6.828 | 24.444 | **1.437** | 25.509 / 34.012 / 48.888 | tiers 1, 2, 3 |
| 1nr5 | 16.942 | 6.693 | 24.338 | **1.437** | 25.413 / 33.883 / 48.676 | tiers 1, 2, 3 |

**Sensitivity to E.** Tier-1 eligibility for 1dv1 and 1nr5 depends on E. With E = 0, their rho would be 1.515 and 1.510. The break-even E is 0.44 s (1dv1) and 0.28 s (1nr5), against measured E of 2.57 and 2.42 s with a within-case spread of about 0.1 s (s04 §A). The classification therefore holds unless the GPU-pose evaluator were more than 5× faster than run4's CPU-pose evaluator. I see no basis for that, but it was not measured.

**C2 screens** (block-paired medians over blocks 1–3):
- (W_cpu+E)/(W_gpu+E): 1aua 2.311, 1ax2 2.360, 1dv1 2.484, 1nr5 2.570.
- W_cpu/W_gpu: 1aua 3.192, 1ax2 3.244, 1dv1 3.387, 1nr5 3.484.
- Padding margin, max W_dense − max W_cpu: 8.71, 7.20, 7.44, 7.40 s, against the 60 s allowance.

**GPU activity.** The anchors receipt shows `"gpu_busy_s": 257.0, "gpu_busy_known": true`, wall 749 s (`R6/control/receipts/0007-anchors.json:1`). Block-D telemetry has 144 samples at 1 s (TC:4868–4873); I did not analyse it.

**Configuration, case and box.**
- Pins (TC:8–25): MEGADOCK 9575280c… (commit check valid), cuda-samples v12.8.
- Binary hashes: megadock 4b85db6e…, megadock-gpu a8375a2a…, decoygen 74264710….
- All eight prepared hashes are valid (TC:84, 151–152). These are the four fixed apo cases.
- Argv matches B:387–391 exactly (TC:188–301).
- Host (TC:26–75): NVIDIA H100 PCIe (driver 570.148.08), Xeon Platinum 8480+, 26 CPUs, CUDA 12.8.
- Box: `gpu_1x_h100_pcie`, us-west-3, USD 3.29/h (`R6/control/box.json:1`).
- Every one of the 40 GPU-arm docking logs prints `# Using  26 CPU cores, 1 GPUs` (a grep count found 40 matches in 40 files). The CPU logs print `0 GPUs` (e.g. `block_1/cpu_standard/1ax2/docking.log:12`).
- Dense logs print `Set 54,000 rotational angles` (e.g. `block_1/gpu_dense/1aua/docking.log:14`).

**How intake and the harness interpreted the request.**
- Intake (Claude Opus understudy) returned `found:true, data:"available", stock_environment:true, size:"tiny", anchors_count:0` (`R6/agent/wf/agents/0001-intake/understudy/reply.txt:1`). It restated the protocol as written (`R6/agent/intake/EXECUTION.json:2–24`) and reported "contract_gaps: None identified in intake".
- The harness put the whole schedule in `run_command.sh`. `run_anchors.sh` ran it once in the background, sampled block-D telemetry from outside, and wrote `anchors_measured.json = {}` (`R6/agent/harness/run_anchors.sh:29–56,121–126`).
- W runs from immediately before `Popen` to after the 50 models are validated (`run_command.sh:221,268`). That matches B:409.
- Job directories are never overwritten (`:209–210`). The timeout is 600 s with a process-group kill (`:185–195`).
- The harness has no evaluator import and reads no native reference (grep for native/DockQ/reference finds only the scope string at `:331`).

**One departure, in validation strictness.** The brief asks for "printed GPU count 0 for cpu_standard and 1 for the GPU arms" (B:415). The harness checks only that 0 or 1 appears among *any* integers on log lines containing "gpu" (`run_command.sh:162–175`), so its check is weaker than specified. The logs themselves show the specified values (40/40 GPU logs say "1 GPUs"), so no job was mis-classified. Thread and rotation checks use the same membership pattern, and the logs show 26 threads and 3,600 or 54,000 rotations.

**Brief identity.** TC records `brief_sha256` 23101d08… and `section_sha256` 57699e1f… (TC:2–6). I cannot hash s04's file to confirm s06's copy was byte-identical. That check was the operator's precondition, and I find no record of it among the files I can read.

**Verdict: the calibration ran as requested** (`calibration_ran = as_requested`).

**Does Claude authorship (run6) versus Codex authorship (run4) affect comparability?** Not for the decisions here:
1. Both runs used the same CPU binary. Run4's setup log records `4b85db6e…  baseline-published/megadock/megadock` (`m5/run4/agent/results/reproduce/out/setup/setup.log:554`), identical to run6's. The prepared-input hashes are fixed by the brief, and the argv and thread environment are the same.
2. P is MEGADOCK's own timer, independent of who wrote the harness. Run6's retained CPU P medians against run4's single values are 8.35 vs 9.14, 7.75 vs 7.14, 12.30 vs 11.98 and 12.49 vs 11.86. That is −8.6%, +8.5%, +2.7% and +5.3%: mixed signs, consistent with host-to-host or run-to-run variation, not an authorship bias.
3. Authorship can matter for W and E, which come from different instruments:
   - Run4's E is a bash-wrapped fresh Python child scoring 50 CPU-standard poses (s04 §A).
   - Run6's W is a Python-parent wall that includes in-W validation.
   - The sealed formula combines them by design (B:330, 421). E is added equally to every arm, so it can only pull rho toward 1, and the break-even analysis above shows the tier classification holds for any E above 0.44 s.
4. One residual difference: run4 ran the CPU binary with `CUDA_VISIBLE_DEVICES=''`, run6 with `'0'` (B:387). The CPU binary prints 0 GPUs in both.

## B. What it supports and what it does not

**Supported, for these four cases on this box type at this tariff:**
- GPU-dense production walls are 1.67–1.75× the CPU-standard envelope (with E) for 1aua and 1ax2, and 1.44× for 1dv1 and 1nr5.
- Dense therefore fits the physical card's tier 2 everywhere and its tier 1 only for 1dv1 and 1nr5.
- No case has rho > 2.0. "Affordable within a CPU-standard-derived budget" is therefore not answered negatively for any case at tier 2.
- GPU-standard production walls are 2.3–2.6× shorter than CPU-standard walls once E is included, and 3.2–3.5× shorter without it.

**Not supported:**
- No acceleration verdict (B:322: "Timing ratios are calibration inputs for budget definition only").
- No CPU/GPU agreement, no tolerance and no quality effect.
- No billed cost: no invoice is on record.

**One within-arm observation** (hashes only; I opened no output contents and compared no arms):
- All 20 CPU-standard `docking.out` files across blocks 0–3 and D have exactly one SHA-256 per case. For example, 1aua is `0b422567…` at TC:315, 1484, 2662, 3176 and 4125.
- The 40 GPU-arm files give 39 distinct hashes: only gpu_standard/1nr5 blocks 3 and D coincide (`b83ebe1a…`, TC:3251, 4641).
- So GPU outputs are not byte-reproducible run to run. CPU outputs were byte-reproducible in all 20 jobs.
- I do not know whether the differences lie in scores, transforms or ranks.
- This matters to the owner's tolerance decision (§D). The physical card's anchor requires "exact ranked rotation/translation identity … Tie mismatch fails this strict gate" (T/out/result.json:263). C2 requires "identical ranked rotation/translation identifiers and ranks for all 50 outputs" (:394). Both gates presume GPU repeat determinism that the hashes do not show.

**Against the card's GUESS: `not_comparable`.**
- Neither kept card carries a GUESS or PROXY input for production walls.
- The physical card has `"required": []` and state `no_unmeasured_input` (T/out/result.json:255–259). Its tiers are DESIGN formulas over the calibrated walls (`T/out/work/seed-20261103/R1/physical/1fffee1a/producer.md:97`).
- C2's only GUESS is `eval_runtime_s` = 60 (band [20, 180]) (T/out/result.json:364–368). Run4 measured it at 2.573 s, outside the band on the low side (s04 §B). Run6 did not remeasure it, as B:330 required.
- So run6 measures a quantity the cards define by rule, not by guess. No band applies.

**Against s04's stated expectation.** s04 expected rho of "about 1.5–1.75 for every case, which would make dense eligible at tier 2 but not tier 1" (s04 §D). That held for 1aua and 1ax2. It did not hold for 1dv1 and 1nr5 (1.437).

**s06's predictions** (definitions in `science/s06/PREDICTIONS.md`; the same outcomes are in `outcomes.json`):

| ID | p | Outcome | Evidence |
|---|---:|---|---|
| Q1 | 0.80 | **true** | `control/stages/intake.json:1` PASS; reply `data:"available"` |
| Q2 | 0.65 | **true** | 48/48 primary complete and valid (TC:4844–4854); `control/stages/reproduce.json:1` PASS |
| Q3 | 0.80 | **true** | 40/40 GPU-arm logs print "1 GPUs"; `0007-anchors.json:1` has `gpu_busy_known:true`, `gpu_busy_s` 257.0 |
| Q4 | 0.80 | **false** | 1ax2 block 1 P = 7.91, above the +10% bound 7.854 on run4's 7.14. The other 11 values are inside their bands. |
| Q5 | 0.75 | **true** | Dense P medians 16.62 / 14.61 / 19.46 / 19.62 against 16.60 / 13.88 / 19.38 / 19.52: largest deviation +5.3% (1ax2) |
| Q6 | 0.88 | **true** | max rho 1.754 ≤ 2.0 |
| Q7 | 0.20 | **false** | rho 1.754 (1aua) and 1.669 (1ax2) are above 1.5 |
| Q8 | 0.95 | **true** | margins 8.71 / 7.20 / 7.44 / 7.40 s, all ≤ 60 |
| Q9 | 0.92 | **true** | medians 2.311 / 2.360 / 2.484 / 2.570, all ≥ 1.05 |
| Q10 | 0.60 | **false** | medians 3.192 / 3.244 / 3.387 / 3.484, all ≥ 3.0 |
| Q11 | 0.55 | **false** | every retained gpu_standard D−P is about 0.23–0.26 s, e.g. block 1 1ax2 1.6237−1.39 = 0.234 (TC:1553–1554) |
| Q12 | 0.85 | **true** | Totals usd 1.3673176027777778 (`operator/OPERATOR_TAKEAWAY.md:26`), a stage-wall estimate |
| Q13 | 0.88 | **true** | understudy transcript `"permission_denials":[]` (`agent/wf/agents/0001-intake/understudy/claude-1.json:1`); `agent/intake/brief.md` exists; `args.brief` lies inside `args.add_dirs` (`R6/args.json:3,7–9`) |
| Q14 | 0.65 | **true** | no `*-harness-repair` call (agents are only 0001-intake and 0002-harness); first setup rc 0 (`0006-setup.json:1`) |

Score: 10 true, 4 false, 0 null.
- The false forecasts on Q10 and Q11 show that I underestimated GPU-standard's speed and overestimated its process overhead outside MEGADOCK's timer.
- The Q4 miss is +0.8% beyond the band on one value.

**Informativeness: yes.** Every sealed decision branch resolved on complete data.

## C. Candidates against the decision rule sealed before the run (B:423–427)

- **Validity.** All 48 primary jobs completed and are valid, and the pins and prepared hashes are valid. The calibration is valid.
- **Physical branch `R1:physical:P1`: kept.** It goes forward with these tiers:
  - 1aua and 1ax2 (1.5 < rho ≤ 2.0): dense is eligible at tiers 2 and 3 only. Tier-1 dense is "recorded unavailable in any later study, never DockQ 0".
  - 1dv1 and 1nr5 (rho ≤ 1.5): dense is eligible at all three tiers.
  - No case is answered negatively on affordability.
- **C2 `seed:idea:2`: kept, but changed.**
  - *Affordability component: dropped.* For every case, max W_dense ≤ max W_cpu + 60 s, so its "primary affordability cap … is non-discriminating, and seed:idea:2's affordability component is dropped unless rewritten in a new sealed plan with a measured allowance" (B:426).
  - *Acceleration component: kept* for later agreement-gated testing, because every per-case median (W_cpu+E)/(W_gpu+E) is ≥ 1.05. As B:426 says, this is a calibration screen, not an acceleration verdict.
  - C2 thus carries only the seed's "execution acceleration" conclusion. The physical branch carries affordability and quality. The two complement each other; they do not compete.
- **Unchanged:** C1 and C3 stay REJECT, I2 stays halted, and C4 stays a reserve diagnostic. None of their decision inputs was measured here.

Counts for `status.json`: two candidates kept. No whole candidate was dropped (C2 lost one component).

## D. Next test: stop, `contract_gap`

**Calibration is done.** Both kept cards' calibration phases are now measured:
- The physical card's evaluator reserve came from run4; its warm production walls for all arms and cases came from run6.
- C2's `eval_runtime_s` came from run4; its timing screen came from run6.

No further measurement on an allowed route would change which candidate goes forward:
- rho sits away from the 1.5 and 2.0 thresholds by at least 0.06, the E break-even is about 5× below the measured E, and C2's screens pass by more than 2×.
- Another timing repeat would re-confirm tiers that are already robust.
- A tree run produces cards, not data.
- The measure route still has no execution controller (gap 3).

**Why the stop is `contract_gap`, not `needs_owner`.** The next informative step is each card's own next phase:
- freeze tolerances,
- then a fresh CPU/GPU agreement comparison,
- then the dense-quality main study.

No existing mechanism can run that:
- m5's full pipeline can only propose from its fixed method menu, so it cannot express a named-arm, agreement-gated, per-case rank1/best50 comparison (gap 1). This is the limitation the owner suspected in run2: run2 stopped at propose with `no_feasible_method`.
- The tree's measure route drops the arms and decision rules (gap 2) and cannot execute (gap 3).
- The reproduce-only m5 route may run calibrations only, not a card's full experiment (step rules).

An owner approval alone would therefore not make the experiment runnable.

**Decisions only the owner can make, once a mechanism exists:**
1. **Justified CPU/GPU tolerances** (atol, rtol, eps_xyz, eps_eval), which the seed requires before comparative results (seed line 13).
   - The cards require them from independent precision analysis or synthetic fixtures, never from fresh four-case differences (T/out/result.json:263).
   - Run6 adds one fact for that decision: GPU `docking.out` files are not byte-reproducible run to run (§B). The strict exact-identity gates in both cards may therefore fail GPU against GPU, before any CPU comparison.
   - Options:
     - (a) Commission the I2-style independent fixture analysis (I2's screen phase, ≤ USD 10, T/out/result.json:290–295) to derive bounds.
     - (b) Accept a declared engineering tolerance, explicitly labelled as not justified.
     - (c) Stop the agreement conclusion as unresolved, which the seed allows if reported.
2. **Approval of the full physical-card experiment.**
   - Its remaining DESIGN timers are freeze 1 h + agreement 2 h + main 4 h + report 2 h = 9 h. At USD 3.29/h that is about USD 29.6, above the USD 20 approval line. The card's whole plan is USD 49.48 (T/out/result.json:258), with a hard stop of 12 h or USD 100 (`producer.md:107,112`).
   - Measured walls suggest the main study's compute is far smaller: about 139 s per 12-job block (TC:4859–4864) plus about 12 × 2.2 s of evaluation. For 1 warm-up + 7 blocks that is under 25 minutes of compute. That is my estimate, not a measurement.
   - It would decide per-case best-of-50 and rank-1 DockQ changes from dense search at common budget tiers, after agreement passes.

**All calibration runs so far.** No invoice is on record for any run, so billed totals are unknown. "Span" means box start to last receipt × 3.29/h, before termination lag.

| Run | Requested by | Result | Stage-wall USD (operator Totals) | Allocation span |
|---|---|---|---:|---|
| run3 | s02 | intake FAIL (Codex) | 0.131 | 562.7 s ≈ 0.51 |
| run4 | s03 | PASS; evaluator max 2.573 s | 0.810 | 1,396 s ≈ 1.28 |
| run5 | s04 | intake FAIL (no file access) | 0.014 | 664.9 s ≈ 0.61 |
| run6 | s04 via s06 | PASS; timing calibration complete | 1.367 | 03:52:37Z → 04:27:20Z = 2,083 s ≈ 1.90 |

- Calibration total: about USD 2.32 stage-wall, or about USD 4.30 allocation span. All of it is inside the pilot's roughly USD 126 already-spent figure and far below the USD 2,000 cap.
- Run6's model inference cost USD 2.454 at list price (`R6/pipeline.log:9`); that is not box cost.

## E. Contract gaps (final list for the owner)

| # | Gap | Where | What it cannot express | Blocks (seed part) | Smallest change |
|---|---|---|---|---|---|
| 1 | m5 has no named-arm ordered comparisons | `D/m5/SCHEMAS.md` (PREDICTIONS 178–188, Propose 211–215, Evaluate 281–299); `D/m5/pipeline.js:1037–1038` | CPU/GPU agreement gating a dense-quality comparison, with per-case rank1/best50 at sealed common budget tiers and unavailable-arm outcomes, outside the fixed method menu | agreement, quality and acceleration conclusions (final experiment); the cause of run2's `no_feasible_method` | an optional named-arm comparison mode taking a sealed protocol (arms, ordered gates, tiers, metrics) instead of a menu proposal |
| 2 | The PLAN→measure handoff loses the protocol | `D/CONTRACT.md` §2.5, §5 "calibration"; `D/src/main.js:468–478`; `D/launch.js:71–96` | arms, decision rules, tiers, held-fixed settings; only scalar GUESS/PROXY ratio bands survive (run6's quantities have no GUESS at all, so the measure route could not even have compiled this calibration) | calibration on the measure route; the final experiment | an immutable full-PLAN handoff, keeping scientific decisions separate from price bands |
| 3 | The measure route has no execution controller | `D/launch.js:45–47, 83–107, 141–153` | a chained design→post stage run (m4's `measure.sh` is absent) | calibration on the measure route | a validated stage-argument chain with watchdog and ledger ingestion |
| 4 | The cost queue cannot represent scientific readiness | `D/src/cost.js:154–163`; `D/src/main.js:470–478`; `D/CONTRACT.md` §5 | unresolved tolerances (atol, rtol, eps_xyz, eps_eval) as required evidence; the physical card shows `no_unmeasured_input` while blocked | "justified numerical tolerances before examining comparative results" | typed required-evidence records, separate from numeric cost inputs |
| 5 | No route for authorised local evidence | `D/src/prompts.js:107–110`; `D/src/gates.js:313–327, 373–388`; `D/m5/pipeline.js:89–108` | intake following owner-authorised pointers to prior records; every brief must embed history (E, P, build commands) by hand | reproducible calibration identity across steps | a hashed, owner-authorised evidence bundle carried through the contracts |
| 6 | Cost accounting uses stage walls | `D/m5/pipeline.js:1007–1008` | "billed allocation cost": run6's takeaway gives USD 1.367 against an allocation span of about USD 1.90 | cost reporting in the final experiment | report the allocation span (existing `runBoxUSD`, `pipeline.js:62–68`) and the invoice |
| 7 | **Closed** (s06; confirmed by run6, Q13 true) | `D/m5/pipeline.js:85–92`; `D/idea/wf.js:128` | — | nothing | hardening only: stage the brief inside `pipeline.js` rather than in the launcher; reword "Never read experiments/" |

**Aggregate.** Six gaps are open (1–6).
- Gaps 2 and 3 block calibration on the tree's own measure route. This calibration was done through m5 reproduce-only instead.
- Gaps 1, 2, 4 and 6 block the final experiment.
- Therefore `gap_blocks = both`.
- The gap that stops progress now is **gap 1**, together with gaps 2 and 3: no mechanism can run the cards' agreement and main phases. Gap 4 is the contractual form of the owner's tolerance decision.

**Hardening note, not a gap:** run6's harness validated printed GPU, thread and rotation counts by set membership (`run_command.sh:160–175`), more loosely than the brief specified. A future protocol handoff should carry validation predicates as exact-equality checks.

## F. Narrowing

Unchanged: **no narrowing** (`NARROWING.md`). C2's affordability component was dropped by a rule sealed before the run. The seed's affordability question is still carried in full by the physical branch.
