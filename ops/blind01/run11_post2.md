You are an authorized agent for the blind-01 experiment. The owner authorized you to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values, plus content-free checks; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run11_post2/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. Read large directories selectively.

## Background
run11 ran the standalone unit probe (contract: section "Standalone unit probe (U52)" and the "Concurrency probe" bullets from "Unit mode (U50b)" through "The standalone unit probe (U52) validates" in `/home/hal/dev/interp/metis/dut/pipeline/m5/SCHEMAS.md`; probe script `/home/hal/dev/interp/metis/dut/pipeline/m5/concurrency_probe.py`). Eight arms ran the same four sample units serially, separately and two or four at once; all exited 0 and every compared output was byte-identical, with throughput factors of about 1.56 (two at once) and 2.3 (four at once). Files: `run11/agent/results/reproduce/out/concurrency/` (`concurrency.json`, `logs/`), `run11/agent/results/reproduce/units_reference.json`, `run11/agent/harness/` (`run_units.sh`, `units.json`, `run_command.sh`), run9's recorded outputs and logs in `run9/agent/results/reproduce/`, and run10's subset files in `run10/agent/results/reproduce/units-check/`. The work directories' output files stayed on the box, which is terminated; only the shared run directory's `out/` was fetched.

An earlier reader (`run11_post/REPORT.md`) found two things this reader must characterise: the concurrent invocations' logs show errors or warnings the serial invocations' logs do not, and the compared output paths cover only some of each unit's result files.

## Questions
A. The new messages in the concurrent logs: what are they, what produces them, and could they change any result file, compared or not? Do the same messages appear in run9's full-run logs, run10's subset log, or the serial and separate (`a-*`, `b-*`) logs of run11?
B. The result files that are not compared: which kinds of file are they, do they hold results the published analysis uses, and would they differ between two identical runs anyway (for example timings or run-specific content)?
C. Do the compared files hold every scientific result each unit produces, so that byte-identity of the compared files means the units computed the same results?
D. Could `units.json`'s output lists be extended to cover the uncompared result files without changing the measured command, its parameters or inputs, and would those files be byte-comparable?

## Write in `run11_post2/`
`REPORT.md` for the owner: the answers with file and line references, and anything you could not establish. Then `status.json`, one JSON object with exactly these keys, each taking only the listed values:
- `"concurrent_message_kind"`: `"resource_or_thread_limits"`, `"shared_path_collision"`, `"numerical_or_convergence"`, `"timing_or_progress"`, `"library_warning"`, `"multiple"`, `"other"`, `"unknown"`
- `"concurrent_messages_affect_results"`: `"no"`, `"yes"`, `"unknown"`
- `"concurrent_messages_seen_before"`: `"yes"`, `"partly"`, `"no"`, `"unknown"`
- `"uncompared_files_kind"`: `"logs_or_timing"`, `"run_metadata"`, `"scientific_results"`, `"multiple"`, `"none"`, `"unknown"`
- `"uncompared_files_used_in_analysis"`: `"no"`, `"yes"`, `"unknown"`
- `"uncompared_files_run_specific"`: `"yes"`, `"no"`, `"partly"`, `"unknown"`
- `"compared_files_hold_all_scientific_results"`: `"yes"`, `"no"`, `"unknown"`
- `"coverage_extendable_without_code_change"`: `"yes"`, `"no"`, `"not_needed"`, `"unknown"`

No other keys and no free text.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run11_post2/`.
- No fabrication. If something cannot be established, say so in REPORT.md and use the matching status value.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
