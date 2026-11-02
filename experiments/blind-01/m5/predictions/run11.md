# run11 predictions: standalone unit probe (sealed before launch)

Operator-written from run metadata and validated reader enums only; no brief content.

## Design

Stage 2 of the staged, bounded test (owner decisions 2026-11-01 and 2026-11-02: test equivalence before spending on concurrency; stage 2 standalone). It asks one question: do the measured baseline's units gain throughput when several run at once on one box, with every output still byte-identical?

- Reference: run9's recorded baseline outputs, with run9's limits (reduced scale, unverified mirror provenance, one reproduce sample). run10 (U51) showed that four median-cost units selected on their own reproduce those files byte for byte; `run10_post` and `run10_post2` found the comparison non-vacuous (files non-empty, units computed, files written by the subset; log errors also present in run9's full run and not affecting compared files).
- Harness: `harness_from` = `run10_harness3/` (unchanged from run10).
- Pipeline: U50b (probe script unit mode, 10568947) and U52 (`args.units_probe`, c7397e4d), merge 90e379cd; `dut/` identical to the tested tree. Suites pass on that tree, apart from an intermittent profile-fixture failure in `test_m5_reproduce.js` (profile path, which this run never reaches; one rerun passed in full, one hit it again). After setup, one probe command runs eight arms over the same four median-cost units, in the fixed order a-1, b-1, c2-1, c4-1, c4-2, c2-2, b-2, a-2: `a` one invocation of all four (the baseline's own serial mode), `b` four single-unit invocations one after another, `c2` two at once then two at once, `c4` four at once. `a-1` must match run9's digests (`baseline_match`) before later arms run; every later invocation must match `a-1` byte for byte (`outputs_match`). Factor per batch = mean counted `a` wall / mean `c<n>` wall; per-invocation start-up costs count against it.
- Inherited path conflict: the measured command writes into the shared run directory, which concurrent invocations share through their links; which paths could not be established by reading. Each arm counts changed entries there (`shared_changes`, fact `units_shared_writes`); the count never changes an outcome.
- Box: `gpu_1x_h100_pcie` requested first (run9's and run10's type). The work is CPU-only; the factor is specific to this box's CPU count.

## Decision rule (fixed before launch; never changed after a result)

| Result | Reading | Next |
|---|---|---|
| `measured`, largest factor ≥ 1.05 | Running units at once yields more work within the same wall time on this box, for typical units, with byte-identical outputs. A claim of more work within budget only; not a better outcome. | Report the factors to the owner with `units_shared_writes`; any further stage needs a new owner decision. |
| `measured`, largest factor < 1.05 | Valid negative finding: no throughput gain from running units at once on this box. | Report; the concurrency line stops for this baseline. |
| `outputs_mismatch` | Running units at once changes outputs (collision in shared files or behaviour under load). | Report with `units_shared_writes`; no concurrency claim without isolation. |
| `baseline_mismatch` | `a-1` did not reproduce run9 on this box, contrary to run10: variability. | Report; no concurrency claim. |
| `failed` | An invocation exited nonzero. | Diagnose with a reader; no criterion change. |
| `skipped` | Budget left no concurrent arm. | Report. |
| Reproduce FAIL (timeout, infra, parse, install) | No evidence. | Diagnose. |

## Predictions

Probabilities are the operator's, written before launch.

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.93 |
| 2 | Setup passes on its first attempt | 0.75 |
| 3 | Reproduce PASS (a valid unit-mode file) | 0.85 |
| 4 | `units_outcome` = `measured` | 0.72 |
| 5 | Given measured: largest factor ≥ 1.05 | 0.70 |
| 6 | Given measured: largest factor ≥ 1.3 | 0.40 |
| 7 | Given measured: largest factor ≥ 2.0 | 0.08 |
| 8 | Given both batch factors: `units_factor_4` > `units_factor_2` | 0.45 |
| 9 | `units_shared_writes` true (given at least one arm ran) | 0.65 |
| 10 | Given `outcome` not measured: `outputs_mismatch` | 0.35 |
| 11 | Run wall under 4 h and run box cost under USD 14 | 0.75 |
| 12 | No ceiling timeout and no infrastructure failure | 0.90 |

Outcome distribution behind 4 and 10: measured 0.72, failed 0.10, outputs_mismatch 0.09, baseline_mismatch 0.05, skipped 0.03, invalid_units 0.01. All predictions are read from signatures (`units_outcome`, `units_factor_2`, `units_factor_4`, `units_shared_writes`) and receipts.

## What a result would and would not establish

- **Would:** for four typical (median-cost) units on this box type, whether running them at once yields more work per wall hour than the baseline's own serial mode, with byte-identical outputs; and whether the shared run directory changes while they run.
- **Would not:** anything about the shortest or longest units, other box types, the full published scale, method quality, or the scientific outcome. Provenance stays unverified. A factor is a throughput claim only (more work within budget), kept separate from any better-outcome claim.

## Outcome (added after the run; the sections above are unchanged since the seal 8c6113ac)

run11 (pushed 7ccd08f8): `gpu_1x_h100_pcie`, pipeline wall 8127 s (2.26 h), run box USD 7.43. Intake PASS (259 s). Reproduce PASS: setup rc 0 first attempt (388 s), `concurrency` rc 0 (6988 s with fetch, budget 42,061 s). Facts: `units_outcome` = `measured`, `units_factor_2` = 1.558, `units_factor_4` = 2.298, `units_shared_writes` = true. Later stages SKIPPED as designed.

| # | P | Outcome | Brier |
|---|---|---|---|
| 1 | 0.93 | yes | 0.0049 |
| 2 | 0.75 | yes | 0.0625 |
| 3 | 0.85 | yes | 0.0225 |
| 4 | 0.72 | yes | 0.0784 |
| 5 | 0.70 | yes (2.298) | 0.0900 |
| 6 | 0.40 | yes | 0.3600 |
| 7 | 0.08 | yes | 0.8464 |
| 8 | 0.45 | yes (2.298 > 1.558) | 0.3025 |
| 9 | 0.65 | yes | 0.1225 |
| 10 | n/a | not applicable (measured) | n/a |
| 11 | 0.75 | yes (2.26 h, USD 7.43) | 0.0625 |
| 12 | 0.90 | yes | 0.0100 |

Mean Brier 0.178 over 11 scored. The size of the gain was badly underpredicted (predictions 6 to 8): the operator expected little headroom because the baseline's own threads already use at least half the logical CPUs.

Decision row: `measured`, largest factor ≥ 1.05. On this box type, for four median-cost units, running them four at once did the same work in 1/2.30 of the serial mode's wall time (two at once: 1/1.56), with every compared output byte-identical to run9's recorded files and to the serial invocation. This is a claim of more work within budget only, not a better outcome, and it is specific to this box's CPU count. The shared run directory changed during at least one arm (`units_shared_writes` true); the byte checks passed regardless. Next per the rule: report to the owner; any further stage needs a new owner decision.

Interpretation (after the result; the criterion is unchanged). Deterministic content-free summary of `concurrency.json` (`run11_post` check, c471cf62), on 26 logical CPUs: every arm counted with all exit codes 0; wall relative to `a-1`: b-1 1.16, c2-1 0.64, c4-1 0.43, c4-2 0.44, c2-2 0.64, b-2 1.18, a-2 1.00; per-replicate factors a-1/c2-1 1.56, a-2/c2-2 1.56, a-1/c4-1 2.32, a-2/c4-2 2.27; separate/serial 1.17 (per-invocation start-up cost); effective cores per CPU 0.28 serial, 0.25 separate, 0.47 for two at once, 0.73 to 0.75 for four at once, busy fraction alike; `shared_changes` exactly 1 in every arm, serial arms included. Authorized reader `run11_post` (c471cf62, enums only): gain source `idle_cpu_in_serial_mode`; factor holds against the nearest serial arm; order effect `later_arms_slower` (small: b-2 1.18 against b-1 1.16); no sign of less work in later invocations; but `concurrent_log_problems` = `new_in_concurrent` (the concurrent invocations' logs show errors or warnings the serial ones do not) and `outputs_cover_all_results` = `partly` (the compared paths are only some of each unit's result files); what the shared entry is and whether invocations read each other's writes stay `unknown`. So the byte-identity holds for the compared files only, and the new log messages are not yet characterised; a follow-up reader (`run11_post2`) characterises both before any claim beyond the measured factors.
