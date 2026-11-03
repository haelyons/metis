# s04 assessment — 2026-11-03

This was an offline record review only: no network, no box contact, no git commands, no credential reads, and I wrote only into s04. I read s01–s03 before run4. Paths are relative to the repository root. Abbreviations: **R4** = `experiments/blind-02/m5/run4`, **R2** = `experiments/blind-02/m5/run2`, **S3** = `experiments/blind-02/science/s03`, **T** = `experiments/blind-02/20261103-0124-tree`, **D** = `dut/pipeline`. The shell was unavailable in this session, so nothing was hashed or executed locally. All numbers are quoted from files.

## A. What the calibration measured

**Requested quantity** (`S3/CALIBRATION_BRIEF.md:339–347`): T = the maximum of 16 complete evaluator subprocess walls, in seconds. Each wall covers one fresh Python process that scores all 50 saved CPU-standard poses for one case. The 16 walls are 4 serial blocks × 4 cases. Each wall runs from process creation to after child exit and the output-file check. The run also had to produce native-self smoke DockQ = 1 ± 1e-6, CPU standard at 3600 rotations with 26 OpenMP threads, the four fixed apo cases, verified historical prepared hashes, and the GPU idle.

**Measured value** (`R4/agent/results/reproduce/out/calibration.json:145–282`):

- T_s = **2.5732721009999295 s** (1dv1, block 3). The screen was set to `allowance60_screen: "pass"`.
- All 16 records have `status: "complete"` and `n_scored: 50`.
- The 16 walls span **1.6709842010000102 s** (1ax2, block 3) to **2.5732721009999295 s**.
- Per-case maxima: 1aua **1.9728683570000385**, 1ax2 **1.7721286510000027**, 1dv1 **2.5732721009999295**, 1nr5 **2.4245986219999622** s.
- Within-case spread was small. 1aua: 1.92286–1.97287. 1ax2: 1.67098–1.77213. 1dv1: 2.47441–2.57327. 1nr5: 2.37378–2.42460. The largest within-case range is 0.101 s (1ax2), about 6% of its minimum.
- Native-self smoke DockQ was **1.0** for all four cases, with walls 1.32–2.07 s (`calculation.json:87–143`).
- Stage walls: docking plus reconstruction **45.19964612500007 s**; whole anchors script **92.87927559499997 s** (`:284–287`), inside the 121 s anchors receipt (`R4/control/receipts/0010-anchors.json:1`).

**Configuration, case and box:**

- The build was CPU OpenMP with `USE_GPU=0 USE_MPI=0` (`calibration.json:11`; build at `R4/agent/results/reproduce/0006-setup.log:133–176`, linking only `-lfftw3f`).
- Each case ran the exact requested argv with `-r 3600` (`R4/agent/harness/run_command.sh:27`).
- MEGADOCK printed: `# Using OpenMP parallelization: 26 threads.`, `# Using  26 CPU cores, 0 GPUs`, `>Ligand rotation =  3600 /  3600`. Printed Elapsed was 9.14 / 7.14 / 11.98 / 11.86 s for 1aua / 1ax2 / 1dv1 / 1nr5 (`R4/agent/results/reproduce/out/run_command.log:7,15,45,59,115,171,227`). Run2's CPU-standard docking times were 9.11 / 7.28 / 11.81 / 11.87 s (`m5/run2_trace/REPORT.md:105–108`), so the docking timing reproduces within 2%.
- Pins were MEGADOCK 9575280 and PINDER ebeb28a, with `prepared_hashes_valid: true`. The setup asserts each prepared file against the historical hash before docking (`R4/agent/harness/setup.sh:719–720`).
- The host had 26 logical CPUs (Xeon Platinum 8480+) and 231,924,760 kB RAM (`0006-setup.log:456–491`).
- Box: `gpu_1x_h100_pcie`, us-west-3, USD 3.29/h (`R4/control/box.json:1`).
- Evaluator: `BiotiteDockQ(... ['R'],['L'],['R'],['L'], parallel_io=False)`, one fresh `python -` child per case per block. Timing ended after the size check of the fsync'd CSV (`R4/agent/harness/run_anchors.sh:11–46,69–88`).

**Zero GPU-seconds is correct here: it shows the CPU-only path the request named, not missing telemetry or a reduced case.**

- Every receipt reports `"gpu_busy_s": 0.0, "gpu_busy_known": true` (e.g. `0010-anchors.json:1`), so GPU telemetry was present and read zero.
- The harness sets `CUDA_VISIBLE_DEVICES=''` (`run_command.sh:6`, `run_anchors.sh:8`), and the binary reports 0 GPUs.
- Run2's 49.6 GPU-s came from its GPU arms. Run4 had none, as requested ("allocated GPU is paid for and remains idle", `S3/CALIBRATION_BRIEF.md:325`).
- Scale was not reduced: 4 cases × 3600 rotations × 50 poses, 50 rows each (`run_anchors.sh:110–125`).

**The setup's first rc 255.** Receipt `0006-setup.json:1` records rc 255 after 154 s, not a timeout. Its log runs through apt, both clones, the CPU build, the venv, the checks JSON and both binary hashes, then stops (`0006-setup.log:554–555`). The prepared-hash assertions ran before that point.

The next command was `megadock -h`. MEGADOCK 9575280 prints valid usage and then exits 255. The repair agent reported exactly that: "Final `megadock -h` printed valid help, then returned 255" (`R4/agent/wf/agents/0003-harness-repair/reply.txt:2`). The repaired setup accepts 255 only together with valid usage text (`setup.sh:748–761`), and its rerun logs `MEGADOCK help exit status: 255` (`0009-setup.log:288`). Run2's setup had already handled this behaviour (`R2/agent/harness/setup.sh:74–79`).

So this was a harness bug, not a scientific or data failure. The repair changed nothing in the workload, settings or protocol. Second setup: rc 0 in 32 s (`0009-setup.json:1`).

**Intake and harness interpretation.** Intake passed: `found:true, data:"available", stock_environment:true, anchors_count:0, licence:"unknown"` (`R4/agent/wf/agents/0001-intake/reply.txt:1`; `control/stages/intake.json:1`, 121.39 s). The harness implemented the request almost literally:

- It ran four fixed serial blocks with no untallied warmup and fresh subprocesses.
- It enforced a 180 s timeout with a censored lower bound, and a 5,400 s science stop.
- It ran the native-self smoke before the blocks.
- It wrote the requested `calibration.json` fields (`run_anchors.sh:59–67,131–136`).

Small departures, none of which changes the endpoint:

1. The timed child is launched through `bash harness/run_anchors.sh --child` before `exec python`. This adds a bash start-up to each wall, which makes the walls slightly conservative.
2. A mapping child and a smoke child ran before block 1, so block 1 was not the first Python import on the box. The brief allowed this ("Do not flush OS caches or treat later blocks as cold-disk samples").
3. `allocation_identity` was recorded as null (`calibration.json:81–84`).
4. The harness exported `CUDA_VISIBLE_DEVICES=''` rather than only passing inherited variables through. That is consistent with the requested idle GPU.

Anchors were empty (0 of 0, `anchors_scored.json:1–7`). The m5 reproduce PASS is therefore not independent scientific validation.

**Verdict: the calibration ran as requested.** The request itself was deliberately narrower than the card input: CPU-standard outputs only, not the card's CPU/GPU agreement phase (`S3/CALIBRATION_BRIEF.md:319`). That is the design, not a narrowing at execution.

**Cost.** The operator's total is **USD 0.8096763111111112** = 885.39 s of stage walls × 3.29/h (`R4/operator/OPERATOR_TAKEAWAY.md:24–26`). That formula sums receipt and stage walls (`D/m5/pipeline.js:1007–1008`). The allocation ran from box start at 02:29:59Z (`box.json:1`) to the last receipt end at 02:53:15Z (`0011-reproduce-freeze.json:1`), which is 1,396 s, about **USD 1.28** at the list rate, before termination lag. No invoice is on record, so the billed total is unknown.

## B. What it supports and what it does not

**Supported:** on CPU-standard outputs for these four cases, a complete fresh-process evaluation of 50 poses takes at most 2.57 s. That is 23.3× below the card's 60 s allowance. The CPU-standard part of the 60-second screen passes.

**Against the card's GUESS:**

- `eval_runtime_s` = 60 GUESS (`T/out/result.json:364–368`). The compiler's 3× GUESS band is [20, 180] s (`D/launch.js:71–78,90–99`). 2.57 s falls **outside the band, on the low side**: the GUESS was too pessimistic by about 23×.
- The separate budget gate `<= 60` (`result.json:375–380`) **passes**.

These answer different questions, as s02 and s03 noted. The value is comparable to the card input with one caveat: the card's input covers evaluation of all arms in its agreement phase. Evaluator work depends on the pose and native atom inventories. GPU-standard and dense poses are rigid transforms of the same prepared inputs, so their evaluator cost should be the same. That is my inference, not a measurement. The card record is not marked fully resolved (S3 rule).

**Not supported:**

- No CPU/GPU agreement, no acceleration, no dense affordability, no quality effect.
- No justified numerical tolerance.
- The CPU-standard DockQ values that run4 wrote are owner artifacts. I did not inspect them, and they are not a comparison.

**s03 predictions** (definitions in `S3/PREDICTIONS.md:9–15`; also in `outcomes.json`):

| ID | p | Outcome | Evidence |
|---|---:|---|---|
| Q1 | 0.70 | **false** | The definition says "False for observed setup/anchors failure". Setup was observed to fail once (rc 255, `0006-setup.json`) before the repaired rerun passed. The "true iff succeed" clause is also met by the final state, so the definition is ambiguous when a repair occurs. Because the rules forbid choosing a reading after seeing the result, I applied the literal failure clause, the reading less favourable to the forecast. I record that no protocol substitution occurred. |
| Q2 | 0.60 | **false** | All 16 walls are valid; maximum 2.573 s, below [5, 30]. |
| Q3 | 0.80 | **true** | All 16 walls ≤ 60 s; pins, outputs and smokes valid. |
| Q4 | 0.80 | **true** | All four native-self DockQ = 1.0 (`calibration.json:96–140`). |
| Q5 | 0.85 | **null** | No billed total through termination. USD 0.81 is a stage-wall estimate and USD 1.28 an allocation-span estimate; the rule excludes both. |
| Q6 | 0.80 | **true** | Follows Q3. |
| Q7 | 0.85 | **true** | Intake PASS with `data:"available"`. |

The result is informative for the question it was designed to answer. Its decision value was medium, as s02 and s03 forecast: a pass keeps both candidates.

## C. Candidates against s03's decision rule

s03's rule, fixed before the run (`S3/CALIBRATION_BRIEF.md:349–353`): "All 16 valid complete walls ≤ 60 with setup/smoke/pins valid: retain C2 provisionally, along with physical branch. Do not mark the full eval_runtime_s record resolved."

- **Kept (two):**
  - **C2** (`seed:idea:2`), provisionally.
  - **The physical branch** (`R1:physical:P1`). Its "synthetic evaluator reserve" now has a measured counterpart: real 50-pose evaluations at ≤ 2.57 s per case on poses with the same atom inventories.
- **Dropped:** none. C1 and C3 remain REJECT and I2 remains halted. C4 remains a reserve diagnostic. None of these is changed by this result.

**What changes, without dropping anything.** C2's primary affordability cap is "CPU-standard calibration envelope", A = cold retrieval + conservative setup + max CPU-standard production wall + **60 s evaluator allowance** (`T/out/work/seed-20261103/seed/idea/370cabd5/producer.md:23,89`). The allowance is now known to be about 23× the measured evaluator cost. Historical dense GPU docking per case was 13.9–19.5 s (`run2_trace/REPORT.md:105–108`). A dense workflow would therefore fit inside A by padding alone, so C2's primary affordability test cannot discriminate.

s03's rule already says that changing the allowance needs a new sealed plan. I therefore keep C2 provisionally and do not rewrite it. The next test seals a check that would drop C2's affordability component if the padding is confirmed (Q8 in `PREDICTIONS.md`).

The physical card's tiers (0.75×, 1× and the dense-inclusive maximum of 2 × calibrated warm wall, `R1/physical/1fffee1a/producer.md:97`) do not have this problem. Its calibration screen is the remaining measurement that tells which tiers dense can enter.

## D. Next test

**One m5 reproduce-only timing calibration: GPU build, all three configurations, four cases, one warmup plus three retained blocks, no native access, no cross-arm comparison.** The brief is `CALIBRATION_BRIEF.md`, run with `--stop-after-reproduce`.

This is the calibration phase that both kept cards already specify: the physical card's "1 warmup plus 3 repeats per arm, study native scoring disabled" (`producer.md:85`) and C2's "time all 3 configurations across all 4 cases without native DockQ" (`370cabd5/producer.md:78`). It is also the seed's own step, "a small runtime calibration to define feasible budgets" (`m5/BRIEF.md:17`).

**What it measures.** For each job: production wall W (docking process through 50 validated reconstructed models), docking process wall D, printed Elapsed P, and reconstruction wall R. One extra diagnostic block records 1-second GPU telemetry. The evaluator reserve E is taken from run4.

**What each result decides** (sealed in the brief):

- Per-case rho = M_dense / max(M_cpu, M_gpu):
  - ≤ 1.5: dense is eligible at all physical tiers.
  - 1.5 to 2.0: tiers 2 and 3 only.
  - > 2.0: dense-defined tier only, so "affordable within a CPU-standard-derived budget" is answered negatively for that case.
- C2's affordability component is dropped if dense fits under CPU + 60 s on every case (the padding check).
- C2's acceleration component is kept only if the median per-case (W_cpu + E)/(W_gpu + E) ≥ 1.05.
- An incomplete calibration means unknown. No reruns beyond the schedule.

**Expected result.** Historical numbers suggest rho of about 1.5–1.75 for every case, which would make dense eligible at tier 2 but not tier 1. That would decide that the physical branch, not C2, carries the dense-affordability and quality comparisons.

**Where and cost:**

- Same box type, same pins, prepared-hash gate kept.
- Run4 used 1,396 s of allocation. This run adds a GPU build and about 60 short jobs (historical docking-only times per case: CPU 7.1–12.0 s, GPU 1.4–1.9 s, dense 13.9–19.5 s).
- Projection: about 1 allocated hour = USD 3.29, plus USD 0.71 uncertainty = **about USD 4 all-in**.
- Hard stop at 2 h or USD 10. New science stops at 75 min. This is well under the owner's USD 20 approval threshold.
- Decision value: **medium**. The test does not resolve tolerances, so no final verdict follows from it.

**Why this and not stop:**

- The comparison is expressible: m5 reproduce-only with a fresh harness carried the CPU calibration end to end (run4), and run2 built and ran both binaries on this box type (`R2/agent/harness/setup.sh:52–80`, copied into the brief).
- Because the brief forbids cross-arm comparison, it does not touch the seed's requirement that tolerances be fixed before comparative results.
- A further tree run would add no measurement.
- The measure route still has no execution controller (gap 3).
- `no_justified_test` does not apply while a sub-USD-5 calibration remains that both kept candidates require and that decides budget tiers.

**What will need the owner after this test** (not now): CPU/GPU numerical tolerances. The seed requires them to be justified before comparative results are examined. Run2 already showed CPU/GPU score deltas of up to 0.14 (`run2_trace/REPORT.md:101`). The physical card requires independent precision analysis. C2's 0.20 tolerance was chosen above the observed 0.14 and is not justified (s02 B). No calibration on these routes can produce a justified tolerance, so the step after this one will probably stop with `needs_owner` or `contract_gap`.

**Brief construction.** The brief is the seed's exact text and the materials addendum unchanged (lines 1–310, matching `m5/b01_materials/BRIEF_run1.md:1–310`), followed by two blank lines and one section headed `## Calibration request (science step s04)`. Without a shell I could not hash the file. I checked the prefix by line alignment (line 310 is identical) and by matching every curly-apostrophe position (19) and every straight-quote line (13) against the source. The operator should compare the SHA-256 of the first 310 lines with `BRIEF_run1.md` before launch.

## E. Contract gaps (final list for the owner)

1. **m5 cannot express named-arm ordered comparisons.**
   - Where: `D/m5/SCHEMAS.md` A/PREDICTIONS 178–188, Propose 211–215, Evaluate 281–299; `D/m5/pipeline.js:1037–1038`.
   - What it cannot express: CPU/GPU agreement gating dense quality, with separate per-case rank1/best50 results at common budgets, outside the fixed method menu.
   - Blocks: the final seed comparison. It does not block descriptive reproduce-only calibrations, which run4 demonstrates.
   - Smallest change: an optional named-arm comparison mode with sealed agreement and quality metrics, ordered prerequisites and unavailable-arm outcomes.
2. **The handoff from tree PLAN to measure loses the protocol.**
   - Where: `D/CONTRACT.md` §2.5 and §5 calibration; `D/src/main.js:468–478`; `D/launch.js:71–96`.
   - What it cannot express: only scalar GUESS/PROXY inputs with ratio bands are exported. Arms, decision rules, tiers and held-fixed settings are dropped. A 2.57 s result reads as "outside band" even though it is budget-favourable.
   - Blocks: calibration on the measure route, and the final experiment.
   - Smallest change: an immutable full PLAN/protocol handoff, with the scientific decision kept separate from scalar price-band checks.
3. **The measure route has no execution controller.**
   - Where: `D/launch.js:45–47,83–107,141–153`.
   - What it cannot express: there are no stage-argument chains after the compiler (the m4 `measure.sh` is absent).
   - Blocks: calibration on that route.
   - Smallest change: a validated design/gate/build/tests/review/launch/post argument chain with watchdog and ledger ingestion.
4. **The cost queue cannot represent scientific readiness.**
   - Where: `D/src/cost.js:154–163`; `D/src/main.js:470–478`; `D/CONTRACT.md` §5.
   - What it cannot express: unresolved tolerances (atol, rtol, eps_xyz, eps_eval) do not appear in `required[]`, so cards show `no_unmeasured_input` while scientifically blocked.
   - Blocks: progression from calibration to the agreement and quality study.
   - Smallest change: typed required-evidence records separate from numeric cost resolution.
5. **There is no route for authorised local evidence.**
   - Where: `D/src/prompts.js:107–110`, `D/src/gates.js:313–327,373–388`, `D/m5/pipeline.js:89–108`.
   - What it cannot express: m5 intake cannot follow prior-record pointers, so every brief must embed historical evidence. s03 and s04 do this by hand.
   - Blocks: reproducible calibration identity across steps.
   - Smallest change: an owner-authorised, hashed evidence bundle propagated through the contracts.
6. **Cost accounting** (new, observed in run4).
   - Where: `D/m5/pipeline.js:1007–1008`.
   - What it cannot express: stage USD is the sum of receipt and stage walls × rate. The takeaway total (USD 0.81) leaves out allocation time before intake and after the last receipt; run4's box-start-to-last-receipt span implies about USD 1.28. The seed asks for "billed allocation cost".
   - Blocks: the cost report of the final experiment, not calibration.
   - Smallest change: report the allocation span from box start to termination (the existing `runBoxUSD` at `pipeline.js:63–67,1021`) and the invoice when available, alongside stage-wall USD.

Aggregate: gaps 2 and 3 block calibration on the tree's own measure route. Gaps 1, 2, 4 and 6 block the final experiment. m5 reproduce-only stays usable for calibrations.

## F. Narrowing

Unchanged: **no narrowing** (see `NARROWING.md`). The next test times all three seed configurations without examining comparative results. It answers the seed's "small runtime calibration to define feasible budgets" and drops nothing.
