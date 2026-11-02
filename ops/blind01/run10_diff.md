You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run10_diff/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. run9's agent files are under `run9/agent/` (pipeline name `A/`). Read large directories selectively.

## Purpose
Readers `run10_why/`, `run10_mech/` and `run10_inputs/` (read their REPORT.md and status.json first, and `run10_review2/`, `run10_harness2/`) reported that subsetting run9's measured baseline needs modified code (`per_unit_code_unmodified: no`, `published_code_unmodified: no`) and that an input-list restriction cannot satisfy the harness rules. The owner suspects two comparisons were conflated: differences from the pristine upstream program that are already present in run9's measured baseline (documented setup or anchors repairs, harness choices) versus additional changes that subsetting itself would require. The owner will permit a narrow contract change allowing selection of original prepared input records, while retaining the measured baseline's own per-unit code, parameters and inputs, and will judge any path-rule conflict that run9's baseline already has separately from one subsetting would add. The reference for every comparison is the recorded run9 baseline, with its existing limits, not the pristine upstream program.

Read run9's harness (`run9/agent/harness/`), the setup and anchors logs and repair records under `run9/agent/results/reproduce/`, the published source and configuration as installed or saved under run9, and the files the measured command reads.

## Questions
1. Does run9's measured baseline already differ from the pristine upstream program: only configuration or environment, patches to source, both, or none?
2. For `run10_harness2/`: is the per-unit code difference that `run10_mech` reported inherited from run9's measured baseline, newly introduced for subsetting, or both?
3. For `run10_inputs/`: is the code difference behind `published_code_unmodified: no` inherited from run9's measured baseline, newly introduced for subsetting, or both?
4. The entry point's command-line selector: does it exist and work, exist but have no effect on which units run (for example overridden by a prepared list or configuration), or not exist?
5. Does run9's measured baseline read a prepared list of input records (a file) that determines which units run?
6. Can the measured baseline, without any code change, be pointed at a list file under the invocation's own `out/` or a temporary directory, through an argument, configuration value or environment variable it already accepts? Or is the list read from a fixed path inside the published tree?
7. Can a restricted list consist only of original prepared records, copied byte for byte from the full list in the same format?
8. Does run9's measured `run_command.sh` itself already write inside the published tree or anywhere other than `out/` or temporary files (an inherited conflict with the harness rules)?
9. Would the restricted-list route add a write inside the published tree, beyond anything run9 already does?
10. Could running only selected records change any selected unit's own computation or result files (statistics across records, a seed or random stream depending on the set or order, ordering, caching)? On what basis: code, inference, or none?
11. What evidence shows that two full runs give byte-identical per-unit result files: two runs actually compared (for example run9's anchors attempts, or run9 against an earlier run), code reading only, or none?
12. Overall: does a route exist that selects original prepared input records, retains the measured baseline's per-unit code, parameters and inputs, and adds no new code change?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run10_diff/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run10_diff/REPORT.md` for the owner with the evidence (file paths, line numbers, code, configuration and log lines), separating measured, read from code or documents, and inferred. If the route exists, describe exactly how a `run_units.sh` would use it and what, if anything, it would write outside `out/` or temporary files.
2. `run10_diff/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"baseline_vs_upstream"`: `"none"`, `"config_or_environment"`, `"source_patches"`, `"both"`, `"unknown"`
   - `"harness2_change_origin"`: `"inherited"`, `"new_for_subsetting"`, `"both"`, `"unknown"`
   - `"inputs_change_origin"`: `"inherited"`, `"new_for_subsetting"`, `"both"`, `"unknown"`
   - `"cli_selector"`: `"effective"`, `"present_ineffective"`, `"absent"`, `"unknown"`
   - `"prepared_list_read"`: `"yes"`, `"no"`, `"unknown"`
   - `"list_redirectable"`: `"yes"`, `"no_fixed_path"`, `"not_applicable"`, `"unknown"`
   - `"restricted_list_original_records"`: `"yes"`, `"no"`, `"not_applicable"`, `"unknown"`
   - `"inherited_path_conflict"`: `"yes"`, `"no"`, `"unknown"`
   - `"route_adds_path_conflict"`: `"yes"`, `"no"`, `"not_applicable"`, `"unknown"`
   - `"selection_affects_unit_results"`: `"no"`, `"yes"`, `"unknown"`
   - `"selection_effect_basis"`: `"code"`, `"inferred"`, `"none"`
   - `"full_run_repeatability_basis"`: `"two_runs_compared"`, `"code_reading"`, `"none"`
   - `"narrow_route_exists"`: `"yes"`, `"no"`, `"unknown"`

   No other keys and no free text.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
