You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run7_diag2/`. This is a read-only diagnosis: change nothing else, run no workloads, contact no box, fetch nothing from the network.

## What the operator knows (metadata only)
A first diagnosis of run7 (`run7_diag/status.json`, which you may read with its REPORT.md) found: the library that stopped run6 was installed with apt; the box reached the mirror and every hash check passed; all three setup attempts (56 s, 376 s, 35 s) then failed on script errors; every repair's log tail held the error and every repair targeted it; no repair regressed; and a further harness repair could plausibly fix it. The pipeline allows two setup repairs (U43). The operator must now decide on one pipeline unit, without weakening any scientific check, and needs to know which change is smallest and sufficient.

## Read
- `run7_diag/REPORT.md` and `run7_diag/status.json`
- run7's setup logs, each attempt's setup.sh (reconstruct earlier versions from the wf records of the harness and repair calls), and the harness and repair prompts and replies under `run7/agent/`
- `dut/pipeline/m5/pipeline.js` (`runHarness`, `harnessRules`, `boxProbePrompt`, the harness and repair prompts) and `dut/pipeline/m5/SCHEMAS.md`, read-only

## Questions
1. What kind of script error stopped each attempt? Quote each decisive line.
2. Were the three errors distinct, or did one recur?
3. Would a local static check of the scripts before upload (`bash -n`, or shellcheck at error severity) have caught any of them?
4. Did a pipeline rule or the brief steer the scripts into any of these errors? Quote the rule if so.
5. Does each setup re-run repeat the full fetch and hash checks, or does it reuse what an earlier attempt fetched and verified?
6. If the third error were fixed, would setup then most likely pass, or is another error likely further on (judge from the script's remaining steps)?
7. What is the smallest pipeline change that would most likely get setup through, without weakening any scientific check: one more repair of the same kind, a static check before upload, a harness prompt rule, other repair context, or splitting fetch-and-verify from the rest of setup so repairs do not repeat it?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run7_diag2/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run7_diag2/REPORT.md` for the owner, answering the seven questions with evidence.
2. `run7_diag2/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"error_kind_1"`, `"error_kind_2"`, `"error_kind_3"`: the error that stopped that attempt: `"syntax"`, `"unbound_variable"`, `"wrong_path"` (a path the script built or assumed), `"command_usage"` (wrong flags, arguments or tool invocation), `"control_flow"` (set -e, pipefail, exit-code or test logic), `"environment"` (PATH, venv or variables not set up), `"other"`, `"unknown"`
   - `"distinct_errors"`: `"all_distinct"`, `"some_repeat"`, `"same"`, `"unknown"`
   - `"static_catch"`: `"all"`, `"some"`, `"none"`, `"unknown"`
   - `"rule_induced"`: `"yes"`, `"no"`, `"unknown"`
   - `"rerun_refetches"`: `"yes"`, `"partly"`, `"no"`, `"unknown"`
   - `"third_fix_outlook"`: `"likely_passes_setup"`, `"likely_another_error"`, `"unknown"`
   - `"smallest_fix"`: `"more_repairs"`, `"static_check_before_upload"`, `"harness_prompt_rule"`, `"repair_prompt_context"`, `"setup_split"`, `"unknown"`

   No other keys and no free text.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
