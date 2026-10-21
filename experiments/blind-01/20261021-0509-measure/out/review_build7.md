# Review of build 7 (m4), execution layer

Read: operator_findings_build7.txt, EXEC_NOTE.md, GATE_COMMIT.md (Pre-authorisation, addenda 3 and 5), run_m4.py (whole file), onbox_m4.sh, lambda_run_m4.sh, remote_run_m4.sh, frozen/lambda_run.sh, frozen/remote_run.sh, frozen/provenance.py, out/selftest_build7.log, out/build7_return.json. Nothing was run or edited. The sha256 values in the selftest log and the build return agree with each other; I could not re-hash the files on disk, so the operator's own re-run comparison (B14) still stands as the check.

Verdict: FAIL. 7 blocking, 10 advisory.

## Operator findings, verified

- Operator 1 (`M4_BASE`): `run_m4.py:3859` reads it only as a fallback after `--base`; `onbox_m4.sh:234` always passes `--base "$RUN_DIR"`. Not a defect.
- Operator 2 (`.keys`, `run_m4.py:5389`): a selftest regex over the program's own source. Nothing reads `.keys`. Not a defect.
- Operator 3 (files touched): only run_m4.py and onbox_m4.sh are new under the run directory. Consistent with item 2.
- Operator 4 (contract binding): noted; see finding 13 on the contract's docking order.

## BLOCKING

1. **BLOCKING. `onbox_m4.sh:237` and `:279-281` (EXEC_NOTE items 29, 32, 31(i), 46; GATE E23, B12).** `set -e` is turned on at line 237. On the outer-timeout route the script runs `run_m4.py --finalize`, which returns 3 (`run_m4.py:3880-3883`, `run_stages` returns `EXIT_GUARD` after `record_stop`). A non-zero status under `set -e` aborts the script before `RC=3` runs. The EXIT trap (`:128-136`) sees `FINISHED=0`, calls `write_minimal_void 2`, and overwrites `RUN_VALID.json` (run_valid false) and `RUN_DONE` (exit 2). The outer-timeout route therefore ends as exit 2 with run_valid false instead of exit 3 with run_valid true. That is a launch spent with the wrong outcome, and A2(b) cannot read it as a time-guard stop. The selftest never runs the shell script, so it does not see this.

2. **BLOCKING. `run_m4.py:3875-3883` with `:1137-1149` (items 29, 30, 46; GATE B2, E22).** `--finalize` builds a fresh `RunState`. Every input starts as "unmeasured", `anchor` is None, `stages_done` is empty and run_valid is true. Only the endpoint files are re-listed (`:3879`). `RUN_DONE`, `RUN_VALID.json` and the summary written by finalize therefore report inputs that were decided before the timeout (for example C3) as "unmeasured_by_a_stop". The per-input status is what A2(b) reads to decide which inputs to rerun, and a relaunch of a decided input is not authorised. Status must be rebuilt from the records on disk.

3. **BLOCKING. `run_m4.py:2133-2137` (MD worker), `:3524-3530` (`stage_storage`) (item 16, item 6 for C4).** Item 16 requires C4 to count the MD trajectory and every log of one 0.5 ns segment, with the frame interval recorded. The worker writes no trajectory (no DCD or XTC reporter) and records no frame interval. The "dynamics trajectory and logs" artifact is the whole `md_<pair>` work directory, which holds `system.xml`, `solvated.pdb`, the build and run JSON files and the reporter CSV. The C4 value is therefore not the quantity item 16 defines, and `md_bytes_per_ns` is computed from the wrong bytes.

4. **BLOCKING. `run_m4.py:3093-3103` (item 28; item 29, E17).** A pair whose docking reaches its 250 s cap is kept as a `truncated` row, but the code then `break`s the pair loop. The remaining pairs never run, although item 28 says C3 stays decided when at least 2 pairs finished. A slow first pair gives n=0 and C3 VOID with pairs 2 and 3 unattempted. The loop must continue past a per-pair cap and stop only when the stage allowance is gone.

5. **BLOCKING. `onbox_m4.sh:94-125` used at `:226-228` and `:295` (item 29, item 8).** `write_minimal_void` always writes `run_valid: false`. At `:226` it is called with code 3 ("no time left after setting up"), which item 29 defines as a guard stop that leaves run_valid as it was. At `:295` it is called with whatever `RC` the runner returned (0, 3 or 4), and records run_valid false against that code. The exit code and run_valid disagree with the rules for exit 3 (and exit 0).

6. **BLOCKING. `run_m4.py:296-305`, `PIP_PINS` (item 33, GATE B6 and E12).** Item 33 says the build chooses the package form whose metadata carries the CUDA platform for OpenMM. The pin is plain `openmm==8.2.0`. As far as I recall the PyPI wheel carries CPU and OpenCL, with CUDA coming from an extra or a separate `openmm-cuda-12` package. The build did not choose a CUDA form, so the smoke check (`:2398-2405`) would fail at the paid install stage. The operator should check the pinned release's `provides_extra` before launch. This rests on recollection, which the gate says is not a ruling, so the operator's metadata check decides it, but the item is not carried as written.

7. **BLOCKING. `onbox_m4.sh:167-180` (item 28: "every apt ... call takes min(its own limit, ...)", item 8).** `apt-get update` (up to 10 tries with 15 s sleeps) and `apt-get install` have no `timeout`. They run inside the paid window before any guard exists. Their duration is only counted afterwards (`M4_APT_SECONDS`), so a stalled mirror can spend the whole install ceiling or more with no void record until the launcher's own 7,200 s timeout. Each call needs a limit drawn from the 1,800 s install total.

## ADVISORY

8. **ADVISORY. `run_m4.py:168-171`, `:2505`, `:2910` (item 28).** "Controls and anchor 700, shared": each stage takes its own 700 s allowance, so the pair can use up to about 770 s. The 400 s margin absorbs it, but it is not a shared total.

9. **ADVISORY. `run_m4.py:2586-2635` (item 20).** The unit-and-scale record holds worked examples only. Item 20 lists raw AlphaFold seconds, MD engine rate lines and raw bytes. Those values cannot exist before the controls under item 1's order, so the directive contradicts itself; the raw values do appear in the rows files. Say so in the record, or update it at the endpoints stage.

10. **ADVISORY. `run_m4.py:1194-1195`.** `spend_usd` adds `pre_t0_seconds` to `elapsed_s`, but `t0` already includes the bootstrap (`onbox_m4.sh:69-70`). The reported `estimated_spend_usd` double counts the bootstrap. The guard uses `stop_at_s`, so only the report is wrong.

11. **ADVISORY. `onbox_m4.sh:94-125` (items 3, 8, 9).** The shell's minimal void records carry no `unit`, `card_value` or `band` in `values`, and the shell writes neither `env.txt` nor `m4_summary.json` on an early abort. The `REMOTE_TIMEOUT` it saw is then recorded nowhere except the log. The launcher's summary-fetch loop will wait about 50 s in that case.

12. **ADVISORY. `run_m4.py:2316-2343` (item 39), unverified.** The parameters are extracted into `<data>/params` and checked, but nothing writes a completion marker. As far as I recall ColabFold checks a `download_*.txt` marker under `params/` and fetches its own archive when it is absent. If so, the first timed call downloads inside the timed call, `download_in_timed_call` fires and C1 is VOID with exit 0, which A2 does not allow a relaunch for. The smoke check does not exercise this path.

13. **ADVISORY. `run_m4.py:2678`, `:2715-2744` (item 42, E13 accepted risk), unverified.** The docking sequence is setup, simulate, `lgd_rank.py`. There is no step that generates conformation PDB files (earlier builds called `lgd_generate_conformations.py`; build 7 does not), and the top pose is read from `swarm_<n>/lightdock_<id>.pdb`. A missing pose file is exit 2 (correct under E8b), but the first paid anchor may die there. Separately, `-s 2` swarms over a whole-capsid receptor makes a contact-overlap pass improbable; an anchor miss is a result and no relaunch is authorised.

14. **ADVISORY. `run_m4.py:2275-2279` (item 34, E14), unverified.** `pip install --report` needs pip 22.2 or later. Ubuntu 22.04's bundled venv pip is 22.0.2, and E14 forbids upgrading it. If so the install step fails at once as exit 2 after the apt step. The operator should confirm the box's venv pip version.

15. **ADVISORY. `lambda_run_m4.sh:41`.** The copy keeps the frozen default `REMOTE_TIMEOUT=${REMOTE_TIMEOUT:-5400}`. A launch without `REMOTE_TIMEOUT=7200` in the environment forwards 5400 and the run stops earlier than A1 intends. It is safe, but the launch line must set it.

16. **ADVISORY. `run_m4.py:3742`, `:2889` (item 46).** After an anchor miss (exit 4) C1 to C4 are written with the label "unmeasured, not holding" and `RUN_DONE` reports them as "unmeasured_by_a_stop", although there was no stop. A reader of `RUN_DONE` alone cannot tell an anchor miss from a stop without reading `voided_by`.

17. **ADVISORY. `run_m4.py:4695-5340`, `onbox_m4.sh` (item 47).** The selftest never runs the shell script or the `--finalize` path. Findings 1, 2 and 5 sit entirely in that gap. Add a shell-level check (planted runner exit codes) or a finalize flow with a pre-decided input.

## Checklist summary

1. EXEC_NOTE items carried: all except 16 (finding 3), 28 (findings 4 and 7), 29 (findings 2 and 5), 32 and 46 (findings 1 and 2), 33 (finding 6).
2. Cost and time: caps read and clamped; projected 4,000 to 6,300 s fits 7,200; apt is the unbounded step (finding 7).
3. Records: convention implemented; a failed anchor or sleep voids later records; finalize loses decided status (finding 2).
4. Secrets: clean. Nothing reads `.keys`, no environment dump, the token is removed before the runner starts and from every child environment.
5. Writes and sudo: under `~/m4_run/` only; sudo only as declared.
6. Launcher: differs from frozen only at declared points; billing-safety blocks intact. `remote_run_m4.sh` differs only in its `cd` line.
7. Selftest log ends `selftest: PASS`, 418 of 418, plausible for the parsers and planted cases.
8. `onbox_command` is `bash remote_run_m4.sh bash onbox_m4.sh`, which is what the launcher runs with `RUNNER=onbox_m4.sh`.
