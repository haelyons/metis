You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run10_why/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. run9's agent files are under `run9/agent/` (pipeline name `A/`). Read large directories selectively.

## Purpose
Two attempts at harness unit files for the next run's unit-mode concurrency probe were each reviewed independently and judged `needs_fix`: `run10_harness/` (review `run10_review/`) and the correction `run10_harness2/` (review `run10_review2/`). Read all four folders' REPORT.md and status.json. The contract is the bullet beginning "Optional unit files (U50)" in `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md` (section "A/harness/") together with the `run_command.sh` rules there and the "Unit mode (U50)" bullets under "Concurrency probe". Earlier readers (`run9_units/`, `run9_outputs/`) reported that the published program selects a subset of units through a published option taking safe identifiers as arguments; the corrected writer reported its subset mechanism as "other". Establish, neutrally and from the files themselves, why `run10_harness2/` still fails the contract, whether that can be fixed in the harness, and what the probe's own checks would catch. The probe runs four units through `run_units.sh` in one invocation first and compares every listed output file byte for byte with run9's frozen reproduce outputs; if any differs, it stops there.

## Questions
1. Which contract requirement does `run10_harness2/` fail, if any (choose the most important): the subset mechanism is not the published program's own option; the per-unit computation may differ from the full run; it may write outside `out/` or temporary files; exit status not propagated; ids not checked; output paths differ from the full run; something in `units.json`; other; none?
2. Does the entry point used by `run9/agent/harness/run_command.sh` itself offer a published way to run only some units, and if not, does another published entry point of the same program run the same per-unit computation?
3. Can the remaining problem be fixed by editing only `run_units.sh` or `units.json`?
4. If `run10_harness2/` were used as is, would a wrong per-unit computation make the probe's byte-for-byte comparison with the frozen outputs fail (so the run would stop at that check), or could the outputs match while the computation still differs?
5. If used as is, what is the realistic risk: none, a wasted run (the probe stops at its baseline check or fails), a misleading result (a factor that does not describe the baseline's own computation), or unknown?
6. Why do the reviews leave `same_computation_per_unit` and `writes_only_out_or_temp` as unknown: missing evidence that static reading cannot supply, or a concrete problem?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run10_why/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run10_why/REPORT.md` for the owner with the evidence (file paths, line numbers, code and log lines), separating measured, read from code or documents, and inferred, and the smallest fix if one is needed.
2. `run10_why/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"failed_requirement"`: `"subset_not_published_option"`, `"computation_may_differ"`, `"may_write_outside_out"`, `"exit_status"`, `"id_check"`, `"output_paths"`, `"units_json"`, `"other"`, `"none"`
   - `"entry_point_has_subset_option"`: `"yes"`, `"no"`, `"unknown"`
   - `"other_published_entry_same_computation"`: `"yes"`, `"no"`, `"not_needed"`, `"unknown"`
   - `"fixable_in_unit_files"`: `"yes"`, `"no"`, `"unknown"`
   - `"probe_check_catches_wrong_computation"`: `"yes"`, `"no"`, `"partly"`, `"unknown"`
   - `"risk_if_used_as_is"`: `"none"`, `"wasted_run"`, `"misleading_result"`, `"unknown"`
   - `"unknowns_reason"`: `"static_reading_limit"`, `"concrete_problem"`, `"both"`, `"unknown"`

   No other keys and no free text.

Finish within 15 minutes. End with a final reply that is exactly the contents of status.json.
