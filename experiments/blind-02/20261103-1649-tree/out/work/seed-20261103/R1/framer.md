# Understanding and predictions before assessment

Task: frame prospective replication of three MEGADOCK configurations on exactly four specified PINDER 2024-02 apo cases. Separate execution acceleration, scientific agreement, and dense-search recovery at common budgets. Tree planning only; no box execution. Run2 quality already seen; fresh runs cannot be unseen holdout or retrospective preregistration. Scope follows [seed](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/BRIEF.md) and [assessment §§A–F](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

Predictions, conditional and not new measurements: (1) GPU standard likely remains faster in docking timers; complete-workflow gain smaller and uncertain. (2) Documented dense GPU search likely costs more than CPU standard docking, so acceleration alone likely cannot fund all added sampling at CPU-standard wall budget. (3) Dense best50 advantage may repeat while rank1 remains mixed; 1nr5 ranking loss must remain visible. (4) Extra parallel hardware alone will not resolve missing scientific tolerances or comparison/controller contracts. Basis: historical observations and route audit, already known before this framing: [run2 trace §§B–E](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md), [assessment §§A,E](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md). These are informed predictions after exposure to exploratory results, not independent preregistered hypotheses.

Proceed: define estimands and evidence limits, pin required identities, design gated calibration and comparison, identify execution gaps, then classify whether added parallel compute addresses binding uncertainty.

# Problem definition

Three arms: C = existing CPU implementation, 3600 rotations; G = existing GPU implementation, 3600; D = existing GPU implementation, documented `-D`, 54000. Each retains exactly 50 predictions. Official command guide documents `megadock`, `megadock-gpu`, `-r`, `-D`, `-N`, scoring switches and OpenMP control. Dense sampling count increases 15-fold; runtime need not scale 15-fold. [MEGADOCK command guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md).

Proposed estimands:

- Acceleration: paired complete-workflow ratio T(C)/T(G), separately docking-only ratio. Four-case portfolio primary; retain per-case times.
- Agreement: C/G standard settings, every ranked transform and score, generated pose correspondence, rank1/best50 DockQ. This validates implementation interchangeability only within sealed margins and four cases.
- Affordability: which completed arm fits each common wall and allocation-dollar cap, including comparison D/C as well as D/G.
- Additional-search recovery: for each case i, Δrank1(i)=DockQ(D rank1)−DockQ(G rank1); Δbest50(i)=max50 DockQ(D)−max50 DockQ(G). Keep both, with signs and raw values. No average replacing opposed case effects.

Proposed budget unit: one completed four-case portfolio with 50 poses per case. Also retain per-case ledger, but do not silently change portfolio cap into per-case cap. Define steady-state T as verified prepared-input staging through docking, pose generation, scoring, validation and result export. Report cold total separately, adding acquisition/preparation/build/setup and allocation idle. For counterfactual cold-arm comparisons charge shared setup consistently to each alternative; actual study ledger charges shared setup once. An arm fitting steady-state cap may fail cold cap. No partial-run DockQ, restart policy, reranking, extra retained poses or adaptive native-guided sampling.

# Historical evidence, without upgrading its status

Run2 observations below copied from private reports, not newly measured. Citation covers every table entry: [assessment §A](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md), [trace §B](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md).

| Case prefix | C docking s | G docking s | D docking s | Δrank1 | Δbest50 |
|---|---:|---:|---:|---:|---:|
| 1aua | 9.11 | 1.66 | 16.60 | −0.0014054091 | +0.1392531405 |
| 1ax2 | 7.28 | 1.38 | 13.88 | +0.0159331475 | +0.8850219281 |
| 1dv1 | 11.81 | 1.88 | 19.38 | +0.0837337051 | +0.0972629189 |
| 1nr5 | 11.87 | 1.93 | 19.52 | −0.4395400155 | +0.1074182756 |

Historical totals C/G/D = 40.07/6.85/69.38 s. Derived ratios: standard acceleration 5.8496; D/G 10.1285; D/C 1.7315. Thus exploratory docking acceleration exists, but documented D did not finish inside C docking time. These timers exclude complete workflow. CPU/GPU standard ranked transforms and DockQ matched; ranked score maxima differed 0.04/0.03/0.04/0.14, with acceptance tolerance null. Neither matching outcomes nor those maxima establish a justified prospective margin. [Trace §B](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md).

Historical bundle median 131.9565 s excludes DockQ; observed concurrency factors 1.0210 and 1.0466 describe bundled throughput. Profile kernel allocation 11.2939% and host-labelled allocation 88.4597% are aggregate accounting, not exclusive critical path or CPU utilization. These cannot establish GPU saturation or refute three-arm research question. Host contention plausible, precise bottleneck unresolved. [Trace §§A,C,D](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md).

# Identity and provenance contract

Exact case list, all apo, PINDER release 2024-02; prefixes elsewhere in document refer only to these IDs. Source and native hash values below are historical recorded pins, not payloads verified here. [Materials lines 48–158](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/b01_materials/BRIEF_run1.md).

| Exact case | Apo receptor / ligand source basename | Native source basename |
|---|---|---|
| 1aua__A1_P24280--1aua__A2_P24280:apo | 6f0e__A1_P24280.pdb / same | 1aua__A1_P24280--1aua__A2_P24280.pdb |
| 1ax2__A1_P16404--1ax2__A2_P16404:apo | 3n35__A1_P16404.pdb / same | 1ax2__A1_P16404--1ax2__A2_P16404.pdb |
| 1dv1__A1_P24182--1dv1__B1_P24182:apo | 3g8c__A1_P24182.pdb / 3g8d__A1_P24182.pdb | 1dv1__A1_P24182--1dv1__B1_P24182.pdb |
| 1nr5__A1_P07547--1nr5__A2_P07547:apo | 1sg6__A1_P07547.pdb / same | 1nr5__A1_P07547--1nr5__A2_P07547.pdb |

Recorded SHA-256 for each unique apo source, with original fetch URL; values sourced from [private materials](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/b01_materials/BRIEF_run1.md), not asserted as freshly verified public hashes:

- [6f0e](https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb): `622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd`.
- [3n35](https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb): `b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e`.
- [3g8c](https://pinderdata.org/2024-02/pdbs/3g8c__A1_P24182.pdb): `48aa5f4b2ac1e57d855b85d56a9c4a74c4b16f7d165b0fce03535815e26bdb60`.
- [3g8d](https://pinderdata.org/2024-02/pdbs/3g8d__A1_P24182.pdb): `1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c`.
- [1sg6](https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb): `4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5`.

Recorded native SHA-256, same private provenance:

- [1aua native](https://pinderdata.org/2024-02/pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb): `a12fd5f7506b927c1d435464cabbb9cd59299fdc4a826b63302052b0fef41a48`.
- [1ax2 native](https://pinderdata.org/2024-02/pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb): `111ed0e1daea9ff8575bb61a2184b5f58fedd5437846e0f8026bebb53ef77a10`.
- [1dv1 native](https://pinderdata.org/2024-02/pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb): `a159da5b6b145570b4d03ac9e17eb7b4315f7a8afd0497a93ad1f77a55debf3e`.
- [1nr5 native](https://pinderdata.org/2024-02/pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb): `ee2fc49ec38f26a216154fd7ce0a93086f2ba60dde6997d86deb196bac96f861`.

Recorded selection CSV: 644 bytes, SHA-256 `f34c87e11bc77f02997f41aaae17cf6958ce02976b9621886d96c03029b27af0`. Recorded index: 124511839 bytes, SHA-256 `ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4`, [index fetch URL](https://pinderdata.org/2024-02/index.parquet). Preparation reads complete canonical monomers, relabels receptor/ligand chains R/L, serializes PDB. CSV/source hashes do not pin resulting prepared PDB bytes. Run2 setup logged prepared hashes, but seal retained null placeholders. Required before future execution: recover immutable prepared artifacts and hashes or regenerate with frozen serializer/dependencies, hash all eight PDBs, compare against historical recorded hashes where available, resolve mismatches before docking. Prepared-byte pins remain missing from this framing; do not invent them. [Materials lines 48–158](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/b01_materials/BRIEF_run1.md), [trace §B.1](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md).

Run2 source identity recorded as commit `9575280c875732553266e26adc607dd892b02616`, tag 4.1.4, printed version 4.1.3; discrepancy unresolved. Public current build guide requires FFTW float support and CUDA for GPU build, and exposes compiler/optimization/OpenMP build choices. Current docs support interface description, not proof historical binary bytes match commit. Pinned-commit raw documentation fetch failed here; no claim historical docs independently verified. [Assessment §A](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md), [build guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/BUILD.md).

Proposed sealed manifest must include source archive/tree hash, clean/patch state, binaries including decoygen, compiler/version/flags, FFTW/CUDA/cuFFT/OpenMP runtime identities, dynamic-library hashes, OS/container, DockQ/Python/dependency lock, preprocessing code and eight input hashes, four reference hashes. Freeze exact commands and all resolved scoring/grid/voxel/output settings; record per-case FFT grid. Recover historical scoring values rather than assuming defaults. Hold 26 OpenMP threads per job, dynamic false, serial case scheduling and fixed affinity; pin CPU topology, GPU UUID/model, driver, clock/power policy, visibility, MPS state, allocation ID/type/rate/billing quantum. Any forced allocation deviation requires documented new seal. Historical 26-thread setting comes from [assessment §A](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md); remaining items are required design, not established identities.

# Gated prospective design

Everything below proposed PLAN, not completed experiment or executable launch seal. Numerical tolerances, prepared hashes and controller remain unresolved. No scientific agreement PASS permitted until supplied and sealed.

1. **Offline contract and correctness preparation.** Freeze manifests/commands; validate output parser, 50 ordered records, finite scores, transform-to-PDB reconstruction and chain/atom preservation. Validate scorer on independently known identical-structure and deliberately displaced fixtures; record expected properties and mapping. Empty anchor set cannot count as independent validation: run2 had 0/0 anchors. [Trace §A.1](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md).

2. **Small calibration only.** First measure cold/warm compact artifact retrieval and setup. Then bounded timing-only sampling on all four cases/three arms, without native scoring. Start one warmup plus three randomized timing blocks; sample GPU activity separately where instrumentation perturbs wall. Measure per-arm whole command and pose generation; estimate scoring overhead using synthetic fixtures or historical labelled estimate. Later native scorer cost can cause recorded overrun, never retroactive cap adjustment. Stop when useful runtime envelope available; do not run final quality study on calibration route. If route cannot stop at declared boundary, do not launch.

3. **Independent numerical evidence, before fresh cross-backend comparison.** Within-backend repeats on frozen inputs diagnose determinism. Use arithmetic/FFT precision analysis and separate synthetic error fixtures to justify score absolute/relative bounds, rigid-transform/coordinate bounds and DockQ evaluation error. Repetition alone cannot establish cross-backend systematic error. Define ranked-pose correspondence and tie rule without natives; inspect cutoff-50 gap under error bounds. Exact within-backend bytes provide deterministic diagnostic, not universal scientific tolerance. Never choose margin from historical maximum 0.14 plus epsilon. If independent justification unavailable, retain agreement UNKNOWN and block density-quality inference. Requirement follows [seed](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/BRIEF.md), unresolved evidence documented in [assessment §C1](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

4. **Seal final comparison before fresh quality evaluation.** Include manifest hash, numerical margins and justification, exact timing schedule, randomization seed, budgets, noise rules, cost cap, telemetry/retrieval policy and stop rules. Proposed final timing: one excluded warmup plus seven randomized blocks of C/G/D, paired within block on same allocation; seed 20261103. All work including warmups billed. Prospective target for worthwhile standard acceleration: 95% lower confidence bound on median paired C/G workflow ratio ≥1.05. Proposed computation: 10000 block bootstrap resamples with fixed seed, no per-case pseudo-replication; seven blocks yield limited precision, report raw ratios and interval. If noisy/inconclusive, report that; no automatic extra repetitions. Choose three common budget caps by deterministic calibration rule: round up 1.25× maximum observed complete-workflow estimate for each arm to billing/time quantum, sort/deduplicate; if caps coincide, retain fewer distinct caps. Seal actual values before quality. Conservative projection must fit full-plan USD100 ceiling. These numerical rules are design choices, not biological thresholds or established noise tolerances.

5. **Fresh C/G agreement gate.** Execute standard arms first under frozen settings. Check all 50 scores/transforms/pose identities, grids, output counts and evaluation metrics against independently justified margins. Standard-only native evaluation permitted here after seal; native unavailable to docking/scoring selection code. Per-case failure blocks main dense-quality inference, and remains reported. Do not relax thresholds after failure. Same output correspondence with score differences may pass only if sealed rule explicitly permits and justifies it.

6. **Dense comparison after gate.** Generate fresh D outputs and evaluate all 50 with pinned scorer. Proposed two independently executed scientific blocks to detect execution/scoring instability, budgeted explicitly; deterministic identical repeats add repeatability evidence, not biological sample size. Keep rank1 defined by MEGADOCK score; native only evaluates. DockQ documents automatic interface mapping and optional fixed mapping; freeze one mapping policy before evaluation, including symmetric homodimer treatment, same across all arms. Prefer exact historical policy if recoverable; do not select mapping to improve D. [DockQ official README, mapping and JSON output](https://github.com/wallnerlab/DockQ#modelnative-chain-mapping).

Proposed quality decision: report every signed per-case Δrank1 and Δbest50. Call meaningful benefit for metric/case only when Δ exceeds max(0.01, independently justified paired scorer/execution error bound) in both scientific blocks; call degradation symmetrically; otherwise unresolved/small effect. Margin 0.01 is chosen reporting threshold, never substitute for error calibration. Report signs even inside margin. Repeated deterministic runs cannot yield population confidence intervals. No four-case biological or general docking-efficacy inference.

Proposed budget decision: completed verified portfolio eligible only if measured workflow time and actual allocation cost both fit sealed cap. Timeout, missing outputs, failed agreement or overrun stored as distinct status; absent budget arm has no imputed DockQ. If D fits only high cap, report benefit conditional on high cap, not improvement at lower cap. At fixed cap, deterministic repeated G searches do not create denser search or more than 50 retained predictions. Record slack, do not fill budget with unrequested ensembles. This preserves three arms rather than inventing anytime algorithm.

# Accounting and spending feasibility

Historical H100 PCIe rate USD3.29/h and six receipts 145/1571/1402/1424/2832/3448 s sum 10822 s, 3.0061h, USD9.8901 by arithmetic. This excludes parts of whole allocation. Freeze plus upload alone 2826 s; complete workflow per arm and ultimate termination charge unknown. Old operator USD10.53 record not reconstructible as final bill. Historical quantities are private observations, not fresh producer measurements or public market quote. [Trace §§B.11,E](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md), [assessment §A](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

Proposed standalone calibration allowance: 0.3–0.8 allocated h, USD0.99–2.63 at historical rate, conditional on compact retrieval/controller. Conservative old-route allowance 3.6h, USD11.84; covers old 3.006h receipt scale plus reserve. These copied planning estimates, not guarantees or permission to run three full m5 routes. Three old routes project roughly USD29.61 before further reserve. [Assessment §C2](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

Before each later calibration, reprice actual allocation including setup, builds, retrieval, storage, billing quantum, retries and idle. Require projection strictly below USD20, target USD5–10, soft stop6h/hard12h; tighter money limit wins. At historical rate USD20 buys about6.079h, so hard12h cannot justify budget expansion. No new run after projected cap exhausted. Full-plan ceiling USD100 includes shared calibration costs and all downstream comparison work; overlapping candidate cards not additive spending authority. Limits follow supplied task and [assessment §§C,D](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

Proposed ledger: allocation start/end/bill receipt; monotonic phase spans; setup, retrieval, steady-state docking, pose generation, evaluation, export, idle; GPU UUID/activity samples and integrated busy estimate; CPU seconds/thread count; exit/timeout and input/output hashes for each arm/case/repetition. Report device kernel time separately from sampled GPU busy and allocated GPU-seconds. Use uninstrumented primary wall timings; profile trace diagnostic. Assign idle and shared costs by predeclared rule and reconcile component charges to total without summing overlapping receipt spans. Bill unavailable → cost estimate explicitly labelled, no fabricated measured bill. Preserve overruns even if terminated before usable poses.

# Specific route gaps and minimal repairs

File/line claims below are reported by named assessment/trace, not independently re-read source files. Reading scope limited to four prompt-named files; public docs checked separately. Private `file://` citations identify local records, not public evidence.

| Route | Reported file/section gap | Required next action |
|---|---|---|
| m5 comparison | `dut/pipeline/m5/SCHEMAS.md` A/PREDICTIONS lines178–188; Propose211–215; Evaluate281–288; adapter290–299. Five-method menu and same-configuration equivalence cannot express ordered C/G agreement then D/G changed quality with separate metrics. `pipeline.js:1037–1038` stops on negative menu. | Add optional named-configuration mode with frozen three arms, pair-specific metrics, agreement gate, per-case budget outcomes and separate quality/performance results. Preserve existing menu semantics. |
| Tree PLAN | `dut/pipeline/CONTRACT.md` §2.5 lines95–162 and `src/schemas.js:187–217` can hold arms, anchor, held_fixed, decision_rule, noise_rule and phases. | Use PLAN for complete comparison description now. Tree acceptance proves plan expressibility, not scientific result. |
| Tree→measure | `dut/pipeline/src/main.js:468–478` omits arms/decision_rule; `launch.js:71–96` validates scalar bands, 2.5× PROXY or3× otherwise. | Carry immutable PLAN/manifest and scientific comparison rules through handoff; keep cost-input band validation separate. Those bands never scientific equivalence. |
| Measure controller | `dut/pipeline/launch.js:83–107` emits QUESTION/CARD/triage args; stage requires measure `pipeline.js:45–47` and `design_args.json`/numbered args at141–153, absent controller handoff. | Establish concrete design/gate/build/tests/review/launch/post args, script/controller, resource bounds, receipts and ledger ingestion; prove handoffs offline before box. |
| Bounded m5 calibration | `dut/pipeline/m5/pipeline.js:1037–1038` lacks verified profile-stop behavior; offered wrapper option unverified in allowed records. U51/U52 terminate after reproduce. | Verify actual wrapper stop before using; otherwise choose explicit bounded measure controller. U51 byte equality alone does not test numerical CPU/GPU agreement. |

All route facts sourced to [assessment §§C–E](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md), [trace §C](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md). No missing stage implemented or controller launched in this framing. No whole experiment substituted for calibration.

# Compute judgment

Binding issues: missing independently justified agreement margins; incomplete prepared-byte/build/dependency identities; absent complete per-arm accounting; scientific comparison lost through controller/compilation contracts. More devices cannot establish those rules. Historical execution totals small relative to transport/allocation wall; bundle concurrency is irrelevant to original contrast. These grounds support planning judgment NOT COMPUTE-BOUND, not physical claim that MEGADOCK kernels never limited by compute. [Assessment §§A,C–E](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md), [trace §§C–E](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md).

Conditional compute signals:

- Complete-workflow paired timing after protocol repair: independent matched allocations could buy more timing blocks and reveal allocation variability; extra hosts change cost estimand, require prespecified matching, billing and cap. More parallel jobs on same host may instead add contention.
- Standard-versus-dense prospective replication on exact four cases: independent resources could finish frozen arms sooner and expose execution variability after agreement gate; no new cases, scoring, retained count or search settings. Extra aggregate spending does not make D affordable under original fixed cap or turn observed quality into holdout evidence.

Immediate next step: complete offline manifest/tolerance/controller plan, then select one bounded runtime/validity calibration. Scientific answer remains conditional: exploratory standard docking faster, scientific interchangeability unsealed, dense best50 gains coexist with rank1 losses, fixed-budget complete-workflow benefit unmeasured. Evidence remains limited to four already examined cases. [Trace §B](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md).

VERDICT: NOT COMPUTE-BOUND
