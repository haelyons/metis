# Sealed predictions, measure run m1 (written 2026-10-20 01:5x UTC, before any agent or box ran)

Author: the operating session (Claude). Not shown to the triage, gate, build or post agents. Hash in out/SEALS.txt.

| # | Prediction | Probability |
|---|---|---|
| P1 | E1: airGR on the box reproduces NSE 0.495 within +/-0.02 on the 59-day period | 0.85 |
| P2 | E2: the JAX GR4J matches airGR daily flow within 1% MARE and NSE within +/-0.02 | 0.75 |
| P3 | E3: batched_forward_ms at 2,684 chains is above 6 ms (card guess of 2 ms off by more than 3x). Point estimate 60 ms, range 20 to 200 ms | 0.85 |
| P4 | GPU/CPU speedup (cpu_671_hours / main_run_hours) is below 5 | 0.70 |
| P4b | speedup is at least 20 | 0.05 |
| P5 | measured overhead_gpu is below the card's 4 (between 1.5 and 3) | 0.60 |
| P6 | E5 resolves if_not (card's expected outcome holds) | 0.90 |
| P7 | E6: main_run_hours above 6 h, so the card's own gate says "Stop and replan" | 0.55 |
| P8 | E7: throughput ratio 2,684/268 within 20% of 10 (time per pass nearly flat in chains) | 0.70 |
| P9 | The run completes its first launch with no halt (installs, harness, launcher) | 0.50 |

## Reasoning, in one paragraph

GR4J is a 7,300-step recurrence. On a GPU a scan runs one small kernel per day-step; the cost per step is latency,
not arithmetic, so the pass time is set by step count, roughly 5 to 25 microseconds per step, and barely moves with
the number of chains until the GPU saturates. The card's 2 ms assumes a throughput-bound workload. The CPU scan pays a
similar per-step cost, so the GPU/CPU ratio is small. If this holds, the card's if_not is right for a reason the card
did not give: both arms are bound by the sequential depth of the recurrence, which is exactly the sequential part a
parallel-in-time restructure would attack. That is the reshape-test's question, measured.

## What would change my mind

P3 fails if XLA fuses the scan body well enough to reach about 1 microsecond per step on the GPU. P1 fails if
CreateRunOptions' default warm-up or initial states differ from what the page's output implies. P9 is a coin flip:
`pip install jax[cuda12]` on the Lambda image and `apt install r-base-core` each have a real failure rate.
