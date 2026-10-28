# positive-openmm run3: outcome against sealed predictions (predictions/run3.md, 9c177cd)

Run committed f4e1d95 (raid wheelman2). Box gpu_1x_a100_sxm4, USD 1.99/h; pipeline usd 1.15; 958k tokens in; pipeline exit 0; box torn down. The chain's push was rejected: the harness had installed a compatible NVRTC wheel into `out/nvrtc-compat.*/`, which reproduce and profile fetched, including two 101 MB shared libraries per copy. The operator removed every `.so` file from the unpushed commit, ignored `**/results/**/*.so` and `*.so.*`, amended and verified the push.

## Verdict
The measurement path now works on a positive control; the run stopped at seal on a missing input, not on evidence.

- U22 and U24 behaved as intended. Intake PASSed with the pip install in `build_commands`. No harness script touches `CUDA_MPS_*`. The probe recorded `mps: true, mps_failed: false` after verifying client connections. Singles took 61.4 to 61.5 s; two copies 88.3 s (factor 1.39); four copies 137.3 s (factor 1.79). The factor rising from 2 to 4 copies is what MPS overlap looks like, unlike run1's flat time-sliced 0.86.
- Seal FAILed with `stochastic_equivalence_invalid`. The seal agent marked outputs stochastic (seeded Langevin dynamics, as the contract requires even for reproducible fixed seeds), which requires positive absolute equivalence margins from scientific requirements or baseline variability. The intake records no published tolerance, and the seal agent may read only intake, profile and bounds, so it found no measured variability. It recorded the margins as unavailable (`tolerance.abs: null`, status `blocked_missing_scientific_margin`) instead of inventing them. That was correct behaviour.
- The measurement it needed already existed. Reproduce's baseline output (`results/reproduce/out/dhfr.*/ensemble.json`) holds per-seed energies for the eight seeds: the standard deviation across seeds is 109 kJ/mol for the mean potential and 293 kJ/mol for the final potential. The pipeline measured the baseline's variability and then withheld it from the stage that needed it.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| H100 SXM5 0.3, PCIe 0.3, A100 0.3, A10 0.1 | A100 SXM4 | yes (0.3) |
| intake PASS 0.9; build_commands holds the pip install 0.95; anchored false 0.85 | PASS; yes; false | yes |
| reproduce PASS 0.85; sequential ensemble 60 to 100 s on A100 | PASS; 59.3 s (anchor run), 61.4 s (probe singles) | PASS yes; time at the low edge |
| harness respects the MPS rule 0.85 | no `CUDA_MPS_*` in any harness script | yes |
| profile PASS 0.9 | PASS | yes |
| probe mps true (verified) 0.75 | mps true, mps_failed false | yes |
| A100 headroom median 1.5 [1.05, 2.2] | 1.79 | yes |
| seal PASS 0.75; prediction_count 3 | FAIL (`stochastic_equivalence_invalid`); 3 rows (data-parallel 1.35 to 1.68, batching 1.18 to 1.55, ensembles 1.30 to 1.65) | seal **no**; count yes |
| reaches implement 0.2 | no | consistent |
| run_box_usd 1 to 3 if stopping between reproduce and propose | 1.15 | yes |
| pipeline exit 0, box torn down, push verified 0.93 | exit 0 and torn down; chain push rejected (large files), fixed by the operator | no |

The reference (NVIDIA, about 5.0 µs/day for eight DHFR runs on an H100 under MPS) was measured at 1.17 µs/day for the sequential ensemble on an A100 and reported, not scored.

## Fix
U25 (seal inputs, gate unchanged): the seal agent also reads the baseline's measured outputs under `A/results/reproduce/`. A margin from baseline variability names the measured file and statistic in its `source`. Without a requirement or measured variability, the seal stays invalid as now. Regression: run3's recorded predictions still FAIL the unchanged validator. Then run4 with a fresh harness and predictions resealed against the new code.
