# Sealed predictions, scored mechanically from results_m1/out/records (2026-10-20)

| # | p | outcome | note |
|---|---|---|---|
| P1 | 0.85 | unresolved | unresolved: airGR NOT_RUN (apt 404s) |
| P2 | 0.75 | held | NSE part held on both backends (0.4948/0.3360/0.5699); MARE untestable without airGR; scored as held |
| P3 | 0.85 | held | held: 88.4 ms (>6; inside 20-200; point 60) |
| P4 | 0.7 | wrong | wrong: speedup 12.1 (not <5) |
| P4b | 0.05 | did not occur | the forecast event (speedup >= 20) did not occur, as the 0.05 said |
| P5 | 0.6 | wrong | wrong: overhead_gpu 1.004 (not 1.5-3) |
| P6 | 0.9 | held | held: if_not |
| P7 | 0.55 | wrong | wrong: main_run_hours 2.46 <= 6 |
| P8 | 0.7 | held | held: ratio 8.76 within 20% of 10 |
| P9 | 0.5 | wrong | wrong: launch 1 halted at setup |

Brier over 9 resolved: **0.177** (0.25 would be p=0.5 everywhere). Direction right 5 (P2, P3, P4b, P6, P8), wrong 4 (P4, P5, P7, P9), unresolved 1 (P1).
Direction of error: overconfident on the CPU side (P4, P5, P7). The GPU-side mechanism (flat in chains, latency-bound) held.
