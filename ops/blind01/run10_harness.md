You are an authorized agent for the blind-01 experiment. The owner authorized you to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values, plus content-free checks of the files you write; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run10_harness/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. Some directories under `run9/` are large: measure with `du` or `ls`, and read only the files you need (logs by head, tail or grep).

## Purpose
The next run reuses run9's harness (`args.harness_from`) and adds two optional harness files so that the pipeline's unit-mode concurrency probe can run a few units of the measured command serially and concurrently. You write that harness source directory. The contract is the bullet beginning "Optional unit files (U50)" in `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md` (section "A/harness/"); read it and the "Unit mode (U50)" bullets in its "Concurrency probe" section, and the `run_command.sh` rules in "A/harness/". Earlier readers' reports (`run9_units/`, `run9_outputs/`, `run9_par/`) describe the units, the published subset option, per-unit output files and recorded costs: read them first.

## Write in `run10_harness/`
1. Exact byte copies of every file in `run9/A/harness/` (`cp -p`), unchanged. Do not edit them.
2. `units.json` exactly as the contract states: `{"units": [...]}` listing every unit of run9's measured command, in the order the full run processes them, each `{id, outputs, cost_s}`. `id` is the identifier the published subset option takes. `outputs` lists only that unit's own result files, relative to `out/`, at the paths the full run wrote them; never the combined summary, logs or any file shared by several units. Every listed path must exist in `run9/A/results/reproduce/out/` (these files equal the frozen baseline outputs). `cost_s` is the unit's own seconds from run9's reproduce logs or outputs (the successful anchors run).
3. `run_units.sh` exactly as the contract states: the exact measured command and environment of `run9/A/harness/run_command.sh`, restricted to the unit ids given as arguments through the published program's own subset option, in the order given. Change nothing else about the command: same binary, configuration, scale, environment, thread setting, working-directory conventions and relative paths; write only under `out/` or temporary files; set or unset no `CUDA_MPS_*` variable; exit nonzero when no id is given; propagate the program's exit status. Each unit's result files must land at the same paths under `out/` as in the full run.
4. `run10_harness/REPORT.md` for the owner: how you derived each part (file paths, code and log lines), how the subset option is invoked, the differences between `run_units.sh` and `run_command.sh` line by line, and anything you could not establish.

Do not execute `run_units.sh` or any workload. You may run `bash -n` on scripts and `python3 -c` to check that `units.json` parses and that its paths exist.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run10_harness/`.
- No fabrication. If something cannot be established, say so in REPORT.md and use the matching status value.

## Outputs
`run10_harness/status.json`, one JSON object with exactly these keys, each taking only the listed values:
- `"copies_written"`: `"yes"`, `"no"`
- `"units_listed"`: `"all_units"`, `"some_units"`, `"none"`
- `"outputs_exist_in_reproduce"`: `"all"`, `"some"`, `"none"`
- `"outputs_per_unit_only"`: `"yes"`, `"no"`, `"unknown"`
- `"cost_source"`: `"reproduce_logs"`, `"reproduce_outputs"`, `"mixed"`, `"unknown"`
- `"subset_mechanism"`: `"published_option"`, `"other"`, `"unknown"`
- `"command_differs_only_in_subset"`: `"yes"`, `"no"`, `"unknown"`
- `"bash_syntax_ok"`: `"yes"`, `"no"`

No other keys and no free text.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
