You are an independent reviewer (a different model family from the author) of units U58, U57a and U57b in this worktree, branch `units`. Read-only: change nothing. Never read anything under experiments/.

The contract is fixed and was written before the code: `dut/pipeline/m5/SCHEMAS.md`, section "Sealed comparison (U57, U58)", read whole; it is in commit db332caf. The implementation and its tests are the last three commits (`git show --stat HEAD~2 HEAD~1 HEAD`, then `git show` each): 26a62afd U58 (scorer, m5/score_comparison.py), 823ce678 U57a (design, seals, agent isolation, harness files), cdac16d5 U57b (on the box: separated users, wrapper, compute). Claude wrote both the code and the tests, in separate sessions, the test author without access to the code.

Review the code against the contract only. Report, most severe first, each place where the code does not do what the contract says or does something it forbids. Give most weight to:
- isolation: any way an arm or the evaluator can read what the contract hides from it (the sealed design's margins, thresholds, confidences, reference values, the evaluator's private reference data or its residue, stray copies of reference files or their hashes, other arms' or the evaluator's files, the run's log/ and job files, identifying command logs in evaluator inputs, the repository, the run root, the design's step folder), or reach the network where the contract forbids it; and any check a hostile arm could defeat (symbolic links, hard links, races, leftover processes, permissions, environment);
- seals: a seal that does not cover what it must, or a sealed file that can change unnoticed between sealing and scoring;
- scoring: a wrong or missing rule in values, missing values, eligibility, intervals, criteria or outcomes, or an output field that differs from the contract;
- behaviour without `args.comparison`: any change to a run that is not a comparison.
Also report a test that would pass on a wrong implementation of a contract rule, and a contract rule no test checks. For each, give the file and line, the contract sentence, and a concrete case that shows the defect. Do not report style. If you find nothing, say so.

Write the report to the file named by the `-o` option. End with one line exactly `VERDICT: clean`, `VERDICT: minor` (only defects that change no result) or `VERDICT: defects`.
