#!/usr/bin/env bash
# Run one command detached on the dev box and collect its outputs and receipt.
# Usage: boxrun.sh --name N --cmd 'CMD' --remote-dir D --timeout SECONDS --fetch REMOTE_SUBDIR --to LOCAL_DIR --receipt FILE.json
set +x
set -euo pipefail
umask 077
BOX=${BOX:-$HOME/.cache/metis-serve/box.sh}
NAME=; CMD=; DIR=; LIMIT=; SUBDIR=; DEST=; RECEIPT=
GPU_SAMPLES=$(mktemp); RC=; TIMED_OUT=false; FETCHED=false; START=$(date -u +%Y-%m-%dT%H:%M:%SZ); BEGIN=$SECONDS
die() { echo "$*" >&2; exit 2; }
finish() {
  local status=$?; trap - EXIT
  [[ $status == 0 || $status == 3 ]] || status=2
  if [[ -n $RECEIPT ]]; then
    python3 - "$RECEIPT" "$NAME" "$RC" "$TIMED_OUT" "$((SECONDS - BEGIN))" "$FETCHED" "$START" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$GPU_SAMPLES" <<'PY' || status=2
import json, math, os, sys
p, name, rc, timed_out, wall, fetched, start, end, samples = sys.argv[1:]
values = []
for line in open(samples):
    try:
        value = float(line.strip())
        if math.isfinite(value) and 0 <= value <= 100:
            values.append(value)
    except ValueError:
        pass
os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
with open(p + ".tmp", "w") as f:
    json.dump(dict(name=name, rc=int(rc) if rc else None, timed_out=timed_out == "true",
                   wall_s=int(wall), gpu_busy_s=sum(values) * 0.02, gpu_busy_known=bool(values), fetched=fetched == "true", started_utc=start, ended_utc=end), f)
    f.write("\n")
os.replace(p + ".tmp", p)
PY
  fi
  rm -f -- "$GPU_SAMPLES"
  exit "$status"
}
trap finish EXIT
trap 'exit 2' INT TERM HUP
while (($#)); do
  (($# >= 2)) || die "Missing value for $1"
  case $1 in
    --name) NAME=$2;; --cmd) CMD=$2;; --remote-dir) DIR=$2;; --timeout) LIMIT=$2;;
    --fetch) SUBDIR=$2;; --to) DEST=$2;; --receipt) RECEIPT=$2;; *) die "Unknown option: $1";;
  esac
  shift 2
done
[[ $NAME =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.-]*$ && -n $CMD && -n $DIR && -n $SUBDIR && -n $DEST && -n $RECEIPT ]] || die 'Missing or invalid arguments (see Usage).'
[[ $LIMIT =~ ^[1-9][0-9]*$ && ${#LIMIT} -le 9 ]] || die 'Timeout must be a positive integer (at most 9 digits).'
fetch() {
  if [[ -n ${FETCH:-} ]]; then "$FETCH" "$1" "$2"; return; fi
  local ip
  ip=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["ip"])' "$HOME/.cache/metis-serve/state.json") || return
  scp -r -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -o ServerAliveInterval=30 \
    -o BatchMode=yes -o ExitOnForwardFailure=yes -i "$HOME/.ssh/lambda_ed25519" "ubuntu@$ip:$1" "$2"
}
# Quote each value before embedding it in the remote shell or run script.
printf -v script '#!/usr/bin/env bash\ncd -- %q || exit 2\nsamples=%q\n: > "$samples"\n(while :; do nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits >> "$samples" 2>/dev/null; sleep 2; done) &\nsampler=$!\ntrap "kill \"$sampler\" 2>/dev/null; wait \"$sampler\" 2>/dev/null" EXIT\ntimeout %q bash -c %q >%q 2>&1\nrc=$?\nkill "$sampler" 2>/dev/null; wait "$sampler" 2>/dev/null\ntrap - EXIT\nprintf "%%s\\n" "$rc" >%q && mv -- %q %q\n' \
  "$DIR" "$NAME.gpu" "$LIMIT" "$CMD" "$NAME.log" "$NAME.rc.tmp" "$NAME.rc.tmp" "$NAME.rc"
# Background only the runner; setup errors must reach the caller.
printf -v launch 'mkdir -p -- %q && rm -f -- %q %q && printf %%s %q >%q && { setsid nohup bash %q </dev/null >/dev/null 2>&1 & }' \
  "$DIR" "$DIR/$NAME.rc" "$DIR/$NAME.rc.tmp" "$script" "$DIR/$NAME.sh" "$DIR/$NAME.sh"
"$BOX" "bash -c $(printf '%q' "$launch")" || die 'Remote launch failed.'
printf -v poll 'cat -- %q' "$DIR/$NAME.rc"
deadline=$((BEGIN + LIMIT + 600))
while :; do
  remaining=$((deadline - SECONDS))
  if ((remaining <= 0)); then TIMED_OUT=true; break; fi
  if value=$(timeout "$remaining" "$BOX" "$poll") && [[ $value =~ ^(0|[1-9][0-9]{0,2})$ ]] && ((value <= 255)); then
    RC=$value; [[ $RC != 124 ]] || TIMED_OUT=true; break
  fi
  remaining=$((deadline - SECONDS)); ((remaining > 0)) || continue
  sleep "$((remaining < 20 ? remaining : 20))"
done
# Telemetry is optional and must never turn an otherwise successful run into a failure.
printf -v telemetry 'cat -- %q' "$DIR/$NAME.gpu"
timeout 30 "$BOX" "$telemetry" > "$GPU_SAMPLES" 2>/dev/null || true
if mkdir -p -- "$DEST"; then
  FETCHED=true
  fetch "$DIR/$SUBDIR" "$DEST" || FETCHED=false
  fetch "$DIR/$NAME.log" "$DEST" || FETCHED=false
fi
[[ $TIMED_OUT != true ]] || exit 3
[[ $RC == 0 && $FETCHED == true ]] || exit 2
