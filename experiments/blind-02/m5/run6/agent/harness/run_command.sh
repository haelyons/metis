#!/usr/bin/env bash
# run_command.sh - the canonical measured baseline command: the sealed s04
# timing-only calibration schedule of the published MEGADOCK binaries
# (3 arms x 4 apo cases x blocks 0-3, then diagnostic block D), serial,
# one job at a time, timed by a parent Python process (time.monotonic).
# Invoked from the working directory as: bash harness/run_command.sh
# Paths are relative to that directory; writes only under out/.
# CUDA_MPS_* variables are inherited unchanged. No telemetry is sampled here.
set -uo pipefail

if [[ ! -f harness/run_command.sh || ! -d baseline-published/megadock || ! -d data/inputs ]]; then
    echo "run_command.sh: run from the working directory containing harness/, baseline-published/ and data/" >&2
    exit 2
fi

# Complete published environment (brief: common environment for every invocation).
export OMP_NUM_THREADS=26
export OMP_DYNAMIC=FALSE
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export LC_ALL=C
export LANG=C
export CUDA_VISIBLE_DEVICES=0
export PYTHONHASHSEED=0

mkdir -p out
# Preserve any earlier attempt; output paths stay stable.
if [[ -e out/timing || -e out/timing_calibration.json || -e out/run_command.log ]]; then
    prev="out/attempts/$(date -u +%Y%m%dT%H%M%S.%NZ)"
    mkdir -p "$prev"
    for p in out/timing out/timing_calibration.json out/run_command.log; do
        [[ -e "$p" ]] && mv "$p" "$prev/"
    done
fi
mkdir -p out/timing

python3 -I - <<'PY' 2>&1 | tee out/run_command.log
import hashlib, json, math, os, signal, statistics, subprocess, sys, time

MD = "baseline-published/megadock"
SHARED = ["-N", "50", "-t", "1", "-v", "1.2", "-e", "1.0", "-d", "1.0", "-a", "-45.0", "-b", "1.0", "-f", "3"]
ARMS = {
    "cpu_standard": {"binary": "megadock", "extra": ["-r", "3600"], "rotations": 3600, "gpus": 0},
    "gpu_standard": {"binary": "megadock-gpu", "extra": ["-r", "3600"], "rotations": 3600, "gpus": 1},
    "gpu_dense": {"binary": "megadock-gpu", "extra": ["-D"], "rotations": 54000, "gpus": 1},
}
SHORT = {"cpu": "cpu_standard", "gpu": "gpu_standard", "dense": "gpu_dense"}
CASES = ["1aua", "1ax2", "1dv1", "1nr5"]
ORDERS = {
    "0": "cpu/1aua gpu/1ax2 dense/1dv1 cpu/1nr5 gpu/1aua dense/1ax2 cpu/1dv1 gpu/1nr5 dense/1aua cpu/1ax2 gpu/1dv1 dense/1nr5",
    "1": "dense/1aua cpu/1ax2 gpu/1dv1 dense/1nr5 cpu/1aua gpu/1ax2 dense/1dv1 cpu/1nr5 gpu/1aua dense/1ax2 cpu/1dv1 gpu/1nr5",
    "2": "gpu/1aua dense/1ax2 cpu/1dv1 gpu/1nr5 dense/1aua cpu/1ax2 gpu/1dv1 dense/1nr5 cpu/1aua gpu/1ax2 dense/1dv1 cpu/1nr5",
    "3": "cpu/1nr5 dense/1dv1 gpu/1ax2 cpu/1aua gpu/1nr5 dense/1ax2 cpu/1dv1 gpu/1aua dense/1nr5 cpu/1ax2 gpu/1dv1 dense/1aua",
}
ORDERS["D"] = ORDERS["1"]
BLOCKS = ["0", "1", "2", "3", "D"]
TIMEOUT_S = 600.0
EXPECTED_PREPARED = {
    "1aua": {"R": "162aad227fdbdb6a0600a5b6a4f5b461663ee7ce419798061ea0cd8ae9be6f35", "L": "f5158ee7030ce712cc5fb419d1e7532d4db2d4b4ddb64b50a5d0d9e45a973600"},
    "1ax2": {"R": "a9be54841e5e92e301558c198a7188b6765ab34cf30cb5d939b46f99db103d35", "L": "8d3948ddc69f493dfeea785aefc09f3de7b191ab7f8250dc102f63dc1d35810e"},
    "1dv1": {"R": "880a12d8a36e84fc8bea31cb4105284827ce1a985128413e4e8f70582fe52ea2", "L": "f9c72e23a1f2afe893c672da0412e82fa8345be23902d1d5cc7c17971193f623"},
    "1nr5": {"R": "ec52d962eacf8e92518ead142a51f6feb18e8d74590ea7048fffc461f52cacf2", "L": "83ad5cf3938c63172fea2254e31e6fe05d5751d072323ff7ed3463d92af0d1a2"},
}
E_HISTORICAL = {"1aua": 1.9728683570000385, "1ax2": 1.7721286510000027, "1dv1": 2.5732721009999295, "1nr5": 2.4245986219999622}
ENV_KEYS = ["OMP_NUM_THREADS", "OMP_DYNAMIC", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "LC_ALL", "LANG", "CUDA_VISIBLE_DEVICES"]

def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

t_run0 = time.monotonic()
wall_start = time.time()

# ---- preflight (outside W): binaries and prepared inputs
for b in ("megadock", "megadock-gpu", "decoygen"):
    if not os.access(os.path.join(MD, b), os.X_OK):
        sys.exit(f"RUN FAILED: missing executable {MD}/{b}; run setup first")
prepared_ok = True
prepared = {}
for c in CASES:
    for tag in ("R", "L"):
        p = f"data/inputs/{c}_{tag}.pdb"
        got = sha_file(p) if os.path.isfile(p) else None
        prepared[f"{c}_{tag}"] = {"sha256": got, "valid": got == EXPECTED_PREPARED[c][tag]}
        prepared_ok &= got == EXPECTED_PREPARED[c][tag]
if not prepared_ok:
    print(json.dumps(prepared, indent=1))
    sys.exit("RUN FAILED: prepared input hash mismatch; the run stops before docking")
binary_sha = {b: sha_file(os.path.join(MD, b)) for b in ("megadock", "megadock-gpu", "decoygen")}

config = {"env": {k: os.environ.get(k) for k in ENV_KEYS}, "shared_args": SHARED,
          "arms": {a: {"binary": f"{MD}/{v['binary']}", "args": SHARED + v["extra"]} for a, v in ARMS.items()},
          "timeout_s": TIMEOUT_S, "blocks": BLOCKS, "orders": ORDERS}
print("CONFIG " + json.dumps(config, sort_keys=True), flush=True)

def read_inventory(path):
    inv, chains = [], set()
    with open(path, "rb") as fh:
        for line in fh:
            rec = line[:6].rstrip()
            if rec in (b"ATOM", b"HETATM"):
                body = line.rstrip(b"\r\n")
                inv.append((rec, body[12:27]))
                if len(body) > 21:
                    chains.add(body[21:22])
    return inv, chains

INV = {}
for c in CASES:
    r_inv, _ = read_inventory(f"data/inputs/{c}_R.pdb")
    l_inv, _ = read_inventory(f"data/inputs/{c}_L.pdb")
    INV[c] = sorted(r_inv + l_inv)

import re
NUM = r"([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)"

def validate_docking(job_dir, arm, log_text, printed):
    """Return list of problems (empty = valid)."""
    probs = []
    try:
        lines = open(os.path.join(job_dir, "docking.out")).read().splitlines()
    except OSError as e:
        return [f"docking.out unreadable: {e}"]
    lines = [l for l in lines if l.strip()]
    if len(lines) != 54:
        probs.append(f"docking.out has {len(lines)} non-empty lines, expected 4+50")
    if lines:
        h = lines[0].split()
        try:
            if not (int(float(h[0])) > 0 and abs(float(h[1]) - 1.2) < 1e-9):
                probs.append(f"header grid/voxel invalid: {lines[0]!r}")
        except (IndexError, ValueError):
            probs.append(f"header line 1 unparsable: {lines[0]!r}")
    for i, l in enumerate(lines[4:54]):
        f = l.split()
        try:
            ok = len(f) == 7 and all(math.isfinite(float(x)) for x in f)
        except ValueError:
            ok = False
        if not ok:
            probs.append(f"row {i+1} not 7 finite fields: {l!r}")
            break
    want = ARMS[arm]
    def values(keyword):
        out = []
        for l in log_text.splitlines():
            if re.search(keyword, l, flags=re.I):
                for x in re.findall(NUM, l):
                    try:
                        v = float(x)
                    except ValueError:
                        continue
                    if v == int(v):
                        out.append(int(v))
        return out
    rot = values(r"rotation|angle")
    thr = values(r"thread")
    gpu_lines = [l for l in log_text.splitlines() if re.search(r"gpu", l, flags=re.I)]
    gpu = values(r"gpu")
    printed["rotations"], printed["threads"], printed["gpus"] = sorted(set(rot)), sorted(set(thr)), sorted(set(gpu))
    if want["rotations"] not in rot:
        probs.append(f"printed rotation count {sorted(set(rot))} lacks {want['rotations']}")
    if 26 not in thr:
        probs.append(f"printed thread count {sorted(set(thr))} lacks 26")
    if want["gpus"] == 0:
        if gpu_lines and 0 not in gpu:
            probs.append(f"printed GPU count {sorted(set(gpu))} lacks 0")
        if not gpu_lines:
            printed["gpu_note"] = "CPU binary printed no GPU line (no GPU in use)"
    elif want["gpus"] not in gpu:
        probs.append(f"printed GPU count {sorted(set(gpu))} lacks {want['gpus']}")
    return probs

def parse_elapsed(log_text):
    ms = re.findall(r"elapsed time\s*[=:]?\s*" + NUM, log_text, flags=re.I)
    return float(ms[-1]) if ms else None

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

def strip_end(data, drop):
    keep = []
    for line in data.splitlines(keepends=True):
        if line[:6].rstrip() in drop:
            continue
        if not line.endswith(b"\n"):
            line += b"\n"
        keep.append(line)
    return b"".join(keep)

def run_job(block, idx, arm, case):
    job = f"out/timing/block_{block}/{arm}/{case}"
    if os.path.exists(job):
        raise SystemExit(f"RUN FAILED: job directory {job} already exists; never overwritten")
    os.makedirs(job)
    a = ARMS[arm]
    argv = [f"{MD}/{a['binary']}", "-R", f"data/inputs/{case}_R.pdb", "-L", f"data/inputs/{case}_L.pdb",
            "-o", f"{job}/docking.out"] + SHARED + a["extra"]
    rec = {"block": block, "order_index": idx, "arm": arm, "case": case, "status": None,
           "W_s": None, "D_s": None, "P_s": None, "R_s": None, "lower_bound_s": None,
           "docking_out_sha256": None, "argv": argv, "job_dir": job, "problems": [], "printed": {}}
    rec_bytes = strip_end(open(f"data/inputs/{case}_R.pdb", "rb").read(), (b"END",))
    dlog = open(f"{job}/docking.log", "wb")
    glog = open(f"{job}/decoygen.log", "wb")
    t0 = time.monotonic()                      # W starts: immediately before docking process creation
    deadline = t0 + TIMEOUT_S
    try:
        rc = run_proc(argv, dlog, deadline)
        t_d = time.monotonic()
        rec["D_s"] = t_d - t0
        dlog.close()
        log_text = open(f"{job}/docking.log", errors="replace").read()
        rec["P_s"] = parse_elapsed(log_text)
        if rc != 0:
            rec["status"] = "failed"
            rec["problems"].append(f"docking exit status {rc}")
        else:
            probs = validate_docking(job, arm, log_text, rec["printed"])
            if probs:
                rec["status"] = "invalid_output"
                rec["problems"] += probs
        if rec["status"] is None:
            r0 = time.monotonic()
            for rank in range(1, 51):
                lig = f"{job}/ligand_{rank}.pdb"
                grc = run_proc([f"{MD}/decoygen", lig, f"data/inputs/{case}_L.pdb", f"{job}/docking.out", str(rank)], glog, deadline)
                if grc != 0 or not os.path.isfile(lig):
                    rec["status"] = "failed"
                    rec["problems"].append(f"decoygen rank {rank} exit status {grc}")
                    break
                lig_bytes = strip_end(open(lig, "rb").read(), (b"END", b"ENDMDL"))
                with open(f"{job}/model_{rank}.pdb", "wb") as fh:
                    fh.write(rec_bytes + lig_bytes + b"END\n")
                if time.monotonic() > deadline:
                    raise Timeout()
            rec["R_s"] = time.monotonic() - r0
        if rec["status"] is None:
            for rank in range(1, 51):
                mp = f"{job}/model_{rank}.pdb"
                if not os.path.isfile(mp) or os.path.getsize(mp) == 0:
                    rec["problems"].append(f"model_{rank} missing or empty")
                    break
                inv, chains = read_inventory(mp)
                if chains != {b"R", b"L"}:
                    rec["problems"].append(f"model_{rank} chains {sorted(x.decode() for x in chains)} != R,L")
                    break
                if sorted(inv) != INV[case]:
                    rec["problems"].append(f"model_{rank} ATOM/HETATM inventory differs from receptor+ligand inputs")
                    break
            if rec["problems"]:
                rec["status"] = "invalid_output"
        t_end = time.monotonic()               # W ends: all models written, closed and validated
        if rec["status"] is None:
            rec["status"] = "complete"
            rec["W_s"] = t_end - t0
        if time.monotonic() > deadline and rec["status"] == "complete":
            rec["status"], rec["W_s"], rec["lower_bound_s"] = "timeout", None, t_end - t0
    except Timeout:
        rec["status"] = "timeout"
        rec["lower_bound_s"] = time.monotonic() - t0
        rec["problems"].append(f"per-job timeout {TIMEOUT_S} s; process group killed")
    finally:
        if not dlog.closed:
            dlog.close()
        glog.close()
    if os.path.isfile(f"{job}/docking.out"):
        rec["docking_out_sha256"] = sha_file(f"{job}/docking.out")
    rec["docking_log_sha256"] = sha_file(f"{job}/docking.log")
    with open(f"{job}/job_record.json", "w") as fh:
        json.dump(rec, fh, indent=1)
    print("JOB " + json.dumps({k: rec[k] for k in ("block", "order_index", "arm", "case", "status", "W_s", "D_s", "P_s", "R_s", "lower_bound_s")}), flush=True)
    if rec["problems"]:
        print("   problems: " + "; ".join(rec["problems"]), flush=True)
    return rec

records = []
block_walls = {}
for block in BLOCKS:
    if block == "D":
        # Marker for the anchors wrapper's block-D nvidia-smi sampling (not sampled here).
        with open("out/timing/block_D.started", "w") as fh:
            fh.write(f"{time.time()}\n")
        time.sleep(2.0)  # gap before block D so external 1 s sampling covers the whole block
    b0 = time.monotonic()
    for idx, tok in enumerate(ORDERS[block].split()):
        arm_s, case = tok.split("/")
        records.append(run_job(block, idx, SHORT[arm_s], case))
    block_walls[block] = time.monotonic() - b0
    if block == "D":
        time.sleep(2.0)
        with open("out/timing/block_D.finished", "w") as fh:
            fh.write(f"{time.time()}\n")

summary = {}
for c in CASES:
    for a in ARMS:
        ws = [r["W_s"] for r in records if r["case"] == c and r["arm"] == a and r["block"] in ("1", "2", "3")]
        all_ok = len(ws) == 3 and all(w is not None for w in ws)
        summary.setdefault(c, {})[a] = {
            "W_blocks_1_3": ws,
            "max_W_s": max(ws) if all_ok else None,
            "median_W_s": statistics.median(ws) if all_ok else None,
            "complete": all_ok,
        }
primary = [r for r in records if r["block"] in ("0", "1", "2", "3")]
setup_rec = None
if os.path.isfile("data/setup_record.json"):
    setup_rec = json.load(open("data/setup_record.json"))
out = {
    "protocol_identity": {
        "brief_section": "## Calibration request (science step s04) .. end of brief.md",
        "section_sha256": "57699e1f29006aa9bfdad6af3e153409b7f8fc4b793b39167fc09a05c0c2b6aa",
        "brief_sha256": "23101d088a8552bf69dbb3c8944cdec01af4b959a0686778499a8069b11707cb",
    },
    "scope": "timing-only; no native access; no cross-arm comparison",
    "pins": (setup_rec or {}).get("pins") or {"megadock_commit_expected": "9575280c875732553266e26adc607dd892b02616"},
    "binary_sha256": binary_sha,
    "binary_sha256_setup": (setup_rec or {}).get("binary_sha256"),
    "host": (setup_rec or {}).get("host"),
    "cuda": (setup_rec or {}).get("cuda"),
    "versions": (setup_rec or {}).get("versions"),
    "setup_checks": (setup_rec or {}).get("setup_checks"),
    "prepared_inputs_run_check": {"valid": prepared_ok, "files": prepared},
    "config": config,
    "jobs": records,
    "evaluator_reserves_E_historical": {"label": "historical (blind-02 m5 run4 CPU-standard evaluator walls), copied verbatim from the brief; not measured here", "E_s": E_HISTORICAL},
    "W_summary_blocks_1_3": summary,
    "validity": {
        "primary_jobs": len(primary),
        "primary_complete_valid": sum(r["status"] == "complete" for r in primary),
        "all_primary_complete": len(primary) == 48 and all(r["status"] == "complete" for r in primary),
        "status_counts": {s: sum(r["status"] == s for r in records) for s in ("complete", "failed", "invalid_output", "timeout")},
    },
    "stage_walls_s": {"setup": ((setup_rec or {}).get("stage_walls_s") or {}).get("setup"),
                      "run_command": time.monotonic() - t_run0, "blocks": block_walls},
    "wall_clock_start_unix": wall_start,
}
with open("out/timing_calibration.json", "w") as fh:
    json.dump(out, fh, indent=1)
print("SUMMARY " + json.dumps(out["validity"]), flush=True)
bad = [r for r in records if r["status"] in ("failed", "invalid_output")]
sys.exit(3 if bad else 0)
PY
status=${PIPESTATUS[0]}
echo "run_command exit status $status" | tee -a out/run_command.log
exit "$status"
