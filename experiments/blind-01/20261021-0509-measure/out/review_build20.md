# Review of build 20, execution layer (tag m4)

Verdict: FAIL. 1 blocking, 8 advisory. Nothing was run. Findings are from reading the files, `git diff 0389e05` on the two built files, and a diff of `remote_run_m4.sh` against `frozen/remote_run.sh`.

## Blocking

1. **BLOCKING. `run_m4.py:2897-2909` and `2928-2961`; EXEC_NOTE item 6 (reuse only "with the recorded sha256"), item 9.**
   `may_reuse_download` returns True when the file exists and no hash was recorded. `downloads_tag-m4.json` is written only after every download, the extraction, the multimer parameter check and the parameter markers have succeeded (`run_m4.py:2981`). If the first attempt failed inside the download stage, a partial `alphafold_params.tar` is left in `~/m4_run/data/`. No record exists, so on restart the partial file is reused and marked `reused: true`. Its sha256 is computed from the file as it stands, so the record looks valid. The archive then fails at `tar` (exit 2) or, worse, extracts a truncated set. The directive allows reuse only for "a file that exists with the recorded sha256". Fix: with no recorded hash, return False and fetch again.

## Advisory

2. **ADVISORY. `onbox_m4.sh:916-927`, `171-339`; item 6 and item 23.** On `fixer_out_of_scope`, `extend_run_done` writes the hold note, and `write_minimal_void` then overwrites `RUN_DONE` and `RUN_VALID.json`. The `hold:` note is lost, and so is the first failure's `voided_by`. The label `fixer_out_of_scope` survives only inside the `void_by_failure:fixer_out_of_scope` status strings. Same effect on the other void path after a hold.

3. **ADVISORY. `onbox_m4.sh:622-629`; item 3.** After a fixer changes the environment and the restart continues, `write_env_check` is called with `equal=false`. That gives the env_check record `decision` FAIL and `run_valid` false (heredoc line 521), while the run goes on with true records. The label is present as item 3 asks, but the `run_valid` field disagrees with the rest of the run (item 19). The runner never reads this record (grep `env_check` finds only `run_m4.py:326`), so nothing else is voided.

4. **ADVISORY. `onbox_m4.sh:850-855`, `676`; item 6.** The 2,400 s cap is applied only inside `hold_open`. `HOLD_SECONDS` is exported to the runner as the raw value, and `env.txt` records `HOLD_SECONDS=$HOLD_SECONDS_SEEN` as written at `write_env_txt` time, so a run that never holds does not show the cap label. A non-numeric `REMOTE_TIMEOUT` passes `awk_le` (line 94) as 0 and then breaks the arithmetic (item 8, no default above 7200). The launcher always forwards `REMOTE_TIMEOUT`, so the exposure is small.

5. **ADVISORY. `onbox_m4.sh:843-935`; item 6 and item 8.** The hold does not check how much of `REMOTE_TIMEOUT` is left before it starts. A failure at elapsed 6,000 s holds until the launcher's `timeout` sends TERM. The TERM trap then ends the hold as an expiry, so billing is bounded, but the "hold: no time to resume" label cannot arise on that path. The wait itself matches item 27: measured with `date +%s`, 10 s poll, 60 s heartbeat, HUP/TERM/INT trapped, and `HOLD_END` written with the cause.

6. **ADVISORY. `lambda_run_m4.sh:225`; EXEC_NOTE Box section ("fetch ... `held_attempt_1/` if present"), item 6.** The launcher fetches only `m4_run/results_m4/out`. `results_m4/held_attempt_1/` is a sibling of `out`, so after a restart the first attempt's records are not fetched, and the launcher's own fetch is the only path that retrieves them. `changes.log` and `HOLD_END` are inside `out` and are fetched. The launcher is operator-owned and unchanged since launch 3, so I rate this advisory. It needs a one-line addition, or a manual copy before teardown.

7. **ADVISORY. `lambda_run_m4.sh` against `frozen/lambda_run.sh`; checklist 6.** The copy differs from the frozen file at more than the five points in checklist 6. It adds `file_system_names`, the extra forwarded variables, the `REMOTE_TIMEOUT` default 5400 to 7200, the `RUN_VALID.json` fetch and the removal of `EXTRA`. The copy's header declares these differences. Every billing-safety mechanism I compared is intact: EXIT-trap `terminate` with retry, `on_signal` and `BACKSTOP_ARMED`, the self-destruct backstop with `pgrep` confirmation, `setsid` with `</dev/null`, the `RUN_DONE` poll, the unhealthy-box aborts, the CRLF guard and the fetch ordering. `tests_m4.py` is also copied to `m4_run/` top level, beside the `tests/` copy that item 2 names. `HOLD_SECONDS` defaults to 0 in the launcher, so the operator must set 2400 for a hold to exist. `remote_run_m4.sh` differs from `frozen/remote_run.sh` only in the `cd` line (checked with diff).

8. **ADVISORY. Checklist 7; `out/selftest_build20.log` and `out/pip_pins_check_build20.txt` do not exist.** The directive removes the selftest ("Local selftest: None"), so there is no `selftest: PASS` line to check. The build return states that only `py_compile` and `bash -n` were run. The pip pins check does not apply, since the environment of record is a prebuilt venv and the runner pins nothing. The operator's finding says the tests passed 48/48 on the box in launch 6, but I did not read the tests or that log.

9. **ADVISORY. `run_m4.py:3515-3520`; item 26 f.** When no `rank_*.list` exists, `run_docking` raises without writing `rank_table_diagnostic_<name>_tag-m4.txt`. Item 26 requires the diagnostic for parse errors and pose failures, so strictly a missing table is outside it. A diagnostic listing the work directory would still help the post-mortem. Separately, `parse_rank_table` raises a parse error for a by-name table whose header has neither a rank nor a score column (`run_m4.py:812-816`), which item 26 (b) does not ask for. The planted cases in item 25 are unaffected.

## Checklist summary

- **1. Checklist items.** Items 1 to 27 are carried by the code and the script, with no miss except as listed above. Items 3 to 6, 8 and 27 were read in `onbox_m4.sh`. Items 13, 25 and 26 were read in `run_m4.py`.
- **2. Cost and time.** `onbox_m4.sh` reads the three variables and applies the caps. `STOP_AT` is the lesser of the time cap and the dollar cap. The runner's outer timer is `STOP_AT - elapsed - 600`. T0 is `etimes` of the parent plus 30 s, with the 300 s fallback. The ceilings sum to 7,200 s, and the runner's `STAGE_CEILING_S` matches item 8.
- **3. Records.** The convention is implemented as in earlier builds. Build 20 changed none of it except the `docking_parameters.rank_table_columns` addition.
- **4. Secrets.** Nothing reads `.keys`. No `env`, `printenv` or `set` dump exists. `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` are unset by the shell before the runner starts, which is stricter than "after the downloads" and safe because the two sources need no token. `env.txt` names only non-secret variables.
- **5. Writes and sources.** Writes stay under `~/m4_run/`, with no sudo, pip or apt call in either file. Downloads are only from `files.rcsb.org` and `storage.googleapis.com`, with URL and sha256 recorded, subject to finding 1.
- **6. Launcher.** See findings 6 and 7.
- **7. Selftest log.** See finding 8.
- **8. onbox_command.** The return states `bash remote_run_m4.sh bash onbox_m4.sh`. The launcher runs `bash remote_run_m4.sh bash $RUNNER`, so `RUNNER` must be given as `onbox_m4.sh`.
- **Build scope.** `git diff 0389e05` shows hunks only in the V1 to V4 regions (rank-table parser and top-row chooser, diagnostic writer, `run_docking` call lines, download reuse and `onbox_m4.sh` hold-wait lines). No line outside V1 to V4 changed.
