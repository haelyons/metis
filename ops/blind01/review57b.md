You are an independent reviewer (a different model family from the author) of the fix round for units U58, U57a and U57b in this worktree, branch `units`. Read-only: change nothing. Never read anything under experiments/.

An earlier Codex review of commits 26a62afd (U58), 823ce678 (U57a) and cdac16d5 (U57b) found defects; its report is quoted below, between the lines `--- earlier report ---` and `--- end ---`. The operator then tightened the contract in commit 77ebbcc5 (`dut/pipeline/m5/SCHEMAS.md`, section "Sealed comparison (U57, U58)"; `git show 77ebbcc5` shows the change), and the fix round is the commit at HEAD (`git show HEAD`). Read the section whole as it stands at HEAD. Claude wrote the code and the tests, in separate sessions, the test author without access to the code.

First, for each finding of the earlier report, say whether HEAD fixes it, with file and line. Then review the code at HEAD against the contract at HEAD, the whole sealed-comparison path and not only the diff. Review the code against the contract only. Report, most severe first, each place where the code does not do what the contract says or does something it forbids. Give most weight to:
- isolation: any way an arm or the evaluator can read what the contract hides from it (the sealed design's margins, thresholds, confidences, reference values, the evaluator's private reference data or its residue, stray copies of reference files or their hashes, other arms' or the evaluator's files, the run's log/ and job files, identifying command logs in evaluator inputs, the repository, the run root, the design's step folder), or reach the network where the contract forbids it; and any check a hostile arm could defeat (symbolic links, hard links, races, leftover processes, permissions, environment);
- seals: a seal that does not cover what it must, or a sealed file that can change unnoticed between sealing and scoring;
- scoring: a wrong or missing rule in values, missing values, eligibility, intervals, criteria or outcomes, or an output field that differs from the contract;
- behaviour without `args.comparison`: any change to a run that is not a comparison.
Also report a test that would pass on a wrong implementation of a contract rule, and a contract rule no test checks. For each, give the file and line, the contract sentence, and a concrete case that shows the defect. Do not report style. If you find nothing, say so.

Write the report to the file named by the `-o` option. End with one line exactly `VERDICT: clean`, `VERDICT: minor` (only defects that change no result) or `VERDICT: defects`.

--- earlier report ---
Report could not be saved: no `-o` path supplied; sandbox permits reads only. No files changed. Nothing under `experiments/` read.

Reviewed branch `units`, HEAD `cdac16d5`, against fixed contract at `db332caf`.

1. **P1 — Arm can hide forbidden output symlinks from validation.** [cmp_wrap.py:255](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_wrap.py:255)

   Contract: “makes the invocation `invalid` when `out/` holds anything other than regular files and directories (a symbolic link included).”

   Arm creates `out/predictions` as a symlink to a known private reference filename, then sets `out/` mode `000`. Recursive sudo chown transfers ownership to the box user without restoring owner permissions. The box user’s `os.walk` silently skips the inaccessible directory. Subsequent `chmod -R go-w,o+rX` grants other users access while leaving owner permissions absent; its failure is ignored. The evaluator can then follow the unchecked symlink and evaluate reference data as predictions. Invocation can remain `ok`.

2. **P1 — Agent copy-back follows symlinked parent directories into hidden files.** [pipeline.js:294](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/pipeline.js:294)

   Contract: “copies each regular file directly under the view’s `intake/` (no symbolic link, no subdirectory).” Also: “Agents see only the view.”

   `copyRegular` checks only the final pathname component. An intake agent can replace its `intake/` directory with a symlink to a hidden directory. Trusted pipeline code follows that directory after isolation ends and copies its regular files. Concrete case: the hidden design directory also contains valid intake artifacts; its design JSON is copied into `A/intake/`, then exposed in the harness view. Equivalent ancestor substitution affects harness and repair copy-back.

3. **P1 — Dispatching with `hidden` does not keep hidden pipeline descendants hidden.** [pipeline.js:279](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/pipeline.js:279), dependency [isolated_runner.js:36](/home/hal/dev/interp/metis-wt/dut/pipeline/idea/isolated_runner.js:36)

   Contract requires hiding “the run root,” the design’s parent directory, and its git work tree.

   The isolation runner mounts hidden paths, then rebinds the entire pipeline directory over those mounts when pipeline code lies under a hidden ancestor. Place a valid design at `dut/pipeline/designs/design.json`: hiding its parent and repository is undone by that later bind. Agents can read the sealed criteria directly. A run root beneath the pipeline directory is likewise re-exposed. The comparison dispatcher neither rejects these layouts nor restores their hiding.

4. **P1 — Remote command scripts expose job identities and sealed timeouts.** [comparison.js:93](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/comparison.js:93), dependency [boxrun.sh:79](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/boxrun.sh:79)

   Contract: “no box path, file name, process argument or environment variable that the evaluator part can read names the arm.” Timeouts must also be unreadable by arms and evaluator.

   Boxrun writes each command into a top-level `<receipt>.sh` without enforcing a remote private umask. With ordinary remote umask `022`, `*-comparison-job.sh` is readable by both separated users. It contains base64 encodings of the complete job and plan: arm identity, commands, environment and resolved timeouts. An evaluator can enumerate these scripts and decode the job matching its invocation token. Protecting `comparison-jobs/` does not protect these copies.

5. **P1 — Comparisons without an evaluator give arms authority over trusted evidence.** [cmp_wrap.py:182](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_wrap.py:182), [cmp_wrap.py:283](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_wrap.py:283)

   Contract requires sealed timeouts to be unreadable by arm processes and closes each invocation “so that no later part reads this invocation’s files.”

   Without an evaluator, arms run as the box user. That same UID owns jobs, logs, wrapper code and completed invocations. An arm can read its timeout from `comparison-jobs/i1.json`, read earlier arms’ logs, rewrite earlier measurements or replace the trusted wrapper. Mode `700` does not separate processes sharing that UID. Successful arm exits also receive no descendant cleanup in this branch, allowing background mutation during later invocations.

   The contract’s prescribed box-user execution does not itself satisfy its confidentiality requirements; this implementation supplies no additional boundary.

6. **P1 — Local seals do not authenticate the harness actually executed remotely.** [pipeline.js:783](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/pipeline.js:783), [comparison.js:106](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/comparison.js:106), [score_comparison.py:202](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/score_comparison.py:202)

   Contract: “They upload with the harness, in the same encoding. No repair changes them.”

   Seals cover local harness files only. Setup and anchors scripts execute remotely before separated-user permissions are applied; their repairs can rewrite a remote adapter or `evaluate.sh`. No remote hash check detects this. Concrete case: repaired `setup.sh` replaces remote `harness/evaluate.sh` with a script emitting a constant score. Local sealed bytes remain unchanged, so scoring accepts measurements produced by the replacement.

7. **P2 — Evaluator execution can exceed the remaining comparison budget.** [comparison.js:86](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/comparison.js:86), [cmp_wrap.py:272](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_wrap.py:272)

   Contract: evaluator timeout is bounded by “the time left in `budget_s`, and the time left before the run ceiling.”

   Both part caps use the same pre-invocation budget snapshot. Evaluator execution then starts a fresh timeout without subtracting arm execution, cleanup or intervening overhead. With 10 seconds remaining, an 8-second arm followed by an 8-second evaluator can consume approximately 16 seconds. The wrapper’s budget deadline limits process cleanup, not evaluator execution.

8. **P2 — Semantically invalid `wrap.json` can establish supported outcomes.** [score_comparison.py:235](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/score_comparison.py:235), [comparison.js:75](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/comparison.js:75)

   Contract: “A missing or invalid `wrap.json` gives status `invalid`”; its measurements must therefore be missing.

   Validators check only part of the schema. A record with all top-level keys, `status:"ok"`, `adapter_rc:9`, `commands:[]`, and `adapter_wall_s:-2` is accepted. An in-memory probe confirmed the scorer returns trusted wall `-2`. A lower-is-better comparison against reference zero can therefore become supported instead of void. Command row schemas and successful exit consistency are also unchecked.

9. **P2 — Standalone scorer accepts invalid sealed designs.** [score_comparison.py:65](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/score_comparison.py:65)

   Contract: “exit 1 for invalid or missing input … with no output file.”

   `check_design` omits required validation of commands, arm descriptions/environment, warmup, order seed, timeouts and budget, among other fields. An in-memory probe accepted empty commands, `warmup:99`, a string order seed and negative timeout/budget together. With matching seals and no comparisons, the scorer can write a successful result for that invalid design. Intake validation does not satisfy the scorer’s independent CLI contract.

10. **P3 — Comparison evaluate facts contain non-null telemetry.** [pipeline.js:1408](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/pipeline.js:1408)

    Contract: “Evaluate facts keep every existing key, null in comparison mode.”

    The shared stage finalizer overwrites `gpu_busy_known` with a boolean whenever evaluate has receipts. Any executed comparison therefore violates the required null facts. This changes metadata, not scientific outcomes.

11. **Weak test — Explicitly accepts the wrong null-facts behavior.** [test_m5_comparison_evaluate.js:976](/home/hal/dev/interp/metis-wt/dut/pipeline/tools/test_m5_comparison_evaluate.js:976)

    Contract: “Evaluate facts keep every existing key, null in comparison mode.”

    The assertion permits boolean `tokens_known` and `gpu_busy_known`. An implementation returning `gpu_busy_known:true` passes this test despite violating that sentence.

12. **Untested rule — System V IPC cleanup.** [test_m5_comparison_evaluate.js:482](/home/hal/dev/interp/metis-wt/dut/pipeline/tools/test_m5_comparison_evaluate.js:482)

    Contract: cleanup must “remove every System V IPC object the user owns.”

    The suite supplies an `ipcrm` fake but creates no part-owned IPC objects and asserts no removal. Deleting IPC cleanup entirely would pass these tests. Concrete missing case: evaluator leaves a world-readable shared-memory segment containing private labels; cleanup must remove it before the next arm starts.

No additional regression identified for runs without `args.comparison`. Verification used source inspection and in-memory probes; file-creating test suites were not run.

VERDICT: defects
--- end ---
