#!/usr/bin/env bash
# On-box batch for measure run m2: runs the runner's stages in order on the rented GPU box.
#
# The launcher runs it from ~/m2_run as:   bash remote_run_m2.sh bash onbox_m2.sh
# No venv and no pip install here. The execution note's toolchain rule uses the image's python3, numpy and
# scipy as they are, and nvcc from PATH or /usr/local/cuda*. The remote bootstrap's own installs are left alone.
#
# Results go under results_m2/out/; the compiled library goes under results_m2/build/.
# Before every stage a guard runs. It stops cleanly before projected spend reaches BUDGET_LEFT_USD.
# It also caps each stage so the run ends inside REMOTE_TIMEOUT (3600 s unless set).
# After the last stage, after any stop and after any failure, it writes m2_summary.json and then RUN_DONE.
# RUN_DONE holds the exit code: 0 all stages ran; 2 toolchain; 3 no GPU; 4 guard inputs missing;
# 5 guard stop; 6 zero-dispersion halt; 124 a stage hit its time cap; 1 any other stage failure.
set -uo pipefail
cd "$(dirname "$0")" || exit 1
OUT=results_m2/out
BUILD=results_m2/build
REMOTE_TIMEOUT=${REMOTE_TIMEOUT:-3600}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONUNBUFFERED=1
STAGES="build gpucheck anchor timers residual_sweep thomas_gpu pcr_gpu cusparse_gpu thomas_batched_gpu launch_probe cpu_dgtsv endpoints"

# A results directory left by an earlier run on this box is moved aside, never mixed in.
if [ -d "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
  PREV="results_m2/out_prev_$(date -u +%Y%m%dT%H%M%SZ)"
  mv "$OUT" "$PREV" && echo "[onbox] earlier results moved to $PREV"
fi
mkdir -p "$OUT/logs" "$BUILD"

# Seconds since this process started. remote_run_m2.sh execs into this script, so that is its start.
elapsed(){ local e; e=$(ps -o etimes= -p $$ 2>/dev/null | tr -d ' '); if [ -n "$e" ]; then echo "$e"; else echo "$SECONDS"; fi; }
# Box uptime in seconds: the spend clock for the cost guard.
uptime_s(){ cut -d' ' -f1 /proc/uptime 2>/dev/null || echo 0; }

finish(){
  local rc=$1 reason=$2
  if [ -f run_m2.py ]; then
    python3 run_m2.py summary --exit-code "$rc" --stop-reason "$reason" 2>&1 | tee -a "$OUT/logs/summary.log"
  fi
  echo "$rc" > "$OUT/RUN_DONE"
  echo "[onbox] RUN_DONE rc=$rc ($reason)"
  exit "$rc"
}

for f in run_m2.py frozen/provenance.py; do
  [ -f "$f" ] || finish 2 "payload file missing: $f"
done

echo "[onbox] start $(date -u +%FT%TZ) REMOTE_TIMEOUT=${REMOTE_TIMEOUT}s PRICE_USD_PER_HOUR=${PRICE_USD_PER_HOUR:-unset}" \
     "BUDGET_LEFT_USD=${BUDGET_LEFT_USD:-unset} INSTANCE_TYPE=${INSTANCE_TYPE:-unset} elapsed=$(elapsed)s"
echo "[onbox] stages: $STAGES"

for st in $STAGES; do
  G=$(python3 run_m2.py guard --remote-timeout "$REMOTE_TIMEOUT" --elapsed "$(elapsed)" --uptime "$(uptime_s)" \
        --price "${PRICE_USD_PER_HOUR:-}" --budget "${BUDGET_LEFT_USD:-}" 2>>"$OUT/logs/guard.log")
  case "$G" in
    "RUN "*)    ALLOW=${G#RUN } ;;
    "STOP "*)   finish 5 "${G#STOP } (before stage $st)" ;;
    "BADENV "*) finish 4 "${G#BADENV } (before stage $st)" ;;
    *)          finish 1 "guard gave no verdict before stage $st: $G" ;;
  esac
  echo "[onbox] stage $st: cap ${ALLOW}s"
  T0=$(date -u +%s)
  timeout -k 30 "$ALLOW" python3 run_m2.py "$st" 2>&1 | tee "$OUT/logs/$st.log"
  rc=${PIPESTATUS[0]}
  T1=$(date -u +%s)
  printf '{"stage": "%s", "rc": %d, "start_utc": %d, "end_utc": %d, "cap_s": %d}\n' \
         "$st" "$rc" "$T0" "$T1" "$ALLOW" >> "$OUT/stages.jsonl"
  if [ "$rc" -ne 0 ]; then
    if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
      finish 124 "time guard: stage $st stopped at its ${ALLOW}s cap"
    fi
    finish "$rc" "stage $st failed (rc=$rc)"
  fi
done
finish 0 "all stages ran"
