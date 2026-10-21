# Review of build 23 (execution layer, tag m4)

Verdict: FAIL, 1 blocking, 4 advisory.

Read: operator findings, EXEC_NOTE, GATE_COMMIT (first 468 lines, the headings of every addendum, and Addendum 17 with the operator actions), review_build22.md, run_m4.py lines 1-1313 only (the rest was not read; build23_return.json states that run_m4.py is unchanged, and I did not diff it), onbox_m4.sh (all), lambda_run_m4.sh, remote_run_m4.sh, frozen/lambda_run.sh, frozen/remote_run.sh, frozen/ONBOX_CONTRACT.md, build23_return.json. Not found on disk: selftest_build23.log, pip_pins_check_build23.txt. frozen/provenance.py was not read.

## What build 23 did

Nothing. build23_return.json says "FIX: none applied" and gives the same line counts and sha256 values as build 22 (run_m4.py 5,040 lines, bd6b7ea7...; onbox_m4.sh 979 lines, 8d7b9d29...). It treats review 13's one blocking finding as a finding against the resume plan and not against the code. That reading matches Addendum 17 answers L5 and L7. The operator's finding 3 still states the same plan, so the finding still holds.

## Findings

1. **BLOCKING** onbox_m4.sh:916-927 (hash compare) and 362-368 (hashes taken at start); EXEC_NOTE item 6 and "Box" section; GATE_COMMIT Addendum 17 L5, L7 and the operator action "never for a runner defect". Operator finding 3 says: ship run_m4.py and onbox_m4.sh to the held A100 and let RESUME re-run from the failed dry-run stage. The shell running on that box hashed the old run_m4.py at its start (`RUNNER_SHA_AT_START`). After RESUME it compares the current hash with that one. A shipped run_m4.py (build 22's parser fix, 3fc1ef7) differs, so the shell takes the `fixer_out_of_scope` branch: no restart, `void_by_failure:fixer_out_of_scope`, exit 2, and no valid record. The held box bills until then. Shipping a new onbox_m4.sh does not help, because bash is already running the old copy. Build 23 changed no line, so nothing in the files makes the plan work. Do not write RESUME with a changed run_m4.py or tests_m4.py. A corrected run_m4.py needs a fresh box, which needs a gate ruling on budget (USD 5.82 remaining against USD 4.311 per launch at its caps; Addendum 17 L9 authorises launch 7 only), or a gate ruling that exempts this hold's restart, which the already-running shell could not honour.

2. ADVISORY (checklist item 7) out/selftest_build23.log does not exist. EXEC_NOTE removes implementer selftests ("Local selftest", item 5), and run_m4.py has no `--selftest`. The 48 author tests run on the box in the tests stage. There is nothing to check. out/pip_pins_check_build23.txt does not exist either; EXEC_NOTE item 3 says the runner pins nothing, so no check applies.

3. ADVISORY (checklist item 6; EXEC_NOTE "Box", item 6 `changes.log`, Addendum 17 operator action) lambda_run_m4.sh:204-228 fetches only `m4_run/results_m4/out`, so `results_m4/held_attempt_1/` is never fetched. After a restart (item 6 moves the first attempt there) its records and tool logs would be lost at termination. `changes.log` is inside `out/`, so it is fetched. The operator copied launch 7's live records by hand. The launcher cannot be changed without leaving the declared points. Money is not at risk. The operator must fetch `held_attempt_1/` by hand before termination.

4. ADVISORY (checklist item 6) lambda_run_m4.sh differs from frozen/lambda_run.sh beyond its five declared points. Each difference is declared in its own header and in EXEC_NOTE "Box": `file_system_names` in the launch body (line 88), the forwarded variables (line 168), the REMOTE_TIMEOUT default 7200 (line 41), the RUN_VALID.json fetch (line 211), and a second copy of tests_m4.py to `m4_run/` (line 119). The header's "declared point 4, additive" wording covers the forwarding. The billing-safety mechanisms (EXIT-trap terminate with its retry loop, `on_signal` and `BACKSTOP_ARMED`, the self-destruct backstop with `pgrep` confirmation, the setsid detach, the RUN_DONE poll, the CRLF guard, the unhealthy-box aborts, the criticals-first fetch) match the frozen file. remote_run_m4.sh differs from frozen/remote_run.sh only in the `cd` line and its comment. Checklist item 8: `onbox_command` equals `bash remote_run_m4.sh bash onbox_m4.sh`, and the launcher runs `bash remote_run_m4.sh bash $RUNNER` with `onbox_m4.sh` as the runner, so they agree.

5. ADVISORY (EXEC_NOTE item 10 and item 9) onbox_m4.sh:681-682 unsets `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` before the runner starts, but downloads run inside the runner (item 9). The token is therefore not available to downloads. It is stricter than item 10 requires. The named sources (RCSB and Google storage) need no token, and launch 7's downloads passed. Review 13's other advisory findings were left unaddressed by instruction.

## Checklist summary

- Items 1 and 3 to 6: carried in the part of run_m4.py and onbox_m4.sh read. Not re-derived for the unread part of run_m4.py (unchanged since build 22).
- Item 2: onbox_m4.sh:66-122 reads PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and REMOTE_TIMEOUT, caps them at 5 and 7200, and computes STOP_AT. The stage ceilings (1,500 + 300 + 700 + 600 + 2,000 + 1,600 + 100 + 400) sum to 7,200 (run_m4.py:176-188).
- Item 4: nothing reads `.keys` on the box, `env.txt` lists named variables only, and the token is unset before the runner starts.
- Item 5: the caches are under the run directory, there is no sudo and no pip in onbox_m4.sh, and the downloads are from the named hosts only (run_m4.py:362-367).
- Operator findings: nothing was listed as an unforwarded or unset variable. I read no file the operator did not mention.
