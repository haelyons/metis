You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run8_diag/`. This is a read-only diagnosis: change nothing else, run no workloads, contact no box, fetch nothing from the network.

## What the operator knows (metadata only)
Run8 (`run8/`) passed intake on the unverified-mirror brief (`intake_mirror/BRIEF_run5.md`). Setup passed on its third attempt (after two repairs; U46 allows four), so stock was verified. Anchors then ran three times (receipts `0054-anchors`, `0056-anchors`, `0058-anchors`) with two `anchors-repair` calls between them:
- 0054: rc 1 after 39 s.
- 0056: rc 124 (timed out) under a 1,200 s anchors budget; receipt wall 1,751 s.
- 0058: rc 1; receipt wall 2,170 s.
Reproduce failed with `error_class` anchor, and `anchors_passed`/`anchors_total` are null. A receipt's wall time includes fetching the remote `out/` and the log back after the command (`dut/pipeline/m5/boxrun.sh`); the upload between 0056 and 0058 took 535 s, so the fetches were probably long. An earlier reader (`run8_family/`) found every call served by Codex with no provider failure.

## Read
- the three anchors logs, `run_anchors.sh` and `run_command.sh` of each attempt (reconstruct earlier versions from the wf records of the harness and repair calls), and the anchors repair prompts and replies under `run8/agent/`
- the fetched outputs under `run8/agent/results/reproduce/` (sizes and file counts of `out/`), intake's anchors and EXECUTION budgets in `run8/`
- `intake_mirror/BRIEF_run5.md`, `intake_mirror/HASHES.tsv`, and the run7 diagnoses, as needed
- `dut/pipeline/m5/pipeline.js` (`runHarness`, the anchors repair prompt, `harnessRules`), `dut/pipeline/m5/boxrun.sh` and `dut/pipeline/m5/SCHEMAS.md`, read-only

## Questions
1. Where did each anchors attempt fail, and on what (quote the decisive log lines)?
2. Did the published baseline workload itself start and finish on the GPU in any attempt?
3. How long does the representative-scale anchor workload take according to the brief, intake and the logs, and does it fit the 1,200 s anchors budget? Where does that budget come from?
4. Did any attempt write measured values for the anchors?
5. How large is the fetched `out/` (bytes and files), and did fetching dominate the receipt wall times?
6. Is there any sign that the mirror copy of the materials caused the failure (wrong, missing or corrupt inputs), as opposed to the scripts or the budget?
7. Did each repair see the decisive error, and did it target it? Did the overrun figure in the repair prompt (which counts fetch time) mislead a repair?
8. What is the smallest pipeline change that would most likely let anchors run to completion and be scored, without weakening any scientific check?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run8_diag/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run8_diag/REPORT.md` for the owner, answering the eight questions with evidence.
2. `run8_diag/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"attempt1_point"`, `"attempt2_point"`, `"attempt3_point"`: `"script_error"` (the harness scripts themselves: syntax, paths, flags, control flow), `"workload_error"` (the published baseline ran and exited with an error), `"workload_too_long"` (the workload was still running at the budget), `"output_parse"` (the workload finished but the scripts failed to extract or write measurements), `"missing_input"`, `"other"`, `"unknown"`
   - `"workload_completed"`: `"yes"`, `"partly"` (some anchor items or configurations finished), `"no"`, `"unknown"`
   - `"budget_fit"`: `"fits"`, `"too_small"`, `"unknown"`
   - `"budget_source"`: `"intake_execution"`, `"pipeline_default"`, `"other"`, `"unknown"`
   - `"measured_values"`: `"all"`, `"some"`, `"none"`, `"unknown"`
   - `"out_size"`: `"under_100mb"`, `"100mb_to_1gb"`, `"over_1gb"`, `"unknown"`
   - `"fetch_dominates_wall"`: `"yes"`, `"no"`, `"unknown"`
   - `"materials_issue"`: `"yes"`, `"no"`, `"unknown"`
   - `"tail_had_cause"`: `"all"`, `"some"`, `"none"`, `"unknown"`
   - `"repairs_targeted_cause"`: `"all"`, `"some"`, `"none"`, `"unknown"`
   - `"overrun_misled"`: `"yes"`, `"no"`, `"unknown"`
   - `"smallest_fix"`: `"more_anchor_repairs"`, `"anchors_budget"` (the anchors budget should come from a measured or published runtime), `"repair_prompt_context"` (repairs need other context, such as command time apart from fetch time), `"harness_prompt_rule"`, `"output_size_rule"` (keep large outputs out of the fetched `out/`), `"materials"`, `"brief"`, `"unknown"`

   No other keys and no free text.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
