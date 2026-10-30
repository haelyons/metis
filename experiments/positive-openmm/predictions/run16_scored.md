# positive-openmm run16: outcome against sealed predictions (predictions/run16.md, 5f3acc2)

Run committed a5cc2fe (the chain's commit, amended; see below). Box gpu_1x_a100_sxm4, USD 1.99/h; run_box_usd 3.65; 2.41M tokens in; wall 6,597 s; pipeline exit 0; box torn down.

## Verdict
End-to-end PASS, the first for the public positive control. Every stage passed. The method is the expected one, MPS replica concurrency (the `ensembles` proposal). It is 1.30× faster than the baseline at equal cost, and its energies match the baseline's to within float32 readout. The pipeline produced a real, verified, modest speedup on the benchmark with no operator step.

- Intake through propose passed on the A100 SXM4. Sequential ensemble 59.7 s; concurrency factor 1.80, MPS verified. Seal on its first attempt, without `protocol_cost`:
  - the eight replica seeds 1000 to 1007 of one ensemble;
  - warmup 1, repetitions 5, curve not applicable;
  - margins 38.6 and 103.5 kJ/mol from reproduce;
  - `baseline_invocation_s` 119.4 s, twice the measured ensemble, the same explicit allowance as run15.

  Propose approved `ensembles` 5 of 5, expected 1.375.
- Smoke 1: the pre-seal adapter again ran one ensemble per sealed seed (490 s) and failed `cost` (projected 5,885 s against 2,160 s). The repair's adapter, one ensemble with the sealed replica seeds, passed at 61.4 s.
- U37 worked without being exercised. The test author's `outputs.json` is `{"method_outputs": ["ensemble.json"]}`, and the method author wrote that path on attempt 1. The layout check passed, the frozen tests passed all 9 cases, and no method repair or review objection was needed.
- Method: `dhfr_ensemble.py` starts an MPS daemon and runs the eight seeded replicas in a two-worker forked process pool. Each replica gets its own CUDA context and seeded integrator. It reached 44.9 s inside the implement run.
- Evaluate:
  - Validity passed; the one published reference is recorded, not gated.
  - Equivalence: 97.5% intervals for the paired median differences were [-0.0014, 0.0039] kJ/mol (mean potential) and [-0.035, 0.024] kJ/mol (final potential), against margins of 38.6 and 103.5. That is about one float32 ulp at 3×10^5.
  - Performance: five interleaved pairs, baseline 60.7 s and method 46.2 to 46.7 s per invocation. Median speedup 1.304, one-sided 95% lower bound 1.301 (> 1.05), cost ratio 0.77, prediction ratio 0.95.
  - The performance scorer took 698 s, against 1,433 s projected at the sealed estimate and a 2,400 s budget.
- Push: the chain's push was rejected. The fresh harness set its pip cache under `out/setup/`, so every whole-`out/` fetch carried it into results (3.75 GB, one file 191 MB). I added `**/results/**/pip-cache/` to `.gitignore`, the same class as the existing `.so` and Nsight ignores; the caches stay on disk. Then I amended the run commit and pushed; the push is verified at a5cc2fe. This is an operator and repository fix, not a pipeline change.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| A100 SXM4 0.55, A10 0.18, H100 SXM5 0.1, H100 PCIe 0.12, A100 PCIe 0.05 | A100 SXM4 | yes (0.55, the mode) |
| intake PASS 0.95 | PASS | yes |
| reproduce PASS 0.93; 55 to 65 s on A100 | PASS; 59.7 s | yes; yes |
| profile PASS 0.95; every receipt fetched 0.95; MPS verified 0.92; A100 headroom 1.77 [1.6, 2.0] | PASS; yes; yes; 1.80 | yes; yes; yes; yes |
| seal PASS 0.88; first attempt `protocol_cost` 0.15 | PASS; no repair | yes; yes (against 0.15) |
| replica seeds of one ensemble 0.7; margins cite reproduce 0.9; curve not applicable 0.85 | yes; cited; yes | yes; yes; yes |
| propose approved 0.88; ensembles 0.55, data-parallel over inputs 0.4 | approved 5/5; ensembles | yes; yes |
| implement reached 0.65 | reached | yes |
| first smoke fails 0.65; repair makes second pass 0.8; VOID at smoke 0.12 | fails (`cost`); passes; no | yes; yes; yes (against 0.12) |
| passing smoke's process_wall_s 55 to 80 s on A100 | 61.4 s | yes |
| valid `outputs.json` 0.9; method writes every path on attempt 1 0.75; `layout` failure 0.2 | yes; yes; no | yes; yes; yes (against 0.2) |
| implement PASS 0.6; method repair used 0.3 | PASS; not used | yes; yes (against 0.3) |
| evaluate reached 0.39 | reached | yes |
| scorer within budget 0.9; validity_pass 0.9; equivalence_pass 0.8; differences within readout noise 0.7 | yes (698 s); yes; yes; yes (≤ 0.035 kJ/mol) | yes; yes; yes; yes |
| performance_pass 0.7; speedup_published 1.4 to 1.8 on A100; evaluate PASS 0.6 | yes; 1.30; PASS | yes; no (below the interval); yes |
| takeaways PASS 0.95; run_box_usd 3 to 8 if it reaches evaluate | PASS; 3.65 | yes; yes |
| pipeline exit 0, box torn down, push verified by the chain 0.9 | exit 0, torn down, chain push rejected | no |
| reaches implement 0.65; reaches evaluate 0.39; end-to-end PASS 0.23 | yes; yes; yes | yes; yes; yes |

## What changed my mind
- The end-to-end PASS came at 0.23. The joint probability was too low. I priced each remaining stage as an independent fresh risk, but the U34 to U37 gates absorbed the failures they were built for: the smoke repaired the per-seed adapter, U36 fit the seal on its first attempt, and U37 put the output path in front of the method author.
- The speedup interval came from run15's single attempt (37 s, 1.58×) and run12's raw pairs (1.59). This method used two workers, and the evaluate wall includes MPS start-up per invocation. The measured 1.30 is close to the proposal's own 1.375 (prediction ratio 0.95). My interval was set on the best earlier method, not on the proposal's expectation.
- The push risk I priced was infrastructure. The actual failure was a harness choice (pip cache under `out/`) that a fresh harness can make any run. The ignore rule now covers it.

## Next
The positive control has passed at a6a3ec4, so by the agreed order the next run is blind-01 (metadata only), then the same-hint OpenMM blind rerun. No pipeline unit is needed for run16.

## Later unit candidates (carried)
- Record meaning:
  - The smoke could compare its measured `process_wall_s` with the sealed `baseline_invocation_s`. The per-seed adapter has now failed smoke 1 in runs 14, 15 and 16 (490 s here against 119.4 s).
  - The seal's 2× allowance (119.4 s against a measured 60.7 s invocation) makes `protocol_cost` stricter than needed.
- Implement box operations fetch the whole `out/` tree every time; here that includes the 3.75 GB pip cache. Implement state and upload receipts took 145 to 305 s each, against 49 to 62 s for the state fetches after the method ran.
- Smoke category in the signature: a second smoke failure maps every category except `timeout` to `error_class: parse`.
- An evaluator command that timed out gets one identical retry, which cannot succeed; the stage is labelled VOID `parse` instead of `timeout`.
- Implement signature `exit_kind: infra` with `error_class: numeric` for a test failure.
- Propose with an empty menu built on missing measurements is FAIL `numeric`; VOID `infra` would separate it from a failed method.
- boxrun keeps no fetch error text.
- `test_m5_reproduce.js` intermittent failure.
