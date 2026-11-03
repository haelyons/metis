# Denser rigid-body search: recovery versus ranking

Planning record only. No box execution or fresh scientific measurements. Numeric scientific acceptance remains blocked on independent justification; no launch until repair gates pass.

```json
{
  "option_title": "Denser rigid-body search: recovery versus ranking",
  "question": "Does GPU docking at 54000 rotations improve rank1 or best50 DockQ over 3600 rotations within identical complete-workflow budgets?",
  "hypothesis": "Denser angular coverage improves best50 recovery more consistently than rank1 because scoring can still favor wrong poses.",
  "compute_axis": {
    "quantity": "Angular orientations searched per docking invocation",
    "unit": "rotations",
    "levels": [
      3600,
      54000
    ]
  },
  "held_fixed": [
    "Exactly these PINDER 2024-02 unbound cases, user-specified: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo.",
    "Keep 50 score-ranked predictions, scoring, preprocessing, atom/residue selection, receptor/ligand assignment, grid policy and actual grids fixed. No reranking or native-guided generation. Parameter interface: [guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md).",
    "Before execution, populate immutable manifest from source/reference pins reproduced in appendix of file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md. Verify source bytes, reproduce chain relabelling and serialization, then hash all 8 prepared PDBs and 4 native references. Historical CSV hashes cannot replace prepared-PDB hashes.",
    "Pin source tree, patches, compiler flags, CPU/GPU/decoygen executable hashes, linked FFTW/CUDA/cuFFT/OpenMP, driver/container, DockQ and preprocessing versions, evaluator/mapping policy, controller hash, CPU affinity, 26 OpenMP threads, allocation UUID and GPU identity. Fail rather than silently substitute inputs or binaries.",
    "Proposed shared settings: -N 50 -t 1 -f 3 -v 1.2 -e 1 -d 1 -a -45 -b 1, identical FFT-grid policy. Confirm against existing harness before sealing; documented interface [guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md). Native files mounted only in evaluator.",
    "CPU standard runs on same rented GPU host, charged for entire instance. This controls hardware allocation, not CPU-only market-cost optimality."
  ],
  "predictions": {
    "if_lever": "At 54000 versus 3600 rotations, best50 DockQ rises over 0.01 beyond noise on all 4 cases; rank1 changes remain separate.",
    "if_not": "At 54000 versus 3600 rotations, at least 1 case lacks best50 DockQ gain over 0.01 beyond noise, or dense search misses budget.",
    "decision_rule": "For each case and eligible common budget, calculate dense-minus-GPU-standard rank1 and best50 separately. Gain iff minimum dense repeated endpoint minus maximum standard endpoint > margin + 2*eps_eval; loss iff maximum dense minus minimum standard < -(margin + 2*eps_eval); otherwise unresolved/no meaningful change. margin=0.01; eps_eval is independently justified and sealed before fresh comparison. All 4 best50 gains support if_lever, any contrary case supports if_not for this strict prediction. Rank1 has its own 4-case gain/loss/unresolved table; never infer rank1 improvement from best50. Missing/timeout arms mean unavailable comparison, not DockQ=0. Acceleration separately requires paired speed-ratio interval lower bound >1.05.",
    "noise_rule": "Use 7 balanced timing blocks, fixed scheduling seed 20261103, all 3 arms per case in randomized order after agreement passes. Record all endpoint ranges; deterministic repeats do not increase biological sample size. Seal evaluator error bound eps_eval on independent fixtures; use worst-case paired endpoint ranges above. Timing: paired block bootstrap, resample 7 blocks jointly across cases, 10000 draws, 95% interval. Exclude only predeclared instrumented diagnostics. No outcome-dependent reruns or tolerance relaxation.",
    "expected": "unsure",
    "expected_why": "User-disclosed exploratory results favor best50 gains but expose rank1 degradation; affordability and prospective numerical acceptance remain unestablished."
  },
  "compute_tested": "yes",
  "compute_tested_why": "Vary documented angular search width by 15 times while fixing retained count and scoring; separate existing GPU acceleration from additional-search quality [guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md).",
  "scored_against": "Same-settings CPU-standard outputs anchor GPU-standard science. Pinned native references evaluate each frozen arm through pinned DockQ: rank1 is highest MEGADOCK score, best50 is maximum DockQ among 50 retained predictions. Native quality never selects timing budgets or tolerances. Public evaluator interface [dockq](https://raw.githubusercontent.com/wallnerlab/DockQ/master/README.md).",
  "arms": [
    {
      "id": "cpu_standard",
      "what": "Existing megadock -r 3600 -N 50; explicit shared flags; CPU standard baseline."
    },
    {
      "id": "gpu_standard",
      "what": "Existing megadock-gpu -r 3600 -N 50; identical shared flags and thread allocation."
    },
    {
      "id": "gpu_dense",
      "what": "Existing megadock-gpu -D -N 50; no conflicting -r; identical scoring and retention. Dense sampling documented by [guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md)."
    }
  ],
  "baseline": {
    "what": "Existing CPU MEGADOCK at 3600 rotations, 50 retained; GPU standard at identical settings isolates added-search effect. Fresh complete-workflow values pending.",
    "value": "Not measured in this planning task",
    "source_id": "guide"
  },
  "anchor": {
    "what": "Independent transform reconstruction and DockQ fixtures validate execution; CPU outputs anchor identical GPU settings before dense quality evaluation.",
    "tolerance": "Exact input/settings/grid/count equality; exact ranked rotation/translation identity required, including rank1 and cutoff membership. Tie mismatch fails this strict gate. Independently implement documented transform reconstruction and compare coordinates within eps_xyz; seal eps_xyz from serialization/rounding analysis. Require abs(score_CPU-score_GPU) <= atol + rtol*max(abs(score_CPU),abs(score_GPU)); derive atol/rtol from pinned FFT precision/error analysis plus nonstudy synthetic fixtures, never fresh four-case differences. Require each paired DockQ difference <= eps_eval. Numeric atol, rtol, eps_xyz and eps_eval remain unresolved blocking inputs: offline repair must provide justified values and freeze them before fresh CPU/GPU comparison; otherwise stop at calibration and report no agreement conclusion.",
    "independent_code": "Build standalone transform-reconstruction checker and independent DockQ-component checker on pinned synthetic fixtures; verify rigid transforms, identity model/native and deliberately displaced ligand. CPU/GPU agreement alone cannot validate shared bugs.",
    "source_id": "dockq"
  },
  "checks": [
    "Build controller and payload: manifest.json, protocol.json, calibrate.py, run_compare.py, reconstruct_check.py, evaluate.py, telemetry sampler and ledger reporter. These are future deliverables, not claimed implemented. Every child process has timeout and artifact flushing; watchdog uses elapsed allocation and actual accrued cost.",
    "Offline dry-run stage arguments, lifecycle transitions, failure injection, retrieval, termination and artifact checks. No box launch until executable route exists. This task writes plan only.",
    "Execution gate: 50 finite ranked scores/transforms, 50 readable decoys, unchanged atom/chains, verified actual grid and input hashes; independent reconstruction and evaluator anchors pass. Standard CPU/GPU agreement must pass before dense predictions receive native scoring.",
    "Scientific tolerance gate remains blocked until independently justified numeric tolerances exist. Historical score deviations cannot set acceptance tolerances. If exact rank/transform gate fails, preserve evidence and stop; any relaxed policy requires new prospective plan.",
    "Mapping policy: freeze allowed chain permutations from sequence identity before quality; apply same evaluator symmetry policy to every pose and arm, log mapping and residue alignment. DockQ can optimize chain mapping [dockq](https://raw.githubusercontent.com/wallnerlab/DockQ/master/README.md); never change policy after seeing an arm.",
    "Timing includes input verification/preparation, docking, reconstruction of 50 decoys, DockQ, compact export. Separately report cold acquisition/build/setup and result retrieval; charge all CPU work, idle and failed/retried work on GPU instance.",
    "Collect uninstrumented monotonic stage timing plus separate diagnostic GPU activity, memory, power and process telemetry at 1-second cadence. Short kernels may be missed; never equate allocation time with GPU busy time. Diagnostic samples excluded from timing comparison by design.",
    "All planned numeric scientific thresholds must appear in frozen protocol before dependent observation; unresolved tolerance symbols are blockers, not implicit zero tolerances.",
    "Prospective replication of already exposed cases; no unseen holdout or retrospective preregistration claim. Historical qualitative evidence and route gaps are user/private provenance recorded in file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md; no public verification claimed.",
    "Route gaps reported by file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md §Specific route gaps, not independently inspected here: dut/pipeline/m5/SCHEMAS.md A/PREDICTIONS 178–188, Propose 211–215, Evaluate 281–288 and adapter 290–299; m5 pipeline.js 1037–1038 cannot express ordered configuration comparison.",
    "Further reported gaps: dut/pipeline/CONTRACT.md §§2.5,5 and src/main.js 468–478/launch.js 71–96 lose arms/decision_rule at compilation; scalar 2.5x PROXY/3x estimate bands are not scientific equivalence. Carry frozen protocol intact beside scalar estimates.",
    "Further reported gaps: dut/pipeline/launch.js 83–107 and measure pipeline.js 45–47,141–153 lack established subsequent stage args/controller. Verify wrapper --stop-after-profile support; do not execute full study through calibration route.",
    "Cost basis: 1 GPU * $3.29/GPU-hour * 12 wall-clock instance hours = $39.48; add $10 reserve = $49.48. Hard card cap $100, below offered $1000 credit. Prices [price](https://lambda.ai/pricing); whole-allocation billing [billing](https://docs.lambda.ai/public-cloud/billing/). Timer controls spend, not a promise that all planned invocations fit."
  ],
  "phases": [
    {
      "id": "repair",
      "what": "Offline only: implement manifest/controller contract, exact stage args, synthetic anchors, independent precision analysis and justified tolerances. Populate missing prepared-PDB hashes from verified bytes. No GPU launch in this planning task.",
      "stop_rule": "No paid work until dry-run lifecycle, independent anchors, timeout/retrieval paths and complete scientific contract pass."
    },
    {
      "id": "calibration",
      "what": "Future bounded timing-only screen: all 4 fixed cases, 1 warmup plus 3 repeats per arm, study native scoring disabled. Use oversized nonstudy synthetic evaluator fixtures to reserve evaluation time; this is calibration, not quality replication. Include setup/build, transport, idle and termination in this allocation.",
      "stop_rule": "3-hour all-in timer costs $9.87 at quoted rate; no full study here. Stop new work early enough for retrieval/termination. Recompute projection using actual rate before launch; projected calibration total must be below $20, target $5–10.",
      "gate": {
        "on": "cal_project_usd",
        "op": "<=",
        "value": 19.99,
        "else": "Do not launch, or stop screen; reduce screen scope without adding cases or evaluating study quality."
      }
    },
    {
      "id": "freeze",
      "what": "After calibration, freeze all numeric tolerances BEFORE fresh CPU/GPU comparison, then budgets/configurations/repetitions/order/noise/decision rules BEFORE quality. Verify signed protocol hash carried to executor. Allocate 1 hour for fresh-host setup/idle if needed.",
      "stop_rule": "Define U_case_arm = 2*maximum calibrated warm invocation time, including measured synthetic evaluator reserve. Freeze per-case tier seconds as ceil(0.75*max(U_CPU,U_GPU)), ceil(max(U_CPU,U_GPU)), ceil(max(U_CPU,U_GPU,U_dense)). Freeze separate batch tiers from serial sums and cold tiers by adding measured setup/acquisition/delivery allowance. Same tiers apply to every arm of each case. Serialize calibration invocations; no bundled-throughput substitution. If evaluator reserve cannot be justified from fixture size/alignment/contact-work coverage, stop without quality."
    },
    {
      "id": "agreement",
      "what": "Fresh CPU/GPU standard comparison on all 4 cases, 1 invocation per arm/case, using sealed independent tolerances; then evaluate their frozen predictions. Separate execution correctness, numerical acceptance and evaluator validation.",
      "stop_rule": "2-hour timer including this phase's idle; any anchor/agreement failure halts dense quality comparison. No thresholds fitted to differences."
    },
    {
      "id": "main",
      "what": "After gates, 1 warmup per arm/case plus 7 balanced randomized blocks across 4 cases and 3 arms. Record every invocation's complete workflow and all 50 DockQ values. Retain per-case rank1/best50 signed changes, winning ranks, timing and budget eligibility.",
      "stop_rule": "4-hour timer. Each invocation has largest frozen tier timeout; incomplete search unavailable at that tier. Smaller tiers are censored from actual timestamps; never relabel partial dense output as complete. No opportunistic extra search or selective repeat. Reuse completed output at larger tiers. Stop new work at cumulative 6-hour soft checkpoint unless all gates and remaining fixed protocol fit hard limits."
    },
    {
      "id": "report",
      "what": "Retrieve artifacts, hash archives, reconcile allocation UTC start/end and final receipt, emit per-case quality/budget tables and separate acceleration/agreement conclusions. Preserve every negative, unavailable arm, timeout and overrun.",
      "stop_rule": "2-hour retrieval/termination reserve; cumulative allocation hard stop 12 hours or $100 total cap, whichever first. Watchdog counts setup, idle and CPU phases. Missing final bill explicitly marked estimated."
    }
  ],
  "numbers": [
    {
      "id": "budget_usd",
      "name": "Card hard spending ceiling",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 100
    },
    {
      "id": "credit_available",
      "name": "User available GPU credit, not spending target",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 1000
    },
    {
      "id": "cases",
      "name": "Exactly user-named unbound cases",
      "unit": "cases",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "arms_count",
      "name": "Required CPU standard, GPU standard, GPU dense arms",
      "unit": "arms",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "standard_rotations",
      "name": "Standard angular search",
      "unit": "rotations",
      "basis": "CITED",
      "value": 3600,
      "source_id": "guide",
      "quote": "3600 angles",
      "page_setting": "Default standard rotation sampling."
    },
    {
      "id": "dense_rotations",
      "name": "Documented -D angular search",
      "unit": "rotations",
      "basis": "CITED",
      "value": 54000,
      "source_id": "guide",
      "quote": "54000 angles",
      "page_setting": "Dense -D rotation sampling."
    },
    {
      "id": "search_ratio",
      "name": "Dense versus standard search width",
      "unit": "ratio",
      "basis": "DERIVED",
      "expr": "dense_rotations / standard_rotations"
    },
    {
      "id": "retained",
      "name": "Fixed predictions per invocation",
      "unit": "poses",
      "basis": "DESIGN",
      "value": 50
    },
    {
      "id": "threads",
      "name": "Frozen OpenMP allocation, verify physical affinity",
      "unit": "threads",
      "basis": "DESIGN",
      "value": 26
    },
    {
      "id": "timing_repeats",
      "name": "Balanced repeated blocks",
      "unit": "blocks",
      "basis": "DESIGN",
      "value": 7
    },
    {
      "id": "warmups",
      "name": "Main warmups per arm/case",
      "unit": "invocations",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "cal_cases",
      "name": "Cases in timing-only calibration, no study native scoring",
      "unit": "cases",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "cal_repeats",
      "name": "Native-blind calibration repeats",
      "unit": "repeats",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "agreement_arms",
      "name": "Standard backends compared first",
      "unit": "arms",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "agreement_repeats",
      "name": "Fresh agreement repetition per arm/case",
      "unit": "repeats",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "prepared_files",
      "name": "Receptor and ligand files",
      "unit": "PDBs",
      "basis": "DERIVED",
      "expr": "cases * agreement_arms"
    },
    {
      "id": "main_invocations",
      "name": "Scored main repeated invocations, contingent on gates",
      "unit": "invocations",
      "basis": "DERIVED",
      "expr": "cases * arms_count * timing_repeats"
    },
    {
      "id": "main_warm_invocations",
      "name": "Untimed warmups",
      "unit": "invocations",
      "basis": "DERIVED",
      "expr": "cases * arms_count * warmups"
    },
    {
      "id": "agreement_invocations",
      "name": "Fresh agreement invocations",
      "unit": "invocations",
      "basis": "DERIVED",
      "expr": "cases * agreement_arms * agreement_repeats"
    },
    {
      "id": "cal_invocations",
      "name": "Screen docking invocations, without native scoring",
      "unit": "invocations",
      "basis": "DERIVED",
      "expr": "cal_cases * arms_count * (cal_repeats + warmups)"
    },
    {
      "id": "main_pose_evals",
      "name": "Main scored repeated poses",
      "unit": "evaluations",
      "basis": "DERIVED",
      "expr": "main_invocations * retained"
    },
    {
      "id": "margin",
      "name": "Meaningful DockQ effect, not numerical tolerance",
      "unit": "DockQ",
      "basis": "DESIGN",
      "value": 0.01
    },
    {
      "id": "speed_threshold",
      "name": "Worthwhile complete-workflow speed ratio",
      "unit": "ratio",
      "basis": "DESIGN",
      "value": 1.05
    },
    {
      "id": "bootstrap_draws",
      "name": "Paired block bootstrap draws",
      "unit": "draws",
      "basis": "DESIGN",
      "value": 10000
    },
    {
      "id": "ci_percent",
      "name": "Timing interval coverage",
      "unit": "percent",
      "basis": "DESIGN",
      "value": 95
    },
    {
      "id": "order_seed",
      "name": "Fixed scheduling and analysis seed",
      "unit": "integer",
      "basis": "DESIGN",
      "value": 20261103
    },
    {
      "id": "telemetry_seconds",
      "name": "Diagnostic telemetry cadence",
      "unit": "seconds",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "cal_h",
      "name": "All-in calibration allocation time box",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "freeze_h",
      "name": "Fresh setup and freeze allocation reserve",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "agreement_h",
      "name": "Agreement allocation time box",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "main_h",
      "name": "Main study allocation time box",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "report_h",
      "name": "Retrieval and termination reserve",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "allocation_h",
      "name": "Maximum total billable instance hours",
      "unit": "hours",
      "basis": "DERIVED",
      "expr": "cal_h + freeze_h + agreement_h + main_h + report_h"
    },
    {
      "id": "soft_h",
      "name": "Cumulative checkpoint",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 6
    },
    {
      "id": "hard_h",
      "name": "Cumulative hard allocation stop",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 12
    },
    {
      "id": "cal_limit",
      "name": "Strictly below $20 calibration gate",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 19.99
    },
    {
      "id": "cal_project_usd",
      "name": "Calibration projected allocation charge; replace with all-in projection before launch",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "cal_h * gpu_count * gpu_rate"
    },
    {
      "id": "other_reserve",
      "name": "Reserve for tax, billing rounding and incidental Lambda charges",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 10
    },
    {
      "id": "persistent_gib",
      "name": "No persistent filesystem provisioned",
      "unit": "GiB",
      "basis": "DESIGN",
      "value": 0
    },
    {
      "id": "fs_usd_gib_month",
      "name": "Illustrative filesystem rate; not current verified tariff",
      "unit": "USD/GiB-month",
      "basis": "PROXY",
      "value": 0.2,
      "source_id": "storage",
      "quote": "$0.20",
      "page_setting": "Lambda documentation example only.",
      "differs_in": [
        "Actual creation tariff unverified; plan provisions no persistent filesystem."
      ]
    },
    {
      "id": "tier_fraction",
      "name": "Low common-budget multiplier",
      "unit": "ratio",
      "basis": "DESIGN",
      "value": 0.75
    },
    {
      "id": "runtime_guard",
      "name": "Design safety factor for calibration maximum, not scientific equivalence",
      "unit": "ratio",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "human_hours",
      "name": "Offline implementation, review and analysis allowance",
      "unit": "person-hours",
      "basis": "DESIGN",
      "value": 16
    },
    {
      "id": "external_cash",
      "name": "Planned extra non-Lambda purchases",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 0
    },
    {
      "id": "gpu_count",
      "name": "GPUs per selected instance",
      "unit": "GPUs",
      "basis": "CITED",
      "value": 1,
      "source_id": "price",
      "quote": "1x",
      "page_setting": "Single-GPU instance tab in supplied pricing snapshot and public pricing page."
    },
    {
      "id": "gpu_rate",
      "name": "Selected single-GPU H100 PCIe price",
      "unit": "USD/GPU-hour",
      "basis": "CITED",
      "value": 3.29,
      "source_id": "price",
      "quote": "$3.29",
      "page_setting": "NVIDIA H100 PCIe single-GPU instance."
    },
    {
      "id": "gpu_memory",
      "name": "Selected GPU memory",
      "unit": "GB",
      "basis": "CITED",
      "value": 80,
      "source_id": "price",
      "quote": "80 GB",
      "page_setting": "NVIDIA H100 PCIe single-GPU instance."
    },
    {
      "id": "allocation_usd",
      "name": "Total maximum allocation charge before reserve",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "allocation_h * gpu_count * gpu_rate"
    },
    {
      "id": "planned_usd",
      "name": "Allocation plus reserve",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "allocation_usd + other_reserve"
    },
    {
      "id": "unspent_credit",
      "name": "Credit not assigned to this card",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "credit_available - planned_usd"
    }
  ],
  "cost": {
    "rates": [
      {
        "id": "h100",
        "gpu": "NVIDIA H100 PCIe",
        "gpu_memory_gb": 80,
        "n_gpus": 1,
        "per_gpu_usd_h": 3.29
      }
    ],
    "lines": [
      {
        "id": "cal_box",
        "phase": "calibration",
        "what": "Timing-only calibration, including setup/retrieval/idle; no study native scoring",
        "kind": "work",
        "rate": "h100",
        "hours": "cal_h"
      },
      {
        "id": "freeze_box",
        "phase": "freeze",
        "what": "Fresh-host setup, protocol transfer and idle reserve",
        "kind": "work",
        "rate": "h100",
        "hours": "freeze_h"
      },
      {
        "id": "agree_box",
        "phase": "agreement",
        "what": "Execution correctness and scientific agreement gate",
        "kind": "work",
        "rate": "h100",
        "hours": "agreement_h"
      },
      {
        "id": "main_box",
        "phase": "main",
        "what": "Fixed four-case replication time box",
        "kind": "work",
        "rate": "h100",
        "hours": "main_h",
        "condition": "All independent anchors, tolerances, agreement and budget freeze pass."
      },
      {
        "id": "report_box",
        "phase": "report",
        "what": "Artifact retrieval, accounting and termination",
        "kind": "work",
        "rate": "h100",
        "hours": "report_h"
      },
      {
        "id": "filesystem",
        "phase": "report",
        "what": "No persistent filesystem; no storage charge. Example tariff is PROXY, not verified current rate.",
        "kind": "storage",
        "usd": "persistent_gib * fs_usd_gib_month"
      },
      {
        "id": "reserve",
        "phase": "report",
        "what": "Dollar reserve, not additional authorized experiments",
        "kind": "allotment",
        "usd": "other_reserve"
      }
    ],
    "yields": [
      "cases",
      "main_invocations",
      "main_pose_evals",
      "standard_rotations",
      "dense_rotations"
    ],
    "spend_cap_usd": 100,
    "total_stated": 49.48
  },
  "full_scale": [],
  "outside_budget": [
    {
      "what": "Offline controller repair, independent numerical review and analysis; design allowance, not measured labor",
      "qty": 16,
      "unit": "person-hours"
    },
    {
      "what": "Additional non-Lambda cash purchases planned; existing workstation and existing local artifact retention used",
      "qty": 0,
      "unit": "USD"
    }
  ],
  "restructuring": {
    "sequential_part": "No dependent angular chain; docking output precedes reconstruction and evaluation. [guide]",
    "method": "none"
  },
  "scope_gap": [
    "Exactly 4 exposed cases, 2 angular levels, fixed 50 retained predictions. No broader biological inference, unseen holdout, CPU-dense arm, score redesign or larger search.",
    "Numeric scientific tolerances and prepared-PDB hashes remain explicit blockers. Plan is concrete implementation contract, not launch-ready scientific acceptance.",
    "Calibration has no study native scoring. Synthetic evaluator reserve must cover pinned input sizes and mapping workload before budgets freeze; otherwise no quality spend.",
    "Default lines are timer-bounded allocations, not predicted completion times. Main yields are targets conditional on gates and frozen-budget completion; overruns/unavailable arms remain reportable.",
    "Persistent storage tariff unverified and irrelevant with zero provisioned storage. Confirm actual H100 availability and rate before launch; no silent hardware fallback.",
    "Private repository paths beyond 2 allowed files were not inspected. Route-gap locations are secondhand from allowed framer, requiring future authorized implementation audit."
  ],
  "novelty": {
    "closest_prior": "Published MEGADOCK GPU study measured docking acceleration at default 3600 rotations; it did not compare dense-search rank1 and best50 DockQ. [prior]",
    "closest_source_id": "prior",
    "prior_max_level": 3600,
    "left_open": "Does 54000-rotation GPU search improve either retained-pose recovery or first-ranked accuracy within complete-workflow budgets on these 4 unbound cases?",
    "decides": "no",
    "searched": true
  },
  "limits": "Exposed 4-case replication only; no biological efficacy, unseen holdout, broad accuracy scaling, or CPU-only market-cost claim. Scientific acceptance remains gated.",
  "test_summary": "Build frozen docking, reconstruction, evaluation and billing harness. Compare CPU and GPU at 3600 rotations; require agreement, then compare GPU 54000 versus 3600 using 50 poses, 7 timing blocks, per-case rank1/best50 and common complete-workflow budgets.",
  "sources": [
    {
      "id": "guide",
      "url": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md",
      "quote": "set the 6 deg. (54000 angles) of rotational sampling (default to none, 15 deg. (3600 angles) of rotational sampling)",
      "supports": "Documented angular levels and -D; command guide also identifies executable, scoring, retention and reconstruction interfaces. Quote is exact table-cell text."
    },
    {
      "id": "price",
      "url": "https://lambda.ai/pricing",
      "quote": "NVIDIA H100 PCIe | 80 GB | 26 | 225 GiB | 1 TiB SSD | $3.29",
      "supports": "1-GPU instance price $3.29/GPU-hour in supplied start-of-run sheet, confirmed pricing page; instance cost equals per-GPU rate times GPU count. Table row, exact page text."
    },
    {
      "id": "dockq",
      "url": "https://raw.githubusercontent.com/wallnerlab/DockQ/master/README.md",
      "quote": "By default, DockQ will try to find the optimal mapping between interfaces found in the native and in the model.",
      "supports": "Evaluator mapping must be pinned; same public documentation gives model/native command and fixed mapping option."
    },
    {
      "id": "prior",
      "url": "https://link.springer.com/article/10.1186/1752-0509-9-S1-S6",
      "quote": "MEGADOCK uses an n_{ θ } value of 3,600 as the default setting.",
      "supports": "Default 3600-rotation setting in nearest retrieved open published GPU performance comparison; mathematical symbol transcribed as extracted."
    },
    {
      "id": "storage",
      "url": "https://docs.lambda.ai/public-cloud/billing/",
      "quote": "For example, at a rate of $0.20 per GiB per month:",
      "supports": "Example filesystem rate only; not verified current tariff. No persistent filesystem in this plan."
    },
    {
      "id": "billing",
      "url": "https://docs.lambda.ai/public-cloud/billing/",
      "quote": "ODC prices instances by hourly usage and bills in one-minute increments.",
      "supports": "Bill whole allocation lifetime, including setup, CPU-only work and idle; allocation cost is distinct from GPU activity."
    }
  ],
  "files_read": [
    "/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/physical-widener.md",
    "/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md"
  ]
}
```

