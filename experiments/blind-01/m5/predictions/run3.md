# Sealed operator predictions: blind-01 m5 run3

Written and committed before launch, blind as for run2 (`predictions/run2.md`): same brief, args (tag b01m5r3), code 2c2e846, chain retry38 (12 h pipeline timeout, 13 h box), reads only through `~/.cache/blind01/blind_read.py` under the read guard hook.

Why: intake on this brief gave different fact sets in two draws (run1: data available, licence unknown; run2: data partial, licence unknown with basis unreachable). This draw measures whether "partial" is stable. Reproduce runs the data for real, so a lenient intake cannot pass missing data into a claim.

## Box
- A10 0.35, H100 PCIe 0.25, A100 SXM4 0.2, H100 SXM5 0.15, A100 PCIe 0.05; all three launch attempts fail 0.05.

## Intake
| Quantity | Prediction |
|---|---|
| intake PASS | 0.5 |
| `data` "available" | 0.5; "partial" 0.45; other 0.05 |
| `licence_basis` "unreachable" | 0.35 |
| given FAIL, `data_unavailable` the only blocker | 0.85 |
| the authority line, given PASS | 0.85 (licence "permitted" is unlikely on this brief so far) |

## Later stages, conditional on reaching them
As in run2.md: reproduce PASS 0.55 (here 0.45: a lenient data draw adds a setup-failure path), profile 0.85, seal 0.75, propose approved 0.45 (Claude refusal halts 0.15), implement 0.45, evaluate 0.5 (scorer timeout 0.3). Watch items W1 to W5 as in run2.md, same probabilities.

## Run level
- Stopping stage: intake 0.5, reproduce 0.25, profile 0.02, seal 0.06, propose 0.09, implement 0.04, evaluate 0.03; end-to-end PASS 0.01.
- Pipeline exit 0, box torn down, push verified by the chain: 0.88.
- run_box_usd: 0.05 to 0.5 at an intake stop; 0.5 to 8 at a reproduce to propose stop; 5 to 40 beyond.

## What would change my mind
- `data` "partial" again with basis "unreachable": fetch failures are systematic for this brief's sources, not chance. That points at the intake agent's network path, or at gated data only the owner can supply.
- `data` "partial" with any other basis: H2 (genuinely gated data) gains weight; an owner question, not a redraw.
