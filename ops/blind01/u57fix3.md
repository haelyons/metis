[x-m5u57fix3-impl]
Working directory dut/pipeline/. Do not read anything under experiments/. Do not edit tests (tools/test_*, tools/e2e_*, tools/m5_profile_fixture.js, tools/m5_smoke_pin.js, tools/run_failures_only.js). The contract is fixed: implement it exactly, and do not edit m5/SCHEMAS.md or CONTRACT.md. Make the smallest change that meets the contract; match the surrounding style and comment density.

Units U57a, U57b and U58, second fix round. The first fix round is committed (fbeeb94d). A second independent Codex review of it, and a live probe on a box (a hostile arm and evaluator), found the defects below. Then the operator added one rule to the contract in commit f0edeb93 (`git show f0edeb93`): Separated users step 1 adds each part user to `/etc/cron.deny` and `/etc/at.deny` (creating either when absent), and cleanup removes the user's crontab and at jobs (`crontab -r -u <user>`; `atrm` for each job `atq` lists for the user; each only when the tool is installed). Implement that rule, and fix each finding below against the contract (m5/SCHEMAS.md, section "Sealed comparison (U57, U58)", read whole):

Live probe (confirms review finding 5): in every arm part and every evaluator part, the files of the `comparison-users` box command (its `.sh`, `.log` and `.gpu` in the shared run directory) were readable by the part user; the job commands' files were private. The `chmod -R go-w,o+rX` of the shared run directory in `cmp_users.sh` must leave every file of the evaluate stage's own box commands (uploads included, and the running `comparison-users` command's own files) at mode 600.

Review findings (quoted from the reviewer):
Remaining defects, most severe first:

1. **P1 — Symlinked design paths leave actual design and repository readable.** [pipeline.js:290](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/pipeline.js:290), dependency [isolated_runner.js:32](/home/hal/dev/interp/metis-wt/dut/pipeline/idea/isolated_runner.js:32)

   Contract: “Criteria, margins, thresholds, reference values and timeouts are fixed by a science step before the run, sealed, and unreadable by the run's agents and by the processes of arms and evaluator.” Isolation must hide the design’s parent and git work tree.

   Real paths are checked for placement, but `hiddenPaths` and git ancestry use the unresolved source pathname. For example, `/launch/design.json` can symlink to `/science/repo/step/design.json`, with both outside pipeline working directory. Intake accepts it, then hides `/launch`; it does not hide `/science/repo/step` or discover `/science/repo/.git`. An agent follows the original symlink target and reads sealed design and repository through the read-only host mount.

   Resolve actual design, run and journal locations when constructing hidden paths; discover git ancestry from resolved design location.

2. **P1 — Arm can schedule processes that survive cleanup and attack later invocations.** [cmp_wrap.py:138](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_wrap.py:138), [cmp_wrap.py:148](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_wrap.py:148)

   Contract: cleanup must kill every process of the part user, and the arm cannot read protected residue or interfere with protected execution “whatever its adapter or commands do.” Declared scheduled-job residual risk covers setup, repairs and anchors—not arms.

   On a box permitting ordinary users to install crontabs, an arm can invoke the setgid `crontab` utility. Its spool directory is not writable by `cmp-arm`, so writable-directory cleanup does not visit it. `pkill` removes current processes but leaves the crontab. During a later invocation lasting past the next minute, cron launches another `cmp-arm` process. That process shares the later arm’s UID and can read or overwrite its current `run/` and `out/`, changing scored results.

   Neither user setup nor execution disables this scheduling route. Deny persistent scheduling to part users or provide an execution boundary whose destruction also prevents later launches.

3. **P2 — Invalid timeout records still supply scored values.** [score_comparison.py:304](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/score_comparison.py:304), [comparison.js:93](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/comparison.js:93)

   Contract: “Walls are `perf_counter` seconds and exit statuses null on timeout.” Also: “A missing or invalid `wrap.json` gives status `invalid`.”

   Both validators accept an otherwise successful arm record with `eval_status:"timeout"` and `eval_rc:9`. They check integer type but never require null exit status on timeout. The record remains `ok`, allowing extraction from `out/`.

   In-memory probe: this record plus `out/value.json` containing `{"v":7}`, compared against reference zero using higher-better non-inferiority, produces `supported`. Required result: invalid invocation, missing value, therefore `void`.

   Enforce timeout/null consistency in both validators. Command rows also accept empty `argv` arrays despite representing non-empty substituted command vectors.

4. **P2 — Standalone scorer accepts sealed designs containing non-JSON constants.** [score_comparison.py:111](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/score_comparison.py:111), [score_comparison.py:710](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/score_comparison.py:710)

   Contract: “Exit 0 after writing; exit 1 for invalid or missing input (a design that intake would reject included), a seal mismatch or a failed write, with no output file.”

   Python’s `json.loads` accepts `NaN`, `Infinity` and `-Infinity`; intake’s `JSON.parse` rejects them. `check_design` checks input keys but never validates `spec` recursively. Evaluator `spec` has the same omission.

   Concrete case: otherwise valid sealed design, `inputs[0].spec` set to raw `NaN`, no comparisons. `check_design` accepts it—confirmed in memory—and scorer can write successful empty results. Intake rejects those same bytes.

   Reject nonstandard JSON constants when parsing sealed input.

5. **P2 — User setup makes private evaluate command files readable again.** [cmp_users.sh:69](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_users.sh:69)

   Contract: “Remote command files: every box command of the evaluate stage in comparison mode creates its own files on the box … at mode `600` before writing to them, so no part user reads a job's contents.”

   `chmod -R go-w,o+rX "$S"` applies to earlier evaluate upload files and the currently executing `comparison-users` script, log and GPU sample file. Files created at `600` become `604`; current log and sample writes continue after that change. Both part users can subsequently read them. The users command script exposes its resolved timeout.

   Preserve command-file privacy while applying shared-tree permissions. The test currently exempts precisely these files; weak-test finding below.

6. **P3 — Timeout receipts still produce non-null comparison evaluate facts.** [pipeline.js:1425](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/pipeline.js:1425)

   Contract: “Evaluate facts keep every existing key, null in comparison mode.”

   GPU telemetry overwrite is guarded, but timeout finalization remains unconditional. A timed-out evaluate box command adds `timed_out:true`, numeric `budget_s` and boolean `overrun` to comparison facts.

   Concrete case: `comparison-users` times out. Evaluate fails, and finalizer emits these non-null facts. Guard this mutation in comparison evaluate as well.

7. **P3 — Invalid versions objects are copied into compute instead of becoming null.** [comparison.js:52](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/comparison.js:52)

   Contract: “`system` and `versions` copy the fetched `system.json` and `versions.json` (null when missing or invalid).” Versions must map each arm, and evaluator when present, to exactly `{version, executable}`.

   `fetched` validates only that JSON is an object. If `versions.sh` prints `{}` or `{"A0":17}`, compute records that invalid object as `versions`. Required value: null.

   Validate fetched versions against required keys and row schema before copying.

**Weak test:** [test_m5_comparison_evaluate.js:1199](/home/hal/dev/interp/metis-wt/dut/pipeline/tools/test_m5_comparison_evaluate.js:1199), [test_m5_comparison_evaluate.js:1220](/home/hal/dev/interp/metis-wt/dut/pipeline/tools/test_m5_comparison_evaluate.js:1220)

Contract sentence: “Remote command files: every box command of the evaluate stage in comparison mode creates its own files on the box … at mode `600` before writing to them, so no part user reads a job's contents.”

Test deliberately selects only receipts *after* `comparison-users`. An implementation exposing evaluate upload and users scripts/logs passes. HEAD supplies that concrete wrong implementation. Check those files during part execution too.

**Untested rule:** [test_m5_comparison_evaluate.js:971](/home/hal/dev/interp/metis-wt/dut/pipeline/tools/test_m5_comparison_evaluate.js:971), [test_m5_comparison_evaluate.js:989](/home/hal/dev/interp/metis-wt/dut/pipeline/tools/test_m5_comparison_evaluate.js:989), [test_m5_comparison_evaluate.js:1960](/home/hal/dev/interp/metis-wt/dut/pipeline/tools/test_m5_comparison_evaluate.js:1960)

Contract sentence: cleanup must “remove every System V IPC object the user owns.”

Fixtures create only shared-memory segments with `ipcmk -M`. They create no message queues or semaphore arrays. An implementation deleting only shared-memory segments passes these checks. Concrete missing cases: evaluator leaves a world-readable message queue containing labels, or arm leaves a semaphore array; both must disappear before next part.

Then run `node tools/test_m5_comparison_evaluate.js`, `node tools/test_m5_comparison_pipeline.js`, `python3 tools/test_m5_comparison_score.py`, `node tools/test_m5_isolation.js`, `node tools/test_m5_evaluate.js`, `bash tools/test_boxrun.sh` and report each summary line. A test written for the earlier rules may fail on a correct fix; report it by name rather than working around it. End with a final message even if checks fail.
