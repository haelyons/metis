#!/usr/bin/env python3
"""Phase p1_pilot throughput probe for option V3. Run on a Lambda 8x A100 node.

Measures, and prints one line per number id used in the cost record:
  af2_h_per_run        wall-clock hours for one ColabFold/AF2-multimer run (750-1000 residues,
                       5 models, up to 20 recycles) on one A100 40 GB
  md_ns_per_day_a100   GROMACS ns/day for a docked capsid-receptor complex (~170k atoms)
  aux_h_per_pair       hours for one rigid-body docking job + MSAs + scoring + I/O
  seed_sd_calls        seed-to-seed SD of bind/no-bind calls on the 3x3 pilot subset

Usage: timeout 21600 python3 measure_throughput.py --out ../pilot/pilot_throughput.txt
Everything is timed with time.monotonic() around the real commands; replace the placeholder
commands below with the installed binaries before running.
"""
import argparse
import subprocess
import time

# Placeholder commands; swap in the installed ColabFold / GROMACS / LightDock invocations.
AF2_CMD = ["colabfold_batch", "--num-models", "5", "--num-recycle", "20",
           "pilot_pair.fasta", "out/af2/"]
MD_CMD = ["gmx", "mdrun", "-ntmpi", "1", "-ntomp", "16", "-nb", "gpu", "-pme", "gpu",
          "-bonded", "gpu", "-update", "gpu", "-nsteps", "1250000", "-s", "pair.tpr",
          "-deffnm", "out/md/pair_5ns"]
DOCK_CMD = ["lightdock3.py", "setup.json", "100", "-s", "fastdfire"]


def timed(cmd):
    t0 = time.monotonic()
    subprocess.run(cmd, check=False)
    return (time.monotonic() - t0) / 3600.0  # hours


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="pilot_throughput.txt")
    args = ap.parse_args()
    af2_h = timed(AF2_CMD)
    md_h = timed(MD_CMD)
    ns_per_day = 5.0 * 24.0 / md_h if md_h > 0 else float("nan")
    aux_h = timed(DOCK_CMD)
    with open(args.out, "w") as fh:
        fh.write("af2_h_per_run %.3f\n" % af2_h)
        fh.write("md_ns_per_day_a100 %.1f\n" % ns_per_day)
        fh.write("aux_h_per_pair %.3f\n" % aux_h)
        fh.write("seed_sd_calls NaN  # fill after scoring the 3 seed sets of the pilot subset\n")
    print(open(args.out).read())


if __name__ == "__main__":
    main()
