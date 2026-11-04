#!/usr/bin/env bash
# Black-box contract tests. Never source or inspect the runner.
set -u
set -o pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
runner=$repo/m5/boxrun.sh
scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
export BOX_ROOT=$scratch/box
# Failed fetches are retried after a wait; keep the suite fast unless a case overrides it.
export BOXRUN_FETCH_WAIT_S=0
mkdir -p "$BOX_ROOT" "$scratch/bin" "$scratch/sleep-bin"
real_sleep=$(type -P sleep)

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
# Counts outputs and log fetch attempts separately (the log is the one ending in .log)
# and fails the first FAIL_OUT outputs attempts and the first FAIL_LOG log attempts.
cat > "$scratch/bin/counting-fetch" <<'SH'
#!/usr/bin/env bash
kind=out
[[ $1 != *.log ]] || kind=log
printf '%s\n' "$kind" >> "$FETCH_DIR/order"
count=0
[[ ! -f $FETCH_DIR/$kind ]] || read -r count < "$FETCH_DIR/$kind"
count=$((count + 1))
printf '%s\n' "$count" > "$FETCH_DIR/$kind"
if [[ $kind == out ]]; then fails=${FAIL_OUT:-0}; else fails=${FAIL_LOG:-0}; fi
if (( count <= fails )); then
    echo "simulated $kind fetch failure" >&2
    exit 1
fi
cd -- "$BOX_ROOT" || exit 1
exec cp -r -- "$1" "$2"
SH
# Records every sleep; skips the 60-second retry wait instead of taking it.
cat > "$scratch/sleep-bin/sleep" <<SH
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "\$SLEEP_LOG"
case \$1 in 60|60s|60.0) exit 0 ;; esac
exec '$real_sleep' "\$@"
SH
chmod +x "$scratch/bin/"* "$scratch/sleep-bin/sleep"

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

lines() {
    local -a rows=()
    [[ ! -f $1 ]] || mapfile -t rows < "$1"
    printf '%s\n' "${#rows[@]}"
}

wall_of() {
    python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["wall_s"])' "$1" 2>/dev/null || echo -1
}

at_least() {
    python3 -c 'import sys; sys.exit(0 if float(sys.argv[1]) >= float(sys.argv[2]) else 1)' "$1" "$2"
}

# SCHEMAS.md receipts: after the remote command, fetch out/ then the log; a failing fetch is
# retried up to four more times, waiting BOXRUN_FETCH_WAIT_S (default 60 s) before each retry;
# fetched is true only when both succeed; only the fetch is repeated; waits count in wall_s.
# wait is a number of seconds, or "default" for an unset BOXRUN_FETCH_WAIT_S with a fake sleep.
retry_case() {
    local name=$1 fail_out=$2 fail_log=$3 expected_rc=$4 expected_exit=$5 fetched=$6
    local seconds=$7 tail=$8 wait=$9
    local failures=0 remote=$BOX_ROOT/$name dir=$scratch/$name out=$scratch/$name/out
    local before after status outs logs retries wall order
    mkdir -p "$remote" "$out" "$dir/fetches"
    local command="printf 'run\n' >> '$remote/runs'; $prepare$tail"
    local -a envs=(BOX="$scratch/bin/box" FETCH="$scratch/bin/counting-fetch"
        FETCH_DIR="$dir/fetches" FAIL_OUT="$fail_out" FAIL_LOG="$fail_log")
    if [[ $wait == default ]]; then
        envs=(-u BOXRUN_FETCH_WAIT_S "${envs[@]}" PATH="$scratch/sleep-bin:$PATH" SLEEP_LOG="$dir/sleeps")
    else
        envs+=(BOXRUN_FETCH_WAIT_S="$wait")
    fi
    before=$(date +%s)
    env "${envs[@]}" timeout --kill-after=2s 105s bash "$runner" \
        --name "$name" --cmd "$command" --remote-dir "$remote" \
        --timeout "$seconds" --fetch artifacts --to "$out" \
        --receipt "$dir/receipt.json" > "$dir/runner.log" 2>&1
    status=$?
    after=$(date +%s)
    check "$name: exit $expected_exit (got $status)" test "$status" -eq "$expected_exit"
    check "$name: receipt fields, rc $expected_rc, fetched $fetched" receipt_check "$dir/receipt.json" \
        "$name" "$expected_rc" "$fetched" "$before" "$after"
    check "$name: remote exit code" test "$(cat "$remote/$name.rc" 2>/dev/null)" = "$expected_rc"
    check "$name: remote command ran exactly once (got $(lines "$remote/runs"))" \
        test "$(lines "$remote/runs")" -eq 1
    outs=$(cat "$dir/fetches/out" 2>/dev/null || echo 0)
    logs=$(cat "$dir/fetches/log" 2>/dev/null || echo 0)
    if [[ $fetched == true ]]; then
        check "$name: complete outputs fetched" test "$(cat "$out/artifacts/result.txt" 2>/dev/null)" = payload
        check "$name: log fetched" test "$(cat "$out/$name.log" 2>/dev/null)" = log-marker
    fi
    if (( expected_rc != 124 )); then
        local want_outs=$(( fail_out >= 5 ? 5 : fail_out + 1 ))
        check "$name: $want_outs outputs fetch attempt(s) (got $outs)" test "$outs" -eq "$want_outs"
        if (( fail_out < 5 )); then
            local want_logs=$(( fail_log >= 5 ? 5 : fail_log + 1 ))
            check "$name: $want_logs log fetch attempt(s) (got $logs)" test "$logs" -eq "$want_logs"
        fi
        order=$(tr -d '\n' 2>/dev/null < "$dir/fetches/order")
        check "$name: outputs fetched before the log ($order)" eval '[[ $order =~ ^(out)+(log)*$ ]]'
    fi
    retries=$(( (outs > 0 ? outs - 1 : 0) + (logs > 0 ? logs - 1 : 0) ))
    if [[ $wait == default ]]; then
        local sixties=0 entry
        if [[ -f $dir/sleeps ]]; then
            while read -r entry; do
                [[ ! $entry =~ ^60(s|\.0+)?$ ]] || sixties=$((sixties + 1))
            done < "$dir/sleeps"
        fi
        check "$name: default wait is 60 s before each of $retries retries (got $sixties)" \
            test "$sixties" -eq "$retries"
    elif (( wait > 0 )); then
        wall=$(wall_of "$dir/receipt.json")
        check "$name: $retries retry waits of ${wait}s count in wall_s (wall_s $wall)" \
            at_least "$wall" "$((retries * wait))"
        check "$name: runner took the waits ($((after - before))s)" \
            test "$((after - before))" -ge "$((retries * wait))"
    fi
    if (( failures )); then
        printf '%s\n' "--- $name runner output ---"
        cat "$dir/runner.log"
    fi
    printf '%s\n' "$failures" > "$dir/failures"
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
# name fail_out fail_log rc exit fetched timeout command-tail wait
retry_cases=(
    'out_retry_1 1 0 0 0 true 10 - 0'
    'out_retry_2 2 0 0 0 true 10 - 0'
    'out_retry_3 3 0 0 0 true 10 - 0'
    'out_retry_4 4 0 0 0 true 10 - 0'
    'log_retry_1 0 1 0 0 true 10 - 0'
    'log_retry_2 0 2 0 0 true 10 - 0'
    'log_retry_3 0 3 0 0 true 10 - 0'
    'log_retry_4 0 4 0 0 true 10 - 0'
    'out_fail_5 99 0 0 2 false 10 - 0'
    'out_fail_5_nonzero 99 0 7 2 false 10 exit7 0'
    'log_fail_5 0 99 0 2 false 10 - 0'
    'both_retry_wait_env 1 1 0 0 true 10 - 2'
    'both_retry_wait_default 1 1 0 0 true 10 - default'
    'no_retry_wait_default 0 0 0 0 true 10 - default'
    'timeout_fetch_fail 99 99 124 3 false 2 sleep30 0'
)
retry_names=()
for row in "${retry_cases[@]}"; do
    read -r name fail_out fail_log rc exit_code fetched seconds tail wait <<< "$row"
    case $tail in
        -) tail= ;;
        exit7) tail='; exit 7' ;;
        sleep30) tail='; sleep 30' ;;
    esac
    retry_case "$name" "$fail_out" "$fail_log" "$rc" "$exit_code" "$fetched" \
        "$seconds" "$tail" "$wait" > "$scratch/$name.results" 2>&1 &
    pids+=("$!")
    retry_names+=("$name")
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

# SCHEMAS.md "Remote command files" sets mode 600 only for the comparison evaluate stage's box commands; without
# args.comparison boxrun's remote files are as before: on a box running under umask 022, the command's script,
# log and exit status are created with the same mode as a file the command itself creates (644).
mode_of() { stat -c %a -- "$1" 2>/dev/null || echo missing; }
cat > "$scratch/bin/umask-box" <<'SH'
#!/usr/bin/env bash
umask 022
cd -- "$BOX_ROOT" || exit 1
exec bash -c "$1"
SH
chmod +x "$scratch/bin/umask-box"
remote=$BOX_ROOT/umask_default
mkdir -p "$remote" "$scratch/umask_default/out"
BOX=$scratch/bin/umask-box FETCH=$scratch/bin/fetch timeout --kill-after=2s 105s bash "$runner" \
    --name umask_default --cmd "$prepare" --remote-dir "$remote" --timeout 10 --fetch artifacts \
    --to "$scratch/umask_default/out" --receipt "$scratch/umask_default/receipt.json" \
    > "$scratch/umask_default/runner.log" 2>&1
check 'umask_default: runner exit 0' test "$?" -eq 0
created=$(mode_of "$remote/artifacts/result.txt")
check "umask_default: a file the command creates is at 644 under umask 022 (got $created)" test "$created" = 644
for suffix in rc log; do
    got=$(mode_of "$remote/umask_default.$suffix")
    check "umask_default: remote .$suffix at the command's own file mode $created, as before (got $got)" test "$got" = "$created"
done
if [[ -f $remote/umask_default.sh ]]; then
    got=$(mode_of "$remote/umask_default.sh")
    check "umask_default: remote command script not restricted to 600 (got $got)" test "$got" != 600
fi

for pid in "${pids[@]}"; do
    wait "$pid" || { echo 'FAIL: test worker crashed'; failures=$((failures + 1)); }
done
for name in success nonzero timeout flaky fetch_failure "${retry_names[@]}"; do
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
