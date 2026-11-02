# run10 predictions: unit equivalence check (sealed before launch)

Operator-written from run metadata and validated reader enums only; no brief content.

## Design

Stage 1 of a staged, bounded test (owner direction 2026-11-01: test equivalence before spending on concurrency). It asks one question: does running four units on their own, by selecting their original prepared input records, reproduce the measured baseline's own per-unit result files byte for byte?

- Reference: run9's recorded baseline outputs (`run9/agent/results/reproduce/out/`), with run9's existing limits (reduced scale, unverified mirror provenance, one reproduce sample). The measured baseline includes run9's documented setup and anchors repairs; the comparison is against it, not against the pristine upstream program.
- Harness: `harness_from` = `run10_harness3/` (cdfb02f2: byte-identical copies of run9's harness plus `run_units.sh` and `units.json`; selection by a restricted copy of the prepared input list holding original records, passed through an input the measured command already accepts; no new code change; adds no writes outside `out/`). Independent review `run10_review3` (2ae3b2bb): restricted list faithful; differences from `run_command.sh` only argument handling, messages and log paths, and selection; units complete and ordered, own files only, costs match records, no added path conflict. Its verdict is `unknown`, not `needs_fix`: whether each unit computes the same as in the full run cannot be settled by reading (this check tests it), and whether the script writes only under `out/` stays open because of the inherited conflict below.
- Inherited path conflict, recorded separately: run9's measured `run_command.sh` already writes outside `out/` (writer's report). It does not affect this single-invocation check; it must be resolved or shown harmless before any concurrent stage.
- Pipeline: U49, U50a (harness unit files) and U51 (`args.units_check`), all in merge bfc6aedc (suites FAILING=0 on the identical tree). Reproduce runs setup, then one invocation of the four units nearest the median recorded cost, and compares their result files with the reference. The invocation runs in its own working directory (`units-check/`, links to the shared tree plus an empty `out/`), as the concurrency probe's arms would; the full control runs in the shared directory, as run9 did. A subset-only mismatch therefore reads as an effect of running units on their own the way stage 2 would (record selection or working directory), not of record selection alone. Only when the invocation exits 0 and the files differ does it run the full baseline once as a variability control. Every later stage is skipped.
- Box: run9's type (`gpu_1x_h100_pcie`) requested first, to limit box-to-box differences in a multi-threaded baseline.

## Decision rule (fixed before launch; the byte-for-byte criterion is never changed after a result)

| Result | Reading | Next |
|---|---|---|
| `units_match` true | The four sampled units reproduce run9's recorded files byte for byte when selected on their own. | Build the concurrency probe (U50b) and propose stage 2 to the owner. |
| Invocation exits nonzero | No evidence about equivalence. | Diagnose with a reader; no criterion change. |
| `units_match` false, `units_full_match` true | A full run on this box reproduces run9, the subset does not: running these units on their own (selected records, own working directory) changes their outputs. | Record the finding; the concurrency line stops for this baseline. |
| `units_match` false, `units_full_match` false, subset equals this box's full run | Run-to-run or box-to-box variability: the subset reproduces this box's full run, but neither reproduces run9. The run9-referenced criterion has failed and stays failed. | Report to the owner; no stage 2 without a new owner decision. |
| `units_match` false, `units_full_match` false, subset differs from this box's full run too | Inconclusive: variability and a possible subsetting effect cannot be separated. | Report to the owner. |
| Full control run fails | No variability evidence. | Report; diagnose. |

## Predictions

Probabilities are the operator's, written before launch.

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.92 |
| 2 | Setup passes on its first attempt (reused repaired `setup.sh`) | 0.60 |
| 3 | Setup passes within its four repairs | 0.90 |
| 4 | The subset invocation exits 0 | 0.80 |
| 5 | Given exit 0: `units_match` true | 0.60 |
| 6 | Given exit 0: subset wall within 0.7 to 1.3 times the four units' recorded costs | 0.65 |
| 7 | Given a mismatch: `units_full_match` true (a full run on this box reproduces run9) | 0.50 |
| 8 | Given `units_match` true: run wall under 1.5 h and run box cost under USD 6 | 0.75 |
| 9 | No ceiling timeout and no infrastructure failure | 0.90 |

Predictions 1 to 5, 7 and 9 are read from signatures (`units_match`, `units_full_match`) and receipts; prediction 6 is read after the run by an authorized reader as an enum.

## What a match would and would not establish

- **Would:** for four typical (median-cost) units, selecting their original records reproduces the measured baseline's per-unit result files on a fresh box. That is the prerequisite for a valid serial-versus-concurrent comparison.
- **Would not:** anything about throughput, the shortest or longest units, the other units, or the scientific outcome. Provenance stays unverified.

## Outcome (added after the run; the sections above are unchanged since the seal)

run10 (pushed 555cc348): `gpu_1x_h100_pcie`, wall 2442 s, run box USD 2.23. Reproduce PASS: setup rc 0 first attempt (388 s), `units-check` rc 0 (1382 s with fetch), `units_match` true, `units_full_match` null (control not run). Later stages SKIPPED as designed.

| # | P | Outcome | Brier |
|---|---|---|---|
| 1 | 0.92 | yes | 0.0064 |
| 2 | 0.60 | yes | 0.1600 |
| 3 | 0.90 | yes | 0.0100 |
| 4 | 0.80 | yes | 0.0400 |
| 5 | 0.60 | yes | 0.1600 |
| 6 | 0.65 | yes (reader `run10_post` a8b00b63 `0_7_to_1_3`; deterministic recount of `units_check.json` agrees) | 0.1225 |
| 7 | 0.50 | not applicable (no mismatch) | n/a |
| 8 | 0.75 | yes (0.68 h, USD 2.23) | 0.0625 |
| 9 | 0.90 | yes | 0.0100 |

Mean Brier 0.071 over 8 scored. Decision row: `units_match` true. `run10_post` also found every compared file non-empty, but errors in the subset's log despite exit 0, a possible collision between concurrent invocations in the shared run directory (byte check detects it only partly), avoidable without code change by per-invocation directories. Follow-up reader `run10_post2` (4580973d): the subset log's errors also appear in run9's full-run logs, have several sources, and do not affect the compared files; all four units were computed and the compared files were written by the subset invocation. Which paths are written outside `out/`, their naming and purpose, whether later units read them, and whether private copies would preserve the computation could not be established by reading. The criterion is not changed by either reader. Owner decision 2026-11-02: stage 2 runs standalone (U52); the probe counts shared-directory changes per arm because the writes could not be characterised by reading.
