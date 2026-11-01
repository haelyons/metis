#!/usr/bin/env bash
# run_units.sh - the measured baseline restricted to original prepared input records.
#
# Invoked as:  bash harness/run_units.sh <system_id:kind>...   (working directory = the shared run directory, or a sibling
# work directory that links baseline-published/, data/ and harness/). Command paths are relative;
# absolute PATH entries and TMPDIR are inherited from run_command.sh (see REPORT.md).
# PATH entries are resolved from this working directory because the published
# FroDock adapter changes directory into a temporary stage directory.
#
# Representative scale (EXECUTION.json, fixed): the 8 preregistered PINDER-S apo-paired systems in
# data/selection.json; requested holo/apo jobs only, n_solutions=50, mpi_np=8, force=false,
# docked by the published `pinder_methods predict --method frodock` and scored by the published
# `pinder_eval` (50 decoys per selected job). FroDock is CPU + MPI only: no GPU is used (CUDA_VISIBLE_DEVICES="",
# GPU count 0). CUDA MPS variables are inherited unchanged.
#
# Output (stdout+stderr of both published commands): out/run_command/run_command.log
#   decoys:  out/results/frodock/<pinder_id>/{holo,apo}_decoys/model_<rank>.pdb
#   scores:  out/results/frodock_metrics.csv, out/results/frodock_leaderboard.csv
# Exit status: nonzero if either published command fails.
set -Eeuo pipefail
[ "$#" -gt 0 ] || { echo "ERROR: at least one system_id:kind is required" >&2; exit 2; }

# ------------------------------------------------------------------ complete environment
export CUDA_VISIBLE_DEVICES=""          # CPU/MPI-only baseline
BASELINE_GPU_COUNT=0
N_SOLUTIONS=50
MPI_NP=8
FORCE=false
EVAL_MAX_WORKERS=8
METHOD=frodock
export PINDER_BASE_DIR=data
export PINDER_RELEASE=2024-02
export LOG_LEVEL=INFO
export PYTHONUNBUFFERED=1
unset PINDER_DATA_DIR || true
# CUDA toolchain selection (same ls-checked rule as setup.sh; not used by the CPU baseline)
CUDA_SEL=""
for root in /usr/local/cuda /usr/lib/cuda; do
  if ls "$root/bin/nvcc" "$root/include/cuda_runtime.h" "$root/lib64/libcudart.so" >/dev/null 2>&1; then
    CUDA_SEL="toolkit_root:$root"; export PATH="$root/bin:$PATH"; export CUDAToolkit_ROOT="$root"; break
  fi
done
if [ -z "$CUDA_SEL" ] && ls /usr/bin/nvcc /usr/include/cuda_runtime.h /usr/lib/x86_64-linux-gnu/libcudart.so >/dev/null 2>&1; then
  CUDA_SEL="distro:/usr/bin/nvcc"
fi
[ -n "$CUDA_SEL" ] || { echo "ERROR: no complete CUDA layout found (same rule as setup.sh)" >&2; exit 1; }
VENV=baseline-published/venv
VPY="$VENV/bin/python"
export PATH="$PWD/baseline-published/frodock/bin:$PWD/$VENV/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1

# ------------------------------------------------------------------ output locations (logs preserved)
RUN_DIR="out/run_command"
RESULTS="out/results"
mkdir -p "$RUN_DIR/history"
TS="$(date -u +%Y%m%dT%H%M%S%NZ)"
if [ -e "$RUN_DIR/run_command.log" ]; then
  mkdir -p "$RUN_DIR/history/$TS"
  mv "$RUN_DIR"/*.log "$RUN_DIR"/*.yaml "$RUN_DIR"/*.json "$RUN_DIR"/*.tar.gz "$RUN_DIR/history/$TS/" 2>/dev/null || true
fi
# Preserve decoys and scoring output from earlier invocations as well as logs.
if [ -d "$RESULTS" ]; then
  mkdir -p "$RUN_DIR/history/$TS"
  mv "$RESULTS" "$RUN_DIR/history/$TS/results"
fi
exec > >(tee "$RUN_DIR/run_command.log") 2>&1
mkdir -p out/tmp
export TMPDIR="$PWD/out/tmp"

for f in "$VPY" "$VENV/bin/pinder_methods" "$VENV/bin/pinder_eval" data/selection.json data/frodock/frodock_setup.csv; do
  [ -e "$f" ] || { echo "ERROR: $f missing; run harness/setup.sh first" >&2; exit 1; }
done
for b in frodockgrid_mpi_gcc frodock_mpi_gcc frodockcluster_gcc frodockview_gcc soap.bin; do
  [ -e "baseline-published/frodock/bin/$b" ] || { echo "ERROR: FroDock $b missing" >&2; exit 1; }
done

# fresh results tree: force=false would otherwise skip jobs whose decoys already exist
mkdir -p "$RESULTS"
cat > "$RUN_DIR/frodock_config.yaml" <<EOF
n_solutions: $N_SOLUTIONS
mpi_np: $MPI_NP
force: $FORCE
EOF
cp data/frodock/frodock_setup.csv "$RESULTS/frodock_setup.csv"   # predict reads <results_dir>/frodock_setup.csv

# ------------------------------------------------------------------ printed configuration (validated)
"$VPY" - "$RUN_DIR/frodock_config.yaml" "$RESULTS/frodock_setup.csv" data/selection.json \
    "$METHOD" "$N_SOLUTIONS" "$MPI_NP" "$FORCE" "$EVAL_MAX_WORKERS" "$BASELINE_GPU_COUNT" <<'PY'
import json, os, sys, yaml
import pandas as pd
from pinder.core import get_index
cfg = yaml.safe_load(open(sys.argv[1])); jobs = pd.read_csv(sys.argv[2]); sel = json.load(open(sys.argv[3]))
idx = get_index()
s = idx[idx["pinder_s"].astype(bool)]
apo = s[s["apo_R"].astype(bool) & s["apo_L"].astype(bool)]
ids = sorted(set(apo["id"]))[: sel["n"]]
print(f"PINDER_S_SYSTEM_COUNT={s['id'].nunique()}")
print(f"PINDER_S_APO_PAIRED_COUNT={apo['id'].nunique()}")
print("SELECTED_IDS=" + json.dumps(ids))
errs = []
if sys.argv[4:] != ["frodock", "50", "8", "false", "8", "0"]: errs.append("actual command parameters differ from fixed configuration")
if os.environ.get("CUDA_VISIBLE_DEVICES") != "": errs.append("CPU baseline must expose zero GPUs")
if os.environ.get("PINDER_BASE_DIR") != "data" or os.environ.get("PINDER_RELEASE") != "2024-02": errs.append("dataset environment differs from fixed configuration")
if ids != sel["ids"]: errs.append("selection from index differs from data/selection.json")
if sel["n"] != 8 or len(ids) != 8: errs.append("representative scale must contain exactly 8 systems")
if cfg != {"n_solutions": 50, "mpi_np": 8, "force": False}: errs.append(f"config {cfg} is not the published representative config")
if sorted(set(jobs["id"])) != sorted(ids): errs.append("frodock_setup.csv ids differ from selection")
if sorted(set(jobs["kind"])) != ["apo", "holo"] or len(jobs) != 2 * len(ids): errs.append("frodock_setup.csv is not holo+apo for every id")
if set(zip(jobs["id"], jobs["kind"])) != {(pid, kind) for pid in ids for kind in ("holo", "apo")}: errs.append("frodock_setup.csv lacks an expected id/pairing")
print(f"CONFIG method=frodock subset=pinder-s pairs=holo,apo n_jobs={len(jobs)} n_solutions={cfg.get('n_solutions')} "
      f"mpi_np={cfg.get('mpi_np')} force={cfg.get('force')} CUDA_VISIBLE_DEVICES='{os.environ.get('CUDA_VISIBLE_DEVICES')}' "
      f"host_nproc={os.cpu_count()} PINDER_BASE_DIR={os.environ.get('PINDER_BASE_DIR')}")
if errs:
    sys.exit("ERROR: " + "; ".join(errs))
PY
echo "GPU_COUNT=$BASELINE_GPU_COUNT CUDA_SELECTION=$CUDA_SEL MPIRUN=$(command -v mpirun) FRODOCK_BIN=$(dirname "$(command -v frodock_mpi_gcc)")"
echo "PINDER_VERSION=$("$VPY" -c 'import importlib.metadata as m;print(m.version("pinder"))')"

# Restrict the validated prepared list; retain its header and original record bytes.
# The unchanged prediction command reads this path through its existing --results_dir.
"$VPY" - "$RESULTS/frodock_setup.csv" "$@" <<'PY'
import csv
import io
from pathlib import Path
import re
import sys

target = Path(sys.argv[1])
requested = sys.argv[2:]
if not requested or len(set(requested)) != len(requested):
    sys.exit("ERROR: provide one or more distinct system_id:kind keys")
raw = target.read_bytes().splitlines(keepends=True)
reader = csv.DictReader(io.StringIO(b"".join(raw).decode("utf-8"), newline=""), strict=True)
rows = list(reader)
if reader.fieldnames != ["id", "kind", "receptor", "ligand"] or not rows:
    sys.exit("ERROR: unexpected prepared manifest schema")
if len(raw) != len(rows) + 1 or any(not line.endswith(b"\n") for line in raw):
    sys.exit("ERROR: expected the original newline-terminated one-line-per-record format")
keys = [row["id"] + ":" + row["kind"] for row in rows]
if len(set(keys)) != len(keys):
    sys.exit("ERROR: duplicate prepared unit")
if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}", key)
       or key not in keys for key in requested):
    sys.exit("ERROR: unknown or invalid requested unit")
target.write_bytes(raw[0] + b"".join(raw[keys.index(key) + 1] for key in requested))
print("RESTRICTED_UNITS=" + ",".join(requested))
PY

# ------------------------------------------------------------------ published docking command
set +e
"$VPY" "$VENV/bin/pinder_methods" predict --method "$METHOD" --data_dir data/frodock \
    --results_dir "$RESULTS" --subset pinder-s --pairs all --config "$RUN_DIR/frodock_config.yaml"
PRED_RC=$?
set -e
echo "PREDICT_EXIT=$PRED_RC"
[ "$PRED_RC" -eq 0 ] || { echo "ERROR: pinder_methods predict exited $PRED_RC" >&2; exit "$PRED_RC"; }

# FroDock 3.12 writes small molecules as HETATM with a blank chain. The published adapter
# concatenates receptor + transformed ligand without restoring that label. Restore only blank
# ligand HETATM labels, retaining every atom, coordinate, rank and all other PDB bytes. Identify the
# ligand suffix by its existing L-labelled atoms. FroDock's output atom count need not equal the
# input reader's count (e.g. alternate locations); validate emitted records, not that equality.
# Keep original decoys and a change manifest beside the saved command output.
"$VPY" - "$RESULTS" "$RUN_DIR" <<'PY'
import csv, json, sys, tarfile
from pathlib import Path
import biotite.structure.io as strucio

results, run_dir = map(Path, sys.argv[1:])
changes = []
with tarfile.open(run_dir / "raw_decoys.tar.gz", "w:gz") as originals:
    for job in csv.DictReader(open(results / "frodock_setup.csv")):
        directory = results / "frodock" / job["id"] / (job["kind"] + "_decoys")
        for model in sorted(directory.glob("model_*.pdb")):
            lines = model.read_text().splitlines(keepends=True)
            atom_lines = [i for i, line in enumerate(lines) if line.startswith(("ATOM  ", "HETATM"))]
            if not atom_lines or lines[atom_lines[0]][21:22] != "R":
                raise SystemExit(f"ERROR: {model}: missing receptor prefix")
            restored = []
            in_ligand = False
            for line_index in atom_lines:
                line = lines[line_index]
                chain = line[21:22]
                if chain == "L":
                    in_ligand = True
                    continue
                if chain == "R" and not in_ligand:
                    continue
                if not in_ligand or chain != " " or not line.startswith("HETATM"):
                    raise SystemExit(f"ERROR: {model}: unexpected chain on PDB line {line_index + 1}")
                restored.append(line_index + 1)
            if not in_ligand:
                raise SystemExit(f"ERROR: {model}: missing labelled ligand atoms")
            if restored:
                originals.add(model, arcname=model.relative_to(results))
                for line_number in restored:
                    line = lines[line_number - 1]
                    lines[line_number - 1] = line[:21] + "L" + line[22:]
                model.write_text("".join(lines))
                changes.append({"file": str(model), "line_numbers": restored, "chain": "L"})
            chains = set(strucio.load_structure(str(model)).chain_id)
            if chains != {"R", "L"}:
                raise SystemExit(f"ERROR: {model}: invalid chains {chains}")
json.dump(changes, open(run_dir / "chain_labels_restored.json", "w"), indent=2)
print(f"CHAIN_LABELS_RESTORED models={len(changes)} atoms={sum(len(c['line_numbers']) for c in changes)}")
PY

# ------------------------------------------------------------------ published scoring command
# pinder_eval asks for interactive confirmation for every subset/pairing with systems not run here;
# answer yes so the published missing-system penalty is applied (no --allow_missing).
set +e +o pipefail
yes y | "$VPY" "$VENV/bin/pinder_eval" --eval_dir "$RESULTS" --method_name "$METHOD" --max_workers "$EVAL_MAX_WORKERS"
EVAL_RC=${PIPESTATUS[1]}
set -e -o pipefail
echo "EVAL_EXIT=$EVAL_RC"
[ "$EVAL_RC" -eq 0 ] || { echo "ERROR: pinder_eval exited $EVAL_RC" >&2; exit "$EVAL_RC"; }
exit 0
