# positive-openmm run11: outcome against sealed predictions (predictions/run11.md, bdb2d07)

Run committed 2a6bca4. Box gpu_1x_a100_sxm4, USD 1.99/h; run_box_usd 1.30; 0.44M tokens in; wall 2,360 s; pipeline exit 0; box torn down; push verified by the chain.

## Verdict
Propose FAIL (`numeric`, outcome null) before any ballot, because the concurrency measurement was lost in transport. The probe itself succeeded. This is not a negative finding, and the pipeline did not claim one: under the contract, an empty menu built on missing headroom stays a FAIL with outcome null, not `no_feasible_method`.

- Intake, reproduce and profile passed on an A100 SXM4. Sequential ensemble 58.6 s; the reference item `nvidia-2025-dhfr-eight-mps-throughput-reference` measured 1.18. Profile complete, wall 62.7 s.
- The concurrency probe exited 0 after 580 s with 361 GPU-busy seconds. boxrun then began fetching `out/` at 09:42:36, wrote two files and stalled; the operation-log fetch also failed, and the receipt (`0008-concurrency.json`) has `fetched: false`. No error text was kept. The box answered again at 09:49 for teardown, so this looks like a network outage of a few minutes.
- With the result unavailable, the profile packet's `concurrency` was null (the probe never fails profile), every whole-workload bound fell to k=1, and every method was infeasible. The seal sealed an empty menu (five infeasible methods, margins SD/sqrt(8) from reproduce: 103.5 kJ/mol final, 38.6 mean; 20 repetitions; budgets [120, 240, 480]). Propose made no model call.
- Root cause: boxrun fetches each operation's outputs once. A transient transport failure after a successful command discards the measurement, even though the outputs are still on the box. The concurrency probe is the costliest profile operation (about 10 min), and nothing repeats it.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| H100 SXM5 0.25, H100 PCIe 0.25, A100 SXM4 0.1, A100 PCIe 0.05, A10 0.35 | A100 SXM4 | no (0.1) |
| intake PASS 0.95 | PASS | yes |
| reproduce PASS 0.93; 55 to 65 s on A100 | PASS; 58.6 s | yes; yes |
| profile PASS 0.95; MPS verified 0.93; A100 headroom 1.78 [1.6, 2.0] | PASS; not measured (lost in fetch) | yes; n/a; n/a |
| seal PASS 0.9; margins cite reproduce 0.9; seeds are one ensemble's replica seeds 0.65 | PASS (empty menu); cited; yes | yes; yes; yes |
| propose approved 0.9 | FAIL, no ballots | no |
| implement reached 0.7, and all given-implement predictions | not reached | no; n/a |
| evaluate reached 0.38, and all given-evaluate predictions | not reached | yes (against 0.38); n/a |
| takeaways PASS 0.95 | PASS | yes |
| run_box_usd 1.5 to 6 if the run stops before evaluate | 1.30 | no (just under; stopped at propose) |
| pipeline exit 0, box torn down, push verified 0.9 | yes | yes |
| end-to-end PASS 0.15 | no | yes (against 0.15) |

## What changed my mind
- I gave intake-to-propose about 0.7 because runs 6 to 10 all passed. I did not price in the transport: every box operation's evidence rests on a single fetch, and a probe that costs ten minutes is lost to a short outage.
- The contract's split between "no feasible method on measurements" and "missing measurements" held: the run did not report a false negative. Its label is still FAIL rather than VOID, which reads as a failure; a candidate, not a gate.

## Fix
U33 (one gate: boxrun retries a failed fetch). After the remote command finishes, boxrun fetches `out/` and then the operation log; a failed fetch is retried up to four more times, 60 s apart, and `fetched` is true only when both succeed. A retry repeats only the fetch, never the command, and the waits count in `wall_s`. Regression: run11's case (a probe that exits 0, a fetch that fails once and then succeeds) yields the measured concurrency in the profile packet. Then run12 from the same brief.

## Later unit candidates (carried)
- Propose with an empty menu built on missing measurements is FAIL `numeric`; VOID `infra` would separate it from a failed method more clearly.
- boxrun keeps no fetch error text, so the cause of a failed fetch cannot be read afterwards.
- Implement box operations fetch the whole `out/` tree (1.3 GB profile report) every time: about 6 min per operation on the A10.
- Identity smoke: frozen tests against the baseline as method, before the method author.
- Seal cost against the evaluate budget at measured ensemble cost.
- Implement signature `exit_kind: infra` with `error_class: numeric` for a test failure.
- `test_m5_reproduce.js` `concurrency-real-mps-cleared` intermittent failure.
