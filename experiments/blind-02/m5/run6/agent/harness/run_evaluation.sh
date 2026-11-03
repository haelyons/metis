#!/usr/bin/env bash
# run_evaluation.sh - published-baseline evaluation adapter for MEGADOCK 9575280c.
# Invoked from a fresh working directory (baseline-published/, method/, data/,
# harness/, payload/ links) as: bash harness/run_evaluation.sh
# Env: EVAL_MODE (equivalence|warmup|performance|curve), EVAL_PROTOCOL (sealed JSON
# path), EVAL_INPUTS, EVAL_SEEDS (JSON), EVAL_OUT, EVAL_COMPUTE_BUDGET (curve only),
# BASELINE_DIR, METHOD_DIR, BASELINE_OUT, METHOD_OUT.
# Runs the published configuration (same binaries, args and environment as
# harness/run_command.sh) on every sealed input/seed, seeds first then input IDs,
# and writes EVAL_OUT/evaluation.json. CUDA_MPS_* variables are inherited unchanged.
set -uo pipefail

: "${EVAL_OUT:?EVAL_OUT must be set}"
: "${EVAL_PROTOCOL:?EVAL_PROTOCOL must be set}"
: "${EVAL_INPUTS:?EVAL_INPUTS must be set}"
: "${EVAL_SEEDS:?EVAL_SEEDS must be set}"
EVAL_MODE=${EVAL_MODE:-performance}
EVAL_COMPUTE_BUDGET=${EVAL_COMPUTE_BUDGET:-}
case "$EVAL_MODE" in equivalence|warmup|performance|curve) ;; *) echo "unknown EVAL_MODE=$EVAL_MODE" >&2; exit 2;; esac
if [[ ! -d baseline-published/megadock || ! -d data/inputs ]]; then
    echo "run_evaluation.sh: baseline-published/megadock or data/inputs missing in $(pwd)" >&2
    exit 2
fi

# Published environment (identical to run_command.sh).
export OMP_NUM_THREADS=26
export OMP_DYNAMIC=FALSE
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export LC_ALL=C
export LANG=C
export CUDA_VISIBLE_DEVICES=0

mkdir -p "$EVAL_OUT"
ELOG="$EVAL_OUT/run_evaluation.$EVAL_MODE.log"
[[ -f "$ELOG" ]] && mv "$ELOG" "$ELOG.$(date -u +%Y%m%dT%H%M%S.%NZ).prev"

python3 -I - <<'PY' 2>&1 | tee "$ELOG"
import hashlib, json, math, os, re, signal, subprocess, sys, time

MD = "baseline-published/megadock"
SHARED = ["-N", "50", "-t", "1", "-v", "1.2", "-e", "1.0", "-d", "1.0", "-a", "-45.0", "-b", "1.0", "-f", "3"]
ARMS = {
    "cpu_standard": {"binary": "megadock", "extra": ["-r", "3600"], "gpus": 0},
    "gpu_standard": {"binary": "megadock-gpu", "extra": ["-r", "3600"], "gpus": 1},
    "gpu_dense": {"binary": "megadock-gpu", "extra": ["-D"], "gpus": 1},
}
CASES = ["1aua", "1ax2", "1dv1", "1nr5"]
TIMEOUT_S = 600.0

mode = os.environ["EVAL_MODE"]
out_dir = os.environ["EVAL_OUT"]
protocol = json.load(open(os.environ["EVAL_PROTOCOL"]))
inputs = json.loads(os.environ["EVAL_INPUTS"])
seeds_spec = json.loads(os.environ["EVAL_SEEDS"])
ids = list(inputs["ids"])
if seeds_spec.get("kind") == "paired_median":
    seeds = [int(s) for s in seeds_spec["seeds"]]
elif seeds_spec.get("kind") == "deterministic":
    seeds = [None]
else:
    sys.exit(f"unsupported EVAL_SEEDS kind {seeds_spec.get('kind')!r}")

def find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find_key(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_key(v, key)
            if r is not None:
                return r
    return None

timing_scope = find_key(protocol, "timing_scope")
if timing_scope is None:
    sys.exit("EVAL_PROTOCOL has no timing_scope")
budget = None
if mode == "curve":
    raw = os.environ.get("EVAL_COMPUTE_BUDGET", "").strip()
    if not raw:
        sys.exit("curve mode requires EVAL_COMPUTE_BUDGET (GPU seconds)")
    try:
        budget = float(json.loads(raw)) if not raw.startswith("{") else float(json.loads(raw).get("gpu_seconds"))
    except (ValueError, TypeError):
        sys.exit(f"invalid EVAL_COMPUTE_BUDGET {raw!r}")

def resolve(input_id):
    """Map a sealed input identity to (case prefix, [arms])."""
    lid = input_id.lower()
    case = next((c for c in CASES if c in lid), None)
    if case is None:
        sys.exit(f"input_id {input_id!r} names none of the cases {CASES}")
    arms = [a for a in ARMS if a in lid]
    if not arms:
        pa = find_key(protocol, "arm") or find_key(protocol, "configuration")
        if isinstance(pa, str) and pa in ARMS:
            arms = [pa]
        elif isinstance(pa, list) and all(isinstance(x, str) and x in ARMS for x in pa) and pa:
            arms = list(pa)
        else:
            arms = list(ARMS)
    return case, arms

def sha_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()

def inventory(path):
    inv, chains = [], set()
    with open(path, "rb") as fh:
        for line in fh:
            rec = line[:6].rstrip()
            if rec in (b"ATOM", b"HETATM"):
                body = line.rstrip(b"\r\n")
                inv.append((rec, body[12:27]))
                chains.add(body[21:22])
    return sorted(inv), chains

def strip_end(data, drop):
    keep = []
    for line in data.splitlines(keepends=True):
        if line[:6].rstrip() in drop:
            continue
        keep.append(line if line.endswith(b"\n") else line + b"\n")
    return b"".join(keep)

class Timeout(Exception):
    pass

def run_proc(argv, log_fh, deadline):
    p = subprocess.Popen(argv, stdout=log_fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        return p.wait(timeout=max(0.001, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        p.wait()
        raise Timeout()

def run_job(job, arm, case):
    os.makedirs(job, exist_ok=False)
    a = ARMS[arm]
    argv = [f"{MD}/{a['binary']}", "-R", f"data/inputs/{case}_R.pdb", "-L", f"data/inputs/{case}_L.pdb",
            "-o", f"{job}/docking.out"] + SHARED + a["extra"]
    rec_bytes = strip_end(open(f"data/inputs/{case}_R.pdb", "rb").read(), (b"END",))
    want_inv = sorted(inventory(f"data/inputs/{case}_R.pdb")[0] + inventory(f"data/inputs/{case}_L.pdb")[0])
    m = {}
    with open(f"{job}/docking.log", "wb") as dlog, open(f"{job}/decoygen.log", "wb") as glog:
        t0 = time.monotonic()
        deadline = t0 + TIMEOUT_S
        try:
            rc = run_proc(argv, dlog, deadline)
            m["D_s"] = time.monotonic() - t0
            if rc != 0:
                raise RuntimeError(f"{arm}/{case}: docking exit status {rc}")
            rows = [l.split() for l in open(f"{job}/docking.out").read().splitlines() if l.strip()][4:]
            if len(rows) != 50 or any(len(r) != 7 or not all(math.isfinite(float(x)) for x in r) for r in rows):
                raise RuntimeError(f"{arm}/{case}: docking.out does not hold 50 rows of 7 finite fields")
            r0 = time.monotonic()
            for rank in range(1, 51):
                lig = f"{job}/ligand_{rank}.pdb"
                grc = run_proc([f"{MD}/decoygen", lig, f"data/inputs/{case}_L.pdb", f"{job}/docking.out", str(rank)], glog, deadline)
                if grc != 0 or not os.path.isfile(lig):
                    raise RuntimeError(f"{arm}/{case}: decoygen rank {rank} exit status {grc}")
                with open(f"{job}/model_{rank}.pdb", "wb") as fh:
                    fh.write(rec_bytes + strip_end(open(lig, "rb").read(), (b"END", b"ENDMDL")) + b"END\n")
            m["R_s"] = time.monotonic() - r0
            for rank in range(1, 51):
                inv, chains = inventory(f"{job}/model_{rank}.pdb")
                if inv != want_inv or chains != {b"R", b"L"}:
                    raise RuntimeError(f"{arm}/{case}: model_{rank} inventory/chains invalid")
            m["W_s"] = time.monotonic() - t0
        except Timeout:
            raise RuntimeError(f"{arm}/{case}: timeout after {TIMEOUT_S} s (process group killed)")
    log = open(f"{job}/docking.log", errors="replace").read()
    el = re.findall(r"elapsed time\s*[=:]?\s*([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)", log, flags=re.I)
    if el:
        m["P_s"] = float(el[-1])
    m["top1_score"] = float(rows[0][6])
    m["top50_score_sum"] = sum(float(r[6]) for r in rows)
    m["valid"] = 1.0
    return m, a["gpus"]

records = []
gpu_used_s = 0.0
stopped_by_budget = False
t_start = time.monotonic()
for seed in seeds:
    for input_id in ids:
        case, arms = resolve(input_id)
        metrics = {}
        for arm in arms:
            if budget is not None and ARMS[arm]["gpus"] and gpu_used_s >= budget:
                stopped_by_budget = True
                break
            sd = "null" if seed is None else str(seed)
            job = os.path.join(out_dir, "jobs", f"seed_{sd}", re.sub(r"[^A-Za-z0-9._-]", "_", input_id), arm)
            m, ngpu = run_job(job, arm, case)
            gpu_used_s += m["W_s"] * ngpu
            for k, v in m.items():
                metrics[k if len(arms) == 1 else f"{arm}.{k}"] = v
        if stopped_by_budget:
            break
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in metrics.values()):
            sys.exit(f"non-finite metric for {input_id}")
        records.append({"input_id": input_id, "seed": seed, "metrics": metrics})
        print("RECORD " + json.dumps(records[-1]), flush=True)
    if stopped_by_budget:
        break
# Every GPU process has exited (and thus synchronized) before the timer stops.
wall_s = time.monotonic() - t_start
result = {"records": records, "timing_scope": timing_scope, "gpu_count": 1, "wall_s": wall_s,
          "mode": mode, "compute_budget": None}
if budget is not None:
    result["compute_budget"] = {"unit": "gpu_seconds", "limit": budget, "used": gpu_used_s,
                                "stopped_by_budget": stopped_by_budget}
with open(os.path.join(out_dir, "evaluation.json"), "w") as fh:
    json.dump(result, fh, indent=1)
print(f"wrote {out_dir}/evaluation.json with {len(records)} records, wall_s={wall_s:.3f}")
PY
status=${PIPESTATUS[0]}
echo "run_evaluation exit status $status" | tee -a "$ELOG"
exit "$status"
