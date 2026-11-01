#!/usr/bin/env bash
# run_evaluation.sh - published-baseline evaluation adapter (PINDER FroDock baseline).
#
# Invoked from a fresh evaluation working directory that links baseline-published/, method/, data/,
# harness/ and payload/, with absolute BASELINE_DIR, METHOD_DIR, BASELINE_OUT, METHOD_OUT, EVAL_OUT and
#   EVAL_MODE            equivalence | warmup | performance | curve
#   EVAL_PROTOCOL        path to the sealed protocol JSON (timing_scope is copied from it verbatim)
#   EVAL_INPUTS          JSON: {"ids": [input_id, ...], ...}; an input_id is a PINDER system ID, optionally
#                        suffixed ":holo" / ":apo" (or "/holo", "/apo") to restrict the pairing
#   EVAL_SEEDS           JSON: {"kind":"paired_median","seeds":[...]} or {"kind":"deterministic",...}
#   EVAL_COMPUTE_BUDGET  GPU-second budget (curve mode only)
#
# For every seed (outer loop) and input id (inner loop) it runs the published configuration unchanged:
# `pinder_methods preprocess` (holo and apo, untimed setup), `pinder_methods predict --method frodock`
# with n_solutions=50, mpi_np=8, force=false (timed), and `pinder_eval` on that run's own decoys.
# FroDock exposes no seed; the seed is recorded and exported as BASELINE_EVAL_SEED only.
# Writes $EVAL_OUT/evaluation.json:
#   {records:[{input_id,seed,metrics:{...}}], timing_scope, gpu_count, wall_s, compute_budget}
# wall_s = sum of the timed predict invocations (process launch, MPI startup, all 8 FroDock stages,
# decoy writing and copy-out included). The baseline uses no GPU (gpu_count 0, 0 GPU-seconds), so a
# curve budget in GPU seconds is never consumed; it is checked and recorded.
# CUDA MPS variables are inherited unchanged.
set -Eeuo pipefail

: "${EVAL_OUT:?EVAL_OUT must be set}"
: "${EVAL_PROTOCOL:?EVAL_PROTOCOL must be set}"
: "${EVAL_INPUTS:?EVAL_INPUTS must be set}"
: "${EVAL_SEEDS:?EVAL_SEEDS must be set}"
EVAL_MODE="${EVAL_MODE:-equivalence}"
EVAL_COMPUTE_BUDGET="${EVAL_COMPUTE_BUDGET:-}"
case "$EVAL_MODE" in equivalence|warmup|performance|curve) ;; *) echo "ERROR: unknown EVAL_MODE $EVAL_MODE" >&2; exit 2;; esac
if [ "$EVAL_MODE" = curve ] && [ -z "$EVAL_COMPUTE_BUDGET" ]; then echo "ERROR: curve mode needs EVAL_COMPUTE_BUDGET" >&2; exit 2; fi

# same environment as harness/run_command.sh
export CUDA_VISIBLE_DEVICES=""
N_SOLUTIONS=50; MPI_NP=8; FORCE=false; EVAL_MAX_WORKERS=8; METHOD=frodock
if [ -d "$PWD/baseline-published" ]; then BP="$PWD/baseline-published"
elif [ -n "${BASELINE_DIR:-}" ] && [ -d "$BASELINE_DIR/baseline-published" ]; then BP="$BASELINE_DIR/baseline-published"
else BP="${BASELINE_DIR:?baseline-published not found}"; fi
DATA_ROOT="$PWD/data"
[ -d "$DATA_ROOT/pinder" ] || DATA_ROOT="$(dirname "$BP")/data"
export PINDER_BASE_DIR="$DATA_ROOT"
export PINDER_RELEASE=2024-02
export LOG_LEVEL=INFO
export PYTHONUNBUFFERED=1
unset PINDER_DATA_DIR || true
CUDA_SEL=""
for root in /usr/local/cuda /usr/lib/cuda; do
  if ls "$root/bin/nvcc" "$root/include/cuda_runtime.h" "$root/lib64/libcudart.so" >/dev/null 2>&1; then
    CUDA_SEL="toolkit_root:$root"; export PATH="$root/bin:$PATH"; export CUDAToolkit_ROOT="$root"; break
  fi
done
if [ -z "$CUDA_SEL" ] && ls /usr/bin/nvcc /usr/include/cuda_runtime.h /usr/lib/x86_64-linux-gnu/libcudart.so >/dev/null 2>&1; then CUDA_SEL="distro:/usr/bin/nvcc"; fi
[ -n "$CUDA_SEL" ] || { echo "ERROR: no complete CUDA layout found" >&2; exit 1; }
VENV="$BP/venv"; VPY="$VENV/bin/python"
export PATH="$BP/frodock/bin:$VENV/bin:$PATH"
for f in "$VPY" "$VENV/bin/pinder_methods" "$VENV/bin/pinder_eval" "$BP/frodock/bin/frodock_mpi_gcc" "$BP/frodock/bin/soap.bin"; do
  [ -e "$f" ] || { echo "ERROR: $f missing (run harness/setup.sh)" >&2; exit 1; }
done

mkdir -p "$EVAL_OUT/logs" "$EVAL_OUT/work"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$EVAL_OUT/logs/run_evaluation.$EVAL_MODE.$TS.log"
exec > >(tee "$LOG") 2>&1
echo "== run_evaluation.sh mode=$EVAL_MODE start $(date -u +%FT%TZ) cwd=$PWD baseline=$BP data=$PINDER_BASE_DIR"

PLAN="$EVAL_OUT/work/plan.$TS.json"
python3 -I - "$PLAN" <<'PY'
import json, os, sys
inputs = json.loads(os.environ["EVAL_INPUTS"]); seeds = json.loads(os.environ["EVAL_SEEDS"])
proto = json.load(open(os.environ["EVAL_PROTOCOL"]))
def find(o, key):
    if isinstance(o, dict):
        if key in o: return o[key], True
        for v in o.values():
            r, ok = find(v, key)
            if ok: return r, True
    elif isinstance(o, list):
        for v in o:
            r, ok = find(v, key)
            if ok: return r, True
    return None, False
scope, ok = find(proto, "timing_scope")
if not ok: sys.exit("ERROR: sealed protocol has no timing_scope")
ids = inputs.get("ids") if isinstance(inputs, dict) else None
if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids):
    sys.exit("ERROR: EVAL_INPUTS.ids must be a non-empty list of strings")
kind = seeds.get("kind")
if kind == "paired_median":
    sl = seeds.get("seeds")
    if not isinstance(sl, list) or not sl or not all(isinstance(s, int) and not isinstance(s, bool) for s in sl):
        sys.exit("ERROR: paired_median EVAL_SEEDS.seeds must be a non-empty integer list")
elif kind == "deterministic":
    sl = [None]
else:
    sys.exit(f"ERROR: unsupported EVAL_SEEDS kind {kind!r}")
items = []
for n, iid in enumerate(ids):
    pid, kinds = iid, ["holo", "apo"]
    for sep in (":", "/"):
        if sep in iid and iid.rsplit(sep, 1)[1] in ("holo", "apo"):
            pid, k = iid.rsplit(sep, 1); kinds = [k]; break
    items.append({"input_id": iid, "pinder_id": pid, "kinds": kinds, "slot": f"in{n:03d}"})
json.dump({"timing_scope": scope, "seeds": sl, "items": items}, open(sys.argv[1], "w"), indent=2)
print(json.dumps({"timing_scope": scope, "seeds": sl, "n_inputs": len(items)}))
PY

# ------------------------------------------------------------------ untimed preprocess per input (published command)
NITEMS=$(python3 -I -c 'import json,sys;print(len(json.load(open(sys.argv[1]))["items"]))' "$PLAN")
for ((i = 0; i < NITEMS; i++)); do
  read -r SLOT PID KINDS < <(python3 -I -c 'import json,sys;it=json.load(open(sys.argv[1]))["items"][int(sys.argv[2])];print(it["slot"],it["pinder_id"],",".join(it["kinds"]))' "$PLAN" "$i")
  PREP="$EVAL_OUT/work/prep/$SLOT"
  if [ -f "$PREP/frodock_setup.csv" ] && [ -f "$PREP/.done_$KINDS" ]; then continue; fi
  rm -rf "$PREP"; mkdir -p "$PREP"
  for kind in ${KINDS//,/ }; do
    "$VPY" "$VENV/bin/pinder_methods" preprocess --method "$METHOD" --data_dir "$PREP" \
        --ids "[\"$PID\"]" --pairs "$kind"
    [ -f "$PREP/frodock_setup.csv" ] || { echo "ERROR: preprocess wrote no csv for $PID $kind" >&2; exit 1; }
    mv "$PREP/frodock_setup.csv" "$PREP/frodock_setup_$kind.csv"
  done
  "$VPY" - "$PREP" "$PID" ${KINDS//,/ } <<'PY'
import os, sys
import pandas as pd
prep, pid, kinds = sys.argv[1], sys.argv[2], sys.argv[3:]
df = pd.concat([pd.read_csv(os.path.join(prep, f"frodock_setup_{k}.csv")) for k in kinds], ignore_index=True)
if sorted(zip(df["id"], df["kind"])) != sorted((pid, k) for k in kinds):
    sys.exit(f"ERROR: {pid} has no {kinds} monomer pair in the PINDER index")
df.to_csv(os.path.join(prep, "frodock_setup.csv"), index=False)
PY
  touch "$PREP/.done_$KINDS"
done

# ------------------------------------------------------------------ seeds first, then inputs
RECS="$EVAL_OUT/work/records.$TS.jsonl"; : > "$RECS"
NSEEDS=$(python3 -I -c 'import json,sys;print(len(json.load(open(sys.argv[1]))["seeds"]))' "$PLAN")
for ((s = 0; s < NSEEDS; s++)); do
  SEED=$(python3 -I -c 'import json,sys;v=json.load(open(sys.argv[1]))["seeds"][int(sys.argv[2])];print("null" if v is None else v)' "$PLAN" "$s")
  export BASELINE_EVAL_SEED="$SEED"
  for ((i = 0; i < NITEMS; i++)); do
    read -r SLOT PID KINDS < <(python3 -I -c 'import json,sys;it=json.load(open(sys.argv[1]))["items"][int(sys.argv[2])];print(it["slot"],it["pinder_id"],",".join(it["kinds"]))' "$PLAN" "$i")
    RUN="$EVAL_OUT/work/$EVAL_MODE/seed_$SEED/$SLOT"
    RES="$RUN/results"
    rm -rf "$RUN"; mkdir -p "$RES"
    printf 'n_solutions: %s\nmpi_np: %s\nforce: %s\n' "$N_SOLUTIONS" "$MPI_NP" "$FORCE" > "$RUN/frodock_config.yaml"
    cp "$EVAL_OUT/work/prep/$SLOT/frodock_setup.csv" "$RES/frodock_setup.csv"
    echo "== seed=$SEED input=$PID kinds=$KINDS"
    T0=$(date +%s.%N)
    set +e
    "$VPY" "$VENV/bin/pinder_methods" predict --method "$METHOD" --data_dir "$EVAL_OUT/work/prep/$SLOT" \
        --results_dir "$RES" --subset pinder-s --pairs all --config "$RUN/frodock_config.yaml" > "$RUN/predict.log" 2>&1
    PRC=$?
    set -e
    T1=$(date +%s.%N)     # predict is a blocking CPU/MPI process tree; no device work outstanding
    cat "$RUN/predict.log"
    [ "$PRC" -eq 0 ] || { echo "ERROR: predict failed ($PRC) for $PID seed $SEED" >&2; exit "$PRC"; }
    set +e +o pipefail
    yes y | "$VPY" "$VENV/bin/pinder_eval" --eval_dir "$RES" --method_name "$METHOD" --max_workers "$EVAL_MAX_WORKERS" > "$RUN/eval.log" 2>&1
    ERC=${PIPESTATUS[1]}
    set -e -o pipefail
    tail -n 20 "$RUN/eval.log"
    [ "$ERC" -eq 0 ] || { echo "ERROR: pinder_eval failed ($ERC) for $PID seed $SEED" >&2; exit "$ERC"; }
    python3 -I - "$RES/frodock_metrics.csv" "$PLAN" "$i" "$SEED" "$T0" "$T1" "$RECS" <<'PY'
import csv, json, math, re, sys
mpath, plan, i, seed, t0, t1, recs = sys.argv[1:8]
it = json.load(open(plan))["items"][int(i)]
seed = None if seed == "null" else int(seed)
wall = float(t1) - float(t0)
rows = [r for r in csv.DictReader(open(mpath)) if r["id"] == it["pinder_id"]]
rank_re = re.compile(r"\d+(?=\D*$)")
def f(x):
    v = float(x)
    if not math.isfinite(v): raise ValueError(x)
    return v
metrics = {}
for kind in it["kinds"]:
    seen, recs_k = set(), []
    for r in rows:
        if r["monomer_name"] != kind or r["model_name"] in seen: continue
        if "pinder_set" in r and r["pinder_set"] not in ("", "pinder_s", "pinder_xl", "pinder_af2"): continue
        seen.add(r["model_name"])
        rank = r.get("rank") or rank_re.findall(r["model_name"])[-1]
        recs_k.append({"rank": int(float(rank)), "DockQ": f(r["DockQ"]), "iRMS": f(r["iRMS"]), "LRMS": f(r["LRMS"]),
                       "Fnat": f(r["Fnat"]), "penalty": r["model_name"].startswith("missing_decoy")})
    if not recs_k: sys.exit(f"ERROR: no metrics (not even the published penalty) for {it['pinder_id']} {kind}")
    recs_k.sort(key=lambda v: v["rank"])
    top, best = recs_k[0], max(recs_k, key=lambda v: v["DockQ"])
    p = f"{kind}_"
    metrics.update({p + "dockq_top1": top["DockQ"], p + "irms_top1": top["iRMS"], p + "fnat_top1": top["Fnat"],
                    p + "lrms_top1": top["LRMS"], p + "dockq_best": best["DockQ"], p + "irms_best": best["iRMS"],
                    p + "fnat_best": best["Fnat"], p + "lrms_best": best["LRMS"],
                    p + "acceptable_top1": float(top["DockQ"] >= 0.23), p + "acceptable_best": float(best["DockQ"] >= 0.23),
                    p + "n_decoys": float(0 if all(v["penalty"] for v in recs_k) else len(recs_k))})
metrics["docking_wall_s"] = wall
metrics["poses_per_s"] = sum(metrics[k + "_n_decoys"] for k in it["kinds"]) / wall if wall > 0 else 0.0
with open(recs, "a") as fh:
    fh.write(json.dumps({"input_id": it["input_id"], "seed": seed, "metrics": metrics}) + "\n")
print(json.dumps({"input_id": it["input_id"], "seed": seed, "metrics": metrics}))
PY
  done
done

python3 -I - "$PLAN" "$RECS" "$EVAL_OUT/evaluation.json" <<'PY'
import json, math, os, sys
plan = json.load(open(sys.argv[1]))
records = [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
want = len(plan["seeds"]) * len(plan["items"])
if len(records) != want: sys.exit(f"ERROR: {len(records)} records, expected {want}")
for r in records:
    for k, v in r["metrics"].items():
        if not isinstance(v, (int, float)) or not math.isfinite(v): sys.exit(f"ERROR: non-finite {k} in {r['input_id']}")
wall = sum(r["metrics"]["docking_wall_s"] for r in records)
budget = None
if os.environ.get("EVAL_MODE") == "curve":
    budget = float(os.environ["EVAL_COMPUTE_BUDGET"])
    used_gpu_s = 0.0 * wall      # gpu_count 0: the CPU/MPI baseline consumes no GPU seconds
    if used_gpu_s > budget: sys.exit("ERROR: GPU-second budget exceeded")
out = {"records": records, "timing_scope": plan["timing_scope"], "gpu_count": 0, "wall_s": wall, "compute_budget": budget}
json.dump(out, open(sys.argv[3], "w"), indent=2)
print(f"wrote {sys.argv[3]}: {len(records)} records, wall_s={wall:.1f}")
PY
echo "== run_evaluation.sh done $(date -u +%FT%TZ)"
