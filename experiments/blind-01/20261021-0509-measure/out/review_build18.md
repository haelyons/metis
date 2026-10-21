# Review of build 18 (execution layer, tag m4)

Verdict: PASS. 0 blocking, 13 advisory.

I ran nothing. Findings come from reading `run_m4.py`, `onbox_m4.sh`, `lambda_run_m4.sh`, `remote_run_m4.sh`, the frozen files, the selftest log, the build return and the operator's findings.

## Checklist summary

1. EXEC_NOTE items 1 to 25 are carried in code.
   - Stage order is setup (environment, lock and capability checks), tests, downloads, controls, anchor, aux, af2, md, storage, endpoints (`run_m4.py:4605-4615`).
   - Lock check is `onbox_m4.sh:577-638`; capability check is `run_m4.py:2923-2973`; tests stage is `run_m4.py:2632-2726`.
   - Hold is `onbox_m4.sh:832-924`; ceilings are `run_m4.py:176-190`; labels are `run_m4.py:289-334`.
2. Cost and time.
   - The shell reads `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD` and `REMOTE_TIMEOUT` and caps them at 5 and 7200 (`onbox_m4.sh:66-95`, `118-120`).
   - The runner recomputes `stop_at_s` (`run_m4.py:1148-1171`) and uses it in the allowance (`run_m4.py:1947-1962`).
   - The ceilings sum to 7,200, which fits `REMOTE_TIMEOUT`.
3. Records.
   - The endpoint records, anchor record, `RUN_VALID.json`, summary and `RUN_DONE` are implemented.
   - A failed anchor sets `run_valid` false before the anchor record is written (`run_m4.py:3523-3529`), so every later record agrees.
4. Secrets.
   - Nothing reads `.keys` and nothing dumps the environment; `env.txt` is a named list.
   - Children get an environment without the token variables (`run_m4.py:1741-1756`).
5. Writes are under `~/m4_run/`, nothing is interactive, there is no sudo, and downloads come from the two named hosts with URL and sha256 recorded.
6. `remote_run_m4.sh` differs from `frozen/remote_run.sh` only in the `cd` line and its comment. `lambda_run_m4.sh` differs from `frozen/lambda_run.sh` only at the declared points (remote dir, payload, forwarded variables, filesystem attach, fetch paths, 7200 default, header). The trap, `terminate` retry, `on_signal`/`BACKSTOP_ARMED`, self-destruct backstop, setsid-detached run, `RUN_DONE` poll, CRLF guard, unhealthy-box aborts and ordering of the summary fetch before the full fetch are intact.
7. See finding 1. The log is not a selftest pass, as expected.
8. `onbox_command` is `bash remote_run_m4.sh bash onbox_m4.sh`, and the launcher runs `bash remote_run_m4.sh bash $RUNNER` with `$RUNNER` = `onbox_m4.sh`.

## Findings

1. ADVISORY. `out/selftest_build18.log`. Checklist 7, EXEC_NOTE "Local selftest" and U5. The log is an argparse error ("unrecognized arguments: --selftest") and does not end with `selftest: PASS`. The directive withdraws the selftest, so this is expected and not credited. Nothing local covers the measurement logic until the box runs `tests_m4.py`.
2. ADVISORY. `lambda_run_m4.sh:210-228`. EXEC_NOTE Box section, Q13, item 26. The launcher fetches only `results_m4/out/`. `results_m4/held_attempt_1/` is not fetched, so after a hold and restart the first attempt's failure records are lost when the box is terminated. Add a `scp -r ... results_m4/held_attempt_1` to the fetch block before the launch.
3. ADVISORY. `run_m4.py:2882-2913`. Item 4, item 27, operator finding 5. The capability check imports JAX and lists a GPU device but never compiles or runs a kernel. A CUDA compiler wheel or runtime mismatch would first show in the first AlphaFold call. That is after the controls, anchor and aux stages, so about 20 minutes and USD 0.7 would be spent before it surfaces (it would then be a real tool failure, exit 2, eligible for the hold). A one-line `jax.jit(lambda x: x + 1)(1.0).block_until_ready()` in `SMOKE_PY` would settle it before the physics.
4. ADVISORY. `onbox_m4.sh:438-531`, `596`, `680-681`; `remote_run_m4.sh:84-85`. Item 10. `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` are unset only inside `attempt_body` after the lock check. The `nvidia-smi`, `pip freeze` and python helper children before that inherit them. Nothing prints them, and no download uses them (the downloads run later in the runner), so the safe move is to unset both at the top of `onbox_m4.sh`.
5. ADVISORY. `onbox_m4.sh:866-873`. Item 6, item 8. The hold wait is bounded by `HOLD_SECONDS` but not by the time left in `REMOTE_TIMEOUT` or `STOP_AT`. At USD 1.99 the launcher's `timeout 7200` still caps spend at USD 3.98. At a price above USD 2.50, a late failure could hold past the dollar cap.
6. ADVISORY. `onbox_m4.sh:519-521`, `613-628`. Items 3, 19. When a fixer changed the environment, `env_check_tag-m4.json` is written with decision FAIL and `run_valid` false while the run proceeds and later records carry `run_valid` true. Item 3 asks only for the label. `finalize_from_disk` reads only `endpoint-*` records, so it does no harm, but the records disagree.
7. ADVISORY. `run_m4.py:2769-2773`. Item 9. The AlphaFold parameter archive's sha256 is computed and recorded but compared with no expected value, so "verified" is not met. There is no expected hash in the directive to compare with.
8. ADVISORY. `run_m4.py:1236-1239`, `4708`; `onbox_m4.sh:570`, `698`. Item 24, operator finding 4. `venv_bin()` takes `Path(sys.executable).resolve().parent`. A venv interpreter is normally a symlink, so `resolve()` would give the system `bin`, not the venv's. `M4_VENV_BIN`, exported by the shell, overrides it, so the real run is right. `M4_BASE` is the only name read on-box that nothing sets. Its default is the current directory, and the shell always passes `--base`, so it is never used.
9. ADVISORY. `run_m4.py:176-188`. Item 8. `controls` and `anchor` each carry their own 700 s ceiling, where item 8 gives one shared 700, and `storage` has an extra 100 that item 8 does not list. The total is still bounded by the `REMOTE_TIMEOUT - elapsed - 500` allowance, so no money is at risk.
10. ADVISORY. `onbox_m4.sh:409-416`. Item 1. The GPU visibility check runs before environment activation and the lock check. A GPU failure there goes straight to `finish 2` with no hold. This is harmless but departs from the stated order.
11. ADVISORY. `run_m4.py:4653-4655`. Item 22. A guard stop in setup, tests, downloads or controls only skips that stage. The later stages are gated on the anchor alone. For example, a guard stop in downloads means the anchor fails on a missing PDB as exit 2, not as a stop.
12. ADVISORY. `remote_run_m4.sh:28-48`; `lambda_run_m4.sh:119`, `168`. Item 28. The frozen bootstrap still runs `pip install --upgrade` against PyPI for the system python, which is operator-owned and reported only. The launcher skips `tests/tests_m4.py` silently if the file is absent (the runner would then void with `void_by_failure:tests`). `ENV_LOCK_SHA256` defaults to empty at the launcher (no pre-check), which on the box is exit 2 after the spend of bootstrap. Set it explicitly and confirm `tests/tests_m4.py` exists before launching.
13. ADVISORY. Whole files. EXEC_NOTE U1 to U9. I ran nothing, including `git diff`. `run_m4.py` went from 7,523 to 4,765 lines and `onbox_m4.sh` from 642 to 942. I read the files and found no change that is evidently outside U1 to U9, but I could not verify the line-level diff against the previous build. The operator's mechanical diff is the check for that.
