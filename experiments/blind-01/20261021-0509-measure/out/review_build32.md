# Review of build 32 (tag m4)

Scope: fix build for the capability stage that failed on launch 11. Files read: operator findings, EXEC_NOTE, GATE_COMMIT section headings and addenda index (the file is over the read limit; the EXEC_NOTE restates the binding terms), run_m4.py (diff and the fix site), onbox_m4.sh, lambda_run_m4.sh, remote_run_m4.sh, the frozen files, tests_local_build32.log, build32_return.json.

Checked and found sound:
- Fix matches the evidence. `collect_labels(state)` at run_m4.py:3205 sets `state.gpu_visible` (run_m4.py:2052) before the test at run_m4.py:3207. `collect_labels` is cached (run_m4.py:1935), so a later call from the env-check path repeats nothing. The diff is 4 inserted lines in one file. It changes no protocol, record field or guard.
- File hashes on disk equal the build return: run_m4.py 38d0b5fb..., onbox_m4.sh 9c1a1067... (item 8 of the checklist).
- onbox_m4.sh is unchanged from the launched version and carries items 3, 6 (H1 to H5), 7, 8, 25 and 29 as before. `STOP_AT` is the lesser of the dollar cap and `REMOTE_TIMEOUT`; the outer timer is `STOP_AT - elapsed - 600`.
- The launcher copy differs from frozen/lambda_run.sh only at the declared points (remote dir, payload, bootstrap name, fetch paths, forwarded variables, file_system_names, header). The billing-safety mechanisms are present. remote_run_m4.sh differs from the frozen copy only in the `cd` line.
- Nothing reads `.keys` in run_m4.py or onbox_m4.sh. No environment dump. No sudo, apt or pip in either file.
- tests_local_build32.log ends with `TESTS: PASS` (46 of 46). Its tests are the stage-interface tests.
- Operator finding 3 (env/box.sh) is outside the payload.

Findings:

1. ADVISORY. EXEC_NOTE "Box / Caps": launch 11 was the one pre-authorised launch; "a launch after 11 needs a new addendum". This build is for a launch 12. The gate must hold that addendum before the launcher runs. It is not an execution-layer defect.
2. ADVISORY. onbox_m4.sh:785-786 (EXEC_NOTE item 10). `HF_TOKEN` is unset before the runner starts, although the downloads run inside the runner. The two named sources need no token, so no money is at risk. The token is never read by anything after the unset, which is the safe direction.
3. ADVISORY. frozen/remote_run.sh:29-48 (EXEC_NOTE item 32). The frozen bootstrap runs `pip install --upgrade` on a cold box. It is the operator's, it ran on launches 9 to 11, and it is not recorded by the build.
4. ADVISORY. out/pip_pins_check_build32.txt does not exist, so the pins check was not available to review. The environment is the lock-hashed artifact; the lock check is on the box.
5. ADVISORY. onbox_m4.sh:176 and :379 (EXEC_NOTE item 25). The shell's void and compute writers rely on `python3` on the system PATH; the venv is already first on PATH after activation. No money impact.
