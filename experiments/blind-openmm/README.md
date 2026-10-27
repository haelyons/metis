# blind-openmm: positive control, run blind

The operator wrote the one-line search hint in `run1/args.json` (no brief file; intake searches). The run is blind to the operator while it runs: only `operator/signatures.jsonl`, `operator/OPERATOR_TAKEAWAY.md`, `control/receipts` (rc and timings) and the raid ledger are read. Predictions are sealed in `predictions/` before launch. OpenMM is public, so the content is read after the run to update priors. Raid `shadow` is set explicitly so `lockpick` stays reserved for the blind-01 run.
