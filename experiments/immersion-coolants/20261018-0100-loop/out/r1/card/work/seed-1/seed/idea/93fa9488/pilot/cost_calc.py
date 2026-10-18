#!/usr/bin/env python3
"""
Cost/size model for option V1: "Force-field error floor for coolant MD"
(enlarged C10-C50 benchmark scored against measurement).

Deterministic arithmetic only -- no GPU needed. Reproduces every DERIVED
number in the plan record. Run:  python3 cost_calc.py
"""
import platform

n_replicates        = 5       # independent replicate trajectories per molecule
replicate_ns        = 20.0    # production length per replicate, ns
timestep_fs         = 2.0     # MD timestep, fs
throughput_ns_day   = 300.0   # PROXY: GROMACS ns/day on one A100 40GB
per_gpu_usd_h       = 1.99    # CITED: Lambda A100 SXM 40GB, USD/GPU-hour
n_anchor            = 5       # DESIGN: anchor molecules in the pilot phase
n_main              = 55      # DESIGN: extra benchmark molecules in the main phase
fs_usd_gib_month    = 0.2     # Lambda filesystem, USD/GiB-month
storage_gb_per_mol  = 1.0     # DESIGN: GK flux/coordinate files per molecule, GiB
months_kept         = 1.0     # DESIGN: months files are kept
budget_usd          = 1000.0  # hard stop

sim_ns_per_molecule = n_replicates * replicate_ns
ns_per_hour         = throughput_ns_day / 24.0
gpu_hours_per_mol   = sim_ns_per_molecule / ns_per_hour
usd_per_mol         = gpu_hours_per_mol * per_gpu_usd_h
n_molecules_total   = n_anchor + n_main
gpu_hours_pilot     = n_anchor * gpu_hours_per_mol
gpu_hours_main      = n_main * gpu_hours_per_mol
usd_pilot           = gpu_hours_pilot * per_gpu_usd_h
usd_main            = gpu_hours_main * per_gpu_usd_h
storage_usd         = n_molecules_total * storage_gb_per_mol * months_kept * fs_usd_gib_month
total_stated        = usd_pilot + usd_main + storage_usd
n_replicate_trajs   = n_molecules_total * n_replicates
total_sim_ns        = n_molecules_total * sim_ns_per_molecule
n_steps_per_mol     = sim_ns_per_molecule * 1e6 / timestep_fs
headroom            = budget_usd - total_stated
full200_usd         = 200 * usd_per_mol + 200 * storage_gb_per_mol * months_kept * fs_usd_gib_month

print("machine=%s python=%s" % (platform.node(), platform.python_version()))
print("sim_ns_per_molecule=%.1f" % sim_ns_per_molecule)
print("ns_per_hour=%.2f" % ns_per_hour)
print("gpu_hours_per_molecule=%.2f" % gpu_hours_per_mol)
print("usd_per_molecule=%.2f" % usd_per_mol)
print("n_molecules_total=%.0f" % n_molecules_total)
print("gpu_hours_pilot=%.1f" % gpu_hours_pilot)
print("gpu_hours_main=%.1f" % gpu_hours_main)
print("usd_pilot=%.2f" % usd_pilot)
print("usd_main=%.2f" % usd_main)
print("storage_usd=%.2f" % storage_usd)
print("total_stated=%.2f" % total_stated)
print("budget_headroom_usd=%.2f" % headroom)
print("n_replicate_trajs=%.0f" % n_replicate_trajs)
print("total_sim_ns=%.0f" % total_sim_ns)
print("n_steps_per_molecule=%.0f" % n_steps_per_mol)
print("full200_usd=%.2f" % full200_usd)
