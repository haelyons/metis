#!/usr/bin/env bash
# What runs on the rented box, in order, with every guard the run needs.
#
# This script does six things and nothing else:
#   1. works out when the run must stop, from the price, the budget and the
#      timeout the launcher forwards, counting the time the box spent booting;
#   2. turns on the python environment of record, which was built once on the
#      attached filesystem, and refuses to go on unless the list of packages in
#      it hashes to exactly the lock the launcher forwarded;
#   3. checks that a graphics processor is visible at all;
#   4. starts the measuring program under a timer that always fires before the
#      launcher's own, so this script is the one that writes the last word;
#   5. holds the box open once, for a bounded repair by a person, when a stage
#      fails, and restarts the measuring program once if the repair stays
#      inside its scope;
#   6. leaves a marker saying what happened, whatever happened.
#
# It installs nothing. There is no package manager call, no administrator
# right, and no environment built here: the environment is an artifact on the
# attached filesystem, named by its lock.
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

# The measuring program and the ceiling on setting up, each named once here.
# No test file is shipped, run or referenced: a separate author writes the
# tests and runs them locally before every launch.
RUNNER_PY="$RUN_DIR/run_m4.py"
RUNNER_CMD=()                     # filled in once the environment of record is on
SETUP_CEILING_S=1500

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

# Where the environment of record lives, which list of packages it must hash
# to, and how long the box may be held open for a repair. The lock is not a
# secret and is written into the environment record; it has no default, because
# a missing lock means nobody checked which environment this is.
ENV_DIR="${ENV_DIR:-/lambda/nfs/metis-env-us-east-1/m4}"
ENV_LOCK_SHA256="${ENV_LOCK_SHA256:-}"
if [ -n "${HOLD_SECONDS:-}" ]; then
  # Whole seconds only: anything else is read as no hold at all.
  HOLD_SECONDS_SEEN="$(printf '%s' "$HOLD_SECONDS" | tr -dc '0-9')"
  HOLD_SECONDS_SEEN="${HOLD_SECONDS_SEEN:-0}"
  HOLD_NOTE="forwarded by the launcher"
else
  HOLD_SECONDS_SEEN=0
  HOLD_NOTE="HOLD_SECONDS not forwarded; no hold"
fi
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
    echo "SETUP_CEILING_SECONDS=$SETUP_CEILING_S"
    echo "SETUP_SECONDS_USED=$SETUP_USED"
    echo "ENV_DIR=$ENV_DIR"
    echo "VENV=$VENV"
    echo "ENV_LOCK_SHA256=$ENV_LOCK_SHA256"
    echo "ENV_LOCK_OBSERVED=$LOCK_OBSERVED"
    echo "ENVIRONMENT_CHANGED_BY_FIXER=$ENV_CHANGED_BY_FIXER"
    echo "HOLD_SECONDS=$HOLD_SECONDS_SEEN"
    echo "HOLD_SECONDS_NOTE=$HOLD_NOTE"
    echo "HELD_ATTEMPTS=$HELD_ATTEMPTS"
    echo "RUN_PY_SHA256_AT_START=$RUNNER_SHA_AT_START"
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
    rec["calibration_valid"] = False
    rec.setdefault("values", {})["calibration_valid"] = False
    rec["values"].setdefault("calibration_checks", [
        {"check": "run_completed", "result": False, "value": False,
         "null_reason": reason}])
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
SETUP_USED=0
HELD_ATTEMPTS=0
ENV_CHANGED_BY_FIXER=false
LOCK_OBSERVED=""
HOLD_LABELS=""
HOLD_SIGNAL=""
# The environment of record, on the filesystem the launcher attached. It is not
# built here and nothing is installed into it.
VENV="$ENV_DIR/venv"

# The measuring program, hashed now, before anything can change it. A repair
# made while the box is held open may change the environment and the glue
# around it; it may not change this file, and this hash is how that is checked
# before the run is restarted.
sha_of() { [ -f "$1" ] && sha256sum "$1" | cut -d' ' -f1 || echo "missing"; }
RUNNER_SHA_AT_START="$(sha_of "$RUNNER_PY")"

# The compute table, written on every exit whatever decided the run. Every
# stage of the run's order is listed, whether it ran or not; a stage that was
# running when the run ended is closed with the time it had.
write_compute_summary() {
  M4_CS_OUT="$OUT" M4_CS_PRICE="$PRICE_USD_PER_HOUR" \
  M4_CS_INSTANCE="${INSTANCE_TYPE:-}" M4_CS_T0="$T0_EPOCH" \
  python3 - <<'PYC' >>"$LOG" 2>&1 || say "the compute table could not be written"
import json, os, time

out = os.environ["M4_CS_OUT"]
os.makedirs(out, exist_ok=True)
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
now_epoch = time.time()
try:
    t0 = float(os.environ.get("M4_CS_T0") or now_epoch)
except ValueError:
    t0 = now_epoch
elapsed = max(0.0, now_epoch - t0)
price = float(os.environ.get("M4_CS_PRICE") or 0) or None

STAGES = ["capability", "downloads", "controls", "anchor",
          "aux", "af2", "md", "storage", "endpoints"]
path = os.path.join(out, "compute_table_tag-m4.json")
table = None
if os.path.exists(path):
    try:
        table = json.load(open(path))
    except Exception:
        table = None
if not isinstance(table, dict):
    table = {}

by_name = {}
for entry in table.get("stages", []):
    if isinstance(entry, dict) and entry.get("stage"):
        by_name[entry["stage"]] = entry

rows = []
for name in STAGES:
    entry = by_name.get(name) or {}
    row = {
        "stage": name,
        "ran": bool(entry.get("ran")),
        "reason": entry.get("reason") or ("not started" if not entry.get("ran") else None),
        "start_utc": entry.get("start_utc"),
        "end_utc": entry.get("end_utc"),
        "wall_clock_s": entry.get("wall_clock_s"),
        "gpu_busy_s": entry.get("gpu_busy_s"),
        "gpu_busy_reason": entry.get("gpu_busy_reason") or "not sampled",
        "gpu_name": entry.get("gpu_name"),
        "exit_code": entry.get("exit_code"),
    }
    if row["ran"] and row["end_utc"] is None:
        row["end_utc"] = now
        if row["start_utc"]:
            try:
                start_epoch = time.mktime(
                    time.strptime(row["start_utc"], "%Y-%m-%dT%H:%M:%SZ"))
                row["wall_clock_s"] = round(now_epoch - start_epoch, 3)
            except Exception:
                row["wall_clock_s"] = None
        row["reason"] = row.get("reason") or "cut short when the run ended"
    rows.append(row)

table = {
    "stages": rows,
    "instance_type": os.environ.get("M4_CS_INSTANCE") or None,
    "price_usd_per_hour": price,
    "elapsed_since_t0_s": round(elapsed, 3),
    "estimated_spend_usd": round((elapsed / 3600.0 * price) if price else 0.0, 4),
    "anchor_decision": table.get("anchor_decision"),
}
with open(path, "w") as fh:
    json.dump(table, fh, indent=2)
    fh.write("\n")

summary_path = os.path.join(out, "m4_summary.json")
summary = {}
if os.path.exists(summary_path):
    try:
        summary = json.load(open(summary_path))
    except Exception:
        summary = {}
if not isinstance(summary, dict):
    summary = {}
summary.setdefault("what_this_run_decides",
                   "This run decides the stand-in protocol only.")
summary["compute"] = table
if "run_valid" not in summary:
    summary["run_valid"] = None
    summary["run_valid_voided_by"] = "the measuring program wrote no summary"
with open(summary_path, "w") as fh:
    json.dump(summary, fh, indent=2)
    fh.write("\n")
print("[onbox] compute table written")
PYC
}

on_exit() {
  local code=$?
  write_compute_summary
  if [ "$FINISHED" = "0" ]; then
    say "aborted before the measuring program finished (shell code $code)"
    if [ ! -f "$OUT/RUN_DONE" ]; then
      write_minimal_void 2 "the on-box script aborted before the measuring program finished" \
        "void_by_failure:shell_abort"
    fi
    write_compute_summary
    exit 2
  fi
  exit "$code"
}
trap on_exit EXIT

finish() {
  local code="$1"
  write_env_txt
  write_compute_summary
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
# 5. A graphics processor must be visible before anything is paid for.
# ---------------------------------------------------------------------------

GPU_RC=0
timeout -k 5 60 nvidia-smi -L >>"$LOG" 2>&1 || GPU_RC=$?
if [ "$GPU_RC" != "0" ]; then
  say "FATAL: no graphics processor is visible (nvidia-smi exit $GPU_RC)"
  write_minimal_void 2 "no graphics processor is visible on this box" \
    "void_by_failure:gpu_check"
  finish 2
fi

# ---------------------------------------------------------------------------
# 6. The python environment of record.
#
# The environment was built once on the filesystem the launcher attached, and
# it is named by its lock: the hash of the list of packages inside it. This
# script turns it on, asks it for that list, and refuses to measure anything
# unless the hash matches the one the launcher forwarded. Nothing is installed
# here, nothing is upgraded, and no package is pinned by this script: the pins
# live in the environment, which is why the lock is the thing that is checked.
# ---------------------------------------------------------------------------

VENV_PY=""

note_hold_label() {
  HOLD_LABELS="${HOLD_LABELS:+$HOLD_LABELS|}$1"
}

# write_env_check <observed> <equal: true|false> <python version> <why>
#   One record of the environment check, through the shared record writer, with
#   the same keys every other record carries.
write_env_check() {
  M4_EC_OUT="$OUT" M4_EC_FROZEN="$RUN_DIR/frozen" M4_EC_VENV="$VENV" \
  M4_EC_EXPECTED="$ENV_LOCK_SHA256" M4_EC_OBSERVED="$1" M4_EC_EQUAL="$2" \
  M4_EC_PYVER="$3" M4_EC_WHY="$4" M4_EC_PRICE="$PRICE_USD_PER_HOUR" \
  M4_EC_INSTANCE="${INSTANCE_TYPE:-}" M4_EC_HELD="$HELD_ATTEMPTS" \
  M4_EC_FIXER="$ENV_CHANGED_BY_FIXER" \
  python3 - <<'PY' >>"$LOG" 2>&1 || say "the environment-check record could not be written"
import json, os, sys, time

out = os.environ["M4_EC_OUT"]
os.makedirs(out, exist_ok=True)
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
equal = os.environ["M4_EC_EQUAL"] == "true"
expected = os.environ["M4_EC_EXPECTED"] or None
observed = os.environ["M4_EC_OBSERVED"] or None
fixer = os.environ["M4_EC_FIXER"] == "true"
held = int(os.environ["M4_EC_HELD"] or 0)

# Every key the records of this run carry about the machine. One that this
# script cannot read on its own says so, in words, beside the value.
unread = "not read by onbox_m4.sh; the measuring program reads it from the box"
machine = {
    "instance_type": os.environ["M4_EC_INSTANCE"] or None,
    "gpu_name": None, "gpu_driver": None, "cuda_runtime_version": None,
    "cuda_plugin_version": None,
    "start_utc": now, "end_utc": now,
    "price_usd_per_hour": float(os.environ["M4_EC_PRICE"] or 0) or None,
    "expected_lock_sha256": expected,
    "observed_lock_sha256": observed,
    "venv_path": os.environ["M4_EC_VENV"],
    "environment_changed_by_fixer": fixer,
    "held_attempts": held,
}
reasons = {k: unread for k, v in machine.items() if v is None}
values = {
    "kind": "environment_check",
    "expected_lock_sha256": expected,
    "observed_lock_sha256": observed,
    "venv_path": os.environ["M4_EC_VENV"],
    "python_version": os.environ["M4_EC_PYVER"] or None,
    "equal": equal,
    "machine": machine,
    "null_reasons": reasons,
}

sys.path.insert(0, os.environ["M4_EC_FROZEN"])
try:
    import provenance
except Exception:
    provenance = None

path = os.path.join(out, "env_check_tag-m4.json")
rec = None
if provenance is not None:
    try:
        provenance.write_result(
            path + ".tmp",
            cell={"stage": "environment check", "tag": "m4"},
            inputs=[{"path": os.environ["M4_EC_VENV"], "sha256_full": observed,
                     "what": "the environment of record, by its lock sha256"}],
            metric="the sha256 of the package list of the environment of record",
            values=values,
            threshold={"expected_lock_sha256": expected},
            decision_rule=("the environment is the one of record only when the "
                           "hash of its package list equals the lock the "
                           "launcher forwarded; anything else stops the run"),
            decision="PASS" if equal else "FAIL",
            notes=os.environ["M4_EC_WHY"])
        rec = json.load(open(path + ".tmp"))
        os.remove(path + ".tmp")
    except Exception:
        rec = None
if rec is None:
    rec = {"cell": {"stage": "environment check", "tag": "m4"}, "inputs": [],
           "metric": "the sha256 of the package list of the environment of record",
           "values": values, "threshold": {"expected_lock_sha256": expected},
           "decision_rule": "the hash of the package list must equal the lock",
           "decision": "PASS" if equal else "FAIL",
           "notes": os.environ["M4_EC_WHY"],
           "env": {"timestamp_utc": now, "host": None, "python": None,
                   "git_rev": None}}
rec["kind"] = "env_check"
rec["run_valid"] = equal
rec["run_valid_voided_by"] = None if equal else os.environ["M4_EC_WHY"]
rec["notes_list"] = ([] if not fixer else
                     ["environment changed by the fixer on the box; lock %s"
                      % (observed or "unknown")])
rec["tag"] = "m4"
with open(path, "w") as fh:
    json.dump(rec, fh, indent=2)
    fh.write("\n")
print("[onbox] environment check written: equal %s" % equal)
PY
}

# The two steps of this section. Each sets ATTEMPT_RC and ATTEMPT_KIND and
# returns non-zero instead of exiting, so the hold below can decide what
# happens next.
LOCK_MISMATCH_SEEN=0

activate_environment() {
  local setup_start pyver
  setup_start="$(date -u +%s)"
  VENV_PY="$VENV/bin/python"
  [ -x "$VENV_PY" ] || VENV_PY="$VENV/bin/python3"
  if [ ! -x "$VENV_PY" ] || [ ! -f "$VENV/bin/activate" ]; then
    say "FATAL: $VENV is not a python environment that can be turned on"
    write_minimal_void 2 "the environment of record is missing or cannot be activated" \
      "void_by_failure:environment_missing"
    ATTEMPT_RC=2
    ATTEMPT_KIND="environment_missing"
    ATTEMPT_STAGE="the environment of record"
    return 1
  fi
  pyver="$("$VENV_PY" -c 'import platform,sys;print(platform.python_implementation()+" "+"%d.%d.%d" % sys.version_info[:3])' 2>>"$LOG")"
  case "$pyver" in
    "CPython 3.10."*) : ;;
    *)
      say "FATAL: the environment of record is not a CPython 3.10 one (got '${pyver:-nothing}')"
      write_minimal_void 2 "the environment of record is not an activatable CPython 3.10 environment" \
        "void_by_failure:environment_missing"
      ATTEMPT_RC=2
      ATTEMPT_KIND="environment_missing"
      ATTEMPT_STAGE="the environment of record"
      return 1 ;;
  esac
  ENV_PYTHON_VERSION="$pyver"
  # shellcheck disable=SC1091
  . "$VENV/bin/activate"
  export VIRTUAL_ENV="$VENV"
  export PATH="$VENV/bin:$PATH"
  export M4_VENV="$VENV"
  export M4_VENV_BIN="$VENV/bin"
  RUNNER_CMD=("$VENV_PY" "$RUNNER_PY")
  say "the environment of record is on: $pyver at $VENV"
  SETUP_USED=$(( SETUP_USED + $(date -u +%s) - setup_start ))
  return 0
}

verify_lock() {
  local setup_start observed freeze_rc expected
  setup_start="$(date -u +%s)"
  expected="$(printf '%s' "$ENV_LOCK_SHA256" | tr 'A-Z' 'a-z')"
  if ! printf '%s' "$expected" | grep -Eq '^[0-9a-f]{64}$'; then
    say "FATAL: no readable environment lock was forwarded (ENV_LOCK_SHA256)"
    write_env_check "" "false" "${ENV_PYTHON_VERSION:-}" \
      "ENV_LOCK_SHA256 was unset or not 64 hexadecimal characters"
    write_minimal_void 2 "the environment lock was not forwarded, so the environment could not be checked" \
      "void_by_failure:env_lock"
    ATTEMPT_RC=2
    ATTEMPT_KIND="env_lock"
    ATTEMPT_STAGE="the environment lock check"
    LOCK_MISMATCH_SEEN=1
    return 1
  fi
  # The list is written out first and hashed from the file, so the hash is of
  # exactly the bytes the environment printed, and the list itself is kept.
  freeze_rc=0
  "$VENV_PY" -m pip freeze > "$OUT/env_pip_freeze.txt" 2>>"$LOG" || freeze_rc=$?
  observed="$(sha_of "$OUT/env_pip_freeze.txt")"
  [ "$observed" = "missing" ] && observed=""
  SETUP_USED=$(( SETUP_USED + $(date -u +%s) - setup_start ))
  LOCK_OBSERVED="$observed"
  if [ "$freeze_rc" != "0" ] || [ -z "$observed" ]; then
    say "FATAL: the environment of record would not list its own packages"
    write_env_check "$observed" "false" "${ENV_PYTHON_VERSION:-}" \
      "the environment would not list its packages (exit $freeze_rc)"
    write_minimal_void 2 "the environment of record would not list its own packages" \
      "void_by_failure:env_lock"
    ATTEMPT_RC=2
    ATTEMPT_KIND="env_lock"
    ATTEMPT_STAGE="the environment lock check"
    LOCK_MISMATCH_SEEN=1
    return 1
  fi
  if [ "$observed" = "$expected" ]; then
    say "the environment lock matches: $observed"
    write_env_check "$observed" "true" "${ENV_PYTHON_VERSION:-}" \
      "the package list of the environment hashes to the lock the launcher forwarded"
    return 0
  fi
  # A lock that differs after a repair is the repair, and it is labelled as
  # such. A lock that differs twice at this very check is final.
  if [ "$HELD_ATTEMPTS" -ge 1 ] && [ "$LOCK_MISMATCH_SEEN" = "0" ]; then
    ENV_CHANGED_BY_FIXER=true
    note_hold_label "environment changed by the fixer on the box; lock $observed"
    say "the environment was changed by the fixer on the box; lock $observed"
    write_env_check "$observed" "false" "${ENV_PYTHON_VERSION:-}" \
      "environment changed by the fixer on the box; lock $observed"
    return 0
  fi
  say "FATAL: the environment lock does not match (observed $observed)"
  write_env_check "$observed" "false" "${ENV_PYTHON_VERSION:-}" \
    "the package list hashes to $observed, not to the lock the launcher forwarded"
  write_minimal_void 2 "the environment on the box is not the environment of record" \
    "void_by_failure:env_lock"
  ATTEMPT_RC=2
  ATTEMPT_KIND="env_lock"
  LOCK_MISMATCH_SEEN=1
  return 1
}

# ---------------------------------------------------------------------------
# 7. One attempt: the measuring program, under a timer that beats the
#    launcher's.
#
# The outer kill is set 600 seconds inside the run's own stopping point, and
# the program's own tool limits are set 700 seconds inside it, so the program
# always gets to write a record about whatever it had to stop. The attempt
# never exits this script; it leaves its exit code in ATTEMPT_RC, so the hold
# below can decide whether the box is kept open for a repair.
# ---------------------------------------------------------------------------

attempt_body() {
  local rc elapsed outer now_elapsed deadline outer_rc marked
  ATTEMPT_RC=0
  ATTEMPT_KIND=""

  activate_environment || return 0
  verify_lock || return 0

  if [ "$SETUP_USED" -ge "$SETUP_CEILING_S" ]; then
    say "FATAL: setting up took ${SETUP_USED}s, which is past its ceiling of ${SETUP_CEILING_S}s"
    write_minimal_void 2 "setting up ran past its ceiling of 1,500 seconds" \
      "void_by_failure:setup_total_ceiling"
    ATTEMPT_RC=2
    ATTEMPT_KIND="setup_total_ceiling"
    ATTEMPT_STAGE="setting up"
    return 0
  fi

  export M4_SETUP_SECONDS="$SETUP_USED"
  export M4_ENV_LOCK_OBSERVED="$LOCK_OBSERVED"
  export M4_ENV_CHANGED_BY_FIXER="$ENV_CHANGED_BY_FIXER"
  export M4_HELD_ATTEMPTS="$HELD_ATTEMPTS"
  export M4_HOLD_LABELS="$HOLD_LABELS"
  export ENV_DIR ENV_LOCK_SHA256
  export HOLD_SECONDS="$HOLD_SECONDS_SEEN"
  [ -n "${CHANGES_LOG_SHA256:-}" ] && export M4_CHANGES_LOG_SHA256="$CHANGES_LOG_SHA256"

  # The download token belongs to the bootstrap's own fetches and to nothing
  # else. From here on neither this script nor any program it starts can see it.
  unset HF_TOKEN
  unset HUGGING_FACE_HUB_TOKEN

  elapsed="$(elapsed_now)"
  outer=$(( STOP_AT - elapsed - 600 ))
  if [ "$outer" -lt 60 ]; then
    say "no time left for any measurement after setting up"
    if [ ! -f "$OUT/RUN_DONE" ]; then
      write_minimal_void 3 "no time left for any measurement after setting up" \
        "unmeasured_by_stop:no_time_after_setup"
    fi
    ATTEMPT_RC=3
    return 0
  fi
  say "starting the measuring program with ${outer}s of its own"

  rc=0
  timeout --signal=TERM --kill-after=30 "$outer" \
    "${RUNNER_CMD[@]}" --run --base "$RUN_DIR" \
    >>"$OUT/run_m4.stdout.log" 2>>"$OUT/run_m4.stderr.log" || rc=$?
  say "the measuring program returned $rc"

  # If the timer fired, stop the tools and close the run as a stop, not a
  # failure. A kill that lands at the deadline is the timer; a kill that lands
  # long before it is something else, and that is a failure.
  if [ "$rc" = "124" ] || [ "$rc" = "137" ]; then
    now_elapsed="$(elapsed_now)"
    deadline=$(( STOP_AT - 600 ))
    if [ "$rc" = "124" ] || [ "$now_elapsed" -ge $((deadline - 5)) ]; then
      outer_rc="$rc"
      say "the timer fired; stopping any tool still running"
      rc=0
      M4_KILL_OUT="$OUT" python3 - <<'PY' >>"$LOG" 2>&1 || rc=$?
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
      say "the process-group stopper returned $rc"
      say "closing the run as a stop, with every unmeasured input void"
      rc=0
      "${RUNNER_CMD[@]}" --finalize --outer-rc "$outer_rc" --base "$RUN_DIR" \
        >>"$OUT/run_m4.stdout.log" 2>>"$OUT/run_m4.stderr.log" || rc=$?
      say "the closing call returned $rc"
      rc=3
    else
      say "the run was killed ${now_elapsed}s in, well before the deadline"
      rc=2
      ATTEMPT_KIND="killed_early"
    fi
  fi

  # The marker must exist whatever happened. When the measuring program wrote
  # its own marker and validity file, those are the last word and this script
  # rewrites neither; its own exit code is the one in that marker. A program
  # that returns 0 without leaving a marker has not finished, and that is
  # broken infrastructure.
  if [ -f "$OUT/RUN_DONE" ]; then
    marked="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("exit_code",""))' \
              "$OUT/RUN_DONE" 2>/dev/null)"
    if [ -n "$marked" ]; then
      say "the measuring program left a marker with exit code $marked"
      rc="$marked"
    fi
    if [ -z "$ATTEMPT_KIND" ]; then
      ATTEMPT_KIND="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("failure_kind") or "")' \
                      "$OUT/RUN_DONE" 2>/dev/null)"
    fi
    ATTEMPT_STAGE="the measuring program"
    ATTEMPT_RC="$rc"
    return 0
  fi

  if [ "$rc" = "0" ]; then
    say "the measuring program returned 0 but left no marker"
    write_minimal_void 2 "the measuring program returned 0 without leaving a marker" \
      "void_by_failure:no_marker"
    ATTEMPT_RC=2
    ATTEMPT_KIND="no_marker"
    return 0
  fi

  case "$rc" in
    3) write_minimal_void 3 "a guard, a stage ceiling or a timeout stopped the run" \
         "unmeasured_by_stop:outer_timeout" ;;
    4) write_minimal_void 4 "the anchor redocking missed the published placement" \
         "unmeasured_by_stop:runner_left_no_marker" ;;
    *) write_minimal_void 2 "the measuring program ended with code $rc and left no marker" \
         "void_by_failure:runner_exit_$rc"
       rc=2
       [ -n "$ATTEMPT_KIND" ] || ATTEMPT_KIND="runner_exit" ;;
  esac
  ATTEMPT_RC="$rc"
  return 0
}

# ---------------------------------------------------------------------------
# 8. The hold: one bounded repair by a person, and one restart.
#
# A stage that failed as broken infrastructure may be worth mending by hand:
# the environment and the glue around it are the fixer's to change, and every
# change is committed to the box's own git repository. The measurement protocol
# and the record fields are not the fixer's to change, which is why the two
# files that hold them are hashed at the start of this script and compared
# before anything restarts. The one failure never held open is the planted
# sleep check: a clock this run cannot trust is not a thing a repair mends.
#
# Time spent held counts as elapsed time and against no stage ceiling. There is
# one hold per launch: a second failure that would qualify ends the launch.
# ---------------------------------------------------------------------------

# Add one sentence to the marker, so a reader sees how the hold ended.
extend_run_done() {
  M4_RD_PATH="$OUT/RUN_DONE" M4_RD_NOTE="$1" python3 - <<'PY' >>"$LOG" 2>&1 || true
import json, os
path = os.environ["M4_RD_PATH"]
note = os.environ["M4_RD_NOTE"]
try:
    doc = json.load(open(path))
except Exception:
    doc = {}
doc["hold"] = note
doc.setdefault("notes", []).append("hold: " + note)
with open(path, "w") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
}

hold_is_eligible() {
  # Every exit-2 stage failure qualifies, except the planted sleep check.
  [ "$ATTEMPT_RC" = "2" ] || return 1
  case "$ATTEMPT_KIND" in
    sleep_check) return 1 ;;
    *) return 0 ;;
  esac
}

# Returns 0 when the run may be restarted once, non-zero when it may not.
hold_open() {
  local waited left runner_now hold_start next_beat cause ended_utc
  if [ "$HELD_ATTEMPTS" -ge 1 ]; then
    say "a second failure that would qualify for a hold: the launch ends here"
    extend_run_done "one hold per launch; the second failure ends the launch"
    return 1
  fi
  # However long the launcher asked for, the box is never held past 2,400 s.
  if [ "${HOLD_SECONDS_SEEN:-0}" -gt 2400 ]; then
    HOLD_SECONDS_SEEN=2400
    say "HOLD_SECONDS capped at 2400"
    note_hold_label "HOLD_SECONDS capped at 2400"
  fi
  if [ "${HOLD_SECONDS_SEEN:-0}" -le 0 ]; then
    say "$HOLD_NOTE"
    note_hold_label "$HOLD_NOTE"
    extend_run_done "$HOLD_NOTE"
    return 1
  fi

  printf '%s\n' \
    "stage: ${ATTEMPT_STAGE:-the stage that failed}" \
    "kind: ${ATTEMPT_KIND:-unknown}" \
    "exit_code: $ATTEMPT_RC" \
    "held_from_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "hold_seconds: $HOLD_SECONDS_SEEN" \
    "resume_file: $OUT/RESUME" \
    "in_scope: the environment and the glue around it, every change committed to git on this box" \
    "out_of_scope: run_m4.py, which must stay byte for byte as it is" \
    > "$OUT/HOLD"
  say "holding the box open for up to ${HOLD_SECONDS_SEEN}s; waiting for $OUT/RESUME"

  # The wait is measured against the clock, never counted in sleeps, so a
  # sleep that is cut short or stretched cannot change how long the box is
  # held. It ends on a resume, on the clock reaching the hold length, or on a
  # signal; there is no other way out of this loop. Every end is written down.
  HOLD_SIGNAL=""
  trap 'HOLD_SIGNAL=HUP' HUP
  trap 'HOLD_SIGNAL=TERM' TERM
  trap 'HOLD_SIGNAL=INT' INT
  hold_start="$(date -u +%s)"
  next_beat=60
  cause=""
  while : ; do
    waited=$(( $(date -u +%s) - hold_start ))
    if [ -f "$OUT/RESUME" ]; then cause="resume"; break; fi
    if [ -n "$HOLD_SIGNAL" ]; then cause="$HOLD_SIGNAL"; break; fi
    if [ "$waited" -ge "$HOLD_SECONDS_SEEN" ]; then cause="expired"; break; fi
    sleep 10
    waited=$(( $(date -u +%s) - hold_start ))
    if [ "$waited" -ge "$next_beat" ]; then
      say "held ${waited}s of ${HOLD_SECONDS_SEEN}s, still waiting for a resume"
      while [ "$waited" -ge "$next_beat" ]; do next_beat=$(( next_beat + 60 )); done
    fi
  done
  trap - HUP TERM INT
  waited=$(( $(date -u +%s) - hold_start ))
  ended_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '%s\n' \
    "cause: $cause" \
    "seconds_waited: $waited" \
    "hold_seconds: $HOLD_SECONDS_SEEN" \
    "ended_utc: $ended_utc" \
    > "$OUT/HOLD_END"
  say "the hold ended after ${waited}s: $cause"

  if [ "$cause" != "resume" ]; then
    note_hold_label "hold: expired ($cause after ${waited}s)"
    extend_run_done "expired ($cause after ${waited}s)"
    return 1
  fi
  say "a resume arrived after ${waited}s"

  runner_now="$(sha_of "$RUNNER_PY")"
  if [ "$runner_now" != "$RUNNER_SHA_AT_START" ]; then
    say "FATAL: the repair changed the measuring program; no restart"
    note_hold_label "fixer_out_of_scope"
    extend_run_done "fixer_out_of_scope: the measuring program changed"
    write_minimal_void 2 "the repair changed the measurement protocol, which is out of its scope" \
      "void_by_failure:fixer_out_of_scope"
    ATTEMPT_RC=2
    return 1
  fi

  left=$(( REMOTE_TIMEOUT_SEEN - $(elapsed_now) ))
  if [ "$left" -lt 1500 ]; then
    say "only ${left}s of the launch are left; too little to restart"
    note_hold_label "hold: no time to resume"
    extend_run_done "no time to resume"
    return 1
  fi

  # The first attempt's results are kept whole, beside the restarted one's.
  if [ -d "$RUN_DIR/results_m4/held_attempt_1" ]; then
    rm -rf "$RUN_DIR/results_m4/held_attempt_1"
  fi
  mv "$OUT" "$RUN_DIR/results_m4/held_attempt_1"
  mkdir -p "$OUT"
  # The note of how the hold ended belongs with the restarted attempt too.
  [ -f "$RUN_DIR/results_m4/held_attempt_1/HOLD_END" ] && \
    cp "$RUN_DIR/results_m4/held_attempt_1/HOLD_END" "$OUT/HOLD_END"
  HELD_ATTEMPTS=1
  ENV_TXT_WRITTEN=0
  say "the first attempt is kept in results_m4/held_attempt_1; restarting once"

  # What the fixer changed, as the box's own git repository tells it.
  if git -C "$RUN_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "$RUN_DIR" log --stat --date=iso-strict \
      --pretty=format:'%H %ad %an %s' > "$OUT/changes.log" 2>>"$LOG" || true
  else
    echo "no git repository on the box; the fixer's changes are not listed" \
      > "$OUT/changes.log"
  fi
  CHANGES_LOG_SHA256="$(sha_of "$OUT/changes.log")"
  note_hold_label "held_attempts: 1; change log sha256 $CHANGES_LOG_SHA256"
  return 0
}

# ---------------------------------------------------------------------------
# 9. The run: one attempt, and at most one more after a repair.
# ---------------------------------------------------------------------------

ATTEMPT_RC=0
ATTEMPT_KIND=""
ATTEMPT_STAGE=""

while : ; do
  attempt_body
  if hold_is_eligible && hold_open; then
    continue
  fi
  break
done

finish "$ATTEMPT_RC"
