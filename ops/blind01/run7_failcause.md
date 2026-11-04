You are an authorized reader for the blind-02 experiment. The owner authorized readers to see its brief and records. The operator who launched you sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-02/m5/ of the metis repository (the current directory). Write only into `run7_failcause/`. Read-only otherwise: change nothing else (above all nothing under `run7/` or `../science/`), run no workloads, contact no box, fetch nothing from the network, run no git commands.

## What the operator knows (metadata only)
run7 is science step s27's fixture run, a sealed comparison (`args.comparison`; contract `/home/hal/dev/interp/metis/dut/pipeline/m5/SCHEMAS.md`, section "Sealed comparison (U57, U58)"). It ran on a `gpu_1x_a10` (no H100 or A100 capacity). Intake, reproduce and evaluate passed. Evaluate receipts: `comparison-users` rc 0, then 13 invocations, each a `comparison-job` (23 to 31 s) and a `comparison` (945 to 989 s for the first 12, 732 s for the last), all rc 0 and none timed out, then the evaluate budget (12,600 s) was spent. Science step s28 (`../science/s28/`) reports that every invocation failed, no fixture value is usable, no isolation concern, and asks for a fixture rerun of the same shape with `budget_s` 16,200, projected 3 to 6 h. The operator must decide whether a rerun can succeed or whether the pipeline needs a fix first. The comparison mechanism was proven on a box only with a trivial public probe (`/home/hal/dev/interp/metis/experiments/shakedown-m5/cmp20/`, run `shakedown-m5/run20`), whose parts did almost no work.

## Read
- `run7/args.json`, `run7/pipeline.log`, `run7/control/` (receipts, `box.json`, `comparison.json`), and under `run7/agent/`: the harness files and adapters, `results/evaluate/comparison_compute.json`, each invocation's `wrap.json`, `log/` and fetched outputs (read large directories selectively)
- `../science/s27/` and `../science/s28/` (assessments, design files, briefs)
- the pipeline code, read-only: `/home/hal/dev/interp/metis/dut/pipeline/m5/` (`cmp_wrap.py`, `cmp_users.sh`, `comparison.js`, `pipeline.js`, `boxrun.sh`, `SCHEMAS.md`)

## Questions
A. Why did each invocation fail? Give the status and exit or timeout facts of every invocation from its `wrap.json` and the decisive log lines.
B. Is the cause in the design or harness (the arm commands, timeouts, inputs), in the comparison mechanism (the part users, their permissions, network rule, device access, environment, HOME or TMPDIR, the wrapper), or in the box or its environment? If the mechanism, name the file and line and what it does that the arm needed otherwise, and whether the contract requires that behaviour.
C. Does s28's rerun design change what caused the failures? Would it fit its budget with every planned invocation at the cost run7 measured, on an A10 and on an H100?
D. Can a rerun succeed as s28 designed it, or only after a pipeline fix or a design change?

## Write in `run7_failcause/`
`REPORT.md` for the owner: the answers with file and line references. Then `status.json`, one JSON object with exactly these keys, each taking only the listed values:
- `"invocation_failure"`: `"arm_timeout"`, `"arm_command_error"`, `"arm_missing_dependency"`, `"arm_output_missing"`, `"evaluator_error"`, `"wrapper_or_pipeline"`, `"mixed"`, `"other"`
- `"failure_caused_by"`: `"design_or_harness"`, `"comparison_mechanism"`, `"box_or_environment"`, `"mixed"`, `"unknown"`
- `"mechanism_defect"`: `"none"`, `"suspected"`, `"confirmed"`
- `"s28_design_addresses_cause"`: `"yes"`, `"partly"`, `"no"`, `"unknown"`
- `"s28_fits_budget"`: `"yes"`, `"at_risk"`, `"no"`, `"unknown"`
- `"rerun_justified"`: `"yes"`, `"after_pipeline_fix"`, `"after_design_change"`, `"no"`

No other keys and no free text in `status.json`. Finish within 30 minutes.
