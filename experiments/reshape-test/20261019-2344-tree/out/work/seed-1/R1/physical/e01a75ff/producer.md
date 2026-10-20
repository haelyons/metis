# Cyclic reduction (PCR): does GPU width shorten the tridiagonal Newton solve?

## What this is

The option claims the "cheap sequential part" of parallel-in-time methods — the
block-bidiagonal Newton correction, a tridiagonal/bidiagonal solve — drops from
O(T) to O(log T) depth under N-fold parallel cyclic reduction (PCR). This plan
builds that solve on a Lambda A100, times a sequential baseline against PCR,
and checks both are right, so the claim stops being a slide and becomes a number.

## What to build

Three CUDA solvers + one reference, all on one A100 SXM 40GB:

1. **Thomas** — sequential forward elimination + back substitution, one thread
   per system. This is the O(T) baseline. Thomas is "inherently sequential" and
   O(n) work (https://en.wikipedia.org/wiki/Tridiagonal_matrix_algorithm).
2. **PCR** — parallel cyclic reduction: each round every row combines with its
   two neighbours at distance `stride`, halving the system each round, so
   log2(T) rounds of full N-way parallelism replace T ordered steps. NVIDIA's
   own docs say PCR "is more computationally expensive but parallelizable"
   (https://docs.nvidia.com/cuda/cusolverdx/get_started/functions/gtsv.html).
3. **Batched Thomas** — K independent systems solved concurrently (one thread
   block each). This is the width control: it shows that running many
   independent solves at once does NOT shorten one system's latency, which is
   exactly what PCR is claimed to do.
4. **Reference** — cuSPARSE `gtsv2_nopivot` (NVIDIA's own hybrid PCR+Thomas) and
   `scipy.linalg.solve_banded` on the instance CPU, to score correctness.

A numpy reference for the exact recurrences already lives in
`pilot/pcr_thomas_check.py`; the CUDA kernels are ports of it.

## How to check it is right

- On diagonally dominant systems, both Thomas and PCR must match cuSPARSE
  `gtsv2_nopivot` and scipy's dense/banded solve to a relative residual below
  1e-10. Diagonally dominant is the regime where Thomas is stable
  (https://en.wikipedia.org/wiki/Tridiagonal_matrix_algorithm).
- If residual > 1e-10, fix the kernels before spending anything on the sweep
  (gate on the anchor phase).

## The measurement (does width shorten the sequential part)

Sweep the number of equations N over {2^10, 2^14, 2^18, 2^22, 2^24}, 5 repeats
each, median wall-clock. Lever if PCR beats Thomas by >= 2x at N = 2^24 and the
ratio grows with N (log vs linear). Prior: Zhang, Cohen, Owens measured PCR
"fewer algorithmic steps but do more work each step" and "up to a 28x speedup
over a sequential LAPACK solver" on a 2009 GTX 280
(https://research.nvidia.com/sites/default/files/pubs/2010-01_Fast-Tridiagonal-Solvers/Zhang_Fast_2009.pdf).

The on-device parallelism that must feed PCR's ~T threads is 108 SMs / 6912
FP32 cores, 1555 GB/s (https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/nvidia-ampere-architecture-whitepaper.pdf),
so for N far above ~2^21 in-flight threads PCR runs in waves — the sweep
measures where that bites.

## Cost

Rate: A100 SXM 40GB, $1.99/GPU/hr (Lambda, 1x and 8x tabs —
https://lambda.ai/pricing). All dollar figures use this rate.

- Anchor + full scalar sweep, 1 GPU, 6 h time box (need ~2 h): 6 * $1.99 = $11.94
- Block-tridiagonal stretch (d = 4, 16), 1 GPU, 4 h (need ~2 h): $7.96 (optional)
- 2- and 8-GPU PCR stretch, 8 GPU, 2 h (need ~1 h): 2 * 8 * $1.99 = $31.84 (optional)

Total stated: $51.74. Hard stop: $1,000. Storage is negligible (a few MB of CSV
on the instance SSD; the billed filesystem is $0.20/GiB/month and is not needed).

## What this cannot show

It times the solve in isolation, not the full Parareal/MGRIT Newton loop: the
iteration count k is set by the dynamics' forgetting rate, which this plan does
not touch. Wiring PCR into a real MGRIT loop on a dissipative PDE at T = 2^26 is
the full-scale run this budget does not buy.
