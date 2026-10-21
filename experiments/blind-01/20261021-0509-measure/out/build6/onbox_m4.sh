#!/usr/bin/env bash
# What runs on the rented box, in order, with a guard before every stage.
#
# The measurement program (run_m4.py) does the work and writes the records.
# This script owns the things a shell owns: the isolated Python environment,
# the order of the stages, the clock and money caps, stopping tools that run
# past their allowance, and the exit code.
#
#   started by the operator as:  bash remote_run_m4.sh bash onbox_m4.sh
#
# EXIT CODES
#   0  every input was decided by measurement
#   2  broken infrastructure or a broken harness (install, download, start-up
#      check, graphics processor, or a tool that really failed)
#   3  a guard, a stage ceiling or a timeout stopped the run with work left
#   4  the anchor re-docking missed
#
# WHY A SEPARATE PYTHON ENVIRONMENT. The box image ships a working CUDA build
# of torch. Installing into the system Python risks a resolver swapping that
# out. The environment below is created with the system packages still visible,
# so the image's torch is used and never replaced, and only the packages this
# run needs are added on top.
#
# NOTHING INTERACTIVE. No prompts anywhere. The only use of administrator
# rights is the two declared system packages below, installed non-interactively.
# No part of this run reads the key file, and nothing prints the environment:
# the environment record lists named, non-secret variables only.

set -euo pipefail

TAG=m4
cd "$(dirname "$0")"
RUN_DIR="$(pwd)"
OUT="${RUN_DIR}/results_${TAG}/out"
WORK="${RUN_DIR}/work_${TAG}"
VENV="${RUN_DIR}/venv_${TAG}"
mkdir -p "$OUT" "$WORK"

# The system packages this run is allowed to install, declared here and handed
# to the measurement program so the declaration and the install cannot drift.
APT_PACKAGES="aria2 ca-certificates"
export M4_APT_PACKAGES="$APT_PACKAGES"

# --- the clock and money caps ----------------------------------------------
# Read from the environment the launcher forwards. No default is larger than
# the gate's own ceilings, whatever arrives.
T0=$(date +%s)
export M4_T0="$T0"
PRICE="${PRICE_USD_PER_HOUR:-1.99}"
BUDGET="${BUDGET_LEFT_USD:-5}"
TIMEOUT_SEEN="${REMOTE_TIMEOUT:-}"
TIMEOUT_NOTE=""
if [ -z "$TIMEOUT_SEEN" ]; then
  TIMEOUT_SEEN=7200
  TIMEOUT_NOTE="REMOTE_TIMEOUT not forwarded; default 7200 used"
fi
read -r PRICE BUDGET REMOTE_T STOP_AT <<EOF
$(awk -v p="$PRICE" -v b="$BUDGET" -v t="$TIMEOUT_SEEN" 'BEGIN{
  if (p <= 0) p = 1.99;
  if (b > 5) b = 5;
  if (t > 7200) t = 7200;
  money = b / p * 3600;
  stop = (t < money) ? t : money;
  printf "%.4f %.4f %d %d\n", p, b, t, stop;
}')
EOF
FETCH_MARGIN=400     # kept back so the results can be written and fetched
OUTER_BACKOFF=600    # the outer stop fires this far before the stopping point

echo "[${TAG}] price USD ${PRICE}/h, budget USD ${BUDGET}, timeout ${REMOTE_T} s, stopping at ${STOP_AT} s"
[ -n "$TIMEOUT_NOTE" ] && echo "[${TAG}] ${TIMEOUT_NOTE}"

# --- the environment record: named, non-secret variables only ---------------
{
  echo "# named non-secret variables seen by this run; nothing else is listed"
  for name in PRICE_USD_PER_HOUR BUDGET_LEFT_USD REMOTE_TIMEOUT INSTANCE_TYPE \
              LAMBDA_INSTANCE_ID GIT_COMMIT CUDA_VISIBLE_DEVICES; do
    printf '%s=%s\n' "$name" "${!name:-}"
  done
  printf 'REMOTE_TIMEOUT_SEEN=%s\n' "$REMOTE_T"
  printf 'STOP_AT_SECONDS=%s\n' "$STOP_AT"
  printf 'M4_T0=%s\n' "$T0"
  printf 'APT_PACKAGES=%s\n' "$APT_PACKAGES"
  [ -n "$TIMEOUT_NOTE" ] && printf 'NOTE=%s\n' "$TIMEOUT_NOTE"
  printf 'HF_TOKEN_PRESENT=%s\n' "$([ -n "${HF_TOKEN:-}" ] && echo yes || echo no)"
} > "${OUT}/env.txt"

# --- the isolated Python environment ---------------------------------------
if [ ! -x "${VENV}/bin/python3" ]; then
  echo "[${TAG}] creating the Python environment (system packages stay visible)"
  python3 -m venv --system-site-packages "$VENV"
fi
PY="${VENV}/bin/python3"
"$PY" -m pip install -q --upgrade pip || true

# --- helpers ----------------------------------------------------------------
elapsed() { echo $(( $(date +%s) - T0 )); }

seconds_left() {
  local left=$(( STOP_AT - $(elapsed) - OUTER_BACKOFF ))
  [ "$left" -lt 1 ] && left=1
  echo "$left"
}

# Stop every tool this run started, by process group id, never by name. A kill
# by name on a shared box could reach something that is not ours.
kill_recorded_groups() {
  local file="${OUT}/process_groups.txt"
  [ -f "$file" ] || return 0
  while read -r pgid; do
    case "$pgid" in ''|*[!0-9]*) continue ;; esac
    kill -TERM "-${pgid}" 2>/dev/null || true
  done < "$file"
  sleep 3
  while read -r pgid; do
    case "$pgid" in ''|*[!0-9]*) continue ;; esac
    kill -KILL "-${pgid}" 2>/dev/null || true
  done < "$file"
  echo "[${TAG}] stopped the recorded tool process groups"
}

finish() {
  local code="$1"
  printf '%s\n' "$code" > "${OUT}/RUN_DONE"
  echo "[${TAG}] finished with exit code ${code}"
  exit "$code"
}

# The outer stop fired: the decisions still get written, from whatever
# finished, and the run is reported as a guard stop rather than a failure.
after_outer_timeout() {
  echo "[${TAG}] the outer stop fired; stopping tools and writing the decisions"
  kill_recorded_groups
  "$PY" run_${TAG}.py --stage endpoints --after-timeout \
    >> "${OUT}/console.log" 2>&1 || true
  finish 3
}

# Run one part of the measurement under an outer stop. A return code of 124
# means that stop fired.
run_stage_group() {
  local group="$1"
  local limit
  limit="$(seconds_left)"
  echo "[${TAG}] ${group}: starting with ${limit} s before the outer stop"
  set +e
  timeout -k 30 "$limit" "$PY" run_${TAG}.py --stage "$group" \
    >> "${OUT}/console.log" 2>&1
  local rc=$?
  set -e
  echo "[${TAG}] ${group}: returned ${rc}"
  return "$rc"
}

# --- stage 1: install, downloads, start-up check, and the harness controls --
# The download token is in the environment for this part only.
rc=0
run_stage_group extract || rc=$?
if [ "$rc" = "124" ]; then after_outer_timeout; fi

# The token is for the downloads and for nothing else. From here on it does not
# exist, in this shell or in any child.
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN || true

if [ "$rc" != "0" ]; then
  echo "[${TAG}] the install-and-controls part failed; writing void records"
  "$PY" run_${TAG}.py --stage endpoints >> "${OUT}/console.log" 2>&1 || true
  finish "$rc"
fi

# --- stage 2: the anchor, then the four measurements ------------------------
rc=0
run_stage_group generate || rc=$?
if [ "$rc" = "124" ]; then after_outer_timeout; fi

# --- stage 3: the decisions, the validity file and the summary --------------
# This part always runs, whatever happened above.
set +e
"$PY" run_${TAG}.py --stage endpoints >> "${OUT}/console.log" 2>&1
end_rc=$?
set -e

# A failure in the measurements outranks the decisions stage's own code: the
# operator must see the reason the run stopped, not the last thing that ran.
if [ "$rc" != "0" ] && [ "$rc" != "3" ]; then
  finish "$rc"
fi
if [ "$rc" = "3" ] && [ "$end_rc" = "0" ]; then
  finish 3
fi
finish "$end_rc"
