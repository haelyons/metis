These tests consume only BASELINE_OUT/run/ensemble.json and
METHOD_OUT/run/ensemble.json. They never execute workload code, inspect source,
read evaluation.json, require held-out seeds, or measure performance. The report
is written to out/tests.json in the invocation directory, including on malformed
or missing artifacts. Fixtures resolve relative to run_tests.sh.

sealed_fixture.json copies the relevant fields from the supplied EXECUTION.json
and PREDICTIONS.json. The fixed scale is eight replicas, 25000 steps per replica,
0.8 simulated ns, one input, and seeds 1000 through 1007. Langevin outputs are
stochastic according to the seal; deterministic CUDA forces do not justify a
not-applicable seed case or zero-margin comparison.

Scientific differences are method minus baseline, paired by input and seed.
The exact binomial median interval uses joint confidence .95 with Bonferroni
across the two sealed metrics. With eight pairs its endpoints are min and max,
with coverage .9921875 per metric. Reject only intervals disjoint from the open
sealed margin interval; overlapping intervals and unavailable finite bounds do
not reject. Structural cases independently detect missing or misassigned pairs.
Tests passing is not an equivalence acceptance decision; evaluate owns that.

Tail checks inspect actual output groups of sizes 3 and 5, both non-divisors of
8, and the final replica's step count and finite energy summaries. No alternate
scale, input or seed is run. The interface serializes no energy series, sample
count or internal worker chunks, so tests cannot establish actual integration,
energy sampling or internal scheduling from these summaries. They establish
only observable output invariants. No upstream output test suite is supplied in
this private view. Configuration and work validation reuse the supplied anchor
validator's observable checks (including its simulated_ns tolerance 1e-12).
The throughput reference has null tolerance and imposes no acceptance threshold.

Local validation: python3 tests/validate_tests.py runs 17 synthetic artifact
checks, each invoking run_tests.sh in an isolated temporary directory under
tests/. It uses the frozen baseline artifact and synthetic mutations only,
including omissions, duplicates, order, seeds, final steps, nonfinite values,
work totals, disjoint energy intervals and inconclusive overlapping intervals.
