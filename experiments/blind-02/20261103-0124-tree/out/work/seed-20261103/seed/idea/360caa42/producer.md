# Concrete experiment plan

```json
{
  "option_title": "Dense search changes candidate recovery and ranking differently",
  "question": "Can affordable GPU search across 54000 rotations improve best50 DockQ while worsening rank1, compared with 3600 rotations on four apo cases?",
  "hypothesis": "More rotations recover better candidates, but unchanged scoring can rank worse poses first, separating best50 gains from rank1 losses.",
  "compute_axis": {
    "quantity": "Rotations searched per docking job, holding retained outputs fixed",
    "unit": "rotations",
    "levels": [
      3600,
      54000
    ]
  },
  "held_fixed": [
    "DESIGN: exactly user-selected PINDER 2024-02 apo cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. Release documented at https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/README.md [pinder]. Exact case selection comes from user.",
    "DESIGN: MEGADOCK commit 9575280c875732553266e26adc607dd892b02616; PINDER commit ebeb28a2f8411363cef722b7d293c978f7442672. Verify revisions before launch; pinned MEGADOCK documentation fetch failed during planning.",
    "DESIGN: preserve -N50 -t1 -v1.2 -e1 -d1 -a-45 -b1 -f3; standard -r3600, dense -D. Flag meanings: https://www.bi.cs.titech.ac.jp/megadock/usage.html [usage]. No reranker, CPU-dense arm or additional retained poses.",
    "DESIGN: hash prepared input bytes, references, residue/chain maps, preparation code, container, dependency lock and binaries. Record compiler flags, CUDA/driver/FFTW versions, FFT grids, affinity, allocation identity, commands and ranking/tie rules. Native coordinates enter evaluation only.",
    "DESIGN: one H100 PCIe GPU, 26 logical CPU threads, fixed affinity, serial cases; record actual topology. Alternate paired standard/dense order by repetition."
  ],
  "predictions": {
    "if_lever": "At 54000 rotations, best50 DockQ gains exceed 0.01 and calibrated noise; rank1 may decline, within common complete-workflow budgets.",
    "if_not": "At 54000 rotations, best50 gains fail 0.01 or noise thresholds, or complete workflows exceed common budgets; rank1 remains separately reported.",
    "decision_rule": "DESIGN: per case and cap in {60,120,300} seconds, both GPU arms must complete search, reconstruction of 50 poses, scoring and logging within cap in every repetition. Additional rescoring used to assess noise is accounted separately. Recovery support requires every paired best50 difference >max(0.01,epsilon_case_best50); ranking harm requires every paired rank1 difference <-max(0.01,epsilon_case_rank1). Report all four cases and both signed endpoints, including smaller changes. No common feasible cap means unavailable comparison. CPU standard provides affordability reference. Margin 0.01 is design, not established numerical tolerance.",
    "noise_rule": "DESIGN: independently validate scorer fixtures and precision before fresh quality. On three CPU/GPU standard repeats per case, seal endpoint epsilon=max(0.000001,2*standard-repeat range,10*independent-scorer discrepancy). Abort if epsilon>0.005 or independent scorer discrepancy>0.00001. Before dense evaluation seal these values. Then run three paired GPU standard/dense output repeats per case; rescore each saved output three times. Fresh within-arm endpoint range exceeding sealed epsilon invalidates case; never widen tolerance afterward. Report individual values and ranges, without population confidence intervals. Record seeds if implementation uses randomness.",
    "expected": "unsure",
    "expected_why": "User-supplied exploratory history suggests recovery gains with ranking losses, but fresh timing, agreement and calibrated repeatability remain unestablished."
  },
  "compute_tested": "yes",
  "compute_tested_why": "DESIGN: vary search width by factor 15, fixed scoring and 50 retained poses; test additional search bought with GPU time.",
  "scored_against": "DESIGN: pinned native references and pinned PINDER DockQ implementation. Rank1 uses original docking-score order; best50 is maximum evaluation DockQ over exactly 50 retained predictions. Compare GPU dense against GPU standard per case. Independently check scorer using https://github.com/wallnerlab/DockQ [dockq]; validate CPU/GPU standard first.",
  "arms": [
    {
      "id": "cpu_standard",
      "what": "megadock, -r3600: matched-settings agreement and CPU affordability reference."
    },
    {
      "id": "gpu_standard",
      "what": "megadock-gpu, -r3600: additional-search quality baseline."
    },
    {
      "id": "gpu_dense",
      "what": "megadock-gpu, -D: 54000 rotations, unchanged scoring and retained poses."
    }
  ],
  "baseline": {
    "what": "Time CPU standard and GPU standard on same pinned host. CPU/GPU comparison establishes acceleration and agreement; GPU standard/dense comparison establishes density effect. Historical docking-only times do not replace full workflow measurements.",
    "value": "3600 rotations; 50 outputs",
    "source_id": "usage"
  },
  "anchor": {
    "what": "Reproduce independent DockQ example, then require matching CPU/GPU standard transforms, rankings and DockQ before dense quality evaluation. [dockq]",
    "published_value": 0.994,
    "tolerance": "DESIGN: documented example first-interface score within 0.0005 of printed 0.994; unrounded cross-scorer discrepancy<=0.00001 on identical mappings. Seal docking-score tolerance=max(0.000001,2*maximum independent-fixture CPU/GPU score difference), capped at 0.2, before selected-case agreement. Fresh standard requires identical ordered rotation/translation identifiers and DockQ endpoint differences<=0.0001. Failure stops comparison; no tuning to selected-case quality.",
    "source_id": "dockq",
    "independent_code": "Pin independent wallnerlab/DockQ commit and fixture bytes before launch. Run documented 1A2K example and native-self/rigid-transform checks. Compare PINDER and independent code with identical residue handling and fixed chain maps. PINDER evaluation documented at https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/README.md [pinder]."
  },
  "checks": [
    "DESIGN: build manifest validator, command generator, timeout/termination supervisor, decoy reconstruction, isolated scoring worker, invoice ledger and per-case report before rental. Dry-check checksum errors, missing/duplicate poses, timeout handling, rank preservation and coordinate transforms. Require exactly 50 finite predictions.",
    "DESIGN: hash protocol before calibration; seal calibrated tolerances, cap selection, repetition order, spending ledger and commands before fresh comparison. Timing calibration cannot access selected-case natives. Standard agreement may access native references; fresh dense quality remains unopened until agreement passes.",
    "DESIGN: capture allocation start/stop, retrieval/build/idle/export and per-stage wall times, CPU occupancy and GPU activity at 1-second intervals. Report elapsed workflows and summed stage time separately. Charge CPU work, idle and transport while allocated; idle billing documented at https://docs.lambda.ai/public-cloud/billing/ [billing].",
    "USER-SUPPLIED HISTORY, not newly measured or publicly verified: docking-only CPU/GPU/dense totals 40.07/6.85/69.38 seconds; standard transforms and DockQ matched. Maximum score differences 0.04/0.03/0.04/0.14 had no sealed tolerance. These are not full-workflow speedups or prospective agreement.",
    "USER-SUPPLIED HISTORY, not new evidence: best50 increased on 1aua, 1ax2, 1dv1 and 1nr5; rank1 declined on 1aua and 1nr5. For 1nr5, rank1 0.4624993→0.0229593 and best50 0.4624993→0.5699176. Preserve every case and sign; no invented public citation.",
    "DESIGN: prospective replication after exposed exploratory results, never unseen holdout or retrospective preregistration. Separate acceleration, agreement, affordability and recovery conclusions. Preserve overruns and unavailable arms. No GPU workloads while carding."
  ],
  "phases": [
    {
      "id": "contract",
      "what": "Offline: implement controller and independent fixtures; fill exact input checksums, dependency pins and stage arguments. Validate protocol and dry-check watchdog before allocation. Prepared bytes must match requested historical preparation; no private repository inspection was performed here.",
      "stop_rule": "No launch until executable manifest, fixtures, ledger, watchdog and protocol seal exist."
    },
    {
      "id": "calibrate",
      "what": "First rental includes setup, retrieval, build and cleanup, charged once. Calibrate precision/scorer on independent bundled fixtures. Time one complete standard and one dense search on largest-grid selected case without native scoring; bound other cases from pinned FFT grids. Measure reconstruction/scoring overhead on independent fixtures. Count caps admitting all-case predicted workflows under 3 times measured timing plus measured overhead. No full four-case quality experiment on calibration route. Conservative total projection must also fit shared science_h allocation, including all agreement/search jobs, scorer repeats, setup and idle; otherwise no scientific launch. Independent scoring fixture, native-self and rigid-transform fixture are separate fixed inputs.",
      "stop_rule": "2-hour allocation timer. Stop if projected calibration charge exceeds USD10 or is not strictly below USD20 including all allocation overhead. No native quality rerun merely to create measurement.",
      "gate": {
        "on": "admissible_caps",
        "op": ">=",
        "value": 1,
        "else": "Export calibration evidence and stop; no scientific rental or dense quality comparison."
      }
    },
    {
      "id": "seal",
      "what": "Offline: replace timing uncertainty with measurements, choose smallest admissible cap from 60/120/300 seconds, and freeze scoring tolerance, commands, paired order and total projected cost. Agreement and later science need explicit executable stage arguments.",
      "stop_rule": "Stop if conservative complete-workflow bound exceeds 300 seconds for either GPU arm on any case, or if all-in allocation cannot fit time/spending boxes."
    },
    {
      "id": "agreement",
      "what": "Shared science rental: three standard CPU/GPU repeats on all four cases. Validate ordered transforms, rankings, scores and DockQ. Derive per-case noise envelopes using sealed formula; seal resulting envelopes before fresh dense evaluation.",
      "stop_rule": "Stop on any anchor failure, DockQ difference>0.0001, score tolerance failure, independent scorer error>0.00001 or epsilon>0.005.",
      "gate": {
        "on": "agreement_pass",
        "op": ">=",
        "value": 1,
        "else": "Stop scientific comparison; retain disagreement report and receipts."
      }
    },
    {
      "id": "compare",
      "what": "Same science rental: three paired standard/dense GPU repetitions on every case; three rescoring repetitions per saved output. All cases retain 50 outputs. Report paired rank1/best50 differences and each common-budget eligibility result. Agreement standard outputs are separate from fresh paired outputs.",
      "stop_rule": "Agreement plus comparison share 3-hour allocation limit. Enforce selected per-workflow cap. Incomplete jobs remain unavailable; do not trim into completed arms. Stop on noise-envelope violation."
    },
    {
      "id": "export",
      "what": "Export outputs, manifests, raw timing/activity logs, scorer results, seals and receipts. Report setup/retrieval separately from steady-state work and invoice-rounded allocation cost.",
      "stop_rule": "Export allowance<=1 hour; aggregate allocation<=6 hours, stricter than user hard12h. All-in spending<=USD25. Watchdog reserves final billing minute inside boxes; no automatic extension."
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
      "id": "card_ceiling",
      "name": "User full-card ceiling",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 100
    },
    {
      "id": "credit_stop",
      "name": "Chosen all-in spending stop",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 25
    },
    {
      "id": "cases",
      "name": "User-selected apo cases",
      "unit": "cases",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "retained",
      "name": "Retained predictions per search",
      "unit": "poses",
      "basis": "DESIGN",
      "value": 50
    },
    {
      "id": "paired_repeats",
      "name": "Paired GPU quality repetitions per case",
      "unit": "pairs",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "agreement_repeats",
      "name": "CPU/GPU standard repetitions per case",
      "unit": "repetitions",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "rescore_repeats",
      "name": "Scorer repetitions per output",
      "unit": "repetitions",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "gpu_arms",
      "name": "Search-width arms",
      "unit": "arms",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "agreement_arms",
      "name": "Standard implementations",
      "unit": "arms",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "threads",
      "name": "Pinned logical CPU threads",
      "unit": "threads",
      "basis": "DESIGN",
      "value": 26
    },
    {
      "id": "gpus",
      "name": "GPUs per instance",
      "unit": "GPUs",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "gpu_mem",
      "name": "Chosen GPU memory",
      "unit": "GB",
      "basis": "DESIGN",
      "value": 80
    },
    {
      "id": "standard_rot",
      "name": "Standard rotations",
      "unit": "rotations",
      "basis": "CITED",
      "value": 3600,
      "source_id": "usage",
      "quote": "default to 3600 angles",
      "page_setting": "MEGADOCK documented standard"
    },
    {
      "id": "dense_rot",
      "name": "Dense rotations",
      "unit": "rotations",
      "basis": "CITED",
      "value": 54000,
      "source_id": "usage",
      "quote": "set the number of rotational sampling angles to 54000",
      "page_setting": "MEGADOCK documented -D"
    },
    {
      "id": "width_factor",
      "name": "Search expansion",
      "unit": "ratio",
      "basis": "DERIVED",
      "expr": "dense_rot / standard_rot"
    },
    {
      "id": "per_rotation",
      "name": "Predictions per rotation, -t",
      "unit": "poses",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "voxel",
      "name": "Voxel pitch, -v",
      "unit": "angstrom",
      "basis": "DESIGN",
      "value": 1.2
    },
    {
      "id": "electrostatics",
      "name": "Electrostatics weight, -e",
      "unit": "ratio",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "hydrophobic",
      "name": "Hydrophobic weight, -d",
      "unit": "ratio",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "rec_penalty",
      "name": "Receptor core penalty, -a",
      "unit": "score parameter",
      "basis": "DESIGN",
      "value": -45
    },
    {
      "id": "lig_penalty",
      "name": "Ligand core penalty, -b",
      "unit": "score parameter",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "score_function",
      "name": "Scoring function, -f",
      "unit": "option",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "calibration_h",
      "name": "All-inclusive calibration time box",
      "unit": "instance-hours",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "science_h",
      "name": "Shared agreement/quality time box",
      "unit": "instance-hours",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "export_h",
      "name": "Export/termination allowance",
      "unit": "instance-hours",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "soft_h",
      "name": "User soft duration; chosen stricter stop",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 6
    },
    {
      "id": "hard_h",
      "name": "User hard duration",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 12
    },
    {
      "id": "calibration_target",
      "name": "Calibration projection stop",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 10
    },
    {
      "id": "calibration_ceiling",
      "name": "Calibration projection must be strictly below",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 20
    },
    {
      "id": "persistent_gib",
      "name": "No persistent filesystem",
      "unit": "GiB",
      "basis": "DESIGN",
      "value": 0
    },
    {
      "id": "fs_usd_gib_month",
      "name": "Illustrative filesystem rate, not current tariff",
      "unit": "USD/GiB-month",
      "basis": "CITED",
      "value": 0.2,
      "source_id": "filesystem",
      "quote": "$0.20 per GiB per month",
      "page_setting": "Documentation worked example; multiplied by zero"
    },
    {
      "id": "cap_short",
      "name": "Candidate workflow cap",
      "unit": "seconds",
      "basis": "DESIGN",
      "value": 60
    },
    {
      "id": "cap_middle",
      "name": "Candidate workflow cap",
      "unit": "seconds",
      "basis": "DESIGN",
      "value": 120
    },
    {
      "id": "cap_long",
      "name": "Largest workflow cap",
      "unit": "seconds",
      "basis": "DESIGN",
      "value": 300
    },
    {
      "id": "effect_margin",
      "name": "Meaningful absolute difference",
      "unit": "DockQ",
      "basis": "DESIGN",
      "value": 0.01
    },
    {
      "id": "noise_floor",
      "name": "Noise floor",
      "unit": "DockQ",
      "basis": "DESIGN",
      "value": 0.000001
    },
    {
      "id": "noise_mult",
      "name": "Standard range multiplier",
      "unit": "ratio",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "scorer_mult",
      "name": "Fixture discrepancy multiplier",
      "unit": "ratio",
      "basis": "DESIGN",
      "value": 10
    },
    {
      "id": "noise_ceiling",
      "name": "Noise envelope ceiling",
      "unit": "DockQ",
      "basis": "DESIGN",
      "value": 0.005
    },
    {
      "id": "scorer_tol",
      "name": "Independent scorer ceiling",
      "unit": "DockQ",
      "basis": "DESIGN",
      "value": 0.00001
    },
    {
      "id": "agreement_tol",
      "name": "CPU/GPU endpoint tolerance",
      "unit": "DockQ",
      "basis": "DESIGN",
      "value": 0.0001
    },
    {
      "id": "score_ceiling",
      "name": "Docking score tolerance ceiling",
      "unit": "score units",
      "basis": "DESIGN",
      "value": 0.2
    },
    {
      "id": "anchor_tol",
      "name": "Rounded fixture tolerance",
      "unit": "DockQ",
      "basis": "DESIGN",
      "value": 0.0005
    },
    {
      "id": "anchor_value",
      "name": "Documented first-interface example score",
      "unit": "DockQ",
      "basis": "CITED",
      "value": 0.994,
      "source_id": "dockq",
      "quote": "DockQ: 0.994",
      "page_setting": "1A2K example, not selected apo cases"
    },
    {
      "id": "telemetry_s",
      "name": "GPU activity sampling interval",
      "unit": "seconds",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "seconds_per_h",
      "name": "Unit conversion",
      "unit": "seconds/hour",
      "basis": "DESIGN",
      "value": 3600
    },
    {
      "id": "human_h",
      "name": "Unpaid human allowance",
      "unit": "person-hours",
      "basis": "DESIGN",
      "value": 12
    },
    {
      "id": "timing_cases",
      "name": "Unscored calibration case count",
      "unit": "cases",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "projection_factor",
      "name": "Conservative measured timing multiplier",
      "unit": "ratio",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "quality_jobs",
      "name": "Paired GPU search jobs excluding agreement",
      "unit": "jobs",
      "basis": "DERIVED",
      "expr": "cases * paired_repeats * gpu_arms"
    },
    {
      "id": "agreement_jobs",
      "name": "Standard agreement search jobs",
      "unit": "jobs",
      "basis": "DERIVED",
      "expr": "cases * agreement_repeats * agreement_arms"
    },
    {
      "id": "pose_scores",
      "name": "Primary pose scoring including rescoring, excluding independent fixtures",
      "unit": "evaluations",
      "basis": "DERIVED",
      "expr": "(quality_jobs + agreement_jobs) * retained * rescore_repeats"
    },
    {
      "id": "compute_usd",
      "name": "Maximum planned pre-tax allocation charge",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "(calibration_h + science_h + export_h) * h100_price * gpus"
    },
    {
      "id": "admissible_caps",
      "name": "Conservative caps admitting both complete GPU workflows on every case",
      "unit": "caps",
      "basis": "GUESS",
      "value": 1,
      "rests_on": "User exploratory docking totals suggest feasibility but omit reconstruction, scoring, setup and retrieval. Unverified count is a gate, not a promise of completed comparisons.",
      "measured_by": "calibrate"
    },
    {
      "id": "agreement_pass",
      "name": "All-case standard agreement and scorer pass",
      "unit": "boolean",
      "basis": "GUESS",
      "value": 1,
      "rests_on": "User reports earlier matching transforms and DockQ without sealed tolerance; prospective agreement can fail.",
      "measured_by": "agreement"
    },
    {
      "id": "h100_price",
      "name": "Single H100 PCIe per-GPU rate",
      "unit": "USD/GPU-hour",
      "basis": "CITED",
      "value": 3.29,
      "source_id": "pricing",
      "quote": "$3.29",
      "page_setting": "One-GPU H100 PCIe on-demand instance"
    },
    {
      "id": "reserve_usd",
      "name": "Tax and billing reserve",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "credit_stop - compute_usd"
    },
    {
      "id": "independent_fixtures",
      "name": "Independent example, native-self and rigid-transform fixtures",
      "unit": "fixtures",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "billing_minutes",
      "name": "Billed minutes per hour",
      "unit": "minutes/hour",
      "basis": "DESIGN",
      "value": 60
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
        "id": "calibration_box",
        "phase": "calibrate",
        "what": "All-inclusive calibration time box: setup, retrieval, build, idle, timings and cleanup; USD6.58 before tax.",
        "kind": "work",
        "rate": "h100",
        "hours": "calibration_h"
      },
      {
        "id": "science_box",
        "phase": "compare",
        "what": "Shared agreement and paired-quality time box, including CPU evaluation, setup and idle; USD9.87 before tax.",
        "kind": "work",
        "rate": "h100",
        "hours": "science_h"
      },
      {
        "id": "export_box",
        "phase": "export",
        "what": "Export and termination allowance across rentals; USD3.29 before tax.",
        "kind": "allotment",
        "rate": "h100",
        "hours": "export_h"
      },
      {
        "id": "persistent_storage",
        "phase": "export",
        "what": "No persistent filesystem provisioned. Use instance disk and export artifacts. Example filesystem rate is not guaranteed tariff [filesystem].",
        "kind": "storage",
        "usd": "persistent_gib * fs_usd_gib_month"
      },
      {
        "id": "billing_reserve",
        "phase": "export",
        "what": "USD5.26 reserved for applicable tax and billing uncertainty; cannot fund extra experiments. Recheck actual billing projection before allocation.",
        "kind": "allotment",
        "usd": "reserve_usd"
      }
    ],
    "yields": [
      "cases",
      "paired_repeats",
      "retained",
      "quality_jobs",
      "pose_scores"
    ],
    "spend_cap_usd": 25,
    "total_stated": 25
  },
  "full_scale": [],
  "outside_budget": [
    {
      "what": "DESIGN: unpaid implementation, review and interpretation",
      "qty": 12,
      "unit": "person-hours"
    },
    {
      "what": "DESIGN: new external services or third-party compute purchases",
      "qty": 0,
      "unit": "USD"
    },
    {
      "what": "DESIGN: existing local workstation and artifact retention; no new purchase",
      "qty": 0,
      "unit": "USD"
    }
  ],
  "restructuring": {
    "sequential_part": "Each answer waits for search, pose reconstruction, then scoring: 3 dependent stages.",
    "method": "none"
  },
  "scope_gap": [
    "Private files were not read under this prompt's restriction. Future verification needed: BRIEF_run1.md:48-158 for case preparation/reference pins and run2/agent/harness/run_command.sh:8-43 for exact commands. No private record is presented as public citation.",
    "User-described executable gap: number-band measure carries scalar uncertainty and phases, not arms, independent anchor, two quality outcomes or decision/noise rules. Existing baseline/method equivalence and scalar curve cannot execute comparison. Missing controller/stage args must include manifest, arm, cap, repeat, scorer, ledger and seal. Compilation is not scientific equivalence.",
    "Available USD1000 is not spending target. User full-card ceiling USD100 applies; chosen stop USD25 is stricter. No CPU-dense, reranker, extra retained poses, broader dataset or biological efficacy test.",
    "No producer GPU measurement. Private historical allocation/transport observations are neither public sources nor producer MEASURED pilots. No guessed runtime is needed to price allocation time boxes.",
    "Independent fixtures may not bound selected-case numerical behavior; fresh agreement/noise gates can invalidate experiment. Single-GPU acceleration is not new dependency-chain restructuring."
  ],
  "novelty": {
    "closest_prior": "Published MEGADOCK benchmark timed parallel execution across 30976 docking jobs; rotation maximum is unspecified here, and it does not settle four-case DockQ tradeoffs. [prior]",
    "closest_source_id": "prior",
    "prior_max_level": null,
    "left_open": "Whether 54000 versus 3600 rotations, fixed 50 outputs, changes best50 and rank1 differently within calibrated budgets on these four apo cases.",
    "decides": "no",
    "searched": true
  },
  "limits": "Four selected apo cases only; exposed prior quality; prospective replication, not holdout. No biological efficacy, population generalization, or ranking improvement inferred from best50 gains.",
  "test_summary": "Validate independent scorer and CPU/GPU standard agreement first. Calibrate complete-workflow budgets, seal noise rules, then compare three paired 3600/54000-rotation repeats on four cases, fixed 50 outputs; report rank1 and best50 separately.",
  "sources": [
    {
      "id": "pricing",
      "url": "https://lambda.ai/pricing",
      "quote": "NVIDIA H100 PCIe | 80 GB | 26 | 225 GiB | 1 TiB SSD | $3.29",
      "supports": "Fetched single-GPU instance price row; supplied starting sheet identifies GPU count as one. Price per GPU-hour, before applicable tax."
    },
    {
      "id": "usage",
      "url": "https://www.bi.cs.titech.ac.jp/megadock/usage.html",
      "quote": "default to 3600 angles",
      "supports": "Official standard/dense rotation settings, scoring/output flags and decoy generation; pinned revision itself still requires verification."
    },
    {
      "id": "pinder",
      "url": "https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/README.md",
      "quote": "The evaluation harness can be used either through methods in pinder.eval or as a CLI script:",
      "supports": "Pinned PINDER release documentation and evaluation implementation; case selection remains user design."
    },
    {
      "id": "dockq",
      "url": "https://github.com/wallnerlab/DockQ",
      "quote": "DockQ: 0.994",
      "supports": "Documented first interface of 1A2K example provides independent scorer anchor; pin version, bytes and mapping before execution."
    },
    {
      "id": "prior",
      "url": "https://pubmed.ncbi.nlm.nih.gov/25100686/",
      "quote": "Calculation time and acceleration by parallelization among nodes on 30 976 docking jobs",
      "supports": "Public figure caption of MEGADOCK 4.0 performance study; jobs are not rotations per search."
    },
    {
      "id": "billing",
      "url": "https://docs.lambda.ai/public-cloud/billing/",
      "quote": "Instances are billed for as long as they're running, regardless if they're actively being used.",
      "supports": "Allocation includes setup, CPU work, transport and idle."
    },
    {
      "id": "filesystem",
      "url": "https://test-docs.lambda.ai/public-cloud/filesystems/",
      "quote": "For example, at a rate of $0.20 per GiB per month:",
      "supports": "Illustrative filesystem rate only, not guaranteed current tariff; no persistent filesystem in plan."
    }
  ],
  "files_read": [
    "/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/seed/idea/360caa42/producer.md"
  ]
}
```
