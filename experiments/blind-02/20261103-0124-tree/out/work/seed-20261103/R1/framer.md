# Understanding before assessment

Task: frame prospective four-case replication; tree planning only, no box execution. Separate GPU acceleration, same-settings scientific agreement, and added-search pose recovery under common complete-workflow budgets. Existing quality already exposed; no unseen holdout claim. Scope and constraints supplied by user; private record URLs below identify local evidence, not public citations.

Predictions before assessment: standard GPU likely faster in docking stage; full-workflow gain smaller. Dense best50 may replicate gains while rank1 remains mixed. More compute cannot repair absent acceptance tolerances, budget definitions, or executable scientific handoff. These predictions guide planning, establish no result.

Evidence to examine: [seed](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/BRIEF.md), [materials](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/b01_materials/BRIEF_run1.md), [prior trace](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md), [assessment](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md). Private file URLs are provenance locators only; no public verification implied.

# Problem definition and evidence limits

Question has three distinct estimands:

1. Acceleration: paired CPU-standard/GPU-standard complete-workflow wall ratio, identical science and inputs.
2. Agreement: same-settings CPU/GPU ranked transforms, scores, poses and evaluation outputs pass independently justified numerical criteria.
3. Additional search: GPU-dense minus GPU-standard DockQ at rank1 and best50, separately for each case, conditional on completed arms fitting same sealed budgets. CPU-standard supplies affordability reference.

These distinctions follow [seed obligations](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/BRIEF.md). Proposed analysis below defines future work; no box, workload, calibration, fresh quality result or scientific acceptance recorded here. Four named records read; public documentation checked. Existing private results remain exploratory, prospective executions remain replication on exposed cases. [Prior trace §B](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md).

Public command guide identifies `megadock`, `megadock-gpu`, `-N` output count, default 3600 rotations and `-D` 54000 rotations. Dense rotation count is 15× standard; runtime need not scale 15×. [MEGADOCK command guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md). CPU/GPU builds use OpenMP; GPU adds CUDA; float FFTW required. [Build guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/BUILD.md). Public documentation supports interface facts, never private timings or hash claims. Attempt to fetch documentation at historical source commit failed; current documentation cannot certify historical binary behavior.

# Exploratory evidence retained

Historical observations below copied from [assessment §A](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md) and [trace §B](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md). URLs identify private provenance; numbers not newly measured or publicly verified.

| Case, apo | CPU 3600 docking s | GPU 3600 docking s | GPU dense docking s | Dense minus standard rank1 DockQ | Dense minus standard best50 DockQ |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1aua | 9.11 | 1.66 | 16.60 | -0.0014054091 | +0.1392531405 |
| 1ax2 | 7.28 | 1.38 | 13.88 | +0.0159331475 | +0.8850219281 |
| 1dv1 | 11.81 | 1.88 | 19.38 | +0.0837337051 | +0.0972629189 |
| 1nr5 | 11.87 | 1.93 | 19.52 | -0.4395400155 | +0.1074182756 |

Docking totals 40.07/6.85/69.38s imply standard CPU/GPU ratio 5.8496, dense/standard GPU ratio 10.1285, dense/CPU-standard ratio 1.7315. Arithmetic supports promising kernel-stage acceleration and greater dense expense, not complete-workflow affordability. Standard CPU/GPU transforms and DockQ matched; maximum score differences 0.04/0.03/0.04/0.14 had null acceptance tolerance. No prospective agreement verdict follows. Dense best50 rose in all four observations; rank1 fell in 1aua and 1nr5. [Assessment §A](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

Historical whole unscored bundle median131.9565s and concurrency factors1.0210/1.0466 concern bundled throughput. Profile assigned11.2939% to kernels,88.4597% to host-labelled categories; these categories do not prove critical path, CPU saturation or GPU saturation. No substitution of these factors for requested comparisons. [Trace §§A,C](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md).

Historical setup145s; anchors/freeze/upload/profile/concurrency receipts1571/1402/1424/2832/3448s. Sum10822s at historical USD3.29/h gives USD9.8901 for those operations, not final allocation bill. Trace reports operator chargeUSD10.53; eventual termination charge unknown. These records warn that transport and idle can dominate short docking runs; fresh measurements required. [Assessment §A](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

# Proposed named arms and identity contract

PLAN proposal, no executions:

| Arm | Executable | Rotation selection | Retained predictions |
| --- | --- | --- | ---: |
| C | existing `megadock` | `-r 3600` | `-N 50` |
| G | existing `megadock-gpu` | `-r 3600` | `-N 50` |
| D | existing `megadock-gpu` | `-D` | `-N 50` |

Command interface supported by [official guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md). Proposed held-fixed settings: scoring function3, voxel1.2Å, electrostatics1, hydrophobic1, receptor penalty-45, ligand penalty1, one prediction per rotation, same FFT-grid policy and actual per-case grid. All values must be checked against retained historical harness before freeze; those interface defaults appear in [guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md). Dense uses `-D` alone; avoid conflicting rotation arguments. No CPU-dense arm, scoring change, reranking, additional cases or increased retention.

Source target from private assessment: commit `9575280c875732553266e26adc607dd892b02616`, tag4.1.4; historical binary printed4.1.3, unresolved. Historical host used26 OpenMP threads. Do not infer binary identity from version string. [Assessment §A](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

Proposed freeze manifest: exact source tree and local patch hashes; compiler/linker commands and flags; CPU/GPU/decoygen executable SHA-256; linked FFTW, CUDA/cuFFT, OpenMP, libc identities; driver, GPU UUID/model/memory, CPU model/topology, RAM, OS/container digest; affinity, `OMP_NUM_THREADS=26`, OMP binding, CUDA device visibility, MPS state, host/GPU exclusivity and power/clock policy. Pin DockQ release/commit and environment, preprocessing code/environment, launcher/controller, evaluator and telemetry code. Reconfirm actual allocation inventory/rate, never infer fresh box from history. These are required future measurements, currently pending.

Prepared-byte gate: verify canonical source bytes and index row, reproduce exact chain relabelling/serialization, hash all eight prepared PDBs, store byte counts and manifests before any fresh docking. Reference files independently hashed; docking process receives prepared monomers only. Native mount/access limited to evaluator. CSV hashes below pin selection records, not resulting PDB bytes; named records do not expose all eight final prepared hashes here. Missing hashes remain explicit blocking inputs, never filled with source hashes. [Materials lines48–158](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/b01_materials/BRIEF_run1.md); [trace §B.1](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md).

Exact four-case scope:

- `1aua__A1_P24280--1aua__A2_P24280:apo`
- `1ax2__A1_P16404--1ax2__A2_P16404:apo`
- `1dv1__A1_P24182--1dv1__B1_P24182:apo`
- `1nr5__A1_P07547--1nr5__A2_P07547:apo`

Identities, preparation and source/reference pins reproduced in appendix from [materials lines48–158](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/b01_materials/BRIEF_run1.md). No substitution with holo inputs or FroDock executable.

# Ordered phases and gates

Design below is prospective proposal, not completed preregistration. Final numerical criteria and calibrated budgets must be resolved and sealed before dependent fresh observations.

**Phase0 — offline protocol repair.** Carry immutable PLAN hash, arms, pins, metrics, decision_rule, noise_rule and phase order through controller. Dry-run stage arguments, stop behavior, timeouts, ledger and artifact retrieval without box. Define independent anchor fixtures for decoy reconstruction and evaluator; empty anchor list cannot validate science. Tree planning ends here until executable route established. Existing gaps documented in [assessment §§D,E](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

**Phase1 — bounded calibration and numerical justification.** First later screen must project belowUSD20 including setup, retrieval, idle and termination; targetUSD5–10. Never execute full study on calibration route. Select one screen, not combined candidate suite. Numerical screen: unchanged monomer inputs, within-backend repeats and non-native synthetic precision/reconstruction fixtures; independently review floating-point error and serialization effects. CPU-only exact-byte repeat may test reproducibility, cannot establish CPU/GPU agreement. Do not inspect fresh cross-backend differences to choose tolerance. Old maximum0.14 cannot become threshold plus epsilon. If adequate independent justification unavailable, stop agreement claim. [Assessment §C1](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

Tolerance proposal form: for each ranked score require `abs(sC-sG) <= atol + rtol*max(abs(sC),abs(sG))`; justify and seal numerical atol/rtol from precision analysis and independent fixtures. Separately seal transform/pose coordinate thresholds, tie/rank correspondence rule, all50 output coverage and DockQ numerical tolerance. Grid, case identities, output counts and scientific settings require exact equality. Near ties require predetermined handling; never silently reorder after failure. Thresholds currently unresolved: no scientific gate can PASS yet. Numerical tolerance, meaningful DockQ effect margin and runtime uncertainty are separate quantities.

Timing screen proposal: one warmup and three balanced timing-only blocks over all four cases and C/G/D, native scoring disabled; capture preparation, docking, decoy generation, retrieval and idle separately. One instrumented diagnostic pass, kept separate from uninstrumented timing. Evaluator overhead estimated with synthetic/nonstudy model-native fixtures until scientific gate passes; remaining uncertainty carried conservatively into budget. If calibrated evaluator overhead later exceeds reserve, retain overrun rather than adjust caps after quality. This screen estimates costs, never answers quality or full acceleration.

**Phase2 — prospective freeze.** Seal resolved numerical tolerances before new C/G comparison. After runtime calibration, seal final configurations, rate, common budgets, repetitions, order seed, acceleration/effect/noise rules, failure rules and totalUSD100 ceiling before fresh quality. Timing proposal: one untimed warmup plus seven randomized balanced C/G/D blocks, scheduling seed20261103. No early stopping when preferred result appears; no selective reruns. Randomization affects scheduling, not docking searches. Seven repetitions estimate runtime variability, not seven independent biological samples.

Common budget proposal: for each case, calibration upper cost estimate U for complete invocation, including conservative evaluator reserve. Generate common absolute time tiers from `0.75*max(U_C,U_G)`, `max(U_C,U_G)`, and `max(U_C,U_G,U_D)`; round upward to whole seconds and freeze actual values before evaluation. Every arm faces same tiers for that case. Report corresponding dollars plus separately assigned setup/retrieval costs. Also report all-four-case batch budgets derived from calibrated batch times; do not mix per-case and batch denominators. Budget-limited arm terminates without result at cap; discrete54000-rotation search cannot be relabelled completed from partial search. Completed output may be assessed at all larger tiers without duplicating run or selecting best repeat. No automatic extra search with leftover budget.

Full-workflow cold budgets include acquisition/preparation/build/setup and result delivery. Warm budgets include prepared-input verification through50 decoys, evaluation and compact result export. Report cold and warm feasibility separately. Shared setup charged once in study ledger, but standalone arm estimate includes its own setup; state amortization for fixed four cases. Billed allocation cost uses entire reserved lifetime, including CPU work and idle on GPU host. GPU busy seconds are separate measurement. CPU arm on same host supports controlled implementation contrast, not CPU-only market-price optimum.

**Phase3 — execution correctness and agreement gate.** Verify settings, binary/input hashes, printed grids, fifty finite ranked transforms/scores, fifty readable decoys, atom/chains and reconstruction consistency. Run sealed C/G same-settings comparison first, then evaluate their frozen predictions under sealed evaluator. Halt D quality comparison if agreement fails; retain failure evidence and spend. Distinguish executable correctness, numerical agreement and evaluator anchor validation. [Required ordering](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/BRIEF.md).

**Phase4 — quality replication, only after gates.** Produce D predictions with same scoring, evaluate50 against pinned native per case. Freeze mapping policy for homologous chains; log chosen mapping and residue alignment. DockQ supports model/native scoring and configurable chain mapping; defaults can optimize mapping, so evaluator identity and policy matter. [DockQ documentation](https://github.com/wallnerlab/DockQ). Native used only for evaluation, never pose generation, ranking, input selection or budget tuning.

Proposed outputs: per case/arm rank1 DockQ, best50 DockQ, winning best50 rank, all50 values, transforms/scores and timing/status. Report signed D-G changes for both metrics regardless sign. Define scientific gain only when signed delta exceeds independently established scorer/repeat noise bound and chosen meaningful margin0.01;0.01 is design preference, not numerical equivalence tolerance or published efficacy cutoff. If repeats differ, report range and apply sealed worst-case criterion; never select favorable run. Deterministic repeats do not increase case sample size. Preserve every negative, near-zero result, mismatch, timeout, unavailable arm and budget overrun. No aggregate claim may conceal rank1 degradation.

Acceleration proposal: per-case paired C/G complete-workflow ratios and all-four batch ratio; retain all seven pairs. Report medians and95% paired-block bootstrap interval, resampling seven blocks jointly across cases,10000 draws, fixed analysis seed20261103. Worthwhile acceleration only if lower bound>1.05; otherwise inconclusive/negative under rule. Small-block interval limitation stated. Instrumented samples excluded by design, not outcome. No speedup conclusion from cost-estimate PASS.

**Phase5 — accounting and report.** Monotonic timestamps for process stages; UTC allocation start/end; telemetry GPU utilization/memory/power and process activity at declared cadence, acknowledging short-stage sampling limits. Separately report uninstrumented wall, diagnostic kernel time, GPU busy measurements, CPU resource use, setup/retrieval bytes and seconds, model/controller idle, failure/retry costs and final provider bill. Cost is billed allocation, not kernel seconds×rate. If final bill unavailable, report estimate and missing receipt explicitly.

Proposed spending controls: each calibration projected<USD20, preferablyUSD5–10; soft6h/hard12h further bounded by dollar cap. At historicalUSD3.29/h,USD20 allows about6.08h,USD100 about30.40h;12h costsUSD39.48 before extra charges. Therefore time limit alone cannot enforce calibration budget. Historical six-receipt3.006h plus0.594h reserve gives3.6h/approximatelyUSD11.84, planning estimate only. Lean screen0.3–0.8h/approximatelyUSD0.99–2.63 remains unproven; transfer/idle may invalidate it. Rate and reserve verified before future launch. Stop new work before remaining reserve insufficient for retrieval/termination; retain actual overrun. Historical basis: [assessment §§A,C2](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md). No fresh producer MEASURED input claimed.

# Specific route gaps

Locations below copied from inspected assessment, not independently reread source files; read scope restricted to four named records. [Assessment §E](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

| Location | Gap | Required repair |
| --- | --- | --- |
| `dut/pipeline/m5/SCHEMAS.md` A/PREDICTIONS178–188, Propose211–215, Evaluate281–288, adapter290–299; `pipeline.js`1037–1038 | Five-method output-preserving menu cannot represent three named configurations, ordered agreement then changed-search quality, two outcomes per case and calibrated budget eligibility. | Optional configuration-comparison protocol with named pairs, agreement gate, distinct acceleration/quality outcomes and lifecycle costs. |
| `dut/pipeline/CONTRACT.md` §2.5 and §5; `src/main.js`468–478; `launch.js`71–96 | PLAN can describe arms/anchor/decision/noise/phases; compilation drops arms/decision_rule, checks scalar2.5×PROXY or3×other bands. | Carry frozen scientific contract alongside scalar calibration; broad estimate bands never scientific equivalence. |
| `dut/pipeline/launch.js`83–107; measure `pipeline.js`45–47,141–153 | Compile emits triage artifacts, missing established design/subsequent stage args and controller chain. | Concrete offline-validated stage args/controller, launcher, payload review, telemetry, stop and post/ledger handling before box. |
| m5 `pipeline.js`1037–1038 versus supplied wrapper `--stop-after-profile` | Profile stop absent from inspected pipeline; wrapper implementation unverified. | Verify bounded wrapper stop before pricing/launch; do not assume flag supported directly. |
| AssessmentC1 and traceB.1–3 | Prepared PDB hashes, justified tolerances and independent anchors not all concretized in accessible plan. | Fill from verified bytes/independent analysis; retain unknowns until then. |

U51 exact-byte checks and U52 scheduling screens can establish narrower properties with authored harness; neither replaces seed comparison. No additional threshold tweak, GPU count or bundled throughput run repairs these contracts. [Assessment §§C1,C4,E](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

# Compute assessment

Inference: current bottleneck is scientific/execution contract and missing prospective calibration, not shortage of parallel hardware. Historical docking stages already take seconds to tens of seconds across four cases; setup/transport and controller completeness remain decisive uncertainties. More parallel compute cannot supply justified tolerances, restore dropped arm semantics or turn exposed quality into holdout evidence. Evidence basis: [assessment §§A,E](file:///home/hal/dev/interp/metis/experiments/blind-02/science/s01/ASSESSMENT.md).

Conditional compute signals:

- Matched independent allocation replicas could improve timing/noise and precision characterization after pins and protocol freeze. Cost accounting must include every allocation; they cannot be used to claim same-budget improvement from increased spend.
- Independent per-case decoy generation and DockQ evaluations could shorten evaluation wall after predictions freeze, potentially changing which complete workflows fit fixed caps. Hold evaluator/mapping/50 predictions fixed; measure added allocation cost and contention. No claim such scaling already demonstrated.

These are possible later compute levers, not reasons to scale current planning task. Final scientific answers remain open: stage acceleration promising; prospective agreement unestablished; dense best50/rank1 effects and affordability require separated replication. No biological efficacy or beyond-four-case inference. [Seed](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/BRIEF.md), [trace §B](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace/REPORT.md).

# Appendix: recorded case/source/reference pins

Copied verbatim from named materials lines48–158. SHA values describe historical records, not fresh downloads. Native references remain evaluation-only. [Private materials provenance](file:///home/hal/dev/interp/metis/experiments/blind-02/m5/b01_materials/BRIEF_run1.md).

The FroDock distribution in these records has provenance `unverified_mirror`. The four recorded units are apo pairings from PINDER release `2024-02`, sampled at zero-based unit-manifest indices `3, 5, 9, 15`. Their recorded examination was a FroDock CPU/MPI unit-concurrency probe whose listed comparison outputs were fifty final ranked PDBs per unit. The identities and input records below are those sampled units.


### Cases and prepared input records

Each fenced CSV block is the original UTF-8 header followed by one original selected record, with LF line endings and a final LF. The path strings in those records are logical prepared-input names emitted by the recorded preprocessing; remote source locations are given separately. The full four-unit selection, in the order below, is 644 bytes with SHA-256 `f34c87e11bc77f02997f41aaae17cf6958ce02976b9621886d96c03029b27af0`.


#### 1. `1aua__A1_P24280--1aua__A2_P24280:apo`

PINDER system: `1aua__A1_P24280--1aua__A2_P24280`; kind: `apo`; unit index: `3`. In the recorded index entry, `pinder_s=True`, `apo_R=True`, `apo_L=True`; `apo_R_pdb=6f0e__A1_P24280.pdb` and `apo_L_pdb=6f0e__A1_P24280.pdb`.


Prepared CSV block: 179 bytes; SHA-256 `a97af77279a2cac61eee504904b82603710ae1194885ff132569cae5826d3e18`. The record alone, excluding header, is 155 bytes with SHA-256 `2e55e24dd1c1edea33bcc687150727fbb1cdd30ee5b3a1f34c59b8fd2f2e3431`.

```csv
id,kind,receptor,ligand
1aua__A1_P24280--1aua__A2_P24280,apo,1aua__A1_P24280--1aua__A2_P24280/inputs/apo/1aua_apo_R.pdb,1aua__A1_P24280--1aua__A2_P24280/inputs/apo/1aua_apo_L.pdb
```


The source-index selection is the single row whose `id` equals the system identifier above, with pairing `apo` and its recorded canonical `apo_R_pdb` / `apo_L_pdb` fields. The recorded preprocessing reads those complete monomer files, assigns chain labels `R` and `L` to receptor and ligand respectively, and serializes them to the named prepared PDBs. This describes the recorded input origin; no new residue or atom selection is introduced.


| Input source or reference location | Fetch URL | Recorded bytes | Recorded SHA-256 |
| --- | --- | ---: | --- |
| Index source; exact row selection above: `index.parquet` | https://pinderdata.org/2024-02/index.parquet | 124511839 | `ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4` |
| Canonical receptor source: `pdbs/6f0e__A1_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb | 192456 | `622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd` |
| Canonical ligand source: `pdbs/6f0e__A1_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb | 192456 | `622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd` |
| Reference native bound complex: `pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb | 388881 | `a12fd5f7506b927c1d435464cabbb9cd59299fdc4a826b63302052b0fef41a48` |


The reference location is a directly fetched PDB, so no archive-member path applies. Reference contents are not included here.


#### 2. `1ax2__A1_P16404--1ax2__A2_P16404:apo`

PINDER system: `1ax2__A1_P16404--1ax2__A2_P16404`; kind: `apo`; unit index: `5`. In the recorded index entry, `pinder_s=True`, `apo_R=True`, `apo_L=True`; `apo_R_pdb=3n35__A1_P16404.pdb` and `apo_L_pdb=3n35__A1_P16404.pdb`.


Prepared CSV block: 179 bytes; SHA-256 `2357dfd034f88367b5e4b51d92effc039c8f413ed15030eacec858e7fa5006d8`. The record alone, excluding header, is 155 bytes with SHA-256 `9f1d3b6811303f2dccc7004f25a8827defdbfee1c1a8100186790a0b4674be3b`.

```csv
id,kind,receptor,ligand
1ax2__A1_P16404--1ax2__A2_P16404,apo,1ax2__A1_P16404--1ax2__A2_P16404/inputs/apo/1ax2_apo_R.pdb,1ax2__A1_P16404--1ax2__A2_P16404/inputs/apo/1ax2_apo_L.pdb
```


The source-index selection is the single row whose `id` equals the system identifier above, with pairing `apo` and its recorded canonical `apo_R_pdb` / `apo_L_pdb` fields. The recorded preprocessing reads those complete monomer files, assigns chain labels `R` and `L` to receptor and ligand respectively, and serializes them to the named prepared PDBs. This describes the recorded input origin; no new residue or atom selection is introduced.


| Input source or reference location | Fetch URL | Recorded bytes | Recorded SHA-256 |
| --- | --- | ---: | --- |
| Index source; exact row selection above: `index.parquet` | https://pinderdata.org/2024-02/index.parquet | 124511839 | `ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4` |
| Canonical receptor source: `pdbs/3n35__A1_P16404.pdb` | https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb | 151794 | `b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e` |
| Canonical ligand source: `pdbs/3n35__A1_P16404.pdb` | https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb | 151794 | `b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e` |
| Reference native bound complex: `pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb` | https://pinderdata.org/2024-02/pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb | 300591 | `111ed0e1daea9ff8575bb61a2184b5f58fedd5437846e0f8026bebb53ef77a10` |


The reference location is a directly fetched PDB, so no archive-member path applies. Reference contents are not included here.


#### 3. `1dv1__A1_P24182--1dv1__B1_P24182:apo`

PINDER system: `1dv1__A1_P24182--1dv1__B1_P24182`; kind: `apo`; unit index: `9`. In the recorded index entry, `pinder_s=True`, `apo_R=True`, `apo_L=True`; `apo_R_pdb=3g8c__A1_P24182.pdb` and `apo_L_pdb=3g8d__A1_P24182.pdb`.


Prepared CSV block: 179 bytes; SHA-256 `90912611cb8363253de9a33055834c1edab8898865a69d413aae39efb11e0eb9`. The record alone, excluding header, is 155 bytes with SHA-256 `29685cddda4e4da851c041bcf8fbefe06b020c716e8014d492f44a4e1b4272fa`.

```csv
id,kind,receptor,ligand
1dv1__A1_P24182--1dv1__B1_P24182,apo,1dv1__A1_P24182--1dv1__B1_P24182/inputs/apo/1dv1_apo_R.pdb,1dv1__A1_P24182--1dv1__B1_P24182/inputs/apo/1dv1_apo_L.pdb
```


The source-index selection is the single row whose `id` equals the system identifier above, with pairing `apo` and its recorded canonical `apo_R_pdb` / `apo_L_pdb` fields. The recorded preprocessing reads those complete monomer files, assigns chain labels `R` and `L` to receptor and ligand respectively, and serializes them to the named prepared PDBs. This describes the recorded input origin; no new residue or atom selection is introduced.


| Input source or reference location | Fetch URL | Recorded bytes | Recorded SHA-256 |
| --- | --- | ---: | --- |
| Index source; exact row selection above: `index.parquet` | https://pinderdata.org/2024-02/index.parquet | 124511839 | `ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4` |
| Canonical receptor source: `pdbs/3g8c__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/3g8c__A1_P24182.pdb | 277182 | `48aa5f4b2ac1e57d855b85d56a9c4a74c4b16f7d165b0fce03535815e26bdb60` |
| Canonical ligand source: `pdbs/3g8d__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/3g8d__A1_P24182.pdb | 234657 | `1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c` |
| Reference native bound complex: `pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb | 536625 | `a159da5b6b145570b4d03ac9e17eb7b4315f7a8afd0497a93ad1f77a55debf3e` |


The reference location is a directly fetched PDB, so no archive-member path applies. Reference contents are not included here.


#### 4. `1nr5__A1_P07547--1nr5__A2_P07547:apo`

PINDER system: `1nr5__A1_P07547--1nr5__A2_P07547`; kind: `apo`; unit index: `15`. In the recorded index entry, `pinder_s=True`, `apo_R=True`, `apo_L=True`; `apo_R_pdb=1sg6__A1_P07547.pdb` and `apo_L_pdb=1sg6__A1_P07547.pdb`.


Prepared CSV block: 179 bytes; SHA-256 `cba9eaa447e9a2a228eaa9c322892f1b8cccb7687e1c24ec089edd4d11804aa9`. The record alone, excluding header, is 155 bytes with SHA-256 `ae51c38740db1a6d2d067395b18b37743b98085be8e40a72ce278c981028bb65`.

```csv
id,kind,receptor,ligand
1nr5__A1_P07547--1nr5__A2_P07547,apo,1nr5__A1_P07547--1nr5__A2_P07547/inputs/apo/1nr5_apo_R.pdb,1nr5__A1_P07547--1nr5__A2_P07547/inputs/apo/1nr5_apo_L.pdb
```


The source-index selection is the single row whose `id` equals the system identifier above, with pairing `apo` and its recorded canonical `apo_R_pdb` / `apo_L_pdb` fields. The recorded preprocessing reads those complete monomer files, assigns chain labels `R` and `L` to receptor and ligand respectively, and serializes them to the named prepared PDBs. This describes the recorded input origin; no new residue or atom selection is introduced.


| Input source or reference location | Fetch URL | Recorded bytes | Recorded SHA-256 |
| --- | --- | ---: | --- |
| Index source; exact row selection above: `index.parquet` | https://pinderdata.org/2024-02/index.parquet | 124511839 | `ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4` |
| Canonical receptor source: `pdbs/1sg6__A1_P07547.pdb` | https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb | 234171 | `4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5` |
| Canonical ligand source: `pdbs/1sg6__A1_P07547.pdb` | https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb | 234171 | `4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5` |
| Reference native bound complex: `pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb` | https://pinderdata.org/2024-02/pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb | 484785 | `ee2fc49ec38f26a216154fd7ce0a93086f2ba60dde6997d86deb196bac96f861` |

VERDICT: NOT COMPUTE-BOUND
