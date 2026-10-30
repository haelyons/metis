The test runner reads only BASELINE_OUT/run/ensemble.json and baseline.log,
and the corresponding METHOD_OUT files. It writes out/tests.json in the run
directory. BASELINE_DIR and METHOD_DIR are deliberately unused. Python's
standard library is sufficient. No GPU, simulation, evaluation records,
timing repetitions, held-out seeds, or method scripts are accessed.

seal.json preserves the relevant PREDICTIONS.json settings and the one fixed
EXECUTION.json scale. DeterministicForces does not imply a deterministic seal:
the sealed output model is stochastic. The exact paired-median CI uses eight
seed pairs, with Bonferroni correction over the two metrics. At this scale its
bounds are the minimum and maximum paired differences. Only disjoint intervals
reject; inconclusive and overlapping intervals pass this independent test.

The canonical workload has eight replicas, 25000 steps each, 100 energy samples
per replica. Changing these to manufacture a non-divisible workload is forbidden.
The tail case traverses output records in fixed three-record windows (3+3+2),
checks both final-window records, the final seed 1007, every exact step count,
and total steps. This verifies exposed output completeness; it cannot establish
the contents of the unexported energy series or internal integration chunks.
No full-series identity, hidden seed initialization, or physical-model identity
is inferred from output metadata. Statistical summaries use the sealed margins.

The upstream case reuses the output checks in harness/run_anchors.sh, including
stdout rounding and agreement with saved timing/throughput. No upstream output
test suite or gate scripts were supplied (EXECUTION.json gate_scripts is empty).
The published throughput anchor is reference-only and imposes no tolerance.

Run PYTHONDONTWRITEBYTECODE=1 python3 tests/selfcheck.py locally to verify the
checker against frozen baseline artifacts and synthetic corruptions, without
running a method. All temporary writes stay under tests and are removed.
