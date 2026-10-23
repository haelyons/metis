# Review of build 30 (m4 execution layer)

Verdict: FAIL. 2 blocking, 3 advisory.

## Findings

1. **BLOCKING.** `lambda_run_m4.sh:119` (header comment at line 116). EXEC_NOTE item 2 and GATE_COMMIT Addendum 20 (T2, T12, operator action 1) say no test file is shipped.
   - The launcher still has `[ -f tests/tests_m4.py ] && { ... scp tests/tests_m4.py ... }`, which copies the file twice, to `m4_run/` and `m4_run/tests/`.
   - `tests/tests_m4.py` exists locally, so the launcher would ship the author's tests to the box.
   - The operator finding says the payload excludes the tests, but the launcher does not match it.
   - Remove the conditional scp, and the comment's reference to the tests file, before launch.

2. **BLOCKING.** `run_m4.py:3189-3193` (`stage_capability`), with `run_m4.py:1741` and `onbox_m4.sh:726-733`. EXEC_NOTE item 3 and item 6 (H4, H5).
   - Item 3 says that after a fixer restart the lock is recomputed and the records carry the label "environment changed by the fixer on the box; lock <hash>" when it differs. Only a second mismatch at this very check is final.
   - `onbox_m4.sh` implements this. It sets `ENV_CHANGED_BY_FIXER=true`, writes the label and continues.
   - `stage_capability` raises `HarnessFailure(kind="env_lock")` whenever `expected != observed`. It does not check `state.environment_changed_by_fixer`.
   - So any hold that ends with a changed environment (the main purpose of the fixer) restarts, then fails at the capability stage as exit 2, final.
   - That spends the hold time and a restart on a path that cannot produce a valid record.
   - Fix: when `environment_changed_by_fixer` is set, record the mismatch and the label and continue. Keep a mismatch with no fixer change, or a second mismatch at this check, as exit 2.

3. **ADVISORY.** `lambda_run_m4.sh:225`. Directive "Box" section: fetch `held_attempt_1/` if present.
   - The launcher fetches only `results_m4/out`.
   - `held_attempt_1/` is a sibling of `out/`, so the first attempt's records are lost at termination after a restart.
   - Add a best-effort `scp -r` of `results_m4/held_attempt_1`.

4. **ADVISORY.** `onbox_m4.sh:789` against `run_m4.py:1402-1411` and `:132-133`. EXEC_NOTE item 8.
   - The outer timer fires at `STOP_AT - 600`.
   - The runner's allowances run to `STOP_AT - 500`, and the 100 s endpoints slot sits between them.
   - If earlier stages use their full ceilings, the endpoints stage can be cut by the timer.
   - `--finalize` then closes the run as `unmeasured_by_stop:outer_timeout`. Money is bounded and a valid record is still written.

5. **ADVISORY.** `onbox_m4.sh:785-786`. EXEC_NOTE item 10.
   - `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` are unset before the runner starts, so downloads in the runner never see the token.
   - The named sources (RCSB and the AlphaFold parameter storage, `run_m4.py:279-281`) need no token, so there is no leak and no failure. The wording "used by downloads only" is satisfied more strictly than required.
   - Before the unset, `nvidia-smi` and `pip freeze` run with the token in their environment. Nothing prints it.

## Checks that passed

- **Operator finding 1 (`M4_BASE`).** `run_m4.py:5615` reads it only as a fallback after `--base`. `onbox_m4.sh:803` always passes `--base "$RUN_DIR"`, so a missing value changes no path.
- **Operator findings 2 to 4.** The tests log has 46 of 46 passed and ends with `TESTS: PASS`. Its tests call the runner through the stage interface (per-stage names such as `anchor_calls_kept_apart`). `onbox_m4.sh` and `run_m4.py` no longer reference the tests, and the shell ships nothing of the tests.
- **Item 8 (cost and time).** `onbox_m4.sh` reads `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD` and `REMOTE_TIMEOUT` and caps them at 5 and 7200. It computes `STOP_AT` as the lesser of the two caps. The runner uses `M4_T0_EPOCH`, and its ceilings sum to 7200. Inner tool calls are cut at `STOP_AT - 700`, which is 100 s inside the outer kill.
- **Item 9 and rule 5 (downloads and writes).** No `sudo`, `apt-get` or `pip install` appears in either script. The two named download URLs are recorded. Caches are under `~/m4_run/`.
- **Item 10 (secrets).** `.keys` is read only by the launcher. `env.txt` lists named variables only.
- **Item 6 (hold, H1 to H5).** All five behaviours are present in `onbox_m4.sh`. The hold is capped at 2400. `RESUME` is checked by sha256 of `run_m4.py`. The restart needs at least 1500 s left. There is one hold per launch. The sleep check is excluded from the hold.
- **Launcher against `frozen/lambda_run.sh`.** The differences are only at declared points: remote dir, payload, bootstrap name, fetch paths, forwarded environment, the filesystem attachment, `REMOTE_TIMEOUT` default and the header, plus finding 1. The EXIT-trap teardown, `terminate()` retry, `on_signal` and `BACKSTOP_ARMED`, the self-destruct backstop, `setsid`, the `RUN_DONE` poll, the CRLF guard, the unhealthy-box aborts and the fetch ordering are intact.
- **`remote_run_m4.sh` against `frozen/remote_run.sh`.** They differ only in the `cd` line.
- **Item 8 of the checklist (onbox command).** `build30_return.json` gives `bash remote_run_m4.sh bash onbox_m4.sh`. The launcher runs `bash remote_run_m4.sh bash $RUNNER`, and `$RUNNER` is `onbox_m4.sh`.
- **Item 7 (exit table).** The exit trap, the minimal void and the `RUN_DONE` marker routes in `onbox_m4.sh` match it. The exit codes are 0, 2, 3 and 4.
- **Not verified.** The full `run_m4.py` record, label and calibration code (items 11, 12, 20, 21, 22, 25, 28, 29) was not read line by line. It rests on the local tests log and the single-line checks above.
