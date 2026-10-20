#!/usr/bin/env python3
"""
compose_check.py -- pilot sanity check for the "linear feature representation ->
parallel-in-time for free" plan.

Two independent checks, run on the local 4-core machine (free) before any Lambda spend:

1. composition_check: on a synthetic LINEAR system x_{t+1} = A x_t, verify that
   repeated squaring (A, A^2, A^4, ... A^T) applied to x0 gives the SAME x_T as
   T sequential matvecs. This is the math behind the framer's ParaDiag exception:
   x_T = A^T x_0 is computable in O(log T) depth by repeated squaring.

2. ls_fit_benchmark: time a least-squares fit of a d-by-d linear transition from
   N samples (normal equations), reporting effective CPU GFLOPS. This anchors the
   per-layer linear-transition fit cost that dominates the regression stage.
"""
import time
import numpy as np


def composition_check(d=512, T=1024, seed=0):
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((d, d)) / (np.sqrt(d) * 1.5)  # stable-ish linear map
    x0 = rng.standard_normal(d)

    # sequential: T matvecs
    x = x0.copy()
    for _ in range(T):
        x = A @ x
    xT_seq = x

    # repeated squaring: B = A^(2^k)
    B = A.copy()
    p = 1
    while p < T:
        B = B @ B
        p *= 2
    xT_sq = B @ x0

    err = float(np.max(np.abs(xT_sq - xT_seq)))
    print(f"composition_check: d={d} T={T} max_abs_error={err:.3e}")
    return err


def ls_fit_benchmark(d=1024, N=4096, seed=1):
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((N, d))
    A_true = rng.standard_normal((d, d)) / np.sqrt(d)
    Y = X @ A_true.T + 0.01 * rng.standard_normal((N, d))

    t0 = time.time()
    XtX = X.T @ X                         # 2*N*d*d FLOP
    XtY = X.T @ Y                         # 2*N*d*d FLOP
    A_hat = np.linalg.solve(XtX, XtY).T   # ~ (2/3)*d^3 FLOP
    dt = time.time() - t0

    flops = 4 * N * d * d + (2.0 / 3.0) * d ** 3
    gflops = flops / dt / 1e9
    print(f"ls_fit_benchmark: d={d} N={N} seconds={dt:.2f} gflops={gflops:.1f}")
    return dt, gflops


if __name__ == "__main__":
    composition_check()
    ls_fit_benchmark()
