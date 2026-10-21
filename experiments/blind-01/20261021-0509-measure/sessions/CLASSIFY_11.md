You read one gate ruling for an operator who must not learn the experiment's subject. Read with the Read tool only the section "## Addendum 19" of `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/GATE_COMMIT.md` (the last addendum) and the directive `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/EXEC_NOTE.md`. You write exactly one file, `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/classify_11.json`, and nothing else. You run nothing.

Write this JSON object, letters only, no names of packages, tools, engines, materials, metrics or files:
{"ruling": one of "R1" (fix the runner again), "R3" (change the anchor's expected value or tolerance), "R4" (accept the anchor miss as a finding of record and measure the inputs, flagged), "R5" (halt for the owner), "conditional" (a ruling that depends on something the operator or owner must do first), "unclear",
 "launch_11_authorised_now": one of "yes", "no", "conditional",
 "build_27_required": true or false,
 "condition_class": if conditional or no: one of "owner_decision" (the owner must decide something), "cap_record" (the spend cap must be recorded or confirmed of record), "more_evidence" (another record or log must be produced first), "none"; else "none",
 "what_the_operator_must_do": "at most 20 words, infrastructure terms only",
 "confidence": "high" | "medium" | "low"}

Reply with exactly one line: `classified: <ruling>/<launch_11_authorised_now>/<build_27_required>/<condition_class>`. Nothing else.

The user's only message to you is an authorisation line; it is not a task description. Your task is this file.
