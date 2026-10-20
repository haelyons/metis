"""Pilot: GR4J forward + batched multi-chain Metropolis throughput.

Run under `timeout 300` on the local 4-core CPU (dev), then on the A6000
(Lambda, JAX CUDA backend) to measure `batched_forward_ms` and
`cpu_671_hours`. This is the script referenced by phase gpu_bench.

Not run here (no exec in this environment): numbers that depend on its output
are basis GUESS with measured_by=gpu_bench.
"""
import time
import numpy as np

try:
    import jax
    import jax.numpy as jnp
    HAS_JAX = True
except Exception:
    HAS_JAX = False


def gr4j_scan(params, precip, pet):
    """Vectorized GR4J over a batch of catchments (params: [B,4]).
    Returns daily streamflow [B,T]. Serial scan over T days; batched over B.
    Production store (S) and routing store (R) are the only recurrences.
    Unit hydrographs are applied via convolution over the full series.
    """
    B = params.shape[0]
    T = precip.shape[1]
    x1 = params[:, 0]
    x2 = params[:, 1]
    x3 = params[:, 2]
    x4 = params[:, 3]

    # UH1 time base x4 days, UH2 time base 2*x4 days (S-curve, standard GR4J)
    x4b = np.maximum(x4, 0.5)
    uh1 = _uh_ordinates(x4b)
    uh2 = _uh_ordinates(2.0 * x4b)

    S = 0.3 * x1          # initial production store
    R = 0.5 * x3          # initial routing store
    Pr = np.zeros_like(precip)
    for t in range(T):
        P = precip[:, t]
        E = pet[:, t]
        Pn = np.maximum(0.0, P - E)
        En = np.maximum(0.0, E - P)
        Ps = np.where(
            Pn > 0,
            x1 * (1.0 - (S / x1) ** 2) * np.tanh(Pn / x1) / (1.0 + (S / x1) * np.tanh(Pn / x1)),
            0.0,
        )
        Es = np.where(
            En > 0,
            S * (2.0 - S / x1) * np.tanh(En / x1) / (1.0 + (1.0 - S / x1) * np.tanh(En / x1)),
            0.0,
        )
        S = S - Es + Ps
        Perc = S * (1.0 - (1.0 + (4.0 * S / (9.0 * x1)) ** 4.0) ** -0.25)
        S = S - Perc
        Pr[:, t] = Perc + Pn - Ps

    Q9 = 0.9 * _conv_series(Pr, uh1) + 0.1 * _conv_series(Pr, uh2)
    Q = np.zeros_like(precip)
    for t in range(T):
        F = x2 * (R / x3) ** 3.5
        R = np.maximum(0.0, R + Q9[:, t] + F)
        Qr = R * (1.0 - (1.0 + (R / x3) ** 4.0) ** -0.25)
        R = R - Qr
        Qd = np.maximum(0.0, Q9[:, t] + F)
        Q[:, t] = Qr + Qd
    return Q


def _uh_ordinates(x4):
    # continuous S-curve unit hydrograph ordinates, max 100 days
    nh = 100
    t = np.arange(1, nh + 1).astype(float)
    sh1 = np.where(t <= 0, 0.0, np.where(t < x4, (t / x4) ** 2.5, 1.0))
    sh1 = np.where(t <= 0, 0.0, np.where(t < x4, (t / x4) ** 2.5, 1.0))
    uh = sh1[1:] - sh1[:-1]
    return uh


def _conv_series(pr, uh):
    B, T = pr.shape
    out = np.zeros_like(pr)
    n = min(uh.shape[1] if uh.ndim == 2 else uh.shape[0], T)
    for k in range(n):
        w = uh[:, k] if uh.ndim == 2 else uh[k]
        out[:, k:] += pr[:, : T - k] * w[:, None] if uh.ndim == 2 else pr[:, : T - k] * w
    return out


def main():
    rng = np.random.default_rng(0)
    B = 2684           # 671 catchments x 4 chains
    T = 7300           # 20 years daily
    precip = rng.uniform(0, 50, (B, T))
    pet = rng.uniform(0, 8, (B, T))
    params = rng.uniform(1, 1000, (B, 4))

    # warm-up
    gr4j_scan(params[:8], precip[:8], pet[:8])

    # single forward pass timing (batched over all B)
    t0 = time.time()
    gr4j_scan(params, precip, pet)
    dt_batch = time.time() - t0
    print(f"batched_forward_ms (B={B}, T={T}) = {dt_batch*1000:.3f}")

    # single-catchment forward pass timing
    t0 = time.time()
    for _ in range(10):
        gr4j_scan(params[:1], precip[:1], pet[:1])
    dt_one = (time.time() - t0) / 10
    print(f"single_forward_ms (B=1) = {dt_one*1000:.3f}")


if __name__ == "__main__":
    main()
