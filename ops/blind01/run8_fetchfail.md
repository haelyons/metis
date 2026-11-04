You are an authorized reader for the blind-02 experiment. The owner authorized readers to see its brief and records. The operator who launched you sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-02/m5/ of the metis repository (the current directory). Write only into `run8_fetchfail/`. Read-only otherwise: change nothing else (above all nothing under `run7/`, `run8/` or `../science/`), run no workloads, contact no box, fetch nothing from the network, run no git commands.

## What the operator knows (metadata only)
run8 is science step s28's fixture rerun, a sealed comparison (`args.comparison`; contract `/home/hal/dev/interp/metis/dut/pipeline/m5/SCHEMAS.md`, section "Sealed comparison (U57, U58)", "Separated users" step 5). It ran on a `gpu_1x_h100_pcie`. Intake and reproduce passed (setup rc 2, then rc 1, then rc 0 after two harness repairs). Evaluate failed with `error_class` infra at its second box command, `comparison-users` (rc 1 after 32 s), before any invocation; that command's log holds the pipeline's fixed message `fetch_private.sh exited <rc>`. In run7 (s27's fixture run, a different harness) the same step passed. The step runs `harness/fetch_private.sh` as the part user `cmp-eval` (`sudo -n -u cmp-eval -- env -i ...`) with working directory `cmp-private` and `HOME` and `TMPDIR` set to `cmp-private/.home`; only `cmp-arm` has the network rule. The operator must decide whether the cause is s28's harness or design (then a science step changes it), the source of the private data, or the comparison mechanism (then the pipeline is fixed and the failure reproduced on a public shakedown run first).

## Read
- `run8/args.json`, `run8/pipeline.log`, `run8/control/` (receipts, `box.json`), and under `run8/agent/`: the harness files (above all `fetch_private.sh`, `setup.sh` and the repairs' records), and the evaluate stage's fetched logs, above all the `comparison-users` log
- the same files of `run7/` for comparison
- `../science/s27/` and `../science/s28/` (their designs and briefs)
- the pipeline code, read-only: `/home/hal/dev/interp/metis/dut/pipeline/m5/` (`cmp_users.sh`, `cmp_wrap.py`, `pipeline.js`, `boxrun.sh`, `SCHEMAS.md`)

## Questions
A. Why did `fetch_private.sh` exit nonzero? Quote its exit code and the decisive log lines.
B. Is the cause in the harness script, the source of the private data, the comparison mechanism (what `cmp_users.sh` gives `cmp-eval`: environment, `PATH`, `HOME`, `TMPDIR`, groups, file permissions, network) or the box? If the mechanism, name file and line, and say whether the contract requires that behaviour.
C. Is run8's `fetch_private.sh` the same as run7's? Did a harness repair change it?
D. What should happen next?

## Write in `run8_fetchfail/`
`REPORT.md` for the owner: the answers with file and line references. Then `status.json`, one JSON object with exactly these keys, each taking only the listed values:
- `"fetch_failure"`: `"network_unreachable"`, `"source_missing_or_moved"`, `"missing_tool_or_package"`, `"permission_denied"`, `"environment_variable"`, `"script_error"`, `"timeout"`, `"other"`
- `"caused_by"`: `"harness_script"`, `"comparison_mechanism"`, `"source"`, `"box_or_environment"`, `"unknown"`
- `"mechanism_defect"`: `"none"`, `"suspected"`, `"confirmed"`
- `"contract_requires_behaviour"`: `"yes"`, `"no"`, `"not_applicable"`
- `"same_script_in_run7"`: `"yes"`, `"no"`, `"unknown"`
- `"harness_repairs_touched_fetch"`: `"yes"`, `"no"`, `"unknown"`
- `"next"`: `"rerun_unchanged"`, `"rerun_after_design_change"`, `"pipeline_fix_first"`, `"public_reproduction_first"`, `"unknown"`

No other keys and no free text in `status.json`. Finish within 30 minutes.
