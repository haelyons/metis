You are an authorized agent for the blind-01 experiment. The owner authorized you to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values, plus content-free checks of the files you write; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run10_harness2/`. Change nothing else (do not edit `run10_harness/` or `run10_review/`), run no workloads, contact no box, fetch nothing from the network, and run no git commands. Some directories under `run9/` are large: measure with `du` or `ls`, and read only the files you need. run9's agent files are under `run9/agent/` (pipeline name `A/`).

## Purpose
`run10_harness/` holds a harness source for the next run: exact copies of `run9/agent/harness/` plus `run_units.sh` and `units.json` for the pipeline's unit-mode concurrency probe. An independent review (`run10_review/REPORT.md` and `status.json`) found that it does not meet the contract: `run_units.sh` differs from `run9/agent/harness/run_command.sh` in its binary or entry point and in output locations, not only in subset selection, and the review could not establish that each listed unit computes exactly what the full run computes for it, or that the script writes only under `out/` or temporary files. Write a corrected harness source that resolves every finding in the review.

The contract is the bullet beginning "Optional unit files (U50)" in `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md` (section "A/harness/"); also the `run_command.sh` rules in that section and the "Unit mode (U50)" bullets under "Concurrency probe". Read the review first, then `run10_harness/REPORT.md`, the earlier readers' reports (`run9_units/`, `run9_outputs/`), the published source and configuration as saved under run9, and run9's reproduce logs and outputs.

## Write in `run10_harness2/`
1. Exact byte copies of every file in `run9/agent/harness/` (`cp -p`), unchanged.
2. `units.json`: copy `run10_harness/units.json` unchanged unless the review found a problem in it; then correct only that.
3. `run_units.sh`: the exact measured command of `run_command.sh` (same binary or entry point, configuration, scale, environment, thread setting, working directory and relative paths), changed only to (a) read unit ids from its arguments and exit nonzero when none is given, and (b) pass them to the published program's own subset option. If the published entry point used by `run_command.sh` cannot select a subset, say so in REPORT.md and choose the published mechanism that runs the same per-unit computation, explaining why it is the same. Each unit's result files must land at the same paths under `out/` as in the full run; write nothing outside `out/` or temporary files; touch no `CUDA_MPS_*` variable; propagate the program's exit status.
4. `run10_harness2/REPORT.md` for the owner: each review finding and how you resolved it, the remaining line-by-line differences between `run_units.sh` and `run_command.sh`, the evidence (source lines) that each listed unit's computation is the same as in the full run, and anything you could not establish.

Do not execute `run_units.sh` or any workload. You may run `bash -n` and `python3 -c` checks.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run10_harness2/`.
- No fabrication. If something cannot be established, say so in REPORT.md and use the matching status value.

## Outputs
`run10_harness2/status.json`, one JSON object with exactly these keys, each taking only the listed values:
- `"copies_written"`: `"yes"`, `"no"`
- `"review_findings_resolved"`: `"all"`, `"some"`, `"none"`
- `"units_json_changed"`: `"yes"`, `"no"`
- `"subset_mechanism"`: `"published_option"`, `"other"`, `"unknown"`
- `"command_differs_only_in_subset"`: `"yes"`, `"no"`, `"unknown"`
- `"same_computation_per_unit"`: `"yes"`, `"no"`, `"unknown"`
- `"writes_only_out_or_temp"`: `"yes"`, `"no"`, `"unknown"`
- `"bash_syntax_ok"`: `"yes"`, `"no"`

No other keys and no free text.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
