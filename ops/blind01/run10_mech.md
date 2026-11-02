You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run10_mech/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. run9's agent files are under `run9/agent/` (pipeline name `A/`). Read large directories selectively.

## Purpose
`run10_why/` found that the entry point `run9/agent/harness/run_command.sh` uses has no published way to run only some units, that no other published entry point runs the same per-unit computation, and that `run10_harness2/run_units.sh` therefore selects units by another mechanism. Read `run10_why/`, `run10_review2/` and `run10_harness2/` (REPORT.md, status.json, `run_units.sh`) first. The owner must decide whether a probe may use such a mechanism. The probe would run four units through it, first in one invocation, compare each unit's own result files byte for byte with run9's frozen reproduce outputs and stop on any difference, then time the same units as separate invocations in sequence and at once. Describe the mechanism and its relation to the published computation neutrally.

## Questions
1. What is `run10_harness2/run_units.sh`'s mechanism: a call into the same published program's internal functions or modules with the same per-unit code; a lower-level published tool that the entry point itself calls per unit; a modified copy of the published entry point; new code that reimplements per-unit work; or other?
2. Is every line of per-unit computation the mechanism runs the published program's own code, unmodified?
3. Besides per-unit work, what does the published entry point do in a full run (setup, shared preprocessing, combining or selecting results across units, writing summaries)? What share of the full run's wall time is that, from run9's logs or outputs: none, under 5%, 5 to 25%, over 25%, or unknown?
4. Does the mechanism skip or change any step that affects a unit's own result files, or only steps whose results are not in those files (for example the cross-unit combination)?
5. Why would the probe's byte-for-byte check catch a wrong computation only partly: the compared files do not cover everything a unit computes; per-unit cost could change without changing outputs; both; or other?
6. Could a later check compare the mechanism's serial per-unit time with run9's recorded per-unit costs (`units.json` `cost_s`) to show that per-unit work is the same size?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run10_mech/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run10_mech/REPORT.md` for the owner with the evidence (file paths, line numbers, code and log lines), separating measured, read from code or documents, and inferred.
2. `run10_mech/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"mechanism"`: `"internal_same_code"`, `"lower_level_published_tool"`, `"modified_entry_copy"`, `"reimplementation"`, `"other"`, `"unknown"`
   - `"per_unit_code_unmodified"`: `"yes"`, `"no"`, `"unknown"`
   - `"non_unit_share"`: `"none"`, `"under_5pct"`, `"5_to_25pct"`, `"over_25pct"`, `"unknown"`
   - `"skipped_steps_affect_unit_files"`: `"yes"`, `"no"`, `"no_steps_skipped"`, `"unknown"`
   - `"partial_catch_reason"`: `"files_incomplete"`, `"cost_can_change_silently"`, `"both"`, `"other"`, `"unknown"`
   - `"cost_check_possible"`: `"yes"`, `"no"`, `"unknown"`

   No other keys and no free text.

Finish within 15 minutes. End with a final reply that is exactly the contents of status.json.
