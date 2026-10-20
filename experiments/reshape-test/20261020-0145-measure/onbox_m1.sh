#!/usr/bin/env bash
# On-box driver for measurement m1: time one batched GR4J forward pass on this GPU box.
#
# How it starts. Inside ~/m1_run, under the launcher's `timeout`, the launcher runs:
#     bash remote_run_m1.sh bash onbox_m1.sh
# The launcher forwards PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and INSTANCE_TYPE in the environment.
#
# What it does, in order:
#   1. Python toolchain. The image's preinstalled JAX is used as is; it is never installed or upgraded.
#      The only install is: python3 -m pip install --user pyreadr.
#      jax, jaxlib and numpy versions are read before and after that install; any change stops the run.
#      JAX must list a GPU. Otherwise RUN_VALID.json says false and the exit code is 3.
#      There is no virtual environment: one would hide the preinstalled JAX.
#   2. R toolchain: one apt-get attempt for R and gfortran, then one R CMD INSTALL of the committed airGR.
#      A failure here does not stop the run. The anchor then falls back to the page value 0.495.
#   3. env.txt: jax and jaxlib versions, JAX devices, pip freeze, R --version, nvidia-smi -q, nproc.
#   4. run_m1.py stages: extract; airGR anchor; JAX anchor; timer checks; timing on GPU then CPU;
#      overhead probes on GPU then CPU; endpoints.
# A cost guard runs before every stage and between timed passes.
# It stops cleanly before projected spend reaches BUDGET_LEFT_USD.
# A time guard keeps the run inside the launcher's cap (REMOTE_TIMEOUT, 5,400 s unless set).
#
# Results: results_m1/out/.
# m1_summary.json there restates run validity, labels and every decision; the launcher fetches it first.
# It is rewritten after the endpoints stage, after any early stop, and just before RUN_DONE.
# RUN_DONE there holds this script's exit code.
# Exit codes: 0 finished; 1 a stage crashed; 2 setup or install failed; 3 JAX sees no GPU;
#             4 stopped cleanly by the cost or time guard; 5 a degenerate output halted the run;
#             143 stopped by a signal.
set -uo pipefail
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" || exit 2

OUT=results_m1/out
LOG="$OUT/logs"
mkdir -p "$LOG"
RUN="python3 -u run_m1.py"
STOPPING=0

say(){ echo "[onbox $(date -u +%H:%M:%S)] $*"; }

finish(){
  $RUN summary --out "$OUT" 2>&1 | tee -a "$LOG/summary.log"
  echo "$1" > "$OUT/RUN_DONE"
  say "RUN_DONE rc=$1"
  exit "$1"
}

# An early stop relabels every finished row and record, then writes whatever records can be derived.
early_stop(){
  local rc=$1 reason=$2
  STOPPING=1
  say "early stop (rc=$rc): $reason"
  $RUN stop --out "$OUT" --reason "$reason" 2>&1 | tee -a "$LOG/stop.log"
  $RUN endpoints --out "$OUT" 2>&1 | tee -a "$LOG/endpoints_after_stop.log"
  finish "$rc"
}

on_signal(){
  trap '' TERM INT HUP
  if [ "$STOPPING" = 1 ]; then finish 143; fi
  early_stop 143 "stopped by a signal before the run finished (most likely the launcher's time cap)"
}
trap on_signal TERM INT HUP

guard(){
  local stage=$1 g
  $RUN guard --out "$OUT" --stage "$stage" 2>&1 | tee -a "$LOG/guard.log"
  g=${PIPESTATUS[0]}
  case "$g" in
    0) ;;
    10) early_stop 4 "the cost or time guard stopped the run before stage '$stage'" ;;
    *) early_stop 2 "the cost guard could not run before stage '$stage' (exit $g)" ;;
  esac
}

stage(){
  local name=$1 rc
  shift
  guard "$name"
  say "stage $name: $*"
  "$@" 2>&1 | tee "$LOG/$name.log"
  rc=${PIPESTATUS[0]}
  say "stage $name exit $rc"
  case "$rc" in
    0) ;;
    4) early_stop 4 "stage '$name' was stopped by the cost or time guard" ;;
    5) early_stop 5 "stage '$name' halted on a degenerate output (see $LOG/$name.log)" ;;
    *) early_stop "$rc" "stage '$name' failed with exit code $rc (see $LOG/$name.log)" ;;
  esac
}

# ---- Preflight: price, budget and the time cap -------------------------------------------------
say "start in $PWD on $(hostname); $(python3 --version 2>&1); $(nproc) vCPUs"
CAP=${REMOTE_TIMEOUT:-5400}
NOW=$(date +%s)
PCOMM=$(ps -o comm= -p "$PPID" 2>/dev/null | tr -d ' ')
PELAPSED=0
if [ "$PCOMM" = "timeout" ]; then PELAPSED=$(ps -o etimes= -p "$PPID" 2>/dev/null | tr -d ' '); fi
case "$PELAPSED" in ''|*[!0-9]*) PELAPSED=0 ;; esac
export M1_DEADLINE_EPOCH=$(( NOW - PELAPSED + CAP - 180 ))
say "time cap ${CAP}s; parent '${PCOMM:-unknown}' started ${PELAPSED}s ago; stages must end by epoch $M1_DEADLINE_EPOCH"
export PRICE_USD_PER_HOUR="${PRICE_USD_PER_HOUR:-}"
export BUDGET_LEFT_USD="${BUDGET_LEFT_USD:-}"
say "price USD ${PRICE_USD_PER_HOUR:-unset} per hour; budget left USD ${BUDGET_LEFT_USD:-unset}; instance type ${INSTANCE_TYPE:-not forwarded}"
guard preflight

# ---- 1. Python toolchain: the image's JAX as is; pyreadr is the only install -------------------
guard pip
$RUN versions --label before_pip --out "$OUT" 2>&1 | tee "$LOG/versions_before_pip.log"
VB=${PIPESTATUS[0]}
[ "$VB" = 0 ] || early_stop 2 "reading package versions before the install failed with exit code $VB"
say "python3 -m pip install --user pyreadr (jax, jaxlib and numpy stay as the image has them)"
timeout 600 python3 -m pip install --user pyreadr > "$LOG/pip_install.log" 2>&1
PIP_RC=$?
tail -n 3 "$LOG/pip_install.log"
[ "$PIP_RC" = 0 ] || early_stop 2 "pip install --user pyreadr failed with exit code $PIP_RC (see $LOG/pip_install.log)"
$RUN versions --label after_pip --compare-to "$LOG/versions_before_pip.json" --out "$OUT" 2>&1 \
  | tee "$LOG/versions_after_pip.log"
VA=${PIPESTATUS[0]}
case "$VA" in
  0) ;;
  2) early_stop 2 "installing pyreadr changed jax, jaxlib or numpy (see $LOG/versions_after_pip.log)" ;;
  *) early_stop 2 "reading package versions after the install failed with exit code $VA" ;;
esac
$RUN gpu-check --out "$OUT" 2>&1 | tee "$LOG/gpu_check.log"
GC=${PIPESTATUS[0]}
case "$GC" in
  0) ;;
  3) early_stop 3 "JAX lists no GPU; RUN_VALID.json says false; no silent CPU fallback" ;;
  *) early_stop 2 "the GPU check crashed with exit code $GC" ;;
esac

# ---- 2. R toolchain and airGR (one attempt each) ------------------------------------------------
guard r_install
export R_LIBS_USER="$PWD/Rlib"   # a library folder this user can write; Rscript later reads it too
mkdir -p "$R_LIBS_USER"
say "sudo apt-get install -y r-base-core gfortran (one attempt)"
timeout 900 sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y r-base-core gfortran > "$LOG/apt_r.log" 2>&1
APT_RC=$?
RCMD_RC=not_tried
if [ "$APT_RC" = 0 ]; then
  say "R CMD INSTALL data/airGR_1.7.9.tar.gz (one attempt) into $R_LIBS_USER"
  timeout 900 R CMD INSTALL data/airGR_1.7.9.tar.gz > "$LOG/r_cmd_install.log" 2>&1
  RCMD_RC=$?
fi
printf 'apt_rc=%s\nrcmd_rc=%s\nr_libs_user=%s\n' "$APT_RC" "$RCMD_RC" "$R_LIBS_USER" > "$OUT/airgr_install_status.txt"
say "apt-get exit $APT_RC; R CMD INSTALL exit $RCMD_RC (a failure means the anchor uses the page value)"
{
  R --version 2>&1 | head -n 1
  gfortran --version 2>&1 | head -n 1
  Rscript -e 'cat("airGR", as.character(packageVersion("airGR")), "\n")' 2>&1
} > "$LOG/versions_r.log" 2>&1
cat "$LOG/versions_r.log"

# ---- 3. Environment record ----------------------------------------------------------------------
{
  echo "== utc date"; date -u
  echo "== nproc"; nproc
  echo "== python3 --version"; python3 --version
  echo "== jax.__version__ and jaxlib.__version__ (the image's preinstalled JAX, used as is)"
  $RUN versions --label env --out "$OUT"
  echo "== JAX devices (GPU check)"; cat "$LOG/gpu_check.log"
  echo "== pip freeze"; python3 -m pip freeze
  echo "== R --version"; R --version || echo "R is not available"
  echo "== nvidia-smi -q"; nvidia-smi -q
  echo "== price and budget"; echo "PRICE_USD_PER_HOUR=$PRICE_USD_PER_HOUR BUDGET_LEFT_USD=$BUDGET_LEFT_USD"
  echo "== instance"; echo "LAMBDA_INSTANCE_ID=${LAMBDA_INSTANCE_ID:-unset} INSTANCE_TYPE=${INSTANCE_TYPE:-not forwarded}"
} > "$OUT/env.txt" 2>&1
say "wrote $OUT/env.txt"

# ---- 4. Stages, in the binding order ------------------------------------------------------------
stage extract      $RUN extract --out "$OUT"
stage anchor_airgr $RUN generate --part anchor_airgr --out "$OUT"
stage anchor_jax   $RUN generate --part anchor_jax --out "$OUT"
stage timers       $RUN generate --part timers --out "$OUT"
stage timing_gpu   $RUN generate --part timing --backend gpu --out "$OUT"
stage timing_cpu   $RUN generate --part timing --backend cpu --out "$OUT"
stage probe_gpu    $RUN generate --part probe --backend gpu --out "$OUT"
stage probe_cpu    $RUN generate --part probe --backend cpu --out "$OUT"
stage endpoints    $RUN endpoints --out "$OUT"

say "all stages finished; run validity:"
head -c 3000 "$OUT/RUN_VALID.json"; echo
finish 0
