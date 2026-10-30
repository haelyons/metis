# blind-openmm run4: metadata-only diagnosis (sealed before reading content)

Read so far: chain status lines, `devbox_up.log` (the box launcher's own output, written before any agent runs), `operator/signatures.jsonl` (numeric, boolean and enum fields), the Blockers section of `operator/OPERATOR_TAKEAWAY.md`, the `control/` listing, the box record and the raid ledger. Nothing under agent/ or pipeline.log.

## Facts
- Run committed 361460a by the chain, push verified. Raid: glasscutter.
- **The box never came up.** The launcher selected gpu_1x_h100_pcie (us-west-3), the instance "never became active with an IP", and the launcher terminated it itself (`devbox up exit 1`). The chain ran the pipeline anyway: retry32.sh does not stop when the box launch fails.
- Intake PASS in 176 s, 436,711 tokens in. Facts: `found` true, `anchors_count` 1, `anchored` false, `data` "available", `licence` "permitted", `licence_basis` "distribution", `stock_environment` null, `size` "unknown".
- Reproduce FAIL in 15 s, exit 2, `exit_kind` "infra": no box to run on. Every later stage SKIPPED; takeaways PASS; run_box_usd 0.

## What the metadata says
- U40 works end to end: the fact was reported, carried into the signature and shown in the takeaway.
- **The licence judgement contradicts run3 on the same basis.** Run3 recorded `licence_basis` "distribution" with `licence` "unknown" (reconstructed: its benchmark.json shows the same reasoning). Run4 records "distribution" with "permitted". `anchors_count` 1 in both suggests the same study. So the same kind of evidence gave opposite verdicts in consecutive runs.
- The pipeline handled the missing box correctly: reproduce failed fast as infra, not as a benchmark finding. The defect is in the chain, which should not start the pipeline without a box.

## Hypotheses: which study (sums to 1)
- H1 0.6: the NVIDIA MPS two-process `benchmark.py` study, as in run3 (anchors 1, basis distribution).
- H2 0.3: OpenMM's own `benchmark.py` DHFR test, without the MPS article.
- H3 0.1: other.

## Scoring of sealed predictions (predictions/run4.md, 9281cd7)
| Prediction | Outcome | Hit |
|---|---|---|
| H100 SXM5 0.4, H100 PCIe 0.3, ... | H100 PCIe selected, never active | no (0.3 on the outcome) |
| `licence_basis` reported 0.9 | "distribution" | yes |
| files complete 0.85 | yes | yes |
| intake PASS 0.4 | PASS | no (0.4 on the outcome) |
| `licence` "permitted" given basis distribution 0.5 | permitted | a coin; consistent with 0.5 |
| stopping stage reproduce 0.2 | reproduce (infra) | no (0.2 on the outcome); the mechanism was not a predicted one |
| exit 0, teardown, chain push 0.85 | yes | yes |
| run_box_usd 0.05 to 0.5 at an intake stop | n/a; 0 at a reproduce infra stop | n/a |

No "what would change my mind" item fired. A box that never came up was not on my list. The chain should treat it as a failed launch, not as a run.

## Next
1. Chain: stop before the pipeline when the box launch fails (retry the launch a bounded number of times first). This is operator tooling, not dut/pipeline.
2. Rerun as run5 at the same code. Intake will be redrawn, so the licence verdict is again a coin until the owner decides the licence criterion.
