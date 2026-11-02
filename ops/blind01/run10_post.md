You are an authorized agent for the blind-01 experiment. The owner authorized you to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values, plus content-free checks; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run10_post/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. Read large directories selectively.

## Background
run10 ran the unit equivalence check (contract: section "Unit equivalence check (U51)" of `/home/hal/dev/interp/metis/dut/pipeline/m5/SCHEMAS.md`). Setup passed, then one invocation of `harness/run_units.sh` ran four sample units in its own working directory, and their result files matched run9's recorded outputs byte for byte (`units_match` true). Its files: `run10/agent/results/reproduce/units_check.json`, `run10/agent/results/reproduce/units-check/` (`run.log`, `wall.json`, `files/`), and the harness in `run10/agent/harness/` (copied from `run10_harness3/`). The reference is `run9/agent/results/reproduce/out/`. `run10_harness3/REPORT.md`, `run10_review3/REPORT.md` and `run10_diff/REPORT.md` describe the unit files and an inherited path-rule conflict: run9's `run_command.sh` (and so `run_units.sh`) already writes outside `out/`.

The next step under consideration is the unit-mode concurrency probe (SCHEMAS.md, bullets beginning "Unit mode (U50)" through the `concurrency.json` bullet): the same four units run in one invocation, as separate invocations one after another, and as two or four separate invocations at once, each invocation in its own work directory made of symbolic links to every top-level entry of the shared run directory plus an empty `out/`, with every unit's output files compared byte for byte.

## Questions
A. Check the equivalence result is not vacuous: were the compared files non-empty, and does the subset's `run.log` show errors or warnings despite exit 0?
B. Prediction 6: `subset_wall_s` against `cost_sum_s` in `units_check.json` (report the bucket of `cost_ratio`).
C. The inherited conflict: exactly what `run_units.sh` (and the program it runs) writes outside the invocation's `out/` and temporary directories, where (resolve each through the work directory's symbolic links), and whether its names are fixed, per unit, or per invocation.
D. Whether two or four concurrent invocations of `run_units.sh` in such work directories would write to or read from the same paths outside `out/`, so that one could change another's results or fail; and whether the probe's byte-for-byte output comparison would detect that.
E. Whether the conflict can be avoided for concurrent invocations without changing the per-unit computation, its parameters or inputs (for example an environment variable or argument the measured command already accepts, or a per-invocation directory), or whether it is harmless as is.

## Write in `run10_post/`
`REPORT.md` for the owner: the answers with file and line references, and anything you could not establish. Then `status.json`, one JSON object with exactly these keys, each taking only the listed values:
- `"compared_files_nonempty"`: `"all"`, `"some_empty"`, `"unknown"`
- `"subset_log_problems"`: `"none"`, `"warnings_only"`, `"errors"`, `"unknown"`
- `"cost_ratio_bucket"`: `"below_0_7"`, `"0_7_to_1_3"`, `"above_1_3"`, `"null"`
- `"outside_out_writes"`: `"none_found"`, `"fixed_paths"`, `"per_unit_paths"`, `"per_invocation_paths"`, `"mixed"`, `"unknown"`
- `"outside_out_location"`: `"temp_dir"`, `"shared_run_directory"`, `"home_or_cache"`, `"multiple"`, `"none"`, `"unknown"`
- `"concurrent_collision"`: `"none"`, `"possible"`, `"likely"`, `"unknown"`
- `"collision_detected_by_byte_check"`: `"yes"`, `"partly"`, `"no"`, `"not_applicable"`, `"unknown"`
- `"avoidable_without_code_change"`: `"yes"`, `"no"`, `"not_needed"`, `"unknown"`
- `"avoidance_kind"`: `"existing_env_or_argument"`, `"per_invocation_directory"`, `"other"`, `"none"`, `"not_applicable"`

No other keys and no free text.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run10_post/`.
- No fabrication. If something cannot be established, say so in REPORT.md and use the matching status value.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
