# Dense search changes candidate recovery and ranking differently

Planning only. No Lambda allocation or scientific execution. JSON below is authoritative plan record. All dollar ceilings include allocated-instance wall time; optional recovery is included in stated maximum. Private history comes only from supplied prompt, not inspected files or producer measurements.

```json
{
  "option_title": "Dense search changes candidate recovery and ranking differently",
  "question": "Can 54000 versus 3600 rotations improve best50 DockQ while harming rank1, within identical affordable workflow caps on 4 unbound cases?",
  "hypothesis": "Denser search recovers better candidates, but fixed scoring can rank them poorly, separating best50 gains from rank1 losses.",
  "compute_axis": {
    "quantity": "Rotational samples per complete docking search; outputs remain fixed",
    "unit": "rotations",
    "levels": [
      3600,
      54000
    ]
  },
  "held_fixed": [
    "DESIGN: exactly 4 requested PINDER 2024-02 apo pairs: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Dataset release documented in [pinder].",
    "DESIGN pins supplied by user: MEGADOCK 9575280c875732553266e26adc607dd892b02616; PINDER ebeb28a2f8411363cef722b7d293c978f7442672. Hash prepared receptor/ligand bytes, native references, residue maps, rotation tables and evaluation manifests before allocation.",
    "DESIGN commands: megadock or megadock-gpu -R receptor.pdb -L ligand.pdb -o output -N50 -t1 -v1.2 -e1 -d1 -a-45 -b1 -f3; add -r3600 for standard or -D for dense. Documented interfaces: [usage], [commands]. Verify pinned binary help before launch; public master documentation is not proof of pinned behavior.",
    "DESIGN: 26 OpenMP threads, fixed affinity, 1 H100 PCIe instance, no concurrent docking jobs. Record actual host topology, CPU, driver, CUDA, FFTW, compiler, container, binary hashes and complete environment; reject silent hardware substitution. Price and advertised host allocation: [lambda].",
    "DESIGN: 50 retained poses in native score order; stable recorded tie handling; identical voxel/grid policy, scoring, preparation, chain/residue mapping and scorer. No reranker, CPU dense arm, extra poses or native-guided search."
  ],
  "predictions": {
    "if_lever": "At 54000 rotations, best50 gains exceed 0.01 DockQ plus noise, while rank1 can decline, within common caps.",
    "if_not": "At 54000 rotations, best50 gains fail 0.01 DockQ plus noise, or complete searches exceed common caps; rank1 changes remain separate.",
    "decision_rule": "DESIGN: per case and endpoint compute paired dense-minus-standard DockQ for both scientific repetitions. Meaningful gain requires every paired difference > 0.01 + 2*tau_q; meaningful loss requires every difference < -(0.01 + 2*tau_q). Otherwise label small, mixed or unresolved; print every signed difference. Recovery supported on a case only when its best50 rule passes and both arms finish inside that case's sealed common cap; never infer all-case improvement from a mean. Rank1 has its own identical rule and cannot veto or substitute for recovery. Margin 0.01 is a design choice, not a numerical tolerance. Report per-case, per-cap availability; timeout is unavailable, never DockQ zero. No available shared cap means affordability failure, not quality failure.",
    "noise_rule": "Before study quality, use 3 independent process repetitions on nonstudy fixtures to estimate maximum cross-implementation/repeat discrepancies for score, transformed coordinates and DockQ. Seal tau_score=max(0.000001,2*fixture discrepancy), tau_xyz=max(0.000001,2*fixture discrepancy), tau_q=max(0.000001,2*fixture discrepancy), with ceilings 0.2 score, 0.001 angstrom and 0.0001 DockQ respectively. Exceeding ceilings blocks launch. Independently rescore identical fixture poses 3 times with primary PINDER evaluator and independently pinned DockQ under identical explicit residue and chain maps [pinder, dockq]. Main study uses 2 paired output-and-scorer repetitions, reversed arm order between repetitions. Within-arm endpoint ranges must stay <= tau_q; otherwise mark unstable and stop inference without widening tolerances. Repetitions measure execution uncertainty, not population confidence; deterministic repeats do not create independent biological samples.",
    "expected": "unsure",
    "expected_why": "User-supplied exploratory history suggests recovery/ranking divergence, but new cost admissibility, numerical agreement and sealed replication remain untested."
  },
  "compute_tested": "yes",
  "compute_tested_why": "Search width rises from 3600 to 54000 rotations, a derived 15-fold increase [usage, commands]; GPU affordability and quality are tested separately.",
  "scored_against": "For each retained pose, evaluate DockQ against byte-pinned native complex with sealed chain/residue policy [pinder, dockq]. Rank1 is DockQ of native-score-first output; best50 is maximum evaluated DockQ among exactly 50 outputs. Compare dense against GPU standard under identical per-case caps; compare CPU/GPU standard separately for correctness and workflow acceleration. Native coordinates enter evaluation only.",
  "arms": [
    {
      "id": "cpu_standard",
      "what": "Affordability and agreement baseline: CPU standard, 3600 rotations, 50 outputs, 26 threads; same rented host, GPU idle but billed."
    },
    {
      "id": "gpu_standard",
      "what": "Density baseline: GPU standard, 3600 rotations, 50 outputs, 26 threads, 1 H100 PCIe."
    },
    {
      "id": "gpu_dense",
      "what": "Search intervention: GPU -D, 54000 rotations, 50 outputs, otherwise identical settings."
    }
  ],
  "baseline": {
    "what": "Fresh CPU standard provides affordability/agreement reference; fresh GPU standard provides paired density comparator. No historical timing is treated as a new measurement.",
    "value": "3600 rotations; 50 outputs; CPU and GPU standard",
    "source_id": "commands"
  },
  "anchor": {
    "what": "Reproduce public DockQ example, then cross-check independent DockQ against primary evaluation before scoring study poses. [dockq]",
    "published_value": 0.653,
    "tolerance": "DESIGN: reproduce documented rounded total within 0.0005 DockQ; then require matched-mapping primary/independent scores and repeat variation within fixture-derived tau_q <= 0.0001.",
    "source_id": "dockq",
    "independent_code": "DockQ, separate from PINDER evaluator. Resolve and record immutable source revision and dependency lock in contract phase; reproduce documented example with its documented mapping before study use."
  },
  "checks": [
    "Build contract before allocation: controller must accept exact manifests, arms, repetitions, alternating order, common caps, process deadlines, telemetry, scorer version, tolerances, decision rules, billing timer and termination credentials. Validate parser, rank selection, maximum-over-50, missing-output failure, residue-map identity, checksums, timeout recording and teardown using synthetic fixture outputs. No cloud workload during card preparation.",
    "CPU/GPU agreement gate: all 4 cases at standard settings, 2 paired repetitions. Require 50 finite outputs, identical ranked transform identities, transformed coordinates within tau_xyz, score deltas within tau_score and rank1/best50 within tau_q. Resolve mismatches before density timing. These tolerances come from independent fixtures, not exploratory study score deltas.",
    "Calibrate complete search plus pose generation plus scorer time without inspecting dense native quality. Time scoring on independent matched-size fixtures; time study docking and pose generation with native references inaccessible. Use upper observed timings and score-time bound to admit caps, then enforce actual workflow deadlines in science. A score-time underestimate produces an explicit overrun, not retrospective cap expansion.",
    "Log monotonic stage times, wall-clock instance creation-to-termination, retrieval/build/setup, each docking, each decoy generation and evaluation, upload and idle. Sample GPU activity every 1 second [DESIGN]; retain telemetry and billing receipts. Charge CPU work, retrieval and idle at full instance rate.",
    "User-provided private history, not independently verified and without public URL: best50 rose on 1aua, 1ax2, 1dv1 and 1nr5; rank1 fell on 1aua and 1nr5. For 1nr5, rank1 0.4624993 -> 0.0229593 and best50 0.4624993 -> 0.5699176. Exact rank1 changes on 1ax2 and 1dv1 were not supplied; recover and preserve them before sealing. Do not invent their signs or label private history MEASURED.",
    "User-provided historical standard CPU/GPU transform and DockQ agreement had score maxima 0.04/0.03/0.04/0.14 without sealed tolerances. These values cannot establish acceptance. Fresh executions are prospective replication of exposed cases, never unseen holdout or retrospective preregistration.",
    "Public pinned MEGADOCK documentation fetch failed; fetched master build/command pages are contextual sources [build, commands]. Pin checkout and inspect actual code/help before execution. No private repository files read under this task's read restriction.",
    "For fixed-budget accounting, charge each arm's docking, pose generation and scoring plus an equal share of its allocation's measured setup/retrieval/export/idle overhead. Freeze overhead allocation formula using planned search count before quality; apply actual overhead afterward. Caps use these all-in per-search charges as well as executable process deadlines. Report raw stage timings alongside charges; an overhead overrun makes affected budget arms unavailable."
  ],
  "phases": [
    {
      "id": "contract",
      "what": "Offline build specification: manifest.json contains exact cases, input/reference hashes, source/dependency pins and settings; protocol.json contains arms, anchor, repeat schedule, timing/scoring interfaces, stop rules and noise formulas; controller accepts --manifest --protocol --phase --cap-seconds --deadline --out and records status before teardown. Resolve scorer pin and independent fixtures; hash preliminary agreement/noise contract before allocation.",
      "stop_rule": "No allocation until executable controller, fixture self-checks, immutable dependencies and preliminary seal exist. This card specifies their required contract; it does not claim those executables were implemented."
    },
    {
      "id": "anchors",
      "what": "Start shared calibration timer covering setup, retrieval, anchors, agreement, timing, export and idle. Fetch only required assets. Build CPU/GPU binaries [build]; reproduce DockQ example and run 3 independent nonstudy fixture repetitions. Establish and seal numerical tolerances before study agreement.",
      "stop_rule": "Terminate calibration allocation by 2 hours including all overhead; reject fixture mismatch or any tolerance ceiling breach. Reserve export/teardown inside timer."
    },
    {
      "id": "calibrate",
      "what": "After anchors pass, establish CPU/GPU standard agreement on all 4 cases, then perform at most 2 native-blind timing repetitions of standard/dense searches per case. Reuse standard agreement timings. Time scorer on independent matched-size fixtures. Share this cost screen with any other option using identical measurements, charged once. Estimate complete workflow bounds and remaining science time.",
      "stop_rule": "No full scientific comparison or dense native-quality inspection on calibration route. Abort on disagreement, missing assets, memory failure or exhausted shared calibration timer.",
      "gate": {
        "on": "max_workflow_s",
        "op": "<=",
        "value": 300,
        "else": "No scientific launch; retain unavailable caps and measured bottleneck. Any later calibration needs separate below-20-dollar projection including setup, retrieval and idle."
      }
    },
    {
      "id": "seal",
      "what": "Select feasible common caps from 30, 60, 120 and 300 seconds using calibrated upper bounds; freeze each case's admitted caps, 2 paired scientific repetitions, tolerances, scorer policy, decision rule, exact order, time allowance and spending ledger. Require projected remaining scientific allocation <= 4 hours. Export timestamped hashes before dense quality.",
      "stop_rule": "No admissible common cap or missing executable contract means stop after feasibility report.",
      "gate": {
        "on": "science_need_h",
        "op": "<=",
        "value": 4,
        "else": "Do not launch science; publish infeasibility and required executable/cost changes without altering sealed comparison."
      }
    },
    {
      "id": "science",
      "what": "Fresh allocation: 2 paired GPU standard/dense bundles across all 4 cases, reversed order in second bundle, generating and scoring all 50 outputs each time. Enforce largest admitted per-case workflow cap; derive smaller-cap availability from full workflow completion timestamps. Evaluate rank1 and best50 separately with sealed rules; report CPU-standard workflow reference from calibration. Include fresh setup/export overhead.",
      "stop_rule": "4-hour allocation timer includes setup, retrieval, export and idle. Stop on agreement/noise failure or unexpected environment change; preserve partials and overruns. At 6 aggregate allocation hours stop normally."
    },
    {
      "id": "recovery",
      "what": "Optional operational recovery only for documented interrupted execution or export; preserve sealed arms and rules. No extra cases, retained poses or unplanned quality hunting. Any later calibration is isolated, projected <= 2 hours and below 20 dollars including overhead; reserve is not permission for a full experiment on calibration route.",
      "stop_rule": "At most 6 additional allocation hours, 12 aggregate hours hard, 100 dollars ledger hard. Each allocation reserves teardown time inside its timer; stop earlier when work finishes."
    }
  ],
  "numbers": [
    {
      "id": "budget_usd",
      "name": "Available Lambda credit",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 1000
    },
    {
      "id": "card_cap_usd",
      "name": "Pilot spending ceiling",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 100
    },
    {
      "id": "cases",
      "name": "Exact requested apo cases",
      "unit": "cases",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "standard_rot",
      "name": "Standard rotations",
      "unit": "rotations",
      "basis": "CITED",
      "value": 3600,
      "source_id": "commands",
      "quote": "| `-r [integer]`            | 3600",
      "page_setting": "Public master command guide; pinned checkout still requires verification."
    },
    {
      "id": "dense_rot",
      "name": "Dense rotations",
      "unit": "rotations",
      "basis": "CITED",
      "value": 54000,
      "source_id": "usage",
      "quote": "-D               : set the number of rotational sampling angles to 54000",
      "page_setting": "MEGADOCK public single-node usage; verify requested source pin before allocation."
    },
    {
      "id": "rotation_ratio",
      "name": "Search-width increase",
      "unit": "ratio",
      "basis": "DERIVED",
      "expr": "dense_rot/standard_rot"
    },
    {
      "id": "retained",
      "name": "Fixed retained predictions",
      "unit": "poses/search",
      "basis": "DESIGN",
      "value": 50
    },
    {
      "id": "per_rotation",
      "name": "Predictions per rotation",
      "unit": "poses/rotation",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "voxel_angstrom",
      "name": "Voxel pitch",
      "unit": "angstrom",
      "basis": "DESIGN",
      "value": 1.2
    },
    {
      "id": "electro_weight",
      "name": "Electrostatics weight",
      "unit": "weight",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "hydro_weight",
      "name": "Hydrophobic weight",
      "unit": "weight",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "receptor_penalty",
      "name": "Receptor core penalty",
      "unit": "score weight",
      "basis": "DESIGN",
      "value": -45
    },
    {
      "id": "ligand_penalty",
      "name": "Ligand core penalty",
      "unit": "score weight",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "score_function",
      "name": "Fixed scoring function selector",
      "unit": "selector",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "threads",
      "name": "Pinned OpenMP threads",
      "unit": "threads",
      "basis": "DESIGN",
      "value": 26
    },
    {
      "id": "gpu_count",
      "name": "Allocated GPUs",
      "unit": "GPUs",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "quality_arms",
      "name": "GPU scientific search widths",
      "unit": "arms",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "science_reps",
      "name": "Paired scientific bundles",
      "unit": "repetitions",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "fixture_reps",
      "name": "Independent fixture repetitions and rescoring repetitions",
      "unit": "repetitions",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "agreement_reps",
      "name": "CPU/GPU standard paired repetitions",
      "unit": "repetitions",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "timing_reps",
      "name": "Maximum native-blind timing repetitions per arm/case",
      "unit": "repetitions",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "scientific_searches",
      "name": "Fresh GPU scientific searches",
      "unit": "searches",
      "basis": "DERIVED",
      "expr": "cases*quality_arms*science_reps"
    },
    {
      "id": "scientific_scores",
      "name": "Fresh scientific pose evaluations",
      "unit": "poses",
      "basis": "DERIVED",
      "expr": "scientific_searches*retained"
    },
    {
      "id": "margin_q",
      "name": "Meaningful endpoint change; not noise tolerance",
      "unit": "absolute DockQ",
      "basis": "DESIGN",
      "value": 0.01
    },
    {
      "id": "noise_factor",
      "name": "Fixture discrepancy multiplier",
      "unit": "factor",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "numerical_floor",
      "name": "Minimum numeric tolerance in each stated unit",
      "unit": "numeric floor",
      "basis": "DESIGN",
      "value": 0.000001
    },
    {
      "id": "score_ceiling",
      "name": "Maximum acceptable calibrated score tolerance",
      "unit": "score",
      "basis": "DESIGN",
      "value": 0.2
    },
    {
      "id": "xyz_ceiling",
      "name": "Maximum acceptable coordinate tolerance",
      "unit": "angstrom",
      "basis": "DESIGN",
      "value": 0.001
    },
    {
      "id": "q_ceiling",
      "name": "Maximum acceptable calibrated DockQ tolerance",
      "unit": "absolute DockQ",
      "basis": "DESIGN",
      "value": 0.0001
    },
    {
      "id": "anchor_q",
      "name": "Published rounded DockQ example total",
      "unit": "DockQ",
      "basis": "CITED",
      "value": 0.653,
      "source_id": "dockq",
      "quote": "Total DockQ over 3 native interfaces: 0.653 with BAC:ABC model:native mapping",
      "page_setting": "Public DockQ example 1A2K; independent fixture, not a study-case benchmark."
    },
    {
      "id": "anchor_tol",
      "name": "Tolerance for rounded published example",
      "unit": "absolute DockQ",
      "basis": "DESIGN",
      "value": 0.0005
    },
    {
      "id": "cap_a_s",
      "name": "Candidate common workflow cap",
      "unit": "seconds",
      "basis": "DESIGN",
      "value": 30
    },
    {
      "id": "cap_b_s",
      "name": "Candidate common workflow cap",
      "unit": "seconds",
      "basis": "DESIGN",
      "value": 60
    },
    {
      "id": "cap_c_s",
      "name": "Candidate common workflow cap",
      "unit": "seconds",
      "basis": "DESIGN",
      "value": 120
    },
    {
      "id": "cap_d_s",
      "name": "Largest candidate common workflow cap",
      "unit": "seconds",
      "basis": "DESIGN",
      "value": 300
    },
    {
      "id": "max_workflow_s",
      "name": "Prospective maximum standard/dense complete workflow bound",
      "unit": "seconds/case",
      "basis": "GUESS",
      "value": 300,
      "rests_on": "Conservative screening placeholder, not an observed runtime; private historical docking-only durations omit transport, pose generation and scoring.",
      "measured_by": "calibrate"
    },
    {
      "id": "science_need_h",
      "name": "Prospective all-inclusive remaining science allocation need",
      "unit": "wall-clock hours",
      "basis": "GUESS",
      "value": 4,
      "rests_on": "Conservative admission placeholder including fresh setup, paired output generation, scoring, export and idle; no fresh timing exists.",
      "measured_by": "calibrate"
    },
    {
      "id": "telemetry_s",
      "name": "GPU activity sampling interval",
      "unit": "seconds",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "cal_h",
      "name": "Shared calibration allocation time box",
      "unit": "wall-clock hours",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "science_h",
      "name": "Science allocation time box",
      "unit": "wall-clock hours",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "recovery_h",
      "name": "Optional recovery allocation time box",
      "unit": "wall-clock hours",
      "basis": "DESIGN",
      "value": 6
    },
    {
      "id": "soft_h",
      "name": "Normal aggregate allocation stop",
      "unit": "wall-clock hours",
      "basis": "DERIVED",
      "expr": "cal_h+science_h"
    },
    {
      "id": "hard_h",
      "name": "Hard aggregate allocation stop",
      "unit": "wall-clock hours",
      "basis": "DERIVED",
      "expr": "soft_h+recovery_h"
    },
    {
      "id": "extra_usd",
      "name": "Tax/billing adjustment reserve, spending choice not tax estimate",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 10
    },
    {
      "id": "human_h",
      "name": "Unfunded implementation and review allowance",
      "unit": "person-hours",
      "basis": "DESIGN",
      "value": 16
    },
    {
      "id": "outside_cash",
      "name": "Planned non-Lambda cash expenditure",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 0
    },
    {
      "id": "calibration_usd",
      "name": "Calibration allocation ceiling",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "cal_h*h100_usd_h*gpu_count"
    },
    {
      "id": "base_usd",
      "name": "Calibration plus science allocation ceiling",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "(cal_h+science_h)*h100_usd_h*gpu_count"
    },
    {
      "id": "planned_usd",
      "name": "Maximum priced plan including optional recovery and reserve",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "hard_h*h100_usd_h*gpu_count+extra_usd"
    },
    {
      "id": "h100_usd_h",
      "name": "Published H100 PCIe price per GPU",
      "unit": "USD/GPU/hour",
      "basis": "CITED",
      "value": 3.29,
      "source_id": "lambda",
      "quote": "$3.29",
      "page_setting": "Instances pricing, 1x NVIDIA H100 PCIe row; before applicable taxes."
    }
  ],
  "cost": {
    "rates": [
      {
        "id": "h100_pcie",
        "gpu": "NVIDIA H100 PCIe",
        "gpu_memory_gb": 80,
        "n_gpus": 1,
        "per_gpu_usd_h": 3.29
      }
    ],
    "lines": [
      {
        "id": "calibration",
        "phase": "anchors",
        "what": "Shared setup, retrieval, anchor, agreement, native-blind cost screen and teardown; one charge across calibration phases. Ceiling 6.58 USD, below 20 USD.",
        "kind": "work",
        "rate": "h100_pcie",
        "hours": "cal_h"
      },
      {
        "id": "paired_science",
        "phase": "science",
        "what": "Fresh complete standard/dense paired workflows, scorer repeats, setup, export and idle; ceiling 13.16 USD.",
        "kind": "work",
        "rate": "h100_pcie",
        "hours": "science_h",
        "need": "science_need_h",
        "condition": "Executable protocol, independent anchor, all-case CPU/GPU agreement, common-cap admissibility and seal pass."
      },
      {
        "id": "operational_reserve",
        "phase": "recovery",
        "what": "Optional operational recovery; ceiling 19.74 USD, only actual instance occupancy billed.",
        "kind": "allotment",
        "rate": "h100_pcie",
        "hours": "recovery_h",
        "optional": true,
        "condition": "Documented interruption; unchanged sealed protocol, remaining ledger/time headroom."
      },
      {
        "id": "billing_reserve",
        "phase": "science",
        "what": "Design reserve for taxes or billing adjustment; verify actual quote before allocation.",
        "kind": "allotment",
        "usd": "extra_usd"
      }
    ],
    "yields": [
      "cases",
      "scientific_searches",
      "scientific_scores",
      "science_reps"
    ],
    "spend_cap_usd": 100,
    "total_stated": 49.48
  },
  "full_scale": [],
  "outside_budget": [
    {
      "what": "Design allowance for human implementation, fixture validation, protocol sealing and review; not a measured labor estimate.",
      "qty": 16,
      "unit": "person-hours"
    },
    {
      "what": "Non-Lambda cash planned; public pages and existing prepared inputs assumed accessible, otherwise block contract.",
      "qty": 0,
      "unit": "USD"
    }
  ],
  "restructuring": {
    "sequential_part": "Each answer requires search, pose generation, scoring, then comparison; 4 dependent stages.",
    "method": "none"
  },
  "scope_gap": [
    "No chain-restructuring claim: GPU kernels divide docking work [prior]; this pilot varies search density on a single GPU.",
    "Exact gap supplied by user: tree PLAN can hold arms, anchor, decision_rule, noise_rule and phases; scalar measure compilation omits arms/decision_rule. Number-band checks test runtime estimates, not scientific equivalence. Existing method-equivalence baseline plus one scalar curve cannot implement this comparison.",
    "Specific contract gaps: supplied run2/agent/harness/run_command.sh:8-43 and materials BRIEF_run1.md:48-158 require exact-input/settings reconstruction; no named controller route or missing stage arguments are established here. Need per-case/per-arm outputs, native-blind timing route, independent scorer calibration, paired repetition schedule, cap enforcement and sealed decisions. These files were named in prompt, not read.",
    "Read restriction excludes private repository records, so preparation hashes, complete historical per-case table and harness behavior remain unverified. Obtain them before contract seal; never substitute public PINDER documentation for exact private provenance.",
    "Credit ceiling 1000 dollars does not justify spending it: planned ceiling 49.48 dollars including optional reserve; card cap 100 dollars. No execution performed. No need to estimate work volume to justify timer-bounded allocation.",
    "No separate Lambda filesystem purchased; use instance-local scratch, export before teardown. Therefore no fs_usd_gib_month input or storage cost line is needed. Any persistent filesystem would require new cited pricing and ledger revision before allocation.",
    "This card is written to producer.md. Shell execution failed before any command ran; no local pilot or measured scientific quantities are claimed. Web pages were fetched; files_read lists no local inputs."
  ],
  "novelty": {
    "closest_prior": "MEGADOCK 4.0 timed 1000000 docking jobs; rotation count was unspecified, without this fixed50 recovery-versus-ranking comparison. [prior]",
    "closest_source_id": "prior",
    "prior_max_level": null,
    "left_open": "Whether 54000 rotations improve best50 while harming rank1 on these 4 apo cases, within calibrated common workflow budgets.",
    "decides": "no",
    "searched": true
  },
  "limits": "Only 4 exposed cases; prospective replication, no biological efficacy or population inference. No reranking, CPU dense comparison, extra retained poses, or new parallel algorithm.",
  "test_summary": "Build gated docking/evaluation controller; validate independent scorer and CPU/GPU standard agreement; calibrate complete-workflow caps; seal rules; run 2 paired 3600/54000-rotation bundles on 4 cases, retaining 50. Report rank1, best50, time, GPU activity and billed cost separately.",
  "sources": [
    {
      "id": "lambda",
      "url": "https://lambda.ai/pricing",
      "quote": "NVIDIA H100 PCIe | 80 GB | 26 | 225 GiB | 1 TiB SSD | $3.29",
      "supports": "Fetched Instances 1x pricing section; 1 GPU at 3.29 USD/GPU/hour, advertised memory and host allocation. Public price plus user-supplied start-of-run sheet agree; rate is before applicable taxes."
    },
    {
      "id": "usage",
      "url": "https://www.bi.cs.titech.ac.jp/megadock/usage.html",
      "quote": "-D               : set the number of rotational sampling angles to 54000",
      "supports": "Documented dense-search flag. Other settings in this card are explicit design choices, checked against pinned executable before launch."
    },
    {
      "id": "commands",
      "url": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md",
      "quote": "MEGADOCK parallelizes rotation calculations by using OpenMP.",
      "supports": "Single-node command guide and thread mechanism; standard rotation table includes 3600. Master page contextual only; requested immutable page fetch failed."
    },
    {
      "id": "build",
      "url": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/BUILD.md",
      "quote": "After completion of `make` command, a binary file `megadock-gpu` will be generated.",
      "supports": "GPU single-node build route; separate CPU build documented on same page. Exact dependencies and H100 architecture must be pinned and validated."
    },
    {
      "id": "pinder",
      "url": "https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/README.md",
      "quote": "The current release version of pinder is `2024-02`.",
      "supports": "Pinned PINDER release documentation; evaluation-harness section documents DockQ evaluator. Exact case bytes and preparation remain contract inputs."
    },
    {
      "id": "dockq",
      "url": "https://github.com/wallnerlab/DockQ",
      "quote": "Total DockQ over 3 native interfaces: 0.653 with BAC:ABC model:native mapping",
      "supports": "Independent scorer's public example anchor and explicit mapping interface. Resolve immutable revision during offline contract creation."
    },
    {
      "id": "prior",
      "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4221127/",
      "quote": "In this simulation, a half million docking jobs required 5.71 h, while a million jobs required 11.51 h.",
      "supports": "Open published MEGADOCK throughput result retrieved by web search; different hardware/workload, not a runtime proxy for this pilot. No rotation-axis maximum established."
    }
  ],
  "files_read": []
}
```
