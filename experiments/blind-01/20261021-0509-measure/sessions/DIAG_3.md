# Anchor diagnostics on the saved result of launch 10 (local, CPU, no launch)

You diagnose why the anchor failed on launches 9 and 10. You run locally, with no GPU and no network. Do not run the
search or computation again. Your job is to find out whether the scoring and the correspondence are correct, using
the saved anchor result and the hash-verified copy of its reference that launch 10 fetched.

## Read (absolute paths under the measure folder M = the current working directory)
- `M/EXEC_NOTE.md`: the anchor item. It defines the anchor's metrics, the published value, the tolerance, and how the
  result and the reference are compared.
- `M/run_m4.py` (build 26, the code that ran on launch 10): the anchor stage and its scoring and correspondence code.
  You may read it and import from it. Do not edit it.
- `M/out/launch10/results_m4/out/`: the anchor record (its recorded values, inputs and hashes), the saved anchor
  result, and the reference copy.
- `M/out/launch9/results_m4/out/`: the same for launch 9, for comparison only.

## Run
Use `M/.venv/bin/python` for everything. It is the environment of record, installed locally from its lock file, and
runs on CPU. One distribution of the lock needs a CUDA compiler and is not installed locally. If importing the runner
needs a module from it, put a stub for that module into `sys.modules` before the import, and never call the stub.
Write only under `M/out/diag_anchor/`: one script `diag_anchor.py`, its output `diag.json`, and
`REPORT.md`. Write nothing anywhere else, install nothing, and use no network. Stay under 40 minutes.

How to work (a previous attempt timed out after 45 minutes having written nothing):
- Within your first 10 minutes, find the anchor stage's scoring and pairing functions in run_m4.py with grep, and
  read only those functions and what they call. Do not read the whole file.
- Write `diag_anchor.py` as one file. Run it with `PYTHONDONTWRITEBYTECODE=1`.
- Run the checks in the order d0, d5, d1, d2, d4, d3. After each one, rewrite `diag.json` with every result so far,
  so a timeout keeps your partial results.
- Write REPORT.md when the checks are done. If you are short of time, write it from the checks you have finished,
  mark the rest NA, and reply.

## Checks (each one is PASS, FAIL or NA, with the numbers behind it in diag.json and REPORT.md)
- **d0 provenance:** the reference copy's sha256 matches the hash in the anchor record's inputs, and the saved result
  is the file the anchor record names.
- **d5 rescore:** score the saved result against the reference copy with the runner's own functions, now and locally.
  The values must reproduce the launch 10 anchor record. A difference means the record does not come from these files.
- **d1 round trip:** score the reference against itself with the runner's own functions. Every anchor metric must be
  perfect (zero distance, full overlap).
- **d2 known transformation:** apply a random rigid rotation and translation to the reference, then score it against
  the untransformed reference with the runner's own functions. Every metric must stay perfect. Also apply one
  perturbation whose expected score you compute by hand, and check the runner returns that value.
- **d3 independent scoring:** implement every anchor metric from its definition in EXEC_NOTE, without copying or
  calling the runner's scoring code, and score the saved result against the reference. Compare with the runner's
  values: AGREE within 1 % (or within an absolute 0.01 for values near zero), else DISAGREE.
- **d4 correspondence:** count how many elements of the saved result the runner pairs with an element of the
  reference, against how many the definition says should be paired. Check whether the identifiers both files use
  line up. Report FULL (all expected pairs made, identifiers consistent), PARTIAL, or NONE.

Then localise the failure to exactly one locus:
- `scorer`: d1, d2 or d3 show the runner's scoring is wrong;
- `correspondence`: d4 is PARTIAL or NONE while the scoring is otherwise right;
- `reference`: d0 fails, or the reference copy is not what the anchor item specifies;
- `computation`: scoring and correspondence are correct and the saved result itself is far from the reference;
- `unknown`: the evidence does not separate these.

Give a confidence of high, medium or low. In REPORT.md, give the numbers, the code locations (function names and
line numbers in run_m4.py) and the reasoning, so that a gate can rule on them. If the locus is `scorer` or
`correspondence`, state the smallest code change that would fix it. Do not make that change yourself.

## Reply
Your final message is exactly one line in this form, nothing else:

`DIAG d0=<PASS|FAIL|NA> d5=<PASS|FAIL|NA> d1=<PASS|FAIL|NA> d2=<PASS|FAIL|NA> d3=<AGREE|DISAGREE|NA> d4=<FULL|PARTIAL|NONE|NA> locus=<scorer|correspondence|reference|computation|unknown> confidence=<high|medium|low>`
