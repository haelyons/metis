# Sealed operator predictions: blind-openmm run2

Written and committed before launch. Run2 uses the exact one-line hint from run1 (`run2/args.json`, no brief file; intake searches). It runs blind to the operator; OpenMM is public, so the content is read after the run. Code at 73f03dd. Single-GPU dev box, chain `~/.cache/blind01/retry32.sh` (status lines only). Probabilities are mine; intervals are 80%.

What changed since run1 (90045f0):
- Agents no longer inherit the operator's Codex network-proxy allowlist, MCP servers or skills (7c14eef).
- Published values without tolerances qualify as references (U20).
- U21 to U38: everything from reproduce to evaluate. The public positive control passed end to end at a6a3ec4 (run16, 1.30×, A100 SXM4).
- An intake FAIL now names `licence`, `data_unavailable` or `env_irreproducible` blockers (U38).

Unchanged: the hint path allows at most two searches and three candidates. Run1's content review found that the hint's wording ("a fixed set of independent simulations with distinct random seeds") selected the OpenMM 7 paper's energy-drift study, not a throughput benchmark.

## Box
- A100 SXM4 0.5, A10 0.18, H100 SXM5 0.15, H100 PCIe 0.12, A100 PCIe 0.05.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.45. Benchmark chosen: OpenMM's `benchmark.py` DHFR test 0.5, the OpenMM 7 paper's energy-drift scripts 0.35, other 0.15. Given FAIL: `found` false 0.55; `licence` blocker 0.4; `data_unavailable` blocker 0.4 |
| reproduce | PASS 0.65 given intake PASS. If it fails: harness or setup 0.6, anchors 0.4 |
| profile | PASS 0.9 given reproduce PASS; headroom on A100 1.75 [1.3, 2.1] if the workload is DHFR-sized replicas; a fixed-time benchmark (headroom near 1 or an exact multiple) 0.2 given `benchmark.py` |
| seal | PASS 0.8 given profile PASS; first attempt `protocol_cost` 0.15 |
| propose | approved 0.6 given seal PASS; ensembles or data-parallel 0.85 given approved |
| implement | reached 0.13 overall; PASS 0.55 given reached; first adapter smoke fails 0.6 given reached |
| evaluate | reached 0.07 overall; PASS 0.6 given reached; speedup_published 1.2 to 1.8 on A100 given PASS |
| takeaways | PASS 0.95 |

## Run level
- Stopping stage: intake 0.55, reproduce 0.16, profile 0.03, seal 0.05, propose 0.08, implement 0.06, evaluate 0.03; end-to-end PASS 0.04.
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- run_box_usd: 0.05 to 0.5 at an intake stop, 0.5 to 2.5 if it stops in reproduce to propose, 2 to 8 beyond.

## What would change my mind
- Intake FAIL with `found` false again and no blocker: the hint path, not evidence access, is the bottleneck. The fix is the hint itself or the search budget, not the gate.
- Intake FAIL with only a `licence` blocker: OpenMM's licence (MIT/LGPL) is public, so this would mean licence evidence is unreachable to the agent. That would also bear on blind-01 run1's H2.
- Intake PASS on the energy-drift study: the hint is satisfiable as written, and later stages meet a fixed-work ensemble like the positive control's.
