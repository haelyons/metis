# positive-openmm run5: outcome against sealed predictions (predictions/run5.md, 3c8b7ae)

Run committed 9d01a17. Box gpu_1x_h100_sxm5, USD 4.29/h; run_box_usd 0.66; 545k tokens in; pipeline exit 0; box torn down; push verified by the chain.

## Verdict
Inconclusive: the run stopped at reproduce on a harness defect the pipeline could not repair, so nothing after reproduce was tested.

- Setup exited 0 (`stock_verified` true). Both anchor runs exited 1 before any measurement, so `anchors_passed` is null and no score was written.
- Cause: the harness agent put a Python preflight block into `run_command.sh` that asserts `openmm.__version__ == '8.2.0'`. OpenMM 8.2.0 reports `8.2`, so the assertion fails before the workload starts. Its own `run_anchors.sh` accepts either form; its `run_evaluation.sh` repeats the strict check. The contract says `run_command.sh` contains only the measured command and its complete environment, so the preflight block was already outside the contract, but nothing checks that.
- The pipeline's one bounded repair could not fix it. The anchors repair agent diagnosed it exactly ("pinned OpenMM 8.2.0 reports __version__ 8.2; run_command.sh requires 8.2.0. Repairing that preflight requires editing run_command.sh"). But the repair may rewrite only the failing script, which the pipeline takes to be `run_anchors.sh`, although the anchors step executes `run_command.sh` too. The repair was spent on the wrong file.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| A100 0.6, H100 SXM5 0.15 | H100 SXM5 | weak (0.15) |
| intake PASS 0.9 | PASS | yes |
| reproduce PASS 0.85 | FAIL (anchor run exits 1 on a version assertion) | **no** |
| everything after reproduce | SKIPPED | not tested |
| takeaways PASS 0.95 | PASS | yes |
| run_box_usd 1 to 3 if stopping at or before propose | 0.66 | no (stopped earlier) |
| pipeline exit 0, box torn down, push verified 0.9 | yes | yes |

## Fix
U27 (repair scope, gate unchanged): the anchors step executes `run_anchors.sh` and the `run_command.sh` it invokes, so the anchors repair may rewrite either or both, with every `run_command.sh` rule still applying. The setup repair is unchanged. Regression: run5's recorded harness and anchor log, replayed with a repair that edits `run_command.sh`, reach anchor scoring; a repair that edits a third script is still refused. Then run6 from the same brief.
