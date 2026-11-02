You are an authorized reviewer for the blind-01 experiment. The owner authorized you to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run10_review2/`. Change nothing else (in particular, do not edit `run10_harness/`, `run10_harness2/` or `run10_review/`), run no workloads, contact no box, fetch nothing from the network, and run no git commands. Some directories under `run9/` are large: measure with `du` or `ls`, and read only the files you need. run9's agent files are under `run9/agent/` (pipeline name `A/`).

## Purpose
Another agent wrote `run10_harness2/`: exact copies of `run9/agent/harness/` plus two new files, `run10_harness2/run_units.sh` and `units.json`, for the pipeline's unit-mode concurrency probe. It corrects an earlier attempt (`run10_harness/`) that a first review (`run10_review/`) found did not meet the contract. The contract is the bullet beginning "Optional unit files (U50)" in `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md` (section "A/harness/"); also read the `run_command.sh` rules in that section and the "Unit mode (U50)" bullets under "Concurrency probe". Review `run10_harness2/` independently whether the two new files meet the contract and whether, for each listed unit, `run_units.sh` makes the program compute exactly what `run_command.sh` computes for that unit. Read `run10_harness2/REPORT.md` and the first review, but check every claim against the files themselves, the published source and configuration as saved under run9, and run9's reproduce logs and outputs (`run9/agent/results/reproduce/`). Earlier readers' reports (`run9_units/`, `run9_outputs/`) describe the units and outputs.

## Questions
1. Line by line, how does `run_units.sh` differ from `run9/agent/harness/run_command.sh`? Classify each difference: argument handling (reading ids, failing without ids), subset selection through the published option, log or message text, log file locations, output locations, environment variables, thread setting, configuration or scale, binary or entry point, working directory, other.
2. For a listed unit, does the program run with the same binary, configuration, inputs, scale, environment and thread setting as under `run_command.sh`, so that its result files would be byte-identical to the full run's?
3. Does `run_units.sh` write anywhere other than `out/` or temporary files, use absolute paths into the run directory, or touch any `CUDA_MPS_*` variable?
4. Does `units.json` list every unit of the full run, in the full run's order, with ids the published option accepts, only that unit's own result files (never a combined summary, log or shared file), and costs that match the unit's own seconds recorded in run9's reproduce outputs or logs?
5. Is anything else in the contract unmet?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run10_review2/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run10_review2/REPORT.md` for the owner with the evidence (file paths, line numbers, code and log lines), separating measured, read from code or documents, and inferred, and, if a fix is needed, exactly what to change.
2. `run10_review2/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"diff_argument_handling"`, `"diff_subset_selection"`, `"diff_messages_or_log_paths"`, `"diff_output_locations"`, `"diff_environment"`, `"diff_thread_setting"`, `"diff_configuration_or_scale"`, `"diff_binary_or_entry"`, `"diff_working_directory"`, `"diff_other"`: each `"yes"` or `"no"`
   - `"same_computation_per_unit"`: `"yes"`, `"no"`, `"unknown"`
   - `"writes_only_out_or_temp"`: `"yes"`, `"no"`, `"unknown"`
   - `"mps_untouched"`: `"yes"`, `"no"`
   - `"units_complete_and_ordered"`: `"yes"`, `"no"`, `"unknown"`
   - `"outputs_own_files_only"`: `"yes"`, `"no"`, `"unknown"`
   - `"costs_match_records"`: `"yes"`, `"no"`, `"unknown"`
   - `"contract_met"`: `"yes"`, `"no"`, `"unknown"`
   - `"verdict"`: `"usable"`, `"needs_fix"`, `"unknown"`

   No other keys and no free text.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
