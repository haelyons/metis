#!/usr/bin/env python3
"""Pilot for the AAV capsid-receptor -> transcytosis plan.

Measures, on the local shared 4-core host only:
  1. n_labels_pilot          rows in labels_pilot.csv (hand-transcribed open-literature labels)
  2. fingerprint_sec_per_pair  5 A contact-fingerprint kernel cost (CPU)
  3. cv_loco_sec               leave-one-group-out logistic CV cost on a synthetic panel
  4. acc_synthetic_*           code-path accuracy on synthetic data with a known signal
  5. random vs uncertainty panel selection accuracy (condition check code path)
  6. machine description

GPU structure-prediction time is NOT measured here (see numbers.sec_pair_seed, PROXY).
"""
import csv, math, os, platform, time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(0)


def log(msg):
    print(msg, flush=True)


def count_labels():
    path = os.path.join(HERE, "labels_pilot.csv")
    with open(path) as f:
        rows = list(csv.DictReader(f))
    n = len(rows)
    pos = sum(1 for r in rows if r["phenotype"] == "1")
    neg = n - pos
    log(f"n_labels_pilot={n}")
    log(f"n_labels_pilot_pos={pos}")
    log(f"n_labels_pilot_neg={neg}")
    return n, pos, neg


def fingerprint_kernel(n_pairs=200, n_cap=220, n_rec=150, cutoff=5.0):
    """Time a 5 A inter-chain contact fingerprint over synthetic coordinates."""
    t0 = time.perf_counter()
    contacts = 0
    for _ in range(n_pairs):
        cap = RNG.normal(scale=25.0, size=(n_cap, 3))
        rec = cap[:1].copy() + RNG.normal(scale=6.0, size=(n_rec, 3))
        d2 = ((cap[:, None, :] - rec[None, :, :]) ** 2).sum(-1)
        contacts += int((d2 < cutoff * cutoff).sum())
    dt = time.perf_counter() - t0
    per = dt / n_pairs
    log(f"fingerprint_sec_per_pair={per:.6f}")
    log(f"fingerprint_pairs={n_pairs} contacts_total={contacts}")
    return per


def make_synthetic(n=480, d_sig=40, d_seq=20, signal=1.2, seed=0):
    rng = np.random.default_rng(seed)
    sig = rng.normal(size=(n, d_sig))
    seq = rng.normal(size=(n, d_seq))
    w = rng.normal(size=d_sig)
    logits = signal * (sig @ w) / math.sqrt(d_sig)
    y = (logits + rng.normal(scale=0.6, size=n) > 0).astype(float)
    groups = rng.integers(0, 8, size=n)  # capsid families
    return sig, seq, y, groups


def logreg_fit_predict(Xtr, ytr, Xte, steps=400, lr=0.5, l2=1e-2):
    Xtr = np.hstack([Xtr, np.ones((len(Xtr), 1))])
    Xte = np.hstack([Xte, np.ones((len(Xte), 1))])
    w = np.zeros(Xtr.shape[1])
    for _ in range(steps):
        p = 1.0 / (1.0 + np.exp(-Xtr @ w))
        g = Xtr.T @ (p - ytr) / len(ytr) + l2 * w
        w -= lr * g
    return 1.0 / (1.0 + np.exp(-(Xte @ w)))


def bacc(y, p, thr=0.5):
    yhat = (p >= thr).astype(float)
    tpr = yhat[y == 1].mean() if (y == 1).any() else 0.0
    tnr = yhat[y == 0].mean() if (y == 0).any() else 0.0
    return 0.5 * (tpr + tnr)


def loco_cv(sig, seq, y, groups, seeds=5, use="sig"):
    accs, t0 = [], time.perf_counter()
    for s in range(seeds):
        rng = np.random.default_rng(s)
        order = np.arange(len(y))
        rng.shuffle(order)
        preds = np.zeros(len(y))
        for g in np.unique(groups):
            te = groups == g
            tr = ~te
            X = sig if use == "sig" else seq
            preds[te] = logreg_fit_predict(X[tr], y[tr], X[te], steps=200, lr=0.5)
        accs.append(bacc(y, preds))
    dt = time.perf_counter() - t0
    return float(np.mean(accs)), float(np.std(accs)), dt, accs


def panel_condition(sig, y, groups, panel=120, seeds=5):
    """Random vs uncertainty-ranked panel selection on synthetic labels."""
    out = {}
    for mode in ("random", "uncertainty"):
        accs = []
        for s in range(seeds):
            rng = np.random.default_rng(100 + s)
            idx = np.arange(len(y))
            if mode == "random":
                pick = rng.choice(idx, size=panel, replace=False)
            else:
                # crude uncertainty proxy: rank by |mean feature| near zero
                score = np.abs(sig.mean(1))
                pick = idx[np.argsort(score)[:panel]]
            preds = np.zeros(len(y))
            for g in np.unique(groups):
                te = groups == g
                tr = np.zeros(len(y), dtype=bool)
                tr[pick] = True
                tr[te] = False
                if tr.sum() < 10:
                    continue
                preds[te] = logreg_fit_predict(sig[tr], y[tr], sig[te], steps=200)
            accs.append(bacc(y, preds))
        out[mode] = (float(np.mean(accs)), float(np.std(accs)))
        log(f"panel_{mode}_acc={out[mode][0]:.3f} sd={out[mode][1]:.3f}")
    log(f"panel_delta_uncertainty_minus_random={out['uncertainty'][0]-out['random'][0]:+.3f}")
    return out


def main():
    log(f"machine={platform.platform()} cpus={os.cpu_count()} python={platform.python_version()}")
    count_labels()
    fingerprint_kernel()
    sig, seq, y, groups = make_synthetic()
    log(f"synthetic_n={len(y)} pos_rate={y.mean():.2f}")
    m, sd, dt, accs = loco_cv(sig, seq, y, groups, use="sig")
    log(f"acc_synthetic_signatures={m:.3f} sd={sd:.3f} seeds={len(accs)}")
    log(f"cv_loco_sec={dt:.3f}")
    m2, sd2, _, _ = loco_cv(sig, seq, y, groups, use="seq")
    log(f"acc_synthetic_seqonly={m2:.3f} sd={sd2:.3f}")
    # shuffled-signature negative control: break signature/label correspondence
    sig_sh = sig[RNG.permutation(len(sig))]
    m3, sd3, _, _ = loco_cv(sig_sh, seq, y, groups, use="sig")
    log(f"acc_synthetic_shuffled={m3:.3f} sd={sd3:.3f}")
    panel_condition(sig, y, groups)
    log("pilot_done=1")


if __name__ == "__main__":
    main()
