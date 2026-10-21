# Review of build 26 (m4 execution layer)

Verdict: PASS. 0 blocking, 6 advisory.

Verified:
- `run_m4.py` is 5,116 lines, sha256 c6617c8b…, and `onbox_m4.sh` is 979 lines, sha256 8d7b9d29…. Both match `BUILT_HASHES_build26.txt` and the build return.
- `git diff 461c939 5be1d53` shows 56 insertions and 0 deletions in `run_m4.py`, in three hunks. No other file changed.
- The hunks are `pose_frame_shift` (3640-3686), the translation call in `score_pose_against_native` (3706-3711) and the `frame_shift` field (3728).
- The shift is applied after chain-role mapping and before any contact, overlap or RMSD computation (EXEC_NOTE item 17: capsid frame, no superposition).
- The tolerances, the decision rule (`anchor_decision`) and the `ANCHOR_*` constants are untouched.
- The serial-versus-parallel RMSD is unaffected, because both poses get the same shift.
- Checklist 1-2: items 3, 4, 5, 6 (H1-H5), 7, 8 and 27 are carried in `onbox_m4.sh` and are unchanged from the reviewed build.
  - Price, budget and timeout are read from the environment and clamped to 5 and 7200.
  - `STOP_AT` and the outer timer are computed from them.
  - The stage ceilings sum to 7,200.
- Checklist 3: the record convention, the void propagation and the shell minimal void are unchanged. The anchor FAIL gives exit 4 and voids C1 to C4.
- Checklist 4: no `.keys` read on the box, no environment dump (`env.txt` lists named variables only), and the token is unset before the runner starts.
- Checklist 5: no sudo, apt or pip install. `pip freeze` is the only pip use. Caches live under `~/m4_run/`.
- Checklist 6:
  - `remote_run_m4.sh` differs from `frozen/remote_run.sh` only in its `cd` line (27).
  - `lambda_run_m4.sh` differs from `frozen/lambda_run.sh` only at the declared points: remote dir, payload, bootstrap name, fetch paths, forwarded env, `REMOTE_TIMEOUT` default 7200, the attached filesystem and the header comment.
  - The terminate retry loop, `BACKSTOP_ARMED`, the self-destruct backstop, setsid and the `RUN_DONE` poll, the CRLF guard and the unhealthy-box aborts are intact.
- Checklist 8: `onbox_command` is `bash remote_run_m4.sh bash onbox_m4.sh`, and the launcher runs `bash remote_run_m4.sh bash $RUNNER` with `RUNNER=onbox_m4.sh`.

Findings:

1. ADVISORY. `lambda_run_m4.sh:225`, EXEC_NOTE Box section (fetch `held_attempt_1/`) and item 32.
   - The launcher fetches only `results_m4/out`.
   - After a hold and restart, the first attempt lives in `results_m4/held_attempt_1/`, a sibling of `out/`. It is not fetched before teardown.
   - `changes.log` is inside `out/`, so it is fetched.
   - The operator should fetch `held_attempt_1/` by hand if a hold occurs, before the box is terminated. The launcher is of record and unchanged.
2. ADVISORY. `lambda_run_m4.sh:168`.
   - `HOLD_SECONDS` defaults to `0` in the launcher when the operator does not set it, so no hold happens. The operator must export `HOLD_SECONDS=2400` (the value of record) for launch 10.
3. ADVISORY. `onbox_m4.sh:681-682` against item 10 ("unsets after the downloads").
   - The token is unset before the runner starts, so the runner's downloads from RCSB and the AlphaFold storage address run tokenless.
   - Both sources are public and launch 9's downloads passed, so there is no leak and no money risk.
4. ADVISORY. `run_m4.py:3640-3686`, item 17.
   - The fix assumes the docking code only translates the rigid capsid, and uses a mean-displacement shift with no rotation.
   - If the tool also rotates, the anchor can still miss. The result would be exit 4 with a valid void record, which is within the contract. The classifier's evidence (centre at the origin, overlap exactly 0) supports a translation-only gap.
5. ADVISORY. Closing section "Build 20" ("a changed line outside V1 to V4 is blocking").
   - Build 26's three hunks are outside V1 to V4. They are the operator-directed anchor-stage fix named in `operator_findings_build26.txt` item 3 and implement exactly it, so I did not treat them as blocking.
6. ADVISORY. Checklist items 7 and the optional pip-pins file.
   - `out/selftest_build26.log` and `out/pip_pins_check_build26.txt` do not exist.
   - EXEC_NOTE "Local selftest" says there is none and that selftests are not required. The author's tests run on the box, per the operator's note that the 48 tests passed in launches 6 to 9.
   - The launcher also ships `tests/tests_m4.py` into `m4_run/` as well as `m4_run/tests/` (line 119), which is harmless.
