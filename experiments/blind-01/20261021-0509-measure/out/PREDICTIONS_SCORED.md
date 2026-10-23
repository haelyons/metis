# Predictions scored (mechanical, measure.sh score; no model)

Sealed predictions sha256 609f1bba1fd8777889245525ff1a5bf1309daf773b698f22c9bb72a537c891d9 (out/SEALS.txt). Rule: held if the measured value lies within the band; void if the record's run_valid is false or the record is missing.

- P1 (af2_h_per_run, PROXY 0.5): void; measured 0.3424851200315687 hours per AlphaFold-Multimer run; band [0.2, 1.25]; record decision VOID; run_valid False
- P2 (md_ns_per_day_a100, PROXY 129): void; measured None nanoseconds simulated per day; band [51.6, 322.5]; record decision VOID; run_valid False
- P3 (aux_h_per_pair, GUESS 1): refuted, unvalidated; measured 0.009490715662638345 hours per capsid-receptor pair; band [0.3333, 3]; record decision FAIL; run_valid False
- P4 (n_storage_gib, GUESS 200): void; measured 9.949365869164467 gibibytes; band [66.67, 600]; record decision VOID; run_valid False

Anchor: FAIL. Launches: 13; estimated USD 10.72. Base rate update: 0 held of 0 decided; measured but scientifically unvalidated (anchor FAIL, calibration valid): 1. Compute tables logged for 2 of 13 launches.
