#!/usr/bin/env python3
"""Pilot: verify that scalar parallel cyclic reduction (PCR) and the sequential
Thomas algorithm both solve a diagonally-dominant tridiagonal system to the same
answer as numpy.linalg.solve, and time both on CPU to get a rough work ratio.

This is the CPU/numpy reference for the GPU CUDA kernels that will be built on
Lambda.  It proves the PCR recurrence is implemented correctly (same x as an
exact dense solve) before any GPU money is spent.
"""
import time
import numpy as np


def thomas(a, b, c, d):
    """Sequential Thomas algorithm (forward elimination + back substitution)."""
    n = len(b)
    cp = np.zeros(n - 1)
    dp = np.zeros(n)
    cp[0] = c[0] / b[0]
    dp[0] = d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i - 1] * cp[i - 1]
        if i < n - 1:
            cp[i] = c[i] / m
        dp[i] = (d[i] - a[i - 1] * dp[i - 1]) / m
    x = np.zeros(n)
    x[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x


def pcr(a, b, c, d):
    """Parallel cyclic reduction: after log2(n) rounds each row is independent.
    Row i: a[i] x[i-1] + b[i] x[i] + c[i] x[i+1] = d[i], with a[0]=c[n-1]=0.
    """
    n = len(b)
    aa = a.astype(np.float64).copy()
    bb = b.astype(np.float64).copy()
    cc = c.astype(np.float64).copy()
    dd = d.astype(np.float64).copy()
    stride = 1
    rounds = int(np.ceil(np.log2(n)))
    for _ in range(rounds):
        # neighbours at distance `stride`
        i = np.arange(n)
        left = np.maximum(i - stride, 0)
        right = np.minimum(i + stride, n - 1)
        alpha = np.zeros(n)
        gamma = np.zeros(n)
        # avoid divide by zero on inactive rows (use eps where neighbour is self)
        bl = bb[left]
        br = bb[right]
        bl = np.where(left == i, 1.0, bl)
        br = np.where(right == i, 1.0, br)
        alpha = np.where(left == i, 0.0, aa[i] / bl)
        gamma = np.where(right == i, 0.0, cc[i] / br)
        new_a = -alpha * aa[left]
        new_c = -gamma * cc[right]
        new_b = bb[i] - alpha * cc[left] - gamma * aa[right]
        new_d = dd[i] - alpha * dd[left] - gamma * dd[right]
        aa, bb, cc, dd = new_a, new_b, new_c, new_d
        stride *= 2
    return dd / bb


def diag_dominant(n, rng):
    """Build a random diagonally dominant tridiagonal system (Thomas-stable)."""
    a = rng.uniform(-1.0, 1.0, n)
    c = rng.uniform(-1.0, 1.0, n)
    a[0] = 0.0
    c[-1] = 0.0
    b = np.abs(a) + np.abs(c) + 1.0 + rng.uniform(0.0, 1.0, n)
    d = rng.uniform(-1.0, 1.0, n)
    return a, b, c, d


def main():
    rng = np.random.default_rng(0)
    print("N        max|thomas-ref|  max|pcr-ref|  rel")
    for n in [2 ** 10, 2 ** 14, 2 ** 18, 2 ** 20]:
        a, b, c, d = diag_dominant(n, rng)
        # dense reference
        A = np.zeros((n, n))
        A[np.arange(n), np.arange(n)] = b
        A[np.arange(1, n), np.arange(n - 1)] = a[1:]
        A[np.arange(n - 1), np.arange(1, n)] = c[:-1]
        ref = np.linalg.solve(A, d)
        xt = thomas(a, b, c, d)
        xp = pcr(a, b, c, d)
        et = np.max(np.abs(xt - ref))
        ep = np.max(np.abs(xp - ref))
        scale = np.max(np.abs(ref))
        print(f"{n:<9} {et:>15.3e}  {ep:>12.3e}  {ep / scale:.3e}")

    # rough CPU timing at one size (work ratio proxy only; GPU numbers come later)
    n = 2 ** 16
    a, b, c, d = diag_dominant(n, rng)
    t0 = time.perf_counter()
    xt = thomas(a, b, c, d)
    t_th = time.perf_counter() - t0
    t0 = time.perf_counter()
    xp = pcr(a, b, c, d)
    t_pc = time.perf_counter() - t0
    agree = np.max(np.abs(xt - xp))
    print(f"CPU timing N=2^16: thomas={t_th:.4f}s pcr={t_pc:.4f}s "
          f"pcr/thomas={t_pc / t_th:.2f}x max|thomas-pcr|={agree:.3e}")


if __name__ == "__main__":
    main()
