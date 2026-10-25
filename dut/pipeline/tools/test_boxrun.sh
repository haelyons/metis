#!/usr/bin/env bash
# Black-box contract tests. Never source or inspect the runner.
set -u
set -o pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
runner=$repo/m5/boxrun.sh
scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
export BOX_ROOT=$scratch/box
mkdir -p "$BOX_ROOT" "$scratch/bin"

cat > "$scratch/bin/box" <<'SH'
#!/usr/bin/env bash
cd -- "$BOX_ROOT" || exit 1
exec bash -c "$1"
SH
cat > "$scratch/bin/flaky-box" <<'SH'
#!/usr/bin/env bash
# A completion probe mentions .rc; the launch itself also contains timeout.
if [[ $1 == *'.rc'* && $1 != *timeout* ]]; then
    count=0
    [[ ! -f $POLL_COUNT ]] || read -r count < "$POLL_COUNT"
    count=$((count + 1))
    printf '%s\n' "$count" > "$POLL_COUNT"
    if (( count <= 2 )); then
        echo 'simulated transient poll failure' >&2
        exit 1
    fi
fi
cd -- "$BOX_ROOT" || exit 1
exec bash -c "$1"
SH
cat > "$scratch/bin/fetch" <<'SH'
#!/usr/bin/env bash
cd -- "$BOX_ROOT" || exit 1
exec cp -r -- "$1" "$2"
SH
cat > "$scratch/bin/fail-fetch" <<'SH'
#!/usr/bin/env bash
exit 1
SH
chmod +x "$scratch/bin/"*

check() {
    local label=$1
    shift
    if "$@"; then
        printf 'ok: %s\n' "$label"
    else
        printf 'FAIL: %s\n' "$label"
        failures=$((failures + 1))
    fi
}

receipt_check() {
    python3 - "$@" <<'PY'
import datetime as dt
import json
import math
import sys

path, name, rc, fetched, before, after = sys.argv[1:]
try:
    with open(path) as stream:
        receipt = json.load(stream)
    required = {'name', 'rc', 'timed_out', 'wall_s', 'fetched',
                'started_utc', 'ended_utc'}
    assert required <= receipt.keys(), 'missing receipt fields'
    assert receipt['name'] == name, receipt
    assert type(receipt['rc']) is int and receipt['rc'] == int(rc), receipt
    assert receipt['timed_out'] is (int(rc) == 124), receipt
    assert receipt['fetched'] is (fetched == 'true'), receipt
    wall = receipt['wall_s']
    assert type(wall) in (int, float) and math.isfinite(wall) and wall >= 0, receipt
    stamps = []
    for field in ('started_utc', 'ended_utc'):
        stamp = dt.datetime.fromisoformat(receipt[field].replace('Z', '+00:00'))
        assert stamp.utcoffset() == dt.timedelta(0), (field, receipt[field])
        stamps.append(stamp.timestamp())
    start, end = stamps
    assert float(before) - 2 <= start <= end <= float(after) + 2, receipt
    assert abs(wall - (end - start)) <= 3, receipt
except (OSError, ValueError, TypeError, KeyError, AssertionError) as error:
    print(f'receipt validation: {error}', file=sys.stderr)
    sys.exit(1)
PY
}

run_case() {
    local name=$1 expected_rc=$2 expected_exit=$3 seconds=$4 command=$5
    local box=$6 fetch=$7 fetched=$8
    local failures=0 remote=$BOX_ROOT/$name out=$scratch/$name/out
    local before after status count
    mkdir -p "$remote" "$out"
    before=$(date +%s)
    BOX=$box FETCH=$fetch POLL_COUNT=$scratch/$name/polls \
        timeout --kill-after=2s 105s bash "$runner" \
        --name "$name" --cmd "$command" --remote-dir "$remote" \
        --timeout "$seconds" --fetch artifacts --to "$out" \
        --receipt "$scratch/$name/receipt.json" \
        > "$scratch/$name/runner.log" 2>&1
    status=$?
    after=$(date +%s)
    check "$name: exit $expected_exit (got $status)" test "$status" -eq "$expected_exit"
    check "$name: receipt fields" receipt_check "$scratch/$name/receipt.json" \
        "$name" "$expected_rc" "$fetched" "$before" "$after"
    check "$name: remote exit code" test "$(cat "$remote/$name.rc" 2>/dev/null)" = "$expected_rc"
    if [[ $fetched == true ]]; then
        check "$name: artifact fetched" test "$(cat "$out/artifacts/result.txt" 2>/dev/null)" = payload
        check "$name: log fetched" test "$(cat "$out/$name.log" 2>/dev/null)" = log-marker
    fi
    if [[ $name == timeout ]]; then
        check "$name: finishes within 35 seconds" test "$((after - before))" -lt 35
    elif [[ $name == flaky ]]; then
        count=$(cat "$scratch/$name/polls" 2>/dev/null || echo 0)
        check "$name: two failed polls followed by retry" test "$count" -ge 3
    fi
    if (( failures )); then
        printf '%s\n' "--- $name runner output ---"
        cat "$scratch/$name/runner.log"
    fi
    printf '%s\n' "$failures" > "$scratch/$name/failures"
}

# Run independent cases concurrently: two 20-second poll retries must not make
# the whole suite exceed three minutes. Each runner has a 105-second watchdog.
prepare='mkdir -p artifacts; printf "payload\n" > artifacts/result.txt; printf "log-marker\n"'
start=$(date +%s)
pids=()
for name in success nonzero timeout flaky fetch_failure; do
    rc=0 exit_code=0 seconds=10 command=$prepare
    box=$scratch/bin/box fetch=$scratch/bin/fetch fetched=true
    case $name in
        nonzero) rc=7; exit_code=2; command="$prepare; exit 7" ;;
        timeout) rc=124; exit_code=3; seconds=2; command="$prepare; sleep 30" ;;
        flaky) box=$scratch/bin/flaky-box ;;
        fetch_failure) exit_code=2; fetch=$scratch/bin/fail-fetch; fetched=false ;;
    esac
    run_case "$name" "$rc" "$exit_code" "$seconds" "$command" \
        "$box" "$fetch" "$fetched" > "$scratch/$name.results" 2>&1 &
    pids+=("$!")
done

# Kill only the polling runner after the remote command signals that it started.
failures=0
remote=$BOX_ROOT/detached
mkdir -p "$remote" "$scratch/detached/out"
BOX=$scratch/bin/box FETCH=$scratch/bin/fetch bash "$runner" \
    --name detached --cmd 'touch started; sleep 4; touch finished' \
    --remote-dir "$remote" --timeout 12 --fetch artifacts \
    --to "$scratch/detached/out" --receipt "$scratch/detached/receipt.json" \
    > "$scratch/detached/runner.log" 2>&1 &
runner_pid=$!
for ((i=0; i<100; i++)); do
    [[ ! -f $remote/started ]] || break
    sleep 0.1
done
check 'detached: command started before runner kill' test -f "$remote/started"
check 'detached: command still running before runner kill' test ! -e "$remote/detached.rc"
check 'detached: kill polling runner' kill -TERM "$runner_pid"
wait "$runner_pid" 2>/dev/null
for ((i=0; i<150; i++)); do
    [[ ! -f $remote/detached.rc ]] || break
    sleep 0.1
done
check 'detached: command finished after runner kill' test -f "$remote/finished"
check 'detached: exit code appears after runner kill' \
    test "$(cat "$remote/detached.rc" 2>/dev/null)" = 0

for pid in "${pids[@]}"; do
    wait "$pid" || { echo 'FAIL: test worker crashed'; failures=$((failures + 1)); }
done
for name in success nonzero timeout flaky fetch_failure; do
    cat "$scratch/$name.results"
    count=$(cat "$scratch/$name/failures" 2>/dev/null || echo 1)
    failures=$((failures + count))
done
elapsed=$(( $(date +%s) - start ))
check "suite: under 3 minutes (${elapsed}s)" test "$elapsed" -lt 180
if (( failures )); then
    printf '%s failure(s)\n' "$failures"
    exit 1
fi
echo 'all checks passed'
