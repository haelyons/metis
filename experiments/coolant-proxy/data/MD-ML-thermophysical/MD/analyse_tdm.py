#!/usr/bin/env python
"""Green-Kubo analysis of the production output: viscosity, thermal conductivity, density.

    python analyse_tdm.py runs/cyclohexylnonane --system-dir systems/cyclohexylnonane -T 313.15

Expects the per-replica directories written by lammps/tdm.in and tdm_continue.in:

    runs/<mol>/run_<i>/Stress_perstep_T<T>K_run<i>_seg<s>.out
    runs/<mol>/run_<i>/HeatFlux_perstep_T<T>K_run<i>_seg<s>.out
    runs/<mol>/run_<i>/volume_T<T>K_run<i>.txt

Method, as in the paper: viscosity is the running Green-Kubo integral of the Maginn
combination of the pressure-tensor autocorrelations, averaged over replicas, cut where
the relative spread sigma/mean exceeds 0.4, and extrapolated with a weighted
double-exponential fit of the integral; its uncertainty is a bootstrap over replicas.
Thermal conductivity is the running integral of the heat-flux autocorrelation read over
a 10 ps window starting where the normalised ACF has decayed into its noise floor,
mean +- std over replicas. Density follows from the fixed NVT box.
"""
import argparse, json, os
import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import curve_fit

KB = 1.3806504e-23
ATM2PA = 101325.0
A2M = 1.0e-10
FS2S = 1.0e-15
KCAL2J = 4186.0 / 6.02214e23
NA = 6.02214076e23
CONVERT_VISC = ATM2PA**2 * FS2S * A2M**3 * 1.0e3   # <P P>[atm^2] V[A^3] dt[fs] -> mPa s
CONVERT_TC = KCAL2J**2 / FS2S / A2M                # <J J> dt -> W/(m K), with /(kB T^2 V)


# ---- reading the deck outputs -------------------------------------------------

def read_run(rdir, prefix, T, rid, ncol):
    """Concatenate the per-segment series for one replica, in segment order."""
    segs = []
    for f in os.listdir(rdir):
        if f.startswith(f"{prefix}_T{T}K_run{rid}_seg") and f.endswith(".out"):
            segs.append((int(f.split("_seg")[-1].split(".")[0]), os.path.join(rdir, f)))
    parts = []
    for s, path in sorted(segs):
        d = pd.read_csv(path, sep=r"\s+", comment="#", header=None, engine="c",
                        on_bad_lines="skip")
        a = d.apply(pd.to_numeric, errors="coerce").dropna().to_numpy()[:, 1:1 + ncol]
        parts.append(a[1:] if s > 1 else a)   # drop the boundary step segments share
    return np.vstack(parts) if parts else None


def system_mass_amu(in_data):
    lines = open(in_data).read().splitlines()
    masses, i = {}, next(k for k, l in enumerate(lines) if l.strip() == "Masses")
    for l in lines[i + 2:]:
        if not l.strip():
            if masses:
                break
            continue
        p = l.split(); masses[int(p[0])] = float(p[1])
    j = next(k for k, l in enumerate(lines) if l.strip().startswith("Atoms"))
    tot = 0.0
    for l in lines[j + 2:]:
        if not l.strip():
            if tot > 0:
                break
            continue
        p = l.split()
        if len(p) >= 3:
            tot += masses[int(p[2])]
    return tot


# ---- autocorrelations ---------------------------------------------------------

def acf(x):
    n = len(x)
    xm = x - x.mean()
    f = np.fft.rfft(xm, n=2 * n)
    return np.fft.irfft(f * np.conj(f))[:n] / np.arange(n, 0, -1)


def stress_acf(P):
    """Maginn combination of the six pressure-tensor autocorrelations."""
    Pxx, Pyy, Pzz, Pxy, Pxz, Pyz = P.T
    return (acf(Pxy) + acf(Pxz) + acf(Pyz)) / 6.0 \
        + (acf(Pxx - Pyy) + acf(Pyy - Pzz) + acf(Pxx - Pzz)) / 24.0


def flux_acf(J):
    return (acf(J[:, 0]) + acf(J[:, 1]) + acf(J[:, 2])) / 3.0


# ---- viscosity: sigma/mean cutoff + double-exponential fit --------------------

def de_integral(t, A, alpha, tau1, tau2):
    return A * (alpha * tau1 * (1 - np.exp(-t / tau1)) +
                (1 - alpha) * tau2 * (1 - np.exp(-t / tau2)))


def fit_eta(t_ps, mean):
    tail = mean[t_ps > 0.3 * t_ps.max()]
    plateau = np.nanmax(tail) if tail.size else np.nanmax(mean)
    p0 = [plateau / 100.0, 0.5, 5.0, 100.0]
    bounds = ([0, 0, 0.5, 5.0], [3 * plateau, 1, 200.0, 5000.0])
    w = 1.0 / np.sqrt(np.clip(t_ps, 1.0, None))
    try:
        popt, _ = curve_fit(de_integral, t_ps, mean, p0=p0, bounds=bounds,
                            sigma=1.0 / w, maxfev=200000)
    except Exception:
        return plateau
    A, al, t1, t2 = popt
    return A * (al * t1 + (1 - al) * t2)


def cut_index(t_ps, mean, sd):
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(np.abs(mean) > 0, sd / np.abs(mean), 0.0)
    idx = np.where((t_ps > 20) & (ratio > 0.4))[0]
    return idx[0] if len(idx) else len(t_ps) - 1


def eta_from_runs(eta_r, t_ps, nboot=200, seed=1):
    cut = cut_index(t_ps, eta_r.mean(0), eta_r.std(0))
    eta = fit_eta(t_ps[:cut + 1], eta_r.mean(0)[:cut + 1])
    rng = np.random.default_rng(seed)
    n = eta_r.shape[0]
    boots = []
    for _ in range(nboot):
        s = eta_r[rng.integers(0, n, n)]
        c = cut_index(t_ps, s.mean(0), s.std(0, ddof=1))
        boots.append(fit_eta(t_ps[:c + 1], s.mean(0)[:c + 1]))
    boots = np.array(boots)
    return eta, float(boots[np.isfinite(boots)].std())


# ---- thermal conductivity: ACF-death window read ------------------------------

def kappa_from_run(C, kap, t_ps, dt_ps):
    norm = C / C[0]
    lo, hi = np.searchsorted(t_ps, 30.0), np.searchsorted(t_ps, 330.0)
    floor = np.std(norm[lo:hi])
    k = max(1, int(round(1.0 / dt_ps)))
    sm = np.convolve(np.abs(norm), np.ones(k) / k, mode="same")
    below = sm < 2 * floor
    five = int(round(5.0 / dt_ps))
    death = next((i for i in range(1, len(below) - five) if below[i:i + five].all()),
                 np.searchsorted(t_ps, 10.0))
    return np.mean(kap[death:death + int(round(10.0 / dt_ps))])


# ---- main ---------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir", help="directory containing run_<i>/ replica outputs")
    ap.add_argument("--system-dir", required=True, help="builder output with in.data")
    ap.add_argument("-T", default="313.15", help="temperature as it appears in filenames")
    ap.add_argument("--dump-fs", type=float, default=5.0,
                    help="fs between samples (timestep x dump_every of the decks)")
    ap.add_argument("--lag-cap-ps", type=float, default=2000.0,
                    help="maximum ACF lag used for the integrals")
    a = ap.parse_args()
    Tk, dt = float(a.T), a.dump_fs
    dt_ps = dt / 1000.0
    cap = int(a.lag_cap_ps / dt_ps)

    rids = sorted(int(d.split("_")[1]) for d in os.listdir(a.runs_dir)
                  if d.startswith("run_") and os.path.isdir(os.path.join(a.runs_dir, d)))
    eta_runs, kap_vals, vols = [], [], []
    for r in rids:
        rdir = os.path.join(a.runs_dir, f"run_{r}")
        S = read_run(rdir, "Stress_perstep", a.T, r, 6)
        J = read_run(rdir, "HeatFlux_perstep", a.T, r, 3)
        if S is None or J is None:
            print(f"run {r}: skipped (missing output)")
            continue
        V = float(np.loadtxt(os.path.join(rdir, f"volume_T{a.T}K_run{r}.txt")))
        vols.append(V)
        print(f"run {r}: {len(S)} samples ({len(S) * dt / 1e6:.2f} ns), V = {V:.0f} A^3")
        CP = stress_acf(S)[:cap]
        eta_runs.append(cumulative_trapezoid(CP, dx=dt, initial=0.0)
                        * V * CONVERT_VISC / (KB * Tk))
        CJ = flux_acf(J)[:cap]
        kap = cumulative_trapezoid(CJ, dx=dt, initial=0.0) * CONVERT_TC / (KB * Tk * Tk * V)
        t_ps = np.arange(len(CJ)) * dt_ps
        kap_vals.append(kappa_from_run(CJ, kap, t_ps, dt_ps))
    if len(eta_runs) < 2:
        raise SystemExit("need at least two replicas")

    n = min(map(len, eta_runs))
    eta_r = np.array([e[:n] for e in eta_runs])
    t_ps = np.arange(n) * dt_ps
    eta, eta_unc = eta_from_runs(eta_r, t_ps)
    kap_vals = np.array(kap_vals)
    mass = system_mass_amu(os.path.join(a.system_dir, "in.data"))
    rho = float(np.mean([mass / NA / (V * 1e-24) for V in vols]))

    print(f"\nT = {Tk} K, {len(eta_r)} replicas")
    print(f"eta   = {eta:.2f} +/- {eta_unc:.2f} mPa s")
    print(f"kappa = {kap_vals.mean():.3f} +/- {kap_vals.std():.3f} W/(m K)")
    print(f"rho   = {rho:.3f} g/cm^3")
    json.dump(dict(T_K=Tk, n_replicas=len(eta_r), eta_mPa_s=eta, eta_unc=eta_unc,
                   kappa_W_mK=kap_vals.mean(), kappa_unc=kap_vals.std(), rho_g_cm3=rho),
              open(os.path.join(a.runs_dir, f"results_T{a.T}K.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
