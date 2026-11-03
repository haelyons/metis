You are an authorized reader for the blind-02 experiment. The owner authorized readers to see its brief and records. The operator who launched you sees only `status.json`, as validated enum values; your final reply and `REPORT.md` are not shown to the operator. They are for the owner.

Working directory: experiments/blind-02/m5/ of the metis repository (the current directory). Write only into `run2_trace/`. The run `run2/` is finished and its box is gone: change nothing under `run2/` or anywhere else, run no workloads, contact no box, fetch nothing from the network, run no git commands.

## What the operator knows (metadata only)
run2 (raid whisper3) PASSed intake (anchors_count 0, anchored false, stock_environment null, licence unknown), reproduce (stock_verified true, 0 of 0 anchors, 3473 s wall, USD 2.92), profile (profile_complete true, timed_fraction 1, gpu_telemetry true, headroom 1.0466, 7703 s wall, USD 7.04) and seal (seal_present true, seal_verified true, prediction_count 0). propose PASSed in 0.002 s with no model call: outcome no_feasible_method, every ballot count 0. implement and evaluate were SKIPPED; takeaways ran. Box: one gpu_1x_h100_pcie, USD 10.53 in all. bounds.json: data-parallel over inputs, batching and ensembles each bound 1.0466 (p 1, k 1.0466); multi-GPU bound 1.0 (p 0.1129, k 1); pipelining bound 1.0012 (p 0.0025, k 2). Receipts: setup 145 s, anchors 1571 s, reproduce-freeze 1402 s, one upload 1424 s, profile 2832 s, concurrency 3448 s. An earlier authorized reader (run2_progress2, while the run was in profile) reported: baseline configuration "several", reproduce covers "all_four" cases, box time dominated by output fetch, fetch resends unchanged outputs, seed comparisons in pipeline "some".

## Read
- `BRIEF.md` and `b01_materials/BRIEF_run1.md` (the seed and its materials addendum)
- `run2_progress2/REPORT.md` (the earlier reader's report; do not repeat its work, build on it)
- `run2/args.json`, `run2/pipeline.log`, `run2/control/` (receipts, seals, stages, box.json), and under `run2/agent/`: `intake/`, `harness/`, `profile-packet.json`, `bounds.json`, `PREDICTIONS.json`, `propose-packet.json`, `GATE.json`, `RESEARCH_TAKEAWAY.md` if present, `results/reproduce/` and `results/profile/` (logs, `out/concurrency/concurrency.json`, the profile summaries; read large directories selectively), and `wf/` (the model calls: prompts and replies of the intake, harness and seal agents)
- the pipeline contract and code, read-only: `/home/hal/dev/interp/metis/dut/pipeline/m5/SCHEMAS.md` (above all the sections Concurrency probe, Standalone unit probe (U52), A/bounds.json, Propose, Evaluate), `pipeline.js`, `bounds.py`, `concurrency_probe.py`, `evaluate.js`

## Questions
A. What stopped the run, exactly. Follow the chain from the measured numbers to the propose outcome: the concurrency probe's single walls and batch walls and the factor it computed, the MPS state, the profile packet's stages and their kinds (which of them bounds.py counted as compute, transfer or other, and why multi-GPU got p 0.1129), the bounds, what the seal agent wrote (predictions empty? the infeasible_methods reasons? did it still seal compute_budgets, an equal_outcome_target, equivalence metrics?), and the deterministic propose step. State which contract rule in SCHEMAS.md produced each step. Say whether any model judgement entered the stop, or none.

B. The seed's requested comparisons and conclusions. List every comparison the seed asks for (each pair or set of configurations, cases, inputs, metrics or budgets it wants compared, and each conclusion it wants drawn), numbered. For each one, trace it through the run: where it is represented in the intake files (which file and field), where it was changed (for example several configurations collapsed into one published_configuration, or a quality metric dropped), which stage measured anything about it (reproduce measured which configurations on which cases; profile measured what), and where it was left unevaluated and by which contract rule. Give file paths and line references.

C. What the stop says about the research question versus about the pipeline. Is the seed's question one that a one-GPU, equal-cost, fixed-menu throughput method (the five menu entries) could answer at all? Which of m5's outputs (speedup_published, equal_cost, the outcome-vs-compute-budget curve, anchors or references, the concurrency factor itself) bear on the seed's question, and which of the seed's conclusions could no m5 run as contracted produce? Separate what the measurements show about the workload (for example that one copy already saturates the GPU, or that the host is the bottleneck) from what the stop shows about the menu.

D. The bottleneck, from the evidence. From the profile summaries, the concurrency logs and the reproduce logs: what share of wall is GPU kernel time, host time, transfer; what did the three single runs and the n=2 and n=4 batches take; does the evidence favour a saturated GPU, a saturated host (CPU threads, nproc, memory), or something else, or is it undetermined? What would decide it?

E. Units. Does the seed's workload decompose into units (per case, per file, per input) that `run_units.sh` and `units.json` could express, as the standalone unit probe (U52) requires? Does run2's harness already have them? If the unit probe ran on this workload, what would it measure that the whole-command probe did not, and could its result change the propose outcome under the current contract (it cannot: say so if so, and say what it would inform instead)?

F. The evaluate stage's compute-budget curve. Under the current contract its arms are the published baseline and the menu method. Could that curve, as sealed in run2 or as the contract allows, measure any of the seed's comparisons? What is the smallest contract change that would let it (for example arms taken from configurations named in the brief), and what would that change break or risk?

G. The smallest justified intervention, with the evidence for and against each: (1) a different use of existing mechanisms (a brief addendum, `--units-probe`, one m5 run per seed configuration stopped after profile, the unit probe, or something else you find in the code), (2) a contract change to m5 (name the sections), (3) a new seed. Say which the evidence favours, and what evidence would favour each of the others.

H. Calibration before a long experiment. List the cheapest real experiments on a box that would narrow the question (for each: what it measures, which existing mechanism runs it, estimated box hours from run2's receipts, and what result would change the plan). Note where fetch time, not the workload, dominated run2's receipts.

## Write in `run2_trace/`
`REPORT.md` for the owner: the answers A to H in order, with file and line references, numbers quoted from the files, and anything you could not establish. Then `status.json`, one JSON object with exactly these keys, each taking only the listed values:
- `"stop_cause"`: `"no_feasible_menu_method"`, `"seal_failed"`, `"ballots"`, `"infra"`, `"other"`, `"unknown"`
- `"propose_model_calls"`: `"none"`, `"some"`, `"unknown"`
- `"seal_predictions"`: `"empty"`, `"nonempty"`, `"unknown"`
- `"seed_question_kind"`: `"single_baseline_throughput"`, `"configuration_comparison"`, `"outcome_vs_compute"`, `"mixed"`, `"other"`, `"unknown"`
- `"comparisons_requested"`: `"none"`, `"one"`, `"two"`, `"three"`, `"four_or_more"`, `"unknown"`
- `"comparisons_at_intake"`: `"all"`, `"some"`, `"none"`, `"unknown"` (represented in the intake files)
- `"comparisons_changed"`: `"none"`, `"some"`, `"all"`, `"unknown"` (represented but altered, such as several configurations collapsed into one)
- `"comparisons_measured"`: `"all"`, `"some"`, `"none"`, `"unknown"` (some stage measured both sides)
- `"first_drop_stage"`: `"intake"`, `"reproduce"`, `"profile"`, `"seal"`, `"propose"`, `"none"`, `"unknown"`
- `"bottleneck"`: `"gpu_saturated"`, `"host_bound"`, `"io_bound"`, `"mixed"`, `"undetermined"`, `"unknown"`
- `"units_decomposable"`: `"yes"`, `"no"`, `"unknown"`
- `"units_in_harness"`: `"yes"`, `"no"`, `"unknown"`
- `"curve_could_serve"`: `"as_sealed"`, `"with_arms_from_seed"`, `"no"`, `"unknown"`
- `"smallest_intervention"`: `"existing_mechanism"`, `"contract_change"`, `"new_seed"`, `"unknown"`
- `"mechanism"`: `"units_probe"`, `"per_configuration_runs"`, `"addendum"`, `"other_existing"`, `"none"`, `"unknown"`
- `"calibration_box_hours"`: `"under_1"`, `"1_to_3"`, `"3_to_6"`, `"over_6"`, `"unknown"`

No other keys and no free text.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push.
- No fabrication. If something cannot be established, say so in REPORT.md and use the matching status value.

Finish within 25 minutes. End with a final reply that is exactly the contents of status.json.
