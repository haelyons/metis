# Agreement validation plan

Prospective plan only. No docking or cloud allocation executed. Public sources fetched; private historical files not read.

```json
{
  "option_title": "Agreement before interpreting acceleration or denser search",
  "question": "Do CPU and GPU docking agree across 4 fixed cases and 50 ranked poses after independent numerical calibration?",
  "hypothesis": "Independent repeats and error analysis can justify CPU/GPU agreement before acceleration or denser search receives scientific interpretation.",
  "compute_axis": {
    "quantity": "Independent same-backend calibration repeats per case and backend; validation effort, not search density",
    "unit": "repeats",
    "levels": [
      2,
      4
    ]
  },
  "held_fixed": [
    "DESIGN inherited from user: exactly 4 PINDER 2024-02 apo cases: 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo.",
    "MEGADOCK source 9575280c875732553266e26adc607dd892b02616; PINDER source ebeb28a2f8411363cef722b7d293c978f7442672. Freeze prepared receptor, ligand and reference byte hashes; source pins alone do not pin data.",
    "DESIGN inherited settings: -N50 -t1 -v1.2 -e1 -d1 -a-45 -b1 -f3 -r3600; OMP_NUM_THREADS=26. Same per-case grid construction and rotation table, compiler optimization, CPU affinity, allocation and dependency identities across repeat levels. Command meanings: [commands](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/doc/README.md).",
    "Build separate CPU and GPU binaries from identical source; record compiler, FFTW, cuFFT, CUDA, driver, architecture flags and binary hashes. Single-node build routes: [build guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/doc/BUILD.md).",
    "No dense execution, native scoring or quality-guided tuning in screen or calibration. Native references remain evaluation-only. No concurrent docking jobs; no bundled-throughput claim."
  ],
  "predictions": {
    "if_lever": "At 4 repeats, independent bounds support agreement for all 4 cases and 50 ranks; 2 repeats leave calibration unresolved.",
    "if_not": "At 4 repeats, agreement remains unresolved or fails, or 2 repeats already suffice; extra calibration buys no changed agreement decision.",
    "decision_rule": "Validation-only rule: compare cumulative levels 2 and 4. A level qualifies only with 0 structural failures and 0 score violations across all cases and ranks under independently justified, sealed per-case bounds. Never use fresh CPU/GPU deltas to choose bounds. If 2 qualifies, retain its sealed bounds and use remaining repeats as validation; if only 4 qualifies, record added calibration value. Neither outcome establishes acceleration or density benefit. Missing error justification means unresolved, not agreement.",
    "noise_rule": "Start with 2 independent process launches per backend per case; extend cumulatively to 4. Record every run and all pairwise same-backend discrepancies. Exact-repeat diagnostic requires byte equality of stable output/PDB manifests, excluding volatile logs. Scientific acceptance separately requires identical output grid metadata, ranked transform correspondence and score intervals justified by floating-point analysis plus independent reference calculations and observed same-backend variation. Derive score and coordinate tolerances from audited arithmetic and serialization precision; seal numeric values before fresh comparison. Do not infer cross-backend tolerance from same-backend determinism, FAQ anecdotes, old 0.14 maximum, ratio bands, or epsilon added to observed differences.",
    "expected": "unsure",
    "expected_why": "User-supplied exploratory observations lack sealed tolerances; published precision guidance does not establish bounds for these inputs and binaries [faq]."
  },
  "compute_tested": "no",
  "compute_tested_why": "Repeat levels vary validation effort; neither parallel compute, denser sampling nor throughput is experimentally varied. Necessary prerequisite card, without compute-lever claim.",
  "scored_against": "CPU standard is operational baseline. Compare every fresh GPU row with its CPU rank, score interval and transform, plus grid metadata and reconstructed atom correspondence. Independent numerical reference and error analysis determine validity, not CPU output alone. Native rank1/best50 DockQ is a later, separately gated check.",
  "arms": [
    {
      "id": "screen_subset",
      "what": "New CPU-standard-only unit harness: 4 cases, same inherited commands and 26 threads; compare stable outputs against exported run2 reference."
    },
    {
      "id": "screen_control",
      "what": "CPU-only full/control harness: same 4 CPU units through original preparation/order/environment route, with dense, GPU docking and native scoring disabled; isolates subsetting from drift."
    },
    {
      "id": "cpu_standard",
      "what": "CPU standard: cumulative 2 then 4 independent calibration repeats per case, followed by 1 fresh sealed comparison run."
    },
    {
      "id": "gpu_standard",
      "what": "GPU standard: same repeat schedule and settings, followed by 1 fresh sealed comparison run; all 50 ranked rows retained."
    }
  ],
  "baseline": {
    "what": "CPU standard, 3600 rotations, 50 retained predictions, 26 threads; baseline reference exported from user-supplied run2, then fresh CPU execution.",
    "value": "No independent numerical baseline established yet; historical reference is execution diagnostic only."
  },
  "anchor": {
    "absent_reason": "No independently checked anchor for these exact inputs, source pin and arithmetic is available in supplied prompt. Published FAQ reports small CPU/GPU differences but gives no case-specific error proof [faq]. Build independent high-precision grid-correlation and pose-reconstruction checks during calibration; require audited error bounds before issuing agreement verdict. If these cannot be established within calibration cap, stop unresolved. Reusing MEGADOCK decoygen alone is not independent validation."
  },
  "checks": [
    "Build plan, not execute docking now. No new box workload or measured pilot claimed. Read no private historical files; their contents and cited sections remain unverified.",
    "Implement controller with explicit stage arguments: export, cpu_subset, cpu_control, repeat_calibration, seal, fresh_compare. Reject -D and native-scoring executable paths in CPU screen/calibration; fail closed on missing case, hash, output or nonzero exit.",
    "Author new units.json and harness_from metadata; record per-unit command argv, working directory, environment, input/binary/dependency hashes, grid identity and output paths. Export stable per-unit docking-output and final PDB SHA-256 manifest; exclude logs, timestamps and volatile headers by an explicit versioned rule. Preserve raw files. Positive byte equality supports repeat/subset assumption only.",
    "If subset differs but control matches exported reference, investigate subsetting. If both differ, investigate baseline drift. If control cannot be recovered, attribution is unresolved. None permits relaxed acceptance.",
    "Write compare_rows.py to require 50 finite score/transform rows, rank identities, grid dimensions/spacing/origin, rotation-table hashes, translation indices, atom/residue identities, and reconstructed poses. Test parser and matcher with synthetic dropped-row, reordered-row, altered-grid and altered-coordinate fixtures before GPU spend.",
    "Write independent reference.py without calling MEGADOCK scoring or decoygen: check rigid transforms and directly accumulate high-precision grid correlations at every retained transform; instrument pre-FFT grids and near-cutoff candidates. Audit voxelization and FFT error propagation. Retained-point agreement alone cannot certify global search; absent defensible cutoff/error analysis leaves numerical verdict unresolved [correlation].",
    "Route gaps to resolve before execution: user identifies run2/agent/harness/run_command.sh:8-43 and b01_materials/BRIEF_run1.md:48-158 as command/input sources; neither was read under current read restriction. User states run2 lacks units. Need new units, harness_from, CPU-only full/control route, stable export, comparison stage/controller args and independent precision analysis; do not claim existing route implements them.",
    "Historical negatives, supplied by user without public citation: run2 docking-only totals CPU/GPU/dense 40.07/6.85/69.38 seconds; matched transforms/DockQ; per-case maximum score deltas 0.04/0.03/0.04/0.14 without acceptance tolerance. Dense best50 improved four observations; rank1 worsened in two, including 1nr5. Preserve as exploratory observations, never new producer measurements or tolerance anchors.",
    "Historical allocation/transport, supplied by user without public citation: setup145s; unscored bundle median131.9565s; receipts145/1571/1402/1424/2832/3448s. Do not use them as fresh timing estimates. Measure setup, retrieval, idle, compilation, docking, export and termination separately.",
    "Later gate, outside this card: seal numerical acceptance, timing repetitions, common-budget feasibility and noise rules before dense recovery evaluation. Report rank1 and best50 DockQ separately per case. New executions replicate already exposed cases; no unseen holdout claim."
  ],
  "phases": [
    {
      "id": "author",
      "what": "Offline author controller, units schema, CPU-only full/control route, manifest exporter, row comparator, independent numerical reference and synthetic fixtures. Obtain authorized export of prepared data and stable run2 reference. Pin everything before allocation.",
      "stop_rule": "Do not allocate if inputs, reference export, stage args, termination controller or independent-check implementation is missing."
    },
    {
      "id": "screen",
      "what": "First time box includes new export, transport, setup and CPU subset/control runs. Measure fresh workflow and output stability. All allocation overhead belongs here; terminate instance at timer.",
      "stop_rule": "Stop after screen_h wall hours or screen_cost_cap USD, whichever first. No dense or native scoring. Missing artifacts or unexplained mismatch blocks later spend.",
      "gate": {
        "on": "screen_pass",
        "op": ">=",
        "value": 1,
        "else": "Stop; preserve mismatches. Fix harness offline; no tolerance relaxation or automatic larger allocation."
      }
    },
    {
      "id": "calibrate",
      "what": "New all-inclusive calibration allocation: independently measure CPU/GPU same-backend repeats at levels 2 and 4, numerical reference residuals, serialization precision and full workflow time. Seal justified per-case tolerance table before fresh comparison.",
      "stop_rule": "Stop after calibration_h wall hours or calibration_cost_cap USD. Never execute full experiment through calibration route. Missing independent bounds blocks verdict.",
      "gate": {
        "on": "calibration_pass",
        "op": ">=",
        "value": 1,
        "else": "Stop unresolved; report missing numerical anchor, repeatability or runtime evidence. No fresh comparison spend."
      }
    },
    {
      "id": "fresh",
      "what": "Seal acceptance document and hashes; execute 1 fresh CPU/GPU pair per case, all 50 ranks. Record full workflow wall time, sampled GPU activity and actual billed allocation; compare under sealed bounds.",
      "stop_rule": "Stop at comparison_h wall hours, spend cap, or any scientific failure. Soft stop at soft_h cumulative hours: checkpoint and terminate unless signed calibration measurements already justify remaining schedule. Hard stop at hard_h cumulative hours."
    },
    {
      "id": "diagnose",
      "what": "Optional diagnostic allocation only for explaining already recorded mismatches or unavailable outputs. Preserve original failed result and sealed bounds; no dense search or quality tuning.",
      "stop_rule": "Stop at diagnostic_h wall hours or hard_h cumulative hours. Changed implementation requires a new prospective protocol; cannot overwrite original verdict."
    }
  ],
  "numbers": [
    {
      "id": "budget_usd",
      "name": "User available GPU credit ceiling",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 1000
    },
    {
      "id": "card_cap",
      "name": "Card ceiling imposed by user",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 100
    },
    {
      "id": "cases",
      "name": "Exact user-selected cases",
      "unit": "cases",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "retained",
      "name": "Retained ranked predictions per docking",
      "unit": "poses",
      "basis": "DESIGN",
      "value": 50
    },
    {
      "id": "standard_rotations",
      "name": "Fixed standard rotational search",
      "unit": "rotations",
      "basis": "DESIGN",
      "value": 3600
    },
    {
      "id": "threads",
      "name": "Fixed inherited OpenMP threads",
      "unit": "threads",
      "basis": "DESIGN",
      "value": 26
    },
    {
      "id": "per_rotation",
      "name": "Predictions per rotation",
      "unit": "poses",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "voxel_pitch",
      "name": "Fixed voxel pitch",
      "unit": "angstrom",
      "basis": "DESIGN",
      "value": 1.2
    },
    {
      "id": "electrostatics",
      "name": "Fixed electrostatics weight",
      "unit": "ratio",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "hydrophobic",
      "name": "Fixed hydrophobic weight",
      "unit": "ratio",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "receptor_penalty",
      "name": "Fixed receptor core penalty",
      "unit": "score coefficient",
      "basis": "DESIGN",
      "value": -45
    },
    {
      "id": "ligand_penalty",
      "name": "Fixed ligand core penalty",
      "unit": "score coefficient",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "score_function",
      "name": "Fixed scoring function selection",
      "unit": "selector",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "backends",
      "name": "CPU and GPU implementations",
      "unit": "backends",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "low_repeats",
      "name": "Initial cumulative calibration level",
      "unit": "repeats/backend/case",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "high_repeats",
      "name": "Maximum cumulative calibration level",
      "unit": "repeats/backend/case",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "fresh_repeats",
      "name": "Held-back fresh comparison level",
      "unit": "runs/backend/case",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "screen_routes",
      "name": "Subset and CPU-only full/control routes",
      "unit": "routes",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "screen_runs",
      "name": "Planned screen docking runs",
      "unit": "runs",
      "basis": "DERIVED",
      "expr": "cases * screen_routes"
    },
    {
      "id": "calibration_runs",
      "name": "Maximum calibration docking runs, cumulative",
      "unit": "runs",
      "basis": "DERIVED",
      "expr": "cases * backends * high_repeats"
    },
    {
      "id": "fresh_runs",
      "name": "Fresh comparison docking runs",
      "unit": "runs",
      "basis": "DERIVED",
      "expr": "cases * backends * fresh_repeats"
    },
    {
      "id": "planned_runs",
      "name": "Core planned docking runs if gates pass",
      "unit": "runs",
      "basis": "DERIVED",
      "expr": "screen_runs + calibration_runs + fresh_runs"
    },
    {
      "id": "fresh_rows",
      "name": "Fresh comparison paired ranked rows",
      "unit": "row pairs",
      "basis": "DERIVED",
      "expr": "cases * retained"
    },
    {
      "id": "zero_failures",
      "name": "Allowed structural or score-bound violations",
      "unit": "violations",
      "basis": "DESIGN",
      "value": 0
    },
    {
      "id": "screen_pass",
      "name": "Measured screen pass indicator; placeholder is required success, not observation",
      "unit": "boolean",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "calibration_pass",
      "name": "Measured calibration pass indicator; placeholder is required success, not observation",
      "unit": "boolean",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "screen_h",
      "name": "All-inclusive first allocation timer",
      "unit": "wall hours",
      "basis": "DESIGN",
      "value": 1.5
    },
    {
      "id": "calibration_h",
      "name": "All-inclusive numerical calibration timer",
      "unit": "wall hours",
      "basis": "DESIGN",
      "value": 2.5
    },
    {
      "id": "comparison_h",
      "name": "All-inclusive fresh comparison timer",
      "unit": "wall hours",
      "basis": "DESIGN",
      "value": 5
    },
    {
      "id": "diagnostic_h",
      "name": "Optional all-inclusive diagnostic timer",
      "unit": "wall hours",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "soft_h",
      "name": "Cumulative soft stop",
      "unit": "wall hours",
      "basis": "DESIGN",
      "value": 6
    },
    {
      "id": "hard_h",
      "name": "Cumulative hard stop including diagnostics",
      "unit": "wall hours",
      "basis": "DESIGN",
      "value": 12
    },
    {
      "id": "screen_reserve",
      "name": "First-allocation billing/tax contingency",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "calibration_reserve",
      "name": "Calibration billing/tax contingency",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "later_reserve",
      "name": "Later billing/tax contingency",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 6
    },
    {
      "id": "screen_cost_cap",
      "name": "First screen all-in cost limit",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 7
    },
    {
      "id": "calibration_cost_cap",
      "name": "Later calibration all-in cost limit",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 11
    },
    {
      "id": "persistent_gib",
      "name": "Paid persistent filesystem provisioned",
      "unit": "GiB",
      "basis": "DESIGN",
      "value": 0
    },
    {
      "id": "human_h",
      "name": "Unpaid authoring and numerical review time box",
      "unit": "person hours",
      "basis": "DESIGN",
      "value": 16
    },
    {
      "id": "price_h",
      "name": "H100 PCIe per-GPU on-demand price",
      "unit": "USD/GPU/hour",
      "basis": "CITED",
      "value": 3.29,
      "source_id": "price",
      "quote": "NVIDIA H100 PCIe | 80 GB | 26 | 225 GiB | 1 TiB SSD | $3.29",
      "page_setting": "Single NVIDIA H100 PCIe instance, same row as supplied price sheet; https://lambda.ai/pricing"
    },
    {
      "id": "gpu_count",
      "name": "GPUs in selected whole instance",
      "unit": "GPUs",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "screen_usd",
      "name": "All-in initial screen reservation",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "screen_h * price_h * gpu_count + screen_reserve"
    },
    {
      "id": "calibration_usd",
      "name": "All-in calibration reservation",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "calibration_h * price_h * gpu_count + calibration_reserve"
    },
    {
      "id": "total_usd",
      "name": "Reservation including optional diagnostics and contingencies",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "(screen_h + calibration_h + comparison_h + diagnostic_h) * price_h * gpu_count + screen_reserve + calibration_reserve + later_reserve"
    },
    {
      "id": "core_usd",
      "name": "Core reservation excluding optional diagnostics",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "total_usd - diagnostic_h * price_h * gpu_count"
    },
    {
      "id": "unused_usd",
      "name": "Available credit not committed",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "budget_usd - total_usd"
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
        "id": "screen_box",
        "phase": "screen",
        "what": "CPU-only screen on whole H100 instance; export, transport, build, retrieval, idle and shutdown included",
        "kind": "work",
        "rate": "h100",
        "hours": "screen_h"
      },
      {
        "id": "screen_contingency",
        "phase": "screen",
        "what": "Billing/tax contingency; terminate before all-in screen cap",
        "kind": "allotment",
        "usd": "screen_reserve"
      },
      {
        "id": "calibration_box",
        "phase": "calibrate",
        "what": "Numerical calibration; all allocation overhead included",
        "kind": "work",
        "rate": "h100",
        "hours": "calibration_h"
      },
      {
        "id": "calibration_contingency",
        "phase": "calibrate",
        "what": "Billing/tax contingency; terminate before all-in calibration cap",
        "kind": "allotment",
        "usd": "calibration_reserve"
      },
      {
        "id": "comparison_box",
        "phase": "fresh",
        "what": "Fresh standard CPU/GPU agreement comparison, including setup, transfer, idle and export",
        "kind": "work",
        "rate": "h100",
        "hours": "comparison_h"
      },
      {
        "id": "diagnostic_box",
        "phase": "diagnose",
        "what": "Optional mismatch diagnosis; no dense search or native scoring",
        "kind": "work",
        "rate": "h100",
        "hours": "diagnostic_h",
        "optional": true,
        "condition": "Original verdict preserved; explicit diagnostic question and cumulative timers permit work."
      },
      {
        "id": "later_contingency",
        "phase": "fresh",
        "what": "Remaining billing/tax contingency; unused money stays unspent",
        "kind": "allotment",
        "usd": "later_reserve"
      }
    ],
    "yields": [
      "cases",
      "screen_runs",
      "calibration_runs",
      "fresh_runs",
      "fresh_rows"
    ],
    "spend_cap_usd": 100,
    "total_stated": 49.48
  },
  "full_scale": [],
  "outside_budget": [
    {
      "what": "Authoring, numerical error review and report time; DESIGN time box, no purchased labor",
      "qty": 16,
      "unit": "person hours"
    },
    {
      "what": "Local writing/web checks; no paid external service or GPU experiment authorized",
      "qty": 0,
      "unit": "USD"
    }
  ],
  "restructuring": {
    "sequential_part": "4 gates: establish inputs, test repeatability, seal error bounds, compare fresh CPU/GPU runs.",
    "method": "none"
  },
  "scope_gap": [
    "Validation card does not answer whether GPU acceleration makes dense recovery affordable; no dense search, common-budget quality comparison or bundled-throughput experiment.",
    "Exactly four exposed cases; no biological efficacy or population inference. Passing byte-repeat diagnostic does not imply numerical equivalence.",
    "Time boxes buy bounded effort, not guaranteed completed runs. No fresh runtime, export-time or repeatability estimates; progress measured in screen and calibration before dependent spend.",
    "At most USD49.48 reserved here, including optional diagnostics; USD950.52 of USD1000 remains uncommitted. Core without optional diagnostics costs USD39.61. First screen USD6.935; later calibration USD10.225. All hours are whole-instance wall hours, one GPU, at USD3.29/GPU/hour [price].",
    "Use instance-local storage and export artifacts before termination; provision zero paid persistent filesystem GiB. No filesystem-rate claim: supplied USD0.20/GiB-month is explicitly an example, not verified tariff.",
    "Public sources cannot authenticate private histories. Current read restriction prevents inspecting named private command/input sections; concrete gap list is mandatory pre-allocation work."
  ],
  "novelty": {
    "closest_prior": "MEGADOCK authors report CPU/GPU precision differences without repeat counts; published parallel study measured docking scalability, not this calibration decision [faq] [paper].",
    "closest_source_id": "faq",
    "prior_max_level": null,
    "left_open": "Whether 2 or 4 independent repeats plus audited error bounds support all 50 ranked poses across these 4 cases remains open.",
    "decides": "no",
    "searched": true
  },
  "limits": "No density, speedup, biological efficacy or population claim. Four previously exposed cases only; absent independent numerical justification leaves agreement unresolved.",
  "test_summary": "Build CPU-only subset/control harness, then calibrate 2 and 4 repeats per backend across 4 cases. Seal independent error bounds; compare 1 fresh CPU/GPU pair per case using all 50 ranks. Stop unresolved if bounds fail.",
  "sources": [
    {
      "id": "price",
      "url": "https://lambda.ai/pricing",
      "quote": "$3.29",
      "supports": "USD3.29 per GPU-hour for single H100 PCIe configuration; exact row reproduced in price_h. GPU count chosen from user-provided sheet; https://lambda.ai/pricing also lists applicable taxes separately."
    },
    {
      "id": "commands",
      "url": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/doc/README.md",
      "quote": "MEGADOCK parallelizes rotation calculations by using OpenMP.",
      "supports": "Pinned command guide fetched directly; single-node binaries, parameter meanings, thread environment and decoygen usage. Fixed numeric settings are user-mandated DESIGN choices."
    },
    {
      "id": "build",
      "url": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/9575280c875732553266e26adc607dd892b02616/doc/BUILD.md",
      "quote": "For GPU use, `SM_VERSIONS` can specity the target NVIDIA GPU architectures of the generated binary.",
      "supports": "Pinned CPU/GPU build paths and architecture identity requirement; compatibility must be checked before scientific comparison."
    },
    {
      "id": "faq",
      "url": "https://www.bi.cs.titech.ac.jp/megadock/faq.html",
      "quote": "Answer: Because of precision of GPUs, the results of docking scores are slightly different by CPU version and GPU version.",
      "supports": "Precision differences motivate separate scientific tolerance; FAQ does not establish acceptance for these exact cases."
    },
    {
      "id": "correlation",
      "url": "https://www.bi.cs.titech.ac.jp/megadock/perform.html",
      "quote": "The total scoring function of MEGADOCK is represented by these functions as follows:",
      "supports": "Published correlation formulation motivates independent direct-correlation check; no numerical bound borrowed from this page."
    },
    {
      "id": "paper",
      "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4221127/",
      "quote": "Notably, a high scalability (98%) was obtained with the largest number of nodes (420 nodes).",
      "supports": "Search returned open full-text extraction of published parallel study. Different compute axis; neither repeat-count calibration nor case-specific agreement result."
    },
    {
      "id": "pinder",
      "url": "https://raw.githubusercontent.com/pinder-org/pinder/ebeb28a2f8411363cef722b7d293c978f7442672/README.md",
      "quote": "PINDER: The Protein INteraction Dataset and Evaluation Resource",
      "supports": "Pinned PINDER repository identity only; exact four-case preparation and reference hashes must come from authorized export, not inferred from README."
    }
  ],
  "files_read": [
    "/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/seed/idea/340ca71c/producer.md"
  ]
}
```
