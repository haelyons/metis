# Differential tracing plan

Planning only. No GPU execution or prospective measurement. Public claims cite source IDs resolved to URLs in record; private requirements remain user-provided provenance. Timers bound spending, not promised completion. Primary audit targets standard CPU/GPU agreement. Parent dense-search study remains gated downstream.

```json
{
  "option_title": "Differential tracing of CPU/GPU numerical disagreement",
  "question": "Can 6 checkpoints locate CPU/GPU disagreement without confusing numerical differences with changed docking poses?",
  "hypothesis": "Matched intermediate arrays plus independent fixtures locate numerical differences; extra GPU replicas cannot justify scientific acceptance tolerances.",
  "compute_axis": {
    "quantity": "Instrumented CPU/GPU executions, fixed diagnostic coverage rather than a search for a compute scaling threshold",
    "unit": "executions",
    "levels": [
      8,
      16
    ]
  },
  "held_fixed": [
    "DESIGN scope: exactly 1aua__A1_P24280--1aua__A2_P24280:apo; 1ax2__A1_P16404--1ax2__A2_P16404:apo; 1dv1__A1_P24182--1dv1__B1_P24182:apo, and 1nr5__A1_P07547--1nr5__A2_P07547:apo from PINDER 2024-02. Case identities are user instructions, not public measurement claims.",
    "Before acquisition, freeze prepared monomer bytes, source/reference hashes and preprocessing; native references accessible only to evaluator. Missing prepared-byte hashes block execution.",
    "Freeze source commit, local patches, compiler flags, binaries, FFTW/cuFFT/CUDA/driver identities, FFT planning and normalization, grid dimensions, scoring, pose generation, evaluator and chain mapping. Mapping matters [mapping].",
    "DESIGN: same 3600 rotations and 50 retained predictions for CPU/GPU diagnostic comparison. Dense 54000 rotations is a separate changed-search arm [commands], never an agreement comparator.",
    "Freeze CPU affinity and thread count after inventory; use same host policy for CPU/GPU. Record allocation UUID, GPU model, clocks, device visibility and exclusivity. No tuning after fresh comparisons.",
    "Trace copy layout, checkpoint coordinates, rotation list, fixture seeds, comparison rules and writer schema sealed before study runs. Instrumented runs excluded from acceleration timing."
  ],
  "predictions": {
    "if_lever": "At 16 executions, tracing still localizes all 6 injected faults and reproduces natural divergence stages across paired repeats.",
    "if_not": "At 16 executions, tracing localizes fewer than 6 injected faults or natural divergence stages change between repeats.",
    "decision_rule": "Diagnostic success requires localized_faults = injected_faults = 6, false_localizations = 0, and exact checkpoint/schema coverage on every scheduled trace. Natural divergence stage must repeat on matched sampled rotations; absent divergence is reported as absent. A reproducible mismatch is evidence for diagnosis, never automatic scientific acceptance. Full CPU/GPU acceptance additionally requires all 50 outputs in every case to pass independently justified score, transform, coordinate, tie and evaluator criteria sealed in seal; unresolved criteria mean BLOCKED, not PASS.",
    "noise_rule": "Run 8 initial instrumented executions, then 8 matched repeat executions: CPU/GPU pair per case in each pass. Compare within-backend traces first, then cross-backend. Record absolute, relative and ULP errors, nonfinite counts, complex layout and normalization. Hash equality diagnoses bitwise identity only. Report changed rank membership and ties separately; repeat variability beyond sealed bounds blocks agreement. No biological sample-size increase from repeats.",
    "expected": "unsure",
    "expected_why": "Injected faults should be localizable by construction; natural divergence reproducibility and defensible application tolerances remain unmeasured."
  },
  "compute_tested": "no",
  "compute_tested_why": "This is a bounded diagnostic audit. The 8-to-16 execution axis adds repeat checks, not a test that more parallel hardware changes docking quality or supplies tolerances. No GPU scaling claim.",
  "scored_against": "Ground-truth injection location; exact integer circular-correlation oracle on synthetic complex grids; independently implemented transform/serialization checks; full same-settings CPU/GPU output comparison under criteria sealed before fresh comparisons. CPU is a comparator, not mathematical truth [numeric]. Parent quality is scored only against pinned native references with frozen DockQ mapping [mapping].",
  "arms": [
    {
      "id": "cpu",
      "what": "Pinned existing CPU MEGADOCK, standard 3600 rotations, 50 predictions; uninstrumented output baseline plus separate instrumented build."
    },
    {
      "id": "gpu",
      "what": "Pinned existing GPU MEGADOCK, same standard settings and retention; matched checkpoints and separate uninstrumented control."
    },
    {
      "id": "fixtures",
      "what": "Independent exact-integer oracle, null controls, and known checkpoint fault injections; these test instrumentation and numerical components."
    },
    {
      "id": "dense_handoff",
      "what": "Downstream only: GPU -D, documented 54000 rotations, same scoring and 50 predictions [commands]. Not run on this diagnostic allocation; separate sealed root replication required."
    }
  ],
  "baseline": {
    "what": "Unmodified same-settings CPU and GPU outputs, followed by each backend's trace-enabled outputs. First require trace-enabled versus unmodified scientific outputs to match exactly on the same backend; otherwise instrumentation is suspect.",
    "value": "Fresh baseline pending; historical private timings and score deltas are exploratory and not cost inputs."
  },
  "anchor": {
    "what": "Exact integer grid correlations and 6 injected faults check checkpoint alignment; independent pose reconstruction checks output interpretation.",
    "published_value": "No published four-case numerical-equivalence threshold found; oracle is proposed independent code, not an executed anchor.",
    "tolerance": "Integer oracle has exact expected values. For tiny-grid FFT diagnostic fixtures require absolute score error <= fixture_error and unique-peak agreement; tied maxima compared as sets. This fixture threshold is a DESIGN screen, not a production scientific score tolerance. Recover every injected stage exactly and accept no false localization on null controls. Production score/pose/DockQ bounds require independent analysis in seal; stop scientific agreement if unavailable.",
    "independent_code": "Build oracle_integer.py using Python integers and explicit periodic indexing, independent of FFT libraries; represent complex values as integer pairs. Build pose_oracle.py with explicit rigid-transform algebra and separate parser. Verify impulse, translation, cancellation and tied-peak fixtures."
  },
  "checks": [
    "Build trace writer around 6 semantic boundaries: voxel grids; forward transforms; conjugated products; normalized inverse transforms; peak/transform selection; serialization. Compare both packed complex components; do not split scoring into invented independent outputs. FFT correlation is documented in [prior].",
    "Save stage metadata: case, rotation identity, dimensions, dtype, strides, endian, normalization and content digest. Match scientific coordinates, not raw memory layout. Trace mode performs read-only copies with synchronization before capture; test it does not change final output.",
    "Capture full arrays for 8 predetermined rotations per standard run: zero-based floor(j*3600/8), j=0 through 7. Save all rotation-level candidate summaries and final 50 predictions. These samples cannot certify earliest divergence at unsampled rotations.",
    "On a final-output discrepancy, allow at most 16 targeted single-rotation replays across the study; select earliest differing candidate rotation from frozen summaries. Replays diagnose failure, never replace scheduled results or repair agreement silently.",
    "Stream arrays to bounded local storage, compare then delete large arrays only after compact evidence is exported. Stop capture at trace_gib; mark coverage incomplete rather than silently reducing checkpoints or rotation count.",
    "Require all 50 transforms, finite scores, reconstructed coordinates, atom/chains and rank membership per case; sealed tie handling cannot rerank to rescue failure. Serialization and evaluator tolerances are separate from intermediate-array diagnostics.",
    "Record complete invocation time and trace overhead, setup/retrieval/idle and GPU activity separately. No kernel-time or bundled-throughput number substitutes for uninstrumented complete-workflow acceleration.",
    "All numeric limits here are DESIGN choices unless numbers says CITED or DERIVED. No fresh GPU measurement or scientific PASS is claimed."
  ],
  "phases": [
    {
      "id": "contract",
      "what": "Offline build specification and executable-route repair. Deliver trace writer/comparator schemas, fixture definitions, immutable manifest and stage/controller dry-run. Confirm rate, prepared hashes, reference pins and inventory. Record user requirements as provenance, not public citations.",
      "stop_rule": "No GPU launch until missing stage arguments, controller chain, source/patch identity, prepared bytes and stop/retrieval behavior are resolved. No box execution in this tree-planning task."
    },
    {
      "id": "screen",
      "what": "Later calibration allocation only: installation, tiny fixtures, memory/transfer/storage measurement and telemetry validation. Exercise all 6 stage injections and null controls. Include setup, retrieval and idle in 2-hour timer. No four-case study or native quality evaluation.",
      "stop_rule": "Projected allocation including shutdown < calibration_cap_usd; target <= calibration_target_usd. At timer expiry terminate and retain incomplete status. No dependent main work on calibration route. Require observed localized_faults >= 6 and zero false localizations before main spend; otherwise stop acquisition.",
      "gate": {
        "on": "calibration_projected_usd",
        "op": "<=",
        "value": 10,
        "else": "Stop, retrieve and redesign offline; never extend calibration into full study."
      }
    },
    {
      "id": "seal",
      "what": "Offline review of precision, FFT error propagation, voxel boundaries, ties, reconstruction/serialization and evaluator stability. Use independent fixtures and analysis; seal numeric production atol/rtol, coordinate and DockQ bounds, tie policy, repetitions and failure rules before fresh study comparisons.",
      "stop_rule": "No tolerance derived from historical or fresh CPU/GPU maximum deltas. Tiny fixtures do not prove production error bounds. If independent justification fails, proceed only with explicitly diagnostic reporting; scientific agreement and dense-quality handoff remain blocked.",
      "gate": {
        "on": "acceptance_contract_ready",
        "op": ">=",
        "value": 1,
        "else": "Diagnostic-only audit allowed; no scientific acceptance or dense-quality release."
      }
    },
    {
      "id": "trace",
      "what": "Main allocation, separate launcher: 8 initial instrumented standard executions, 8 repeat executions, per-backend uninstrumented controls, bounded targeted replay. Use 8 fixed sampled rotations and 6 checkpoints. Run CPU/GPU pairs with matched settings, without native evaluation until correctness checks pass.",
      "stop_rule": "Main work timebox 8 hours; stop new work at soft 6 cumulative allocation hours and assess remaining retrieval reserve. Global hard limit 12 allocation hours across screen/main/retrieval. Incomplete runs preserved."
    },
    {
      "id": "analyze",
      "what": "Offline compare stored traces, validate 6 injections and null controls, identify first reproducible bitwise and threshold-crossing stages separately, then classify score rounding, changed transforms, coordinates or serialization. Report sampled coverage and unresolved causes.",
      "stop_rule": "No GPU reservation for stored-trace analysis. Scientific agreement requires sealed bounds; a diagnosis alone never passes it.",
      "gate": {
        "on": "localized_faults",
        "op": ">=",
        "value": 6,
        "else": "Reject tracing reliability; retain negative result and block scientific handoff."
      }
    },
    {
      "id": "handoff",
      "what": "Export diagnostic evidence plus machine-readable agreement status. Downstream root study must separately calibrate CPU 3600, GPU 3600 and GPU -D 54000 complete workflows, fixed 50 predictions; seal common budgets and timing/noise rules before quality evaluation.",
      "stop_rule": "No downstream scientific quality run under this card. Parent study: 1 warmup and 7 balanced timing blocks; 95% paired-block interval, 10000 resamples, worthwhile speedup lower bound >1.05. Report per-case dense-minus-standard rank1 and best50 DockQ separately; gain exceeds max(0.01, independently sealed evaluator/repeat noise). Preserve unavailable budgets, negatives, overruns and all exposed-case replication status."
    },
    {
      "id": "close",
      "what": "Timebox 2 additional allocation hours for retrieval, shutdown and contingency across allocations. Export compact evidence, telemetry, manifests and failure logs; terminate instances and verify bill. Ledger includes CPU work and idle [billing].",
      "stop_rule": "Maximum study allocation hours 12, dollars 100 including all charges; reserve covers taxes/rounding/termination uncertainty. No automatic spending of unused credit. If final invoice unavailable, label cost estimated."
    }
  ],
  "numbers": [
    {
      "id": "budget_usd",
      "name": "Hard card ceiling, below user credit allowance",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 100
    },
    {
      "id": "credit_usd",
      "name": "User's available credit ceiling, not target spend",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 1000
    },
    {
      "id": "cases",
      "name": "Fixed user-requested cases",
      "unit": "cases",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "backends",
      "name": "CPU and GPU standard implementations",
      "unit": "backends",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "passes",
      "name": "Initial trace pass plus matched repeat",
      "unit": "passes",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "initial_execs",
      "name": "Initial CPU/GPU trace executions",
      "unit": "executions",
      "basis": "DERIVED",
      "expr": "cases * backends"
    },
    {
      "id": "trace_execs",
      "name": "Scheduled instrumented executions including repeats",
      "unit": "executions",
      "basis": "DERIVED",
      "expr": "initial_execs * passes"
    },
    {
      "id": "checkpoints",
      "name": "Ordered semantic checkpoints",
      "unit": "checkpoints",
      "basis": "DESIGN",
      "value": 6
    },
    {
      "id": "sample_rotations",
      "name": "Predetermined rotations per trace execution",
      "unit": "rotations",
      "basis": "DESIGN",
      "value": 8
    },
    {
      "id": "checkpoint_sets",
      "name": "Maximum scheduled sampled checkpoint sets",
      "unit": "sets",
      "basis": "DERIVED",
      "expr": "trace_execs * sample_rotations * checkpoints"
    },
    {
      "id": "retained",
      "name": "Predictions retained per scientific arm",
      "unit": "predictions",
      "basis": "DESIGN",
      "value": 50
    },
    {
      "id": "standard_rotations",
      "name": "Documented standard search",
      "unit": "rotations",
      "basis": "CITED",
      "value": 3600,
      "source_id": "commands",
      "quote": "15 deg. (3600 angles) of rotational sampling",
      "page_setting": "MEGADOCK command guide standard rotation setting."
    },
    {
      "id": "dense_rotations",
      "name": "Documented dense search for downstream handoff",
      "unit": "rotations",
      "basis": "CITED",
      "value": 54000,
      "source_id": "commands",
      "quote": "6 deg. (54000 angles)",
      "page_setting": "MEGADOCK -D command setting; not funded as diagnostic work."
    },
    {
      "id": "replay_cap",
      "name": "Maximum targeted single-rotation replays",
      "unit": "executions",
      "basis": "DESIGN",
      "value": 16
    },
    {
      "id": "fixture_families",
      "name": "Impulse, translation, cancellation, tie",
      "unit": "families",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "grid_side_small",
      "name": "First cubic fixture side length",
      "unit": "voxels",
      "basis": "DESIGN",
      "value": 4
    },
    {
      "id": "grid_side_large",
      "name": "Second cubic fixture side length",
      "unit": "voxels",
      "basis": "DESIGN",
      "value": 8
    },
    {
      "id": "fixture_sizes",
      "name": "Number of grid sizes",
      "unit": "sizes",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "fixture_inputs",
      "name": "Independent fixture inputs",
      "unit": "inputs",
      "basis": "DERIVED",
      "expr": "fixture_families * fixture_sizes"
    },
    {
      "id": "fixture_execs",
      "name": "Backend and repeat fixture checks",
      "unit": "executions",
      "basis": "DERIVED",
      "expr": "fixture_inputs * backends * passes"
    },
    {
      "id": "fixture_error",
      "name": "Tiny-grid absolute FFT diagnostic error screen; no production equivalence claim",
      "unit": "score units",
      "basis": "DESIGN",
      "value": 0.25
    },
    {
      "id": "injected_faults",
      "name": "Known earliest-stage fault injections on tiny fixtures",
      "unit": "faults",
      "basis": "DESIGN",
      "value": 6
    },
    {
      "id": "null_controls",
      "name": "Unchanged fixture controls",
      "unit": "controls",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "screen_fixture_execs",
      "name": "Fixture checks plus injection and null runs",
      "unit": "executions",
      "basis": "DERIVED",
      "expr": "fixture_execs + injected_faults + null_controls"
    },
    {
      "id": "localized_faults",
      "name": "Unmeasured successfully localized injections; conservative placeholder",
      "unit": "faults",
      "basis": "GUESS",
      "value": 0,
      "rests_on": "No execution or independent numerical review completed; use zero until phase measures readiness.",
      "measured_by": "screen"
    },
    {
      "id": "false_localizations",
      "name": "Allowed false fault localization on null controls",
      "unit": "faults",
      "basis": "DESIGN",
      "value": 0
    },
    {
      "id": "acceptance_contract_ready",
      "name": "Unestablished scientific acceptance contract; conservative placeholder",
      "unit": "boolean",
      "basis": "GUESS",
      "value": 0,
      "rests_on": "No execution or independent numerical review completed; use zero until phase measures readiness.",
      "measured_by": "seal"
    },
    {
      "id": "trace_gib",
      "name": "Maximum local trace workspace, enforced by writer",
      "unit": "GiB",
      "basis": "DESIGN",
      "value": 10
    },
    {
      "id": "persistent_gib",
      "name": "Persistent Lambda filesystem allocation",
      "unit": "GiB",
      "basis": "DESIGN",
      "value": 0
    },
    {
      "id": "fs_usd_gib_month",
      "name": "Price-sheet filesystem example, not verified live quote",
      "unit": "USD/GiB-month",
      "basis": "CITED",
      "value": 0.2,
      "source_id": "fs",
      "quote": "For example, at a rate of $0.20 per GiB per month:",
      "page_setting": "Illustrative filesystem example; actual price may differ. Persistent volume size is zero, so cost does not depend on this example."
    },
    {
      "id": "screen_hours",
      "name": "Calibration whole-allocation timebox including setup and delivery",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "trace_hours",
      "name": "Main acquisition whole-allocation work timebox",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 8
    },
    {
      "id": "close_hours",
      "name": "Retrieval/shutdown/contingency allocation time reserve",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 2
    },
    {
      "id": "soft_hours",
      "name": "Soft cumulative allocation limit",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 6
    },
    {
      "id": "hard_hours",
      "name": "Hard cumulative allocation limit",
      "unit": "hours",
      "basis": "DERIVED",
      "expr": "screen_hours + trace_hours + close_hours"
    },
    {
      "id": "calibration_cap_usd",
      "name": "Strict upper boundary for later calibration; projection must be below this",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 20
    },
    {
      "id": "calibration_target_usd",
      "name": "Preferred calibration spending ceiling",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 10
    },
    {
      "id": "calibration_projected_usd",
      "name": "Conservative calibration projection including reserved extras",
      "unit": "USD",
      "basis": "DERIVED",
      "expr": "screen_hours * gpu_rate_usd_h * gpu_count + screen_extra_reserve_usd"
    },
    {
      "id": "extra_reserve_usd",
      "name": "Allotment for tax, billing rounding and unforeseen provider charges",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 10
    },
    {
      "id": "parent_warmups",
      "name": "Downstream timing warmups, not purchased here",
      "unit": "runs",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "parent_timing_blocks",
      "name": "Downstream balanced timing repetitions, not purchased here",
      "unit": "blocks",
      "basis": "DESIGN",
      "value": 7
    },
    {
      "id": "confidence_percent",
      "name": "Downstream paired timing interval coverage",
      "unit": "percent",
      "basis": "DESIGN",
      "value": 95
    },
    {
      "id": "bootstrap_draws",
      "name": "Downstream paired-block resamples",
      "unit": "draws",
      "basis": "DESIGN",
      "value": 10000
    },
    {
      "id": "speedup_floor",
      "name": "Downstream worthwhile acceleration lower-bound threshold",
      "unit": "ratio",
      "basis": "DESIGN",
      "value": 1.05
    },
    {
      "id": "quality_margin",
      "name": "Downstream chosen DockQ gain margin, not equivalence tolerance",
      "unit": "DockQ",
      "basis": "DESIGN",
      "value": 0.01
    },
    {
      "id": "human_hours",
      "name": "Outside-Lambda engineering/review allowance",
      "unit": "hours",
      "basis": "DESIGN",
      "value": 32
    },
    {
      "id": "gpu_rate_usd_h",
      "name": "Single H100 PCIe per-GPU on-demand rate",
      "unit": "USD/GPU-hour",
      "basis": "CITED",
      "value": 3.29,
      "source_id": "price",
      "quote": "$3.29",
      "page_setting": "1-GPU H100 PCIe instance."
    },
    {
      "id": "gpu_memory_gb",
      "name": "Selected GPU memory",
      "unit": "GB",
      "basis": "CITED",
      "value": 80,
      "source_id": "price",
      "quote": "80 GB",
      "page_setting": "H100 PCIe price row."
    },
    {
      "id": "prior_jobs",
      "name": "Published timing benchmark size, not diagnostic axis",
      "unit": "docking jobs",
      "basis": "CITED",
      "value": 352,
      "source_id": "prior",
      "quote": "352 docking",
      "page_setting": "ZLAB Docking Benchmark timing table; different workload, not a cost estimate."
    },
    {
      "id": "gpu_count",
      "name": "GPUs per reserved instance",
      "unit": "GPUs",
      "basis": "DESIGN",
      "value": 1
    },
    {
      "id": "screen_extra_reserve_usd",
      "name": "Calibration share of existing extras reserve, not additional spending",
      "unit": "USD",
      "basis": "DESIGN",
      "value": 3
    }
  ],
  "cost": {
    "rates": [
      {
        "id": "h100_single",
        "gpu": "NVIDIA H100 PCIe",
        "gpu_memory_gb": 80,
        "n_gpus": 1,
        "per_gpu_usd_h": 3.29
      }
    ],
    "lines": [
      {
        "id": "calibration",
        "phase": "screen",
        "what": "Timer-bounded fixture calibration, setup/idle/retrieval included; $6.58 before reserved extras [price].",
        "kind": "work",
        "rate": "h100_single",
        "hours": "screen_hours"
      },
      {
        "id": "acquisition",
        "phase": "trace",
        "what": "Timer-bounded standard CPU/GPU trace acquisition and controls; CPU work on GPU host billed too [billing]. No throughput or completion estimate.",
        "kind": "work",
        "rate": "h100_single",
        "hours": "trace_hours"
      },
      {
        "id": "shutdown",
        "phase": "close",
        "what": "Allocation-time reserve for transport, idle, retrieval and verified termination; $6.58 [price].",
        "kind": "allotment",
        "rate": "h100_single",
        "hours": "close_hours"
      },
      {
        "id": "persistent_storage",
        "phase": "close",
        "what": "No persistent filesystem created; local arrays exported or deleted before termination. Illustrative filesystem rate is unused [fs].",
        "kind": "storage",
        "usd": "persistent_gib * fs_usd_gib_month"
      },
      {
        "id": "extras",
        "phase": "close",
        "what": "Bounded reserve, not predicted tax or spending requirement. Stop if verified all-in projected bill exceeds ceiling.",
        "kind": "allotment",
        "usd": "extra_reserve_usd"
      }
    ],
    "yields": [
      "cases",
      "trace_execs",
      "checkpoint_sets",
      "fixture_inputs",
      "screen_fixture_execs",
      "retained"
    ],
    "spend_cap_usd": 100,
    "total_stated": 49.48
  },
  "full_scale": [],
  "outside_budget": [
    {
      "what": "DESIGN engineering, independent numerical review and report allowance; no paid consultant assumed",
      "qty": 32,
      "unit": "human hours"
    },
    {
      "what": "DESIGN incremental non-Lambda cash allocation; use existing workstation and artifact storage",
      "qty": 0,
      "unit": "USD"
    }
  ],
  "restructuring": {
    "sequential_part": "Each traced rotation consumes 6 dependent checkpoints; 8 initial executions cover 4 CPU/GPU case pairs.",
    "method": "none"
  },
  "scope_gap": [
    "No prospective MEASURED inputs: planning only, no GPU launch, no local benchmark, no promise that timer purchases completed study. Incomplete coverage is a valid negative result.",
    "Production numerical tolerances remain scientific blockers until seal. Fixtures establish component behavior and trace reliability, not universal error bounds or acceptable pose error.",
    "Only 8 sampled rotations have full intermediate arrays per run; unsampled-rotation differences require bounded replay. First different array need not be root cause without independent fixture reproduction.",
    "Parent complete-workflow acceleration and dense-search quality remain downstream. This diagnostic budget cannot answer them and does not authorize bundled-throughput substitutions.",
    "Framer §Specific route gaps reports dut/pipeline/m5/SCHEMAS.md A/PREDICTIONS, Propose, Evaluate and adapter sections and pipeline.js configuration dispatcher cannot represent ordered agreement plus changed-search quality. This report is private inherited provenance, not a fresh source-code audit.",
    "Framer §Specific route gaps reports dut/pipeline/CONTRACT.md §§2.5,5; src/main.js compilation and launch.js handoff drop scientific arms/decision rules. Scalar 2.5x PROXY or 3x other estimate bands are not scientific equivalence.",
    "Framer §Specific route gaps reports dut/pipeline/launch.js and measure pipeline.js lack established later stage arguments/controller; --stop-after-profile wrapper behavior remains unverified. Offline dry-run must establish bounded launch/stop/ledger before allocation.",
    "Framer §Ordered phases and gates leaves prepared PDB hashes and independent numerical criteria unresolved. Framer reports prior binary version inconsistency; pin verified source and executable bytes rather than trust a version string.",
    "User supplied exploratory results already exposed quality. Fresh work is prospective replication on exposed cases, never unseen holdout or retrospective preregistration. Private historical timings, setup/transport receipts and score deltas are not public citations or budget inputs.",
    "Available credit 1000 USD does not imply a reason to spend it: 100 USD hard card cap, 49.48 USD scheduled envelope, 12 allocation-hour timer maximum. No justified expansion beyond fixed diagnostic scope.",
    "GUESS zero readiness and localized-fault counts are conservative unresolved placeholders, not observed failures. Replace only with recorded phase evidence; gates enforce their stated thresholds."
  ],
  "novelty": {
    "closest_prior": "MEGADOCK published CPU/GPU docking timings over 352 jobs; it did not establish intermediate-trace equivalence or scientific acceptance thresholds [prior].",
    "closest_source_id": "prior",
    "prior_max_level": null,
    "left_open": "Can matched checkpoints distinguish harmless score differences from changed selected poses on these 4 exposed unbound cases?",
    "decides": "no",
    "searched": true
  },
  "limits": "Sampled tracing diagnoses implementations; it proves neither biological efficacy, generalization beyond 4 cases, numerical equivalence without justified tolerances, nor dense-search affordability.",
  "test_summary": "Build 6-checkpoint CPU/GPU traces, validate exact-grid fixtures and injected faults, acquire 8 executions plus 8 repeats, and compare 50 predictions per case. Keep acceptance, acceleration and dense-search quality separate.",
  "sources": [
    {
      "id": "price",
      "url": "https://lambda.ai/pricing",
      "quote": "NVIDIA H100 PCIe | 80 GB | 26 | 225 GiB | 1 TiB SSD | $3.29",
      "supports": "Public single-GPU on-demand price row; instance selection, memory and rate. Verify availability and checkout price before launch."
    },
    {
      "id": "billing",
      "url": "https://docs.lambda.ai/public-cloud/billing/",
      "quote": "ODC prices instances by hourly usage and bills in one-minute increments.",
      "supports": "Allocation billing, including CPU work and idle; account for entire reserved lifetime."
    },
    {
      "id": "fs",
      "url": "https://docs.lambda.ai/public-cloud/billing/",
      "quote": "For example, at a rate of $0.20 per GiB per month:",
      "supports": "Illustrative filesystem price only; page explicitly warns actual price may differ. Plan creates no persistent filesystem."
    },
    {
      "id": "numeric",
      "url": "https://docs.nvidia.com/cuda/floating-point/index.html",
      "quote": "The FMA operation computes \\(\\text{rn}(X \\times Y + Z)\\) with only one rounding step.",
      "supports": "FMA and reassociation motivate diagnosis; compliance does not establish application-level equivalence."
    },
    {
      "id": "commands",
      "url": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md",
      "quote": "54000 angles",
      "supports": "Documented standard and dense rotation counts. Current documentation is an interface reference, not certification of historical binaries."
    },
    {
      "id": "build",
      "url": "https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/BUILD.md",
      "quote": "|  (c) | GPU node        | GPU + OpenMP       |",
      "supports": "Separate CPU and GPU builds; confirm actual dependency identities and build flags."
    },
    {
      "id": "prior",
      "url": "https://www.bi.cs.titech.ac.jp/megadock/perform.html",
      "quote": "Total (352 docking) time (hour)  | 67.1  | 8.20  | 2.26  | 1.02",
      "supports": "Published CPU/GPU docking timing comparison; different dataset and hardware, no numerical tracing acceptance study."
    },
    {
      "id": "mapping",
      "url": "https://github.com/wallnerlab/DockQ",
      "quote": "By default, DockQ will try to find the optimal mapping between interfaces found in the native and in the model.",
      "supports": "Evaluator mapping must be pinned before CPU/GPU scientific agreement and later quality comparison."
    }
  ],
  "files_read": [
    "/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/interp.md",
    "/home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md"
  ]
}
```
