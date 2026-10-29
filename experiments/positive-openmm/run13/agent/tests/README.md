The runner reads BASELINE_OUT and METHOD_OUT only. It never reads or executes
METHOD_DIR. It writes METHOD_OUT/tests.json (out/tests.json in the supplied
interface), including on missing or malformed output, and exits nonzero on failure.
It accepts direct ensemble.json or exactly one immediate child ensemble.json,
matching the frozen harness layout. It requires the corresponding stdout.log.

Sources: intake/EXECUTION.json, intake/brief.md, proposal.json, PREDICTIONS.json,
harness/run_anchors.sh and frozen baseline ensemble.json. The upstream output
validation is adapted from run_anchors.sh without its workload invocation. No
upstream fixed-work test suite or gate scripts are provided (gate_scripts=null).
The runner uses Python's standard library and launches no simulations.

Exactly the sealed 8 replicas, seeds 1000..1007, 25000 steps, CUDA configuration
and 0.8 ns are checked. The tail case checks records 6 and 7 explicitly: they
form the remainder of a three-record traversal of the eight actual outputs.
No second workload, altered seed set or altered step count is introduced.
The sealed work is divisible by both the 250-step sampling interval and the
four-worker scheduling bound. Output-only tests cannot establish that an
internal scheduler handles a different workload with a partial worker wave.
The baseline saves neither energy series nor sample counts; these tests do not
claim to verify internal sampling, RNG calls, timing boundaries or trajectories.

Outputs are stochastic under the seal despite DeterministicForces=true. Energy
comparisons pair the single input's outputs by replica and seed. Exact median
order-statistic intervals use per-tail alpha .0125 (joint confidence .95 across
two metrics). With eight pairs the interval is min/max. Only an interval disjoint
from the open sealed margin rejects; overlap and insufficient finite-interval
sample sizes pass this screening case. Structural completeness is checked
separately. No evaluation records, timing repetitions, compute budgets or
performance acceptance thresholds are used here.

Local verification: bash -n tests/run_tests.sh; python3 -B tests/self_check.py.
Self-checks run the shell entry point against frozen baseline copies and
synthetic corruptions in temporary directories under tests, then remove them.
