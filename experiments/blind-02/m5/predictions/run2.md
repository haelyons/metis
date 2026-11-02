# blind-02 run2 predictions: unchanged relaunch after run1's infra failure (sealed before launch)

Operator exposure as recorded in `run1.md`: the operator is not blind to this experiment's brief (owner chose to continue, 2026-11-02); these are not blind predictions.

## Design

Same brief (`b01_materials/BRIEF_run1.md`), pipeline, chain (`retry51.sh`), box order and fresh harness as run1. Nothing changed.

run1 (metadata only): intake PASS in 181 s (`found` true, `data` available, `licence` unknown, `licence_basis` none, no anchors). Reproduce FAIL `infra` 15 s later: the first box command (`0001-upload`) has a receipt with rc null, not timed out, not fetched, wall 15 s. In `m5/boxrun.sh` an empty rc with that shape is the remote launch failing (`Remote launch failed.`); 15 s equals ssh's `ConnectTimeout=15`. The box had answered the readiness ssh check about 3 min earlier. `pipeline.js` discards boxrun's stderr, so the ssh error text is not recorded, and `pipeline.log` holds none of the fixed ssh error phrases. Reading: a transient loss of ssh reachability; run2 tests that reading. If the same failure recurs, the fix is a pipeline unit (a bounded retry of the idempotent remote launch, with boxrun's error class recorded), not another relaunch.

## Decision rule (fixed before launch; never changed after a result)

| Result | Next |
|---|---|
| Reproduce FAIL `infra` again at the first box command | No further relaunch; build the launch-retry unit with its own tests, then relaunch. |
| Any other stage FAIL or VOID | Diagnose with an authorized reader; a pipeline change only as a new unit with its own tests; no criterion change. |
| End-to-end PASS | Report the takeaways' enums and stage facts to the owner. |

## Predictions

Probabilities are the operator's, written before launch. Rows 1 to 13 as in `run1.md`, conditioned the same way; row 14 is new.

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.85 |
| 2 | Intake `licence_basis` is `owner` or `distribution` (given intake ran) | 0.30 |
| 3 | Setup passes within its repairs | 0.70 |
| 4 | Reproduce PASS | 0.55 |
| 5 | Profile PASS (given reproduce PASS) | 0.45 |
| 6 | Profile `host_only` true (given profile ran) | 0.45 |
| 7 | Propose outcome `approved` (given propose ran) | 0.45 |
| 8 | Implement PASS (given implement ran) | 0.45 |
| 9 | Evaluate PASS (given evaluate ran) | 0.35 |
| 10 | End-to-end PASS | 0.06 |
| 11 | Run wall under 6 h | 0.65 |
| 12 | Run box cost under USD 25 | 0.75 |
| 13 | No ceiling timeout and no infrastructure failure | 0.85 |
| 14 | The first box command gets a receipt with an integer rc | 0.90 |

All predictions are read from signatures, receipts and box metadata.

## Outcome (added after the run; the sections above are unchanged since the seal 988466cc)

run2 (pushed 3bb34c48): `gpu_1x_h100_pcie` (us-west-3), pipeline wall 11,518 s (3.2 h), run box USD 10.53; two files over 95 MB left uncommitted on disk. Intake PASS (226 s; same facts as run1). Reproduce PASS (3,473 s): setup rc 0 first attempt (145 s), anchors rc 0 (1,571 s), freeze rc 0 (1,402 s); no published anchors (0 of 0), `stock_verified` true, 49.6 GPU s. Profile PASS (7,703 s): `profile_complete` true, `timed_fraction` 1, `gpu_telemetry` true, `host_only` false, `headroom` 1.047 (concurrency probe rc 0, 3,448 s). Seal PASS (116 s): verified, `prediction_count` 0. Propose PASS with `outcome` `no_feasible_method` (no model calls); implement and evaluate SKIPPED; takeaways PASS with the fixed line "Finding: negative. No menu method has measured headroom of at least 1.05 on this hardware." Bounds (`blind_read.py`, fixed menu names and numbers only): data-parallel over inputs, batching and ensembles 1.047 (k = concurrency factor, p 1); multi-GPU 1.0 (one GPU; p 0.113); pipelining 1.001 (k 2, p 0.0025); none feasible. The negative therefore rests on the measured bounds, not on the seal's zero predictions.

| # | P | Outcome | Brier |
|---|---|---|---|
| 1 | 0.85 | yes | 0.0225 |
| 2 | 0.30 | no (`none`) | 0.0900 |
| 3 | 0.70 | yes | 0.0900 |
| 4 | 0.55 | yes | 0.2025 |
| 5 | 0.45 | yes | 0.3025 |
| 6 | 0.45 | no (`host_only` false) | 0.2025 |
| 7 | 0.45 | no (`no_feasible_method`) | 0.2025 |
| 8, 9 | | not run | n/a |
| 10 | 0.06 | no (stop point propose) | 0.0036 |
| 11 | 0.65 | yes | 0.1225 |
| 12 | 0.75 | yes | 0.0625 |
| 13 | 0.85 | yes | 0.0225 |
| 14 | 0.90 | yes | 0.0100 |

Mean Brier 0.111 over 12 scored. Decision row: neither a failure nor an end-to-end PASS; the run stopped at propose on the contract's measured negative finding, so the rows above do not prescribe a next step: report to the owner. Bounded reading: on this box, the fixed menu's best measured headroom is 1.047 (plain concurrent copies of the baseline command), just under the 1.05 gate, from one probe measurement; GPU kernels occupy about 11% of the baseline's wall time. This says nothing about the seed's own comparisons, which the m5 stages do not express in full (reader `run2_progress2`: `seed_comparisons_in_pipeline` `some`). The progress reader's ceiling projection did not apply: with no method, no implement or evaluate box commands ran.
