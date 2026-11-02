#!/usr/bin/env bash
# run_anchors.sh - run the published protocol at the representative scale and report measured anchors.
#
# Invoked as:  bash harness/run_anchors.sh   (same working directory as setup.sh)
#
# Runs `bash harness/run_command.sh` unchanged (the canonical measured command and environment), then
# parses only that run's saved outputs:
#   out/run_command/run_command.log      printed configuration, index counts, pinder logger lines
#   out/results/frodock_metrics.csv      per-decoy Fnat/iRMS/LRMS/DockQ/CAPRI written by pinder_eval
# and writes
#   out/anchors_measured.json   {item_id: measured_number} for every intake anchors.json item
#   out/anchors_details.json    per-system/per-pairing top-1 and best-of-50 DockQ, iRMS, Fnat, LRMS,
#                               acceptability (DockQ >= 0.23), failed jobs, per-job docking wall-clock
#
# Item measurements:
#   dockq_acceptable_threshold  best DockQ over all 800 measured decoys (16 jobs x 50 poses); compared
#                               by the pipeline against the published ">= 0.23" acceptance criterion
#   pinder_s_system_count       number of PINDER-S systems in the release index, printed by run_command
#   pinder_s_apo_paired_count   PINDER-S systems with apo receptor and apo ligand, printed by run_command
# Checks fail only on missing or invalid output; values are never compared to published numbers here.
set -Eeuo pipefail

mkdir -p out/anchors_logs
TS="$(date -u +%Y%m%dT%H%M%SZ)"
for f in out/anchors_measured.json out/anchors_details.json out/run_anchors.log; do
  [ -e "$f" ] && { mkdir -p "out/anchors_logs/$TS"; mv "$f" "out/anchors_logs/$TS/"; }
done
exec > >(tee out/run_anchors.log) 2>&1
echo "== run_anchors.sh start $(date -u +%FT%TZ)"

set +e
bash harness/run_command.sh
RC=$?
set -e
echo "== run_command.sh exit status $RC"
cp out/run_command/run_command.log "out/anchors_logs/run_command.$TS.log" 2>/dev/null || true
[ "$RC" -eq 0 ] || { echo "ERROR: harness/run_command.sh failed ($RC); see out/run_command/run_command.log" >&2; exit "$RC"; }

python3 -I - out/run_command/run_command.log out/results/frodock_metrics.csv data/selection.json \
    out/anchors_measured.json out/anchors_details.json <<'PY'
import csv, json, math, re, sys
from pathlib import Path
from datetime import datetime
log_path, metrics_path, sel_path, out_path, det_path = sys.argv[1:6]
ITEMS = ["dockq_acceptable_threshold", "pinder_s_system_count", "pinder_s_apo_paired_count"]
# Frozen intake IDs above also support pipeline deployments shipping only harness/. If intake
# accompanies the scripts, use every supplied item (anchors and references), including an empty set.
intake_path = Path("intake/anchors.json")
if intake_path.is_file():
    intake_items = json.load(open(intake_path))
    if intake_items == {}:
        intake_items = []
    if not isinstance(intake_items, list):
        sys.exit("ERROR: intake/anchors.json must contain a list of items")
    ITEMS = [item["id"] for item in intake_items]
    if len(ITEMS) != len(set(ITEMS)):
        sys.exit("ERROR: duplicate intake item IDs")
if not ITEMS:
    json.dump({}, open(out_path, "w"))
    json.dump({"measured": {}, "command_log": log_path}, open(det_path, "w"), indent=2)
    print("{}")
    sys.exit(0)
KINDS = ["holo", "apo"]
N_SOLUTIONS = 50
ACCEPT = 0.23
def fail(msg): sys.exit("ERROR: " + msg)

log = open(log_path, errors="replace").read()
def logint(key):
    m = re.findall(rf"^{key}=(\d+)\s*$", log, re.M)
    if not m: fail(f"{key} not found in run_command output")
    return int(m[-1])
m = re.findall(r"^SELECTED_IDS=(\[.*\])\s*$", log, re.M)
if not m: fail("SELECTED_IDS not found in run_command output")
ids = json.loads(m[-1])
if ids != json.load(open(sel_path))["ids"]: fail("run_command selection differs from data/selection.json")

def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None

try:
    rows = list(csv.DictReader(open(metrics_path)))
except FileNotFoundError:
    fail(f"{metrics_path} missing")
if not rows: fail("metrics csv is empty")
for col in ("id", "monomer_name", "model_name", "DockQ", "iRMS", "Fnat", "LRMS"):
    if col not in rows[0]: fail(f"metrics csv lacks column {col}")
rank_re = re.compile(r"\d+(?=\D*$)")
per = {}
seen = set()
for r in rows:
    if r["id"] not in ids or r["monomer_name"] not in KINDS: continue
    if "pinder_set" in r and r["pinder_set"] not in ("", "pinder_s"): continue
    key = (r["id"], r["monomer_name"], r["model_name"])
    if key in seen: continue
    seen.add(key)
    rank = num(r.get("rank"))
    if rank is None:
        mm = rank_re.findall(r["model_name"]); rank = float(mm[-1]) if mm else None
    vals = {k: num(r[k]) for k in ("DockQ", "iRMS", "Fnat", "LRMS")}
    if rank is None or any(v is None for v in vals.values()): fail(f"invalid metrics row {key}")
    vals["rank"] = int(rank); vals["model_name"] = r["model_name"]; vals["CAPRI"] = r.get("CAPRI", "")
    per.setdefault((r["id"], r["monomer_name"]), []).append(vals)

# per-job docking wall-clock from the published adapter's logger lines (start of stage 1 .. decoy copy)
ts_re = r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) \|"
def ts(s): return datetime.strptime(s, "%Y-%m-%d %H:%M:%S,%f").timestamp()
starts, ends = {}, {}
for mt in re.finditer(ts_re + r".*Running FroDock \(\d+ solutions\) on complex (\S+) (\S+) ", log, re.M):
    starts[(mt.group(2), mt.group(3))] = ts(mt.group(1))
for mt in re.finditer(ts_re + r".*Copying the results to \S*/frodock/([^/\s]+)/(\w+)_decoys", log, re.M):
    ends[(mt.group(2), mt.group(3))] = ts(mt.group(1))

jobs, failed, best_all = [], [], []
for pid in ids:
    for kind in KINDS:
        recs = sorted(per.get((pid, kind), []), key=lambda v: v["rank"])
        if not recs: fail(f"no metrics rows (not even the published penalty) for {pid} {kind}")
        penalty = all(v["model_name"].startswith("missing_decoy") for v in recs)
        if penalty: failed.append({"id": pid, "kind": kind})
        top = recs[0]
        best = max(recs, key=lambda v: v["DockQ"])
        best_all.append(best["DockQ"])
        wall = (ends[(pid, kind)] - starts[(pid, kind)]) if (pid, kind) in starts and (pid, kind) in ends else None
        jobs.append({"id": pid, "kind": kind, "n_decoys_scored": 0 if penalty else len(recs), "penalised_missing": penalty,
                     "top1": {k: top[k] for k in ("DockQ", "iRMS", "Fnat", "LRMS", "CAPRI", "rank")},
                     "best": {k: best[k] for k in ("DockQ", "iRMS", "Fnat", "LRMS", "CAPRI", "rank")},
                     "top1_acceptable": top["DockQ"] >= ACCEPT, "best_acceptable": best["DockQ"] >= ACCEPT,
                     "docking_wall_s": wall,
                     "poses_per_s": (N_SOLUTIONS / wall) if (wall and not penalty) else None})

measured = {
    "dockq_acceptable_threshold": max(best_all),
    "pinder_s_system_count": logint("PINDER_S_SYSTEM_COUNT"),
    "pinder_s_apo_paired_count": logint("PINDER_S_APO_PAIRED_COUNT"),
}
for k in ITEMS:
    v = measured.get(k)
    if v is None or not math.isfinite(float(v)): fail(f"no finite measurement for {k}")
json.dump({k: measured[k] for k in ITEMS}, open(out_path, "w"), indent=2)
walls = [j["docking_wall_s"] for j in jobs if j["docking_wall_s"] is not None]
details = {
    "definitions": {
        "dockq_acceptable_threshold": "max DockQ over all scored decoys of the 16 holo/apo jobs (best-of-50 per job, then max)",
        "pinder_s_system_count": "PINDER-S systems in index.parquet (release 2024-02) via pinder.core.get_index",
        "pinder_s_apo_paired_count": "PINDER-S systems with apo_R and apo_L",
        "docking_wall_s": "pinder logger timestamp of 'Running FroDock' to 'Copying the results' for that job",
    },
    "selected_ids": ids, "jobs": jobs, "failed_jobs_penalised": failed,
    "summary": {
        "n_jobs": len(jobs),
        "top1_acceptable_jobs": sum(j["top1_acceptable"] for j in jobs),
        "best_acceptable_jobs": sum(j["best_acceptable"] for j in jobs),
        "docking_wall_s_sum": sum(walls) if len(walls) == len(jobs) else None,
    },
    "measured": measured,
}
json.dump(details, open(det_path, "w"), indent=2)
print(json.dumps(measured, indent=2))
print(json.dumps(details["summary"], indent=2))
PY
echo "== run_anchors.sh done $(date -u +%FT%TZ)"
