# Review 15 of build 23 (run_m4.py bd6b7ea7…, onbox_m4.sh 8d7b9d29…) under EXEC_NOTE as revised by addendum 18

Verdict: PASS. 0 blocking, 6 advisory.

Item 6 is judged under its current wording only (H1 to H5, in `onbox_m4.sh`). All five are present:

- H1: `hold_is_eligible` (onbox_m4.sh:833-840) excludes `sleep_check`, which is the kind `run_m4.py:3277` raises. `HOLD` is written at 863-872 after the attempt's void records and `RUN_DONE`. It carries stage, kind, exit code, UTC time and `hold_seconds`. The 2,400 cap is at 851-855. No `HOLD` is written when `HOLD_SECONDS` is 0 or unset (856-861).
- H2: the wait at 879-897 is measured with `date +%s`, polls every 10 s, writes a heartbeat every 60 s, and traps HUP, TERM and INT. It ends only on `RESUME`, expiry or a signal. `HOLD_END` is written at 898-907.
- H3: hashes of `run_m4.py` and `tests/tests_m4.py` are taken at start (367-368) and compared at 916-927. A difference gives `fixer_out_of_scope`, exit 2, no restart.
- H4: with at least 1,500 s left (929-935), `out` is moved to `held_attempt_1` (941) and `attempt_body` is re-run once from its first stage (971-977). T0 is `T0_EPOCH`, unchanged, and STOP_AT is unchanged. A `RESUME` never ends the launch in place of the restart. Expiry ends the launch with the first attempt's records (909-913).
- H5: a second eligible failure with `HELD_ATTEMPTS` of 1 or more returns 1 at 845-849. Exit is 2 and there is no second hold.

## Findings

1. ADVISORY. Checklist 7 / EXEC_NOTE "Local selftest". `out/selftest_build23.log` does not exist. The directive removes the selftest and credits none, so there is nothing to check. `out/pip_pins_check_build23.txt` and `out/operator_findings` pins are likewise absent; the runner pins nothing (item 3). No action.

2. ADVISORY. EXEC_NOTE Box section (fetch paths). `lambda_run_m4.sh:210-225` fetches `results_m4/out/` but not `results_m4/held_attempt_1/`. If a hold ends in a restart, the first attempt's records stay on the box and are lost when it is terminated. The directive asks for `held_attempt_1/` to be fetched if present. It is not an item and costs no valid record, so not blocking. Add a fetch for `m4_run/results_m4/held_attempt_1` before launch if a hold is likely.

3. ADVISORY. EXEC_NOTE item 32, `onbox_m4.sh:922-925`. On `fixer_out_of_scope`, `extend_run_done` writes the "hold" note first, and `write_minimal_void` then rewrites `RUN_DONE` without it (put() never overwrites a record, but `RUN_DONE` is opened "w" at 331). This is the observed launch 7 outcome: a `RESUME` after the runner swap ends in exit 2 because the start hash is held in the shell's memory. That matches H3 as worded. Operator finding 2 (the on-box script finishes instead of re-running) is a defect to carry into build 24, REPORTING under item 32. It does not affect a run that does not hold.

4. ADVISORY. EXEC_NOTE item 3, `onbox_m4.sh:521`. The env_check record sets `run_valid` to `equal`. After a fixer change (626-628) the record is therefore `run_valid` false while the run continues, with every later record true. Item 3 asks only for the label. Only reachable after a hold and restart.

5. ADVISORY. EXEC_NOTE item 2 ("Nothing else is on the box"). `lambda_run_m4.sh:119` also copies `tests/tests_m4.py` to `~/m4_run/`, in addition to `~/m4_run/tests/`. Harmless; only the `tests/` copy is hashed and run.

6. ADVISORY. EXEC_NOTE item 8 / `onbox_m4.sh:574,600`. `SETUP_USED` accumulates across the restart, so the restarted attempt starts with the first attempt's setup seconds against the 1,500 s ceiling. This is conservative. Item 30 also applies: `frozen/remote_run.sh` pip-upgrades packages before `onbox_m4.sh` and is not recorded by the build.

## Checklist

- **1. Items carried.** Items 1 to 5, 7 to 10 and 19 to 27 are carried in the paths read: stage order in `DEFAULT_STAGES`, the lock check, a void table in `write_minimal_void`, `STAGE_CEILING_S` summing to 7,200, and the allowance formula at `run_m4.py:2128-2143`. I did not read all 5,040 lines of `run_m4.py`. Items 11 to 18 and 25 (measurement logic, labels, parsers) were not read line by line; they are covered on the box by the 48 tests, which passed in launch 7.
- **2. Cost and time.** `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD` and `REMOTE_TIMEOUT` are read in the shell (66-95) and in `RunState` (1329-1341). Defaults are no higher than 5 and 7200. The projected wall-clock of about 5,400 to 6,500 s fits 7,200. Launch 8 at the operator's min(5, remaining) leaves 4.51 after spend of record 5.49, which covers the 4.311 needed at 7,800 s and USD 1.99.
- **3. Records.** `write_minimal_void` carries the endpoint keys, `run_valid`, `RUN_VALID.json`, the summary and `RUN_DONE`, and never overwrites a decided record. The anchor-miss void propagates through `void_run` and `run_stages`.
- **4. Secrets.** Nothing reads `.keys` outside the operator's launcher. `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` are unset at `onbox_m4.sh:681-682`. `env.txt` lists named variables only. `SECRET_ENV_KEYS` is stripped for children (`run_m4.py:1930`, 4587). The runner has no `sudo`, `apt-get` or `pip` call.
- **5. Writes and downloads.** All writes are under `$RUN_DIR`, with caches and `TMPDIR` redirected. Nothing is interactive. Download hosts are limited to `files.rcsb.org` and `storage.googleapis.com`.
- **6. Launcher copy.** `lambda_run_m4.sh` differs from `frozen/lambda_run.sh` only at the declared points: remote dir, payload, bootstrap name, forwarded env, `file_system_names`, `REMOTE_TIMEOUT` default 7200, fetch paths and the header. The EXIT trap, `terminate()` retry loop, `on_signal` and `BACKSTOP_ARMED`, the self-destruct backstop, `setsid`, the `RUN_DONE` poll, the CRLF guard, the unhealthy-box aborts and the criticals-first fetch are intact. `remote_run_m4.sh` differs from `frozen/remote_run.sh` only in its `cd` line.
- **7. Selftest log.** Absent, as the directive provides (finding 1).
- **8. onbox_command.** `bash remote_run_m4.sh bash onbox_m4.sh` matches what the launcher runs (`lambda_run_m4.sh:168`).
- **Operator findings.** Verified: file sizes and hashes match the build return (5,040 and 979 lines). No `.keys` mention in either file. The environment names the runner reads (`M4_*`, `ENV_*`, `HOLD_SECONDS`, `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD`, `REMOTE_TIMEOUT`, `M4_BASE`) are set or forwarded by `onbox_m4.sh` or the launcher.
