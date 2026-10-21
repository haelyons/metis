# Review of build 25 (tag m4): execution layer

Verdict: PASS. 0 blocking, 7 advisory.

## Basis

- `run_m4.py` is 5,060 lines with sha256 755c32d3…. `onbox_m4.sh` is 979 lines with sha256 8d7b9d29…. Both match the build return.
- `git diff HEAD~1` shows `run_m4.py` changed only at lines 3472-3482 (11 added) and 3511-3519 (9 added), 20 lines in all. `onbox_m4.sh` is unchanged. This is exactly the diagnosis of record and nothing else.
- The new working-directory handling and the error-line check follow the diagnosis:
  - `run_docking` copies both structure files into the run's own working directory. The callers pass distinct directories: `anchor_serial`, `anchor_parallel` and `aux_<pair>`.
  - An `ERROR` line in the setup step's stdout now raises `HarnessFailure`, which is exit 2.
  - The launch 8 log `tool_logs/anchor_anchor_parallel_setup.log` carries `[lightdock3_setup] ERROR: ...` in its stdout section, so the new check matches the real message.
- Launcher copy `lambda_run_m4.sh` against `frozen/lambda_run.sh`. The differences are only:
  - the remote directory
  - the payload
  - the forwarded environment
  - the file-system attachment in the launch call
  - the `REMOTE_TIMEOUT` default of 7200
  - the fetch paths
  - the header comment
  - Every billing-safety mechanism is intact: the EXIT-trap teardown, the `terminate()` retry loop, `on_signal`/`BACKSTOP_ARMED`, the self-destruct backstop, the `setsid` detach, the RUN_DONE poll, the CRLF guard, the unhealthy-box aborts and the criticals-first fetch order.
- `remote_run_m4.sh` differs from `frozen/remote_run.sh` only in the `cd` line (checklist 6).
- `onbox_command` is `bash remote_run_m4.sh bash onbox_m4.sh`. That is what the launcher runs: `bash remote_run_m4.sh bash $RUNNER`, with `$RUNNER` being `onbox_m4.sh` (checklist 8).
- On the checklist items for cost, records and secrets:
  - Cost (2): `onbox_m4.sh` reads `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD` and `REMOTE_TIMEOUT` and caps them at 5 and 7200. `STOP_AT` is the lesser of the dollar cap and the time cap. The runner's outer timer is `STOP_AT - elapsed - 600`, and a void record is written on a stop. The ceilings sum to 7,200.
  - Records (3): item 19 is carried. This is the same code that produced the full record set in launches 6 to 8.
  - Secrets (4): nothing reads `.keys` in the on-box files, and `env.txt` lists named variables only.
- Item 6, H1 to H5, all present in `onbox_m4.sh`:
  - H1: `HOLD` written at lines 863-872, with the 2,400 cap at 851-855 and no hold when `HOLD_SECONDS` is 0 at 856-861.
  - H2 and item 27: measured `date +%s` wait with 10 s polling, a 60 s heartbeat, HUP/TERM/INT traps and `HOLD_END`, at lines 879-907.
  - H3: hash comparison at 916-927.
  - H4: the 1,500 s check and the move to `held_attempt_1`, restarting through the `continue` at lines 971-977.
  - H5: one hold per launch, at lines 845-849.

## Findings

1. ADVISORY. Checklist 7 and EXEC_NOTE "Local selftest". `out/selftest_build25.log` does not exist. EXEC_NOTE removes `--selftest` and credits no implementer selftest, so nothing is owed. The operator reports the author's 48 tests passed 48/48 on the box in launches 6, 7 and 8.

2. ADVISORY. `run_m4.py:3470-3482`, item 6 / V4 restart. The new per-run directories sit under `work_m4/`, which is outside `results_m4/out` and is not cleared between attempts. Nothing in the file removes it (grep for `rmtree` is empty). After a hold, the restarted attempt reruns `run_docking` in directories that already hold the first attempt's generated `lightdock_*` files. Setup would again report "already exists". With the new error check that is exit 2 at the anchor, final under H5. Launch 8's own restarted attempt shows this: its serial setup log carries the same error.
   - The first attempt on a fresh box is unaffected.
   - It only matters for a restart after a failure at or after the anchor's setup.
   - Item 6 says a finding outside H1 to H5 is advisory.
   - Suggested fix for a later build: clear `work_m4` before a restart, or on entry to `run_docking`.

3. ADVISORY. `onbox_m4.sh:681-682`, item 10. `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` are unset before the runner starts, so before the runner's downloads rather than after them. This is stricter than the item, there is no leak, and both named sources (RCSB, Google storage) are public.

4. ADVISORY. `onbox_m4.sh:851-861`, item 8 and H1. The hold length is capped at 2,400 s but not at `REMOTE_TIMEOUT` minus elapsed time. A failure late in the run could hold past the launcher's `timeout` at `REMOTE_TIMEOUT`. The TERM trap during the hold means the shell then ends the wait and writes `HOLD_END`, and billing stays bounded by the launcher's own timeout and the backstop.

5. ADVISORY. `lambda_run_m4.sh:225`, EXEC_NOTE "Box" (launcher). The full fetch copies `results_m4/out` only. `held_attempt_1/` is a sibling under `results_m4/` and is not fetched, although the note says it is. `changes.log` is under `out/` and is fetched. The first attempt's records are lost at teardown unless the operator copies them by hand while the box is held.

6. ADVISORY. `lambda_run_m4.sh:119`. `tests/tests_m4.py` is copied twice, to `m4_run/` and to `m4_run/tests/`. The loose copy is unused, since `onbox_m4.sh` hashes and runs only the `tests/` one. It is harmless.

7. ADVISORY. `run_m4.py:3513-3514`, item 7 (tool failure). The error-line test is a case-sensitive `"ERROR"` match on stdout only. It matches the observed lightdock message, but a tool that wrote `Error` or wrote only to stderr would pass it.
