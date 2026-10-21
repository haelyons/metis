# Review 5 of build 10 (execution layer, tag m4)

Verdict: PASS. 0 blocking, 3 advisory.

Read: operator findings, EXEC_NOTE (57 items), GATE_COMMIT (Pre-authorisation, addendum 7), `run_m4.py` (the `git diff` against build 9 in full, plus targeted reads: environment reads, `.keys` line, test-hook names), `onbox_m4.sh` (whole), `lambda_run_m4.sh` and `remote_run_m4.sh` (diffed against the frozen files), `frozen/ONBOX_CONTRACT.md` (checked against, with G3 / EXEC_NOTE item 56 applied; its four points are not cited), the selftest log, the build's return, the pip pins check. I ran nothing.

## Findings

1. **ADVISORY.** `out/build10_return.json` does not exist. Concerns checklist 8 and EXEC_NOTE item 57 (the return states line counts, hashes, count, changed lines).
   - The return of build 10 is in `out/build9_return.json` (overwritten, modified in git) and in `out/wf-build-20261021-1453/out/result.json`; the two are identical.
   - It states 7,127 and 637 lines, the two sha256 values, 677 of 677, the changed places, and `onbox_command` = `bash remote_run_m4.sh bash onbox_m4.sh`.
   - Those values match the files on disk (`sha256sum`, `wc -l`) and `out/BUILT_HASHES_build10.txt`. The command is what the launcher runs: the launcher's detached line runs `bash remote_run_m4.sh bash $RUNNER`, with `RUNNER` the third argument (`onbox_m4.sh`), and `remote_run_m4.sh` runs its arguments.
   - Operator note: the file name the review brief names is absent; the evidence is intact elsewhere.

2. **ADVISORY.** `onbox_m4.sh:45-65`; `run_m4.py:4618`. Concerns operator finding 1 and standing rule 8 / EXEC_NOTE item 48(d). Verified, unchanged from build 9.
   - `M4_SHELL_TEST`, `M4_TEST_ROOT`, `M4_TEST_RUNNER`, `M4_TEST_BIN` and `M4_TEST_INSTALL_CEILING_S` are read only between `# BEGIN TEST HOOKS` and `# END TEST HOOKS`, and only when `M4_SHELL_TEST` is exactly `1`. The launcher forwards none of them, so a real run is unaffected.
   - Defaults: `INSTALL_CEILING_S=1800`, `RUN_DIR` the script's own directory.
   - `M4_BASE` (`run_m4.py:4618`) is a fallback after `--base`; the shell always passes `--base`.
   - Recorded so the operator's finding is closed.

3. **ADVISORY.** `run_m4.py:7068`. Concerns operator finding 2 and standing rule 8 / EXEC_NOTE item 5. Verified, not a leak.
   - The only `.keys` text (other than `dict.keys()` calls) is a selftest regex run over the program's own source. Nothing reads the key store.
   - No `env`, `printenv` or `set` dump exists; `env.txt` lists named non-secret variables only (`onbox_m4.sh:138-158`). `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` are unset at `onbox_m4.sh:518-519` before the runner starts and are never written out.

## Checklist

1. EXEC_NOTE items: the build is an in-place edit of build 9, which review 4 found complete apart from item 33's OpenMM form. The diff touches only item 57's list; no changed line falls outside it (see item 6 below). No item is missed.
2. Cost and time: `onbox_m4.sh:83-123` reads `PRICE_USD_PER_HOUR` (default 1.99), `BUDGET_LEFT_USD` (clamped to at most 5) and `REMOTE_TIMEOUT` (clamped to at most 7200; unset is labelled). `STOP_AT` is min(budget / price x 3600, timeout) from a T0 that includes the bootstrap. The outer kill is `STOP_AT - elapsed - 600` and a short `OUTER` gives a code-3 void. The ceilings sum to 7,200 s, which equals `REMOTE_TIMEOUT`; the allowance formula holds each stage inside it.
3. Records: unchanged from build 9 except `write_minimal_void`. Its new `standing()` keeps a decided C record decided and never rewrites it. A record whose `void_reason` or `notes_list` carries "unmeasured, not holding" is not treated as decided, so the shell's own voids and the runner's stop voids are still replaced as before. Code 4 voids all four. A failed anchor or gate still voids every later record.
4. Secrets: see findings 2 and 3. The token is used only by the frozen bootstrap's downloads.
5. Writes only under `~/m4_run/` (caches `TMPDIR`, `PIP_CACHE_DIR`, `XDG_CACHE_HOME`, `MPLCONFIGDIR`, JAX and colabfold caches all set under `RUN_DIR`). Nothing is interactive. `sudo` appears only at `onbox_m4.sh:423` and `:456` (`sudo -n env DEBIAN_FRONTEND=noninteractive apt-get update` and `install` of `python3-venv aria2 curl`). The new pin `openmm-cuda==8.1.1.12` comes through pip with `--report`, so its URL and hash are recorded like the other pins. The operator's index check (`out/pip_pins_check_build10.txt`) finds 9 of 9 pins, none missing or unpinned, no extra undeclared.
6. Launcher and bootstrap: `lambda_run_m4.sh` differs from `frozen/lambda_run.sh` only in the header comment, the remote directory, the payload lines, the forwarded variables (`PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD`, `INSTANCE_TYPE`, `REMOTE_TIMEOUT`), the bootstrap name, the fetch paths (plus the `RUN_VALID.json` fetch) and the `REMOTE_TIMEOUT` default 7200; all are declared in its header. The `timeout $REMOTE_TIMEOUT` wrapper, `setsid`, the marker poll, the fetch retry loop and the termination logic are unchanged. `remote_run_m4.sh` differs from `frozen/remote_run.sh` only in its `cd` line. Item 57's scope holds for the two build files: the `run_m4.py` diff is the `PIP_PINS` comment and list, `pip_pins_problems`, its selftest cases, the planted-record hook in the stand-in program and two new flows; the `onbox_m4.sh` diff is inside `write_minimal_void`.
7. Selftest log: `selftest: 677 of 677 checks passed`, the two hashes (matching the files), `selftest: elapsed 15.3s`, last line `selftest: PASS`. The count is plausible against build 9's 658: the two shell flows and the pin cases are in, and the replaced bracketed-extra cases are out.
8. See finding 1.
