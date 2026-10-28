# positive-openmm run7: outcome against sealed predictions (predictions/run7.md, 42d4256)

Run committed aef0723. Box gpu_1x_h100_pcie, USD 3.29/h; run_box_usd 6.19; 2.10M tokens in; wall 6,769 s; pipeline exit 0; box torn down; push verified by the chain.

## Verdict
Inconclusive: the first run through implement (PASS), then evaluate was VOID because the baseline's evaluation adapter crashed before writing measurements. Validity passed; equivalence and performance were never measured, so no speedup or equivalence claim exists.

- Intake to propose passed as in run6: sequential ensemble 51.8 s on H100 PCIe, MPS verified (factor 1.94), seal margins SD/sqrt(8) of each per-seed outcome cited from reproduce's `ensemble.json` (132.2 kJ/mol for final potential), propose approved 5 of 5 for data-parallel over inputs, expected 1.5.
- Implement PASS. U28 held: the isolated test author ran 12 commands and the method author 34, with no namespace errors. The first method attempt failed one independent test (`equivalence`); the single repair fixed it; the launch review passed. The method runs replicas as concurrent processes under its own MPS control directory.
- Evaluate VOID (`missing_or_invalid_measurements`): validity passed (method anchors), then the first equivalence run, baseline arm, exited 1. The harness agent wrote `run_evaluation.sh` during reproduce, before any seal existed, and guessed the shape of `EVAL_INPUTS`. The seal's `evaluation_inputs` was `{configuration, generated_inputs, identity, ids, pins, software_pins}`; the script treated every key as an input and passed the `generated_inputs` list to `pathlib.Path` (TypeError). The contract said only that `EVAL_INPUTS` is a JSON encoding of `evaluation_inputs`; neither the harness prompt nor the method author prompt states that `ids` is the input list.
- The baseline evaluation adapter is first executed in evaluate; nothing earlier exercises it.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| H100 SXM5 0.55, H100 PCIe 0.08 | H100 PCIe | no (0.08) |
| intake PASS 0.9 | PASS | yes |
| reproduce PASS 0.85; 35 to 55 s on H100 | PASS; 51.8 s | yes; yes |
| profile PASS 0.9; MPS verified 0.9; H100 headroom 2.0 [1.6, 2.4] | PASS; verified; 1.94 | yes; yes; yes |
| seal PASS 0.75; SD/sqrt(n) cited from reproduce 0.6 | PASS; SD/sqrt(8) cited | yes; yes |
| propose approved 0.75; data-parallel 0.6 | approved 5/5; data-parallel | yes; yes |
| implement reached 0.4 | reached | yes |
| test author runs commands and writes run_tests.sh 0.85 | yes | yes |
| method author writes all three files 0.8; patch applies 0.75 | yes; yes | yes; yes |
| implement PASS 0.35 given reached | PASS | yes (against 0.35) |
| method starts its own MPS daemon 0.6; processes over threads 0.75; repair used 0.4 | yes; processes; repair used | yes; yes; yes |
| evaluate reached 0.14 | reached | yes (against 0.14) |
| an evaluation script hits its 2400 s budget 0.3 | no; the baseline equivalence run failed after 85 s | no timeout |
| validity_pass 0.8 | true | yes |
| equivalence_pass, performance_pass, speedup | not measured (VOID) | n/a |
| takeaways PASS 0.95 | PASS | yes |
| run_box_usd 5 to 20 if it reaches evaluate | 6.19 | yes |
| pipeline exit 0, box torn down, push verified 0.9 | yes | yes |

## Fix
U29 (interface statement, no gate change): the contract now fixes both shapes. `EVAL_INPUTS` is an object whose `ids` array lists the input identities in order, and its other keys are never inputs. `EVAL_SEEDS` is `paired_median` with integer seeds in order, or `deterministic` with one null seed. The harness prompt, which writes `run_evaluation.sh` before the seal exists, and the method author prompt both state them. Regression: run7's sealed `evaluation_inputs` and `paired_seed_tests` reach the adapters intact; an adapter that follows the contract yields ids by seeds in order and is accepted, and one that treats every key as an input is not. Then run8 from the same brief.

## Later unit candidate
Exercise the baseline evaluation adapter before evaluate (for example a one-seed equivalence smoke after the seal), so an adapter defect costs a repair rather than a VOID evaluation.
