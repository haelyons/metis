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
