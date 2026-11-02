You are an authorized reviewer for the blind-01 experiment. The owner authorized you to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run10_review3/`. Change nothing else (in particular, do not edit any other `run10_*` folder), run no workloads, contact no box, fetch nothing from the network, and run no git commands. Some directories under `run9/` are large: measure with `du` or `ls`, and read only the files you need. run9's agent files are under `run9/agent/` (pipeline name `A/`).

## Purpose
Another agent wrote `run10_harness3/`: exact copies of `run9/agent/harness/` plus two new files, `run_units.sh` and `units.json`, for the pipeline's unit equivalence check and unit-mode concurrency probe. Earlier attempts and readers (`run10_harness/`, `run10_harness2/`, `run10_review/`, `run10_review2/`, `run10_why/`, `run10_mech/`, `run10_inputs/`, `run10_diff/`) established that the entry point's command-line selector has no effect and that the measured command reads a prepared input list whose path it already accepts. The owner decided to allow selecting original prepared input records, retaining the measured baseline's per-unit code, parameters and inputs, including run9's documented repairs; the reference is the measured baseline, not the pristine upstream program, and a path-rule conflict `run_command.sh` already has is judged separately as inherited. The contract (amended) also includes the section "Unit equivalence check (U51)". Review `run10_harness3/` independently whether the two new files meet the contract and whether, for each listed unit, `run_units.sh` makes the program compute exactly what `run_command.sh` computes for that unit. Read `run10_harness3/REPORT.md`, `run10_diff/REPORT.md` and the earlier reviews, but check every claim against the files themselves, the published source and configuration as saved under run9, and run9's reproduce logs and outputs (`run9/agent/results/reproduce/`). Earlier readers' reports (`run9_units/`, `run9_outputs/`) describe the units and outputs.

## Questions
1. Line by line, how does `run_units.sh` differ from `run9/agent/harness/run_command.sh`? Classify each difference: argument handling (reading ids, failing without ids), subset selection through the published option, log or message text, log file locations, output locations, environment variables, thread setting, configuration or scale, binary or entry point, working directory, other.
2. For a listed unit, does the program run with the same binary, configuration, inputs, scale, environment and thread setting as under `run_command.sh`, so that its result files would be byte-identical to the full run's?
3. Does `run_units.sh` write anywhere other than `out/` or temporary files, use absolute paths into the run directory, or touch any `CUDA_MPS_*` variable?
4. Does `units.json` list every unit of the full run, in the full run's order, with ids the published option accepts, only that unit's own result files (never a combined summary, log or shared file), and costs that match the unit's own seconds recorded in run9's reproduce outputs or logs?
5. Is the restricted list built only from original records, copied byte for byte in the list's own format, and passed through an input the measured command already accepts, with no new code change?
6. Does `run_command.sh` itself already have a path-rule conflict (inherited), and do the unit files add any?
7. Is anything else in the amended contract unmet?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run10_review3/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run10_review3/REPORT.md` for the owner with the evidence (file paths, line numbers, code and log lines), separating measured, read from code or documents, and inferred, and, if a fix is needed, exactly what to change.
2. `run10_review3/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"diff_argument_handling"`, `"diff_subset_selection"`, `"diff_messages_or_log_paths"`, `"diff_output_locations"`, `"diff_environment"`, `"diff_thread_setting"`, `"diff_configuration_or_scale"`, `"diff_binary_or_entry"`, `"diff_working_directory"`, `"diff_other"`: each `"yes"` or `"no"`
   - `"same_computation_per_unit"`: `"yes"`, `"no"`, `"unknown"`
   - `"writes_only_out_or_temp"`: `"yes"`, `"no"`, `"unknown"`
   - `"mps_untouched"`: `"yes"`, `"no"`
   - `"units_complete_and_ordered"`: `"yes"`, `"no"`, `"unknown"`
   - `"outputs_own_files_only"`: `"yes"`, `"no"`, `"unknown"`
   - `"costs_match_records"`: `"yes"`, `"no"`, `"unknown"`
   - `"restricted_list_faithful"`: `"yes"`, `"no"`, `"not_applicable"`, `"unknown"`
   - `"inherited_path_conflict"`: `"yes"`, `"no"`, `"unknown"`
   - `"unit_files_add_path_conflict"`: `"no"`, `"yes"`, `"unknown"`
   - `"contract_met"`: `"yes"`, `"no"`, `"unknown"`
   - `"verdict"`: `"usable"`, `"needs_fix"`, `"unknown"`

   No other keys and no free text.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
