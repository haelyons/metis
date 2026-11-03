# Result

Picks 6 · PASS 3 · on-goal cards U4 0 · U3 3 · halts: G-plan 1

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [R1·phys·P1](#card-R1-physical-P1) Denser rigid-body search: recovery versus ranking | PASS 1/2 | top 1/4 · SAME | unsure | 3 | 5 → 5 | 5 → 5 | 3 | — | 1 → 1 | — | none · plan $49 · 0 GUESS |
| [R1·interp·I2](#card-R1-interp-I2) Differential tracing of CPU/GPU numerical disagreement | halted: G-plan | top 2/3 · SAME | unsure | — | 1 → — | 5 → — | — | — | 1 → — | — | not judged · plan $49 · 2 GUESS |
| [seed·idea·2](#card-seed-idea-2) Complete-workflow acceleration and dense-search affordability | PASS 2/2 | seed | unsure | 3 | — → 5 | — → 5 | 3 | — | — → 2 | — | $59 at quality · plan $100 · 3 GUESS |
| [seed·idea·4](#card-seed-idea-4) CPU host scheduling as workflow affordability calibration | PASS 2/2 | seed | unsure | 1 | — → 5 | — → 5 | 1 | — | — → 1 | — | none · plan $7 · 0 GUESS |
| [seed·idea·3](#card-seed-idea-3) Dense search changes candidate recovery and ranking differently | REJECT (2 blocking) | seed | unsure | 5 | — → 5 | — → 5 | 5 | — | — → 1 | — | $16 at compare · plan $25 · 2 GUESS |
| [seed·idea·1](#card-seed-idea-1) Agreement before interpreting acceleration or denser search | REJECT (1 blocking) | seed | unsure | 1 | — → 5 | — → 5 | 3 | — | — → 1 | — | $40 at fresh · plan $40 · 0 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-R1-physical-P1"></a>**P1 · Denser rigid-body search: recovery versus ranking.** R1 · physical · top pick · distance SAME · compute tested: yes · plan expects: unsure · PASS

**Question.** Does GPU docking at 54000 rotations improve rank1 or best50 DockQ over 3600 rotations within identical complete-workflow budgets?

**What is known.** Published MEGADOCK GPU study measured docking acceleration at default 3600 rotations; it did not compare dense-search rank1 and best50 DockQ. [prior] Does 54000-rotation GPU search improve retained-pose recovery or first-ranked accuracy within complete-workflow budgets on these 4 unbound cases?

**Hypothesis.** Denser angular coverage improves best50 recovery more consistently than rank1 because scoring can still favor wrong poses.

**If compute is the lever.** At 54000 versus 3600 rotations, best50 DockQ rises over 0.01 beyond noise on all 4 cases; rank1 changes remain separate.

**If not.** At 54000 versus 3600 rotations, at least 1 case lacks best50 DockQ gain over 0.01 beyond noise, or dense search misses budget.

**Test.** Build frozen docking, reconstruction, evaluation and billing harness. Compare CPU and GPU at 3600 rotations; require agreement, then compare GPU 54000 versus 3600 using 50 poses, 7 timing blocks, per-case rank1/best50 and common complete-workflow budgets.

*Compute axis.* Angular orientations searched per docking invocation: 3,600–54,000 rotations, 2 levels. Closest prior: 3,600 [prior], beyond it.

*Restructuring.* none.

**Check first.** Independent transform reconstruction and DockQ fixtures validate execution; CPU outputs anchor identical GPU settings before dense quality evaluation. Tolerance: Exact input/settings/grid/count equality; exact ranked rotation/translation identity required, including rank1 and cutoff membership. Tie mismatch fails this strict gate. Independently reconstruct documented transforms and compare coordinates within eps_xyz; derive eps_xyz from serialization/rounding analysis. Require abs(score_CPU-score_GPU) <= atol + rtol*max(abs(score_CPU),abs(score_GPU)); derive atol/rtol from pinned FFT precision/error analysis plus nonstudy synthetic fixtures, never fresh four-case differences. Require each paired DockQ difference <= eps_eval. Numeric atol, rtol, eps_xyz and eps_eval remain unresolved blocking inputs. Repair must provide independently justified values and freeze them before fresh comparison; otherwise stop without agreement or dense-quality conclusions..

**Would not show.** Exposed 4-case replication only; no biological efficacy, unseen holdout, broad accuracy scaling, or CPU-only market-cost claim. Scientific acceptance remains gated.

*Cost.* Plans $49.48 of the $100 budget over 12 machine-hours, leaving $50.52. Pilot gate: Calibration allocation charge; replace with actual all-in projection before launch ≤ 20, else Do not launch, or stop screen; reduce calibration scope without evaluating study quality..

**Judges.** Dramaturg: PASS 1/2. Decides at: none · plan $49 · 0 GUESS (critic: Unresolved tolerances and possible agreement-gate failure can halt dense evaluation; no phase guarantees decision_rule applies whichever outcome occurs).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $100 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-11-03 · filesystem $0.20/GiB-month [q]
Spend      calibration  Future bounded timing-only screen: all 4 cases, 1 warmup plus 3 repeats per arm; study native scoring disabled. Use oversized nonstudy evaluator fixtures for evaluation reserve. Include setup/build, transport, idle and termination.  1x NVIDIA H100 PCIe 80GB $3.29/h  3 h  $9.87
           freeze  Freeze justified numerical tolerances before fresh CPU/GPU comparison. Freeze configurations, common budgets, repetitions, order, noise/decision rules and spending cap before quality. Verify executor receives protocol hash. Allow 1 hour for fresh-host setup/idle.  1x NVIDIA H100 PCIe 80GB $3.29/h  1 h  $3.29
           agreement  Fresh CPU/GPU standard comparison on all 4 cases, 1 invocation per arm/case, using sealed independent tolerances; then evaluate frozen predictions. Separate execution correctness, numerical agreement and evaluator validation.  1x NVIDIA H100 PCIe 80GB $3.29/h  2 h  $6.58
           main  After gates, 1 warmup per arm/case plus 7 balanced randomized blocks across 4 cases and 3 arms. Record complete workflows and all 50 DockQ values. Retain rank1/best50 changes, winning ranks, timings and budget eligibility.  1x NVIDIA H100 PCIe 80GB $3.29/h  4 h  $13.16
           report  Retrieve/hash artifacts, reconcile allocation timestamps and final receipt, report per-case quality/budget tables and separate acceleration/agreement conclusions. Preserve negatives, unavailable arms, timeouts and overruns.  1x NVIDIA H100 PCIe 80GB $3.29/h  2 h  $16.58
           Planned $49.48 · unallocated $50.52 · cap $100
Rests on   gate Calibration allocation charge; replace with actual all-in projection before launch ≤ 20 in calibration (now 9.87, passes; uncut plan at it $49.48), else Do not launch, or stop screen; reduce calibration scope without evaluating study quality.
Scenarios  none
Buys       Exactly user-named unbound cases: 4 [d]
           Main repeated invocations, contingent on gates: 84 [=]
           Main repeated pose evaluations: 4,200 [=]
           Standard angular search: 3,600 [c]
           Documented -D angular search: 54,000 [c]
Flags      none
Full scale none
Outside    Offline controller repair, independent numerical review and analysis; design allowance: 16 person-hours · Extra non-Lambda purchases planned; existing workstation and local artifact retention used: 0 USD
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
search_ratio = dense_rotations / standard_rotations = 54000 / 3600 = 15 ratio
prepared_files = cases * agreement_arms = 4 * 2 = 8 PDBs
main_invocations = cases * arms_count * timing_repeats = 4 * 3 * 7 = 84 invocations
main_warm_invocations = cases * arms_count * warmups = 4 * 3 * 1 = 12 invocations
agreement_invocations = cases * agreement_arms * agreement_repeats = 4 * 2 * 1 = 8 invocations
cal_invocations = cal_cases * arms_count * (cal_repeats + warmups) = 4 * 3 * (3 + 1) = 48 invocations
main_pose_evals = main_invocations * retained = 84 * 50 = 4200 evaluations
allocation_h = cal_h + freeze_h + agreement_h + main_h + report_h = 3 + 1 + 2 + 4 + 2 = 12 hours
cal_project_usd = cal_h * gpu_count * gpu_rate = 3 * 1 * 3.29 = 9.87 USD
allocation_usd = allocation_h * gpu_count * gpu_rate = 12 * 1 * 3.29 = 39.48 USD
planned_usd = allocation_usd + other_reserve = 39.48 + 10 = 49.48 USD
unspent_credit = credit_available - planned_usd = 1000 - 49.48 = 950.52 USD
cal_box.hours = cal_h = 3 = 3 h
freeze_box.hours = freeze_h = 1 = 1 h
agree_box.hours = agreement_h = 2 = 2 h
main_box.hours = main_h = 4 = 4 h
report_box.hours = report_h = 2 = 2 h
filesystem.usd = persistent_gib * fs_usd_gib_month = 0 * 0.2 = 0 usd
reserve.usd = other_reserve = 10 = 10 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:hypothesis` PARTIAL · page: "" · note: Predicted improvement needs no source. Claim that scoring can favor wrong poses lacks cited support.
- sample 1 · `card:anchor` PARTIAL · page: "DockQ" · note: Recorded mapping quote appears. Documentation supports DockQ evaluation and mapping control, but does not establish independent transform reconstruction, fixture validation, or CPU/GPU agreement. Those remain proposed validation procedures.
- sample 2 · `card:hypothesis` UNSUPPORTED · page: "" · note: Predicted improvement needs no source. Causal claim that scoring can favor wrong poses has no cited source.

**Critic.**
- stakes 5 · `card:question` "Does GPU docking at 54000 rotations improve rank1 or best50 DockQ over 3600 rotations within identical complete-workflow budgets?" · Either outcome informs whether to spend fixed workflow budgets on dense search; test directly measures per-case pose recovery and affordability.
- lever 3 · `plan:anchor.tolerance` "Exact input/settings/grid/count equality; exact ranked rotation/translation identity required, including rank1 and cutoff membership. Tie mismatch fails this strict gate. Independently reconstruct documented transforms and compare coordinat…" · Search spans 15× with inputs fixed, but unresolved eps_eval prevents checking whether predicted gains exceed numerical noise.
- verifiable 3 · `plan:scored_against` "Same-settings CPU-standard outputs anchor GPU-standard science. Pinned native references evaluate frozen predictions through pinned DockQ: rank1 is highest MEGADOCK score, best50 is maximum DockQ among 50 retained predictions. Native qualit…" · Pinned native structures provide independent reference truth; no published-number reproduction within stated tolerance precedes comparison.
- open 5 · `card:closest_prior` "Published MEGADOCK GPU study measured docking acceleration at default 3600 rotations; it did not compare dense-search rank1 and best50 DockQ. [prior]" · Published comparison measures standard-search acceleration; dense-search rank1 and best50 recovery under common workflow budgets remain open.
- reshape 1 · `card:sequential_part` "No dependent angular chain; docking output precedes reconstruction and evaluation. [guide]" · No sequential dependency removed. Angular work already parallel; reconstruction and evaluation still follow docking.
- baseline NA · `card:method` "none" · Restructuring method is none.

**Option critic.**
- stakes 5: Answer determines whether fixed budgets should fund denser angular search.
- open 5: Names 3,600–54,000 rotations; cited guide provides settings without quality-scaling measurements across this reachable range.
- reshape 1: Angles are independent; decoy reconstruction waits on output, but no dependent chain restructuring is proposed.
- distance SAME: Tests root’s dense-search rank1 and best50 recovery under common workflow budgets.

**Producer says (not judged).** expected unsure (User-disclosed exploratory results favor best50 gains but expose rank1 degradation; affordability and prospective numerical acceptance remain unestablished.); compute_tested yes (Vary documented angular search width by 15 times while fixing retained count and scoring; separate existing GPU acceleration from additional-search quality. https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md); decides no; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
- predictions.if_not: a sentence of 22 words
- test_summary: a sentence of 27 words
- dramaturg findings failed G-find after a resample; decided as returned
- dramaturg-2 findings failed G-find after a resample; decided as returned
- prose over 240 words (295)

**Root question (R1).** Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget? Small pilot on exactly four unbound PINDER 2024-02 cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Compare existing MEGADOCK CPU standard 3600 rotations, GPU standard 3600, and GPU documented dense 54000 (-D). Keep scoring and retained predictions fixed at 50. Pin prepared input bytes, references, binary/dependency/settings/thread/allocation identities. First establish execution correctness and scientific CPU/GPU agreement at identical settings using justified numerical tolerances sealed before fresh comparison. Then assess dense-search DockQ for rank1 and best50 separately, per case; native references only for evaluation. Calibrate runtime before choosing feasible common budgets; seal configurations, timing repetitions, comparison/noise rules and total spending cap before quality evaluation. Report complete workflow time, GPU activity and billed allocation cost, separating setup/retrieval from steady-state work. Keep acceleration, agreement and additional-search quality conclusions separate. Preserve negatives, unavailable budget arms and overruns. No biological efficacy or beyond-four-case inference. Run2 already exposed quality, so fresh executions are prospective replication under new rules, never unseen holdout or retrospective preregistration. Do not substitute throughput of bundled runs for this question. Repository /home/hal/dev/interp/metis: seed experiments/blind-02/m5/BRIEF.md; case preparation/source/reference pins experiments/blind-02/m5/b01_materials/BRIEF_run1.md:48-158; full prior trace experiments/blind-02/m5/run2_trace/REPORT.md; new assessment experiments/blind-02/science/s01/ASSESSMENT.md. Run2 measured docking totals CPU/GPU/dense 40.07/6.85/69.38 seconds, not complete workflows; standard CPU/GPU transforms and DockQ matched, score max deltas 0.04/0.03/0.04/0.14 with no acceptance tolerance. Dense best50 improved all four observations, rank1 worsened in two including 1nr5. These are exploratory, not sealed conclusions. Historical H100 PCIe rate USD3.29/hour, setup145s, whole unscored bundle median131.9565s; old receipts setup/anchors/freeze/upload/profile/concurrency 145/1571/1402/1424/2832/3448s. Historical allocation and transport observations are estimates for a fresh box, not new producer measurements or public citations. Tree plans only, no box execution. Full card plan ceiling USD100; each later calibration must project below USD20 including setup, retrieval and idle, preferably USD5-10, soft6h/hard12h. Do not run full experiments on calibration route. Identify specific file/section gaps if existing routes cannot implement comparison. Tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases. Measure compilation carries uncertain scalar inputs and phases, not arms/decision_rule; checks 2.5x PROXY or 3x other estimate bands, never scientific equivalence. Measure execution requires missing stage args/controller to be established. Card factual web sources may be checked; do not fabricate citations for private records.

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/physical/1fffee1a/producer.md)

---

<a id="card-R1-interp-I2"></a>**I2 · Differential tracing of CPU/GPU numerical disagreement.** R1 · interp · top pick · distance SAME · compute tested: no · plan expects: unsure · halted: G-plan

**Question.** Can 6 checkpoints locate CPU/GPU disagreement without confusing numerical differences with changed docking poses?

**What is known.** MEGADOCK published CPU/GPU docking timings over 352 jobs; it did not establish intermediate-trace equivalence or scientific acceptance thresholds [prior]. Can matched checkpoints distinguish harmless score differences from changed selected poses on these 4 exposed unbound cases?

**Hypothesis.** Matched intermediate arrays plus independent fixtures locate numerical differences; extra GPU replicas cannot justify scientific acceptance tolerances.

**If the hypothesis holds.** At 16 executions, tracing still localizes all 6 injected faults and reproduces natural divergence stages across paired repeats.

**If not.** At 16 executions, tracing localizes fewer than 6 injected faults or natural divergence stages change between repeats.

**Test.** Build 6-checkpoint CPU/GPU traces, validate exact-grid fixtures and injected faults, acquire 8 executions plus 8 repeats, and compare 50 predictions per case. Keep acceptance, acceleration and dense-search quality separate.

*Compute axis.* Instrumented CPU/GPU executions, fixed diagnostic coverage rather than a search for a compute scaling threshold: 8–16 executions, 2 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** Exact integer grid correlations and 6 injected faults check checkpoint alignment; independent pose reconstruction checks output interpretation. Tolerance: Integer oracle has exact expected values. For tiny-grid FFT diagnostic fixtures require absolute score error <= fixture_error and unique-peak agreement; tied maxima compared as sets. This fixture threshold is a DESIGN screen, not a production scientific score tolerance. Recover every injected stage exactly and accept no false localization on null controls. Production score/pose/DockQ bounds require independent analysis in seal; stop scientific agreement if unavailable..

**Would not show.** Sampled tracing diagnoses implementations; it proves neither biological efficacy, generalization beyond 4 cases, numerical equivalence without justified tolerances, nor dense-search affordability.

*Cost.* Plans $49.48 of the $100 budget over 12 machine-hours, leaving $50.52. Main guess: Unmeasured successfully localized injections; conservative placeholder [g], measured after $6.58 of spend. 2 cost flags in the block.

**Halted at G-plan.** compute_tested is no: This is a bounded diagnostic audit. The 8-to-16 execution axis adds repeat checks, not a test that more parallel hardware changes docking quality or supplies tolerances. No GPU scaling claim.

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $100 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-11-03 · filesystem $0.20/GiB-month [q]
Spend      screen  Timer-bounded fixture calibration, setup/idle/retrieval included; $6.58 before reserved extras [price].  1x NVIDIA H100 PCIe 80GB $3.29/h  2 h [=]  $6.58
           trace  Timer-bounded standard CPU/GPU trace acquisition and controls; CPU work on GPU host billed too [billing]. No throughput or completion estimate.  1x NVIDIA H100 PCIe 80GB $3.29/h  8 h [=]  $26.32
           close  Allocation-time reserve for transport, idle, retrieval and verified termination; $6.58 [price].  1x NVIDIA H100 PCIe 80GB $3.29/h  2 h [=]  $6.58
           close  No persistent filesystem created; local arrays exported or deleted before termination. Illustrative filesystem rate is unused [fs].  [=]  $0
           close  Bounded reserve, not predicted tax or spending requirement. Stop if verified all-in projected bill exceeds ceiling.  [=]  $10
           Planned $49.48 · unallocated $50.52 · cap $100
Rests on   Unmeasured successfully localized injections; conservative placeholder 0 faults [g] rests on: No execution or independent numerical review completed; use zero until phase measures readiness. · measured in screen ($6.58 spent by then) · gate Unmeasured successfully localized injections; conservative placeholder ≥ 6 in analyze (now 0, fails; uncut plan at it $49.48), else Reject tracing reliability; retain negative result and block scientific handoff. · budget not reached within 1000×
           Unestablished scientific acceptance contract; conservative placeholder 0 boolean [g] rests on: No execution or independent numerical review completed; use zero until phase measures readiness. · measured in seal ($6.58 spent by then) · gate Unestablished scientific acceptance contract; conservative placeholder ≥ 1 in seal (now 0, fails; uncut plan at it $49.48), else Diagnostic-only audit allowed; no scientific acceptance or dense-quality release. · budget not reached within 1000×
           gate Conservative calibration projection including reserved extras ≤ 10 in screen (now 9.58, passes; uncut plan at it $49.48), else Stop, retrieve and redesign offline; never extend calibration into full study.
Scenarios  none
Buys       Fixed user-requested cases: 4 [d]
           Scheduled instrumented executions including repeats: 16 [=]
           Maximum scheduled sampled checkpoint sets: 768 [=]
           Independent fixture inputs: 8 [=]
           Fixture checks plus injection and null runs: 39 [=]
           Predictions retained per scientific arm: 50 [d]
Flags      gate in seal fails at the plan's own value: Unestablished scientific acceptance contract; conservative placeholder is 0, needs ≥ 1; expected path: Diagnostic-only audit allowed; no scientific acceptance or dense-quality release.
           gate in analyze fails at the plan's own value: Unmeasured successfully localized injections; conservative placeholder is 0, needs ≥ 6; expected path: Reject tracing reliability; retain negative result and block scientific handoff.
Full scale none
Outside    DESIGN engineering, independent numerical review and report allowance; no paid consultant assumed: 32 human hours · DESIGN incremental non-Lambda cash allocation; use existing workstation and artifact storage: 0 USD
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
initial_execs = cases * backends = 4 * 2 = 8 executions
trace_execs = initial_execs * passes = 8 * 2 = 16 executions
checkpoint_sets = trace_execs * sample_rotations * checkpoints = 16 * 8 * 6 = 768 sets
fixture_inputs = fixture_families * fixture_sizes = 4 * 2 = 8 inputs
fixture_execs = fixture_inputs * backends * passes = 8 * 2 * 2 = 32 executions
screen_fixture_execs = fixture_execs + injected_faults + null_controls = 32 + 6 + 1 = 39 executions
hard_hours = screen_hours + trace_hours + close_hours = 2 + 8 + 2 = 12 hours
calibration_projected_usd = screen_hours * gpu_rate_usd_h * gpu_count + screen_extra_reserve_usd = 2 * 3.29 * 1 + 3 = 9.58 USD
calibration.hours = screen_hours = 2 = 2 h
acquisition.hours = trace_hours = 8 = 8 h
shutdown.hours = close_hours = 2 = 2 h
persistent_storage.usd = persistent_gib * fs_usd_gib_month = 0 * 0.2 = 0 usd
extras.usd = extra_reserve_usd = 10 = 10 usd
```

**Option critic.**
- stakes 5: Diagnosing numerical disagreement can determine whether GPU execution passes agreement requirements and subsequent comparisons proceed.
- open 1: Compute-bought quantity and published measurement gap both say none.
- internals 5: Intermediate arrays identify the first divergent stage; final outputs cannot locate where numerical disagreement began.
- reshape 1: Checkpoint dependencies remain; proposed concurrency concerns independent cases and rotations.
- distance SAME: Locating CPU/GPU numerical divergence addresses execution correctness and same-settings agreement, explicit root subquestions.

**Producer says (not judged).** expected unsure (Injected faults should be localizable by construction; natural divergence reproducibility and defensible application tolerances remain unmeasured.); compute_tested no (This is a bounded diagnostic audit. The 8-to-16 execution axis adds repeat checks, not a test that more parallel hardware changes docking quality or supplies tolerances. No GPU scaling claim.); decides no; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
- gate in seal fails at the plan's own value: Unestablished scientific acceptance contract; conservative placeholder is 0, needs ≥ 1; expected path: Diagnostic-only audit allowed; no scientific acceptance or dense-quality release.
- gate in analyze fails at the plan's own value: Unmeasured successfully localized injections; conservative placeholder is 0, needs ≥ 6; expected path: Reject tracing reliability; retain negative result and block scientific handoff.
- prose over 240 words (250)

**Root question (R1).** Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget? Small pilot on exactly four unbound PINDER 2024-02 cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Compare existing MEGADOCK CPU standard 3600 rotations, GPU standard 3600, and GPU documented dense 54000 (-D). Keep scoring and retained predictions fixed at 50. Pin prepared input bytes, references, binary/dependency/settings/thread/allocation identities. First establish execution correctness and scientific CPU/GPU agreement at identical settings using justified numerical tolerances sealed before fresh comparison. Then assess dense-search DockQ for rank1 and best50 separately, per case; native references only for evaluation. Calibrate runtime before choosing feasible common budgets; seal configurations, timing repetitions, comparison/noise rules and total spending cap before quality evaluation. Report complete workflow time, GPU activity and billed allocation cost, separating setup/retrieval from steady-state work. Keep acceleration, agreement and additional-search quality conclusions separate. Preserve negatives, unavailable budget arms and overruns. No biological efficacy or beyond-four-case inference. Run2 already exposed quality, so fresh executions are prospective replication under new rules, never unseen holdout or retrospective preregistration. Do not substitute throughput of bundled runs for this question. Repository /home/hal/dev/interp/metis: seed experiments/blind-02/m5/BRIEF.md; case preparation/source/reference pins experiments/blind-02/m5/b01_materials/BRIEF_run1.md:48-158; full prior trace experiments/blind-02/m5/run2_trace/REPORT.md; new assessment experiments/blind-02/science/s01/ASSESSMENT.md. Run2 measured docking totals CPU/GPU/dense 40.07/6.85/69.38 seconds, not complete workflows; standard CPU/GPU transforms and DockQ matched, score max deltas 0.04/0.03/0.04/0.14 with no acceptance tolerance. Dense best50 improved all four observations, rank1 worsened in two including 1nr5. These are exploratory, not sealed conclusions. Historical H100 PCIe rate USD3.29/hour, setup145s, whole unscored bundle median131.9565s; old receipts setup/anchors/freeze/upload/profile/concurrency 145/1571/1402/1424/2832/3448s. Historical allocation and transport observations are estimates for a fresh box, not new producer measurements or public citations. Tree plans only, no box execution. Full card plan ceiling USD100; each later calibration must project below USD20 including setup, retrieval and idle, preferably USD5-10, soft6h/hard12h. Do not run full experiments on calibration route. Identify specific file/section gaps if existing routes cannot implement comparison. Tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases. Measure compilation carries uncertain scalar inputs and phases, not arms/decision_rule; checks 2.5x PROXY or 3x other estimate bands, never scientific equivalence. Measure execution requires missing stage args/controller to be established. Card factual web sources may be checked; do not fabricate citations for private records.

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/interp/8ce94062/producer.md)

---

<a id="card-seed-idea-1"></a>**1 · Agreement before interpreting acceleration or denser search.** seed pick · compute tested: no · plan expects: unsure · REJECT

**Question.** Do CPU and GPU docking agree across 4 fixed cases and 50 ranked poses after independent numerical calibration?

**What is known.** MEGADOCK authors report CPU/GPU precision differences without repeat counts; published parallel study measured docking scalability, not this calibration decision [faq] [paper]. Whether 2 or 4 independent repeats plus audited error bounds support all 50 ranked poses across these 4 cases remains open.

**Hypothesis.** Independent repeats and error analysis can justify CPU/GPU agreement before acceleration or denser search receives scientific interpretation.

**If the hypothesis holds.** At 4 repeats, independent bounds support agreement for all 4 cases and 50 ranks; 2 repeats leave calibration unresolved.

**If not.** At 4 repeats, agreement remains unresolved or fails, or 2 repeats already suffice; extra calibration buys no changed agreement decision.

**Test.** Build CPU-only subset/control harness, then calibrate 2 and 4 repeats per backend across 4 cases. Seal independent error bounds; compare 1 fresh CPU/GPU pair per case using all 50 ranks. Stop unresolved if bounds fail.

*Compute axis.* Independent same-backend calibration repeats per case and backend; validation effort, not search density: 2–4 repeats, 2 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** None: No independently checked anchor for these exact inputs, source pin and arithmetic is available in supplied prompt. Published FAQ reports small CPU/GPU differences but gives no case-specific error proof [faq]. Build independent high-precision grid-correlation and pose-reconstruction checks during calibration; require audited error bounds before issuing agreement verdict. If these cannot be established within calibration cap, stop unresolved. Reusing MEGADOCK decoygen alone is not independent validation.

**Would not show.** No density, speedup, biological efficacy or population claim. Four previously exposed cases only; absent independent numerical justification leaves agreement unresolved.

*Cost.* Plans $39.61 of the $100 budget over 9 machine-hours, leaving $60.39. Pilot gate: Measured screen pass indicator; placeholder is required success, not observation ≥ 1, else Stop; preserve mismatches. Fix harness offline; no tolerance relaxation or automatic larger allocation..

**Judges.** Dramaturg: REJECT (1 blocking). Decides at: $40 at fresh · plan $40 · 0 GUESS (critic: Calibration can stop unresolved, but successful calibration requires fresh CPU/GPU comparison before sealed bounds establish agreement and repeat-level decision).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $100 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-11-03
Spend      screen  First time box includes new export, transport, setup and CPU subset/control runs. Measure fresh workflow and output stability. All allocation overhead belongs here; terminate instance at timer.  1x NVIDIA H100 PCIe 80GB $3.29/h  1.5 h  $6.94
           calibrate  New all-inclusive calibration allocation: independently measure CPU/GPU same-backend repeats at levels 2 and 4, numerical reference residuals, serialization precision and full workflow time. Seal justified per-case tolerance table before fresh comparison.  1x NVIDIA H100 PCIe 80GB $3.29/h  2.5 h  $10.22
           fresh  Seal acceptance document and hashes; execute 1 fresh CPU/GPU pair per case, all 50 ranks. Record full workflow wall time, sampled GPU activity and actual billed allocation; compare under sealed bounds.  1x NVIDIA H100 PCIe 80GB $3.29/h  5 h  $22.45
           diagnose  Optional mismatch diagnosis; no dense search or native scoring  1x NVIDIA H100 PCIe 80GB $3.29/h  3 h [=]  $9.87  optional
           Planned $39.61 · unallocated $60.39 · with options $49.48 · cap $100
Rests on   gate Measured screen pass indicator; placeholder is required success, not observation ≥ 1 in screen (now 1, passes; uncut plan at it $39.61), else Stop; preserve mismatches. Fix harness offline; no tolerance relaxation or automatic larger allocation.
           gate Measured calibration pass indicator; placeholder is required success, not observation ≥ 1 in calibrate (now 1, passes; uncut plan at it $39.61), else Stop unresolved; report missing numerical anchor, repeatability or runtime evidence. No fresh comparison spend.
Scenarios  none
Buys       Exact user-selected cases: 4 [d]
           Planned screen docking runs: 8 [=]
           Maximum calibration docking runs, cumulative: 32 [=]
           Fresh comparison docking runs: 8 [=]
           Fresh comparison paired ranked rows: 200 [=]
Flags      none
Full scale none
Outside    Authoring, numerical error review and report time; DESIGN time box, no purchased labor: 16 person hours · Local writing/web checks; no paid external service or GPU experiment authorized: 0 USD
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
screen_runs = cases * screen_routes = 4 * 2 = 8 runs
calibration_runs = cases * backends * high_repeats = 4 * 2 * 4 = 32 runs
fresh_runs = cases * backends * fresh_repeats = 4 * 2 * 1 = 8 runs
planned_runs = screen_runs + calibration_runs + fresh_runs = 8 + 32 + 8 = 48 runs
fresh_rows = cases * retained = 4 * 50 = 200 row pairs
screen_usd = screen_h * price_h * gpu_count + screen_reserve = 1.5 * 3.29 * 1 + 2 = 6.935 USD
calibration_usd = calibration_h * price_h * gpu_count + calibration_reserve = 2.5 * 3.29 * 1 + 2 = 10.225 USD
total_usd = (screen_h + calibration_h + comparison_h + diagnostic_h) * price_h * gpu_count + screen_reserve + calibration_reserve + later_reserve = (1.5 + 2.5 + 5 + 3) * 3.29 * 1 + 2 + 2 + 6 = 49.48 USD
core_usd = total_usd - diagnostic_h * price_h * gpu_count = 49.48 - 3 * 3.29 * 1 = 39.61 USD
unused_usd = budget_usd - total_usd = 100 - 49.48 = 50.52 USD
screen_box.hours = screen_h = 1.5 = 1.5 h
screen_contingency.usd = screen_reserve = 2 = 2 usd
calibration_box.hours = calibration_h = 2.5 = 2.5 h
calibration_contingency.usd = calibration_reserve = 2 = 2 usd
comparison_box.hours = comparison_h = 5 = 5 h
diagnostic_box.hours = diagnostic_h = 3 = 3 h
later_contingency.usd = later_reserve = 6 = 6 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:closest_prior` PARTIAL · page: "the results of docking scores are slightly different by CPU version and GPU version." · note: FAQ confirms precision differences and gives no repeat counts. Paper fetch returned browser verification; scalability quote and characterization of study could not be checked.
- sample 1 · `card:limits` PARTIAL · page: "" · note: Scope restrictions and unresolved-agreement rule describe plan. Claim that four cases were previously exposed is factual and unsourced.
- sample 1 · `src:paper` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Source and redirect returned browser verification. Recorded quote, claimed full-text extraction and study scope could not be verified.
- sample 2 · `card:closest_prior` PARTIAL · page: "Because of precision of GPUs, the results of docking scores are slightly different by CPU version and GPU version." · note: FAQ quote appears exactly, preceded by 'Answer:'. FAQ reports precision differences without repeat counts. Paper inaccessible behind browser check; scalability and calibration claims unverified.
- sample 2 · `card:limits` PARTIAL · page: "" · note: Scope limits and agreement rule describe plan. Claim that four cases were previously exposed has no source.
- sample 2 · `src:paper` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Browser check blocked article; recorded quote and claimed scope could not be verified.

**Critic.**
- stakes 5 · `card:if_not` "At 4 repeats, agreement remains unresolved or fails, or 2 repeats already suffice; extra calibration buys no changed agreement decision." · Outcomes decide whether extra calibration buys agreement confidence, whether two repeats suffice, or whether scientific interpretation must stop unresolved.
- lever 1 · `plan:compute_axis` "{"quantity":"Independent same-backend calibration repeats per case and backend; validation effort, not search density","unit":"repeats","levels":[2,4]}" · Repeat levels span only 2×; noise rule supplies no established bound showing predicted qualification difference exceeds calibration variability.
- verifiable 3 · `plan:checks[5]` "Write independent reference.py without calling MEGADOCK scoring or decoygen: check rigid transforms and directly accumulate high-precision grid correlations at every retained transform; instrument pre-FFT grids and near-cutoff candidates. A…" · Independent high-precision correlations and transform checks provide reference truth if implemented; no published-number reproduction within stated tolerance.
- open 5 · `card:closest_prior` "MEGADOCK authors report CPU/GPU precision differences without repeat counts; published parallel study measured docking scalability, not this calibration decision [faq] [paper]." · Named priors address precision differences and scalability; neither answers whether two versus four repeats justify agreement across these cases.
- reshape 1 · `card:sequential_part` "4 gates: establish inputs, test repeatability, seal error bounds, compare fresh CPU/GPU runs." · Inputs, repeatability, error-bound sealing and fresh comparison remain sequential dependencies; plan removes none.
- baseline NA · `card:method` "none" · Restructuring method is none; criterion explicitly permits NA.

**Producer says (not judged).** expected unsure (User-supplied exploratory observations lack sealed tolerances; published precision guidance does not establish bounds for these inputs and binaries [faq].); compute_tested no (Repeat levels vary validation effort; neither parallel compute, denser sampling nor throughput is experimentally varied. Necessary prerequisite card, without compute-lever claim.); decides no; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd: set by the question
- novelty.closest_prior: a sentence of 21 words
- novelty.left_open: a sentence of 21 words
- dramaturg findings failed G-find after a resample; decided as returned
- dramaturg-2 findings failed G-find after a resample; decided as returned
- prose over 240 words (254)

**Root question (null).** Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget? Small pilot on exactly four unbound PINDER 2024-02 cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Compare existing MEGADOCK CPU standard 3600 rotations, GPU standard 3600, and GPU documented dense 54000 (-D). Keep scoring and retained predictions fixed at 50. Pin prepared input bytes, references, binary/dependency/settings/thread/allocation identities. First establish execution correctness and scientific CPU/GPU agreement at identical settings using justified numerical tolerances sealed before fresh comparison. Then assess dense-search DockQ for rank1 and best50 separately, per case; native references only for evaluation. Calibrate runtime before choosing feasible common budgets; seal configurations, timing repetitions, comparison/noise rules and total spending cap before quality evaluation. Report complete workflow time, GPU activity and billed allocation cost, separating setup/retrieval from steady-state work. Keep acceleration, agreement and additional-search quality conclusions separate. Preserve negatives, unavailable budget arms and overruns. No biological efficacy or beyond-four-case inference. Run2 already exposed quality, so fresh executions are prospective replication under new rules, never unseen holdout or retrospective preregistration. Do not substitute throughput of bundled runs for this question. Repository /home/hal/dev/interp/metis: seed experiments/blind-02/m5/BRIEF.md; case preparation/source/reference pins experiments/blind-02/m5/b01_materials/BRIEF_run1.md:48-158; full prior trace experiments/blind-02/m5/run2_trace/REPORT.md; new assessment experiments/blind-02/science/s01/ASSESSMENT.md. Run2 measured docking totals CPU/GPU/dense 40.07/6.85/69.38 seconds, not complete workflows; standard CPU/GPU transforms and DockQ matched, score max deltas 0.04/0.03/0.04/0.14 with no acceptance tolerance. Dense best50 improved all four observations, rank1 worsened in two including 1nr5. These are exploratory, not sealed conclusions. Historical H100 PCIe rate USD3.29/hour, setup145s, whole unscored bundle median131.9565s; old receipts setup/anchors/freeze/upload/profile/concurrency 145/1571/1402/1424/2832/3448s. Historical allocation and transport observations are estimates for a fresh box, not new producer measurements or public citations. Tree plans only, no box execution. Full card plan ceiling USD100; each later calibration must project below USD20 including setup, retrieval and idle, preferably USD5-10, soft6h/hard12h. Do not run full experiments on calibration route. Identify specific file/section gaps if existing routes cannot implement comparison. Tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases. Measure compilation carries uncertain scalar inputs and phases, not arms/decision_rule; checks 2.5x PROXY or 3x other estimate bands, never scientific equivalence. Measure execution requires missing stage args/controller to be established. Card factual web sources may be checked; do not fabricate citations for private records.

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/seed/idea/340ca71c/producer.md)

---

<a id="card-seed-idea-2"></a>**2 · Complete-workflow acceleration and dense-search affordability.** seed pick · compute tested: yes · plan expects: unsure · PASS

**Question.** Can GPU docking make 54000 rotations affordable within CPU 3600-rotation workflow budgets, improving pose recovery across 4 unbound complexes?

**What is known.** MEGADOCK times 352 docking jobs up to 1260 GPUs; maximum rotations unspecified, leaving matched complete-workflow search budgets unresolved [prior]. Whether 54000 rotations complete CPU-standard workflow budgets and improve best50 recovery without concealing rank1 regressions on these 4 unbound cases.

**Hypothesis.** GPU acceleration offsets denser rotational search, improving best50 DockQ within matched complete-workflow time and allocation cost.

**If compute is the lever.** GPU standard accelerates workflows by at least 1.05; dense completes CPU-standard budgets and improves best50 DockQ by 0.01 on 3 cases.

**If not.** GPU standard gains fall below 1.05, dense misses CPU-standard budgets, or best50 DockQ gains below 0.01 occur on 2 cases.

**Test.** Build deadline-controlled workflow runner. Compare CPU 3600, GPU 3600 and GPU 54000 rotations across 4 fixed cases. Require agreement before 7 paired timing blocks with shared budgets. Report top-ranked and best among 50 predictions’ DockQ separately. Stop calibration at $9.87; stop entire plan at $100.

*Compute axis.* Rotational sampling per docking calculation: 3,600–54,000 rotations, 2 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** CPU and GPU standard poses agree; native self-comparison and independent DockQ checks validate evaluation before dense scoring. Tolerance: DESIGN, sealed before fresh comparisons: identical ranked rotation/translation identifiers and ranks for all 50 outputs; maximum absolute docking-score difference <=0.20. This conservative engineering threshold exceeds user-reported historical maximum 0.14, not a numerical-analysis guarantee. Coordinates after reconstruction: maximum absolute coordinate difference <=0.001 angstrom; DockQ absolute difference <=0.000001 for corresponding standard poses. Self-DockQ within 0.000001 of 1. Independent PINDER versus pinned standalone DockQ absolute difference <=0.005 after identical atom, residue and chain maps; fail closed if semantics cannot be reconciled. No widening after seeing failures..

**Would not show.** Four cases; exploratory history already exposed. Conditional runtime feasibility. No population inference, biological efficacy, guaranteed rank1 improvement or unseen-holdout claim.

*Cost.* Plans $100 of the $100 budget over 20 machine-hours, leaving $0. Main guess: Maximum complete per-case evaluation runtime; unknown until agreement [g], measured after $19.74 of spend; the budget is reached if it is 1.0× higher. 6 cost flags in the block.

**Judges.** Dramaturg: PASS 2/2. Decides at: $59 at quality · plan $100 · 3 GUESS (critic: Quality phase unlocks recovery scores and validates evaluation; combined with completed timing and agreement, every decision-rule component becomes assessable, including negative or inconclusive outcomes).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $100 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-11-03 · filesystem $0.20/GiB-month [q]
Spend      calibration  Single H100 allocation, at most 3 hours including launch/setup/retrieval/build/export/termination. Time all 3 configurations across all 4 cases without native DockQ; uninstrumented first, diagnostic trace afterward. Measure cold/warm transport and byte equality. Estimate scored-workflow evaluation allowance conservatively from separately timed synthetic evaluator smoke input, not native target quality.  1x NVIDIA H100 PCIe 80GB $3.29/h  3 h  $9.87
           agreement  Up to 3 allocated hours, inclusive setup/idle: independent evaluator smoke checks, standard CPU/GPU matched comparison on every case and all 50 poses. Measure complete evaluator walls; compare against sealed numerical gates before dense target scoring.  1x NVIDIA H100 PCIe 80GB $3.29/h  3 h  $9.87
           timing  Up to 6 allocated hours, inclusive setup/retrieval/idle: one warmup plus 7 randomized matched blocks across 3 arms and 4 cases. Run complete scored workflows independently with quality summaries embargoed. Enforce sealed per-case caps; retain misses. Trace separate reruns only after primary timing.  1x NVIDIA H100 PCIe 80GB $3.29/h  6 h  $19.74
           quality  Up to 6 allocated hours, inclusive setup/idle: unlock frozen scores; summarize rank1 and best50 per case/cap, audit chain/residue mapping, missing arms and all regressions. Independently check evaluator outputs, preserve raw predictions and native access logs.  1x NVIDIA H100 PCIe 80GB $3.29/h  6 h  $19.74
           archive  Up to 2 allocated hours for export checksums, receipts, final reproducibility archive and termination. Use attached instance SSD only, no persistent filesystem.  1x NVIDIA H100 PCIe 80GB $3.29/h  2 h  $40.78
           Planned $100 · unallocated $0 · cap $100
Rests on   Documented standard rotational sampling 3,600 rotations [g] rests on: citation not confirmed: UNREACHABLE · no phase measures it · budget reached at 3,600 (1.0× higher)
           Documented dense rotational sampling 54,000 rotations [g] rests on: citation not confirmed: UNREACHABLE · no phase measures it · budget reached at 54,000 (1.0× higher)
           Maximum complete per-case evaluation runtime; unknown until agreement 60 seconds [g] rests on: Unmeasured planning placeholder equal to fixed evaluator allowance; no assertion of observed or expected speed. · measured in agreement ($19.74 spent by then) · gate Maximum complete per-case evaluation runtime; unknown until agreement ≤ 60 in agreement (now 60, passes; uncut plan at it $100), else If measured complete per-case evaluation exceeds fixed 60-second allowance, stop; publish revised caps in a new plan before new replication. · budget reached at 60 (1.0× higher)
           gate Bounded calibration projection from timer, excluding tax covered by contingency ≤ 20 in calibration (now 20, fails; uncut plan at it $100), else Do not launch, or terminate current calibration; report execution-chain gap and measured partial work.
Scenarios  none
Buys       Fixed user-selected apo cases: 4 [d]
           CPU standard, GPU standard, GPU dense: 3 [d]
           Documented standard rotational sampling: 3,600 [g]
           Documented dense rotational sampling: 54,000 [g]
           Output poses per case and arm: 50 [d]
           Randomized paired timing blocks: 7 [d]
           Warmup plus retained complete per-case workflows: 96 [=]
           Case-arm pose slots, excluding repeated measurements: 600 [=]
Flags      error (quote) at numbers.billing_minutes.quote: 1 does not appear in the quote "ODC prices instances by hourly usage and bills in one-minute increments."; a value transformed from the page belongs in a DERIVED number
           gate in calibration fails at the plan's own value: Bounded calibration projection from timer, excluding tax covered by contingency is 20, needs ≤ 20; expected path: Do not launch, or terminate current calibration; report execution-chain gap and measured partial work.
           Documented standard rotational sampling [g] is load-bearing and no phase measures it
           thin headroom: the budget is reached if Documented standard rotational sampling is 1.0× higher
           Documented dense rotational sampling [g] is load-bearing and no phase measures it
           thin headroom: the budget is reached if Documented dense rotational sampling is 1.0× higher
           thin headroom: the budget is reached if Maximum complete per-case evaluation runtime; unknown until agreement is 1.0× higher
Full scale none
Outside    DESIGN human engineering, source/manifests reconciliation and review allowance; stop if insufficient rather than assume runnable pipeline.: 16 person-hours · DESIGN maximum local CPU cores for file authoring/checking; no GPU experiment run.: 4 shared CPU cores · DESIGN incremental paid services outside Lambda; use existing local archive storage.: 0 USD
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
search_ratio = rot_dense/rot_standard = 54000 / 3600 = 15 ratio
timed_workflows = cases*arms_count*(warmups+timing_blocks) = 4 * 3 * (1 + 7) = 96 workflows
trace_workflows = cases*arms_count*trace_blocks = 4 * 3 * 1 = 12 workflows
unique_pose_outputs = cases*arms_count*retained = 4 * 3 * 50 = 600 poses
timed_pose_outputs = timed_workflows*retained = 96 * 50 = 4800 poses
interval_coverage = 1-2/2^timing_blocks = 1 - 2 / 2 ^ 7 = 0.984375 fraction
calibration_projection_usd = calibration_hours*h100_price*gpu_count+calibration_reserve_usd = 3 * 3.29 * 1 + 10.12 = 19.99 USD
planned_hours = calibration_hours+agreement_hours+timing_hours+quality_hours+archive_hours = 3 + 3 + 6 + 6 + 2 = 20 hours
planned_compute_usd = planned_hours*h100_price*gpu_count = 20 * 3.29 * 1 = 65.8 USD
contingency_usd = budget_usd-planned_compute_usd = 100 - 65.8 = 34.2 USD
calibration_box.hours = calibration_hours = 3 = 3 h
agreement_box.hours = agreement_hours = 3 = 3 h
timing_box.hours = timing_hours = 6 = 6 h
quality_box.hours = quality_hours = 6 = 6 h
archive_box.hours = archive_hours = 2 = 2 h
contingency.usd = budget_usd-(calibration_box+agreement_box+timing_box+quality_box+archive_box) = 100 - (9.87 + 9.87 + 19.74 + 19.74 + 6.58) = 34.2 usd
persistent_storage.usd = fs_gib*fs_usd_gib_month = 0 * 0.2 = 0 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:anchor` PARTIAL · page: "\text{DockQ}=\frac{1}{3}\left({\mathrm{f}}_{\text{nat}}+\frac{1}{1+{\left(\frac{\text{iRMSD}}{a}\right)}^{2}}+\frac{1}{1+{\left(\frac{\text{LRMSD}}{b}\right)}^{2}}\right)" · note: Recorded quote appears. Equation supports self-score 1 with complete contacts and zero RMSDs. Page does not establish CPU/GPU pose agreement or completed validation for this plan; these require evidence if asserted as results.
- sample 1 · `card:limits` PARTIAL · page: "" · note: Case count and inference limits describe planned scope. Claim that exploratory history was already exposed is factual and has no source.
- sample 1 · `src:prior` PARTIAL · page: "#GPUs | 105 | 210 | 315 | 420 | 630 | 840 | 1,050 | 1,260
Thinノードは2ソケットのIntel Xeon X5670 CPU (2.93GHz, 6 cores) と3枚のNVIDIA Tesla K20X (GK110) GPUを搭載しています．" · note: Recorded quote appears. Page supports 352 calculations on Xeon X5670/Tesla K20X hardware and leaves rotation count unspecified. It does not establish comparative claim that this is nearest prior result.
- sample 1 · `num:rot_standard` UNREACHABLE · page: "" · note: Pinned raw URL repeatedly returned fetch failure, Cache miss. Matching GitHub blob URL also failed; quote and value unverified.
- sample 1 · `num:rot_dense` UNREACHABLE · page: "" · note: Pinned raw URL repeatedly returned fetch failure, Cache miss. Matching GitHub blob URL also failed; quote and value unverified.
- sample 2 · `card:anchor` PARTIAL · page: "DockQ assesses the quality of a multimeric model by comparing it to a reference structure (typically an experimentally determined structure)." · note: Recorded quote appears. Equation (1) gives self-score 1 when native contacts are complete and both RMSDs zero. CPU/GPU pose agreement is unsupported as an established fact; if intended as a future validation requirement, it needs no source.
- sample 2 · `card:limits` PARTIAL · page: "" · note: Scope and inference limits need no source. Claim that exploratory history was already exposed has no supporting source.
- sample 2 · `src:prior` PARTIAL · page: "Thinノードは2ソケットのIntel Xeon X5670 CPU (2.93GHz, 6 cores) と3枚のNVIDIA Tesla K20X (GK110) GPUを搭載しています．" · note: Recorded GPU row appears; page supports 352 calculations on older hardware and leaves rotation count unspecified. 'Nearest' published result cannot be established from this page.
- sample 2 · `num:rot_standard` UNREACHABLE · page: "" · note: Pinned raw URL and corresponding GitHub page failed to fetch with cache-miss errors; quote and value unverified.
- sample 2 · `num:rot_dense` UNREACHABLE · page: "" · note: Pinned raw URL and corresponding GitHub page failed to fetch with cache-miss errors; quote and value unverified.

**Critic.**
- stakes 5 · `card:question` "Can GPU docking make 54000 rotations affordable within CPU 3600-rotation workflow budgets, improving pose recovery across 4 unbound complexes?" · Either outcome changes whether to fund dense search for these four cases; complete workflow time, cost and recovery directly measure that choice.
- lever 3 · `plan:predictions.noise_rule` "One untallied warmup per configuration; 7 randomized matched blocks, each configuration running all 4 cases serially. Use fixed randomization seed 20261103. Per block compute ratio of summed complete per-case walls; derive exact distributio…" · Search spans 15× with inputs fixed, but noise rule provides no bound establishing predicted differences exceed run-to-run variation.
- verifiable 3 · `card:anchor` "CPU and GPU standard poses agree; native self-comparison and independent DockQ checks validate evaluation before dense scoring. Tolerance: DESIGN, sealed before fresh comparisons: identical ranked rotation/translation identifiers and ranks …" · Independent native references and evaluator checks establish external truth. Native self-comparison checks identity, but does not reproduce a published measured result.
- open 5 · `card:closest_prior` "MEGADOCK times 352 docking jobs up to 1260 GPUs; maximum rotations unspecified, leaving matched complete-workflow search budgets unresolved [prior]." · Published multi-GPU docking throughput leaves dense sampling and matched complete-workflow budget recovery unanswered; card states this gap.
- reshape 2 · `plan:scope_gap[0]` "Existing GPU kernels split docking work; no new algorithm removes sequential workflow stages. No independent-copies throughput claim." · Existing GPU kernels split docking work within one stage; retrieval, docking, reconstruction, evaluation and export remain sequential.
- baseline NA · `card:method` "none" · Restructuring method is none; criterion explicitly allows NA.

**Producer says (not judged).** expected unsure (User-supplied exploratory history suggests standard acceleration and mixed dense quality, but complete workflow affordability and prospective agreement remain unestablished.); compute_tested yes (Changes search from 3600 to 54000 rotations using existing GPU implementation; measures complete answer latency and recovery, not bundled-job throughput [commands].); decides partly; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
- cost record repaired: 1 expression(s) rewritten
- quote at numbers.billing_minutes.quote: 1 does not appear in the quote "ODC prices instances by hourly usage and bills in one-minute increments."; a value transformed from the page belongs in a DERIVED number
- gate in calibration fails at the plan's own value: Bounded calibration projection from timer, excluding tax covered by contingency is 20, needs ≤ 20; expected path: Do not launch, or terminate current calibration; report execution-chain gap and measured partial work.
- thin headroom: the budget is reached if Maximum complete per-case evaluation runtime; unknown until agreement is 1.0× higher
- predictions.if_lever: a sentence of 21 words
- test_summary: a sentence of 26 words
- test_summary: rewritten by the field repair
- card field test_summary still fails: dollar figure
- dramaturg findings failed G-find after a resample; decided as returned
- dramaturg-2 findings failed G-find after a resample; decided as returned
- prose over 240 words (299)

**Root question (null).** Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget? Small pilot on exactly four unbound PINDER 2024-02 cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Compare existing MEGADOCK CPU standard 3600 rotations, GPU standard 3600, and GPU documented dense 54000 (-D). Keep scoring and retained predictions fixed at 50. Pin prepared input bytes, references, binary/dependency/settings/thread/allocation identities. First establish execution correctness and scientific CPU/GPU agreement at identical settings using justified numerical tolerances sealed before fresh comparison. Then assess dense-search DockQ for rank1 and best50 separately, per case; native references only for evaluation. Calibrate runtime before choosing feasible common budgets; seal configurations, timing repetitions, comparison/noise rules and total spending cap before quality evaluation. Report complete workflow time, GPU activity and billed allocation cost, separating setup/retrieval from steady-state work. Keep acceleration, agreement and additional-search quality conclusions separate. Preserve negatives, unavailable budget arms and overruns. No biological efficacy or beyond-four-case inference. Run2 already exposed quality, so fresh executions are prospective replication under new rules, never unseen holdout or retrospective preregistration. Do not substitute throughput of bundled runs for this question. Repository /home/hal/dev/interp/metis: seed experiments/blind-02/m5/BRIEF.md; case preparation/source/reference pins experiments/blind-02/m5/b01_materials/BRIEF_run1.md:48-158; full prior trace experiments/blind-02/m5/run2_trace/REPORT.md; new assessment experiments/blind-02/science/s01/ASSESSMENT.md. Run2 measured docking totals CPU/GPU/dense 40.07/6.85/69.38 seconds, not complete workflows; standard CPU/GPU transforms and DockQ matched, score max deltas 0.04/0.03/0.04/0.14 with no acceptance tolerance. Dense best50 improved all four observations, rank1 worsened in two including 1nr5. These are exploratory, not sealed conclusions. Historical H100 PCIe rate USD3.29/hour, setup145s, whole unscored bundle median131.9565s; old receipts setup/anchors/freeze/upload/profile/concurrency 145/1571/1402/1424/2832/3448s. Historical allocation and transport observations are estimates for a fresh box, not new producer measurements or public citations. Tree plans only, no box execution. Full card plan ceiling USD100; each later calibration must project below USD20 including setup, retrieval and idle, preferably USD5-10, soft6h/hard12h. Do not run full experiments on calibration route. Identify specific file/section gaps if existing routes cannot implement comparison. Tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases. Measure compilation carries uncertain scalar inputs and phases, not arms/decision_rule; checks 2.5x PROXY or 3x other estimate bands, never scientific equivalence. Measure execution requires missing stage args/controller to be established. Card factual web sources may be checked; do not fabricate citations for private records.

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/seed/idea/370cabd5/producer.md)

---

<a id="card-seed-idea-3"></a>**3 · Dense search changes candidate recovery and ranking differently.** seed pick · compute tested: yes · plan expects: unsure · REJECT

**Question.** Can affordable GPU search across 54000 rotations improve best50 DockQ while worsening rank1, compared with 3600 rotations on four apo cases?

**What is known.** Published MEGADOCK benchmark timed parallel execution across 30976 docking jobs; rotation maximum is unspecified here, and it does not settle four-case DockQ tradeoffs. [prior] Whether 54000 versus 3600 rotations, fixed 50 outputs, changes best50 and rank1 differently within calibrated budgets on these four apo cases.

**Hypothesis.** More rotations recover better candidates, but unchanged scoring can rank worse poses first, separating best50 gains from rank1 losses.

**If compute is the lever.** At 54000 rotations, best50 DockQ gains exceed 0.01 and calibrated noise; rank1 may decline, within common complete-workflow budgets.

**If not.** At 54000 rotations, best50 gains fail 0.01 or noise thresholds, or complete workflows exceed common budgets; rank1 remains separately reported.

**Test.** Validate independent scorer and CPU/GPU standard agreement first. Calibrate complete-workflow budgets, seal noise rules, then compare three paired 3600/54000-rotation repeats on four cases, fixed 50 outputs; report rank1 and best50 separately.

*Compute axis.* Rotations searched per docking job, holding retained outputs fixed: 3,600–54,000 rotations, 2 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** Reproduce independent DockQ example, then require matching CPU/GPU standard transforms, rankings and DockQ before dense quality evaluation. [dockq] Tolerance: DESIGN: documented example first-interface score within 0.0005 of printed 0.994; unrounded cross-scorer discrepancy<=0.00001 on identical mappings. Seal docking-score tolerance=max(0.000001,2*maximum independent-fixture CPU/GPU score difference), capped at 0.2, before selected-case agreement. Fresh standard requires identical ordered rotation/translation identifiers and DockQ endpoint differences<=0.0001. Failure stops comparison; no tuning to selected-case quality..

**Would not show.** Four selected apo cases only; exposed prior quality; prospective replication, not holdout. No biological efficacy, population generalization, or ranking improvement inferred from best50 gains.

*Cost.* Plans $25 of the $100 budget over 6 machine-hours, leaving $75. Main guess: Conservative caps admitting both complete GPU workflows on every case [g], measured after $6.58 of spend; the budget is reached if it is 1.0× higher. 2 cost flags in the block.

**Judges.** Dramaturg: REJECT (2 blocking). Decides at: $16 at compare · plan $25 · 2 GUESS (critic: Comparison supplies paired quality, noise validity and measured budget eligibility; earlier gates can stop work but cannot resolve successful-path recovery outcomes).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $100 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-11-03 · filesystem $0.20/GiB-month [q]
Spend      calibrate  All-inclusive calibration time box: setup, retrieval, build, idle, timings and cleanup; USD6.58 before tax.  1x NVIDIA H100 PCIe 80GB $3.29/h  2 h [=]  $6.58
           compare  Shared agreement and paired-quality time box, including CPU evaluation, setup and idle; USD9.87 before tax.  1x NVIDIA H100 PCIe 80GB $3.29/h  3 h [=]  $9.87
           export  Export and termination allowance across rentals; USD3.29 before tax.  1x NVIDIA H100 PCIe 80GB $3.29/h  1 h [=]  $3.29
           export  No persistent filesystem provisioned. Use instance disk and export artifacts. Example filesystem rate is not guaranteed tariff [filesystem].  [=]  $0
           export  USD5.26 reserved for applicable tax and billing uncertainty; cannot fund extra experiments. Recheck actual billing projection before allocation.  [=]  $5.26
           Planned $25 · unallocated $75 · cap $25
Rests on   Conservative caps admitting both complete GPU workflows on every case 1 caps [g] rests on: User exploratory docking totals suggest feasibility but omit reconstruction, scoring, setup and retrieval. Unverified count is a gate, not a promise of completed comparisons. · measured in calibrate ($6.58 spent by then) · gate Conservative caps admitting both complete GPU workflows on every case ≥ 1 in calibrate (now 1, passes; uncut plan at it $25), else Export calibration evidence and stop; no scientific rental or dense quality comparison. · budget reached at 1 (1.0× higher)
           All-case standard agreement and scorer pass 1 boolean [g] rests on: User reports earlier matching transforms and DockQ without sealed tolerance; prospective agreement can fail. · measured in agreement ($6.58 spent by then) · gate All-case standard agreement and scorer pass ≥ 1 in agreement (now 1, passes; uncut plan at it $25), else Stop scientific comparison; retain disagreement report and receipts. · budget reached at 1 (1.0× higher)
Scenarios  none
Buys       User-selected apo cases: 4 [d]
           Paired GPU quality repetitions per case: 3 [d]
           Retained predictions per search: 50 [d]
           Paired GPU search jobs excluding agreement: 24 [=]
           Primary pose scoring including rescoring, excluding independent fixtures: 7,200 [=]
Flags      thin headroom: the budget is reached if Conservative caps admitting both complete GPU workflows on every case is 1.0× higher
           thin headroom: the budget is reached if All-case standard agreement and scorer pass is 1.0× higher
Full scale none
Outside    DESIGN: unpaid implementation, review and interpretation: 12 person-hours · DESIGN: new external services or third-party compute purchases: 0 USD · DESIGN: existing local workstation and artifact retention; no new purchase: 0 USD
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
width_factor = dense_rot / standard_rot = 54000 / 3600 = 15 ratio
quality_jobs = cases * paired_repeats * gpu_arms = 4 * 3 * 2 = 24 jobs
agreement_jobs = cases * agreement_repeats * agreement_arms = 4 * 3 * 2 = 24 jobs
pose_scores = (quality_jobs + agreement_jobs) * retained * rescore_repeats = (24 + 24) * 50 * 3 = 7200 evaluations
compute_usd = (calibration_h + science_h + export_h) * h100_price * gpus = (2 + 3 + 1) * 3.29 * 1 = 19.74 USD
reserve_usd = credit_stop - compute_usd = 25 - 19.74 = 5.26 USD
calibration_box.hours = calibration_h = 2 = 2 h
science_box.hours = science_h = 3 = 3 h
export_box.hours = export_h = 1 = 1 h
persistent_storage.usd = persistent_gib * fs_usd_gib_month = 0 * 0.2 = 0 usd
billing_reserve.usd = reserve_usd = 5.26 = 5.26 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:closest_prior` UNREACHABLE · page: "" · note: PubMed fetch returned only footer link; retry failed. Recorded caption and benchmark claims could not be checked.
- sample 1 · `src:prior` UNREACHABLE · page: "" · note: PubMed fetch returned only footer link; retry failed. Quote and distinction between jobs and rotations could not be verified.
- sample 2 · `card:limits` PARTIAL · page: "" · note: Scope and inference limits need no source. Claim of exposed prior quality lacks cited evidence.

**Critic.**
- stakes 5 · `card:if_not` "At 54000 rotations, best50 gains fail 0.01 or noise thresholds, or complete workflows exceed common budgets; rank1 remains separately reported." · Either outcome changes whether to spend fixed budgets on dense search; test directly measures complete-workflow affordability and pose recovery.
- lever 5 · `plan:predictions.noise_rule` "DESIGN: independently validate scorer fixtures and precision before fresh quality. On three CPU/GPU standard repeats per case, seal endpoint epsilon=max(0.000001,2*standard-repeat range,10*independent-scorer discrepancy). Abort if epsilon>0…" · Compute increases 15×; inputs, scoring and retained poses stay fixed. Required gains exceed sealed noise, with violations invalidating cases.
- verifiable 5 · `plan:anchor` "Reproduce independent DockQ example, then require matching CPU/GPU standard transforms, rankings and DockQ before dense quality evaluation. [dockq] Tolerance: DESIGN: documented example first-interface score within 0.0005 of printed 0.994; …" · Independent native references ground DockQ; independent published example must reproduce 0.994 within 0.0005 before comparison.
- open 5 · `card:closest_prior` "Published MEGADOCK benchmark timed parallel execution across 30976 docking jobs; rotation maximum is unspecified here, and it does not settle four-case DockQ tradeoffs. [prior]" · Published benchmark measures parallel throughput across docking jobs; it leaves fixed-budget rotation density and separate rank1/best50 recovery unanswered.
- reshape 1 · `card:method` "none" · No dependency removed. Search, reconstruction and scoring remain sequential; existing GPU implementation supplies acceleration.
- baseline NA · `card:method` "none" · Restructuring method is none; criterion explicitly permits NA.

**Producer says (not judged).** expected unsure (User-supplied exploratory history suggests recovery gains with ranking losses, but fresh timing, agreement and calibrated repeatability remain unestablished.); compute_tested yes (DESIGN: vary search width by factor 15, fixed scoring and 50 retained poses; test additional search bought with GPU time.); decides no; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
- thin headroom: the budget is reached if Conservative caps admitting both complete GPU workflows on every case is 1.0× higher
- thin headroom: the budget is reached if All-case standard agreement and scorer pass is 1.0× higher
- question: a sentence of 21 words
- test_summary: a sentence of 23 words
- novelty.closest_prior: a sentence of 23 words
- novelty.left_open: a sentence of 21 words
- dramaturg findings failed G-find after a resample; decided as returned
- dramaturg-2 findings failed G-find after a resample; decided as returned
- prose over 240 words (263)

**Root question (null).** Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget? Small pilot on exactly four unbound PINDER 2024-02 cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Compare existing MEGADOCK CPU standard 3600 rotations, GPU standard 3600, and GPU documented dense 54000 (-D). Keep scoring and retained predictions fixed at 50. Pin prepared input bytes, references, binary/dependency/settings/thread/allocation identities. First establish execution correctness and scientific CPU/GPU agreement at identical settings using justified numerical tolerances sealed before fresh comparison. Then assess dense-search DockQ for rank1 and best50 separately, per case; native references only for evaluation. Calibrate runtime before choosing feasible common budgets; seal configurations, timing repetitions, comparison/noise rules and total spending cap before quality evaluation. Report complete workflow time, GPU activity and billed allocation cost, separating setup/retrieval from steady-state work. Keep acceleration, agreement and additional-search quality conclusions separate. Preserve negatives, unavailable budget arms and overruns. No biological efficacy or beyond-four-case inference. Run2 already exposed quality, so fresh executions are prospective replication under new rules, never unseen holdout or retrospective preregistration. Do not substitute throughput of bundled runs for this question. Repository /home/hal/dev/interp/metis: seed experiments/blind-02/m5/BRIEF.md; case preparation/source/reference pins experiments/blind-02/m5/b01_materials/BRIEF_run1.md:48-158; full prior trace experiments/blind-02/m5/run2_trace/REPORT.md; new assessment experiments/blind-02/science/s01/ASSESSMENT.md. Run2 measured docking totals CPU/GPU/dense 40.07/6.85/69.38 seconds, not complete workflows; standard CPU/GPU transforms and DockQ matched, score max deltas 0.04/0.03/0.04/0.14 with no acceptance tolerance. Dense best50 improved all four observations, rank1 worsened in two including 1nr5. These are exploratory, not sealed conclusions. Historical H100 PCIe rate USD3.29/hour, setup145s, whole unscored bundle median131.9565s; old receipts setup/anchors/freeze/upload/profile/concurrency 145/1571/1402/1424/2832/3448s. Historical allocation and transport observations are estimates for a fresh box, not new producer measurements or public citations. Tree plans only, no box execution. Full card plan ceiling USD100; each later calibration must project below USD20 including setup, retrieval and idle, preferably USD5-10, soft6h/hard12h. Do not run full experiments on calibration route. Identify specific file/section gaps if existing routes cannot implement comparison. Tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases. Measure compilation carries uncertain scalar inputs and phases, not arms/decision_rule; checks 2.5x PROXY or 3x other estimate bands, never scientific equivalence. Measure execution requires missing stage args/controller to be established. Card factual web sources may be checked; do not fabricate citations for private records.

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/seed/idea/360caa42/producer.md)

---

<a id="card-seed-idea-4"></a>**4 · CPU host scheduling as workflow affordability calibration.** seed pick · compute tested: partly · plan expects: unsure · PASS

**Question.** Can concurrent CPU docking jobs reduce complete workflow cost while preserving every output across four fixed cases?

**What is known.** MEGADOCK reported 98% scaling at 420 heterogeneous nodes; it did not test fixed-thread CPU job concurrency on one host. [prior] Whether widths 2 or 4 preserve every output and exceed 1.05 speed factor twice on one fixed host.

**Hypothesis.** Concurrent independent jobs may fill idle CPU capacity, reducing workflow time without changing docking calculations or retained poses.

**If compute is the lever.** Width 2 or 4 preserves outputs and achieves at least 1.05 speed factor in both repeats against nearby original serial blocks.

**If not.** Widths 2 and 4 preserve outputs but fail the 1.05 speed-factor threshold in at least one repeat each.

**Test.** Compare original four-case serial run, four separate serial jobs, and 2 or 4 concurrent jobs, keeping 26 threads per job. Require identical outputs and nearby original serial times divided by concurrent times >=1.05 in both repeats. Allocation time limit costs $6.58 before tax.

*Compute axis.* Independent CPU docking jobs allowed to run concurrently on one fixed host: 1–4 concurrent jobs, 3 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** Reproduce frozen CPU docking records and every retained pose exactly; then verify separate serial units against fresh original execution. Tolerance: 0 differing scientific bytes, 0 missing or extra scientific files, identical stable relative paths. Exclude only predeclared volatile logs and timestamps..

**Would not show.** CPU scheduling screen only; no GPU acceleration, dense-search recovery, biological efficacy, population generalization or confidence claim from two repeats.

*Cost.* Plans $6.58 of the $100 budget over 2 machine-hours, leaving $93.42.

**Judges.** Dramaturg: PASS 2/2. Decides at: none · plan $7 · 0 GUESS (critic: Probe measures independent-job scheduling throughput only; no phase tests GPU affordability or dense-search pose recovery within fixed budgets).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $100 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-11-03
Spend      setup  Retrieval, build, identity checks and all associated idle time  1x NVIDIA H100 PCIe 80GB $3.29/h  0.5 h [=]  $1.65
           anchor  Initial original serial and separate serial blocks plus equality checks  1x NVIDIA H100 PCIe 80GB $3.29/h  0.25 h [=]  $0.82
           probe  Remaining sealed blocks, complete pose generation and resource diagnostics  1x NVIDIA H100 PCIe 80GB $3.29/h  1 h [=]  $3.29
           export  Artifact export, final billing record and allocation termination  1x NVIDIA H100 PCIe 80GB $3.29/h  0.25 h [=]  $0.82
           Planned $6.58 · unallocated $93.42 · cap $10
Rests on   none
Scenarios  none
Buys       Fixed supplied apo cases: 4 [d]
           Maximum complete timing blocks: 8 [=]
           Maximum docking executions if every arm finishes: 32 [=]
           Retained pose artifacts across all executions: 1,600 [=]
           Unique case and rank slots; repetitions add no science: 200 [=]
Flags      none
Full scale none
Outside    Human preparation design allowance; unpaid by Lambda credits: 4 person hours · Paid persistent filesystem; none provisioned: 0 GiB
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
max_threads = threads * width_four = 26 * 4 = 104 threads
blocks = arm_count * repeats = 4 * 2 = 8 blocks
docking_jobs = blocks * cases = 8 * 4 = 32 jobs
pose_artifacts = docking_jobs * retained = 32 * 50 = 1600 pose artifacts
unique_pose_slots = cases * retained = 4 * 50 = 200 case/rank slots
total_h = setup_h + anchor_h + probe_h + export_h = 0.5 + 0.25 + 1 + 0.25 = 2 instance hours
allocation_usd = total_h * gpu_count * gpu_rate = 2 * 1 * 3.29 = 6.58 USD
setup_box.hours = setup_h = 0.5 = 0.5 h
anchor_box.hours = anchor_h = 0.25 = 0.25 h
probe_box.hours = probe_h = 1 = 1 h
export_box.hours = export_h = 0.25 = 0.25 h
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:test_summary` PARTIAL · page: "" · note: Comparison, thread count and thresholds specify planned test. Factual $6.58 before-tax allocation cost has no source; unsupported.
- sample 2 · `card:test_summary` PARTIAL · page: "" · note: Comparisons, thread count and thresholds specify planned test. Allocation cost of $6.58 before tax is factual but has no source.

**Critic.**
- stakes 5 · `card:if_lever` "Width 2 or 4 preserves outputs and achieves at least 1.05 speed factor in both repeats against nearby original serial blocks." · Passing advances concurrent CPU scheduling; failure deprioritizes unchanged-thread concurrency. Complete workflow timing directly measures that choice.
- lever 1 · `plan:compute_axis` "{"quantity":"Independent CPU docking jobs allowed to run concurrently on one fixed host","unit":"concurrent jobs","levels":[1,2,4]}" · Concurrency spans only 4×; noise rule supplies no bound establishing that 5% gain exceeds run-to-run noise. Two conditions fail.
- verifiable 1 · `card:anchor` "Reproduce frozen CPU docking records and every retained pose exactly; then verify separate serial units against fresh original execution. Tolerance: 0 differing scientific bytes, 0 missing or extra scientific files, identical stable relativ…" · Frozen CPU records and fresh serial outputs come from same docking implementation; exact equality checks consistency, without independent truth or published-number reproduction.
- open 5 · `card:closest_prior` "MEGADOCK reported 98% scaling at 420 heterogeneous nodes; it did not test fixed-thread CPU job concurrency on one host. [prior]" · Published heterogeneous-node scaling does not answer fixed-thread CPU concurrency on one host; card states gap.
- reshape 1 · `card:method` "none" · Independent case jobs run side by side; no sequential dependency removed.
- baseline NA · `card:method` "none" · Restructuring method is none; criterion explicitly permits NA.

**Producer says (not judged).** expected unsure (Fixed thread counts may leave exploitable idle capacity or cause contention; this plan assumes neither outcome.); compute_tested partly (Concurrency varies while host resources remain fixed. Test measures host scheduling efficiency, not benefits from buying additional GPUs or CPU cores.); decides no; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd: set by the question
- predictions.if_lever: a sentence of 21 words
- test_summary: rewritten by the field repair
- card field test_summary still fails: dollar figure
- dramaturg findings failed G-find after a resample; decided as returned
- dramaturg-2 findings failed G-find after a resample; decided as returned

**Root question (null).** Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget? Small pilot on exactly four unbound PINDER 2024-02 cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Compare existing MEGADOCK CPU standard 3600 rotations, GPU standard 3600, and GPU documented dense 54000 (-D). Keep scoring and retained predictions fixed at 50. Pin prepared input bytes, references, binary/dependency/settings/thread/allocation identities. First establish execution correctness and scientific CPU/GPU agreement at identical settings using justified numerical tolerances sealed before fresh comparison. Then assess dense-search DockQ for rank1 and best50 separately, per case; native references only for evaluation. Calibrate runtime before choosing feasible common budgets; seal configurations, timing repetitions, comparison/noise rules and total spending cap before quality evaluation. Report complete workflow time, GPU activity and billed allocation cost, separating setup/retrieval from steady-state work. Keep acceleration, agreement and additional-search quality conclusions separate. Preserve negatives, unavailable budget arms and overruns. No biological efficacy or beyond-four-case inference. Run2 already exposed quality, so fresh executions are prospective replication under new rules, never unseen holdout or retrospective preregistration. Do not substitute throughput of bundled runs for this question. Repository /home/hal/dev/interp/metis: seed experiments/blind-02/m5/BRIEF.md; case preparation/source/reference pins experiments/blind-02/m5/b01_materials/BRIEF_run1.md:48-158; full prior trace experiments/blind-02/m5/run2_trace/REPORT.md; new assessment experiments/blind-02/science/s01/ASSESSMENT.md. Run2 measured docking totals CPU/GPU/dense 40.07/6.85/69.38 seconds, not complete workflows; standard CPU/GPU transforms and DockQ matched, score max deltas 0.04/0.03/0.04/0.14 with no acceptance tolerance. Dense best50 improved all four observations, rank1 worsened in two including 1nr5. These are exploratory, not sealed conclusions. Historical H100 PCIe rate USD3.29/hour, setup145s, whole unscored bundle median131.9565s; old receipts setup/anchors/freeze/upload/profile/concurrency 145/1571/1402/1424/2832/3448s. Historical allocation and transport observations are estimates for a fresh box, not new producer measurements or public citations. Tree plans only, no box execution. Full card plan ceiling USD100; each later calibration must project below USD20 including setup, retrieval and idle, preferably USD5-10, soft6h/hard12h. Do not run full experiments on calibration route. Identify specific file/section gaps if existing routes cannot implement comparison. Tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases. Measure compilation carries uncertain scalar inputs and phases, not arms/decision_rule; checks 2.5x PROXY or 3x other estimate bands, never scientific equivalence. Measure execution requires missing stage args/controller to be established. Card factual web sources may be checked; do not fabricate citations for private records.

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/seed/idea/310ca263/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|
| R1:interp:I1 | Exact score attribution and controlled ablation | ADJACENT | Docking score attribution and ablation | 7 | not_picked | not drawn |
| R1:interp:I2 | Differential tracing of CPU/GPU numerical disagreement | SAME | CPU GPU numerical divergence diagnosis | 11 | picked_top | no open option; highest total |
| R1:interp:I3 | Protein-language-model SAE hypothesis audit | ELSEWHERE | Protein language model feature interventions | 11 | not_eligible | ELSEWHERE; not drawn for the pool |
| R1:physical:P1 | Denser rigid-body search: recovery versus ranking | SAME | Rigid docking angular search accuracy | 10 | picked_top | highest total with open >= 3 |
| R1:physical:P2 | Fixed-search docking throughput | ADJACENT | Fixed docking computational throughput | 4 | not_eligible | compute_open settled, sequential none |
| R1:physical:P3 | Massive multimer sampling and long recycling | ELSEWHERE | AlphaFold multimer sampling accuracy | 8 | not_eligible | ELSEWHERE; not drawn for the pool |
| R1:physical:P4 | GPU molecular dynamics for native-interface recovery | ELSEWHERE | Molecular dynamics native interface recovery | 8 | not_eligible | ELSEWHERE; not drawn for the pool |

## Log

```
R1: NOT COMPUTE-BOUND, 2 compute signal(s) -> WIDENER + INTERP
R1:physical: no reshape option
R1:interp: no reshape option
R1:interp: no open option; top taken by total
pool: 3 candidate cluster(s); picked 0
seed:idea:seed: dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
seed:idea:seed: G-plan repair: planned $100.00 over $100.00 while stated $100.00 is not
seed:idea:seed: dropped the producer's definition of budget_usd: set by the question
seed:idea:seed: novelty.closest_prior: a sentence of 21 words
seed:idea:seed: novelty.left_open: a sentence of 21 words
R1:physical:top: dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
R1:physical:top: predictions.if_not: a sentence of 22 words
R1:physical:top: test_summary: a sentence of 27 words
seed:idea:seed: cost record repaired: 1 expression(s) rewritten
seed:idea:seed: quote at numbers.billing_minutes.quote: 1 does not appear in the quote "ODC prices instances by hourly usage and bills in one-minute increments."; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: gate in calibration fails at the plan's own value: Bounded calibration projection from timer, excluding tax covered by contingency is 20, needs ≤ 20; expected path: Do not launch, or terminate current calibration; report execution-chain gap and measured partial work.
seed:idea:seed: thin headroom: the budget is reached if Maximum complete per-case evaluation runtime; unknown until agreement is 1.0× higher
seed:idea:seed: predictions.if_lever: a sentence of 21 words
seed:idea:seed: test_summary: a sentence of 26 words
seed:idea:seed: card fields failing: test_summary (dollar figure)
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
R1:interp:top: dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
R1:interp:top: gate in seal fails at the plan's own value: Unestablished scientific acceptance contract; conservative placeholder is 0, needs ≥ 1; expected path: Diagnostic-only audit allowed; no scientific acceptance or dense-quality release.
R1:interp:top: gate in analyze fails at the plan's own value: Unmeasured successfully localized injections; conservative placeholder is 0, needs ≥ 6; expected path: Reject tracing reliability; retain negative result and block scientific handoff.
R1:interp:top: halted at G-plan: compute_tested is no: This is a bounded diagnostic audit. The 8-to-16 execution axis adds repeat checks, not a test that more parallel hardware changes docking quality or supplies tolerances. No GPU scaling claim.
R1:physical:top: dramaturg: degenerate: card:question; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits; degenerate: num:gpu_count
seed:idea:seed: test_summary: rewritten by the field repair
seed:idea:seed: card field test_summary still fails: dollar figure
seed:idea:seed: dropped the producer's definition of budget_usd: set by the question
seed:idea:seed: predictions.if_lever: a sentence of 21 words
seed:idea:seed: card fields failing: test_summary (dollar figure)
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
R1:physical:top: dramaturg (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
R1:physical:top: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: test_summary: rewritten by the field repair
seed:idea:seed: card field test_summary still fails: dollar figure
R1:physical:top: dramaturg-2: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
R1:physical:top: dramaturg-2 (resample): degenerate: card:question; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
R1:physical:top: dramaturg-2 findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg-2: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
seed:idea:seed: dramaturg-2: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg-2 (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
seed:idea:seed: dramaturg-2 findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg-2 (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg-2 findings failed G-find after a resample; decided as returned
seed:idea:seed: dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
seed:idea:seed: thin headroom: the budget is reached if Conservative caps admitting both complete GPU workflows on every case is 1.0× higher
seed:idea:seed: thin headroom: the budget is reached if All-case standard agreement and scorer pass is 1.0× higher
seed:idea:seed: question: a sentence of 21 words
seed:idea:seed: test_summary: a sentence of 23 words
seed:idea:seed: novelty.closest_prior: a sentence of 23 words
seed:idea:seed: novelty.left_open: a sentence of 21 words
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg-2: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open
seed:idea:seed: dramaturg-2: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg-2 (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg-2 findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg-2 (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
seed:idea:seed: dramaturg-2 findings failed G-find after a resample; decided as returned
R1:physical:top: prose over 240 words (295)
R1:interp:top: prose over 240 words (250)
seed:idea:seed: prose over 240 words (254)
seed:idea:seed: prose over 240 words (299)
seed:idea:seed: prose over 240 words (263)
```