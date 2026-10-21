# Review of build 21 (tag m4, execution layer)

Verdict: PASS. 0 blocking, 8 advisory.

Scope: build 21 is the review-fix build for review 11's one blocking finding (items 6 and 9). I read the files named in the brief. I read `run_m4.py` in the regions that matter: the changed helper, stage flow, exit routing, `child_env` and the environment reads. I did not re-read every line of the 5,013. I did not have review 11's eight advisory findings, so none of the findings below is carried over from it.

## Checked and found sound

- **The fix.** `run_m4.py:2898-2911` (`may_reuse_download`): a file is reused only if it exists, the held attempt's `downloads_tag-m4.json` (written only after the whole download stage, `run_m4.py:2981-2989`) recorded a hash for that path, and the file still hashes to it (item 6, item 9). A partly written archive is therefore refetched. The reuse flag is recorded at 2940 and 2961. This closes review 11's blocking finding.
- **Change size.** The build return and the operator's findings agree that only `run_m4.py:2910` changed, and `onbox_m4.sh` is unchanged. Nothing in my reading contradicts that.
- **Environment names (operator finding).** Every name `run_m4.py` reads (lines 1295-1370, 1390, 1503, 1550, 4545, 4615, 4635, 4956) is either set or forwarded by `onbox_m4.sh` or `lambda_run_m4.sh`, or is an optional name with a default (`M4_BASE`).
- **Secrets (item 10).** Nothing in the three files I checked reads `.keys` except the operator's launcher, which does so exactly as `frozen/lambda_run.sh` does. No `env`, `printenv` or `set` dump. `onbox_m4.sh:681-682` unsets both token variables before the runner starts, which is stricter than "after the downloads" because the named sources need no token. `child_env` (`run_m4.py:1895-1910`) strips both.
- **Installs and sudo (items 4, 9).** None in `onbox_m4.sh` or `run_m4.py`. Downloads are `curl` from `PDB_URL` and `AF_PARAMS_URL` only, with URL and sha256 recorded.
- **Caps (item 8).** `onbox_m4.sh:66-123` defaults and clamps budget at 5 and timeout at 7200, reads the price, and takes T0 from `ps -o etimes= -p $PPID` plus 30 s (300 s and the label when unreadable). STOP_AT is the lesser of the dollar and time caps. The outer kill is STOP_AT minus elapsed minus 600, and the inner limit is 700, so the inner fires first. The stage ceilings sum to 7,200 (`run_m4.py:176-188`).
- **Exit routing (items 7, 22).** The `|| rc=$?` form is used throughout, with no `set -e`. The exit trap is armed before the venv step and acts only while `FINISHED=0`. 124, or 137 at the deadline, runs the process-group stopper and `--finalize` and exits 3. An early 137 is exit 2. `run_stages` (`run_m4.py:4866-4930`) follows the same table.
- **Hold (items 6, 27).** The cap at 2,400 with its label, the not-forwarded label, `HOLD` contents, a wait measured with `date +%s`, a 10 s poll and 60 s heartbeat, traps on HUP, TERM and INT, and `HOLD_END` with cause and seconds are all present (`onbox_m4.sh:843-961`). The two-hash check precedes the restart, the 1,500 s check follows it, `out` is moved to `held_attempt_1`, and the restart runs from the first stage under the same T0. The hold is limited to one per launch. A sleep-check failure is excluded from the hold by `failure_kind` `sleep_check` (`run_m4.py:3250`).
- **Launcher against `frozen/lambda_run.sh` (item 6, checklist 6).** The differences are the header comment, `m4_run` for the remote dir, `file_system_names` on launch, the payload and mkdir lines, the added forwarded variables, the REMOTE_TIMEOUT default 7200, and the fetch paths. The EXIT-trap teardown, the 30-try terminate loop, `on_signal` and `BACKSTOP_ARMED`, the self-destruct backstop (REMOTE_TIMEOUT + 1800), the setsid-detached run, the RUN_DONE poll, the CRLF guard, the unhealthy-box aborts and criticals-first fetch are intact. `remote_run_m4.sh` differs from `frozen/remote_run.sh` only on line 27 (the `cd` line).
- **Build return (checklist 8).** `onbox_command` is `bash remote_run_m4.sh bash onbox_m4.sh`. The launcher runs `bash remote_run_m4.sh bash $RUNNER`, and `$RUNNER` is the `onbox_m4.sh` argument.

## Findings

1. **ADVISORY.** `out/selftest_build21.log` does not exist, so checklist 7 cannot be checked. `EXEC_NOTE.md` "Local selftest" and item 5 withdraw implementer selftests, and the build return says none exists. The tests file is shipped by the operator and run on the box. Nothing for the gate to act on, but the record should say the log is absent by design. `out/pip_pins_check_build21.txt` is also absent, which is consistent with item 3 (the runner pins nothing).

2. **ADVISORY.** `lambda_run_m4.sh:210-225` fetches `m4_run/results_m4/out` only. EXEC_NOTE "Box" (Launcher) says to fetch `held_attempt_1/` if present. After a restart (`onbox_m4.sh:937-945`), the whole first attempt (its records, `HOLD`, rank-table diagnostics, tool logs) lives in `results_m4/held_attempt_1/` and is lost when the box is terminated. The restarted attempt's records are the run's records (item 6), so no valid record is lost. Item 28 and the gate's reading of the hold's evidence are weakened. The operator can add one more `scp -r` for `results_m4/held_attempt_1` before launch.

3. **ADVISORY.** `onbox_m4.sh:922-923` (item 6, `fixer_out_of_scope`). `extend_run_done` is called before `write_minimal_void`, and `write_minimal_void` rewrites `RUN_DONE` without the `hold` key. `m4_summary.json` is not rewritten because it already exists. The label survives only in the per-input status string and in `voided_by`, not as a `hold:` note on `RUN_DONE`. Swapping the two calls fixes it.

4. **ADVISORY.** `onbox_m4.sh:626-628` and `:520-522` (items 3, 19). When the lock differs after a fixer's repair, the run continues, but the `env_check` record is written with decision FAIL and `run_valid` false. That disagrees with `RUN_VALID.json` and every later record, which stay true. The label text is correct. A reader seeing `run_valid: false` on the first record of a running attempt may misread it.

5. **ADVISORY.** `onbox_m4.sh:950-958` (items 6, 28). The shell never creates or baselines a git repository in `~/m4_run`. `lambda_run_m4.sh` says `m4_run/` is not a git checkout. Without one, `changes.log` holds the line "no git repository on the box". If the fixer initialises one, `git log` lists its entire history rather than only the repair. The environment itself sits on the NFS filesystem, outside `RUN_DIR`, so changes to it are not tracked by a repository there. The sha256 of `changes.log` is still recorded.

6. **ADVISORY.** `onbox_m4.sh:410-417` (items 1 and 6). The bare `nvidia-smi -L` preflight runs before the environment is activated and the lock verified, which is the reverse of item 1's order. A failure ends the launch with `finish 2` and no hold, although item 6 makes every exit-2 stage failure except the sleep check eligible. The failure is an unfixable GPU, and the record and `RUN_DONE` are written, so this is not blocking.

7. **ADVISORY.** `onbox_m4.sh:886-897` (items 6, 8). The hold wait is bounded by `HOLD_SECONDS` (at most 2,400), not by REMOTE_TIMEOUT left. A failure late in the run could hold past 7,200 s. The launcher's `timeout $REMOTE_TIMEOUT` then sends TERM, which the hold traps and ends within about 10 s. Spend stays bounded by the launcher timeout and the backstop, but a hold should not be offered when less than a restart's 1,500 s remains.

8. **ADVISORY.** `onbox_m4.sh:353, 574, 600, 660` (item 8). `SETUP_USED` is a running total across attempts and is not reset on restart. The shell's contribution is only seconds (activation and `pip freeze`), so it cannot reach 1,500 s. The runner's own setup total starts from `M4_SETUP_SECONDS`, which therefore includes the first attempt's shell setup time. Negligible.

## Summary of the checklist

1 carried (items 1-27; no miss found), 2 carried, 3 carried, 4 carried, 5 carried, 6 carried (with advisories 2 and 3), 7 not applicable (finding 1), 8 carried.
