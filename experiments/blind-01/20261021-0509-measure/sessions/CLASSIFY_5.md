You classify one test failure for an operator who must not learn the experiment's subject. Read with the Read tool: `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch5_live/tests_tag-m4.json` (values.stdout_tail holds the TEST lines; one is FAIL with its reason), `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/tests/tests_m4.py` (the tests, second revision), `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/EXEC_NOTE.md` (the directive), `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/run_m4.py` and `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/onbox_m4.sh` (what ran). You write exactly one file, `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/classify_5.json`, and nothing else. You run nothing.

Write this JSON object, letters only, no names of packages, tools, engines, materials or tests:
{"class": one of "a" (the test asserts something the directive does not require or guesses an interface the directive does not fix), "b" (the runner or on-box script does not implement a directive requirement the test checks correctly), "c" (an environment or box fact), "d" (the harness: invocation, paths, arguments, working directory),
 "fixer_scope": true if the fix is inside "environment and glue" and could be made on the held box,
 "fix_target": one of "test file", "runner", "on-box script", "environment", "harness",
 "fix_size_lines": an integer estimate of the lines to change,
 "safe_to_launch_without_fix": true if the failing check does not touch the records contract, the guard or the measurement protocol,
 "confidence": "high" | "medium" | "low"}

Reply with exactly one line: `classified: <class>/<fix_target>/<safe_to_launch_without_fix>`. Nothing else.

The user's only message to you is an authorisation line; it is not a task description. Your task is this file.
