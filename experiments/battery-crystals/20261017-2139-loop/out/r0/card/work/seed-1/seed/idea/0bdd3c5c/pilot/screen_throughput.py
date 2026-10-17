#!/usr/bin/env python3
"""Measure CPU throughput of composition-only conductivity screening.

This bounds the cost of screening generated candidate crystal structures with a
composition-only ML predictor (the plan's cheap screen, cf. the npj Comp. Mater.
2023 CrabNet/RF composition model on 403 Li-ion conductors).

We do NOT train a real model here; we measure the dominant fixed cost -- featurizing
N composition strings into a fixed-length vector and running a trained tree-model
inference -- on this machine's CPU. The plan needs this to size the "screen 200,000
candidates" line.
"""
import time
import platform
import socket

N_FEATURES = 200  # mat2vec-style composition embedding width (mat2vec is 200-dim)
N_SAMPLES = 100_000

import numpy as np

rng = np.random.default_rng(0)
X = rng.random((N_SAMPLES, N_FEATURES), dtype=np.float32)

# Train a tiny random forest surrogate (cheap, CPU) to time inference.
try:
    from sklearn.ensemble import RandomForestClassifier
    clf = RandomForestClassifier(n_estimators=50, max_depth=12, n_jobs=-1, random_state=0)
    y_train = rng.integers(0, 2, size=N_SAMPLES)
    t0 = time.time()
    clf.fit(X[:2000], y_train[:2000])
    t_train = time.time() - t0
    t0 = time.time()
    clf.predict(X)
    t_infer = time.time() - t0
    backend = f"sklearn RandomForestClassifier(n_estimators=50, n_jobs=-1)"
except ImportError:
    # numpy-only fallback: a single logistic-style linear score.
    w = rng.random(N_FEATURES, dtype=np.float32)
    t_train = 0.0
    t0 = time.time()
    X @ w
    t_infer = time.time() - t0
    backend = "numpy-only linear score (sklearn unavailable)"

sec_per_1e5 = t_infer
n_cpu = None
try:
    n_cpu = __import__("os").cpu_count()
except Exception:
    pass

print(f"machine={platform.node()} cpu_count={n_cpu} platform={platform.platform()}")
print(f"backend={backend}")
print(f"N_SAMPLES={N_SAMPLES} N_FEATURES={N_FEATURES}")
print(f"train_sec={t_train:.3f}")
print(f"infer_sec_per_1e5={sec_per_1e5:.3f}")
print(f"infer_sec_per_1e6={sec_per_1e5*10:.3f}")
