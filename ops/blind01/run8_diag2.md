You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run8_diag2/`. This is a read-only diagnosis: change nothing else, run no workloads, contact no box, fetch nothing from the network.

## What the operator knows (metadata only)
A first diagnosis of run8 (`run8_diag/status.json`, which you may read with its REPORT.md) found that intake set a 1,200 s anchors budget, the representative-scale anchor workload was still running at that budget in two attempts and only partly completed, and the smallest fix is an anchors budget from a measured or published runtime. The operator plans one pipeline unit: for setup, anchors and profile, intake's budgets become recorded estimates only, and each box command's timeout becomes the time left before a 12 h run ceiling (43,200 s from pipeline start), unless the operator's args set a budget. Reproduction-only results count, so reproduce is not cut early. The operator needs to know whether that fits this workload.

## Read
- `run8_diag/REPORT.md` and `run8_diag/status.json`
- the anchors logs and scripts under `run8/agent/`, intake's records in `run8/` (EXECUTION.json, anchors, baseline), and `intake_mirror/BRIEF_run5.md`
- `dut/pipeline/m5/pipeline.js` (profile stage, the fixed profiler and the concurrency probe) and `dut/pipeline/m5/SCHEMAS.md`, read-only

## Questions
1. How long should one complete anchors run take at the representative scale on a single H100 or A100, and on what basis (published timing, partial progress in the logs, or both)?
2. Does the profile stage run the same workload (`run_command.sh`), and roughly how much longer would it take under the profiler and the concurrency probe?
3. Would a timeout equal to the time left before a 12 h ceiling likely let anchors finish, with time for at least one anchors repair if the first attempt fails?
4. Is the representative scale intake chose the published scale, or reduced from it?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run8_diag2/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run8_diag2/REPORT.md` for the owner, answering the four questions with evidence.
2. `run8_diag2/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"anchors_runtime"`: `"under_20m"`, `"20m_to_1h"`, `"1h_to_3h"`, `"3h_to_6h"`, `"6h_to_12h"`, `"over_12h"`, `"unknown"`
   - `"runtime_basis"`: `"published"`, `"partial_progress"`, `"both"`, `"none"`
   - `"profile_same_workload"`: `"yes"`, `"no"`, `"unknown"`
   - `"profile_runtime_factor"`: `"under_2x"`, `"2x_to_5x"`, `"over_5x"`, `"unknown"` (profile stage wall relative to one anchors run)
   - `"ceiling_fits_anchors"`: `"yes_with_repair"`, `"yes_no_repair"`, `"no"`, `"unknown"`
   - `"scale"`: `"published"`, `"reduced"`, `"unknown"`

   No other keys and no free text.

Finish within 15 minutes. End with a final reply that is exactly the contents of status.json.
