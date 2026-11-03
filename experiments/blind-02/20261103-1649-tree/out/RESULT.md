# Result

Picks 5 · PASS 1 · on-goal cards U4 0 · U3 1 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [R1·phys·P1](#card-R1-physical-P1) Angular-search saturation at fixed output count | REJECT (1 blocking) | top 1/5 · SAME, tie of 2 broken by seeded order | unsure | 5 | 5 → 5 | 5 → 5 | 3 | — | 1 → 1 | — | $36 at comparison · plan $39 · 0 GUESS |
| [seed·idea·2](#card-seed-idea-2) Complete-workflow acceleration and dense-search affordability | PASS 2/2 | seed | unsure | 5 | — → 5 | — → 5 | 5 | — | — → 1 | — | $49 at report · plan $49 · 2 GUESS |
| [seed·idea·3](#card-seed-idea-3) Dense search changes candidate recovery and ranking differently | REJECT (2 blocking) | seed | unsure | 5 | — → 5 | — → 5 | 5 | — | — → 1 | — | $30 at science · plan $30 · 2 GUESS |
| [seed·idea·1](#card-seed-idea-1) Agreement before interpreting acceleration or denser search | REJECT (2 blocking) | seed | unsure | 1 | — → 5 | — → 5 | 3 | — | — → 1 | — | $26 at compare · plan $40 · 0 GUESS |
| [seed·idea·4](#card-seed-idea-4) CPU host scheduling as workflow affordability calibration | REJECT (2 blocking) | seed | unsure | 1 | — → 5 | — → 5 | 1 | — | — → 1 | — | none · plan $7 · 0 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-R1-physical-P1"></a>**P1 · Angular-search saturation at fixed output count.** R1 · physical · top pick · distance SAME · compute tested: yes · plan expects: unsure · REJECT

**Question.** Does increasing rotations from 3600 to 54000 improve rank1 and best50 DockQ on four apo pairs within matched complete-workflow budgets?

**What is known.** MEGADOCK measured runtime through 1000000 docking jobs [prior]; guide documents 54000 rotations [angles], without fixed-50 DockQ width comparisons. Whether 54000 versus 3600 rotations improves rank1 or best50 on these four apo cases while completed workflows meet common budgets.

**Hypothesis.** Denser angular search improves best50 DockQ by finding better poses, while fixed scoring can leave rank1 worse.

**If compute is the lever.** At 54000 rotations, best50 DockQ rises beyond 0.01 and noise; rank1 changes separately, with both arms completing matched budgets.

**If not.** At 54000 rotations, best50 DockQ stays within 0.01 or noise, worsens, or fails matched budgets; rank1 may worsen.

**Test.** Build sealed three-arm controller; validate CPU/GPU agreement at 3600 rotations, then compare GPU 54000 against GPU and CPU 3600 under common workflow caps, retaining 50 poses and separate per-case rank1/best50 DockQ.

*Compute axis.* Rotational search width per docking job: 3,600–54,000 rotations, 2 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** CPU standard anchors GPU poses and scores; independent transform reconstruction and DockQ fixtures validate evaluation before dense comparisons. Tolerance: DESIGN: exact ranked transform identities and pose bytes; DockQ absolute error <= dockq_tol. Score absolute-plus-relative tolerances remain unset until independent arithmetic/FFT certification in numerical_gate. No tolerance derived from historical score maxima. Certification absent means agreement UNKNOWN and dense inference blocked..

**Would not show.** Four previously examined cases; prospective replication after exploratory exposure, not unseen validation. No biological efficacy, population generalization or saturation plateau.

*Cost.* Plans $39.48 of the $100 budget over 12 machine-hours, leaving $60.52. Pilot gate: Time-box calibration projection; reprice before launch ≤ 20, else Do not launch; repair route or reduce scope and reseal..

**Judges.** Dramaturg: REJECT (1 blocking). Decides at: $36 at comparison · plan $39 · 0 GUESS (critic: First phase measuring agreement, per-case dense-search quality and complete-workflow affordability; failures and unavailable arms remain explicit outcomes).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $100 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-11-03 · filesystem $0.20/GiB-month [q]
Spend      calibration  All-in calibration including acquisition, build, idle and export  1x NVIDIA H100 PCIe 80GB $3.29/h  3 h [=]  $9.87
           numerical_gate  Numerical certification and fixtures  1x NVIDIA H100 PCIe 80GB $3.29/h  2 h [=]  $6.58
           comparison  Agreement, quality and complete-workflow timings  1x NVIDIA H100 PCIe 80GB $3.29/h  6 h [=]  $19.74
           export  Diagnostic/export/receipt/termination reserve  1x NVIDIA H100 PCIe 80GB $3.29/h  1 h [=]  $3.29
           export  No persistent filesystem; local instance disk and export to existing workspace  [=]  $0
           Planned $39.48 · unallocated $60.52 · cap $100
Rests on   gate Time-box calibration projection; reprice before launch ≤ 20 in calibration (now 9.87, passes; uncut plan at it $39.48), else Do not launch; repair route or reduce scope and reseal.
Scenarios  none
Buys       Frozen apo cases: 4 [d]
           Calibration target, excluding synthetic checks: 48 [=]
           Final docking target, excluding synthetic checks: 120 [=]
           Final pose evaluation target, including warmup: 6,000 [=]
Flags      none
Full scale none
Outside    DESIGN reserved human engineering, provenance recovery, numerical review and reporting; not measured labor: 24 person-hours · DESIGN paid external services or compute; none planned: 0 USD · DESIGN offered Lambda credit outside this card's spending authority: 900 USD
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
width_ratio = dense_rot / standard_rot = 54000 / 3600 = 15 ratio
cal_jobs = cases * arms_n * (cal_warm + cal_reps) = 4 * 3 * (1 + 3) = 48 jobs
final_jobs = cases * arms_n * (timing_warm + timing_reps + science_reps) = 4 * 3 * (1 + 7 + 2) = 120 jobs
final_pose_evals = final_jobs * retained = 120 * 50 = 6000 poses
projected_cal_usd = cal_hours * gpu_count * h100_price = 3 * 1 * 3.29 = 9.87 USD
planned_hours = cal_hours + anchor_hours + main_hours + export_hours = 3 + 2 + 6 + 1 = 12 hours
planned_usd = planned_hours * gpu_count * h100_price = 12 * 1 * 3.29 = 39.48 USD
unspent_card_usd = budget_usd - planned_usd = 100 - 39.48 = 60.52 USD
cal_box.hours = cal_hours = 3 = 3 h
anchor_box.hours = anchor_hours = 2 = 2 h
main_box.hours = main_hours = 6 = 6 h
export_box.hours = export_hours = 1 = 1 h
storage.usd = persistent_storage * fs_usd_gib_month = 0 * 0.2 = 0 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:closest_prior` PARTIAL · page: "6°刻みの場合54000通りの角度，15°刻みの場合3600通りの角度で計算します．" · note: Guide confirms angular counts and contains no fixed-50 DockQ comparison. Prior article returned browser challenge, preventing verification of million-job runtime and absence of quality comparisons there.
- sample 1 · `card:limits` PARTIAL · page: "" · note: Previously examined cases and exploratory exposure are factual history claims without sources. Remaining statements define study scope and interpretation limits.
- sample 1 · `src:prior` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Article and redirect returned browser challenge. Recorded quote, runtime, rotation distribution and absence of maximum rotation count could not be checked.

**Critic.**
- stakes 5 · `card:if_not` "At 54000 rotations, best50 DockQ stays within 0.01 or noise, worsens, or fails matched budgets; rank1 may worsen." · Benefit supports buying denser search for these cases; negligible gains, degradation or budget failure support retaining standard search.
- lever 5 · `plan:predictions.noise_rule` "Seal independently justified FFT/arithmetic score bounds before fresh cross-backend comparison. Require exact ranked transform identities and generated pose bytes; score differences within certified absolute-plus-relative bounds; DockQ erro…" · 15× rotation span buys additional search; inputs, scoring and outputs stay fixed. Benefit must exceed 0.01 and sealed paired error.
- verifiable 3 · `plan:scored_against` "Pinned native complexes evaluated with pinned DockQ [dockq]; report rank1 and maximum among 50 per case. CPU standard anchors GPU standard. Receipts reconciled with allocation ledger anchor cost." · Pinned native complexes provide independent reference truth; fixtures check evaluation, but no published numerical result is explicitly reproduced within stated tolerance.
- open 5 · `card:closest_prior` "MEGADOCK measured runtime through 1000000 docking jobs [prior]; guide documents 54000 rotations [angles], without fixed-50 DockQ width comparisons." · Published bundled-job runtime addresses different quantity; documented angular counts do not answer fixed-50 pose recovery under matched workflow budgets.
- reshape 1 · `card:sequential_part` "No 54000-step chain: independent angles retain local voxelization, FFT and solution dependencies [prior]." · Angles already independent; existing MEGADOCK parallelism supplies implementation. Plan removes no sequential dependency.
- baseline NA · `card:method` "none" · Restructuring method is none.

**Option critic.**
- stakes 5: Either result changes whether to spend fixed budgets on denser angular search.
- open 5: Names rotation count, documented 54,000 limit, and absent quality curve; unexplored widths plausibly fit stated compute reach.
- reshape 1: Sequential chain explicitly none; rotations are independent tasks with existing parallel implementation.
- distance SAME: Asks whether wider MEGADOCK rotational search improves rank1 and best50 recovery within matched workflow budgets.

**Producer says (not judged).** expected unsure (Previously exposed exploratory results motivate best50 gains with mixed rank1, but justified agreement margins and complete-workflow affordability remain unresolved; private provenance [context].); compute_tested yes (Rotational width changes; retained predictions and scoring remain fixed. Existing GPU execution supplies parallelism. Two endpoints test additional-search recovery, not a saturation plateau.); decides no; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
- test_summary: a sentence of 31 words
- dramaturg findings failed G-find after a resample; decided as returned

**Root question (R1).** Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget? Small pilot on exactly four unbound PINDER 2024-02 cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Compare existing MEGADOCK CPU standard 3600 rotations, GPU standard 3600, and GPU documented dense 54000 (-D). Keep scoring and retained predictions fixed at 50. Pin prepared input bytes, references, binary/dependency/settings/thread/allocation identities. First establish execution correctness and scientific CPU/GPU agreement at identical settings using justified numerical tolerances sealed before fresh comparison. Then assess dense-search DockQ for rank1 and best50 separately, per case; native references only for evaluation. Calibrate runtime before choosing feasible common budgets; seal configurations, timing repetitions, comparison/noise rules and total spending cap before quality evaluation. Report complete workflow time, GPU activity and billed allocation cost, separating setup/retrieval from steady-state work. Keep acceleration, agreement and additional-search quality conclusions separate. Preserve negatives, unavailable budget arms and overruns. No biological efficacy or beyond-four-case inference. Run2 already exposed quality, so fresh executions are prospective replication under new rules, never unseen holdout or retrospective preregistration. Do not substitute throughput of bundled runs for this question. Repository /home/hal/dev/interp/metis: seed experiments/blind-02/m5/BRIEF.md; case preparation/source/reference pins experiments/blind-02/m5/b01_materials/BRIEF_run1.md:48-158; full prior trace experiments/blind-02/m5/run2_trace/REPORT.md; new assessment experiments/blind-02/science/s01/ASSESSMENT.md. Run2 measured docking totals CPU/GPU/dense 40.07/6.85/69.38 seconds, not complete workflows; standard CPU/GPU transforms and DockQ matched, score max deltas 0.04/0.03/0.04/0.14 with no acceptance tolerance. Dense best50 improved all four observations, rank1 worsened in two including 1nr5. These are exploratory, not sealed conclusions. Historical H100 PCIe rate USD3.29/hour, setup145s, whole unscored bundle median131.9565s; old receipts setup/anchors/freeze/upload/profile/concurrency 145/1571/1402/1424/2832/3448s. Historical allocation and transport observations are estimates for a fresh box, not new producer measurements or public citations. Tree plans only, no box execution. Full card plan ceiling USD100; each later calibration must project below USD20 including setup, retrieval and idle, preferably USD5-10, soft6h/hard12h. Do not run full experiments on calibration route. Identify specific file/section gaps if existing routes cannot implement comparison. Tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases. Measure compilation carries uncertain scalar inputs and phases, not arms/decision_rule; checks 2.5x PROXY or 3x other estimate bands, never scientific equivalence. Measure execution requires missing stage args/controller to be established. Card factual web sources may be checked; do not fabricate citations for private records.

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-02/20261103-1649-tree/out/work/seed-20261103/R1/physical/1fffee1a/producer.md)

---

<a id="card-seed-idea-1"></a>**1 · Agreement before interpreting acceleration or denser search.** seed pick · compute tested: no · plan expects: unsure · REJECT

**Question.** Do CPU and GPU standard docking agree across all 50 retained poses on four fixed cases after independent repeatability and error calibration?

**What is known.** Published MEGADOCK measured scaling across 30,976 docking jobs using up to 420 nodes; it did not establish this four-case numerical tolerance [prior]. Whether independent repeats and precision analysis justify CPU/GPU agreement for every retained pose on these four fixed inputs.

**Hypothesis.** Independent repeats and numerical error analysis can establish defensible CPU/GPU agreement before acceleration or denser search receives scientific interpretation.

**If the hypothesis holds.** Four repeats determine whether CPU and GPU agree for all four cases where two repeats leave results unclear.

**If not.** Four repeats leave at least one case unresolved, or both repeat levels already give identical agreement status.

**Test.** Build CPU-only repeat and control software first; use 2 then 4 repeats to set independent numerical error limits; freeze limits; compare fresh standard CPU/GPU outputs for four cases and all 50 rows. Budget $40; exclude dense search and quality scoring.

*Compute axis.* Independent same-backend calibration executions per case and backend; cumulative levels, not search density: 2–4 repeats per case per backend, 2 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** None: No published numerical tolerance or independently reproduced code anchor exists in this plan. Build independent transform and synthetic-correlation checks plus precision/error analysis during calibration. Until these pass and numeric tolerances are sealed, scientific CPU/GPU agreement stays unavailable. Published scaling evidence [prior] is not an accuracy anchor.

**Would not show.** Four-case execution validation only; no biological efficacy, generalization, dense-search improvement, throughput claim, unseen holdout or tolerance inferred from historical agreement.

*Cost.* Plans $40 of the $100 budget over 9 machine-hours, leaving $60. Pilot gate: Maximum allowed stable-file byte mismatches; observed count recorded in screen ≤ 0, else Stop dependent calibration; diagnose subsetting versus baseline drift without changing criterion..

**Judges.** Dramaturg: REJECT (2 blocking). Decides at: $26 at compare · plan $40 · 0 GUESS (critic: Fresh paired outputs evaluated against both frozen calibration levels establish whether four repeats resolve agreement where two do not).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $100 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-11-03 · filesystem $0.20/GiB-month [q]
Spend      screen  CPU-only diagnostic; includes retrieval, compilation, optional full/control, idle and initial export  1x NVIDIA H100 PCIe 80GB $3.29/h  1 h [=]  $3.29
           calibrate  Same-backend repeats and independent numerical checks; includes any relaunch overhead  1x NVIDIA H100 PCIe 80GB $3.29/h  2 h [=]  $6.58
           compare  Fresh standard CPU/GPU agreement pairs after all gates  1x NVIDIA H100 PCIe 80GB $3.29/h  5 h [=]  $16.45
           export  Final transfer, receipt collection, reconciliation, idle and termination  1x NVIDIA H100 PCIe 80GB $3.29/h  1 h [=]  $3.29
           export  Use instance-local disk and export before termination; no persistent filesystem  [=]  $0
           export  Tax, minute rounding and incidental charges only; never extra experiments  [=]  $10.39
           Planned $40 · unallocated $60 · cap $40
Rests on   gate Maximum allowed stable-file byte mismatches; observed count recorded in screen ≤ 0 in screen (now 0, passes; uncut plan at it $40), else Stop dependent calibration; diagnose subsetting versus baseline drift without changing criterion.
           gate Required conjunction of completed repeats, independent checks, justified numeric tolerances and affordable forecast; observed value recorded before compare ≥ 1 in calibrate (now 1, passes; uncut plan at it $40), else No fresh comparison: report absent anchor, missing numeric tolerances or incomplete calibration.
Scenarios  none
Buys       CPU units in initial screen: 4 [d]
           Cumulative calibration executions: 32 [=]
           Fresh comparison executions: 8 [=]
           Rankwise cross-backend row pairs: 200 [=]
           Fresh generated complex PDBs: 400 [=]
Flags      none
Full scale none
Outside    Human engineering/review allotment; DESIGN, not measured effort: 16 person hours · External money authorized: none; use existing local storage/network. Any paid non-Lambda service requires revised budget.: 0 USD
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
calibration_jobs = cases * backends * repeat_high = 4 * 2 * 4 = 32 jobs
fresh_jobs = cases * backends * fresh_repeats = 4 * 2 * 1 = 8 jobs
fresh_rows = cases * retained = 4 * 50 = 200 row pairs
fresh_pdbs = fresh_jobs * retained = 8 * 50 = 400 PDBs
jobs_max = screen_units + control_jobs_max + calibration_jobs + fresh_jobs = 4 + 4 + 32 + 8 = 48 jobs
calibration_h = screen_h + calibrate_h = 1 + 2 = 3 instance hours
hard_h = screen_h + calibrate_h + compare_h + export_h = 1 + 2 + 5 + 1 = 9 instance hours
allocation_usd = hard_h * gpu_count * h100_price = 9 * 1 * 3.29 = 29.61 USD
calibration_usd = calibration_h * gpu_count * h100_price = 3 * 1 * 3.29 = 9.87 USD
cash_reserve = card_cap_usd - allocation_usd = 40 - 29.61 = 10.39 USD
uncommitted_credit = budget_usd - card_cap_usd = 100 - 40 = 60 USD
screen_box.hours = screen_h = 1 = 1 h
calibration_box.hours = calibrate_h = 2 = 2 h
comparison_box.hours = compare_h = 5 = 5 h
export_box.hours = export_h = 1 = 1 h
persistent_storage.usd = persistent_gib * fs_usd_gib_month = 0 * 0.2 = 0 usd
cash_contingency.usd = cash_reserve = 10.39 = 10.39 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:closest_prior` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Browser verification blocked article text. Recorded quote, job count, node count and absence of four-case tolerance could not be checked.
- sample 1 · `src:prior` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Browser verification blocked article text. Recorded quote, 30,976 jobs, five timing measurements and claimed methodological limits could not be checked.

**Critic.**
- stakes 5 · `card:if_lever` "Four repeats determine whether CPU and GPU agree for all four cases where two repeats leave results unclear." · Resolution at four repeats supports buying extra calibration compute; unchanged or unresolved status supports stopping that escalation. Test measures agreement readiness directly.
- lever 1 · `plan:compute_axis` "{"quantity":"Independent same-backend calibration executions per case and backend; cumulative levels, not search density","unit":"repeats per case per backend","levels":[2,4]}" · Repeat count spans only 2×. Plan also lacks evidence that resolution differences exceed calibration variability; two conditions fail or remain unknown.
- verifiable 3 · `plan:scored_against` "CPU standard provides paired reference, not truth. Independent transform reconstruction, synthetic correlation checks and higher-precision error analysis validate mechanics; fresh CPU/GPU outputs face frozen casewise tolerances. Later nativ…" · Independent transform reconstruction and synthetic checks provide planted mechanical truth, but no published-number reproduction precedes comparison.
- open 5 · `card:closest_prior` "Published MEGADOCK measured scaling across 30,976 docking jobs using up to 420 nodes; it did not establish this four-case numerical tolerance [prior]." · Published scaling study addresses throughput across many jobs, leaving four-case numerical tolerance and repeat-count sufficiency unanswered.
- reshape 1 · `card:sequential_part` "Four gates: CPU repeat screen, independent calibration, frozen tolerances, fresh CPU/GPU comparison." · Screen, calibration, tolerance freeze and fresh comparison remain sequential. Plan removes no dependency.
- baseline NA · `card:method` "none" · Restructuring method is none.

**Producer says (not judged).** expected unsure (Repeats can expose instability, but this plan has no independent error anchor yet and cannot predict whether additional repeats resolve it.); compute_tested no (Necessary validation card. More executions buy evidence about agreement; this plan tests neither search-density gains nor parallel scheduling or throughput.); decides no; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
- question: a sentence of 22 words
- test_summary: a sentence of 28 words
- novelty.closest_prior: a sentence of 22 words
- test_summary: rewritten by the field repair
- predictions.if_lever: rewritten by the field repair
- card field test_summary still fails: dollar figure
- card field predictions.if_lever still fails: neither if_lever nor if_not contains a number
- dramaturg findings failed G-find after a resample; decided as returned

**Root question (null).** Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget? Small pilot on exactly four unbound PINDER 2024-02 cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Compare existing MEGADOCK CPU standard 3600 rotations, GPU standard 3600, and GPU documented dense 54000 (-D). Keep scoring and retained predictions fixed at 50. Pin prepared input bytes, references, binary/dependency/settings/thread/allocation identities. First establish execution correctness and scientific CPU/GPU agreement at identical settings using justified numerical tolerances sealed before fresh comparison. Then assess dense-search DockQ for rank1 and best50 separately, per case; native references only for evaluation. Calibrate runtime before choosing feasible common budgets; seal configurations, timing repetitions, comparison/noise rules and total spending cap before quality evaluation. Report complete workflow time, GPU activity and billed allocation cost, separating setup/retrieval from steady-state work. Keep acceleration, agreement and additional-search quality conclusions separate. Preserve negatives, unavailable budget arms and overruns. No biological efficacy or beyond-four-case inference. Run2 already exposed quality, so fresh executions are prospective replication under new rules, never unseen holdout or retrospective preregistration. Do not substitute throughput of bundled runs for this question. Repository /home/hal/dev/interp/metis: seed experiments/blind-02/m5/BRIEF.md; case preparation/source/reference pins experiments/blind-02/m5/b01_materials/BRIEF_run1.md:48-158; full prior trace experiments/blind-02/m5/run2_trace/REPORT.md; new assessment experiments/blind-02/science/s01/ASSESSMENT.md. Run2 measured docking totals CPU/GPU/dense 40.07/6.85/69.38 seconds, not complete workflows; standard CPU/GPU transforms and DockQ matched, score max deltas 0.04/0.03/0.04/0.14 with no acceptance tolerance. Dense best50 improved all four observations, rank1 worsened in two including 1nr5. These are exploratory, not sealed conclusions. Historical H100 PCIe rate USD3.29/hour, setup145s, whole unscored bundle median131.9565s; old receipts setup/anchors/freeze/upload/profile/concurrency 145/1571/1402/1424/2832/3448s. Historical allocation and transport observations are estimates for a fresh box, not new producer measurements or public citations. Tree plans only, no box execution. Full card plan ceiling USD100; each later calibration must project below USD20 including setup, retrieval and idle, preferably USD5-10, soft6h/hard12h. Do not run full experiments on calibration route. Identify specific file/section gaps if existing routes cannot implement comparison. Tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases. Measure compilation carries uncertain scalar inputs and phases, not arms/decision_rule; checks 2.5x PROXY or 3x other estimate bands, never scientific equivalence. Measure execution requires missing stage args/controller to be established. Card factual web sources may be checked; do not fabricate citations for private records.

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-02/20261103-1649-tree/out/work/seed-20261103/seed/idea/340ca71c/producer.md)

---

<a id="card-seed-idea-2"></a>**2 · Complete-workflow acceleration and dense-search affordability.** seed pick · compute tested: yes · plan expects: unsure · PASS

**Question.** Can GPU docking make 54000 rotations affordable within CPU workflow budgets and improve pose recovery across four unbound cases?

**What is known.** Published MEGADOCK benchmark reports 352 dockings in 8.20 CPU hours versus 2.26 with one GPU; rotation maximum unspecified [prior]. Prior timings do not establish complete scored workflow affordability or dense best50 versus rank1 recovery on these four unbound cases.

**Hypothesis.** GPU acceleration pays for denser rotation sampling, improving best50 pose recovery within fixed complete workflow budgets.

**If compute is the lever.** 54000 rotations finish within CPU budgets; best50 DockQ rises by 0.02 on at least three cases, with standard acceleration above 1.05.

**If not.** 54000 rotations exceed every common cap, or fewer than three cases gain 0.02 best50 DockQ; rank1 may worsen.

**Test.** Time CPU standard, GPU standard and GPU dense complete scored workflows on one host. Seal caps after timing-only calibration; require pose agreement first. Compare rank1 and best50 DockQ separately, preserving missed deadlines and regressions.

*Compute axis.* Rotational sampling angles per docking configuration: 3,600–54,000 rotations, 2 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** Reproduce public DockQ example, then require CPU/GPU pose agreement and independent DockQ agreement on all retained standard poses [dockq]. Tolerance: Example absolute error <= example_tol; CPU/GPU retained transform multiset identical, with ordering swaps allowed only inside score_tol_abs + score_tol_rel*max(abs(scores)) ties. Matched-coordinate max error <= coord_tol_angstrom; matched DockQ error <= dockq_tol. Relative score tolerance is conservative engineering choice for floating arithmetic, not established equivalence; geometry and independent metrics are mandatory. Seal before fresh comparison; failure stops quality interpretation without widening tolerances..

**Would not show.** Four cases only; no biological efficacy, population inference, unseen holdout, CPU-only rental comparison or guaranteed completion. Historical quality exposure remains disclosed.

*Cost.* Plans $49.48 of the $100 budget over 12 machine-hours, leaving $50.52. Pilot gate: calibration_total_usd ≤ 10, else Do not launch; reduce setup scope off-cloud or abandon route. Never bypass with full pipeline.. 2 cost flags in the block.

**Judges.** Dramaturg: PASS 2/2. Decides at: $49 at report · plan $49 · 2 GUESS (critic: Report completes independent score checks and paired timing aggregation needed for decision rule; earlier phases can terminate without resolving all outcomes).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $100 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-11-03 · filesystem $0.20/GiB-month [q]
Spend      calibration  Hard time box includes setup, cold/warm retrieval, timing-only runs, profiling, idle, export and shutdown; completion not guaranteed.  1x NVIDIA H100 PCIe 80GB $3.29/h  2.5 h [=]  $8.22
           calibration  Tax, rounding and shutdown allowance; actual charges monitored.  [=]  $1.50
           main  Hard time box for fresh setup if needed, anchor, standard agreement, timed repeats and dense native evaluation after gates.  1x NVIDIA H100 PCIe 80GB $3.29/h  6 h [=]  $19.74
           report  Hard time box for cross-checks, analysis, allocation overhead, archive/export and termination; may finish earlier.  1x NVIDIA H100 PCIe 80GB $3.29/h  3.5 h [=]  $11.52
           report  Remaining tax, billing rounding and shutdown allowance; no additional science work.  [=]  $8.50
           report  No paid persistent filesystem. Example rate explicitly not a current storage quote [billing].  [=]  $0
           Planned $49.48 · unallocated $50.52 · cap $100
Rests on   standard_rotations 3,600 rotations [g] rests on: citation not confirmed: UNREACHABLE · no phase measures it · budget not reached within 1000×
           dense_rotations 54,000 rotations [g] rests on: citation not confirmed: UNREACHABLE · no phase measures it · budget not reached within 1000×
           gate calibration_total_usd ≤ 10 in calibration (now 9.72, passes; uncut plan at it $49.48), else Do not launch; reduce setup scope off-cloud or abandon route. Never bypass with full pipeline.
Scenarios  none
Buys       cases: 4 [d]
           arms_count: 3 [d]
           standard_rotations: 3,600 [g]
           dense_rotations: 54,000 [g]
           retained: 50 [d]
           cal_workflows: 24 [=]
           timed_workflows: 84 [=]
           main_pose_evals: 4,800 [=]
Flags      standard_rotations [g] is load-bearing and no phase measures it
           dense_rotations [g] is load-bearing and no phase measures it
Full scale none
Outside    DESIGN off-cloud engineering and scientific review; no wage assumed.: 12 person hours · DESIGN paid services outside Lambda; none planned; external source retrieval and output archive use existing resources.: 0 USD
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
cal_workflows = cases * arms_count * cache_passes = 4 * 3 * 2 = 24 unscored workflows, conditional on time box
timed_workflows = cases * arms_count * repeats = 4 * 3 * 7 = 84 scored workflows, conditional on gates
main_workflows = cases * arms_count * (warmups + repeats) = 4 * 3 * (1 + 7) = 96 scored workflows including warmups
main_pose_evals = main_workflows * retained = 96 * 50 = 4800 pose evaluations, excluding independent cross-checks
unique_poses = cases * arms_count * retained = 4 * 3 * 50 = 600 poses per completed repetition
calibration_total_usd = calibration_h * gpu_rate * gpu_count + cal_tax_reserve_usd = 2.5 * 3.29 * 1 + 1.5 = 9.725 USD
allocated_h = calibration_h + main_h + report_h = 2.5 + 6 + 3.5 = 12 instance wall hours
compute_usd = allocated_h * gpu_rate * gpu_count = 12 * 3.29 * 1 = 39.48 USD
planned_usd = compute_usd + cal_tax_reserve_usd + other_reserve_usd = 39.48 + 1.5 + 8.5 = 49.48 USD
unused_credit_usd = credit_limit_usd - planned_usd = 1000 - 49.48 = 950.52 USD
cal_box.hours = calibration_h = 2.5 = 2.5 h
cal_extra.usd = cal_tax_reserve_usd = 1.5 = 1.5 usd
main_box.hours = main_h = 6 = 6 h
report_box.hours = report_h = 3.5 = 3.5 h
other_extra.usd = other_reserve_usd = 8.5 = 8.5 usd
filesystem.usd = fs_gib * fs_usd_gib_month = 0 * 0.2 = 0 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:left_open` UNSUPPORTED · page: "" · note: Claim about what prior timings establish has no cited source in this card.
- sample 1 · `card:limits` PARTIAL · page: "" · note: Scope limits need no source. Historical quality exposure being disclosed is an unsourced factual claim.
- sample 1 · `num:standard_rotations` UNREACHABLE · page: "" · note: Pinned raw URL and corresponding GitHub file page failed to fetch with cache-miss errors. Direct request also failed DNS resolution; quote and value could not be verified.
- sample 1 · `num:dense_rotations` UNREACHABLE · page: "" · note: Pinned raw URL and corresponding GitHub file page failed to fetch with cache-miss errors. Direct request also failed DNS resolution; quote and value could not be verified.
- sample 2 · `card:left_open` UNSUPPORTED · page: "" · note: Factual characterization of prior evidence has no cited source in this card.
- sample 2 · `card:limits` PARTIAL · page: "" · note: Scope limits need no source. Historical quality exposure is asserted without supporting source.
- sample 2 · `num:standard_rotations` UNREACHABLE · page: "" · note: Pinned raw URL failed twice with cache-miss errors; equivalent GitHub file URL also failed. Quote and value could not be checked.
- sample 2 · `num:dense_rotations` UNREACHABLE · page: "" · note: Pinned raw URL failed twice with cache-miss errors; equivalent GitHub file URL also failed. Quote and value could not be checked.

**Critic.**
- stakes 5 · `card:test_summary` "Time CPU standard, GPU standard and GPU dense complete scored workflows on one host. Seal caps after timing-only calibration; require pose agreement first. Compare rank1 and best50 DockQ separately, preserving missed deadlines and regressio…" · Both outcomes guide whether to fund dense search within fixed workflow budgets; test measures cost, completion and recovery directly.
- lever 5 · `plan:predictions.noise_rule` "Before fresh outputs, seal bootstrap seed, order seed, warmups, repetitions, endpoint and confidence rule. Randomize arm order within each case/repetition block. Bootstrap repetition blocks, preserving all cases; each resample computes medi…" · Sampling spans 15×; extra rotations consume compute. Inputs and scoring stay fixed; repeated paired gains and timing confidence rules constrain noise.
- verifiable 5 · `card:anchor` "Reproduce public DockQ example, then require CPU/GPU pose agreement and independent DockQ agreement on all retained standard poses [dockq]. Tolerance: Example absolute error <= example_tol; CPU/GPU retained transform multiset identical, wit…" · Native references provide independent pose truth; public DockQ reproduction and CPU/GPU agreement have explicit plan tolerances.
- open 5 · `card:left_open` "Prior timings do not establish complete scored workflow affordability or dense best50 versus rank1 recovery on these four unbound cases." · Published docking throughput leaves complete workflow affordability and dense rank1 versus best50 recovery unanswered.
- reshape 1 · `card:method` "none" · No restructuring proposed. Docking, pose generation and scoring remain sequential; existing GPU implementation already appears in published comparison.
- baseline NA · `card:method` "none" · Restructuring method is none; criterion explicitly permits NA.

**Producer says (not judged).** expected unsure (User-supplied exploratory history suggests faster standard docking and better dense best50, but complete workflow affordability and rank1 recovery remain unresolved.); compute_tested yes (Vary search from standard to documented dense rotations while keeping scoring and retained poses fixed [cmd]; measure whether existing GPU implementation buys search within sealed wall and dollar caps.); decides no; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
- predictions.if_lever: a sentence of 21 words
- dramaturg findings failed G-find after a resample; decided as returned
- dramaturg-2 findings failed G-find after a resample; decided as returned
- prose over 240 words (262)

**Root question (null).** Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget? Small pilot on exactly four unbound PINDER 2024-02 cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Compare existing MEGADOCK CPU standard 3600 rotations, GPU standard 3600, and GPU documented dense 54000 (-D). Keep scoring and retained predictions fixed at 50. Pin prepared input bytes, references, binary/dependency/settings/thread/allocation identities. First establish execution correctness and scientific CPU/GPU agreement at identical settings using justified numerical tolerances sealed before fresh comparison. Then assess dense-search DockQ for rank1 and best50 separately, per case; native references only for evaluation. Calibrate runtime before choosing feasible common budgets; seal configurations, timing repetitions, comparison/noise rules and total spending cap before quality evaluation. Report complete workflow time, GPU activity and billed allocation cost, separating setup/retrieval from steady-state work. Keep acceleration, agreement and additional-search quality conclusions separate. Preserve negatives, unavailable budget arms and overruns. No biological efficacy or beyond-four-case inference. Run2 already exposed quality, so fresh executions are prospective replication under new rules, never unseen holdout or retrospective preregistration. Do not substitute throughput of bundled runs for this question. Repository /home/hal/dev/interp/metis: seed experiments/blind-02/m5/BRIEF.md; case preparation/source/reference pins experiments/blind-02/m5/b01_materials/BRIEF_run1.md:48-158; full prior trace experiments/blind-02/m5/run2_trace/REPORT.md; new assessment experiments/blind-02/science/s01/ASSESSMENT.md. Run2 measured docking totals CPU/GPU/dense 40.07/6.85/69.38 seconds, not complete workflows; standard CPU/GPU transforms and DockQ matched, score max deltas 0.04/0.03/0.04/0.14 with no acceptance tolerance. Dense best50 improved all four observations, rank1 worsened in two including 1nr5. These are exploratory, not sealed conclusions. Historical H100 PCIe rate USD3.29/hour, setup145s, whole unscored bundle median131.9565s; old receipts setup/anchors/freeze/upload/profile/concurrency 145/1571/1402/1424/2832/3448s. Historical allocation and transport observations are estimates for a fresh box, not new producer measurements or public citations. Tree plans only, no box execution. Full card plan ceiling USD100; each later calibration must project below USD20 including setup, retrieval and idle, preferably USD5-10, soft6h/hard12h. Do not run full experiments on calibration route. Identify specific file/section gaps if existing routes cannot implement comparison. Tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases. Measure compilation carries uncertain scalar inputs and phases, not arms/decision_rule; checks 2.5x PROXY or 3x other estimate bands, never scientific equivalence. Measure execution requires missing stage args/controller to be established. Card factual web sources may be checked; do not fabricate citations for private records.

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-02/20261103-1649-tree/out/work/seed-20261103/seed/idea/370cabd5/producer.md)

---

<a id="card-seed-idea-3"></a>**3 · Dense search changes candidate recovery and ranking differently.** seed pick · compute tested: yes · plan expects: unsure · REJECT

**Question.** Can 54000 versus 3600 rotations improve best50 DockQ while harming rank1, within identical affordable workflow caps on 4 unbound cases?

**What is known.** MEGADOCK 4.0 timed 1000000 docking jobs; rotation count was unspecified, without this fixed50 recovery-versus-ranking comparison. [prior] Whether 54000 rotations improve best50 while harming rank1 on these 4 apo cases, within calibrated common workflow budgets.

**Hypothesis.** Denser search recovers better candidates, but fixed scoring can rank them poorly, separating best50 gains from rank1 losses.

**If compute is the lever.** At 54000 rotations, best50 gains exceed 0.01 DockQ plus noise, while rank1 can decline, within common caps.

**If not.** At 54000 rotations, best50 gains fail 0.01 DockQ plus noise, or complete searches exceed common caps; rank1 changes remain separate.

**Test.** Build gated docking/evaluation controller; validate independent scorer and CPU/GPU standard agreement; calibrate complete-workflow caps; seal rules; run 2 paired 3600/54000-rotation bundles on 4 cases, retaining 50. Report rank1, best50, time, GPU activity and billed cost separately.

*Compute axis.* Rotational samples per complete docking search; outputs remain fixed: 3,600–54,000 rotations, 2 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** Reproduce public DockQ example, then cross-check independent DockQ against primary evaluation before scoring study poses. [dockq] Tolerance: DESIGN: reproduce documented rounded total within 0.0005 DockQ; then require matched-mapping primary/independent scores and repeat variation within fixture-derived tau_q <= 0.0001..

**Would not show.** Only 4 exposed cases; prospective replication, no biological efficacy or population inference. No reranking, CPU dense comparison, extra retained poses, or new parallel algorithm.

*Cost.* Plans $29.74 of the $100 budget over 6 machine-hours, leaving $70.26. Main guess: Prospective all-inclusive remaining science allocation need [g], measured after $6.58 of spend; the budget is reached if it is 6.3× higher.

**Judges.** Dramaturg: REJECT (2 blocking). Decides at: $30 at science · plan $30 · 2 GUESS (critic: Earlier gates establish agreement and affordability; successful paths require science to measure paired rank1 and best50 differences under sealed caps and noise rules).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $100 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-11-03
Spend      anchors  Shared setup, retrieval, anchor, agreement, native-blind cost screen and teardown; one charge across calibration phases. Ceiling 6.58 USD, below 20 USD.  1x NVIDIA H100 PCIe 80GB $3.29/h  2 h [=]  $6.58
           science  Fresh complete standard/dense paired workflows, scorer repeats, setup, export and idle; ceiling 13.16 USD.  1x NVIDIA H100 PCIe 80GB $3.29/h  4 h [=]  $13.16  time box; need 4 h (margin 1.00×)
           recovery  Optional operational recovery; ceiling 19.74 USD, only actual instance occupancy billed.  1x NVIDIA H100 PCIe 80GB $3.29/h  6 h [=]  $19.74  optional
           science  Design reserve for taxes or billing adjustment; verify actual quote before allocation.  [=]  $10
           Planned $29.74 · unallocated $70.26 · with options $49.48 · cap $100
Rests on   Prospective all-inclusive remaining science allocation need 4 wall-clock hours [g] rests on: Conservative admission placeholder including fresh setup, paired output generation, scoring, export and idle; no fresh timing exists. · measured in calibrate ($6.58 spent by then) · gate Prospective all-inclusive remaining science allocation need ≤ 4 in seal (now 4, passes; uncut plan at it $29.74), else Do not launch science; publish infeasibility and required executable/cost changes without altering sealed comparison. · budget reached at 25.4 (6.3× higher) · box overflows at 1.0×
           Prospective maximum standard/dense complete workflow bound 300 seconds/case [g] rests on: Conservative screening placeholder, not an observed runtime; private historical docking-only durations omit transport, pose generation and scoring. · measured in calibrate ($6.58 spent by then) · gate Prospective maximum standard/dense complete workflow bound ≤ 300 in calibrate (now 300, passes; uncut plan at it $29.74), else No scientific launch; retain unavailable caps and measured bottleneck. Any later calibration needs separate below-20-dollar projection including setup, retrieval and idle. · budget not reached within 1000×
Scenarios  none
Buys       Exact requested apo cases: 4 [d]
           Fresh GPU scientific searches: 16 [=]
           Fresh scientific pose evaluations: 800 [=]
           Paired scientific bundles: 2 [d]
Flags      none
Full scale none
Outside    Design allowance for human implementation, fixture validation, protocol sealing and review; not a measured labor estimate.: 16 person-hours · Non-Lambda cash planned; public pages and existing prepared inputs assumed accessible, otherwise block contract.: 0 USD
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
rotation_ratio = dense_rot/standard_rot = 54000 / 3600 = 15 ratio
scientific_searches = cases*quality_arms*science_reps = 4 * 2 * 2 = 16 searches
scientific_scores = scientific_searches*retained = 16 * 50 = 800 poses
soft_h = cal_h+science_h = 2 + 4 = 6 wall-clock hours
hard_h = soft_h+recovery_h = 6 + 6 = 12 wall-clock hours
calibration_usd = cal_h*h100_usd_h*gpu_count = 2 * 3.29 * 1 = 6.58 USD
base_usd = (cal_h+science_h)*h100_usd_h*gpu_count = (2 + 4) * 3.29 * 1 = 19.74 USD
planned_usd = hard_h*h100_usd_h*gpu_count+extra_usd = 12 * 3.29 * 1 + 10 = 49.48 USD
calibration.hours = cal_h = 2 = 2 h
paired_science.hours = science_h = 4 = 4 h
paired_science.need = science_need_h = 4 = 4 h
operational_reserve.hours = recovery_h = 6 = 6 h
billing_reserve.usd = extra_usd = 10 = 10 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:closest_prior` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Browser challenge blocked article. Recorded quote, job count, unspecified rotation count and absence of comparison could not be checked.
- sample 1 · `src:prior` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Browser challenge blocked article. Recorded throughput quote and supporting workload claims could not be checked.
- sample 2 · `card:closest_prior` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Source returned browser verification screen. Timing claim, unspecified rotation count and absence of fixed50 comparison could not be checked.
- sample 2 · `src:prior` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Source returned browser verification screen; alternate access attempts failed. Recorded quote and supporting claims could not be verified.

**Critic.**
- stakes 5 · `card:if_not` "At 54000 rotations, best50 gains fail 0.01 DockQ plus noise, or complete searches exceed common caps; rank1 changes remain separate." · Outcomes change whether to fund dense search on these cases; measured recovery and complete-workflow caps directly determine that choice.
- lever 5 · `plan:predictions` "{"if_lever":"At 54000 rotations, best50 gains exceed 0.01 DockQ plus noise, while rank1 can decline, within common caps.","if_not":"At 54000 rotations, best50 gains fail 0.01 DockQ plus noise, or complete searches exceed common caps; rank1 …" · 15× rotations buys compute alone; inputs, scoring and outputs fixed. Meaningful differences exceed sealed noise bounds; unstable repetitions block inference.
- verifiable 5 · `card:anchor` "Reproduce public DockQ example, then cross-check independent DockQ against primary evaluation before scoring study poses. [dockq] Tolerance: DESIGN: reproduce documented rounded total within 0.0005 DockQ; then require matched-mapping primar…" · Byte-pinned native structures provide independent reference truth. Published DockQ example reproduced within stated tolerance before independent scorer agreement checks.
- open 5 · `card:closest_prior` "MEGADOCK 4.0 timed 1000000 docking jobs; rotation count was unspecified, without this fixed50 recovery-versus-ranking comparison. [prior]" · Published throughput study does not answer fixed-budget, fixed50 recovery versus ranking across 3600 and 54000 rotations; gap explicit.
- reshape 1 · `card:sequential_part` "Each answer requires search, pose generation, scoring, then comparison; 4 dependent stages." · Search, pose generation, scoring and comparison remain sequential. Existing GPU implementation reused; no dependency removed.
- baseline NA · `card:method` "none" · Restructuring method is none; criterion explicitly permits NA.

**Producer says (not judged).** expected unsure (User-supplied exploratory history suggests recovery/ranking divergence, but new cost admissibility, numerical agreement and sealed replication remain untested.); compute_tested yes (Search width rises from 3600 to 54000 rotations, a derived 15-fold increase [usage, commands]; GPU affordability and quality are tested separately.); decides no; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd: set by the question
- test_summary: a sentence of 26 words
- dramaturg findings failed G-find after a resample; decided as returned
- dramaturg-2 findings failed G-find after a resample; decided as returned

**Root question (null).** Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget? Small pilot on exactly four unbound PINDER 2024-02 cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Compare existing MEGADOCK CPU standard 3600 rotations, GPU standard 3600, and GPU documented dense 54000 (-D). Keep scoring and retained predictions fixed at 50. Pin prepared input bytes, references, binary/dependency/settings/thread/allocation identities. First establish execution correctness and scientific CPU/GPU agreement at identical settings using justified numerical tolerances sealed before fresh comparison. Then assess dense-search DockQ for rank1 and best50 separately, per case; native references only for evaluation. Calibrate runtime before choosing feasible common budgets; seal configurations, timing repetitions, comparison/noise rules and total spending cap before quality evaluation. Report complete workflow time, GPU activity and billed allocation cost, separating setup/retrieval from steady-state work. Keep acceleration, agreement and additional-search quality conclusions separate. Preserve negatives, unavailable budget arms and overruns. No biological efficacy or beyond-four-case inference. Run2 already exposed quality, so fresh executions are prospective replication under new rules, never unseen holdout or retrospective preregistration. Do not substitute throughput of bundled runs for this question. Repository /home/hal/dev/interp/metis: seed experiments/blind-02/m5/BRIEF.md; case preparation/source/reference pins experiments/blind-02/m5/b01_materials/BRIEF_run1.md:48-158; full prior trace experiments/blind-02/m5/run2_trace/REPORT.md; new assessment experiments/blind-02/science/s01/ASSESSMENT.md. Run2 measured docking totals CPU/GPU/dense 40.07/6.85/69.38 seconds, not complete workflows; standard CPU/GPU transforms and DockQ matched, score max deltas 0.04/0.03/0.04/0.14 with no acceptance tolerance. Dense best50 improved all four observations, rank1 worsened in two including 1nr5. These are exploratory, not sealed conclusions. Historical H100 PCIe rate USD3.29/hour, setup145s, whole unscored bundle median131.9565s; old receipts setup/anchors/freeze/upload/profile/concurrency 145/1571/1402/1424/2832/3448s. Historical allocation and transport observations are estimates for a fresh box, not new producer measurements or public citations. Tree plans only, no box execution. Full card plan ceiling USD100; each later calibration must project below USD20 including setup, retrieval and idle, preferably USD5-10, soft6h/hard12h. Do not run full experiments on calibration route. Identify specific file/section gaps if existing routes cannot implement comparison. Tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases. Measure compilation carries uncertain scalar inputs and phases, not arms/decision_rule; checks 2.5x PROXY or 3x other estimate bands, never scientific equivalence. Measure execution requires missing stage args/controller to be established. Card factual web sources may be checked; do not fabricate citations for private records.

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-02/20261103-1649-tree/out/work/seed-20261103/seed/idea/360caa42/producer.md)

---

<a id="card-seed-idea-4"></a>**4 · CPU host scheduling as workflow affordability calibration.** seed pick · compute tested: partly · plan expects: unsure · REJECT

**Question.** Can running 2 or 4 independent CPU docking jobs together cut four-case workflow cost while preserving every retained pose?

**What is known.** Published MEGADOCK docking benchmarks reached 98% scaling at 420 nodes; they measured distributed work, not four jobs competing on one host [prior]. Whether 2 or 4 fixed-thread CPU jobs sharing 26 logical CPUs preserve every output and beat serial workflow time by 1.05.

**Hypothesis.** Independent jobs may fill idle host capacity, making unchanged four-case CPU docking at least 1.05 times faster with identical outputs.

**If compute is the lever.** At width 2 or 4, both paired four-case workflow speedups reach 1.05 with exact docking and pose equality.

**If not.** Neither width achieves 1.05 in both paired four-case workflow speedups, or output equality fails.

**Test.** Build separate CPU job commands and output checker; compare original four-case serial workflow, separate serial jobs, and 2/4 concurrent jobs in mirrored order. Require identical outputs and both measured speedups at least 1.05. Reserve 2 instance-hours, USD6.58, with USD10 hard cap.

*Compute axis.* Independent fixed-input CPU docking jobs allowed concurrently on one unchanged host: 1–4 concurrent jobs, 3 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** Match frozen serial docking outputs and all 50 poses per case, then require identical outputs from each scheduling arm. Tolerance: Zero docking-output and pose-PDB byte differences; zero input or shared immutable-file changes. Exclude only presealed volatile logs. No public numerical anchor or independent implementation validates these exact private prepared inputs..

**Would not show.** No dense-search quality, GPU scheduling, biological efficacy or beyond-four-case inference; two repeats provide an operational screen, not statistical confidence.

*Cost.* Plans $6.58 of the $100 budget over 2 machine-hours, leaving $93.42.

**Judges.** Dramaturg: REJECT (2 blocking). Decides at: none · plan $7 · 0 GUESS (critic: Phases measure CPU scheduling throughput and equality; none tests GPU dense-search affordability or pose recovery within fixed budgets).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $100 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-11-03
Spend      setup_anchor  Allocation-wide setup, retrieval, build and first correctness anchor; timer bounded.  1x NVIDIA H100 PCIe 80GB $3.29/h  0.5 h [=]  $1.65
           compare  Remaining prospective scheduling comparison; timer bounded, unfinished arms unavailable.  1x NVIDIA H100 PCIe 80GB $3.29/h  1 h [=]  $3.29
           report_close  Export, idle contingency and confirmed termination; timer bounded.  1x NVIDIA H100 PCIe 80GB $3.29/h  0.5 h [=]  $1.65
           Planned $6.58 · unallocated $93.42 · cap $10
Rests on   none
Scenarios  none
Buys       Fixed cases per workflow: 4 [d]
           Scheduling arms: 4 [d]
           Maximum planned timed workflows, conditional on gates and timers: 8 [=]
           Maximum planned docking executions: 32 [=]
           Maximum retained pose outputs across timed executions: 1,600 [=]
Flags      none
Full scale none
Outside    DESIGN allowance for human harness implementation, manifest review and report inspection: 8 human hours · DESIGN allowance for local planning and small report artifacts on existing machine: 0 additional USD
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
planned_workflows = arm_count * repeats = 4 * 2 = 8 workflows
planned_dockings = planned_workflows * cases = 8 * 4 = 32 dockings
planned_poses = planned_dockings * retained = 32 * 50 = 1600 poses
total_h = setup_h + compare_h + close_h = 0.5 + 1 + 0.5 = 2 instance hours
total_usd = total_h * hourly_gpu * gpu_count = 2 * 3.29 * 1 = 6.58 USD
setup_box.hours = setup_h = 0.5 = 0.5 h
compare_box.hours = compare_h = 1 = 1 h
close_box.hours = close_h = 0.5 = 0.5 h
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:closest_prior` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Source blocked by browser check. Recorded quote and claims about distributed scaling could not be verified.
- sample 1 · `card:limits` PARTIAL · page: "" · note: Scope exclusions and two-repeat design need no source. Claim about statistical confidence lacks cited support.
- sample 1 · `src:prior` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Source blocked by browser check. Recorded quote and stated support could not be verified.
- sample 2 · `card:test_summary` PARTIAL · page: "" · note: Commands, comparisons, equality checks, thresholds and spending cap describe plan. USD6.58 cost for two instance-hours lacks source.
- sample 2 · `card:closest_prior` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Source returned browser challenge after redirect attempt. Recorded quote and benchmark claims could not be checked.
- sample 2 · `src:prior` UNREACHABLE · page: "Checking your browser before accessing pmc.ncbi.nlm.nih.gov ..." · note: Source returned browser challenge after redirect attempt. Recorded quote and claimed support could not be checked.

**Critic.**
- stakes 5 · `card:if_lever` "At width 2 or 4, both paired four-case workflow speedups reach 1.05 with exact docking and pose equality." · Passing selects concurrent CPU scheduling; failure rejects unchanged-thread concurrency. Measured workflow speed and output equality directly govern that choice.
- lever 1 · `plan:compute_axis.levels` "[1,2,4]" · Concurrency spans only 4×; noise rule does not establish that 1.05 exceeds timing noise. Two conditions fail or remain unverified.
- verifiable 1 · `card:anchor` "Match frozen serial docking outputs and all 50 poses per case, then require identical outputs from each scheduling arm. Tolerance: Zero docking-output and pose-PDB byte differences; zero input or shared immutable-file changes. Exclude only …" · Frozen serial outputs and fresh baseline come from same docking method; equality checks supply no independent truth or published reproduction.
- open 5 · `card:closest_prior` "Published MEGADOCK docking benchmarks reached 98% scaling at 420 nodes; they measured distributed work, not four jobs competing on one host [prior]." · Published distributed scaling addresses different hardware arrangement; same-host four-job contention and output preservation remain open.
- reshape 1 · `card:method` "none" · Only independent docking jobs run side by side; no sequential dependency removed.
- baseline NA · `card:method` "none" · Restructuring method is none.

**Producer says (not judged).** expected unsure (Host saturation and launch overhead could erase concurrency gains; supplied historical observations are private exploratory context, not transferable measurements.); compute_tested partly (Vary host job concurrency, not GPU count or scientific search size. GPU remains unused while its attached CPU host is billed. This is an affordability calibration, not evidence about GPU acceleration or dense-search recovery.); decides no; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd: set by the question
- novelty.closest_prior: a sentence of 22 words
- novelty.left_open: a sentence of 21 words
- test_summary: rewritten by the field repair
- card field test_summary still fails: compute-hours
- dramaturg findings failed G-find after a resample; decided as returned
- dramaturg-2 findings failed G-find after a resample; decided as returned
- prose over 240 words (242)

**Root question (null).** Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget? Small pilot on exactly four unbound PINDER 2024-02 cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Compare existing MEGADOCK CPU standard 3600 rotations, GPU standard 3600, and GPU documented dense 54000 (-D). Keep scoring and retained predictions fixed at 50. Pin prepared input bytes, references, binary/dependency/settings/thread/allocation identities. First establish execution correctness and scientific CPU/GPU agreement at identical settings using justified numerical tolerances sealed before fresh comparison. Then assess dense-search DockQ for rank1 and best50 separately, per case; native references only for evaluation. Calibrate runtime before choosing feasible common budgets; seal configurations, timing repetitions, comparison/noise rules and total spending cap before quality evaluation. Report complete workflow time, GPU activity and billed allocation cost, separating setup/retrieval from steady-state work. Keep acceleration, agreement and additional-search quality conclusions separate. Preserve negatives, unavailable budget arms and overruns. No biological efficacy or beyond-four-case inference. Run2 already exposed quality, so fresh executions are prospective replication under new rules, never unseen holdout or retrospective preregistration. Do not substitute throughput of bundled runs for this question. Repository /home/hal/dev/interp/metis: seed experiments/blind-02/m5/BRIEF.md; case preparation/source/reference pins experiments/blind-02/m5/b01_materials/BRIEF_run1.md:48-158; full prior trace experiments/blind-02/m5/run2_trace/REPORT.md; new assessment experiments/blind-02/science/s01/ASSESSMENT.md. Run2 measured docking totals CPU/GPU/dense 40.07/6.85/69.38 seconds, not complete workflows; standard CPU/GPU transforms and DockQ matched, score max deltas 0.04/0.03/0.04/0.14 with no acceptance tolerance. Dense best50 improved all four observations, rank1 worsened in two including 1nr5. These are exploratory, not sealed conclusions. Historical H100 PCIe rate USD3.29/hour, setup145s, whole unscored bundle median131.9565s; old receipts setup/anchors/freeze/upload/profile/concurrency 145/1571/1402/1424/2832/3448s. Historical allocation and transport observations are estimates for a fresh box, not new producer measurements or public citations. Tree plans only, no box execution. Full card plan ceiling USD100; each later calibration must project below USD20 including setup, retrieval and idle, preferably USD5-10, soft6h/hard12h. Do not run full experiments on calibration route. Identify specific file/section gaps if existing routes cannot implement comparison. Tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases. Measure compilation carries uncertain scalar inputs and phases, not arms/decision_rule; checks 2.5x PROXY or 3x other estimate bands, never scientific equivalence. Measure execution requires missing stage args/controller to be established. Card factual web sources may be checked; do not fabricate citations for private records.

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-02/20261103-1649-tree/out/work/seed-20261103/seed/idea/310ca263/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|
| R1:interp:A | Numerical mechanism audit for CPU/GPU agreement | SAME | CPU GPU numerical agreement | 10 | not_eligible | compute_open none, sequential none |
| R1:interp:B | Fixed-pose score attribution for dense-search ranking failures | ADJACENT | Docking score component attribution | 8 | not_eligible | compute_open none, sequential none |
| R1:interp:C | Protein SAE annotations as scoped research extension | ELSEWHERE | Protein SAE interface hypotheses | 7 | not_eligible | compute_open none, sequential none |
| R1:physical:P1 | Angular-search saturation at fixed output count | SAME | Rotational search quality saturation | 10 | picked_top | highest total with open >= 3, tie of 2 broken by seeded order |
| R1:physical:P2 | Candidate-pool width and native-blind reranking | ADJACENT | Candidate pool reranking benefit | 8 | not_picked | not drawn |
| R1:physical:P3 | Apo-panel scaling and case-dependent benefit | ADJACENT | Apo panel search generalization | 10 | not_picked | not drawn |
| R1:physical:P4 | Sequential atomistic binding and conformational-path sampling | ELSEWHERE | Flexible atomistic binding pathways | 7 | not_eligible | ELSEWHERE; not drawn for the pool |
| R1:physical:P5 | Fixed-batch docking latency through parallel execution | ADJACENT | Parallel docking batch acceleration | 2 | not_eligible | compute_open settled, sequential none |

## Log

```
R1: NOT COMPUTE-BOUND, 2 compute signal(s) -> WIDENER + INTERP
R1:physical: no reshape option
R1:interp: 0 eligible option(s); picking 0
pool: 1 candidate cluster(s); picked 0
seed:idea:seed: dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
seed:idea:seed: question: a sentence of 22 words
seed:idea:seed: test_summary: a sentence of 28 words
seed:idea:seed: novelty.closest_prior: a sentence of 22 words
seed:idea:seed: card fields failing: test_summary (dollar figure); predictions.if_lever (neither if_lever nor if_not contains a number)
R1:physical:top: dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
R1:physical:top: test_summary: a sentence of 31 words
seed:idea:seed: dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
seed:idea:seed: predictions.if_lever: a sentence of 21 words
seed:idea:seed: test_summary: rewritten by the field repair
seed:idea:seed: predictions.if_lever: rewritten by the field repair
seed:idea:seed: card field test_summary still fails: dollar figure
seed:idea:seed: card field predictions.if_lever still fails: neither if_lever nor if_not contains a number
R1:physical:top: dramaturg: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open
seed:idea:seed: dropped the producer's definition of budget_usd: set by the question
seed:idea:seed: test_summary: a sentence of 26 words
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:limits
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dropped the producer's definition of budget_usd: set by the question
seed:idea:seed: novelty.closest_prior: a sentence of 22 words
seed:idea:seed: novelty.left_open: a sentence of 21 words
seed:idea:seed: card fields failing: test_summary (compute-hours)
R1:physical:top: dramaturg (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
R1:physical:top: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: test_summary: rewritten by the field repair
seed:idea:seed: card field test_summary still fails: compute-hours
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg-2: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:limits
seed:idea:seed: dramaturg-2 (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:limits; degenerate: src:dockq
seed:idea:seed: dramaturg-2 findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg-2: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg-2: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
seed:idea:seed: dramaturg-2 (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:anchor; degenerate: card:limits
seed:idea:seed: dramaturg-2 findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg-2 (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg-2 findings failed G-find after a resample; decided as returned
seed:idea:seed: prose over 240 words (262)
seed:idea:seed: prose over 240 words (242)
```