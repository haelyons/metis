# blind-01 m5 run1: metadata-only diagnosis

Read: chain status lines, `operator/signatures.jsonl` (status, exit and error fields, numbers, booleans and the enum facts `data`, `licence`, `size`), `operator/OPERATOR_TAKEAWAY.md`, the `control/receipts` listing (empty), and the raid ledger row. Nothing else was read. No content review will follow: blind-01 content is never read.

## Facts
- Raid `lockpick`, run committed fb5b701 by the chain, push verified. Box gpu_1x_a10 (USD 1.29/h), up and torn down; pipeline exit 0; no large files left out.
- Intake FAIL in 175 s, one Codex call, 384,586 tokens in and 7,544 out.
- Intake facts: `found` true, `anchors_count` 3, `anchored` true, `data` "available", `licence` "unknown", `stock_environment` null, `size` "unknown".
- Signature: `exit_code` -1, `exit_kind` unknown, `error_class` none, `blockers` ["none"].
- Every later stage SKIPPED; no box command ran; run_box_usd 0.06.

## Why intake failed
The intake contract (SCHEMAS.md) passes intake only when the files are complete, `found` is true, `data` is "available", `licence` is "permitted", and `stock_environment` is not false. Three of those conditions are satisfied here. The fourth is not: `licence` is "unknown", and the owner's rule is that unverified permissions block. The agent found a public benchmark with three anchors and available data. It could not establish permission to run it. On this evidence the gate behaved as specified; nothing here shows a pipeline defect in the gate.

The signature is a reporting defect. A FAIL caused by the licence condition carries `blockers` ["none"] and `error_class` none, although the signature vocabulary already has a `licence` blocker. The takeaway's Blockers section therefore reads "none", and its gate flags omit `licence` and `data`. The cause was recoverable here only because the facts were complete. This is the same gap blind-openmm run1 showed (intake FAIL, error_class none).

## Hypotheses (not resolvable from metadata; no content review)
- H1 0.5: the benchmark's licence is genuinely absent or restrictive, so "unknown" is correct. The fix would be owner-side: a brief that states the permission basis, or an owner decision on the rule.
- H2 0.3: a licence exists but the agent could not read it. The agent's web search may serve cached pages only; the network proxy has been disabled since 7c14eef, so its shell can still reach hosts directly.
- H3 0.2: a licence was readable but the agent judged it conservatively (for example an unclear clause for benchmarking use).

## Scoring of sealed predictions (run1.md, 16ce6f3)
| Prediction | Outcome | Hit |
|---|---|---|
| A100 SXM4 0.5, A10 0.18, H100 SXM5 0.15, H100 PCIe 0.12, A100 PCIe 0.05 | A10 | no (0.18 on the outcome) |
| intake PASS 0.6 | FAIL | no |
| given FAIL: `found` false 0.6; a named blocker 0.5 | `found` true; blockers none | no; no (against 0.5) |
| stopping stage intake 0.4 (the mode) | intake | yes |
| exit 0, teardown, chain push 0.88; a file over 95 MB 0.1 | yes; none | yes; yes (against 0.1) |
| run_box_usd 0.1 to 0.5 at an intake stop | 0.06 | no (below) |
| end-to-end PASS 0.02 | no | yes (against 0.02) |

"What would change my mind" item 1 fired: intake FAIL with no named blocker and `error_class: none`.

## Next
- Pipeline (no content needed): U38, one reporting gate. An intake FAIL signature names the failed conditions from the existing blocker vocabulary: `licence` when `licence` is not "permitted", `data_unavailable` when `data` is not "available", and `env_irreproducible` when `stock_environment` is false.
- Owner: blind-01 cannot pass intake until its licence is established. Only the owner can see whether the brief states it, or decide whether the rule should accept an owner-stated permission basis. The operator will not read the brief to find out.
