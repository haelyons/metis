#!/usr/bin/env bash
# What runs on the rented box, in order, with every guard the run needs.
#
# This script does five things and nothing else:
#   1. works out when the run must stop, from the price, the budget and the
#      timeout the launcher forwards, counting the time the box spent booting;
#   2. installs the declared system packages, each call under its own timer,
#      and builds a private python environment, with no prompt and no upgrade
#      of anything preinstalled;
#   3. checks that a graphics processor is visible at all;
#   4. starts the measuring program under a timer that always fires before the
#      launcher's own, so this script is the one that writes the last word;
#   5. leaves a marker saying what happened, whatever happened.
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
# NO `set -e`. Every command whose non-zero status is an expected outcome (the
# measuring program, its closing call, the outer timer, the process-group
# stopper) is run as `RC=0; <command> || RC=$?` and the route table below reads
# RC. Under `set -e` a non-zero status would abort the script before its route
# ran, and the exit trap would then report a stop as a failure. That happened
# once; it costs a whole paid box.
#
#   usage:  bash remote_run_m4.sh bash onbox_m4.sh

set -uo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The measuring program, the ceiling on installing, and the search path, each
# named once here so the test hook below can replace them.
TEST_MODE=0
RUNNER_PY="$RUN_DIR/run_m4.py"
RUNNER_CMD=()                     # filled in once the private environment exists
INSTALL_CEILING_S=1800

# BEGIN TEST HOOKS
if [ "${M4_SHELL_TEST:-0}" = "1" ]; then
  # The only place in this file that reads a variable whose name starts M4_TEST_.
  # It exists so the measuring program's own checks can run this script without
  # a graphics processor, without a network and without spending money: the
  # routes below are what those checks exercise. Without M4_SHELL_TEST=1 set to
  # exactly 1, nothing in this block runs and nothing else changes.
  TEST_MODE=1
  RUN_DIR="${M4_TEST_ROOT:-$RUN_DIR}"
  mkdir -p "$RUN_DIR"
  RUN_DIR="$(cd "$RUN_DIR" && pwd)"
  RUNNER_PY="$RUN_DIR/run_m4.py"
  if [ -n "${M4_TEST_RUNNER:-}" ]; then
    # Split on spaces: the replacement is a command line, not one file name.
    read -r -a RUNNER_CMD <<< "${M4_TEST_RUNNER}"
  fi
  INSTALL_CEILING_S="${M4_TEST_INSTALL_CEILING_S:-$INSTALL_CEILING_S}"
  if [ -n "${M4_TEST_BIN:-}" ]; then
    PATH="${M4_TEST_BIN}:$PATH"
    export PATH
  fi
fi
# END TEST HOOKS

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

elapsed_now() { echo $(( $(date -u +%s) - T0_EPOCH )); }

# ---------------------------------------------------------------------------
# 2. The records this script writes when the measuring program cannot.
#
# These carry the same keys as the program's own records: a reader who opens
# one file must see the unit, the card's value, the card's band, the decision
# and whether the run is valid, without opening anything else. They are written
# through the shared record writer when it imports here, and by hand with the
# same keys when it does not.
# ---------------------------------------------------------------------------

ENV_TXT_WRITTEN=0
write_env_txt() {
  [ "$ENV_TXT_WRITTEN" = "1" ] && return 0
  ENV_TXT_WRITTEN=1
  {
    echo "# Named non-secret variables only, written by onbox_m4.sh."
    echo "INSTANCE_TYPE=${INSTANCE_TYPE:-}"
    echo "PRICE_USD_PER_HOUR=$PRICE_USD_PER_HOUR"
    echo "BUDGET_LEFT_USD=$BUDGET_LEFT_USD"
    echo "REMOTE_TIMEOUT_SEEN=$REMOTE_TIMEOUT_SEEN"
    echo "REMOTE_TIMEOUT_NOTE=$TIMEOUT_NOTE"
    echo "PRE_T0_SECONDS=$PRE_T0"
    echo "BOOTSTRAP_ASSUMED=$BOOTSTRAP_ASSUMED"
    echo "STOP_AT_SECONDS=$STOP_AT"
    echo "INSTALL_CEILING_SECONDS=$INSTALL_CEILING_S"
    echo "INSTALL_SECONDS_USED=$INSTALL_USED"
    echo "APT_PACKAGES=$APT_PACKAGES"
    echo "VENV=$VENV"
    echo "HF_TOKEN=<not read, not printed, removed from every child>"
    echo "HUGGING_FACE_HUB_TOKEN=<not read, not printed, removed from every child>"
  } >> "$OUT/env.txt"
}

# write_minimal_void <code> <reason> <status>
#   code 2 or 4 -> run_valid false. code 3 -> run_valid true, unless a validity
#   file already on disk says false, in which case false is kept. Never called
#   with 0, and only called when the measuring program left no marker.
write_minimal_void() {
  local code="$1" reason="$2" status="$3"
  write_env_txt
  M4_VOID_OUT="$OUT" M4_VOID_CODE="$code" M4_VOID_REASON="$reason" \
  M4_VOID_STATUS="$status" M4_VOID_FROZEN="$RUN_DIR/frozen" \
  M4_VOID_TIMEOUT="$REMOTE_TIMEOUT_SEEN" \
  python3 - <<'PY' >>"$LOG" 2>&1 || say "the minimal void record could not be written"
import json, os, sys, time

out = os.environ["M4_VOID_OUT"]
code = int(os.environ["M4_VOID_CODE"])
reason = os.environ["M4_VOID_REASON"]
status = os.environ["M4_VOID_STATUS"]
frozen = os.environ["M4_VOID_FROZEN"]
os.makedirs(out, exist_ok=True)
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

INCOMPLETE = "incomplete run: unmeasured inputs are VOID, not holding"
WHAT = ("This run decides the stand-in protocol only: four cost inputs measured "
        "once on one rented single-GPU box, on pairs built from chains of PDB "
        "entry 6IHB, not on the card's own pairs and not on the card's 8-GPU "
        "setting. It does not run the card's 54-run pilot or its 216-run grid, "
        "and it does not evaluate the card's own prediction. Two runs on the "
        "same box are two samples of one box, never a replication.")
CARD = {
    "C1": ("af2_h_per_run", "hours per AlphaFold-Multimer run", 0.5, [0.2, 1.25]),
    "C2": ("md_ns_per_day_a100", "nanoseconds simulated per day", 129, [51.6, 322.5]),
    "C3": ("aux_h_per_pair", "hours per capsid-receptor pair", 1, [0.3333, 3]),
    "C4": ("n_storage_gib", "gibibytes", 200, [66.67, 600]),
}

# run_valid follows the one table in the execution directive.
run_valid = code == 3
valid_path = os.path.join(out, "RUN_VALID.json")
if code == 3 and os.path.exists(valid_path):
    try:
        if json.load(open(valid_path)).get("run_valid") is False:
            run_valid = False
    except Exception:
        pass

sys.path.insert(0, frozen)
try:
    import provenance                      # the shared record writer
except Exception:
    provenance = None

def put(path, cell, metric, values, threshold, rule, notes):
    if os.path.exists(path):
        return                             # never overwrite a real result
    rec = None
    if provenance is not None:
        try:
            provenance.write_result(
                path + ".tmp", cell=cell, inputs=[], metric=metric, values=values,
                threshold=threshold, decision_rule=rule, decision="VOID", notes=notes)
            rec = json.load(open(path + ".tmp"))
            os.remove(path + ".tmp")
        except Exception:
            rec = None
    if rec is None:                        # same keys, written by hand
        rec = {"cell": cell, "inputs": [], "metric": metric, "values": values,
               "threshold": threshold, "decision_rule": rule, "decision": "VOID",
               "notes": notes, "env": {"timestamp_utc": now, "host": None,
                                       "python": None, "git_rev": None}}
    rec["decision"] = "VOID"
    rec["run_valid"] = run_valid
    rec["run_valid_voided_by"] = reason
    rec["voided_by"] = reason
    rec["notes_list"] = [INCOMPLETE]
    rec["tag"] = "m4"
    with open(path, "w") as fh:
        json.dump(rec, fh, indent=2)
        fh.write("\n")

put(os.path.join(out, "endpoint-anchor_tag-m4.json"),
    {"stage": "anchor", "endpoint": "anchor", "tag": "m4"},
    "the anchor redocking was not compared: the run ended before it finished",
    {"measured": None, "published": ("AAVR-PKD2 bound to the AAV2 spike region "
                                     "adjacent to the icosahedral three-fold axis "
                                     "(PDB 6IHB)"),
     "tolerance": {"min_contact_overlap": 0.5,
                   "max_interface_backbone_rmsd_a": 5.0,
                   "max_serial_parallel_rmsd_a": 2.0},
     "unit": "fraction of published contacts, and angstrom",
     "null_reasons": {"measured": reason}},
    {"min_contact_overlap": 0.5, "max_interface_backbone_rmsd_a": 5.0},
    "an anchor the run never compared is VOID, never holding",
    reason)

# An input the measuring program already decided keeps that decision. Its
# record is read, never rewritten, and it is not shown as void below. Only an
# input with no such record takes this script's status. Code 4 (the anchor
# missed) voids all four, whatever their records say.
UNMEASURED = "unmeasured, not holding"

def standing(cid):
    """Read one input's record on disk: decided, void by a rule, or not done."""
    path = os.path.join(out, "endpoint-%s_tag-m4.json" % cid)
    try:
        rec = json.load(open(path))
    except Exception:
        return None
    if not isinstance(rec, dict):
        return None
    decision = rec.get("decision")
    values = rec.get("values") or {}
    why = str(values.get("void_reason") or values.get("voided_by") or "")
    notes = " ".join(str(n) for n in (rec.get("notes_list") or []))
    if decision in ("PASS", "FAIL"):
        return {"status": "decided", "decision": decision, "voided_by": None}
    if decision == "VOID" and UNMEASURED not in why and UNMEASURED not in notes:
        if values.get("marginal") or why:
            return {"status": "void_by_rule:%s" % (why or "marginal"),
                    "decision": "VOID", "voided_by": why or "marginal"}
    return None

KEPT = {} if code == 4 else {c: s for c in CARD for s in [standing(c)] if s}

for cid, (key, unit, value, band) in CARD.items():
    if cid in KEPT:
        continue
    put(os.path.join(out, "endpoint-%s_tag-m4.json" % cid),
        {"stage": "endpoints", "input": cid, "key": key, "tag": "m4"},
        "%s was not measured: the run ended before this stage" % key,
        {"measured": None, "unit": unit, "card_value": value, "band": band,
         "n": 0, "void_reason": "unmeasured, not holding (%s)" % reason,
         "null_reasons": {"measured": reason}},
        {"band": band, "card_value": value},
        "an input the run never reached is VOID, never holding",
        reason)

inputs = {}
for c in ("C1", "C2", "C3", "C4"):
    if c in KEPT:
        inputs[c] = dict(KEPT[c])
    else:
        inputs[c] = {"status": status, "decision": "VOID", "voided_by": reason}

summary = {}
summary["what_this_run_decides"] = WHAT
summary["tag"] = "m4"
summary["written_by"] = "onbox_m4.sh, because the measuring program left no marker"
summary["run_valid"] = run_valid
summary["run_valid_voided_by"] = reason
summary["exit_code"] = code
summary["inputs_status"] = inputs
summary["remote_timeout_seen_s"] = os.environ.get("M4_VOID_TIMEOUT")
summary["notes"] = [INCOMPLETE]
sp = os.path.join(out, "m4_summary.json")
if not os.path.exists(sp):
    with open(sp, "w") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")

with open(valid_path, "w") as fh:
    json.dump({"run_valid": run_valid, "voided_by": reason, "stopped": code == 3,
               "inputs_status": inputs, "tag": "m4"}, fh, indent=2)
    fh.write("\n")

with open(os.path.join(out, "RUN_DONE"), "w") as fh:
    json.dump({"exit_code": code, "run_valid": run_valid, "voided_by": reason,
               "stopped_by": [reason], "inputs": inputs, "tag": "m4",
               "finished_utc": now,
               "notes": [INCOMPLETE]}, fh, indent=2)
    fh.write("\n")
print("[onbox] minimal void written: code %d run_valid %s" % (code, run_valid))
PY
}

# ---------------------------------------------------------------------------
# 3. The marker, armed before anything can fail.
#
# The trap is set here, before the environment is built, so that an abort in
# the install still leaves a record, a validity file and a marker behind. A run
# that dies silently is indistinguishable from a run that was never started,
# and that has cost real money before. The trap acts only while FINISHED is 0;
# every route below sets FINISHED=1 before its own exit.
# ---------------------------------------------------------------------------

FINISHED=0
INSTALL_USED=0
APT_PACKAGES="python3-venv aria2 curl"
VENV="$RUN_DIR/venv_m4"

on_exit() {
  local code=$?
  if [ "$FINISHED" = "0" ]; then
    say "aborted before the measuring program finished (shell code $code)"
    if [ ! -f "$OUT/RUN_DONE" ]; then
      write_minimal_void 2 "the on-box script aborted before the measuring program finished" \
        "void_by_failure:shell_abort"
    fi
    exit 2
  fi
  exit "$code"
}
trap on_exit EXIT

finish() {
  local code="$1"
  write_env_txt
  say "finished with exit code $code"
  FINISHED=1
  exit "$code"
}

# ---------------------------------------------------------------------------
# 4. Caches, so nothing is written outside this run's own directory.
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
# 5. Declared system packages, every call under its own timer.
#
# These three are the only packages installed with administrator rights, and
# `apt-get update` is the only other call made that way. Each call draws on one
# shared budget of INSTALL_CEILING_S seconds; running that budget out is broken
# infrastructure (exit 2), never a guard stop. The measuring program records
# each package's version and archive hash before it installs anything else.
# ---------------------------------------------------------------------------

# apt_limit <own limit> -> seconds this call may run, inside the shared budget
apt_limit() {
  local own="$1" left
  left=$(( INSTALL_CEILING_S - INSTALL_USED ))
  [ "$left" -lt 0 ] && left=0
  if [ "$own" -lt "$left" ]; then echo "$own"; else echo "$left"; fi
}

apt_install_stage() {
  local start limit rc attempt updated loop_start loop_spent
  start="$(date -u +%s)"
  say "installing the declared system packages: $APT_PACKAGES"

  # The package database can be locked by the image's own unattended upgrades
  # at boot. Waiting for it is correct; failing on it would throw away a paid
  # box. At most ten tries, fifteen seconds apart, the whole loop at most 300
  # seconds, and every single try under its own timer.
  updated=0
  loop_start="$(date -u +%s)"
  for attempt in 1 2 3 4 5 6 7 8 9 10; do
    limit="$(apt_limit 120)"
    if [ "$limit" -le 0 ]; then
      say "FATAL: the install budget of ${INSTALL_CEILING_S}s ran out before the package database could be read"
      write_minimal_void 2 "the install budget ran out during apt-get update" \
        "void_by_failure:install_total_ceiling"
      finish 2
    fi
    rc=0
    timeout -k 10 "$limit" sudo -n env DEBIAN_FRONTEND=noninteractive \
      apt-get update -qq >>"$LOG" 2>&1 || rc=$?
    INSTALL_USED=$(( $(date -u +%s) - start ))
    if [ "$rc" = "0" ]; then updated=1; break; fi
    loop_spent=$(( $(date -u +%s) - loop_start ))
    if [ "$loop_spent" -ge 300 ]; then
      say "the package database stayed busy for ${loop_spent}s"
      break
    fi
    if [ "$(apt_limit 120)" -le 0 ]; then
      say "FATAL: the install budget ran out while the package database was busy"
      write_minimal_void 2 "the install budget ran out during apt-get update" \
        "void_by_failure:install_total_ceiling"
      finish 2
    fi
    say "the package database is busy (exit $rc); waiting (attempt $attempt)"
    sleep 15
  done
  if [ "$updated" != "1" ]; then
    say "FATAL: the package database could not be read"
    write_minimal_void 2 "apt-get update did not succeed inside its limits" \
      "void_by_failure:apt_update"
    finish 2
  fi

  limit="$(apt_limit 600)"
  if [ "$limit" -le 0 ]; then
    say "FATAL: the install budget ran out before the system packages could be installed"
    write_minimal_void 2 "the install budget ran out before apt-get install" \
      "void_by_failure:install_total_ceiling"
    finish 2
  fi
  rc=0
  timeout -k 10 "$limit" sudo -n env DEBIAN_FRONTEND=noninteractive \
    apt-get install -y -qq $APT_PACKAGES >>"$LOG" 2>&1 || rc=$?
  INSTALL_USED=$(( $(date -u +%s) - start ))
  if [ "$rc" != "0" ]; then
    say "FATAL: the declared system packages could not be installed (exit $rc)"
    write_minimal_void 2 "the declared system packages could not be installed" \
      "void_by_failure:apt_install"
    finish 2
  fi
  export M4_APT_SECONDS="$INSTALL_USED"
  say "system packages installed in ${INSTALL_USED}s"
}

apt_install_stage

# ---------------------------------------------------------------------------
# 6. A graphics processor must be visible before anything is paid for.
# ---------------------------------------------------------------------------

if [ "$TEST_MODE" = "0" ]; then
  GPU_RC=0
  timeout -k 5 60 nvidia-smi -L >>"$LOG" 2>&1 || GPU_RC=$?
  if [ "$GPU_RC" != "0" ]; then
    say "FATAL: no graphics processor is visible (nvidia-smi exit $GPU_RC)"
    write_minimal_void 2 "no graphics processor is visible on this box" \
      "void_by_failure:gpu_check"
    finish 2
  fi
fi

# ---------------------------------------------------------------------------
# 7. A private python environment.
#
# The image's own CUDA build of torch is left alone; nothing here upgrades a
# preinstalled package and nothing upgrades pip, because an upgrade that is not
# recorded is a download that is not recorded. The measuring program does the
# one recorded pip bootstrap, if the environment's own pip is too old to report
# what it downloaded.
# ---------------------------------------------------------------------------

if [ "$TEST_MODE" = "0" ]; then
  if [ ! -x "$VENV/bin/python3" ]; then
    say "building the private python environment"
    VENV_RC=0
    python3 -m venv --system-site-packages "$VENV" >>"$LOG" 2>&1 || VENV_RC=$?
    if [ "$VENV_RC" != "0" ]; then
      say "FATAL: the private python environment could not be built"
      write_minimal_void 2 "the private python environment could not be built" \
        "void_by_failure:venv"
      finish 2
    fi
  fi
  export VIRTUAL_ENV="$VENV"
  export PATH="$VENV/bin:$PATH"
  export M4_VENV="$VENV"
  export M4_VENV_BIN="$VENV/bin"
  say "tools will resolve through $VENV/bin"
  RUNNER_CMD=("$VENV/bin/python3" "$RUNNER_PY")
fi

# The download token belongs to the bootstrap's own fetches and to nothing
# else. From here on neither this script nor any program it starts can see it.
unset HF_TOKEN
unset HUGGING_FACE_HUB_TOKEN

# ---------------------------------------------------------------------------
# 8. The measuring program, under a timer that beats the launcher's.
#
# The outer kill is set 600 seconds inside the run's own stopping point, and
# the program's own tool limits are set 700 seconds inside it, so the program
# always gets to write a record about whatever it had to stop.
# ---------------------------------------------------------------------------

ELAPSED="$(elapsed_now)"
OUTER=$(( STOP_AT - ELAPSED - 600 ))
if [ "$OUTER" -lt 60 ]; then
  say "no time left for any measurement after setting up"
  if [ ! -f "$OUT/RUN_DONE" ]; then
    write_minimal_void 3 "no time left for any measurement after setting up" \
      "unmeasured_by_stop:no_time_after_setup"
  fi
  finish 3
fi
say "starting the measuring program with ${OUTER}s of its own"

RC=0
timeout --signal=TERM --kill-after=30 "$OUTER" \
  "${RUNNER_CMD[@]}" --run --base "$RUN_DIR" \
  >>"$OUT/run_m4.stdout.log" 2>>"$OUT/run_m4.stderr.log" || RC=$?
say "the measuring program returned $RC"

# ---------------------------------------------------------------------------
# 9. If the timer fired, stop the tools and close the run as a stop, not a
#    failure. A kill that lands at the deadline is the timer; a kill that lands
#    long before it is something else, and that is a failure.
# ---------------------------------------------------------------------------

if [ "$RC" = "124" ] || [ "$RC" = "137" ]; then
  NOW_ELAPSED="$(elapsed_now)"
  DEADLINE=$(( STOP_AT - 600 ))
  if [ "$RC" = "124" ] || [ "$NOW_ELAPSED" -ge $((DEADLINE - 5)) ]; then
    OUTER_RC="$RC"
    say "the timer fired; stopping any tool still running"
    RC=0
    M4_KILL_OUT="$OUT" python3 - <<'PY' >>"$LOG" 2>&1 || RC=$?
import json, os, signal
path = os.path.join(os.environ["M4_KILL_OUT"], "process_groups.json")
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
    say "the process-group stopper returned $RC"
    say "closing the run as a stop, with every unmeasured input void"
    RC=0
    "${RUNNER_CMD[@]}" --finalize --outer-rc "$OUTER_RC" --base "$RUN_DIR" \
      >>"$OUT/run_m4.stdout.log" 2>>"$OUT/run_m4.stderr.log" || RC=$?
    say "the closing call returned $RC"
    RC=3
  else
    say "the run was killed ${NOW_ELAPSED}s in, well before the deadline"
    RC=2
  fi
fi

# ---------------------------------------------------------------------------
# 10. The marker must exist whatever happened.
#
# When the measuring program wrote its own marker and validity file, those are
# the last word and this script rewrites neither; its own exit code is the one
# in that marker. A program that returns 0 without leaving a marker has not
# finished, and that is broken infrastructure.
# ---------------------------------------------------------------------------

if [ -f "$OUT/RUN_DONE" ]; then
  MARKED="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("exit_code",""))' \
            "$OUT/RUN_DONE" 2>/dev/null)"
  if [ -n "$MARKED" ]; then
    say "the measuring program left a marker with exit code $MARKED"
    RC="$MARKED"
  fi
  finish "$RC"
fi

if [ "$RC" = "0" ]; then
  say "the measuring program returned 0 but left no marker"
  write_minimal_void 2 "the measuring program returned 0 without leaving a marker" \
    "void_by_failure:no_marker"
  finish 2
fi

case "$RC" in
  3) write_minimal_void 3 "a guard, a stage ceiling or a timeout stopped the run" \
       "unmeasured_by_stop:outer_timeout" ;;
  4) write_minimal_void 4 "the anchor redocking missed the published placement" \
       "void_by_anchor_miss" ;;
  *) write_minimal_void 2 "the measuring program ended with code $RC and left no marker" \
       "void_by_failure:runner_exit_$RC"
     RC=2 ;;
esac
finish "$RC"
