#!/usr/bin/env python3
"""Pilot script for phase p1_pilot (run on the Lambda 8x A100 instance).

Writes pilot/pilot_metrics.txt with the numbers the plan's cost depends on:
  af_job_min        - wall minutes per AlphaFold-Multimer seed job (~250-400 aa complexes)
  anchor_job_min    - wall minutes for the published LRP6(20-1370) x X1 peptide anchor job
  dock_job_min      - CPU minutes per global rigid-body docking job
  md_ns_per_gpu_day - measured GROMACS throughput for the ~50k-atom refinement system
  anchor_contacts   - 1 if the PHP.eB-LY6A anchor reproduces published contacts (P5', F6', LY6A A58)
  motif_gap_shallow - first motif gap at the 144-model level (sanity check of the analysis path)

Usage (on the instance, after ColabFold and GROMACS are installed):
  python3 pilot/run_pilot.py --out pilot/pilot_metrics.txt \
      --anchor-af anchor/ranking_debug.json --anchor-log anchor/colabfold.log \
      --jobs jobs/job_times.json --md-log md/gmx.log

Without the optional flags it still writes the job manifest and the axis/geometry
utilities used later by phase p5_analysis.
"""
import argparse
import json
import math
import os
import re
import sys
import time

# ---- fixed panel (matches the plan record) ---------------------------------
CAPSIDS = [
    "AAV9", "AAV2", "PHP.B", "PHP.eB", "PHP.eC", "9P31",
    "9P36", "VCAP-102", "AAV9-X1.1", "CAP-Mac", "CAP-B22", "AAV-BI30",
]
RECEPTORS = ["LY6A", "LY6C1", "ALPL", "LRP6_E1E2", "CA4", "AAVR_PKD2"]
GPI_RECEPTORS = {"LY6A", "LY6C1", "ALPL", "CA4"}
POSES_PER_PAIR = {144: 2, 720: 10, 2880: 40}  # pose models per pair at each compute level

# published anchor contacts (Shay et al. 2023 Sci Adv, PMC10115422)
ANCHOR_PEPTIDE_CONTACTS = {"P5", "F6"}          # Pro5', Phe6' of the PHP.eB insert
ANCHOR_RECEPTOR_CONTACTS = {"A58"}               # LY6A Ala58


def build_manifest():
    rows = []
    for c in CAPSIDS:
        for r in RECEPTORS:
            rows.append({"capsid": c, "receptor": r, "pair": f"{c}__{r}",
                         "cognate": (c, r) in COGNATE})
    return rows


COGNATE = {
    ("PHP.B", "LY6A"), ("PHP.eB", "LY6A"), ("CAP-B22", "LY6A"),
    ("PHP.eC", "LY6C1"),
    ("9P31", "CA4"), ("9P36", "CA4"),
    ("VCAP-102", "ALPL"),
    ("AAV9-X1.1", "LRP6_E1E2"), ("CAP-Mac", "LRP6_E1E2"), ("AAV-BI30", "LRP6_E1E2"),
}


def axis_class(contact_centroid, three_fold_axes, two_fold_axes, five_fold_axes,
               cutoff=15.0):
    """Nearest icosahedral axis to the receptor contact centroid (capsid centred at origin)."""
    def near(axes):
        return min(math.dist(contact_centroid, a) for a in axes)
    d3, d2, d5 = near(three_fold_axes), near(two_fold_axes), near(five_fold_axes)
    if min(d3, d2, d5) > cutoff:
        return "wall", min(d3, d2, d5)
    best = min((d3, "3-fold"), (d2, "2-fold"), (d5, "5-fold"))
    return best[1], best[0]


def gpi_anchor_angle_deg(attachment_vector, membrane_normal=(0.0, 0.0, 1.0)):
    """Angle between the receptor C-terminal attachment vector and the membrane normal."""
    av = attachment_vector
    nv = membrane_normal
    dot = sum(a * b for a, b in zip(av, nv))
    na = math.sqrt(sum(a * a for a in av))
    nn = math.sqrt(sum(b * b for b in nv))
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / (na * nn)))))


def motif_call(pose):
    """GPI-engaging 3-fold motif: 3-fold class, compatible anchor vector, one-per-trimer."""
    cls, _ = pose["axis_class"]
    ang = gpi_anchor_angle_deg(pose["attachment_vector"])
    return (cls == "3-fold") and (ang <= 30.0) and (pose["n_receptor_per_trimer"] == 1)


def motif_gap(cognate_flags, calls):
    comp = [c for f, c in zip(cognate_flags, calls) if f]
    ret = [c for f, c in zip(cognate_flags, calls) if not f]
    if not comp or not ret:
        return float("nan")
    return sum(comp) / len(comp) - sum(ret) / len(ret)


def parse_af_job_minutes(log_path, key="TOTAL"):
    """Read per-job wall time from a colabfold log or a jobs/job_times.json."""
    if log_path.endswith(".json"):
        with open(log_path) as fh:
            data = json.load(fh)
        vals = [v for v in data.get(key, {}).values()]
        return sum(vals) / max(1, len(vals)) / 60.0
    mins = []
    with open(log_path) as fh:
        for line in fh:
            m = re.search(r"took\s+([0-9.]+)\s*s", line)
            if m:
                mins.append(float(m.group(1)) / 60.0)
    return sum(mins) / max(1, len(mins))


def parse_md_ns_per_day(log_path):
    with open(log_path) as fh:
        text = fh.read()
    m = re.search(r"Performance:\s+([0-9.]+)", text)
    return float(m.group(1)) if m else float("nan")


def anchor_contacts_ok(ranking_json, contact_json):
    """Check published contacts are reproduced (P5'/F6' peptide, LY6A A58 within 5 A)."""
    with open(ranking_json) as fh:
        ranking = json.load(fh)
    top = ranking["order"][0]
    with open(contact_json) as fh:
        contacts = json.load(fh)
    pep = {c["residue"] for c in contacts[top]["peptide"]}
    rec = {c["residue"] for c in contacts[top]["receptor"]}
    ok = (ANCHOR_PEPTIDE_CONTACTS <= pep) and (ANCHOR_RECEPTOR_CONTACTS & rec)
    return 1 if ok else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="pilot/pilot_metrics.txt")
    ap.add_argument("--anchor-af", default=None)
    ap.add_argument("--anchor-contacts", default=None)
    ap.add_argument("--jobs", default=None)
    ap.add_argument("--md-log", default=None)
    ap.add_argument("--dump-manifest", default="pilot/job_manifest.json")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    manifest = build_manifest()
    with open(args.dump_manifest, "w") as fh:
        json.dump({"pairs": manifest,
                   "levels": POSES_PER_PAIR,
                   "n_pairs": len(manifest)}, fh, indent=2)

    lines = []
    lines.append("n_pairs=%d" % len(manifest))
    for level, per in POSES_PER_PAIR.items():
        lines.append("n_pose_level_%d=%d" % (level, len(manifest) * per))

    if args.jobs:
        lines.append("af_job_min=%.3f" % parse_af_job_minutes(args.jobs))
    if args.anchor_af:
        lines.append("anchor_job_min=%.3f" % parse_af_job_minutes(args.anchor_af))
    if args.md_log:
        lines.append("md_ns_per_gpu_day=%.1f" % parse_md_ns_per_day(args.md_log))
    if args.anchor_af and args.anchor_contacts:
        lines.append("anchor_contacts=%d" %
                     anchor_contacts_ok(args.anchor_af, args.anchor_contacts))

    # geometry sanity example for the analysis path (placeholder pose; real poses
    # come from p2/p3 and are classified with the same functions)
    demo = {"axis_class": axis_class((0.0, 0.0, 125.0), [(0.0, 0.0, 125.0)], [], [],
                                     cutoff=15.0),
            "attachment_vector": (0.0, 0.0, 1.0),
            "n_receptor_per_trimer": 1}
    lines.append("demo_motif_call=%d" % int(motif_call(demo)))
    lines.append("demo_motif_gap=%.3f" %
                 motif_gap([True, True, False, False], [True, True, False, False]))

    with open(args.out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
