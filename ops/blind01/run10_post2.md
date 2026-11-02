You are an authorized agent for the blind-01 experiment. The owner authorized you to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values, plus content-free checks; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run10_post2/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. Read large directories selectively.

## Background
run10 ran the unit equivalence check (section "Unit equivalence check (U51)" of `/home/hal/dev/interp/metis/dut/pipeline/m5/SCHEMAS.md`): one invocation of `harness/run_units.sh` ran four sample units in its own working directory (symbolic links to every top-level entry of the shared run directory plus an empty `out/`); it exited 0 and the four units' result files matched run9's recorded outputs (`run9/agent/results/reproduce/out/`) byte for byte. The previous reader, `run10_post/` (read its REPORT.md first), found the files non-empty, but reported errors in the subset's `run.log` (`run10/agent/results/reproduce/units-check/run.log`), a possible collision between concurrent invocations in the shared run directory, and that it could not establish which paths outside `out/` are written. Also read `run10_harness3/REPORT.md`, `run10_diff/REPORT.md` and the harness in `run10/agent/harness/`. run9's own logs are under `run9/agent/results/reproduce/`.

## Questions
A. The errors in the subset's log: what kind are they, do the same errors appear in run9's full-run logs for the same units (or for every unit), do they come from record selection, the separate working directory and its links, the path conflict, the environment or setup, or the program itself as a non-fatal message; and could they affect the compared result files?
B. Was each of the four sample units actually computed by the subset invocation, and were the compared files written by it (not copied or linked from elsewhere)?
C. Every path the invocation writes outside its own `out/` and temporary directories (resolve through the links): fixed names, per unit or per invocation; their purpose (scratch, a cache reused across units, intermediate results, logs); whether a later unit reads what an earlier one wrote there.
D. Whether giving each concurrent invocation its own copy of only those written locations (instead of a link to the shared one), with everything else still linked, would leave the per-unit computation, its parameters and inputs unchanged.

## Write in `run10_post2/`
`REPORT.md` for the owner: the answers with file and line references, and anything you could not establish. Then `status.json`, one JSON object with exactly these keys, each taking only the listed values:
- `"subset_errors_vs_run9"`: `"also_in_run9"`, `"only_in_subset"`, `"mixed"`, `"no_errors"`, `"unknown"`
- `"subset_error_source"`: `"program_nonfatal"`, `"environment_or_setup"`, `"selection_or_restricted_list"`, `"working_directory_or_links"`, `"path_conflict"`, `"multiple"`, `"other"`, `"unknown"`
- `"errors_affect_compared_outputs"`: `"no"`, `"yes"`, `"unknown"`
- `"units_all_computed"`: `"yes"`, `"no"`, `"unknown"`
- `"outputs_written_by_subset"`: `"yes"`, `"no"`, `"unknown"`
- `"outside_out_naming"`: `"fixed"`, `"per_unit"`, `"per_invocation"`, `"mixed"`, `"none"`, `"unknown"`
- `"outside_out_purpose"`: `"scratch"`, `"cache_reused_across_units"`, `"intermediate_results"`, `"logs"`, `"multiple"`, `"none"`, `"unknown"`
- `"later_units_read_earlier_writes"`: `"no"`, `"yes"`, `"unknown"`
- `"private_copies_preserve_computation"`: `"yes"`, `"no"`, `"not_applicable"`, `"unknown"`

No other keys and no free text.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run10_post2/`.
- No fabrication. If something cannot be established, say so in REPORT.md and use the matching status value.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
