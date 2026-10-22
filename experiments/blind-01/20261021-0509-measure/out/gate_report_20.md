# Report for addendum 20: owner direction after the anchor halt (2026-10-22), anchor diagnostics, build 27

The owner ruled on the HALT of addendum 19. Ruling of record:

1. **Calibration branch (a deviation of record, made after the anchor failed on launches 9 and 10).** The anchor's
   FAIL stays FAIL. Later records are still measured. Each carries `run_valid=false` (scientifically unvalidated,
   voided by the anchor) and `calibration_valid`, decided only by its own checks: guards, completion, and the workload
   checks the directive must now name for each input (input sizes, step counts, well-formed outputs, whatever shows
   the run did the intended work). Standing rule 3 and contract section 3.6 now say this.
2. **Stage interface instead of selftests.** Contract section 7 (`frozen/ONBOX_CONTRACT.md`, v2; v1 is kept in
   `out/ONBOX_CONTRACT_v1.md`) replaces the implementer selftest with a stage interface. Each stage runs alone. Each
   external program can be replaced through an environment variable. Each parser is callable by name. Importing the
   runner does no work. A separate author writes tests against that interface, using fixtures recorded on the box.
   The tests run locally, in a copy of the environment of record (`.venv`, installed from the lock file; one
   distribution needs a CUDA compiler and is not installed locally), before every launch, and must pass. The box no
   longer runs the author's tests.
3. **Anchor diagnostics before another launch.** A diagnostician has already run locally on the saved anchor result
   of launch 10 and its hash-verified reference copy, with no GPU and no new search. Its full report and numbers are
   in `out/diag_anchor/REPORT.md` and `out/diag_anchor/diag.json`, and its script is
   `out/diag_anchor/diag_anchor.py`. From now on, the anchor stage writes these diagnostics into the anchor record
   itself (contract 3.6).
4. **Evidence.** Rule on measured outcomes only from raw files you have read yourself, and cite their paths.
5. **Compute is always logged.** Whatever the anchor or any stage decides, a launch yields compute information (GPU
   time, wall-clock per stage, instance), and it is recorded. Contract section 3.8 now requires a `compute` table in
   the summary, written by an exit trap on every exit. The operator's score step carries it into the ledger with the
   launch records (type, hours, USD, exit code).
6. **Backtests deferred.** Checking the tests against historical defects is postponed until after launch 11.

The diagnostician's one-line reply was `d0=PASS d5=PASS d1=PASS d2=FAIL d3=AGREE d4=FULL locus=computation
confidence=high`. Before you accept the locus, reconcile it with the failed d2, the known-transformation check. Either d2
exposes a scorer defect, in which case the locus is `scorer`, or d2 does not apply to the metric as the directive
defines it (for example, a metric defined in a fixed frame), in which case the check was misapplied. Decide which from
the script and the code, not from the report's conclusion.

## Evidence to read yourself (raw)
- `out/diag_anchor/REPORT.md`, `out/diag_anchor/diag.json`, `out/diag_anchor/diag_anchor.py`
- `out/launch10/results_m4/out/`: the anchor record and every file it names; `out/launch9/results_m4/out/`: the same
- `run_m4.py` (build 26): the anchor stage and its scoring and correspondence code, at the locations the
  diagnostics report names
- `frozen/ONBOX_CONTRACT.md` (v2), sections 3.6, 5, 7 and 8

## Rule on
- **The diagnostics:** do they hold up against the raw files and the code? What is the locus (scorer,
  correspondence, reference, computation, unknown), and what must build 27 change, if anything, in the anchor stage?
  If the scoring or the correspondence is wrong, the fix is a code fix justified by these diagnostics, which do not
  depend on the expected value. Record it as such.
- **The regenerated EXEC_NOTE (at most 40 items, required-for-launch items first).** It must carry:
  - the stage interface: the stage names, the environment variable for each external program, and the parser
    function names;
  - the calibration branch, with the workload checks for each input;
  - the compute table in the summary, written on every exit;
  - the anchor diagnostics in the anchor record;
  - the on-box script no longer running the author's tests;
  - every item superseded by the above removed.
- **Build 27:** authorise it as an in-place edit of `run_m4.py` and `onbox_m4.sh`: the interface, the calibration
  branch, the anchor diagnostics, and the anchor fix if you rule one. Or HALT, and say why.
- **Launch 11:** what must hold before it (the local tests pass on the built files; review PASS), its cap within
  USD 20 of record (USD 6.68 spent), and its timeout.
