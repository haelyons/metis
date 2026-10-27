# blind-openmm run1: metadata-only diagnosis (sealed before reading content)

Read so far: operator/signatures.jsonl, operator/OPERATOR_TAKEAWAY.md, control/ listing (no receipts: no box command ran), raid ledger, chain output. Nothing under agent/ or pipeline.log.

## Facts
- Run committed 881af3c; box gpu_1x_h100_sxm5 up and torn down; pipeline exit 0; push verified.
- intake FAIL in 136 s: found=false, anchors_count 0, data "partial", licence "unknown", stock_environment null, size unknown. One Codex call: 416,993 tokens in, 3,872 out. error_class none, exit_kind unknown, blockers none.
- Every later stage SKIPPED; run_box_usd 0.16 (box idle for the whole run).

## Scoring of sealed predictions (predictions/run1.md)
- intake PASS 0.8: **miss**. My "what would change my mind" item 1 fired: the search-hint path is the bottleneck, not compute.
- Most likely stopping stage reproduce 0.35, intake 0.1: miss (intake).
- Box H100 SXM5 0.6, exit 0 and teardown and push 0.9, end-to-end pass 0.06: consistent.
- Tokens 300k to 900k: 417k in range, but all spent in one intake call.

## Hypotheses, before reading content (probabilities sum to 1)
- H1 0.35: my hint over-specified the workload. "A fixed set of independent simulations with distinct random seeds" matches no published benchmark as written (OpenMM's benchmark runs one simulation), and the prompt forbids substituting or inventing, so the agent declined. data "partial" fits finding the DHFR inputs but not the described set.
- H2 0.30: the agent found the OpenMM DHFR benchmark but no qualifying published anchor (number plus tolerance) for it, and treated "no anchor" as "not found". licence "unknown" argues against a settled candidate, which weakens H2.
- H3 0.25: the search budget (two searches, three candidates) ran out on large pages (417k input tokens for one call) before licence and anchors were confirmed.
- H4 0.10: web search or network failure inside the Codex sandbox.

## System issues visible from metadata alone
1. An intake FAIL carries error_class none and exit_kind unknown, so a blind operator cannot tell "nothing qualifies" from "search failed". Intake failure needs a fixed-vocabulary reason in the signature.
2. retry7.sh brings the box up before intake, which needs no GPU. Cost here USD 0.16 and about 10 minutes of capacity wait; it grows with a slow intake.
