You are an authorized agent for the blind-01 experiment. The owner authorized you to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values, plus content-free checks of the files you write; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run10_harness3/`. Change nothing else (do not edit any other `run10_*` folder), run no workloads, contact no box, fetch nothing from the network, and run no git commands. run9's agent files are under `run9/agent/` (pipeline name `A/`). Read large directories selectively.

## Purpose
The next run first tests unit equivalence: it runs four units through `run_units.sh` once and compares each unit's own result files byte for byte with run9's recorded outputs (`run9/agent/results/reproduce/out/`). Earlier attempts (`run10_harness/`, `run10_harness2/`) and the readers `run10_review/`, `run10_review2/`, `run10_why/`, `run10_mech/`, `run10_inputs/` and `run10_diff/` established that the entry point's command-line selector has no effect, and that the measured command reads a prepared input list whose path it already accepts. Read them all first, especially `run10_diff/REPORT.md`. The contract is now the bullet beginning "Optional unit files (U50)" in `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md` (section "A/harness/"), as amended by the owner's decision; also read the `run_command.sh` rules there and the section "Unit equivalence check (U51)". The reference is the measured baseline as run9 ran it, including its documented repairs, not the pristine upstream program.

## Write in `run10_harness3/`
1. Exact byte copies of every file in `run9/agent/harness/` (`cp -p`), unchanged.
2. `units.json` exactly as the contract states, listing every unit of the full run in its order. Reuse `run10_harness/units.json` if its ids identify each unit's record in the prepared input list and its outputs and costs remain correct; otherwise write it anew. `outputs` lists only each unit's own result files (never a combined summary, log or shared file), all present in `run9/agent/results/reproduce/out/`.
3. `run_units.sh`: the exact measured command of `run9/agent/harness/run_command.sh`, changed only to (a) read unit ids from its arguments and exit nonzero when none is given, (b) build, under `out/` or a temporary directory, a restricted copy of the prepared input list holding only the listed units' original records, copied byte for byte from the list the measured command reads, in its own format and in the order given, and (c) pass that list's path through the argument, configuration value or environment variable the measured command already accepts for it. Retain the measured baseline's per-unit code, parameters, inputs, binary, configuration, scale, environment, thread setting and working directory exactly; make no code change; write nothing outside `out/` or temporary files beyond what `run_command.sh` itself already does; touch no `CUDA_MPS_*` variable; propagate the program's exit status. Each unit's result files must land at the same paths under `out/` as in the full run.
4. `run10_harness3/REPORT.md` for the owner: how the restricted list is built and passed (source lines), the line-by-line differences between `run_units.sh` and `run_command.sh`, any path-rule conflict `run_command.sh` already has (inherited, listed separately), and anything you could not establish.

Do not execute `run_units.sh` or any workload. You may run `bash -n` and `python3 -c` checks, including a check that the restricted list built for four sample ids would consist only of byte-identical original records.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run10_harness3/`.
- No fabrication. If something cannot be established, say so in REPORT.md and use the matching status value.

## Outputs
`run10_harness3/status.json`, one JSON object with exactly these keys, each taking only the listed values:
- `"copies_written"`: `"yes"`, `"no"`
- `"selection_route"`: `"restricted_prepared_list"`, `"published_selector"`, `"other"`
- `"list_records_original"`: `"yes"`, `"no"`, `"unknown"`
- `"list_passed_via_existing_input"`: `"yes"`, `"no"`, `"unknown"`
- `"new_code_change"`: `"no"`, `"yes"`
- `"command_differs_only_in_selection"`: `"yes"`, `"no"`, `"unknown"`
- `"adds_writes_outside_out"`: `"no"`, `"yes"`, `"unknown"`
- `"inherited_path_conflict"`: `"yes"`, `"no"`, `"unknown"`
- `"units_json_reused"`: `"yes"`, `"no"`
- `"bash_syntax_ok"`: `"yes"`, `"no"`

No other keys and no free text.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
