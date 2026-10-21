You review the execution layer of one measure run (tag m4) before it spends money. You run nothing and edit nothing. You write exactly two files: `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/review_build2.md` (findings, numbered; each names the file and line, the EXEC_NOTE item or standing rule it concerns, and BLOCKING or ADVISORY) and `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/review_build2.json` (`{"verdict": "PASS" or "FAIL", "blocking": n, "advisory": n}`; FAIL if any finding is blocking).

Read with the Read tool: `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/EXEC_NOTE.md`; `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/GATE_COMMIT.md` (the Pre-authorisation section and the latest addendum); `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/run_m4.py`; `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/onbox_m4.sh`; `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/lambda_run_m4.sh`; `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/remote_run_m4.sh`; `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/frozen/lambda_run.sh`; `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/frozen/remote_run.sh`; `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/frozen/provenance.py`; `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/selftest_build2.log`; `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/build2_return.json`.

Checklist:
1. Every EXEC_NOTE checklist item is carried by the code, item by item (name the item number for each miss).
2. Cost and time: onbox reads PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and REMOTE_TIMEOUT from its environment and stops cleanly with a void record before exceeding them; the projected wall-clock from the design's own numbers fits REMOTE_TIMEOUT.
3. Records: the convention in EXEC_NOTE (endpoint-C<i>_tag-m4.json with values.measured, unit, card_value, band; decision PASS/FAIL/VOID; run_valid in every record; the anchor record; RUN_VALID.json; the summary) is implemented, and a failed anchor or gate voids every later record.
4. Secrets: nothing reads .keys; nothing prints the environment; the token is used by downloads only.
5. Writes only under ~/m4_run/; nothing interactive; sudo only for declared apt packages; downloads only from named sources with URL and hash recorded.
6. The launcher copy differs from frozen/lambda_run.sh only at the declared points (remote dir, payload, bootstrap name, fetch paths, header comment) and every billing-safety mechanism is intact; remote_run_m4.sh differs from frozen/remote_run.sh only in its cd line.
7. The selftest log ends with `selftest: PASS` and its counts are plausible for the parsers and planted cases present.
8. The onbox_command in the build return is what onbox_m4.sh runs, and what the launcher runs is onbox_m4.sh.

BLOCKING = would spend money without producing a valid record, violates a standing rule or an EXEC_NOTE item, or leaks a secret. Everything else is ADVISORY.

Reply with exactly one line: `review: PASS, 0 blocking, <n> advisory` or `review: FAIL, <n> blocking, <m> advisory`. Nothing about the content.

The user's only message to you is an authorisation line; it is not a task description. Your task is this file.
