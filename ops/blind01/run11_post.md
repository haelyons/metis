You are an authorized agent for the blind-01 experiment. The owner authorized you to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values, plus content-free checks; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run11_post/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. Read large directories selectively.

## Background
run11 ran the standalone unit probe (contract: section "Standalone unit probe (U52)" and the "Concurrency probe" bullets from "Unit mode (U50b)" through "The standalone unit probe (U52) validates" in `/home/hal/dev/interp/metis/dut/pipeline/m5/SCHEMAS.md`; probe script `/home/hal/dev/interp/metis/dut/pipeline/m5/concurrency_probe.py`). After setup, eight arms ran the same four sample units: `a` one invocation of all four, `b` four single-unit invocations one after another, `c2` two at once then two at once, `c4` four at once, in the order a-1, b-1, c2-1, c4-1, c4-2, c2-2, b-2, a-2, each invocation in its own work directory of symbolic links to the shared run directory plus an empty `out/`. Its files: `run11/agent/results/reproduce/out/concurrency/concurrency.json`, the invocation logs in `run11/agent/results/reproduce/out/concurrency/logs/`, `run11/agent/results/reproduce/units_reference.json`, the receipt log for the `concurrency` operation under `run11/agent/results/reproduce/`, and the harness in `run11/agent/harness/` (`run_units.sh`, `units.json`, `run_command.sh`). The probe recorded outcome `measured`, every output byte-identical, and changes in the shared run directory (`shared_changes`). Earlier readers `run10_post/REPORT.md` and `run10_post2/REPORT.md` describe writes the measured command makes outside `out/`.

## Questions
A. Logs: do the concurrent invocations' logs (`c2-*`, `c4-*`) show errors or warnings that the serial invocations' logs (`a-1`, `a-2`) do not?
B. Coverage: do the compared output paths (each sample unit's `outputs` in `units.json`, which the probe hashes and compares) cover all of each unit's result files, or only some of them?
C. Shared writes: from the per-arm `shared_changes` counts, the logs and the code, what are the entries the measured command changes in the shared run directory during an arm, and could one invocation read entries another invocation wrote (in the same arm or a later arm)?
D. Less work: is there any sign that any later invocation did less computation than `a-1` (for example reusing results, caches or intermediate files left by earlier invocations, or skipping units)?
E. Order: compare each arm with its repeat (a-1 with a-2, b-1 with b-2, c2-1 with c2-2, c4-1 with c4-2). Is there an order effect (for example all later arms faster than `a-1`), and does the measured factor hold when each concurrent arm is compared only with its nearest serial arm?
F. Gain source: from `effective_cores`, `busy_fraction`, `threads_max`, `nproc` and memory fields, what most plausibly explains the measured factor?

## Write in `run11_post/`
`REPORT.md` for the owner: the answers with file and line references or the numbers used, and anything you could not establish. Then `status.json`, one JSON object with exactly these keys, each taking only the listed values:
- `"concurrent_log_problems"`: `"none"`, `"same_as_serial"`, `"new_in_concurrent"`, `"unknown"`
- `"outputs_cover_all_results"`: `"yes"`, `"partly"`, `"unknown"`
- `"shared_writes_purpose"`: `"logs"`, `"scratch"`, `"cache_reused_across_invocations"`, `"intermediate_results"`, `"multiple"`, `"none"`, `"unknown"`
- `"cross_invocation_reads"`: `"no"`, `"yes"`, `"unknown"`
- `"less_work_in_later_invocations"`: `"no"`, `"yes"`, `"unknown"`
- `"order_effect"`: `"none"`, `"later_arms_faster"`, `"later_arms_slower"`, `"mixed"`, `"unknown"`
- `"factor_holds_against_nearest_serial"`: `"yes"`, `"no"`, `"unknown"`
- `"gain_source"`: `"idle_cpu_in_serial_mode"`, `"memory_or_io_overlap"`, `"startup_or_serial_sections"`, `"multiple"`, `"other"`, `"unknown"`

No other keys and no free text.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run11_post/`.
- No fabrication. If something cannot be established, say so in REPORT.md and use the matching status value.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
