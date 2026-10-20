#!/usr/bin/env python3
"""Recompute the plan's Lambda bill from its number ids.

Every constant below is the record's number id. Rates are the price
sheet read at 2026-10-20 (https://lambda.ai/pricing):
  8x NVIDIA A100 SXM 40 GB : $1.99 per GPU-hour
  1x NVIDIA A100 SXM 40 GB : $1.99 per GPU-hour
  filesystem               : $0.20 per GiB-month (fs_usd_gib_month)
Wall-clock hours are instance hours: GPU-work / n_gpus.
"""

# --- number ids -------------------------------------------------------
min_per_pred_ours = 8.0        # minutes per prediction, GUESS (probe measures)
pairs_grid = 36
preds_per_pair_grid = 30
sentinel_pairs = 2
preds_per_pair_top = 480
version_arms = 2
preds_per_version = 150
storage_gib = 50
fs_usd_gib_month = 0.20
per_gpu_usd_h = 1.99
n_gpus_grid = 8
budget_usd = 1000.0

preds_grid_total = pairs_grid * preds_per_pair_grid
preds_depth_total = sentinel_pairs * (preds_per_pair_top - preds_per_pair_grid)
preds_version_total = version_arms * preds_per_version
preds_total = preds_grid_total + preds_depth_total + preds_version_total
gpu_h_total = preds_total * min_per_pred_ours / 60.0

grid_wall_h = preds_grid_total * min_per_pred_ours / 60.0 / n_gpus_grid
depth_wall_h = preds_depth_total * min_per_pred_ours / 60.0 / n_gpus_grid
version_wall_h = preds_version_total * min_per_pred_ours / 60.0 / n_gpus_grid

print("preds_grid_total=%d preds_depth_total=%d preds_version_total=%d preds_total=%d"
      % (preds_grid_total, preds_depth_total, preds_version_total, preds_total))
print("gpu_h_total=%.2f grid_wall_h=%.2f depth_wall_h=%.2f version_wall_h=%.2f"
      % (gpu_h_total, grid_wall_h, depth_wall_h, version_wall_h))

# --- time-boxed lines (hours are boxes; need is estimated work) -------
lines = [
    # id, hours_box, n_gpus, need_h
    ("L_probe",   5,  1, 2 + 6 * min_per_pred_ours / 60),
    ("L_anchor",  8,  1, 3 + 30 * min_per_pred_ours / 60),
    ("L_grid",   20,  8, grid_wall_h),
    ("L_depth",  16,  8, depth_wall_h),
    ("L_version", 6,  8, version_wall_h),
    ("L_analysis", 6, 1, 3),
]
total = 0.0
for lid, hours, n_gpus, need in lines:
    usd = hours * n_gpus * per_gpu_usd_h
    total += usd
    print("line=%s hours=%d n_gpus=%d need_h=%.2f usd=%.2f" % (lid, hours, n_gpus, need, usd))

storage_usd = storage_gib * fs_usd_gib_month
contingency_usd = 150.0
total += storage_usd + contingency_usd
print("storage_usd=%.2f contingency_usd=%.2f" % (storage_usd, contingency_usd))
print("total_stated_usd=%.2f budget_usd=%.2f headroom_usd=%.2f"
      % (total, budget_usd, budget_usd - total))

# spend if the GUESS is wrong and predictions take 25 min each
slow = 25.0
slow_work = (preds_total * slow / 60.0) * per_gpu_usd_h
print("scenario_slow_gpu_h_total=%.2f scenario_slow_work_usd=%.2f"
      % (preds_total * slow / 60.0, slow_work))
