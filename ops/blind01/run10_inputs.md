You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run10_inputs/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. run9's agent files are under `run9/agent/` (pipeline name `A/`). Read large directories selectively.

## Purpose
`run10_why/` found that the entry point used by `run9/agent/harness/run_command.sh` has no published option to run only some units, and `run10_mech/` found that `run10_harness2/run_units.sh` runs modified per-unit code. Read those folders and `run10_review2/` first. The operator will not use modified per-unit code. One route remains unchecked: running the same published entry point with unmodified code, the same configuration otherwise, and only the chosen units as its inputs, by restricting what it reads (for example an input list in its configuration, the contents of the input directory it scans, or input paths it takes on its command line), with any restricted input set built from links or copies under `out/` or a temporary directory. Establish neutrally whether that route exists and is faithful.

## Questions
1. Can the entry point used by `run_command.sh`, with unmodified code, run only chosen units by restricting its inputs or configuration? If so, how: an input list in its configuration, the contents of a directory it scans, input paths on its command line, or other?
2. With that restriction, would each chosen unit run exactly the published per-unit code with the same configuration and scale, and write its own result files at the same paths under `out/` as in the full run?
3. Could restricting the input set change any unit's own computation or result files: normalisation or statistics across inputs, a shared random stream or seed that depends on the input set or order, ordering, caching, or anything else?
4. Can this be written as a `run_units.sh` that obeys every `run_command.sh` rule in `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md` ("A/harness/": relative paths, writes only under `out/` or temporary files, no `CUDA_MPS_*` changes, exit status propagated), changing only the input or configuration selection and nothing else about the command?
5. Would the configuration or input files it needs differ from the published ones in anything other than the list of units?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run10_inputs/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run10_inputs/REPORT.md` for the owner with the evidence (file paths, line numbers, code and configuration lines), separating measured, read from code or documents, and inferred, and, if the route exists, exactly how `run_units.sh` would do it.
2. `run10_inputs/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"restriction_possible"`: `"yes"`, `"no"`, `"unknown"`
   - `"restriction_kind"`: `"config_input_list"`, `"scanned_directory"`, `"command_line_inputs"`, `"other"`, `"none"`
   - `"published_code_unmodified"`: `"yes"`, `"no"`, `"not_applicable"`
   - `"same_paths"`: `"yes"`, `"no"`, `"not_applicable"`, `"unknown"`
   - `"restriction_changes_computation"`: `"no"`, `"yes"`, `"not_applicable"`, `"unknown"`
   - `"harness_rules_satisfiable"`: `"yes"`, `"no"`, `"not_applicable"`, `"unknown"`
   - `"config_differs_only_in_units"`: `"yes"`, `"no"`, `"not_applicable"`, `"unknown"`

   No other keys and no free text.

Finish within 15 minutes. End with a final reply that is exactly the contents of status.json.
