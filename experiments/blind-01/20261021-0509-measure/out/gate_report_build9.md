# Operator's note to the gate (mechanical; the operator has not read the findings)

Review 4 of build 9: FAIL, 1 blocking, 3 advisory (earlier: 6, 11, 7 blocking). Build 9 edited build 7's files in place as the directive asked; selftest 658 of 658; all eight pins exist on the index, one extra is not declared by its release (out/pip_pins_check_build9.txt).

Rulings asked: (a) rule on the one blocking finding: if it is a code change, authorise build 10 as an in-place edit limited to that change and to any advisory item you choose to make binding; if it is a directive matter, settle it in the directive; (b) for each advisory finding, accept as-is for launch 1 of record or make it a numbered item; (c) pre-authorise launch 1 on build 10 when review 5 reports zero blocking findings, with the launch environment values restated (REMOTE_TIMEOUT, BUDGET_LEFT_USD, PRICE_USD_PER_HOUR, INSTANCE_TYPE, region).

# Review 4 of build 9 (the reviewer's file, verbatim)

# Review 4 of build 9 (execution layer, tag m4)

Verdict: FAIL. 1 blocking, 3 advisory.

Read: operator findings, EXEC_NOTE (54 items), GATE_COMMIT (pre-authorisation, addenda 3, 5, 6), run_m4.py (targeted: pins, downloads, argument parsing, environment reads, install stage, entry point), onbox_m4.sh (whole), lambda_run_m4.sh, remote_run_m4.sh, both frozen shell files, frozen/ONBOX_CONTRACT.md (checked against; see finding 3), selftest log, build return, pip pins check. I ran nothing.

## Findings

1. **BLOCKING.** `run_m4.py:405` (`"openmm[cuda12]==8.2.0"`, with the comment at lines 381-392). Concerns EXEC_NOTE item 33 (the OpenMM requirement is written in the form that pulls the CUDA platform) and GATE_COMMIT F6 (a metadata mismatch is a build re-run). The operator's index check (`out/pip_pins_check_build9.txt` line 7) reports `EXTRA-NOT-DECLARED openmm[cuda12]==8.2.0: extra cuda12 not in []`.
   - The pinned release declares no `cuda12` extra, so the chosen form does not pull the CUDA platform.
   - pip will normally install plain `openmm` and continue. The smoke check at the end of the install stage (`Platform.getPlatformByName("CUDA")`) would then fail, and the launch would end as exit 2 after the box is paid for, with no measurement. A2(a) would be consumed.
   - The code comment itself says this outcome is the one the operator's check exists to catch. The other seven pins are found, with none missing or unpinned.
   - The fix is a build re-run, not a hand edit. Use a sibling pinned requirement whose distribution name starts `openmm-cuda`, and confirm it against the index.

2. **ADVISORY.** `onbox_m4.sh:361-366` (`apt_limit`), `:380`, `:413`, and `:494-503`. Concerns EXEC_NOTE items 28 and 48(c) and GATE_COMMIT F7.
   - F7 gives the apt limit as min(own limit, 1,800 minus install seconds used, REMOTE_TIMEOUT minus elapsed minus 500). The shell implements the first two terms only.
   - The "no time left after setting up" check comes after the apt stage, so a very small REMOTE_TIMEOUT would still let apt run up to 1,800 s.
   - It cannot bind at the authorised REMOTE_TIMEOUT=7200 with BUDGET_LEFT_USD=5. Apt is capped at 1,800 s total, 300 s for the update loop, and the elapsed bootstrap is far below 4,900 s. Spend stays inside the caps, so this is advisory under F22's definition.
   - The selftest flow for `REMOTE_TIMEOUT=10` passes only because the stub `sudo` is instant.

3. **ADVISORY.** `frozen/ONBOX_CONTRACT.md` items 2, 3 and 9 versus the directive.
   - The contract expects `env_<tag>.json`, an exit code 5, a timed dry run on the real input that feeds the guard, and says the script never writes RUN_DONE.
   - The directive (EXEC_NOTE items 8, 20, 43 and 46) defines exit codes 0, 2, 3 and 4, has the runner and shell write `RUN_DONE`, and uses estimate floors instead of a dry-run rate. The build follows the directive, which the contract allows to tighten but not loosen.
   - None of these would spend money without a valid record. Recorded for the operator.

4. **ADVISORY.** `onbox_m4.sh:284-287`. Concerns EXEC_NOTE item 54.
   - When the runner dies without writing `RUN_DONE`, `write_minimal_void` rewrites `RUN_VALID.json`. It marks all four inputs void with the shell's status, even when the runner had already written decided C records.
   - Those records stay on disk (`put` never overwrites them), but `RUN_VALID.json`'s `inputs_status` and the summary (written only if absent) can disagree with them. The run_valid value itself follows the item 8 table.

## Verified, no finding

- Operator finding 1:
  - The `M4_TEST_*` names and `M4_SHELL_TEST` are read only between `# BEGIN TEST HOOKS` and `# END TEST HOOKS` (`onbox_m4.sh:44-66`), and only when `M4_SHELL_TEST` is exactly `1`. The launcher forwards none of them, so they are inert in a real run.
  - `M4_BASE` (`run_m4.py:4606`) is a fallback after `--base`, and the shell always passes `--base`.
- Operator finding 2: `run_m4.py:6983` is a selftest regex over the program's own source. Nothing reads `.keys`. No `env`, `printenv` or `set` dump exists, and `env.txt` lists named non-secret variables only.
- HF_TOKEN is unset at `onbox_m4.sh:483-484` before the runner starts. The runner's `ToolRunner` strips both token names from every child.
- Caps (checklist 2):
  - PRICE defaults to 1.99. BUDGET_LEFT_USD and REMOTE_TIMEOUT are clamped to at most 5 and at most 7200. An unset REMOTE_TIMEOUT is labelled.
  - STOP_AT is min(budget / price x 3600, timeout), counted from T0 (bootstrap start from `ps etimes` plus 30 s, else 300 s with the label). The outer kill is 600 s inside STOP_AT.
  - The projected total is at most 7,200 s, which fits.
- Launcher, remote bootstrap and onbox_command (checklist 6, 8):
  - `lambda_run_m4.sh` differs from `frozen/lambda_run.sh` only at declared points: remote dir, payload, bootstrap name, forwarded environment, REMOTE_TIMEOUT default 7200, fetch lines, header.
  - Trap teardown, the terminate retry loop, `BACKSTOP_ARMED`, the backstop, setsid, the marker poll, the CRLF guard and the unhealthy-box aborts are unchanged.
  - `remote_run_m4.sh` differs from `frozen/remote_run.sh` only in its `cd` line.
  - The build return's `onbox_command` is `bash remote_run_m4.sh bash onbox_m4.sh`, which matches what the launcher runs.
- Selftest (checklist 7): `out/selftest_build9.log` has 658 of 658 checks, ends with `selftest: PASS`, and its file hashes match the files on disk.
- Shell routes (checklist 3, 5): no `set -e`, every runner, finalize and timeout call uses `RC=0; ... || RC=$?`, the trap acts only while `FINISHED=0`, and sudo is only the declared `apt-get` calls. Nothing is written outside `~/m4_run/`.
- Downloads come from RCSB, the AlphaFold storage address, and pip and apt, with URL and hash recorded.
