{
  "option_title": "CPU host scheduling as workflow affordability calibration",
  "question": "Can running 2 or 4 independent CPU docking jobs together cut four-case workflow cost while preserving every retained pose?",
  "hypothesis": "Independent jobs may fill idle host capacity, making unchanged four-case CPU docking at least 1.05 times faster with identical outputs.",
  "compute_axis": {
    "quantity": "Independent fixed-input CPU docking jobs allowed concurrently on one unchanged host",
    "unit": "concurrent jobs",
    "levels": [
      1,
      2,
      4
    ]
  },
  "held_fixed": [
    "DESIGN from supplied task: exactly 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo; 1nr5__A1_P07547--1nr5__A2_P07547:apo. PINDER release 2024-02; prepared bytes and evaluation references require manifest verification before launch.",
    "DESIGN from supplied task: MEGADOCK source 9575280c875732553266e26adc607dd892b02616; PINDER source ebeb28a2f8411363cef722b7d293c978f7442672. Freeze binary, compiler, dependencies, image, environment, CPU affinity policy and input SHA-256 hashes.",
    "DESIGN: CPU executable only; OMP_NUM_THREADS=26 per job, unchanged across widths. OpenMP control documented publicly [usage]. One H100 PCIe instance with 26 advertised vCPUs [lambda]; record actual CPU topology and allowed CPU set before comparison.",
    "DESIGN: -N50 -t1 -v1.2 -e1 -d1 -a-45 -b1 -f3 -r3600. No dense -D arm, rescoring, additional samples, changed ranking or thread reduction.",
    "DESIGN: preserve canonical relative paths and every selected final pose; each invocation gets an isolated replica of the same path tree. Keep output manifest and immutable input tree; exclude only explicitly listed volatile logs from equality.",
    "DESIGN: fixed four-case order, output generation, validation and timing boundaries across all arms. Native references stay outside scheduling and prediction generation."
  ],
  "predictions": {
    "if_lever": "At width 2 or 4, both paired four-case workflow speedups reach 1.05 with exact docking and pose equality.",
    "if_not": "Neither width achieves 1.05 in both paired four-case workflow speedups, or output equality fails.",
    "decision_rule": "First require exact equality. Run a,b,c2,c4,c4,c2,b,a. For each concurrent run, divide the temporally nearest baseline-own a workflow time by its workflow time. Advance a width only when both ratios >=1.05; if both qualify choose larger minimum ratio, exact tie favors width 2. A mismatch stops subsequent arms. Failure to finish yields unavailable, never a pass.",
    "noise_rule": "Symmetric order gives 2 repeats per arm and nearby baseline-own anchors. Publish both ratios, raw times and baseline drift; mean alone supplies no confidence claim. If neither width passes or baseline timing is unstable, next separate calibration repeats baseline-only variability control; preserve 1.05 criterion. Two repeats cannot establish population confidence.",
    "expected": "unsure",
    "expected_why": "Host saturation and launch overhead could erase concurrency gains; supplied historical observations are private exploratory context, not transferable measurements."
  },
  "compute_tested": "partly",
  "compute_tested_why": "Vary host job concurrency, not GPU count or scientific search size. GPU remains unused while its attached CPU host is billed. This is an affordability calibration, not evidence about GPU acceleration or dense-search recovery.",
  "scored_against": "Compare every input, docking output, ranked transform/score row and all 50 generated pose PDBs per case against supplied frozen reference manifests, then against baseline-own execution. Require zero byte differences outside a presealed volatile-log exclusion list. Compare complete four-case workflow wall time against nearby baseline-own serial execution.",
  "arms": [
    {
      "id": "a",
      "what": "Baseline-own existing four-case serial invocation, including its unchanged setup, docking, pose generation and output validation."
    },
    {
      "id": "b",
      "what": "Four independent unit invocations run serially; same science and 26 threads/job. Isolates process and wrapper overhead from scheduling."
    },
    {
      "id": "c2",
      "what": "Same four unit invocations with maximum 2 active jobs; 26 threads each."
    },
    {
      "id": "c4",
      "what": "Same four unit invocations with maximum 4 active jobs; 26 threads each."
    }
  ],
  "baseline": {
    "what": "Fresh baseline-own four-case serial workflow on the same instance; also time separate serial units. No historical speed is an acceptance target.",
    "value": "Prospectively measured workflow seconds; no producer pilot."
  },
  "anchor": {
    "what": "Match frozen serial docking outputs and all 50 poses per case, then require identical outputs from each scheduling arm.",
    "tolerance": "Zero docking-output and pose-PDB byte differences; zero input or shared immutable-file changes. Exclude only presealed volatile logs. No public numerical anchor or independent implementation validates these exact private prepared inputs."
  },
  "checks": [
    "PLAN ONLY: no instance launch, compilation or docking execution during card preparation; no producer MEASURED results claimed.",
    "Before cloud spend, build a CPU-only calibration harness design: units.json with four exact commands and canonical output manifests; runner with bounded concurrency; collector with process-tree accounting; comparator with explicit exclusions; watchdog with allocation ledger.",
    "Freeze references before execution. Verify prepared input hashes, frozen docking outputs and final-pose files are available. Run baseline-own first; baseline mismatch aborts all later arms.",
    "Each unit must regenerate all 50 selected pose PDBs at stable relative paths. Compare full file contents, counts, ranks, transforms and scores; no numerical tolerance is introduced for CPU scheduling.",
    "Timing includes wrapper launch, docking, pose generation, manifest checks and collection for every arm; separately report allocation provisioning, build, retrieval, warmup, export and idle.",
    "Collect process-tree user+system CPU seconds, wall seconds, effective cores=CPU seconds/wall seconds, busy fraction=effective cores/allowed logical CPUs, voluntary/involuntary context switches, peak aggregate RSS, thread peaks and shared immutable-file change counts. Define sampling interval before launch.",
    "Record GPU utilization to document resource accounting only. Draw no MPS, GPU scheduling, CPU/GPU numerical agreement or DockQ conclusions.",
    "High busy fraction without speedup deprioritizes unchanged-thread concurrency; low busy fraction without speedup motivates launch/I/O inspection. These are diagnostic directions, not extra acceptance tests.",
    "Keep logs, failed arms, overruns and all timing observations. A separate 13-thread follow-up needs a new sealed plan; never mix it into this comparison.",
    "Record actual allocation receipt through confirmed termination. If exported billing cannot be confirmed, report cost as bounded reservation rather than measured invoice.",
    "Resource sampler interval: sample_interval=0.1 seconds; record sampler CPU overhead. Apply identical collector to all arms."
  ],
  "phases": [
    {
      "id": "seal",
      "what": "Offline: specify units, output manifests, presealed exclusions, order, timers, diagnostics and controller interface. Verify required private artifacts later under authorized access before any allocation.",
      "stop_rule": "No launch until reference outputs and exact CPU unit commands are available. This card does not read private repository files."
    },
    {
      "id": "setup_anchor",
      "what": "Start one instance and global watchdog; retrieve/build pinned CPU executable, record hardware, verify manifests, execute first baseline-own anchor.",
      "stop_rule": "Stop and terminate if setup/anchor time box expires or any anchor mismatch occurs."
    },
    {
      "id": "compare",
      "what": "Execute remaining b,c2,c4,c4,c2,b,a; validate each output before counting throughput. Measure actual workflow ratios and diagnostics.",
      "stop_rule": "Stop subsequent arms on any mismatch; timer ends phase without completing missing arms."
    },
    {
      "id": "report_close",
      "what": "Export compact manifests, timings, equality results, diagnostics and cost ledger; terminate instance and confirm termination. Apply fixed ratio decision only to completed paired runs.",
      "stop_rule": "Allocation watchdog terminates by total 2 hours from allocation start, including setup, retrieval, idle and export. Report incomplete pairs as unavailable."
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
      "id": "card_cap",
      "name": "Full card ceiling",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 100
    },
    {
      "id": "calibration_cap",
      "name": "Hard calibration cap",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 10
    },
    {
      "id": "cases",
      "name": "Fixed cases per workflow",
      "unit": "cases",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "arm_count",
      "name": "Scheduling arms",
      "unit": "arms",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "width_serial",
      "name": "Serial concurrency",
      "unit": "jobs",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "width_two",
      "name": "Intermediate concurrency",
      "unit": "jobs",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "width_four",
      "name": "Maximum concurrency",
      "unit": "jobs",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "threads_job",
      "name": "Unchanged OpenMP threads per job",
      "unit": "threads",
      "basis": "DESIGN",
      "value": 26
    },
    {
      "id": "rotations",
      "name": "Standard rotational search",
      "unit": "rotations",
      "basis": "DESIGN",
      "value": 3600
    },
    {
      "id": "retained",
      "name": "Retained predictions per case",
      "unit": "poses",
      "basis": "DESIGN",
      "value": 50
    },
    {
      "id": "per_rotation",
      "name": "Predictions per rotation",
      "unit": "predictions",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "voxel",
      "name": "Voxel pitch",
      "unit": "angstrom",
      "basis": "DESIGN",
      "value": 1.2
    },
    {
      "id": "electrostatic",
      "name": "Electrostatic weight",
      "unit": "weight",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "hydrophobic",
      "name": "Hydrophobic weight",
      "unit": "weight",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "receptor_penalty",
      "name": "Receptor core penalty",
      "unit": "weight",
      "basis": "DESIGN",
      "value": -45
    },
    {
      "id": "ligand_penalty",
      "name": "Ligand core penalty",
      "unit": "weight",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "score_function",
      "name": "Scoring function selection",
      "unit": "index",
      "basis": "DESIGN",
      "value": 3
    },
    {
      "id": "repeats",
      "name": "Repeats per scheduling arm",
      "unit": "repeats",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "speed_gate",
      "name": "Required paired workflow speedup",
      "unit": "factor",
      "basis": "DESIGN",
      "value": 1.05
    },
    {
      "id": "mismatch_allowed",
      "name": "Allowed nonvolatile output mismatches",
      "unit": "files",
      "basis": "DESIGN",
      "value": 0
    },
    {
      "id": "setup_h",
      "name": "Setup and first anchor time box",
      "unit": "instance hours",
      "basis": "DESIGN",
      "value": 0.5
    },
    {
      "id": "compare_h",
      "name": "Remaining comparison time box",
      "unit": "instance hours",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "close_h",
      "name": "Export and termination time box",
      "unit": "instance hours",
      "basis": "DESIGN",
      "value": 0.5
    },
    {
      "id": "sample_interval",
      "name": "Resource sampling interval, sealed before launch",
      "unit": "seconds",
      "basis": "DESIGN",
      "value": 0.1
    },
    {
      "id": "human_h",
      "name": "Human implementation allowance",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 8
    },
    {
      "id": "host_vcpus",
      "name": "Advertised host CPU allocation",
      "unit": "vCPUs",
      "basis": "CITED",
      "value": 26,
      "source_id": "lambda",
      "quote": "26",
      "page_setting": "Single NVIDIA H100 PCIe on-demand instance; vCPUs are not assumed physical cores."
    },
    {
      "id": "hourly_gpu",
      "name": "Per-GPU hourly rate",
      "unit": "USD/GPU/hour",
      "basis": "CITED",
      "value": 3.29,
      "source_id": "lambda",
      "quote": "$3.29",
      "page_setting": "Single NVIDIA H100 PCIe on-demand instance."
    },
    {
      "id": "gpu_count",
      "name": "Allocated GPUs; CPU workload leaves GPU unused",
      "unit": "GPUs",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "planned_workflows",
      "name": "Maximum planned timed workflows, conditional on gates and timers",
      "unit": "workflows",
      "basis": "DERIVED",
      "expr": "arm_count * repeats"
    },
    {
      "id": "planned_dockings",
      "name": "Maximum planned docking executions",
      "unit": "dockings",
      "basis": "DERIVED",
      "expr": "planned_workflows * cases"
    },
    {
      "id": "planned_poses",
      "name": "Maximum retained pose outputs across timed executions",
      "unit": "poses",
      "basis": "DERIVED",
      "expr": "planned_dockings * retained"
    },
    {
      "id": "total_h",
      "name": "Whole allocation time box",
      "unit": "instance hours",
      "basis": "DERIVED",
      "expr": "setup_h + compare_h + close_h"
    },
    {
      "id": "total_usd",
      "name": "Maximum scheduled pre-tax allocation cost",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "total_h * hourly_gpu * gpu_count"
    }
  ],
  "cost": {
    "rates": [
      {
        "id": "h100_host",
        "gpu": "NVIDIA H100 PCIe",
        "gpu_memory_gb": 80,
        "n_gpus": 1,
        "per_gpu_usd_h": 3.29
      }
    ],
    "lines": [
      {
        "id": "setup_box",
        "phase": "setup_anchor",
        "what": "Allocation-wide setup, retrieval, build and first correctness anchor; timer bounded.",
        "kind": "work",
        "rate": "h100_host",
        "hours": "setup_h"
      },
      {
        "id": "compare_box",
        "phase": "compare",
        "what": "Remaining prospective scheduling comparison; timer bounded, unfinished arms unavailable.",
        "kind": "work",
        "rate": "h100_host",
        "hours": "compare_h"
      },
      {
        "id": "close_box",
        "phase": "report_close",
        "what": "Export, idle contingency and confirmed termination; timer bounded.",
        "kind": "allotment",
        "rate": "h100_host",
        "hours": "close_h"
      }
    ],
    "yields": [
      "cases",
      "arm_count",
      "planned_workflows",
      "planned_dockings",
      "planned_poses"
    ],
    "spend_cap_usd": 10,
    "total_stated": 6.58
  },
  "full_scale": [],
  "outside_budget": [
    {
      "what": "DESIGN allowance for human harness implementation, manifest review and report inspection",
      "qty": 8,
      "unit": "human hours"
    },
    {
      "what": "DESIGN allowance for local planning and small report artifacts on existing machine",
      "qty": 0,
      "unit": "additional USD"
    }
  ],
  "restructuring": {
    "sequential_part": "One workflow completes 4 fixed docking cases before producing its complete report.",
    "method": "none"
  },
  "scope_gap": [
    "Calibration uses at most USD10 of available USD1000 credit; no reason to spend remaining credit on this host scheduling question. Full card ceiling remains USD100, but this option does not schedule that spend.",
    "CPU throughput cannot decide root question: CPU/GPU standard agreement, GPU dense-search affordability and rank1/best50 DockQ require separately sealed prospective replication.",
    "Supplied task reports run2 quality was already exposed. Any later quality execution is replication, never unseen holdout or retrospective preregistration.",
    "Supplied private history: whole mixed bundle factor 1.0466 and FroDock width4 factor 2.2976 are exploratory context only; different bundle/executable, no MEGADOCK unit speedup inference or fabricated public citation.",
    "Supplied private history: docking-only CPU/GPU/dense totals 40.07/6.85/69.38 seconds, setup 145 seconds and dense rank1 regressions remain exploratory negatives; none sizes this time-box budget.",
    "Implementation gaps reported in supplied option, not independently inspected: run2/agent/harness/run_command.sh:8-43 lacks unit route; BRIEF_run1.md:48-158 supplies preparation obligations; new MEGADOCK units and CPU-only harness are required.",
    "Tree PLAN can represent arms, anchor, decision and noise rules. Measure compilation represents uncertain scalars/phases, not comparison arms; its 2.5x PROXY or 3x other bands cannot replace 1.05 advancement or output equality. Execution stage arguments/controller remain to be established.",
    "No public URL can substantiate exact private prepared bytes or historical runs. They are supplied requirements/context, not CITED or producer MEASURED evidence. Block launch if artifacts cannot be verified.",
    "No persistent Lambda filesystem requested; fs_usd_gib_month is not used. Transfer/storage capacity and runtime are not assumed sufficient: timeouts may yield unavailable results.",
    "Timer budget covers all billed allocation time. Advertised prices exclude applicable taxes [lambda_tax]; taxes and paid external services require separate accounting before launch if credit does not cover them."
  ],
  "novelty": {
    "closest_prior": "Published MEGADOCK docking benchmarks reached 98% scaling at 420 nodes; they measured distributed work, not four jobs competing on one host [prior].",
    "closest_source_id": "prior",
    "prior_max_level": null,
    "left_open": "Whether 2 or 4 fixed-thread CPU jobs sharing 26 logical CPUs preserve every output and beat serial workflow time by 1.05.",
    "decides": "no",
    "searched": true
  },
  "limits": "No dense-search quality, GPU scheduling, biological efficacy or beyond-four-case inference; two repeats provide an operational screen, not statistical confidence.",
  "test_summary": "Build CPU units and equality checker; compare original four-case serial workflow, separate serial invocations, and widths 2/4 in symmetric order. Require identical outputs and both speedups ≥1.05. Reserve 2 instance-hours, USD6.58, with USD10 hard cap.",
  "sources": [
    {
      "id": "lambda",
      "url": "https://lambda.ai/pricing",
      "quote": "NVIDIA H100 PCIe | 80 GB | 26 | 225 GiB | 1 TiB SSD | $3.29",
      "supports": "Advertised single-GPU instance row: GPU memory, vCPUs and per-GPU hourly rate; supplied start-of-run sheet identifies GPU count as 1."
    },
    {
      "id": "lambda_tax",
      "url": "https://lambda.ai/pricing",
      "quote": "* plus applicable sales tax/VAT/GST",
      "supports": "Displayed rates exclude applicable taxes."
    },
    {
      "id": "usage",
      "url": "https://www.bi.cs.titech.ac.jp/megadock/usage.html",
      "quote": "MEGADOCK can parallelize rotation calculations by using OpenMP.",
      "supports": "CPU rotation parallelization; same page documents CPU executable, OMP_NUM_THREADS and docking arguments. Exact planned settings are task-mandated DESIGN choices."
    },
    {
      "id": "prior",
      "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4221127/",
      "quote": "Notably, a high scalability (98%) was obtained with the largest number of nodes (420 nodes).",
      "supports": "Published distributed docking scaling result; unlike same-host fixed-thread concurrency. Search returned this open-access article."
    }
  ],
  "files_read": ["/home/hal/dev/interp/metis/experiments/blind-02/20261103-1649-tree/out/work/seed-20261103/seed/idea/310ca263/producer.md"]
}
