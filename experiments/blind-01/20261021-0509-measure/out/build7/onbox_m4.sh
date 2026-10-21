#!/usr/bin/env bash
# What runs on the rented box, in order, with every guard the run needs.
#
# This script does four things and nothing else:
#   1. works out when the run must stop, from the price, the budget and the
#      timeout the launcher forwards, counting the time the box spent booting;
#   2. installs the declared system packages and builds a private python
#      environment, with no prompt and no upgrade of anything preinstalled;
#   3. starts the measuring program under a timer that always fires before the
#      launcher's own, so this script is the one that writes the last word;
#   4. leaves a marker saying what happened, whatever happened.
#
# Everything it writes goes under results_m4/out/, which is the directory the
# launcher fetches. Nothing is written anywhere else.
#
# Exit codes, which the marker repeats:
#   0  every stage finished
#   2  broken infrastructure, or the timing harness itself proved untrustworthy
#   3  a guard, a stage ceiling or a timeout stopped the run short
#   4  the anchor redocking missed the published placement
#
#   usage:  bash remote_run_m4.sh bash onbox_m4.sh

set -uo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$RUN_DIR"
OUT="$RUN_DIR/results_m4/out"
mkdir -p "$OUT"
LOG="$OUT/onbox_m4.log"

say() { echo "[onbox] $(date -u +%H:%M:%S) $*" | tee -a "$LOG"; }

# ---------------------------------------------------------------------------
# 1. When must this stop?
#
# The launcher forwards the price, what is left of the budget and the whole
# box lifetime it enforces. Each is read through a default, and no default is
# ever looser than the caps the run was approved under.
# ---------------------------------------------------------------------------

PRICE_USD_PER_HOUR="${PRICE_USD_PER_HOUR:-1.99}"
BUDGET_LEFT_USD="${BUDGET_LEFT_USD:-5}"
BOOTSTRAP_ASSUMED=0
if [ -n "${REMOTE_TIMEOUT:-}" ]; then
  REMOTE_TIMEOUT_SEEN="$REMOTE_TIMEOUT"
  TIMEOUT_NOTE="forwarded by the launcher"
else
  REMOTE_TIMEOUT_SEEN=7200
  TIMEOUT_NOTE="REMOTE_TIMEOUT not forwarded; default 7200 used"
fi
# Never above the approved caps, whatever arrives in the environment.
awk_le() { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a+0<=b+0)}'; }
awk_le "$REMOTE_TIMEOUT_SEEN" 7200 || REMOTE_TIMEOUT_SEEN=7200
awk_le "$BUDGET_LEFT_USD" 5 || BUDGET_LEFT_USD=5

# The clock starts when the box started working, not when this line runs. The
# bootstrap that launched this script has been running for some seconds
# already, and those seconds are billed. Thirty seconds is added for the box's
# own start-up before that bootstrap.
PRE_T0="$(ps -o etimes= -p "$PPID" 2>/dev/null | tr -dc '0-9')"
if [ -z "$PRE_T0" ]; then
  PRE_T0=300
  BOOTSTRAP_ASSUMED=1
  say "bootstrap time unreadable; assuming 300 s"
else
  PRE_T0=$((PRE_T0 + 30))
fi
NOW_EPOCH="$(date -u +%s)"
T0_EPOCH=$((NOW_EPOCH - PRE_T0))
export M4_T0_EPOCH="$T0_EPOCH"
export M4_PRE_T0_SECONDS="$PRE_T0"
export M4_BOOTSTRAP_ASSUMED="$BOOTSTRAP_ASSUMED"
export REMOTE_TIMEOUT="$REMOTE_TIMEOUT_SEEN"
export PRICE_USD_PER_HOUR BUDGET_LEFT_USD

# The money cap and the clock cap, whichever comes first.
STOP_AT="$(awk -v t="$REMOTE_TIMEOUT_SEEN" -v b="$BUDGET_LEFT_USD" \
               -v p="$PRICE_USD_PER_HOUR" \
               'BEGIN{d=(p>0)?b/p*3600:t; print (d<t)?int(d):int(t)}')"
say "price $PRICE_USD_PER_HOUR/h, budget $BUDGET_LEFT_USD, timeout ${REMOTE_TIMEOUT_SEEN}s"
say "bootstrap already used ${PRE_T0}s; the run must stop ${STOP_AT}s after that start"

# ---------------------------------------------------------------------------
# 2. The marker, armed before anything can fail.
#
# The trap is set here, before the environment is built, so that an abort in
# the install still leaves a record, a validity file and a marker behind. A
# run that dies silently is indistinguishable from a run that was never
# started, and that has cost real money before.
# ---------------------------------------------------------------------------

FINISHED=0
write_minimal_void() {
  local code="$1" reason="$2"
  python3 - "$OUT" "$code" "$reason" <<'PY' || true
import json, os, sys, time
out, code, reason = sys.argv[1], int(sys.argv[2]), sys.argv[3]
os.makedirs(out, exist_ok=True)
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
inputs = {c: {"status": "unmeasured_by_a_stop", "decision": "VOID",
              "stop": reason} for c in ("C1", "C2", "C3", "C4")}
for cid in ("C1", "C2", "C3", "C4"):
    path = os.path.join(out, "endpoint-%s_tag-m4.json" % cid)
    if os.path.exists(path):
        continue
    json.dump({
        "cell": {"stage": "endpoints", "input": cid, "tag": "m4"},
        "inputs": [], "metric": "not measured: the run ended before this stage",
        "values": {"measured": None, "void_reason":
                   "unmeasured, not holding (%s)" % reason},
        "threshold": {},
        "decision_rule": "an input the run never reached is VOID, never holding",
        "decision": "VOID", "run_valid": False, "run_valid_voided_by": reason,
        "notes_list": ["incomplete run: unmeasured inputs are VOID, not holding"],
        "env": {"timestamp_utc": now}, "tag": "m4",
    }, open(path, "w"), indent=2)
json.dump({"run_valid": False, "voided_by": reason, "stopped": True,
           "inputs_status": inputs, "tag": "m4"},
          open(os.path.join(out, "RUN_VALID.json"), "w"), indent=2)
json.dump({"exit_code": code, "run_valid": False, "voided_by": reason,
           "stopped_by": [reason], "inputs": inputs, "tag": "m4",
           "finished_utc": now},
          open(os.path.join(out, "RUN_DONE"), "w"), indent=2)
PY
}

on_exit() {
  local code=$?
  if [ "$FINISHED" = "0" ]; then
    say "aborted before the measuring program finished (shell code $code)"
    write_minimal_void 2 "the on-box script aborted before the measuring program finished"
    exit 2
  fi
  exit "$code"
}
trap on_exit EXIT

# ---------------------------------------------------------------------------
# 3. Caches, so nothing is written outside this run's own directory.
# ---------------------------------------------------------------------------

export TMPDIR="$RUN_DIR/tmp"
export PIP_CACHE_DIR="$RUN_DIR/cache/pip"
export XDG_CACHE_HOME="$RUN_DIR/cache/xdg"
export MPLCONFIGDIR="$RUN_DIR/cache/mpl"
export JAX_CACHE_DIR="$RUN_DIR/cache/jax"
export XLA_FLAGS="--xla_gpu_force_compilation_parallelism=1"
export COLABFOLD_CACHE="$RUN_DIR/cache/colabfold"
mkdir -p "$TMPDIR" "$PIP_CACHE_DIR" "$XDG_CACHE_HOME" "$MPLCONFIGDIR" \
         "$JAX_CACHE_DIR" "$COLABFOLD_CACHE" "$RUN_DIR/data"

# ---------------------------------------------------------------------------
# 4. Declared system packages.
#
# These three are the only packages installed with administrator rights, and
# `apt-get update` is the only other call made that way. Each is pinned to
# whatever the image's own package list offers; the measuring program records
# the version and archive hash of each before it installs anything else.
# ---------------------------------------------------------------------------

APT_PACKAGES="python3-venv aria2 curl"
APT_START="$(date -u +%s)"
say "installing the declared system packages: $APT_PACKAGES"
# The package database can be locked by the image's own unattended upgrades at
# boot. Waiting for it is correct; failing on it would throw away a paid box.
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if sudo -n env DEBIAN_FRONTEND=noninteractive apt-get update -qq >>"$LOG" 2>&1; then
    break
  fi
  say "the package database is busy; waiting (attempt $attempt)"
  sleep 15
done
if ! sudo -n env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
       $APT_PACKAGES >>"$LOG" 2>&1; then
  say "FATAL: the declared system packages could not be installed"
  write_minimal_void 2 "the declared system packages could not be installed"
  FINISHED=1
  exit 2
fi
APT_SECONDS=$(( $(date -u +%s) - APT_START ))
export M4_APT_SECONDS="$APT_SECONDS"
say "system packages installed in ${APT_SECONDS}s"

# ---------------------------------------------------------------------------
# 5. A private python environment.
#
# The image's own CUDA build of torch is left alone; nothing here upgrades a
# preinstalled package and nothing upgrades pip, because an upgrade that is
# not recorded is a download that is not recorded.
# ---------------------------------------------------------------------------

VENV="$RUN_DIR/venv_m4"
if [ ! -x "$VENV/bin/python3" ]; then
  say "building the private python environment"
  if ! python3 -m venv --system-site-packages "$VENV" >>"$LOG" 2>&1; then
    say "FATAL: the private python environment could not be built"
    write_minimal_void 2 "the private python environment could not be built"
    FINISHED=1
    exit 2
  fi
fi
export VIRTUAL_ENV="$VENV"
export PATH="$VENV/bin:$PATH"
export M4_VENV="$VENV"
export M4_VENV_BIN="$VENV/bin"
say "tools will resolve through $VENV/bin"

# The download token belongs to the bootstrap's own fetches and to nothing
# else. From here on neither this script nor any program it starts can see it.
unset HF_TOKEN
unset HUGGING_FACE_HUB_TOKEN

# ---------------------------------------------------------------------------
# 6. The measuring program, under a timer that beats the launcher's.
#
# The outer kill is set 600 seconds inside the run's own stopping point, and
# the program's own tool limits are set 700 seconds inside it, so the program
# always gets to write a record about whatever it had to stop.
# ---------------------------------------------------------------------------

ELAPSED=$(( $(date -u +%s) - T0_EPOCH ))
OUTER=$(( STOP_AT - ELAPSED - 600 ))
if [ "$OUTER" -lt 60 ]; then
  say "FATAL: no time left for any measurement after setting up"
  write_minimal_void 3 "no time left for any measurement after setting up"
  FINISHED=1
  exit 3
fi
say "starting the measuring program with ${OUTER}s of its own"

set +e
timeout --signal=TERM --kill-after=30 "$OUTER" \
  "$VENV/bin/python3" "$RUN_DIR/run_m4.py" --run --base "$RUN_DIR" \
  >>"$OUT/run_m4.stdout.log" 2>>"$OUT/run_m4.stderr.log"
RC=$?
set -e
say "the measuring program returned $RC"

# ---------------------------------------------------------------------------
# 7. If the timer fired, stop the tools and close the run as a stop, not a
#    failure. A kill that lands at the deadline is the timer; a kill that
#    lands long before it is something else, and that is a failure.
# ---------------------------------------------------------------------------

if [ "$RC" = "124" ] || [ "$RC" = "137" ]; then
  NOW_ELAPSED=$(( $(date -u +%s) - T0_EPOCH ))
  DEADLINE=$(( STOP_AT - 600 ))
  if [ "$RC" = "124" ] || [ "$NOW_ELAPSED" -ge $((DEADLINE - 5)) ]; then
    say "the timer fired; stopping any tool still running"
    python3 - "$OUT" <<'PY' || true
import json, os, signal, sys
path = os.path.join(sys.argv[1], "process_groups.json")
try:
    groups = json.load(open(path)).get("groups", [])
except Exception:
    groups = []
def identity(pid):
    try:
        raw = open("/proc/%d/stat" % pid).read()
    except OSError:
        return None
    close = raw.rindex(")")
    return raw[raw.index("(") + 1:close], raw[close + 2:].split()[19]
for g in groups:
    who = identity(g.get("pid") or -1)
    if who is None or who[0] != g.get("comm") or who[1] != g.get("starttime"):
        print("[onbox] skipping a process group whose leader is gone or replaced:",
              g.get("pgid"))
        continue
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(g["pgid"], sig)
        except Exception:
            break
    print("[onbox] stopped process group", g.get("pgid"))
PY
    say "closing the run as a stop, with every unmeasured input void"
    "$VENV/bin/python3" "$RUN_DIR/run_m4.py" --finalize --outer-rc "$RC" \
      --base "$RUN_DIR" >>"$OUT/run_m4.stdout.log" 2>>"$OUT/run_m4.stderr.log"
    RC=3
  else
    say "the run was killed ${NOW_ELAPSED}s in, well before the deadline"
    write_minimal_void 2 "the run was killed well before the deadline"
    RC=2
  fi
fi

# ---------------------------------------------------------------------------
# 8. The marker must exist whatever happened.
# ---------------------------------------------------------------------------

if [ ! -f "$OUT/RUN_DONE" ]; then
  say "the measuring program left no marker; writing one"
  write_minimal_void "$RC" "the measuring program left no marker"
fi

{
  echo "APT_PACKAGES=$APT_PACKAGES"
  echo "APT_SECONDS=$APT_SECONDS"
  echo "REMOTE_TIMEOUT_SEEN=$REMOTE_TIMEOUT_SEEN"
  echo "REMOTE_TIMEOUT_NOTE=$TIMEOUT_NOTE"
  echo "PRE_T0_SECONDS=$PRE_T0"
  echo "STOP_AT_SECONDS=$STOP_AT"
  echo "OUTER_TIMER_SECONDS=$OUTER"
  echo "VENV=$VENV"
} >> "$OUT/env.txt"

say "finished with exit code $RC"
FINISHED=1
exit "$RC"
