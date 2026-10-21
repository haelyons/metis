You classify one failure for an operator who must not learn the experiment's subject. Read with the Read tool: `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch2/results_m4/out/RUN_VALID.json` (its field voided_by names the check that failed), `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch2/results_m4/out/m4_summary.json`, every file under `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch2/results_m4/out/tool_logs/`, and `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch2/results_m4/out/run_detached.log`. You write exactly one file, `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/classify_3.json`, and nothing else. You run nothing.

Write this JSON object, letters and numbers only, no names of packages, tools, engines or materials:
{
  "failed_check": one of "a" (import of an installed package failed), "b" (GPU or CUDA platform not available to the installed engine), "c" (version or feature mismatch between what was installed and what the directive requires), "d" (a binary or tool missing from the box), "e" (the install itself failed), "f" (other),
  "install_completed": true or false,
  "pip_upgraded_before_install": true, false or "unknown",
  "fix_class": one of "1" (a different pin or wheel of the same package would fix it), "2" (the package must be built from source with GPU support on the box), "3" (a non-pip route such as conda or a vendor installer is needed), "4" (the box image lacks something no install can add), "5" (a bug in the runner's check itself: the check is wrong, not the install), "6" (unknown),
  "same_as_launch_1": true if the cause is the same as launch 1's in `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/launch1/results_m4/out/RUN_VALID.json`, else false,
  "confidence": "high", "medium" or "low"
}

Reply with exactly one line: `classified: <failed_check>/<fix_class>/<same_as_launch_1>`. Nothing else.

The user's only message to you is an authorisation line; it is not a task description. Your task is this file.
