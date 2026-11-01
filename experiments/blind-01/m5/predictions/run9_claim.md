# run9 claim: reduced-scale consistency check

Operator-written from validated reader enums and run metadata only; no brief content. Accepted by the owner on 2026-11-01, replacing "reduced-scale baseline calibration".

**Claim.** The mirrored materials install and run from start to finish. On a reduced set of inputs, the study's main quantity clears its one published threshold. Two ungated reference quantities also fall within the tolerance they would have had as anchors.

## Measurements

| Item | Measurement |
|---|---|
| Box | `gpu_1x_h100_pcie`, USD 3.29/h. Run total 39,907 s, USD 36.47 (run commit cd717e32). |
| Setup | Passed on the fourth attempt, after three repairs. |
| Anchors runs | rc 1 at 5,091 s, rc 1 at 6,159 s, then rc 0 at 7,347 s. Receipt walls include fetching `out/`. |
| Profiled command | One command took 1 to 2 h (`run9_replay`). |
| Gated anchor | One anchor, `anchors_passed` 1/1. It is the main quantity (`run9_scale`). It is compared as a lower threshold, and the measured value is more than 50% away from the published value (`run9_scale2`). |
| References | Two ungated references measure other quantities. Both are within the tolerance they would have had as anchors. |
| Scale | The number of distinct inputs was reduced 10 to 100 times relative to the published protocol (`run9_scale`, `run9_units`). The earlier category "replicates or samples" merged this with repeated trials; it is not a replicate count. |
| Work units | 8 to 63 units, run one after another (`run9_par`). Each unit is one distinct input, and units take 1 to 10 min each. Their costs vary widely, with a coefficient of variation over 50% (`run9_units`). |
| Combination | Per-input results are combined by taking the best or maximum (`run9_units`), so the reported quantity depends on how many inputs are covered. Expanding the inputs would add coverage, not precision; this is inferred (`run9_units`). |
| Compute | The published baseline is CPU-only. GPU utilisation was zero and Nsight had no capture problem (`run9_diag4`). It is multi-threaded, and that was measured (`run9_par`). The box has 8 to 31 logical CPUs (`run9_replay`). |

## Limits

- **Not a calibration.** The source of the anchor's tolerance, the noise expected at run9's scale, and the margin as a fraction of the tolerance are all unknown. Whether a defective copy would fail the check is also unknown, at both run9's scale and the published scale.
- **Effect of the reduced scale is inferred.** A reader inferred that the reduced scale makes the threshold harder to pass, so the pass is conservative on that one check (`run9_scale2`).
- **Provenance is unresolved.** The mirror's match to the original is unverified (owner decision, 2026-10-31). A run at the published scale would not resolve it.
- **One sample.** Reproduce passed once and has not been repeated.
- **The published scale was not attempted.** Its estimated serial runtime on this box is 12 to 48 h, beyond the 12 h run ceiling.

## After reproduce

- **Profile stopped with `parse`.** Nsight Systems 2025 writes empty files for skipped reports, and the summariser rejected them.
- **That parsing failure is fixed.** U48 (b28f0452) and the U48 correction (0681a9b4) now count those empty files as zero.
- **A replay on the saved files gives the result without a new run.** With the fix, the profile gate stops with `numeric`, failing only the wrapper rule; the rest of the gate passes (`run9_replay2`).
- **No further full run.** The owner judged that another full run is not justified just to reach this stop.

Reader commits: `run9_diag4` 0bc378bb, `run9_replay` bc6885c7, `run9_par` 4eaaf88c, `run9_scale` d1acf41d, `run9_scale2` c3d8e782, `run9_replay2` d17bdef0, `run9_units` 5e29f221.
