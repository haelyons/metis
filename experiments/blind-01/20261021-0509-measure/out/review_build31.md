# Review of build 31 (tag m4): execution layer

Verdict: PASS. 0 blocking, 4 advisory.

How I checked: I read the files named in the brief. For three points I also ran a read-only `diff`, `sha256sum` and `ls`:
- the launcher and bootstrap copies against `frozen/`;
- the build's file hashes against `out/build31_return.json`;
- the file times against the test log.

I did not read `run_m4.py` in full (277 KB). I read the shell script and the launchers in full, and searched the runner for the secret, write-path, environment, lock and exit-kind points.

Verified, by checklist number:
- 1. EXEC_NOTE items.
  - Items 3, 6 (H1 to H5), 7, 8 and 29 are carried by `onbox_m4.sh`.
  - The runner carries items 4, 5, 10, 25 and 28. I confirmed these by search only.
  - The sleep-check hold exclusion matches the runner's `kind="sleep_check"` (`run_m4.py:3497`).
- 2. Cost and time.
  - `onbox_m4.sh:66-95` reads PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and REMOTE_TIMEOUT from the environment.
  - Defaults never exceed 5 or 7200, and the values are clamped (`:94-95`).
  - `STOP_AT` is the lesser of the dollar cap and the time cap (`:118-120`).
  - The runner's outer timeout is `STOP_AT - elapsed - 600` (`:789`), and a timer kill leads to `--finalize` and void records (`:810-858`).
  - The ceilings sum to 7,200, as item 8 says.
- 3. Records.
  - `write_minimal_void` writes the anchor, C1 to C4, summary, RUN_VALID and RUN_DONE.
  - It never overwrites a decided record (`onbox_m4.sh:170-343`).
  - `run_m4.py` carries `calibration_valid` and `run_valid_voided_by`.
  - The anchor-miss path is carried per items 11 and 7 (not read in full).
- 4. Secrets.
  - Nothing reads `.keys`: the only match in `run_m4.py` is `keys = list(rows[0].keys())` at `:754`.
  - There is no `printenv`, `env` or `set` dump, and `env.txt` lists named variables only (`onbox_m4.sh:137-164`).
  - `onbox_m4.sh:785-786` unsets the token before the runner starts.
  - The runner strips both token names from tool children (`SECRET_ENV_KEYS`, `run_m4.py:218`).
  - The launcher passes the token only to the detached run, as the frozen launcher does.
- 5. Writes, sudo, downloads.
  - Output goes under `$RUN_DIR/results_m4/out`.
  - Caches and TMPDIR point under `$RUN_DIR` (`onbox_m4.sh:500-508`).
  - There is no sudo, apt or pip call in either file.
  - `run_m4.py` has no `sudo`, `apt-get`, `pip install` or absolute-path write matches.
  - The only pip call is the `pip freeze` lock hash.
- 6. Launcher and bootstrap.
  - `lambda_run_m4.sh` differs from `frozen/lambda_run.sh` only at declared points:
    - header comment;
    - remote dir;
    - payload;
    - `file_system_names`;
    - forwarded environment variables;
    - REMOTE_TIMEOUT default 7200;
    - fetch paths.
  - Every billing-safety mechanism is intact: the EXIT trap, `terminate` retry loop, `on_signal`/`BACKSTOP_ARMED`, backstop with pgrep confirmation, setsid run, marker poll, unhealthy-box aborts and CRLF guard.
  - The launcher no longer ships `tests/tests_m4.py`. The payload is `run_m4.py`, `remote_run_m4.sh`, the onbox script and `frozen/provenance.py`, plus `data/` if present.
  - `remote_run_m4.sh` differs from `frozen/remote_run.sh` only on line 27, the `cd` line.
- 7. Local tests.
  - The log ends `TESTS: 46 of 46 passed` and `TESTS: PASS`.
  - The log (04:14) is newer than `run_m4.py` (04:01) and `onbox_m4.sh`.
  - The test file calls the runner as `--stage <name> --in <dir> --out <dir>` (`tests/tests_m4.py:1077`).
- 8. `onbox_command`.
  - The build return gives `bash remote_run_m4.sh bash onbox_m4.sh`.
  - The launcher runs `bash remote_run_m4.sh bash $RUNNER`, with `$RUNNER` being `onbox_m4.sh`.
  - The file hashes match the build return: `c068d87b…` for `run_m4.py` and `9c1a1067…` for `onbox_m4.sh`.

Operator finding 3 (M4_BASE) is closed. `onbox_m4.sh:803` and `:849` always pass `--base "$RUN_DIR"`, so `M4_BASE` is never consulted on the box. The fallback at `run_m4.py:5622` is the current directory, which is `$RUN_DIR` after the `cd` at `onbox_m4.sh:51`.

## Findings

1. ADVISORY. `lambda_run_m4.sh:208-228`. This concerns the Box section's fetch of `held_attempt_1/` and the fetch paths.
   - The launcher fetches only `results_m4/out`.
   - After a hold and restart, the first attempt is moved to `results_m4/held_attempt_1/` (`onbox_m4.sh:1043`), a sibling of `out`. Nothing fetches it.
   - `changes.log` is inside `out` and is fetched.
   - The restart still produces valid records. The first attempt's evidence would be lost unless the operator fetches it by hand before teardown, which the launcher does automatically after the poll ends.
   - The fix is one extra `scp -r` of `results_m4/held_attempt_1`.

2. ADVISORY. `onbox_m4.sh:990-1001`, EXEC_NOTE item 6 H1 and item 8.
   - The hold wait is bounded by `HOLD_SECONDS` (at most 2,400) but not by `STOP_AT` or the remaining `REMOTE_TIMEOUT`.
   - A failure late in the run would hold past the launcher's `timeout` and be killed there.
   - Records and RUN_DONE already exist before the hold, so no record is lost.
   - Spend stays within the 7,800 s bound of the Box section at the 1.99 and 2.50 prices.

3. ADVISORY. `onbox_m4.sh:625` and `run_m4.py:1742` (the lock-mismatch-after-fixer path), items 3 and 21.
   - After a fixer change the environment check record is written `equal=false`, decision FAIL and `run_valid=false`, though the run goes on.
   - Later records carry the fixer label.
   - A reader may take that record as a failed gate.
   - Item 3 only requires the label.

4. ADVISORY. `out/build31_return.json`, `selftest_output` and `onbox_sh`.
   - The build return is stale.
   - It says the launcher still ships the test file (the old line 119). That is no longer true in `lambda_run_m4.sh`.
   - It also cites `run_m4.py --selftest`, an implementer selftest that item 5 and standing change (ii) do not require. The box script does not call it.
   - No action is needed before launch beyond the operator noting that the return's launcher remark is out of date.

Also noted under item 32 (not counted). `remote_run_m4.sh` runs `pip install --upgrade` into `~/.local` on first use, and `.setup_ready` is written outside `results_m4/`. This is the operator's frozen bootstrap, and `remote_run_m4.sh` is identical to it except for the `cd` line. `out/pip_pins_check_build31.txt` does not exist, so I made no pins check.
