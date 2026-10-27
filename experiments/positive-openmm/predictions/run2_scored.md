# positive-openmm run2: outcome against sealed predictions (predictions/run2.md, b1e515f)

Run committed 2c3dcde (raid getaway2). Box gpu_1x_a100_sxm4, USD 1.99/h; pipeline usd 0.05; 151,352 tokens in; pipeline exit 0; box torn down; push verified.

## Verdict
Inconclusive: the run stopped at intake, so none of the hypotheses (MPS verification, headroom, the U23 gate) was tested. Intake FAILed on completeness, not on evidence. Every intake fact passed (found true, data available, licence permitted, stock_environment null, one reference, anchored false). The failing check is `baseline.json.build_commands`, which was `[]`. The agent put the same command run1 listed as a build (`python3 -m pip install openmm==8.2.0 OpenMM-CUDA-12==8.2.0`) under a new key `install_commands`, with `build_commands_reason` "Brief specifies binary pip installation; no source build command required or supplied." The baseline was executable as written.

This is a pipeline defect, not missing evidence. SCHEMAS.md requires a non-empty `build_commands`, but the intake prompt lists the field without saying it must be non-empty or that package installs count as builds. Run1's agent read it one way and run2's agent read it the other. The takeaway shows `error_class=none` on this FAIL, so the cause was found only by reading the public intake files (the known follow-up: intake error_class on FAIL).

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| H100 SXM5 0.4, PCIe 0.35, A100 0.15 | A100 SXM4 | weak (0.15) |
| intake PASS 0.85 | FAIL (completeness: empty build_commands) | **no** |
| anchored false 0.85 | false (one reference) | yes |
| everything after intake | SKIPPED | not tested |
| takeaways PASS 0.95 | PASS | yes |
| run_box_usd 1 to 3 if stopping at or before propose | 0.05 (pipeline stages only) | no (stopped earlier than any predicted stop) |
| pipeline exit 0, box torn down, push verified 0.93 | yes | yes |

## Fix
U24 (contract first, gate unchanged): the intake prompt states that `build_commands` lists every command that builds or installs the baseline, including package-manager installs of released binaries, and is never empty. Regression: run1's recorded intake files still PASS; run2's recorded files still FAIL, because the gate is unchanged and they do not meet it. Then rerun the positive control (run3) with a fresh harness and predictions resealed against the new code.
