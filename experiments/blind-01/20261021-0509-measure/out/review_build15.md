# Review of build 15 (execution layer, tag m4)

Verdict: FAIL. 4 blocking, 3 advisory.

Read: operator findings, EXEC_NOTE (all 78 items), GATE_COMMIT (pre-authorisation, addendum 12), run_m4.py (the pin block, the pin parser, the pin selftest, the hygiene selftest, the install calls), onbox_m4.sh (whole), both launchers and both frozen bootstraps (diffed), ONBOX_CONTRACT, selftest log, build 15 return, pip index check. Nothing was run.

Build 15 changed no file: run_m4.py is 7,416 lines and onbox_m4.sh 642, hashes equal the selftest line (82b8465e..., 8982a9e0...). Item 75 scope is therefore not met, because items 75(a), (b) and (c) require edits.

## Blocking

1. **BLOCKING. Replace the comment block at `run_m4.py:381-405` with the text item 76 prescribes.** The block still says the openmm pairing and the `with_cuda` extra are "INFERENCES MADE BY THE REVIEW BOARD, not verified facts" (lines 394-395). It names three sources, not four: `out/pip_release_files_lightdock.txt` is absent. It does not state that the index metadata says `openmm-cuda==8.1.1.12` requires `openmm==8.1.1`, or that the release has a CPython 3.10 manylinux x86_64 wheel (per the operator's listing). It never says the `with_cuda` extra alone is the gate's inference. Items: EXEC_NOTE 58, 75(a), 76; GATE M3. This is review 7's finding 3, still open.

2. **BLOCKING. Add the static check of items 67 and 77 to the selftest, e.g. next to `run_m4.py:7328-7336`.** A grep for `out/pip_`, `out/gate` and the piece-built prefixes finds no such check; only the `.keys`, `--upgrade pip` and environment-dump checks exist. Missing: the call-argument scan over both files, the three planted failures (`open(...)`, `Path(...).read_text()`, `cat ...`), the comment-only pass and the two-real-files pass. Items: EXEC_NOTE 67, 75(b), 77; GATE M2. This is review 7's finding 2, still open. The selftest count (749) has not moved, which agrees.

3. **BLOCKING. Rewrite the comment assertions in `selftest_pip_pins`, `run_m4.py:6571-6586`.** They still require the string "INFERENCES MADE BY THE REVIEW BOARD" (6574-6575), so once finding 1 is fixed the selftest fails. They check three file names (6576-6579), not four. They check a `SIBLING REQUIRES ENGINE VERSION:` marker, not the item 76 sentence. They have no planted cases: a comment with one name removed fails, a comment still saying "not verified facts" fails, the good comment passes. Items: EXEC_NOTE 64, 75(c), 76; GATE M3. The lone-sibling refusal (`run_m4.py:468-472`) and its cases are present and must be kept (item 75(d), M4); this was checked and is fine.

4. **BLOCKING. The build's return and the launch preconditions are not met.** `out/build15_return.json` says "STOPPED - NOT BUILT" and "NOT ISSUED" for `onbox_command`, so there is no onbox command to compare with what `onbox_m4.sh` runs (checklist 8; EXEC_NOTE 7, 36). Item 78(a) and item 62(iii) name `out/pip_pins_resolve_build14.txt` as the evidence file. It is 0 bytes, and `out/pip_pins_list_b14.txt` does not exist. The operator's passing resolve is in `out/pip_pins_resolve_build15.txt` and `.json`, which are not the files the directive names; by item 78(a) an outcome reported elsewhere is not a run of record. Launching without them goes against item 62 and GATE M9, so money would be spent without the authorised precondition. The operator's reading of the files (operator finding 5) applies: the nine pins in `run_m4.py:411-421` are identical to item 70, and the pip install call (`run_m4.py:2766-2767`) carries no forbidden option from item 71. Findings 1 to 3 are the only edits of the code the gate asked for; this finding is the evidence and return gap. The gate rules on whether the evidence under another file name is accepted.

## Advisory

5. **ADVISORY. `frozen/remote_run.sh` (as shipped via `remote_run_m4.sh:31,47`) runs unrecorded `pip install --upgrade pip` and `--upgrade pillow ... transformers accelerate` into `~/.local`.** These are downloads from the package index that are not recorded, and they use up install time outside the shell's 1,800 s install total. Items: EXEC_NOTE 7, 34, 45; GATE H7 rules it the operator's frozen bootstrap, so not blocking.

6. **ADVISORY. `jax-cuda12-plugin[with_cuda]` (pin 3) is flagged by the operator's index check as an extra not declared by the release (`with_cuda` against `with-cuda`).** The dry-run resolve passes. GATE M5 rules it as-is. Item 58.

7. **ADVISORY. The box venv sits over the image's torch 2.7 and the preinstalled `nvidia-*` packages, so the pip resolve in a clean venv does not model the box.** GATE M6 accepts this as a stated risk. A conflict ends the launch as exit 2 with a void record. Item 66.

## Checklist

1. Items carried: items 1 to 56 are carried by the build 11 and 14 code, per the selftest (749 of 749, cases for items 21 to 29, 31, 47 to 49, 55). Misses: items 58 and 64 (comment, finding 1 and 3), item 67 and 77 (finding 2), item 75 and 76 (findings 1 to 3).
2. Cost and time: `onbox_m4.sh:83-96` reads `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD`, `REMOTE_TIMEOUT` and clamps them to 5 and 7200. `STOP_AT` is the lesser of the dollar and time cap (119-121). Outer kill is `STOP_AT - elapsed - 600` (535) and a void record is written on every route. Ceilings sum to 7,200 and fit `REMOTE_TIMEOUT`. Fine.
3. Records: endpoint, anchor, RUN_VALID and summary conventions are implemented (selftest flows (a) to (l)), with the void path in `onbox_m4.sh:164-332`. Fine.
4. Secrets: no `.keys` read (selftest check at `run_m4.py:7332-7333`); no environment dump; `HF_TOKEN` unset at `onbox_m4.sh:523-524`. The launcher reads `.keys` and passes `HF_TOKEN`, which is the frozen design. Operator finding 6 is as in build 11.
5. Writes: everything is under `~/m4_run/` (cache variables `onbox_m4.sh:380-386`); sudo only for `apt-get` (428, 461); five declared apt packages (351). Fine.
6. Launcher: `lambda_run_m4.sh` differs from `frozen/lambda_run.sh` only at remote dir, payload, fetch paths, forwarded variables, the `REMOTE_TIMEOUT` default and the header comment. The terminate retry loop, on_signal, backstop, setsid, marker poll, CRLF guard and unhealthy-box aborts are untouched. `remote_run_m4.sh` differs from `frozen/remote_run.sh` only in the `cd` line (27). Fine.
7. Selftest log ends `selftest: PASS`, 749 of 749, and the printed hashes match the files. The count agrees with the files unchanged from build 14 (and so with missing items 76 and 77).
8. The return gives no `onbox_command` (finding 4). The launcher runs `bash remote_run_m4.sh bash onbox_m4.sh` (line 168), which is `onbox_m4.sh`.
