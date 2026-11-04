You are an independent reviewer (a different model family from the author) of one small fix round in this worktree, branch `units`. Read-only: change nothing. Never read anything under experiments/.

Scope is narrow. Do not do another open-ended review of the sealed-comparison path. Answer only:
(a) Your previous narrow check (quoted below between `--- earlier report ---` and `--- end ---`) found two defects in its section (b): the allow-list precedence (with scheduled-job removal after the kill) and the mode-600 exemption pattern. Its item 2 in section (a) was "partly fixed" for the same reason. The operator clarified the contract in commit 2151b52b (`git show 2151b52b`), and the fix round is HEAD (8cc4a17b). For each of the two defects, does HEAD fix it? Say fixed / partly fixed / not fixed, with file and line and one sentence of evidence, and say whether a wrong implementation of that kind would now fail a test.
(b) Any regression or new contract violation introduced by `git diff 39355ae5..HEAD`. Judge against the contract at HEAD (m5/SCHEMAS.md, section "Sealed comparison (U57, U58)"). Report only defects in changed code or defects the change causes elsewhere, most severe first, each with file, line, the contract sentence and a concrete failure case. Skip style and pre-existing issues outside the diff.

Claude wrote the code and the tests, in separate sessions, the test author without access to the code.

End with one line: `VERDICT: clean` if both items in (a) are fixed and (b) found nothing, otherwise `VERDICT: defects`.

--- earlier report ---
(a)

1. **Fixed** — [pipeline.js:292](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/pipeline.js:292): hidden paths include resolved design directory, its git ancestry, and resolved run/journal locations.
2. **Partly fixed** — [cmp_users.sh:67](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_users.sh:67), [cmp_wrap.py:176](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_wrap.py:176): deny entries and scheduled-job removal added, but existing allow-lists can override scheduling prohibition.
3. **Fixed** — [comparison.js:92](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/comparison.js:92), [score_comparison.py:316](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/score_comparison.py:316): both validators reject non-null timeout exit statuses and empty command vectors.
4. **Fixed** — [score_comparison.py:66](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/score_comparison.py:66), [score_comparison.py:727](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/score_comparison.py:727): sealed input parsing rejects `NaN`, `Infinity`, and `-Infinity`.
5. **Fixed** — [cmp_users.sh:84](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_users.sh:84): permission traversal preserves mode-600 evaluate command files, including currently executing users script/log/GPU files.
6. **Fixed** — [pipeline.js:1430](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/pipeline.js:1430): timeout finalization skips comparison evaluate facts.
7. **Fixed** — [comparison.js:60](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/comparison.js:60): versions require every expected key and exactly two string fields per row; `{}` and `{"A0":17}` become null.
8. **Weak test: fixed** — [test_m5_comparison_evaluate.js:1483](/home/hal/dev/interp/metis-wt/dut/pipeline/tools/test_m5_comparison_evaluate.js:1483): new snapshots check all evaluate receipts during part execution; exposing upload or users command files now fails.
9. **Untested rule: fixed** — [test_m5_comparison_evaluate.js:2254](/home/hal/dev/interp/metis-wt/dut/pipeline/tools/test_m5_comparison_evaluate.js:2254), [test_m5_comparison_evaluate.js:2150](/home/hal/dev/interp/metis-wt/dut/pipeline/tools/test_m5_comparison_evaluate.js:2150): fixtures create message queues and semaphore arrays and require removal before next part; shared-memory-only cleanup now fails.

(b)

- **P1 — Scheduling prohibition ignores existing allow-lists.** [cmp_users.sh:67](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_users.sh:67). HEAD contract: “adds each part user to `/etc/cron.deny` and `/etc/at.deny` … so that no part user can schedule a job.” Existing `/etc/cron.allow` containing `cmp-arm` overrides `cron.deny`; `at.allow` has equivalent precedence. On such a reused box, an arm can schedule a job due during directory cleanup, after the process-kill check but before scheduled-job removal. That newly launched process escapes cleanup and can interfere with subsequent invocations. Deny-list presence alone cannot enforce this contract.

- **P2 — Permission exemption also hides ordinary input files.** [cmp_users.sh:84](/home/hal/dev/interp/metis-wt/dut/pipeline/m5/cmp_users.sh:84). HEAD contract: shared-tree setup “grants other users read access to every file,” subject to command-file privacy. Exemption matches every top-level mode-600 file named `[0-9]*-*`, without identifying actual command files. Concrete case: setup creates box-owned `$S/2026-input.bin` at mode `600`; previous traversal made it readable, while HEAD skips it, causing arm reads through `run/2026-input.bin` to fail with `EACCES`.

Verification: source inspection, in-memory validator/parser probes, Python syntax checks, and `git diff --check`. File-creating suites not run. No files changed; nothing under `experiments/` read.

VERDICT: defects--- end ---
