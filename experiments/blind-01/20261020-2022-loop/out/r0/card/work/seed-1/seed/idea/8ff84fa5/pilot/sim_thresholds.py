#!/usr/bin/env python3
"""Toy calibration of the split-half contact-Jaccard noise rule.

Two generative models of AlphaFold-class pose sampling for one
capsid-peptide x receptor-ectodomain pair:

  unimodal : every prediction draws the SAME interface footprint
             (each of 20 true contacts kept with prob 0.9, plus 2%
              spurious contacts)
  bimodal  : predictions alternate between TWO footprints that share
             only 4 of 20 contacts

For each sampling depth n in {30, 150, 480} (the plan's compute levels)
we draw n predictions, split them into two halves by seed index three
different ways, and take the median Jaccard of the two halves' contact
sets (contacts present in >=50% of the half). This is the statistic the
plan uses to call "one footprint" (J >= 0.7) vs "still alternating"
(J <= 0.4). Nothing here is AlphaFold: it calibrates how the statistic
behaves under the two hypotheses the real run must separate.
"""
import random
from statistics import median

RNG = random.Random(20261020)

N_CONTACTS = 60  # 12 capsid residues x 5 receptor residues
FOOT_A = frozenset(range(0, 20))
FOOT_B = frozenset(range(16, 36))  # shares 4 contacts with A
KEEP = 0.9
SPURIOUS = 0.02


def draw_pose(footprint):
    contacts = set()
    for c in range(N_CONTACTS):
        if c in footprint:
            if RNG.random() < KEEP:
                contacts.add(c)
        elif RNG.random() < SPURIOUS:
            contacts.add(c)
    return frozenset(contacts)


def draw_sample(n, mode):
    out = []
    for i in range(n):
        foot = FOOT_A if mode == "unimodal" or i % 2 == 0 else FOOT_B
        out.append(draw_pose(foot))
    return out


def consensus(poses):
    counts = {}
    for p in poses:
        for c in p:
            counts[c] = counts.get(c, 0) + 1
    thr = 0.5 * len(poses)
    return frozenset(c for c, k in counts.items() if k >= thr)


def jaccard(a, b):
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def split_half_jaccard(sample):
    n = len(sample)
    js = []
    for shift in (0, n // 3, 2 * n // 3):
        ordered = sample[shift:] + sample[:shift]
        half = n // 2
        js.append(jaccard(consensus(ordered[:half]), consensus(ordered[half:])))
    return median(js)


def top_footprint_share(sample):
    """Fraction of poses whose contact set is closer to the majority
    footprint than to any other drawn cluster (Jaccard >= 0.5)."""
    counts = {}
    for p in sample:
        for c in p:
            counts[c] = counts.get(c, 0) + 1
    ref = frozenset(c for c, k in counts.items() if k >= 0.5 * len(sample))
    hit = sum(1 for p in sample if jaccard(p, ref) >= 0.5)
    return hit / len(sample)


print("sim_thresholds.py  seed=20261020  contacts=%d footA=%d footB=%d overlap=%d"
      % (N_CONTACTS, len(FOOT_A), len(FOOT_B), len(FOOT_A & FOOT_B)))
for mode in ("unimodal", "bimodal"):
    for n in (30, 150, 480):
        j = split_half_jaccard(draw_sample(n, mode))
        share = top_footprint_share(draw_sample(n, mode))
        print("mode=%s n=%d split_half_jaccard=%.3f top_footprint_share=%.3f"
              % (mode, n, j, share))

# Replicates at n=150 to size run-to-run noise of the statistic
for mode in ("unimodal", "bimodal"):
    reps = [split_half_jaccard(draw_sample(150, mode)) for _ in range(20)]
    lo, hi = min(reps), max(reps)
    print("mode=%s n=150 reps=20 jaccard_min=%.3f jaccard_max=%.3f spread=%.3f"
          % (mode, 150, lo, hi, hi - lo))
