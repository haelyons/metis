[x-m5u58fix-impl]
Working directory dut/pipeline/. Do not read anything under experiments/. Do not edit tests (tools/test_*, tools/e2e_*, tools/m5_profile_fixture.js, tools/m5_smoke_pin.js, tools/run_failures_only.js). The contract is fixed: implement it exactly, and do not edit m5/SCHEMAS.md or CONTRACT.md. Make the smallest change that meets the contract; match the surrounding style and comment density.

Unit U58, fix round. Your m5/score_comparison.py (uncommitted in this worktree) is kept. The separate test author's suite, tools/test_m5_comparison_score.py, passes 651 of 654 checks. The three failures all show the scorer accepting an invalid `C/arms_seal.json` (exit 0, output written) where the contract requires exit 1 with no output file:
- invalid-arms-seal-omits-file: arms_seal.json without versions.sh
- invalid-arms-seal-omits-adapter: arms_seal.json without arms/A1.sh
- invalid-arms-seal-extra-key: arms_seal.json with an extra top-level key

Contract (m5/SCHEMAS.md, section "Sealed comparison (U57, U58)"): the pipeline writes `C/arms_seal.json`, exactly `{files, sealed_utc}`, mapping each of the sealed harness files' names (one adapter per arm as `arms/<id>.sh`, `cmp_files.json`, `cmp_extract.json`, `versions.sh` and, exactly when the design has an evaluator, `fetch_private.sh` and `evaluate.sh`) to the SHA-256 of its bytes. The scorer checks the SHA-256 of each sealed harness file against it and exits 1, with no output file, for invalid or missing input or a seal mismatch. A seal that omits a file the design requires, names a file it does not require, or has keys other than exactly `files` and `sealed_utc` is invalid input: otherwise an unsealed harness file could change without the scorer noticing. Read the contract section again for the exact file set and apply it.

Checks: `python3 -I tools/test_m5_comparison_score.py` (all checks must pass), `python3 tools/test_m5_signatures.py`, `python3 tools/test_m5_card_score.py`. Do not write or change tests. Report the change and the results. End with a final message even if checks fail.
