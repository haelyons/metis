#!/usr/bin/env bash
# run_anchors.sh - run the canonical measured command (harness/run_command.sh,
# unchanged environment) at the sealed representative scale, sample block-D GPU
# telemetry from outside it, validate its saved output and write
# out/anchors_measured.json. The intake publishes no anchors or references
# (anchors.json == []), so the measured map is {}.
# Invoked from the working directory as: bash harness/run_anchors.sh
# CUDA_MPS_* variables are inherited unchanged.
set -uo pipefail

if [[ ! -f harness/run_command.sh ]]; then
    echo "run_anchors.sh: run from the working directory as 'bash harness/run_anchors.sh'" >&2
    exit 2
fi
if [[ -n "${EVAL_MODE:-}" && "${EVAL_MODE}" != "anchors" ]]; then
    exec bash harness/run_evaluation.sh
fi

mkdir -p out
ALOG=out/run_anchors.log
if [[ -f "$ALOG" ]]; then
    mv "$ALOG" "out/run_anchors.$(date -u +%Y%m%dT%H%M%S.%NZ).prev.log"
fi
exec > >(tee -a "$ALOG") 2>&1
echo "== run_anchors start $(date -u +%FT%TZ)"
T0=$(date +%s.%N)
LAUNCH_EPOCH=$(date +%s.%N)

bash harness/run_command.sh &
CMD_PID=$!

# Block-D telemetry: nvidia-smi at 1 s while block D runs (outside the measured command).
SMI_PID=""
started_fresh() {
    [[ -f out/timing/block_D.started ]] || return 1
    python3 -I -c "import sys; sys.exit(0 if float(open('out/timing/block_D.started').read().split()[0]) >= float(sys.argv[1]) else 1)" "$LAUNCH_EPOCH" 2>/dev/null
}
while kill -0 "$CMD_PID" 2>/dev/null; do
    if [[ -z "$SMI_PID" ]] && started_fresh; then
        nvidia-smi -i 0 --query-gpu=timestamp,utilization.gpu,memory.used --format=csv -l 1 \
            > out/timing/gpu_telemetry.csv 2> out/timing/gpu_telemetry.err &
        SMI_PID=$!
        echo "block D telemetry started (pid $SMI_PID)"
    fi
    if [[ -n "$SMI_PID" && -f out/timing/block_D.finished ]]; then
        break
    fi
    sleep 0.2
done
wait "$CMD_PID"
CMD_STATUS=$?
if [[ -n "$SMI_PID" ]]; then
    kill "$SMI_PID" 2>/dev/null || true
    wait "$SMI_PID" 2>/dev/null || true
    echo "block D telemetry stopped"
fi
echo "run_command.sh exit status $CMD_STATUS"
T1=$(date +%s.%N)

python3 -I - "$T0" "$T1" "$CMD_STATUS" <<'PY'
import json, math, os, sys

ITEM_IDS = []   # intake anchors.json is [] : no anchors, no references
problems = []

expected_env = {"OMP_NUM_THREADS": "26", "OMP_DYNAMIC": "FALSE", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                "NUMEXPR_NUM_THREADS": "1", "LC_ALL": "C", "LANG": "C", "CUDA_VISIBLE_DEVICES": "0"}
shared = ["-N", "50", "-t", "1", "-v", "1.2", "-e", "1.0", "-d", "1.0", "-a", "-45.0", "-b", "1.0", "-f", "3"]
expected_arms = {
    "cpu_standard": {"binary": "baseline-published/megadock/megadock", "args": shared + ["-r", "3600"]},
    "gpu_standard": {"binary": "baseline-published/megadock/megadock-gpu", "args": shared + ["-r", "3600"]},
    "gpu_dense": {"binary": "baseline-published/megadock/megadock-gpu", "args": shared + ["-D"]},
}

cfg = None
try:
    for line in open("out/run_command.log", errors="replace"):
        if line.startswith("CONFIG "):
            cfg = json.loads(line[7:])
except OSError as e:
    problems.append(f"out/run_command.log missing: {e}")
if cfg is None:
    problems.append("no CONFIG line in out/run_command.log")
else:
    if cfg.get("env") != expected_env:
        problems.append(f"printed environment {cfg.get('env')} != published {expected_env}")
    if cfg.get("arms") != expected_arms:
        problems.append("printed arm commands differ from the published configuration")

data = None
try:
    data = json.load(open("out/timing_calibration.json"))
except (OSError, ValueError) as e:
    problems.append(f"out/timing_calibration.json missing or invalid: {e}")
if data is not None:
    jobs = data.get("jobs", [])
    if len(jobs) != 60:
        problems.append(f"{len(jobs)} job records, expected 60 (48 primary + 12 block D)")
    for j in jobs:
        if j.get("argv", [None])[0] != expected_arms.get(j.get("arm"), {}).get("binary") or \
           j.get("argv", [])[7:] != expected_arms.get(j.get("arm"), {}).get("args"):
            problems.append(f"job {j.get('block')}/{j.get('arm')}/{j.get('case')} argv differs from published configuration")
            break
        if j.get("status") == "complete" and not (isinstance(j.get("W_s"), (int, float)) and math.isfinite(j["W_s"])):
            problems.append(f"job {j.get('block')}/{j.get('arm')}/{j.get('case')} complete without finite W_s")
            break
    tel = "out/timing/gpu_telemetry.csv"
    nrows = 0
    if os.path.isfile(tel):
        nrows = max(0, sum(1 for l in open(tel) if l.strip()) - 1)
    data["gpu_telemetry_block_D"] = {"path": tel, "samples": nrows, "interval_s": 1,
                                     "fields": "timestamp, utilization.gpu, memory.used"}
    if nrows == 0:
        problems.append("block D GPU telemetry is missing or empty")
    sw = data.setdefault("stage_walls_s", {})
    sw["run_anchors"] = float(sys.argv[2]) - float(sys.argv[1])
    with open("out/timing_calibration.json", "w") as fh:
        json.dump(data, fh, indent=1)
    print("validity:", json.dumps(data.get("validity")))

measured = {}
for item in ITEM_IDS:
    problems.append(f"no measurement parser for intake item {item}")
with open("out/anchors_measured.json", "w") as fh:
    json.dump(measured, fh)
print("wrote out/anchors_measured.json:", json.dumps(measured))
if problems:
    print("ANCHORS OUTPUT PROBLEMS:\n  " + "\n  ".join(problems))
    sys.exit(4)
PY
PSTATUS=$?
echo "== run_anchors end $(date -u +%FT%TZ)"
if [[ $CMD_STATUS -ne 0 ]]; then exit "$CMD_STATUS"; fi
exit "$PSTATUS"
