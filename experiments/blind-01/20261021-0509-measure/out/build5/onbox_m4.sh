#!/usr/bin/env bash
# On-box batch for the four-input measurement (tag m4). Runs once, on one rented GPU box.
#
# WHAT IT DOES, in this order and no other:
#   1. install, downloads and a start check   declared apt and pip packages, then a check that
#                                             every declared tool actually starts on this machine
#   2. controls                               a planted 60 second sleep, an empty run, a unit print
#   3. anchor                                 redock the receptor onto the capsid, serial then parallel
#   4. docking and analysis                   per pair, which is what the auxiliary hours measure
#   5. AlphaFold timings                      one seed at a time across all three pairs
#   6. dynamics timings                       one half-nanosecond production segment per complex
#   7. storage                                bytes written, by artifact type
#   8. endpoints                              the four decisions, the summary and the markers
# Steps 2 to 8 live in run_m4.py. This script installs, checks, guards the clock, and records stops.
#
# CAPS. It reads PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and REMOTE_TIMEOUT from its environment.
# Defaults are 1.99 dollars an hour, 5 dollars and 7200 seconds. A larger budget or timeout in the
# environment is lowered back to 5 dollars and 7200 seconds: one launch may not exceed them. An
# unset REMOTE_TIMEOUT is recorded as such, with the default used in its place.
#
# TWO KINDS OF BAD ENDING, KEPT APART.
#   Broken machine: a failed install, download, start check, GPU check or a tool that exits non-zero.
#   Nothing is retried, patched or substituted. The run is marked not valid, every input is written
#   as not decided, and the code is 2 (or 4 for a missed anchor).
#   Out of clock or money: a stage that cannot start or that reaches its ceiling, or a tool stopped
#   at its allowance. Finished inputs keep their decisions, the unfinished ones are written as not
#   decided with the words "incomplete run", the run stays valid, and the code is 3.
#
# SECRETS. This script reads no key file and prints no environment dump. results_m4/out/env.txt
# lists named non-secret variables only. No download here needs a token, and both token variables
# are removed from this shell once the installs are done.
#
#   usage:  bash remote_run_m4.sh bash onbox_m4.sh

set -uo pipefail
cd "$(dirname "$0")"

OUT=results_m4/out
mkdir -p "$OUT" "$OUT/logs"

# The moment the box started working. Every guard measures from here. A second launch keeps the
# first one's start only if its state is still on the box; a fresh box writes a fresh start.
# The launcher's own clock starts a minute or two earlier, at the bootstrap. The 400 second margin
# below covers that gap, so our guard stops before the launcher's hard kill.
[ -f "$OUT/t0.txt" ] || date +%s > "$OUT/t0.txt"
T0=$(cat "$OUT/t0.txt")
elapsed() { echo $(( $(date +%s) - T0 )); }

# Caps. Never above one launch's ceiling, whatever the environment says.
REMOTE_TIMEOUT_SEEN="${REMOTE_TIMEOUT:-}"
PRICE_USD_PER_HOUR="${PRICE_USD_PER_HOUR:-1.99}"
BUDGET_LEFT_USD="${BUDGET_LEFT_USD:-5}"
REMOTE_TIMEOUT="${REMOTE_TIMEOUT:-7200}"
[ -z "$PRICE_USD_PER_HOUR" ] && PRICE_USD_PER_HOUR=1.99
[ -z "$BUDGET_LEFT_USD" ] && BUDGET_LEFT_USD=5
[ -z "$REMOTE_TIMEOUT" ] && REMOTE_TIMEOUT=7200
BUDGET_LEFT_USD=$(awk -v b="$BUDGET_LEFT_USD" 'BEGIN{print (b>5||b<=0)?5:b}')
REMOTE_TIMEOUT=$(awk -v t="$REMOTE_TIMEOUT" 'BEGIN{print (t>7200||t<=0)?7200:int(t)}')
TIMEOUT_NOTE=""
[ -z "$REMOTE_TIMEOUT_SEEN" ] && TIMEOUT_NOTE="REMOTE_TIMEOUT not forwarded; default 7200 used"
export PRICE_USD_PER_HOUR BUDGET_LEFT_USD REMOTE_TIMEOUT

# The earlier of the money cap and the clock cap, in seconds from the start.
STOP_AT=$(awk -v p="$PRICE_USD_PER_HOUR" -v b="$BUDGET_LEFT_USD" -v t="$REMOTE_TIMEOUT" \
  'BEGIN{m=(p>0)?b/p*3600:t; print int((m<t)?m:t)}')

# Stage ceilings in seconds, from the gate checklist. They add up to the 7200 second cap:
# 1800 + 700 + 600 + 2000 + 1600 + 100 + 400 of margin.
CEIL_INSTALL=1800
CEIL_CONTROLS_ANCHOR=700
CEIL_AUX=600
CEIL_AF2=2000
CEIL_MD=1600
CEIL_ENDPOINTS=100
MARGIN=400
# The measured work (docking, AlphaFold, dynamics, storage) shares one window.
CEIL_GENERATE=$(( CEIL_AUX + CEIL_AF2 + CEIL_MD ))
# How long before the cap this script stops the runner. The runner gives each tool 700 seconds
# less than the cap, so a tool is always stopped by the runner first, 100 seconds earlier.
OUTER_KILL_RESERVE=600

# Pinned versions. Nothing here floats, and nothing is substituted if it fails to install.
PIN_COLABFOLD="colabfold[alphafold]==1.5.5"
PIN_JAX="jax[cuda12]==0.4.35"
PIN_OPENMM="openmm[cuda12]==8.2.0"     # this is the form that carries the CUDA platform
PIN_LIGHTDOCK="lightdock==0.9.4"
APT_PACKAGES="build-essential=12.9ubuntu3"  # pinned by version; some wheels compile from source

# Named non-secret variables only. No environment dump, ever.
{
  echo "INSTANCE_TYPE=${INSTANCE_TYPE:-}"
  echo "PRICE_USD_PER_HOUR=$PRICE_USD_PER_HOUR"
  echo "BUDGET_LEFT_USD=$BUDGET_LEFT_USD"
  echo "REMOTE_TIMEOUT=$REMOTE_TIMEOUT"
  echo "REMOTE_TIMEOUT_SEEN=$REMOTE_TIMEOUT_SEEN"
  echo "REMOTE_TIMEOUT_NOTE=$TIMEOUT_NOTE"
  echo "STOP_AT_S=$STOP_AT"
  echo "GIT_COMMIT=${GIT_COMMIT:-}"
  echo "LAMBDA_INSTANCE_ID=${LAMBDA_INSTANCE_ID:-}"
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}"
  echo "T0_EPOCH=$T0"
} > "$OUT/env.txt"

PY=python3
VENV_PY="$PWD/.venv/bin/python"
VENV_BIN="$PWD/.venv/bin"

# Record the failure where a reader will find it, then stop. Never patch around a failure.
# Code 2 and 4 mark the run not valid; code 3 is a clock or money stop and does not.
fail() {
  local stage="$1" reason="$2" code="${3:-2}"
  echo "[fail] stage=$stage code=$code reason=$reason"
  local runner="$PY"
  [ -x "$VENV_PY" ] && runner="$VENV_PY"
  "$runner" run_m4.py --fail-stage "$stage" --reason "$reason" --exit-code "$code" \
    >> "$OUT/logs/fail_${stage}.log" 2>&1 || true
  echo "$code" > "$OUT/RUN_DONE"
  exit "$code"
}

# Seconds this stage may use: whatever is left before the cap, less what is reserved.
budget_for() {
  local reserve="$1"
  local left=$(( STOP_AT - $(elapsed) - reserve ))
  [ "$left" -lt 1 ] && left=0
  echo "$left"
}

# Stop every tool the runner started, by process group number, never by name. The runner keeps
# the list; a group that has already gone is simply not there any more.
kill_recorded_groups() {
  local list="$OUT/process_groups.txt"
  [ -f "$list" ] || return 0
  while read -r pg; do
    [ -z "$pg" ] && continue
    echo "[kill] stopping process group $pg"
    kill -TERM "-$pg" 2>/dev/null || true
  done < "$list"
  sleep 5
  while read -r pg; do
    [ -z "$pg" ] && continue
    kill -KILL "-$pg" 2>/dev/null || true
  done < "$list"
  : > "$list"
}

echo "[m4] start $(date -u +%FT%TZ) cap ${STOP_AT}s price ${PRICE_USD_PER_HOUR}/h budget ${BUDGET_LEFT_USD}"
[ -n "$TIMEOUT_NOTE" ] && echo "[m4] $TIMEOUT_NOTE"

# --- 1. install, downloads and the start check ------------------------------------------------
# A GPU must be present before anything is installed. A box without one bills for nothing.
nvidia-smi -L > "$OUT/logs/nvidia_smi_list.log" 2>&1 || fail "gpu_check" "nvidia-smi did not run" 2
grep -qi "gpu" "$OUT/logs/nvidia_smi_list.log" || fail "gpu_check" "no GPU listed" 2

INSTALL_LEFT=$(( CEIL_INSTALL - $(elapsed) ))
[ "$INSTALL_LEFT" -lt 60 ] && fail "install" "no time left inside the ${CEIL_INSTALL}s install ceiling" 3

# Declared apt packages, installed without any prompt. This is the only use of sudo here, and
# the environment is handed to apt through sudo itself, because sudo drops it otherwise.
timeout "$INSTALL_LEFT" bash -c "
  set -e
  sudo -n env DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=300 update -qq
  sudo -n env DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=300 install -y -qq --no-install-recommends $APT_PACKAGES
" > "$OUT/logs/apt.log" 2>&1 || fail "install" "declared apt packages did not install" 2

# What apt installed, with the version and the archive hash it names, one line per package.
: > "$OUT/apt_packages.txt"
for spec in $APT_PACKAGES; do
  pkg="${spec%%=*}"
  ver=$(dpkg-query -W -f='${Version}' "$pkg" 2>/dev/null || echo "unknown")
  sha=$(apt-cache show "$pkg" 2>/dev/null | awk -F': ' '/^SHA256: /{print $2; exit}')
  echo "$pkg | $ver | ${sha:-unknown}" >> "$OUT/apt_packages.txt"
done

# A virtual environment on top of the image's own CUDA stack, which stays as shipped.
timeout 300 "$PY" -m venv --system-site-packages .venv > "$OUT/logs/venv.log" 2>&1 \
  || fail "install" "virtual environment not created" 2

INSTALL_LEFT=$(( CEIL_INSTALL - $(elapsed) ))
[ "$INSTALL_LEFT" -lt 60 ] && fail "install" "no time left inside the ${CEIL_INSTALL}s install ceiling" 3
timeout "$INSTALL_LEFT" "$VENV_PY" -m pip install -q --upgrade pip wheel \
  > "$OUT/logs/pip_base.log" 2>&1 || fail "install" "pip did not upgrade" 2

# Declared pip packages, every one pinned, resolved in one command so nothing later downgrades
# anything earlier. ColabFold runs AlphaFold-Multimer, LightDock docks, OpenMM runs the dynamics.
# The report names the address and the archive hash of every wheel that arrived; it is kept.
INSTALL_LEFT=$(( CEIL_INSTALL - $(elapsed) ))
[ "$INSTALL_LEFT" -lt 60 ] && fail "install" "no time left inside the ${CEIL_INSTALL}s install ceiling" 3
timeout "$INSTALL_LEFT" "$VENV_PY" -m pip install -q --report "$OUT/pip_report.json" \
  "$PIN_COLABFOLD" "$PIN_JAX" "$PIN_OPENMM" "$PIN_LIGHTDOCK" \
  > "$OUT/logs/pip_tools.log" 2>&1 || fail "install" "declared pip packages did not install" 2

"$VENV_PY" -m pip freeze > "$OUT/logs/pip_freeze.txt" 2>&1 || true

# The start check. Every declared tool must start on this machine, on the GPU, now, inside the
# install ceiling: recollection about what a wheel carries is not evidence. A failure here is a
# broken machine, before a single GPU measurement has been paid for.
SMOKE_LEFT=$(( CEIL_INSTALL - $(elapsed) ))
[ "$SMOKE_LEFT" -lt 30 ] && fail "smoke_check" "no time left inside the ${CEIL_INSTALL}s install ceiling" 3
timeout "$SMOKE_LEFT" bash -c "
  set -e
  '$VENV_PY' - <<'PYCHECK'
import jax
print('jax', jax.__version__)
devices = jax.devices()
print('jax devices', devices)
assert any(getattr(d, 'platform', '') == 'gpu' for d in devices), 'jax lists no GPU device'
import colabfold.batch            # the AlphaFold-Multimer stack
print('colabfold import ok')
import openmm
from openmm import Platform
platform = Platform.getPlatformByName('CUDA')
print('openmm', openmm.version.version, 'platform', platform.getName())
PYCHECK
  '$VENV_BIN/colabfold_batch' --help > /dev/null
  echo 'colabfold_batch --help ok'
  '$VENV_BIN/lightdock3.py' --help > /dev/null
  echo 'lightdock3.py --help ok'
" > "$OUT/smoke_check.txt" 2>&1 || fail "smoke_check" "a declared tool did not start on this box" 2

# The installs are the only thing here that could have wanted a token. Nothing after this point
# gets one, from this shell or from any child of it.
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN

# --- 2 to 4. downloads, controls, anchor -------------------------------------------------------
# run_m4.py fetches the published entry and the AlphaFold parameter archive, runs the three
# controls, then redocks serially and in parallel. A missed anchor exits 4 from inside.
STAGE_BUDGET=$(( CEIL_INSTALL - $(elapsed) + CEIL_CONTROLS_ANCHOR ))
[ "$STAGE_BUDGET" -lt 60 ] && fail "extract" "no time left for downloads, controls and anchor" 3
timeout "$STAGE_BUDGET" "$VENV_PY" run_m4.py --stage extract
RC=$?
if [ "$RC" = 124 ]; then
  kill_recorded_groups
  timeout "$CEIL_ENDPOINTS" "$VENV_PY" run_m4.py --stage endpoints \
    >> "$OUT/logs/endpoints.log" 2>&1
  fail "extract" "the outer timeout stopped downloads, controls and anchor" 3
fi
[ "$RC" != 0 ] && { echo "$RC" > "$OUT/RUN_DONE"; echo "[m4] extract exited $RC"; exit "$RC"; }

# The downloads are done. Both token variables leave this shell here as well, so nothing after
# the downloads can see one, wherever it is run from.
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN

# --- 5 to 7. docking per pair, AlphaFold, dynamics, storage ------------------------------------
# The window is the smaller of the three stage ceilings added up and what the cap leaves, keeping
# back the endpoint slot and the margin. The runner stops each tool 100 seconds before this kill.
STAGE_BUDGET=$(budget_for $(( CEIL_ENDPOINTS + MARGIN )))
[ "$STAGE_BUDGET" -gt "$CEIL_GENERATE" ] && STAGE_BUDGET=$CEIL_GENERATE
OUTER_LIMIT=$(budget_for "$OUTER_KILL_RESERVE")
[ "$STAGE_BUDGET" -gt "$OUTER_LIMIT" ] && STAGE_BUDGET=$OUTER_LIMIT
[ "$STAGE_BUDGET" -lt 60 ] && fail "generate" "no time left for the measured work" 3
timeout "$STAGE_BUDGET" "$VENV_PY" run_m4.py --stage generate
RC=$?
if [ "$RC" = 124 ]; then
  # The clock ran out while a tool was still running. Stop every group the runner started, then
  # decide what finished, leave the rest undecided, and end as a clock stop, not as a failure.
  kill_recorded_groups
  timeout "$CEIL_ENDPOINTS" "$VENV_PY" run_m4.py --stage endpoints \
    >> "$OUT/logs/endpoints.log" 2>&1
  "$VENV_PY" run_m4.py --fail-stage "generate" \
    --reason "the outer timeout stopped the measured work" --exit-code 3 \
    >> "$OUT/logs/endpoints.log" 2>&1 || true
  echo "3" > "$OUT/RUN_DONE"
  echo "[m4] the measured work hit the cap; the finished records are written"
  exit 3
fi
if [ "$RC" != 0 ] && [ "$RC" != 3 ]; then
  echo "$RC" > "$OUT/RUN_DONE"; echo "[m4] generate exited $RC"; exit "$RC"
fi
GENERATE_RC=$RC

# --- 8. endpoints ------------------------------------------------------------------------------
timeout "$CEIL_ENDPOINTS" "$VENV_PY" run_m4.py --stage endpoints
RC=$?
[ "$RC" = 124 ] && fail "endpoints" "the endpoint stage hit its ${CEIL_ENDPOINTS}s ceiling" 3
if [ "$RC" != 0 ] && [ "$RC" != 3 ]; then
  echo "$RC" > "$OUT/RUN_DONE"; echo "[m4] endpoints exited $RC"; exit "$RC"
fi
[ "$GENERATE_RC" = 3 ] && RC=3

echo "$RC" > "$OUT/RUN_DONE"
echo "[m4] done $(date -u +%FT%TZ) elapsed $(elapsed)s exit $RC"
exit "$RC"
