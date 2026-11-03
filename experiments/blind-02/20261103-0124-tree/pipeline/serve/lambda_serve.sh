#!/usr/bin/env bash
# Serve one Lambda GPU through a local SSH tunnel. No public inference listener.
# Usage: bash serve/lambda_serve.sh up [--model M] [--types "TYPE ..."] [--max-hours 6] [--port 18000]
#        bash serve/lambda_serve.sh up --dev [--fs NAME] [--types "TYPE ..."] [--max-hours 8]
#        bash serve/lambda_serve.sh status | down
# Only one serve or dev box may exist at once: both modes share one state file.
# Dev commands: ~/.cache/metis-serve/box.sh <command...>
# Credentials: LAMBDA_KEYS_FILE (default /home/hal/dev/interp/dm_hack/.keys), LAMBDA_KEY_ONE=...
# The local watchdog requires this machine to remain awake and connected.
set +x
set -euo pipefail
umask 077
API=https://cloud.lambda.ai/api/v1
CACHE=$HOME/.cache/metis-serve; STATE=$CACHE/state.json
SELF=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/$(basename -- "${BASH_SOURCE[0]}")
export LAMBDA_KEYS_FILE=${LAMBDA_KEYS_FILE:-/home/hal/dev/interp/dm_hack/.keys}
die() { echo "$*" >&2; exit 1; }
json() { python3 -c "import json,sys; d=json.load(sys.stdin); $1" "${@:2}"; }
api() {
  local key= line path=$1; shift
  while IFS= read -r line || [[ -n $line ]]; do
    if [[ $line == LAMBDA_KEY_ONE=* ]]; then key=${line#*=}; fi
  done < "$LAMBDA_KEYS_FILE"
  key=${key%$'\r'}; key=${key#\"}; key=${key%\"}; key=${key#\'}; key=${key%\'}
  [[ -n $key ]] || die "Missing LAMBDA_KEY_ONE in LAMBDA_KEYS_FILE"
  printf 'Authorization: Bearer %s\n' "$key" | curl -fsS --connect-timeout 15 --max-time 30 \
    -A 'curl/metis-serve' -H @- -H 'Content-Type: application/json' "$API/$path" "$@"
}
remote() {
  local opts=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -o ServerAliveInterval=30
    -o BatchMode=yes -o ExitOnForwardFailure=yes -i "$HOME/.ssh/lambda_ed25519")
  if [[ $1 == --tunnel ]]; then
    ssh "${opts[@]}" -N -L "127.0.0.1:$PORT:127.0.0.1:8000" "ubuntu@$IP" </dev/null >"$CACHE/tunnel.log" 2>&1 & TUNNEL=$!
  else ssh "${opts[@]}" "ubuntu@$IP" "$@"; fi
}
snapshot() {
  api instances | json 'assert isinstance(d["data"], list); print(json.dumps(next((x for x in d["data"] if x["id"] == sys.argv[1]), {"status":"terminated"})))' "$ID"
}
save() {
  python3 - "$STATE" "$ID" "$IP" "$TYPE" "$REGION" "$PRICE" "$MODEL" "$PORT" "$START" "$TUNNEL" "$WATCH" "$MODE" "$FS" "$BOX" <<'PY'
import json, os, sys
p = sys.argv[1]
d = dict(zip("instance_id ip type region price_usd_h model port started_utc tunnel_pid watchdog_pid mode filesystem box_helper".split(), sys.argv[2:]))
for k in ("port", "tunnel_pid", "watchdog_pid"): d[k] = int(d[k] or 0)
d["price_usd_h"] = float(d["price_usd_h"])
with open(p + ".tmp", "w") as f: json.dump(d, f, indent=2); f.write("\n")
os.replace(p + ".tmp", p)
box = os.path.join(os.path.dirname(p), "box.json")
with open(box + ".tmp", "w") as f:
    json.dump({k: d[k] for k in ("type", "region", "price_usd_h", "started_utc")}, f, indent=2)
    f.write("\n")
os.replace(box + ".tmp", box)
PY
}
load() {
  local values
  values=$(json 'print("\n".join(str(d.get(k, "serve" if k == "mode" else "")) for k in "instance_id ip type region price_usd_h model port started_utc tunnel_pid watchdog_pid mode filesystem box_helper".split()))' < "$STATE")
  mapfile -t fields <<< "$values"
  ID=${fields[0]}; IP=${fields[1]}; TYPE=${fields[2]}; REGION=${fields[3]}; PRICE=${fields[4]}
  MODEL=${fields[5]}; PORT=${fields[6]}; START=${fields[7]}; TUNNEL=${fields[8]}; WATCH=${fields[9]}
  MODE=${fields[10]}; FS=${fields[11]:-}; BOX=${fields[12]:-}
}
down() {
  echo "Terminating $ID"
  until [[ $(snapshot 2>/dev/null | json 'print(d["status"])' 2>/dev/null || echo unknown) == terminated ]]; do
    api instance-operations/terminate -X POST --data "{\"instance_ids\":[\"$ID\"]}" >/dev/null 2>&1 || true
    echo "Waiting for termination: $ID"; sleep 20
  done
  [[ $TUNNEL -gt 1 ]] && kill "$TUNNEL" 2>/dev/null || true
  [[ $WATCH -gt 1 && $WATCH != $$ ]] && kill -- "-$WATCH" 2>/dev/null || true
  python3 - "$CACHE/box.json" "$TYPE" "$REGION" "$PRICE" "$START" <<'PY'
import datetime, json, os, sys
p, kind, region, price, start = sys.argv[1:]
end = datetime.datetime.now(datetime.timezone.utc)
hours = max(0, (end - datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds() / 3600)
d = dict(type=kind, region=region, price_usd_h=float(price), started_utc=start,
         ended_utc=end.isoformat().replace("+00:00", "Z"), hours=hours)
with open(p + ".tmp", "w") as f:
    json.dump(d, f, indent=2)
    f.write("\n")
os.replace(p + ".tmp", p)
PY
  if [[ -f $STATE ]]; then mv -- "$STATE" "$CACHE/state.$ID.$(date -u +%Y%m%dT%H%M%SZ).json"; fi
  echo "Terminated $ID; state archived."
}
case ${1:-} in
  _watch)
    expected=$2; deadline=$3
    delay=$((deadline - $(date -u +%s))); ((delay <= 0)) || sleep "$delay"
    [[ -f $STATE ]] || exit 0
    load; [[ $ID == "$expected" ]] || exit 0
    down; exit 0 ;;
  status|down)
    [[ -f $STATE ]] || { echo 'No managed instance.'; exit 0; }
    load
    if [[ $1 == down ]]; then down; exit 0; fi
    instance_state=$(snapshot | json 'print(d["status"])') || instance_state=unavailable
    echo "Instance $ID: $instance_state"
    echo "mode: $MODE"
    if [[ $MODE == dev ]]; then
      if [[ -n $FS ]]; then
        if remote "mountpoint -q -- $(printf '%q' "/lambda/nfs/$FS")"; then echo "Filesystem /lambda/nfs/$FS: mounted"
        else echo "Filesystem /lambda/nfs/$FS: not mounted or SSH unavailable"; fi
      else echo 'Filesystem: none attached'; fi
    else
    if kill -0 "$TUNNEL" 2>/dev/null && [[ $TUNNEL -gt 1 ]]; then echo 'Tunnel: alive'; else echo 'Tunnel: down'; fi
    if curl -fsS --max-time 5 "http://127.0.0.1:$PORT/v1/models" >/dev/null; then echo 'Models: ready'; else echo 'Models: unavailable'; fi
    fi
    python3 - "$START" "$PRICE" <<'PY'
import datetime, sys
h = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(sys.argv[1].replace("Z", "+00:00"))).total_seconds() / 3600
print(f"Elapsed: {h:.2f} hours; estimated USD: {h * float(sys.argv[2]):.2f}")
PY
    exit 0 ;;
  up) shift ;;
  *) die 'Usage: lambda_serve.sh up [--dev [--fs NAME]] [--model M] [--types "TYPE ..."] [--max-hours HOURS (serve: 6, dev: 8)] [--port 18000] | status | down' ;;
esac
if [[ -f $STATE ]]; then
  load
  [[ $(snapshot | json 'print(d["status"])') == terminated ]] || die "Managed instance $ID is live; run down first."
  down
fi
MODEL=openai/gpt-oss-120b; TYPES='gpu_1x_h100_pcie gpu_1x_h100_sxm5 gpu_1x_a100_sxm4_80gb'; HOURS=; PORT=18000
MODE=serve; FS=; BOX=
while (($#)); do
  if [[ $1 == --dev ]]; then MODE=dev; shift; continue; fi
  (($# >= 2)) || die "Missing value for $1"
  case $1 in --model) MODEL=$2;; --types) TYPES=$2;; --max-hours) HOURS=$2;; --port) PORT=$2;; --wait-capacity) WAITCAP=$2;; --fs) FS=$2;; *) die "Unknown option: $1";; esac
  shift 2
done
if [[ $MODE == dev ]]; then HOURS=${HOURS:-8}; else HOURS=${HOURS:-6}; fi
[[ -z $FS || $MODE == dev ]] || die '--fs requires --dev'
SECONDS_LIMIT=$(python3 - "$HOURS" "$PORT" <<'PY'
import math, sys
h, p = float(sys.argv[1]), int(sys.argv[2])
assert math.isfinite(h) and h > 0 and h * 3600 >= 1 and 1 <= p <= 65535, "Invalid hours or port"
print(math.ceil(h * 3600))
PY
)
[[ -n $MODEL && $MODEL != -* ]] || die 'Invalid model'
if [[ $MODE == serve ]]; then
python3 - "$PORT" <<'PY'
import socket, sys
with socket.socket() as s: s.bind(("127.0.0.1", int(sys.argv[1])))
PY
fi
FS_REGIONS=
if [[ -n $FS ]]; then
  FS_REGIONS=$(api file-systems | json 'print(" ".join(x["region"]["name"] for x in d["data"] if x["name"] == sys.argv[1]))' "$FS")
  [[ -n $FS_REGIONS ]] || die "Filesystem not found: $FS"
fi
cap_deadline=$(( $(date -u +%s) + ${WAITCAP:-0} * 60 ))   # --wait-capacity MIN: poll every 2 min until a requested type has capacity
while :; do
selection=$(api instance-types | json '
for name in sys.argv[1].split():
    item = d["data"].get(name, {}); regions = item.get("regions_with_capacity_available", [])
    regions = [r for r in regions if not sys.argv[2] or r["name"] in sys.argv[2].split()]
    if regions:
        print(name, regions[0]["name"], item["instance_type"]["price_cents_per_hour"] / 100); break
' "$TYPES" "$FS_REGIONS")
if [[ -n $selection ]]; then
  read -r TYPE REGION PRICE <<< "$selection"
  echo "Selected $TYPE in $REGION at USD $PRICE/hour"
  mkdir -p "$CACHE"
  payload=$(python3 -c 'import json,sys; print(json.dumps(dict(instance_type_name=sys.argv[1],region_name=sys.argv[2],ssh_key_names=["latent_verify_hal_20260721"],name="metis-serve",**({"file_system_names":[sys.argv[3]]} if sys.argv[3] else {}))))' "$TYPE" "$REGION" "$FS")
  ID=$( (api instance-operations/launch -X POST --data "$payload" || true) | json 'print(d["data"]["instance_ids"][0])' 2>/dev/null || true)
  [[ -n $ID ]] && break
  echo "Launch of $TYPE refused (capacity taken meanwhile?)"
fi
(( $(date -u +%s) < cap_deadline )) || die 'No requested GPU type has capacity.'
echo "No capacity for: $TYPES; retrying in 2 min"; sleep 120
done

[[ -n $ID ]] || die 'Launch returned no instance ID.'
IP=; TUNNEL=0; WATCH=0; START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
trap 'exit 130' INT HUP TERM
trap 'rc=$?; trap - EXIT; if ((rc)); then echo "Startup failed; saving ~/vllm.log to $CACHE/vllm_failed.log, then terminating $ID" >&2; [[ -n ${IP:-} ]] && { (remote "tail -n 300 ~/vllm.log; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader") > "$CACHE/vllm_failed.log" 2>&1 || true; }; down; fi' EXIT   # down runs even when the box never answered ssh
save
setsid nohup bash "$SELF" _watch "$ID" "$(( $(date -u +%s) + SECONDS_LIMIT ))" </dev/null >"$CACHE/watchdog.log" 2>&1 & WATCH=$!
save
for ((i=0; i<80; i++)); do
  info=$(snapshot); IP=$(printf '%s' "$info" | json 'print(d.get("ip") or "")')
  [[ $(printf '%s' "$info" | json 'print(d["status"])') == active && -n $IP ]] && break
  sleep 15
done
((i < 80)) || die 'Instance never became active with an IP.'
save
for ((i=0; i<90; i++)); do remote true 2>/dev/null && break; sleep 10; done   # up to 15 min: a GH200 took more than 4
((i < 24)) || die 'SSH never became ready.'
if [[ $MODE == dev ]]; then
  BOX=$CACHE/box.sh
  {
    printf '#!/usr/bin/env bash\nset -euo pipefail\nIP=%q\n' "$IP"
    declare -f remote
    cat <<'HELPER'
(($#)) || { echo 'Usage: box.sh <command...>' >&2; exit 1; }
remote "$*"   # like ssh host cmd: the words are joined and the box's shell parses them
HELPER
  } > "$BOX"
  chmod 700 "$BOX"
  save
  kill -0 "$WATCH" 2>/dev/null || die 'Watchdog exited unexpectedly.'
  trap - EXIT INT HUP TERM
  echo "Ready: dev box $ID; commands: $BOX <command...>"
  exit 0
fi
remote "bash -s -- $(printf '%q' "$MODEL")" <<'REMOTE'
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null || { curl -fsSL https://astral.sh/uv/install.sh | sh; }
uv venv --python 3.12 "$HOME/vllm-venv"
uv pip install --python "$HOME/vllm-venv/bin/python" "vllm==0.11.0" "transformers<5" --torch-backend=auto   # Lambda driver 570 = CUDA 12.8: newer vllm wheels need libcudart.so.13; vllm 0.11 breaks on transformers 5
# gpt-oss's tokenizer (openai_harmony) fetches its vocab at start; it failed on a GH200, so fetch it first and point at it
mkdir -p "$HOME/tiktoken"; for v in o200k_base cl100k_base; do [ -s "$HOME/tiktoken/$v.tiktoken" ] || curl -fsSL --retry 3 -o "$HOME/tiktoken/$v.tiktoken" "https://openaipublic.blob.core.windows.net/encodings/$v.tiktoken"; done
export TIKTOKEN_ENCODINGS_BASE="$HOME/tiktoken"
nohup "$HOME/vllm-venv/bin/vllm" serve "$1" --host 127.0.0.1 --port 8000 \
  --served-model-name gpt-oss-120b --enable-auto-tool-choice --tool-call-parser openai \
  --max-model-len 32768 --gpu-memory-utilization 0.90 --max-num-seqs 64 >"$HOME/vllm.log" 2>&1 </dev/null &
REMOTE
ready_deadline=$(( $(date -u +%s) + 2400 )); next_progress=0
until remote 'curl -fsS --max-time 10 http://127.0.0.1:8000/v1/models' >/dev/null 2>&1; do
  now=$(date -u +%s); ((now < ready_deadline)) || die 'vLLM readiness timed out; inspect ~/vllm.log.'
  if ((now >= next_progress)); then echo 'Waiting for vLLM; log: ~/vllm.log'; next_progress=$((now + 60)); fi
  sleep 10
done
remote --tunnel
save
for ((i=0; i<15; i++)); do
  kill -0 "$TUNNEL" 2>/dev/null || die "Tunnel exited; inspect $CACHE/tunnel.log"
  curl -fsS --max-time 5 "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1 && break
  sleep 1
done
((i < 15)) || die 'Local tunnel never became ready.'
kill -0 "$WATCH" 2>/dev/null || die 'Watchdog exited unexpectedly.'
trap - EXIT INT HUP TERM
echo "Ready: lambda/gpt-oss-120b at http://127.0.0.1:$PORT/v1 (instance $ID)"
