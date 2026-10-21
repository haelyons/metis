# Review of build 6 (tag m4), execution layer

Verdict: FAIL. 11 blocking, 15 advisory. Nothing was run and nothing was edited. Line numbers refer to `run_m4.py` (3,719 lines) unless another file is named.

Files read: operator findings, EXEC_NOTE.md, GATE_COMMIT.md (Pre-authorisation and addendum 3), run_m4.py (all), onbox_m4.sh, lambda_run_m4.sh, remote_run_m4.sh, frozen/lambda_run.sh, frozen/remote_run.sh, frozen/provenance.py, out/selftest_build6.log, out/build6_return.json.

## Operator findings, verified

1. `M4_OUT_DIR` (line 62) has a default, `HERE/results_m4/out`. `REMOTE_T` and `STOP_AT` are set by the `read` at onbox_m4.sh:57, before first use at line 70. None of the three is a defect.
2. Files written: only run_m4.py and onbox_m4.sh. Confirmed by the build return. The selftest log shows 253 of 253 and `selftest: PASS` as its last line. The log hashes equal the build return's hashes. The line counts (3,719 and 191) match the files as read.
3. `frozen/ONBOX_CONTRACT.md` is not on my read list and I did not read it. See finding 26.

## Checklist summary

1. EXEC_NOTE items carried item by item: not all. Misses are items 6, 8, 12, 13, 14, 17, 20, 28, 29 (anchor route), 30 and 33 (findings 1 to 11).
2. Cost and time: onbox reads PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and REMOTE_TIMEOUT, defaults at most 5 and 7200, and clamps (onbox_m4.sh:49-65, run_m4.py:407-446). Selftest covers the 1.99, 2.50 and 3.00 cases. The ceilings sum to 7,200 s. The install ceiling is not enforced as a stage total (finding 2). Bootstrap time before T0 eats margin (finding 19).
3. Records: convention implemented, with gaps in findings 9 to 11 and 15.
4. Secrets: clean. Nothing reads `.keys` or dumps the environment. `child_env` strips both tokens from every child (lines 277-283, 1283). onbox unsets them after the extract group (onbox_m4.sh:163). `env.txt` lists named variables only.
5. Writes under ~/m4_run: mostly. Exceptions are in finding 20.
6. Launcher copy: differs from frozen only at declared points, plus one extra scp line (finding 18). Billing-safety blocks (EXIT trap, terminate retry loop, on_signal and BACKSTOP_ARMED, self-destruct backstop, setsid run, RUN_DONE poll, CRLF guard, unhealthy-box aborts, criticals-first fetch) read identical to frozen. remote_run_m4.sh differs from frozen/remote_run.sh only at line 27 (the cd line).
7. Selftest log ends `selftest: PASS`. Counts are plausible for the parsers and planted cases present, and the log's 12 flow routes match `_selftest_stage_flow`. The selftest runs fakes for the stages and never runs the real `stage_*` bodies. That is why findings 1, 3, 5, 6 and 7 are not caught.
8. `onbox_command` is `bash remote_run_m4.sh bash onbox_m4.sh`. The launcher runs `bash remote_run_m4.sh bash $RUNNER`, and RUNNER is onbox_m4.sh. Match.

## BLOCKING

1. **Tools are called by bare name; the venv's bin directory is never on PATH.** run_m4.py:2059 (smoke check `colabfold_batch`, `lightdock3.py`), 2245 (empty-run control `colabfold_batch`), 2351-2354 and 2372-2382 (`lightdock3_setup.py`, `lightdock3.py`, `lgd_*`), 2663-2664 (`colabfold_batch`). onbox_m4.sh:93 sets `PY=${VENV}/bin/python3` and calls it directly, with no activation and no PATH export. Pip puts the console scripts in `venv_m4/bin`, which is not on PATH, and `child_env` copies the unchanged PATH. The smoke check raises FileNotFoundError and the install stage ends exit 2 after the whole install is paid for. EXEC_NOTE items 33 and 8, and rule 4. Would spend money without producing a valid record.

2. **The 1,800 s install ceiling is not a stage total.** run_m4.py:449-471 (`stage_ceiling_s` subtracts nothing for "install") and 2123, 2127, 2137-2141, 2159, 2173 (each call takes the full `stage_allowance_s`). Apt update, apt install, five pip groups, two downloads and the smoke check can each run to 1,800 s, so the install can run to about 6,600 s until the outer `timeout` fires. The ceiling never stops the stage. EXEC_NOTE item 28, GATE_COMMIT B8. Would spend money without producing a valid record.

3. **The AlphaFold parameter archive is downloaded but never extracted, and colabfold then fetches its own inside the timed call.** run_m4.py:220-225 and 2150-2164 download `alphafold_params_2022-12-06.tar` into the work directory (about 5 GB). Nothing unpacks it into `<data>/params`. 2663-2674 passes `--data wd`. With no params there, colabfold_batch downloads its own archive during the first prediction. That puts download and extraction time into the first C1 run's wall-clock and makes an unrecorded download (no URL or hash in any record). EXEC_NOTE items 13 (whole-call timing is the decision value), 14 and 34.

4. **The stand-in pairs are not checked against item 12 and the evidence is not recorded.** run_m4.py:1784 and 1828-1859 build each pair from one capsid slice plus one receptor chain. `want_cap = min(len(cap), target - len(rec))` (1839) clamps silently. If the 6IHB capsid chain is shorter than about 900 residues, the three pairs come out under 750 residues and identical. There is no assertion that each total is in 750 to 1,000 or that the three differ. Sequences, chain-id mapping and the hash of the pair files appear in no output: the FASTA files are written to `work_m4` (2639-2642), which the launcher does not fetch, and the rows carry only chain ids and lengths. EXEC_NOTE item 12.

5. **MD runs on the receptor alone, not on a docked complex.** run_m4.py:2719 and 2739-2741 pass `pose` straight to the worker. The pose file holds only the partner that moved (the docstring at 2410-2415 says so). The capsid is never merged back in for MD, although `stage_aux` does merge it for analysis (2585). The worker (1940-2028) then solvates about 100 residues. Even at 1.6 nm padding that cannot reach 120,000 to 180,000 atoms, so C2 is VOID on every run and the speed measured is not the card's quantity. EXEC_NOTE items 17 and 23, gate answer 10. Would spend money without producing a valid record.

6. **The engine's rate line is never parsed.** run_m4.py:2009-2011 write the StateDataReporter speed column to `out_json + ".log"` (in `work_m4`). 2744-2754 parse `log_path`, which is the tool's stdout log (`out/md_<name>.log`) and holds no speed line. `engine_ns_per_day` is always None, so `rates_disagree` (2764) never fires. The "engine rate and wall-clock disagree" label cannot appear. The unit-and-scale record (2307-2312) has no engine rate lines. The MD "log" measured for C4 (2811) is the stdout log. EXEC_NOTE items 17 and 20(c), gate answer 7(c).

7. **The empty-input control runs a tool, not the harness.** run_m4.py:2240-2251 time `colabfold_batch --help`. Gate answer 7(b) says "the harness with no tool call". A JAX and TensorFlow import almost certainly exceeds 2 s. The "setup overhead subtracted" label then goes on, and `adjusted_seconds` (2345-2348) takes the import time off every AlphaFold run (2680) and every docking pair (2592). The byte check reads an output directory that no command writes to (2250), so it is vacuous. EXEC_NOTE item 20.

8. **No pose and tool timeouts become an anchor miss, exit 4.** run_m4.py:2388-2394 (`dock` returns pose None on a timeout), 2463-2475 (no pose gives overlap None and `anchor_decision` False, reason "could not be compared") and 2535-2536 (FailStop code 4). Exit 4 sets run_valid false and is non-relaunchable under A2 ("a missed anchor is a result"). A docking timeout should be a ceiling stop (exit 3, items 29 and B3). A tool that ran but produced no parsable pose is a harness failure (exit 2, item 8). Both would be recorded as a scientific result.

9. **`m4_summary.json` does not state the stand-in scope first.** run_m4.py:274 writes every JSON with `sort_keys=True`, so `what_this_run_decides` (1563) lands last, after `unmeasured_inputs`. GATE_COMMIT answer 6(b) and EXEC_NOTE item 30 require it first. The selftest checks only that the key exists (3519).

10. **Per-record labels are missing.** run_m4.py:586-593, 596-611, 2100-2112 and 2030-2068 supply machine labels. Missing from every measured record: the CUDA runtime version (the smi query has no CUDA column, so `cuda_version` is always None, and the smoke check records none); start and end wall-clock (only `provenance` write time exists); the AlphaFold parameter archive hash (it is in `state["downloads"]` and the install record, not in `machine` or the C records); JAX build and compiler or wheel flags beyond a version string. EXEC_NOTE item 6, GATE_COMMIT labels.

11. **The C2 record omits the atom counts and engine precision.** run_m4.py:1523-1525 add only `timestep_fs` and `production_ns`. Atom counts, precision, platform and engine version exist only in the rows (2757-2775). EXEC_NOTE item 6 ("C2 the atom counts and engine precision").

## ADVISORY

12. **Package forms are unverified (reviewer recollection, not checked).** run_m4.py:206-218. `colabfold==1.5.5` without its `alphafold` extra may not provide the `alphafold` module the smoke check imports (2045). The plain `openmm==8.2.0` wheel may lack the CUDA platform, which may need `openmm[cuda12]` (2053). The smoke check will say; a failure is a clean void record under A2(a) but loses launch 1. EXEC_NOTE item 33.

13. **Docking CLI and output format are untested before the paid anchor.** run_m4.py:2372-2383 (flags `-rs -ls -sp --noxt --noh --now -s -g`, `swarm_0/gso_10.out`), 887-926 and 2398-2407. The smoke check only runs `--help`. `parse_docking_table` assumes a rank column and `.pdb` names in the table, as the planted selftest table has, and the real tool's table may not. If the named pose file is not found (2402-2404), the fallback takes `sorted(glob)[0]`, the lexicographically first pose, not the top-ranked one (item 17 "top docking pose"). With finding 8 this leads to a false anchor result.

14. **onbox steps before the first stage can fail with no void record.** onbox_m4.sh:89-94. A `python3 -m venv` failure (python3-venv is not in the declared apt packages) or `set -e` abort exits without `RUN_DONE` or a record. `pip install --upgrade pip` is an unrecorded download (item 34). EXEC_NOTE items 8 and 34.

15. **Failing control and anchor records carry `run_valid` true.** run_m4.py:2221-2236 and 2491-2536 write the records before `void_run`. The sleep record says FAIL and the anchor record says FAIL, both with `run_valid` true. EXEC_NOTE item 3.

16. **`estimated_s` is never passed to the guard.** run_m4.py:2095, 2206, 2432, 2553, 2631, 2714 and 2792 call `guard_before_stage` with no estimate, so only the AlphaFold loop projects the next run (2651). "A stage whose estimated remaining time exceeds the time left is not started" (item 27) is implemented but unused. A stage can start with seconds left and be killed at once.

17. **`stage_aux` with 2 of 3 pairs finished after a ceiling stop is recorded as done.** run_m4.py:2562-2568 and 2618-2622 record the stop but return normally, so `stages_done` (1686) lists the stage. EXEC_NOTE item 29 says the stage is then not in `stages_done`.

18. **Launcher has one fetch line not in frozen.** lambda_run_m4.sh:211 adds `scp ... results_m4/out/RUN_VALID.json`. It is additive and harmless, but it is not a path substitution, and the header does not declare it.

19. **The frozen bootstrap spends unrecorded time and downloads before T0.** remote_run_m4.sh:29-49 pip-installs pillow, jinja2, numpy, scikit-learn, transformers and accelerate with no `--report`. That time counts against the launcher's `timeout 7200` but not against onbox's T0 and STOP_AT (onbox_m4.sh:47), so the 400 s fetch margin is partly spent. At full ceilings the finish is about 6,800 s plus bootstrap, about 250 s inside 7,200 s. A slow bootstrap removes that margin. The file is frozen, so this is a note for the operator.

20. **Writes and sudo beyond the declaration.** pip caches (`~/.cache/pip`) and colabfold or JAX caches are outside `~/m4_run/`, and the frozen bootstrap installs into `~/.local`. `sudo -n ... apt-get update` (2120-2125) is a sudo call that is not a declared-package install. Rule 5 and EXEC_NOTE item 7.

21. **C1 `gate_pass` is reported on a VOID C1.** run_m4.py:1518-1520 and 1763-1764 compute `gate_pass` from `measured` even when C1 is VOID (not an A100, below minimum). It can read true or false on a number that has no decision. EXEC_NOTE item 11.

22. **Exit 3 is also returned for VOIDs that are not guard stops.** run_m4.py:1719-1736. An unmarginal VOID from not-an-A100, zero spread or a below-minimum count with no stop sends exit 3. Item 29 reserves 3 for guard, ceiling or timeout stops, and A2(b) reads exit 3 as "stopped on its time guard".

23. **Outer-timeout routing edge cases.** onbox_m4.sh:147 uses `timeout -k 30`, so a python that needs the KILL returns 137, not 124, and is handled as a failure, not a guard stop (item 32). `kill_recorded_groups` (107-120) signals every pgid ever recorded, including long-finished tools whose group ids may have been reused.

24. **Pip report hash is not cited in `inputs`.** run_m4.py:2140-2148 and 1535. The hash sits in `values.machine.pip_reports`, while each record's `inputs` lists only the rows file. Item 34 asks for the hash in `inputs`.

25. **C4 docking bytes under-count.** run_m4.py:2804-2808 measure `Path(pose).parent`, which can be the swarm directory and exclude `setup.json`, the rank table and the copied structures. Item 16 asks for "docking poses and tables of one pair".

26. **`frozen/ONBOX_CONTRACT.md` was not reviewed.** It is not on my read list. The operator's note asks for its stage order, guard arithmetic from measured rates, and atomic per-phase records. Stage order matches item 1, and records and state are written atomically (263-270, 647). Guard arithmetic uses the fixed ceilings, with measured rates only inside the AlphaFold loop (finding 16).
