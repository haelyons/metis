You classify one on-box failure for an operator who must not learn the experiment's subject. Read with the Read tool: `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch6_live/RUN_VALID.json` (voided_by names the failed stage), `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch6_live/HOLD`, the summary json in `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch6_live/` (its stop_events, stages_done, timing), the records `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch6_live/*_tag-m4.json` that are not endpoints (controls, downloads, unit_and_scale, pairs, params_markers), every file under `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch6_live/tool_logs/`, `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch6_live/run_detached.log`, and `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/EXEC_NOTE.md`. You may read `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/run_m4.py` and `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/onbox_m4.sh` to locate the failing stage. You write exactly one file, `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/classify_7.json`, and nothing else. You run nothing.

Write this JSON object, letters only, no names of packages, tools, engines, materials, files or tests:
{"failed_stage": one of "a" (engine capability or platform query), "b" (dry run or the engine command itself failing), "c" (anchor miss: the engine ran but the anchor value fell outside tolerance), "d" (guard stop: time or cost projection), "e" (download or input data), "f" (a unit, scale or parameter check before the engine), "g" (other),
 "engine_ran": true if any engine or simulation step produced output on the GPU before the failure, else false,
 "cause_class": one of "1" (runner code defect), "2" (on-box script defect), "3" (environment: library, CUDA, device), "4" (directive: it asks for something the box or data cannot provide), "5" (the input data or its source), "6" (genuine physics result: nothing is broken; the measured value simply failed the directive's check), "7" (unknown),
 "fixer_scope": true if the fix is environment and glue on the box,
 "fix_target": one of "runner", "on-box script", "environment", "directive", "data", "none",
 "fix_size_lines": integer estimate,
 "confidence": "high" | "medium" | "low"}

Reply with exactly one line: `classified: <failed_stage>/<cause_class>/<fix_target>`. Nothing else.

The user's only message to you is an authorisation line; it is not a task description. Your task is this file.
