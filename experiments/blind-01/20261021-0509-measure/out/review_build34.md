# Review of build 34 (m4 execution layer)

Verdict: PASS. 0 blocking, 6 advisory.

Basis: I read the files named in the prompt. The runner (6,547 lines) I sampled at the points the checklist names (lock check, guard arithmetic, child environment, stage order, failure kinds, `--stage` interface) and did not read line by line. I ran nothing.

Checklist result:
- (1) Items 1-29 are present in the code at the points sampled. The hold behaviours H1-H5 are all in `onbox_m4.sh` lines 937-1063.
- (2) The shell reads `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD` and `REMOTE_TIMEOUT` and caps them at 5 and 7200. The runner's guard follows `min(remote_timeout, dollar cap)`. The projected 4,000-6,800 s fits 7,200 s.
- (3) The records convention and the voiding after an anchor miss are implemented (`write_record`, calibration branch). The 50 local tests cover them.
- (4) Nothing reads `.keys`. No environment dump: `env.txt` lists named variables only. `child_env` strips both token variables.
- (5) The shell and runner write under `results_m4/` and the run's own cache directories. No sudo, pip or apt calls are in either file. The downloads are RCSB 6IHB and the AlphaFold parameter archive on googleapis.
- (6) `lambda_run_m4.sh` differs from the frozen launcher only at the declared points. The billing-safety lines (self-destruct, deadline, marker poll) are unchanged. `remote_run_m4.sh` differs from `frozen/remote_run.sh` only in its `cd` line.
- (7) The tests log ends with `TESTS: PASS` (50 of 50). The tests use the stage interface.
- (8) The `onbox_command` is `bash remote_run_m4.sh bash onbox_m4.sh`. The launcher runs `bash remote_run_m4.sh bash $RUNNER` with `RUNNER` as its third argument.

Findings:

1. ADVISORY. `lambda_run_m4.sh:210-213,225` (EXEC_NOTE "Box", launcher fetch list; item 6 H4). The launcher fetches `results_m4/out/` only. After a hold and restart, `onbox_m4.sh:1043` moves the first attempt to `results_m4/held_attempt_1/`. That directory is never fetched, so the first attempt's records stay on the box and are lost when it terminates. This costs no money and spoils no record, but it defeats the "kept whole" intent of H4. Fix in the operator's launcher: add a fetch of `m4_run/results_m4/held_attempt_1`.

2. ADVISORY. `onbox_m4.sh:789` against `run_m4.py:1409` (item 8, item 24). The outer timer is `STOP_AT - elapsed - 600`, but the runner's own stage allowance runs to `remote_timeout - 500`. A run that reaches the last stages will be cut by the outer timer, which closes it through `--finalize` (exit 3 or 4), about 100 s before the guard would have stopped it. This is clean, not a money risk.

3. ADVISORY. `onbox_m4.sh:785-786` (item 10). The tokens are unset before the runner starts, not after its downloads. The two download sources are public, so nothing is lost, and the secret stays safe. It differs from the item's wording.

4. ADVISORY. `run_m4.py:5701`, `onbox_m4.sh:803` (operator finding 4). `M4_BASE` is read on the box, but neither the launcher nor the shell sets it. The shell passes `--base "$RUN_DIR"` to `--run` and `--finalize`, so the fallback is never reached on the box. Harmless.

5. ADVISORY. `frozen/remote_run.sh` (item 32; item 5 "writes only under ~/m4_run/"). The frozen bootstrap runs `pip install --upgrade` into `~/.local` and writes `.setup_ready` before `onbox_m4.sh` starts. This is the operator's code, not the build's. The activated venv does not use the user site, so it cannot shadow the environment of record.

6. ADVISORY. `out/pip_pins_check_build34.txt` does not exist, so I could not check the package-index result for the runner's pins. I also could not check the forwarded `ENV_LOCK_SHA256` value against lock 7dde3c7d5ad3f34f. The code compares the hash of `pip freeze` with the forwarded value and installs nothing (`onbox_m4.sh:682-743`; `run_m4.py:3232-3290`), which is what operator finding 3 asked me to confirm. The operator should check that the value passed at launch is the full 64-character hash of the lock.
