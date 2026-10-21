# Review of build 22 (execution layer, tag m4)

Verdict: FAIL, 1 blocking, 3 advisory.

Read: operator findings, EXEC_NOTE, GATE_COMMIT (first 468 lines only; the addendum 17 section was not reached in the read), run_m4.py (lines 1-1313 and 3380-3640, plus the commit diff 3fc1ef7 against its parent), onbox_m4.sh, lambda_run_m4.sh, remote_run_m4.sh, the frozen launcher and bootstrap, ONBOX_CONTRACT.md, build22_return.json, and the launch 7 evidence (RUN_VALID.json, CLASSIFIER_NOTE.txt). Not found on disk: selftest_build22.log, pip_pins_check_build22.txt.

## What the fix does (operator finding 3)

The diff of run_m4.py between the build 21 commit and the build 22 commit is exactly: new `split_fields` (lines 714-740) and three call sites changed, `is_data_line` (743), `rank_table_shape` (775) and `parse_rank_table` (811). Nothing else in run_m4.py changed. onbox_m4.sh is unchanged (sha 8d7b9d29...). The sha of run_m4.py on disk matches the return (bd6b7ea7...).

Traced against the launch 7 evidence: the 12-word header and a data row with one bracketed group give 12 fields, so the mapping is `by_name`. The score column is `Scoring`, with no rank column, so the top row is the first row written. The score is monotone in the five rows shown. `pose_path_from_row` (3397-3411) reads `Swarm` and `Glowworm`, which gives `swarm_0/lightdock_15.pdb`, with no glob fallback. The 9-token and 3-token planted shapes of EXEC_NOTE item 25 contain no brackets and split as before. The records contract, guard and anchor logic are untouched.

## Findings

1. **BLOCKING** onbox_m4.sh:916-927 (and 362-368), EXEC_NOTE item 6, operator finding 4. The plan is to ship the fixed run_m4.py to the held box and write RESUME. The running shell hashed the old run_m4.py at its start (`RUNNER_SHA_AT_START`). After RESUME it compares the current hash with that one. A changed run_m4.py takes the `fixer_out_of_scope` branch: no restart, `void_by_failure:fixer_out_of_scope`, exit 2. Item 6 states this halt in so many words: the fixer may not change run_m4.py. So the planned resume cannot produce a valid record, and the held box keeps billing until RESUME. The shell that is running on the held box cannot be edited. A fix to run_m4.py needs a fresh launch (a new box, with the budget and launch count that the gate rules). Alternatively the gate has to rule that this hold's restart is exempt, and onbox_m4.sh has to be rebuilt for that. That rebuild does not help the box that is already held, because its shell is already running. Do not write RESUME with a changed run_m4.py.

2. ADVISORY (checklist item 7) out/selftest_build22.log does not exist. EXEC_NOTE says implementer selftests are neither required nor credited (header, "Local selftest", item 5), and run_m4.py has no `--selftest`. The 48 author tests are run on the box (the tests stage). The tests file is unchanged. There is nothing to check for item 7.

3. ADVISORY (checklist item 6) lambda_run_m4.sh differs from frozen/lambda_run.sh beyond the five declared points: `file_system_names` in the launch body (line 88), more forwarded variables (ENV_FS, ENV_TAG, HOLD_SECONDS, ENV_DIR, ENV_LOCK_SHA256, REMOTE_TIMEOUT, PRICE, BUDGET, INSTANCE_TYPE; line 168), the REMOTE_TIMEOUT default 7200 (line 41), a fetch of `RUN_VALID.json` (line 211), and a second copy of tests_m4.py to `m4_run/` (line 119). The copy's own header and EXEC_NOTE "Box" declare these. The billing-safety mechanisms (EXIT trap, terminate retry, on_signal and BACKSTOP_ARMED, self-destruct backstop, setsid detach, marker poll, CRLF guard, unhealthy-box aborts, criticals-first fetch) are intact. The onbox script it runs is `bash remote_run_m4.sh bash $RUNNER` with RUNNER=onbox_m4.sh, which matches `onbox_command` (checklist item 8). remote_run_m4.sh differs from the frozen script only in the cd line and its trailing comment. `HF_TOKEN` is passed to the box environment and onbox_m4.sh unsets it after the lock check (line 681), as item 10 requires. The downloads therefore happen later in the runner and not with the token.

4. ADVISORY (item 10) onbox_m4.sh:681-682 unsets `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` before the runner starts, while downloads run inside the runner (item 9). The token is therefore unavailable to downloads. The named sources (RCSB, Google storage) need no token and launch 7's downloads passed, so there is no effect. It is stricter than item 10 requires.

## Checklist summary (not re-derived beyond the points above)

- Items 1, 3 to 6 and 8 carried by run_m4.py and onbox_m4.sh as reviewed in build 21; the build 22 diff does not touch them.
- Item 2: onbox reads PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and REMOTE_TIMEOUT, caps them at 5 and 7200, and computes STOP_AT (lines 66-122).
- Item 4: nothing reads .keys on the box; env.txt lists named variables only.
