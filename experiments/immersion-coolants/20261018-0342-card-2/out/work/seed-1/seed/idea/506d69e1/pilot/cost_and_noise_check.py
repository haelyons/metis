#!/usr/bin/env python3
"""Phase-1 (p_local) check code for plan IC-V1.

Run on the shared local machine before any Lambda spend:

    timeout 600 python3 cost_and_noise_check.py > cost_and_noise_check.out

Part A: cost arithmetic of the Lambda lines (must match the record's total_stated).
Part B: synthetic Green-Kubo replicate noise, to validate the decision and noise
rules (replica averaging 1/sqrt(n), bootstrap coverage, false-positive rate of
calling a rank-correlation improvement when there is none).

No GPU is needed. Numerical results must be pasted into the record only after
this script is actually executed (basis MEASURED).
"""
import math
import random

# ---- Part A: cost arithmetic (numbers as in the plan record) ----
throughput_ns_day = 250.0      # PROXY, measured in phase p_bench
n_gpus = 8
a100x8_usd_gpu_h = 1.99
a6000_usd_gpu_h = 1.09
n_replicas = 6
t_eq_ns = 2.0
t_prod_ns = 5.0
ns_per_mol = t_eq_ns + n_replicas * t_prod_ns
n_mol_core = 48
n_mol_total = 120
n_mol_ext = n_mol_total - n_mol_core
pilot_ns = 150.0
gib_store = 150.0
fs_usd_gib_month = 0.2
rerun_usd = 120.0

gpu_h_per_mol = 24.0 * ns_per_mol / throughput_ns_day
mol_usd = gpu_h_per_mol * a100x8_usd_gpu_h


def wall_hours(ns_total):
    return math.ceil(24.0 * ns_total / (throughput_ns_day * n_gpus))


lines = [
    ("l_dry", 4 * a6000_usd_gpu_h),
    ("l_bench", wall_hours(pilot_ns) * n_gpus * a100x8_usd_gpu_h),
    ("l_core", wall_hours(n_mol_core * ns_per_mol) * n_gpus * a100x8_usd_gpu_h),
    ("l_ext", wall_hours(n_mol_ext * ns_per_mol) * n_gpus * a100x8_usd_gpu_h),
    ("l_score", 6 * a6000_usd_gpu_h),
    ("l_store", gib_store * fs_usd_gib_month),
    ("l_rerun", rerun_usd),
]
total = sum(v for _, v in lines)
print("PART_A")
print(f"ns_per_mol {ns_per_mol:.1f}")
print(f"gpu_h_per_mol {gpu_h_per_mol:.3f}")
print(f"mol_usd {mol_usd:.4f}")
print(f"bench_wall_h {wall_hours(pilot_ns)}")
print(f"core_wall_h {wall_hours(n_mol_core * ns_per_mol)}")
print(f"ext_wall_h {wall_hours(n_mol_ext * ns_per_mol)}")
for name, usd in lines:
    print(f"{name}_usd {usd:.2f}")
print(f"total_usd {total:.2f}")

# ---- Part B: synthetic Green-Kubo noise / decision-rule check ----
random.seed(20261018)

TRUE_ETA = [1.0 + 9.0 * (i / 59.0) ** 1.5 for i in range(60)]  # 1..10 mPa.s
CV = 0.25  # per-replica relative noise of a 5 ns Green-Kubo integral


def replicate_mean(n_rep):
    return [t * random.lognormvariate(0.0, math.sqrt(math.log(1 + CV * CV))) **
            1.0 if n_rep == 1 else
            t * math.exp(sum(math.log(random.lognormvariate(
                0.0, math.sqrt(math.log(1 + CV * CV)))) for _ in range(n_rep)) / n_rep)
            for t in TRUE_ETA]


def spearman(a, b):
    ra = [sorted(range(len(a)), key=lambda i: a[i]).index(i) for i in range(len(a))]
    rb = [sorted(range(len(b)), key=lambda i: b[i]).index(i) for i in range(len(b))]
    n = len(a)
    d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
    return 1 - 6 * d2 / (n * (n * n - 1))


def mape(pred, true):
    return sum(abs(p - t) / t for p, t in zip(pred, true)) / len(true)


s1 = [replicate_mean(1)[i] for i in range(60)]
s6 = [replicate_mean(6)[i] for i in range(60)]
# per-molecule standard error estimate: spread of 8 synthetic single replicas
se1 = [abs(replicate_mean(1)[i] - TRUE_ETA[i]) / TRUE_ETA[i] for i in range(60)]
se6 = [abs(s6[i] - TRUE_ETA[i]) / TRUE_ETA[i] for i in range(60)]
mean = lambda xs: sum(xs) / len(xs)
print("PART_B")
print(f"se_ratio_6_to_1 {mean(se6) / mean(se1):.3f}")  # expect ~ 1/sqrt(6) = 0.408
print(f"mape_nrep1 {mean(se1):.3f}")
print(f"mape_nrep6 {mean(se6):.3f}")
print(f"spearman_nrep6 {spearman(s6, TRUE_ETA):.3f}")

# false-positive rate: call a 'rank improvement' when a constant 1.25x bias is
# corrected with no real change in ordering (null: rho unchanged)
fp = 0
trials = 2000
for _ in range(trials):
    biased = [t * 1.25 for t in TRUE_ETA]
    noisy = [biased[i] * random.lognormvariate(0.0, 0.05) for i in range(60)]
    if spearman(noisy, TRUE_ETA) > 0.90:  # would be called 'trustworthy ranking'
        fp += 1
print(f"fp_rate {fp / trials:.3f}")  # under a pure scale bias rho stays ~1; must not decide alone
print(f"trials {trials}")
