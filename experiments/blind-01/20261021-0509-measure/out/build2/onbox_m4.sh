#!/usr/bin/env bash
# On-box batch for the four-input measurement (tag m4). Runs once, on one rented GPU box.
#
# WHAT IT DOES, in this order and no other:
#   1. install and downloads   declared apt packages, a virtual environment, declared pip packages
#   2. controls                a planted 60 second sleep, an empty run, the unit and scale print
#   3. anchor                  redock the receptor onto the capsid, serial first, then parallel
#   4. docking and analysis    per pair, which is what the auxiliary hours measure
#   5. AlphaFold timings       one seed at a time across all three pairs
#   6. dynamics timings        one half-nanosecond production segment per complex
#   7. storage                 bytes written, by artifact type
#   8. endpoints               the four decisions, the summary and the markers
# Steps 2 to 8 live in run_m4.py. This script installs, guards the clock, and records failures.
#
# CAPS. It reads PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and REMOTE_TIMEOUT from its environment.
# Defaults are 1.99 dollars an hour, 5 dollars and 7200 seconds. A larger budget or timeout in
# the environment is lowered back to 5 dollars and 7200 seconds: one launch may not exceed them.
#
# FAILURE IS RECORDED, NEVER PATCHED. Any failed install, download, GPU check or tool start stops
# the run. It writes a not-decided record for every input, marks the run not valid, writes the
# exit code to results_m4/out/RUN_DONE and exits non-zero. Nothing is retried or substituted.
#   exit 2 broken machine or broken harness    exit 3 cost or time guard stop    exit 4 anchor miss
#
# SECRETS. This script reads no key file and prints no environment dump. results_m4/out/env.txt
# lists named non-secret variables only. No download here needs a token.
#
#   usage:  bash remote_run_m4.sh bash onbox_m4.sh

set -uo pipefail
cd "$(dirname "$0")"

OUT=results_m4/out
mkdir -p "$OUT" "$OUT/logs"

# The moment the box started working. Every guard measures from here. A second launch keeps the
# first one's start only if its state is still on the box; a fresh box writes a fresh start.
# The launcher's own clock starts a minute or two earlier, at the bootstrap. The 500 second
# margin below covers that gap, so our guard stops before the launcher's hard kill.
[ -f "$OUT/t0.txt" ] || date +%s > "$OUT/t0.txt"
T0=$(cat "$OUT/t0.txt")
elapsed() { echo $(( $(date +%s) - T0 )); }

# Caps. Never above one launch's ceiling, whatever the environment says.
PRICE_USD_PER_HOUR="${PRICE_USD_PER_HOUR:-1.99}"
BUDGET_LEFT_USD="${BUDGET_LEFT_USD:-5}"
REMOTE_TIMEOUT="${REMOTE_TIMEOUT:-7200}"
[ -z "$PRICE_USD_PER_HOUR" ] && PRICE_USD_PER_HOUR=1.99
[ -z "$BUDGET_LEFT_USD" ] && BUDGET_LEFT_USD=5
[ -z "$REMOTE_TIMEOUT" ] && REMOTE_TIMEOUT=7200
BUDGET_LEFT_USD=$(awk -v b="$BUDGET_LEFT_USD" 'BEGIN{print (b>5||b<=0)?5:b}')
REMOTE_TIMEOUT=$(awk -v t="$REMOTE_TIMEOUT" 'BEGIN{print (t>7200||t<=0)?7200:int(t)}')
export PRICE_USD_PER_HOUR BUDGET_LEFT_USD REMOTE_TIMEOUT

# The earlier of the money cap and the clock cap, in seconds from the start.
STOP_AT=$(awk -v p="$PRICE_USD_PER_HOUR" -v b="$BUDGET_LEFT_USD" -v t="$REMOTE_TIMEOUT" \
  'BEGIN{m=(p>0)?b/p*3600:t; print int((m<t)?m:t)}')

# Stage ceilings in seconds, from the gate checklist. They add up to the 7200 second cap:
# 2000 + 700 + 2100 + 1800 + 100 + 500 of margin.
CEIL_INSTALL=2000
CEIL_CONTROLS_ANCHOR=700
CEIL_ENDPOINTS=100
MARGIN=500

# Named non-secret variables only. No environment dump, ever.
{
  echo "INSTANCE_TYPE=${INSTANCE_TYPE:-}"
  echo "PRICE_USD_PER_HOUR=$PRICE_USD_PER_HOUR"
  echo "BUDGET_LEFT_USD=$BUDGET_LEFT_USD"
  echo "REMOTE_TIMEOUT=$REMOTE_TIMEOUT"
  echo "STOP_AT_S=$STOP_AT"
  echo "GIT_COMMIT=${GIT_COMMIT:-}"
  echo "LAMBDA_INSTANCE_ID=${LAMBDA_INSTANCE_ID:-}"
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}"
  echo "T0_EPOCH=$T0"
} > "$OUT/env.txt"

PY=python3
VENV_PY="$PWD/.venv/bin/python"

# Record the failure where a reader will find it, then stop. Never patch around a failure.
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

# Seconds this stage may use: whatever is left before the cap, less the margin.
budget_for() {
  local reserve="$1"
  local left=$(( STOP_AT - $(elapsed) - reserve ))
  [ "$left" -lt 1 ] && left=0
  echo "$left"
}

echo "[m4] start $(date -u +%FT%TZ) cap ${STOP_AT}s price ${PRICE_USD_PER_HOUR}/h budget ${BUDGET_LEFT_USD}"

# --- 1. install and downloads ---------------------------------------------------------------
# A GPU must be present before anything is installed. A box without one bills for nothing.
nvidia-smi -L > "$OUT/logs/nvidia_smi_list.log" 2>&1 || fail "gpu_check" "nvidia-smi did not run" 2
grep -qi "gpu" "$OUT/logs/nvidia_smi_list.log" || fail "gpu_check" "no GPU listed" 2

INSTALL_LEFT=$(( CEIL_INSTALL - $(elapsed) ))
[ "$INSTALL_LEFT" -lt 60 ] && fail "install" "no time left inside the ${CEIL_INSTALL}s install ceiling" 3

# Declared apt packages, installed without any prompt. This is the only use of sudo here.
# build-essential is declared because some pip packages compile from source.
timeout "$INSTALL_LEFT" bash -c '
  set -e
  export DEBIAN_FRONTEND=noninteractive
  sudo -n apt-get update -qq
  sudo -n apt-get install -y -qq --no-install-recommends build-essential
' > "$OUT/logs/apt.log" 2>&1 || fail "install" "declared apt packages did not install" 2

# A virtual environment on top of the image's own CUDA stack, which stays as shipped.
timeout 300 "$PY" -m venv --system-site-packages .venv > "$OUT/logs/venv.log" 2>&1 \
  || fail "install" "virtual environment not created" 2

INSTALL_LEFT=$(( CEIL_INSTALL - $(elapsed) ))
[ "$INSTALL_LEFT" -lt 60 ] && fail "install" "no time left inside the ${CEIL_INSTALL}s install ceiling" 3

# Declared pip packages. ColabFold runs AlphaFold-Multimer, LightDock docks, OpenMM runs the
# dynamics. Versions are read back and recorded by run_m4.py.
timeout "$INSTALL_LEFT" "$VENV_PY" -m pip install -q --upgrade pip wheel \
  > "$OUT/logs/pip_base.log" 2>&1 || fail "install" "pip did not upgrade" 2

INSTALL_LEFT=$(( CEIL_INSTALL - $(elapsed) ))
[ "$INSTALL_LEFT" -lt 60 ] && fail "install" "no time left inside the ${CEIL_INSTALL}s install ceiling" 3
timeout "$INSTALL_LEFT" "$VENV_PY" -m pip install -q \
  "colabfold[alphafold]" "jax[cuda12]" openmm lightdock \
  > "$OUT/logs/pip_tools.log" 2>&1 || fail "install" "declared pip packages did not install" 2

"$VENV_PY" -m pip freeze > "$OUT/logs/pip_freeze.txt" 2>&1 || true

# --- 2 to 4. downloads, controls, anchor -----------------------------------------------------
# run_m4.py fetches the published entry and the AlphaFold parameter archive, runs the three
# controls, then redocks serially and in parallel. A missed anchor exits 4 from inside.
STAGE_BUDGET=$(( CEIL_INSTALL - $(elapsed) + CEIL_CONTROLS_ANCHOR ))
[ "$STAGE_BUDGET" -lt 60 ] && fail "extract" "no time left for downloads, controls and anchor" 3
timeout "$STAGE_BUDGET" "$VENV_PY" run_m4.py --stage extract
RC=$?
[ "$RC" = 124 ] && fail "extract" "downloads, controls and anchor hit their ceiling" 3
[ "$RC" != 0 ] && { echo "$RC" > "$OUT/RUN_DONE"; echo "[m4] extract exited $RC"; exit "$RC"; }

# --- 5 to 7. docking per pair, AlphaFold, dynamics, storage ----------------------------------
STAGE_BUDGET=$(budget_for $(( CEIL_ENDPOINTS + MARGIN )))
[ "$STAGE_BUDGET" -lt 60 ] && fail "generate" "no time left for the measured work" 3
timeout "$STAGE_BUDGET" "$VENV_PY" run_m4.py --stage generate
RC=$?
if [ "$RC" = 124 ]; then
  # The clock ran out inside the measured work. Decide what finished, void the rest, exit 3.
  timeout "$CEIL_ENDPOINTS" "$VENV_PY" run_m4.py --stage endpoints >> "$OUT/logs/endpoints.log" 2>&1
  "$VENV_PY" run_m4.py --fail-stage "generate" \
    --reason "the measured work hit the time or cost cap" --exit-code 3 \
    >> "$OUT/logs/endpoints.log" 2>&1 || true
  echo "3" > "$OUT/RUN_DONE"
  echo "[m4] generate hit the cap; finished records written"
  exit 3
fi
[ "$RC" != 0 ] && { echo "$RC" > "$OUT/RUN_DONE"; echo "[m4] generate exited $RC"; exit "$RC"; }

# --- 8. endpoints ----------------------------------------------------------------------------
timeout "$CEIL_ENDPOINTS" "$VENV_PY" run_m4.py --stage endpoints
RC=$?
[ "$RC" = 124 ] && fail "endpoints" "the endpoint stage hit its ${CEIL_ENDPOINTS}s ceiling" 3
[ "$RC" != 0 ] && { echo "$RC" > "$OUT/RUN_DONE"; echo "[m4] endpoints exited $RC"; exit "$RC"; }

echo "0" > "$OUT/RUN_DONE"
echo "[m4] done $(date -u +%FT%TZ) elapsed $(elapsed)s"
exit 0
