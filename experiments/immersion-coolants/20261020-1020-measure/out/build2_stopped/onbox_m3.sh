#!/usr/bin/env bash
# On-box batch for the throughput measurement (tag m3). It runs on the rented GPU box, inside the
# launcher's REMOTE_TIMEOUT window, through the bootstrap:   bash remote_run_m3.sh bash onbox_m3.sh
#
# WHAT IT DOES, IN THE ORDER THE EXECUTION NOTE SETS (EXEC_NOTE.md, checklist item 13)
#   1. install: micromamba 2.9.0 (its sha256 recorded, and checked against the value the coolant
#      pilot measured for the same file), then LAMMPS 2024.08.29 from conda-forge, CUDA 12.6 build,
#      into ./engine. Nothing else is installed: no pip, no apt, no Python environment.
#   2. lmp -h and GPU check (run_m3.py extract): the GPU package must be listed, else code 2.
#   3. timed dry run   4. copy of the box   5. equilibration   6-8. runs a, b, c   9. endpoints.
#   A cost and time guard runs before every stage: `run_m3.py guard` here, and inside each stage.
#   Step 5 (checklist item 3b): if the committed equilibrate.in stops with an error naming comm_style,
#   balance, tiled or rcb, run_m3.py deletes exactly those three lines in a copy
#   (results_m3/decks/equilibrate_noballance.in), records the error line and the diff, and runs the
#   equilibration once more from the copy, after a fresh guard. Any other error stops the run (code 12).
#
# WHAT MUST SIT BESIDE THIS SCRIPT: run_m3.py, frozen/provenance.py and data/ (the launcher ships them).
# RESULTS: results_m3/out/ (records, logs, raw rows, RUN_VALID.json, m3_summary.json, RUN_DONE).
# The engine is ./engine; the writable box copy is results_m3/system/; restart files stay on the box.
#
# ENVIRONMENT: PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and INSTANCE_TYPE (forwarded by the launcher);
# REMOTE_TIMEOUT (5400 s unless set). The run stops cleanly before projected spend reaches
# BUDGET_LEFT_USD and before REMOTE_TIMEOUT, cutting run c first, then run b.
#
# After a nonzero code, m3_summary.json labels every finished run "incomplete run: descriptive only,
# no verdict".
# EXIT CODES (also written to results_m3/out/RUN_DONE)
#   0 finished   2 install failed or GPU package missing   3 stopped by the cost or time guard
#   4 pre-launch build gate failed   10 dry run  11 box copy  12 equilibration  13 run a  14 run b
#   15 run c   16 endpoints   17 extract   1 any other failure
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || exit 1
OUT="$HERE/results_m3/out"
mkdir -p "$OUT"
rm -f "$OUT/RUN_DONE"
exec > >(tee -a "$OUT/onbox_m3.log") 2>&1

# This process was started by the launcher's `timeout`; run_m3.py reads its start time from /proc
# to know how much of the REMOTE_TIMEOUT window is left.
export M3_WINDOW_PID=$$
export REMOTE_TIMEOUT="${REMOTE_TIMEOUT:-5400}"
export PYTHONUNBUFFERED=1   # live progress lines for the launcher's poll
PY=python3
RUNNER="$HERE/run_m3.py"
FINISHED=0

stamp() { echo "[$1] $(date -u +%FT%TZ) uptime $(cut -d' ' -f1 /proc/uptime) s"; }

finish() {   # finish <code> <reason...>: summary, then the RUN_DONE marker, then exit
  local rc=$1; shift
  if [ "$rc" != 0 ]; then "$PY" "$RUNNER" void --reason "the run stopped with code $rc: $*" || true; fi
  "$PY" "$RUNNER" summary --exit-code "$rc" --note "$*" || echo "[finish] the summary could not be written"
  printf '%s\n' "$rc" > "$OUT/RUN_DONE"
  FINISHED=1
  echo "[finish] code $rc: $* ($(date -u +%FT%TZ))"
  exit "$rc"
}

on_exit() {
  local rc=$?
  if [ "$FINISHED" != 1 ]; then
    [ "$rc" = 0 ] && rc=1
    "$PY" "$RUNNER" void --reason "the on-box script ended without finishing (code $rc)" || true
    "$PY" "$RUNNER" summary --exit-code "$rc" --note "ended without finishing" || true
    printf '%s\n' "$rc" > "$OUT/RUN_DONE"
    echo "[finish] code $rc: ended without finishing"
  fi
}
trap on_exit EXIT
trap 'echo "[signal] stopped by a signal"; exit 143' TERM INT HUP

[ -f "$RUNNER" ] || finish 1 "run_m3.py is not beside this script"
[ -f "$HERE/frozen/provenance.py" ] || finish 1 "frozen/provenance.py is not beside this script"
[ -d "$HERE/data" ] || finish 1 "data/ is not beside this script"

# ---- 1. install ------------------------------------------------------------------------------
stamp "install: guard"
GUARD_TXT="$("$PY" "$RUNNER" guard --stage install)"
rc=$?
echo "$GUARD_TXT"
[ "$rc" = 0 ] || finish "$rc" "the cost or time guard stopped the run before the install"
ALLOW=$(printf '%s\n' "$GUARD_TXT" | sed -n 's/^allowed_seconds=\([0-9][0-9]*\)$/\1/p' | tail -1)
[ -n "$ALLOW" ] || finish 1 "the guard printed no allowed time for the install"
DEADLINE=$(( $(date +%s) + ALLOW ))
left() { echo $(( DEADLINE - $(date +%s) )); }

MM_URL="https://conda.anaconda.org/conda-forge/linux-64/micromamba-2.9.0-0.tar.bz2"
MM_SHA_PILOT="8761c382127e6363bd9e0a2451aa3ef90d071a79133f736e2f759a3bf13040dd"   # measured by the coolant pilot
SPEC_EXACT="lammps=2024.08.29=cuda126_py310_h894d002_nompi_2"
SPEC_FALLBACK="lammps=2024.08.29=cuda126_py310*nompi*"
MMDIR="$HERE/mm"
MM="$MMDIR/bin/micromamba"
export MAMBA_ROOT_PREFIX="$MMDIR/root"
IREC="$OUT/install_record.txt"
ILOG="$OUT/install.log"
: > "$IREC"
kv() { printf '%s=%s\n' "$1" "$2" >> "$IREC"; }
install_fail() {
  kv end_epoch "$(date +%s.%N)"
  kv install_ok 0
  kv failure "$1"
  "$PY" "$RUNNER" void --reason "install failed: $1"
  finish 2 "install failed: $1"
}

stamp "install: start (allowed ${ALLOW} s)"
kv start_epoch "$(date +%s.%N)"
kv allowed_seconds "$ALLOW"
kv micromamba_url "$MM_URL"
mkdir -p "$MMDIR"
L=$(left); [ "$L" -gt 0 ] || install_fail "no time left for the micromamba download"
timeout "$L" curl -fsSL --retry 5 -o "$MMDIR/micromamba.tar.bz2" "$MM_URL" >> "$ILOG" 2>&1 \
  || install_fail "the micromamba download failed"
MM_SHA=$(sha256sum "$MMDIR/micromamba.tar.bz2" | cut -d' ' -f1)
kv micromamba_sha256 "$MM_SHA"
kv micromamba_sha256_pilot "$MM_SHA_PILOT"
[ "$MM_SHA" = "$MM_SHA_PILOT" ] || install_fail "the micromamba tarball's sha256 differs from the coolant pilot's"
tar -xjf "$MMDIR/micromamba.tar.bz2" -C "$MMDIR" bin/micromamba >> "$ILOG" 2>&1 || install_fail "could not unpack micromamba"
"$MM" --version >> "$ILOG" 2>&1 || install_fail "micromamba does not start"

nvidia-smi > "$OUT/nvidia_smi.txt" 2>&1 || echo "[install] nvidia-smi exited nonzero"
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader > "$OUT/nvidia_smi_query.txt" 2>&1 || true
CUDA_VER=$(sed -n 's/.*CUDA Version: *\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' "$OUT/nvidia_smi.txt" | head -1)
if [ -n "$CUDA_VER" ]; then export CONDA_OVERRIDE_CUDA="$CUDA_VER"; fi
kv conda_override_cuda "${CUDA_VER:-unset}"

rm -rf ./engine
SPEC_USED=""
L=$(left)
kv spec_tried_first "$SPEC_EXACT"
if [ "$L" -gt 0 ] && timeout "$L" "$MM" create -y -p ./engine -c conda-forge --override-channels "$SPEC_EXACT" >> "$ILOG" 2>&1; then
  SPEC_USED="$SPEC_EXACT"
else
  kv spec_first_code "$?"
  echo "[install] the exact build did not install; trying $SPEC_FALLBACK"
  rm -rf ./engine
  L=$(left)
  kv spec_tried_second "$SPEC_FALLBACK"
  if [ "$L" -gt 0 ] && timeout "$L" "$MM" create -y -p ./engine -c conda-forge --override-channels "$SPEC_FALLBACK" >> "$ILOG" 2>&1; then
    SPEC_USED="$SPEC_FALLBACK"
  else
    install_fail "neither LAMMPS spec installed (or the time guard's deadline passed)"
  fi
fi
kv spec_used "$SPEC_USED"
"$MM" list -p ./engine > "$OUT/micromamba_list.txt" 2>> "$ILOG" || install_fail "micromamba list failed"
"$MM" list -p ./engine --json > "$OUT/micromamba_list.json" 2>> "$ILOG" || true
[ -x ./engine/bin/lmp ] || install_fail "the engine has no lmp binary"
kv end_epoch "$(date +%s.%N)"
kv install_ok 1
./engine/bin/lmp -h > "$OUT/lmp_help.txt" 2>&1
kv lmp_help_code "$?"
stamp "install: done ($SPEC_USED)"

# ---- 2 to 9: the stages; each runs its own guard first ------------------------------------------
stage() {   # stage <label> <command...>: run it, print its code, return the code
  local label=$1; shift
  stamp "$label: start"
  "$@"
  local rc=$?
  stamp "$label: code $rc"
  return "$rc"
}

stage "lmp -h and GPU check" "$PY" "$RUNNER" extract              || finish $? "the lmp -h and GPU check stage stopped the run"
stage "timed dry run"        "$PY" "$RUNNER" generate --stage dryrun      || finish $? "the dry run stage stopped the run"
stage "copy of the box"      "$PY" "$RUNNER" generate --stage copy        || finish $? "the box copy stage stopped the run"
stage "equilibration"        "$PY" "$RUNNER" generate --stage equilibrate || finish $? "the equilibration stage stopped the run"
stage "run a"                "$PY" "$RUNNER" generate --stage prod_a      || finish $? "the run a stage stopped the run"
stage "run b"                "$PY" "$RUNNER" generate --stage prod_b      || finish $? "the run b stage stopped the run"
stage "run c"                "$PY" "$RUNNER" generate --stage prod_c      || finish $? "the run c stage stopped the run"
stage "endpoints"            "$PY" "$RUNNER" endpoints                    || finish $? "the endpoints stage failed"

echo "[result] files in results_m3/out/:"
ls -1 "$OUT" | sed 's/^/    /'
finish 0 "every stage finished"
