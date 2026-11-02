#!/usr/bin/env bash
# Black-box contract tests for U53 incremental fetch (m5/SCHEMAS.md, "Incremental fetch (U53)").
# Never source or inspect the runner. Runs m5/boxrun.sh without FETCH (except case 6), with a
# fake box, fake rsync/scp/ssh first on PATH, a scratch HOME and a scratch BOXRUN_MIRROR_ROOT.
set -u
set -o pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
runner=$repo/m5/boxrun.sh
scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT

total=0
failures=0
check() {
    local label=$1
    shift
    total=$((total + 1))
    if "$@"; then
        printf 'ok: %s\n' "$label"
    else
        printf 'FAIL: %s\n' "$label"
        failures=$((failures + 1))
    fi
}

real_rsync=$(type -P rsync || true)
if [[ -z $real_rsync ]]; then
    echo 'FAIL: suite setup: a real rsync is required on PATH for the fake rsync'
    echo '1 failure(s)'
    exit 1
fi

ip=203.0.113.7
export HOME=$scratch/home
export BOX_ROOT=$scratch/box
export BOXRUN_MIRROR_ROOT=$scratch/mirror   # deliberately not created: boxrun creates it
export BOXRUN_FETCH_WAIT_S=0
export FAKE_IP=$ip
export SSH_LOG=$scratch/ssh.log
unset FETCH
mkdir -p "$HOME/.cache/metis-serve" "$HOME/.ssh" "$BOX_ROOT" "$scratch/bin" "$scratch/logs"
printf '{"ip": "%s"}\n' "$ip" > "$HOME/.cache/metis-serve/state.json"
: > "$HOME/.ssh/lambda_ed25519"
key=$HOME/.ssh/lambda_ed25519

cat > "$scratch/bin/box" <<'SH'
#!/usr/bin/env bash
cd -- "$BOX_ROOT" || exit 1
exec bash -c "$1"
SH
# Injected FETCH for case 6 (same as test_boxrun.sh).
cat > "$scratch/bin/fetch" <<'SH'
#!/usr/bin/env bash
cd -- "$BOX_ROOT" || exit 1
exec cp -r -- "$1" "$2"
SH
# Fake rsync: logs its arguments (one per line, per call), fails when RSYNC_FAIL=1, otherwise
# maps ubuntu@<ip>:<path> to the local path (the fake box's directories are local absolute
# paths) and runs the real rsync locally without -e.
cat > "$scratch/bin/rsync" <<SH
#!/usr/bin/env bash
real='$real_rsync'
SH
cat >> "$scratch/bin/rsync" <<'SH'
mkdir -p "$LOG_DIR"
n=$(( $(ls "$LOG_DIR" | grep -c '^rsync\.') + 1 ))
printf '%s\n' "$@" > "$LOG_DIR/rsync.$n"
printf 'rsync\n' >> "$LOG_DIR/order"
if [[ ${RSYNC_FAIL:-0} == 1 ]]; then
    echo 'rsync: command not found (simulated)' >&2
    exit 127
fi
args=()
while (( $# )); do
    case $1 in
        -e) shift ;;
        ubuntu@*:*)
            [[ ${1%%:*} == "ubuntu@$FAKE_IP" ]] || { echo "fake rsync: bad host $1" >&2; exit 12; }
            args+=("${1#*:}") ;;
        *:*) echo "fake rsync: unexpected remote $1" >&2; exit 12 ;;
        *) args+=("$1") ;;
    esac
    shift
done
exec "$real" "${args[@]}"
SH
# Fake scp: logs its arguments, maps ubuntu@<ip>:<path> likewise and copies with cp -r
# (with -L, as scp -r follows symbolic links). SCP_OUT_FAIL=1 fails copies of non-.log sources.
cat > "$scratch/bin/scp" <<'SH'
#!/usr/bin/env bash
mkdir -p "$LOG_DIR"
n=$(( $(ls "$LOG_DIR" | grep -c '^scp\.') + 1 ))
printf '%s\n' "$@" > "$LOG_DIR/scp.$n"
operands=()
while (( $# )); do
    case $1 in
        -[iocFPlSJ]) shift ;;
        -*) ;;
        *) operands+=("$1") ;;
    esac
    shift
done
(( ${#operands[@]} >= 2 )) || { echo 'fake scp: usage' >&2; exit 1; }
dest=${operands[-1]}
unset 'operands[-1]'
kind=scp-out
for src in "${operands[@]}"; do [[ $src != *.log ]] || kind=scp-log; done
printf '%s\n' "$kind" >> "$LOG_DIR/order"
if [[ $kind == scp-out && ${SCP_OUT_FAIL:-0} == 1 ]]; then
    echo 'scp: simulated failure' >&2
    exit 1
fi
for src in "${operands[@]}"; do
    [[ ${src%%:*} == "ubuntu@$FAKE_IP" ]] || { echo "fake scp: bad source $src" >&2; exit 1; }
    cp -rL -- "${src#*:}" "$dest" || exit 1
done
SH
# Fake ssh: never reach a network. Logs and fails.
cat > "$scratch/bin/ssh" <<'SH'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$SSH_LOG"
exit 255
SH
chmod +x "$scratch/bin/"*
export PATH=$scratch/bin:$PATH

receipt_check() {
    python3 - "$@" <<'PY'
import json, sys
path, name, rc, fetched = sys.argv[1:]
try:
    with open(path) as stream:
        receipt = json.load(stream)
    assert receipt.get('name') == name, receipt
    assert type(receipt.get('rc')) is int and receipt['rc'] == int(rc), receipt
    assert receipt.get('fetched') is (fetched == 'true'), receipt
    assert receipt.get('timed_out') is False, receipt
except (OSError, ValueError, AssertionError) as error:
    print(f'receipt validation: {error}', file=sys.stderr)
    sys.exit(1)
PY
}

# tree_exact REMOTE LOCAL: LOCAL holds exactly the regular files of REMOTE (symbolic links
# followed), same relative paths and bytes, as regular files, and nothing else.
tree_exact() {
    python3 - "$@" <<'PY'
import os, sys
remote, local = sys.argv[1:]
def remote_files(root):
    files = {}
    for dirpath, dirs, names in os.walk(root, followlinks=True):
        for name in names:
            full = os.path.join(dirpath, name)
            if os.path.isfile(full):
                with open(full, 'rb') as f:
                    files[os.path.relpath(full, root)] = f.read()
    return files
want = remote_files(remote)
if not os.path.isdir(local) or os.path.islink(local):
    print(f'tree: {local} is not a directory', file=sys.stderr); sys.exit(1)
got, dirs, bad = {}, set(), []
for dirpath, subdirs, names in os.walk(local):
    for d in subdirs:
        full = os.path.join(dirpath, d)
        if os.path.islink(full):
            bad.append(os.path.relpath(full, local))
        dirs.add(os.path.relpath(full, local))
    for name in names:
        full = os.path.join(dirpath, name)
        rel = os.path.relpath(full, local)
        if os.path.islink(full) or not os.path.isfile(full):
            bad.append(rel); continue
        with open(full, 'rb') as f:
            got[rel] = f.read()
allowed_dirs = {os.path.dirname(p) for p in want}
expanded = set()
for d in allowed_dirs:
    while d:
        expanded.add(d); d = os.path.dirname(d)
problems = []
if bad: problems.append(f'not regular files: {sorted(bad)}')
if set(got) - set(want): problems.append(f'extra: {sorted(set(got) - set(want))}')
if set(want) - set(got): problems.append(f'missing: {sorted(set(want) - set(got))}')
diff = sorted(p for p in set(want) & set(got) if want[p] != got[p])
if diff: problems.append(f'bytes differ: {diff}')
if dirs - expanded: problems.append(f'extra dirs: {sorted(dirs - expanded)}')
if not want: problems.append('remote tree is empty (test setup)')
if problems:
    print('tree: ' + '; '.join(problems), file=sys.stderr); sys.exit(1)
PY
}

# rsync_args FILE PART REMOTE_DIR MIRROR KEY: checks one logged rsync call.
rsync_args() {
    python3 - "$@" <<'PY'
import os, shlex, sys
path, part, remote, mirror, key, ip = sys.argv[1:]
try:
    with open(path) as f:
        args = f.read().split('\n')[:-1]
except OSError as e:
    print(f'rsync args: {e}', file=sys.stderr); sys.exit(1)
ok = True
def need(cond, msg):
    global ok
    if not cond:
        print(f'rsync args: {msg}; args={args}', file=sys.stderr); ok = False
if part == 'options':
    for opt in ('-rLt', '--delete', '-z'):
        need(opt in args, f'missing {opt}')
elif part == 'ssh':
    need('-e' in args[:-1], 'missing -e')
    if '-e' in args[:-1]:
        cmd = args[args.index('-e') + 1]
        words = shlex.split(cmd)
        need(words and os.path.basename(words[0]) == 'ssh', f'-e is not an ssh command: {cmd}')
        need(key in words, f'-e lacks the key {key}: {cmd}')
        for opt in ('ConnectTimeout', 'ServerAliveInterval', 'BatchMode'):
            need(opt in cmd, f'-e lacks {opt}: {cmd}')
elif part == 'ends':
    need(len(args) >= 2 and args[-2] == f'ubuntu@{ip}:{remote}/out/',
         f'source should be ubuntu@{ip}:{remote}/out/')
    need(len(args) >= 2 and args[-1] == mirror, f'destination should be {mirror}')
sys.exit(0 if ok else 1)
PY
}

count_in() {   # count_in FILE WORD
    local n=0 line
    if [[ -f $1 ]]; then
        while read -r line; do [[ $line != "$2" ]] || n=$((n + 1)); done < "$1"
    fi
    printf '%s\n' "$n"
}

out_order() {  # rsync/scp-out entries of the order file, space separated
    local line s=
    if [[ -f $1 ]]; then
        while read -r line; do [[ $line == scp-log ]] || s+="$line "; done < "$1"
    fi
    printf '%s\n' "${s% }"
}

last_rsync_call() {
    local n=0
    while [[ -f $1/rsync.$((n + 1)) ]]; do n=$((n + 1)); done
    printf '%s\n' "$1/rsync.$n"
}

# run_box NAME REMOTE TO [ENV=VAL...]: runs one command; the remote command appends to
# <remote>/runs (outside out/) and prints log-marker to its log.
run_box() {
    local name=$1 remote=$2 to=$3
    shift 3
    mkdir -p "$to" "$scratch/receipts"
    env LOG_DIR="$scratch/logs/$name" BOX="$scratch/bin/box" "$@" \
        timeout --kill-after=2s 105s bash "$runner" \
        --name "$name" --cmd "printf 'run\n' >> runs; printf 'log-marker\n'" \
        --remote-dir "$remote" --timeout 20 --fetch out --to "$to" \
        --receipt "$scratch/receipts/$name.json" > "$scratch/logs/$name.runner" 2>&1
    status=$?
}

show_output_if_failed() {
    if (( failures > $1 )); then
        printf '%s\n' "--- $2 runner output ---"
        cat "$scratch/logs/$2.runner" 2>/dev/null
    fi
}

# Remote tree used by several cases, with nested folders and non-text bytes.
make_tree() {
    local out=$1/out
    mkdir -p "$out/nested/deep" "$out/other"
    printf 'alpha\n' > "$out/a.txt"
    printf '\000\001\377binary\n' > "$out/nested/deep/b.bin"
    printf 'gamma gamma\n' > "$out/other/c.txt"
    printf 'keep\n' > "$out/nested/keep.txt"
}

# 1. Fetch through rsync.
before=$failures
remote1=$BOX_ROOT/m5-11111111-aaaa
mkdir -p "$remote1"; make_tree "$remote1"
to=$scratch/case1
run_box c1 "$remote1" "$to"
logs=$scratch/logs/c1
check 'c1 rsync: exit 0' test "$status" -eq 0
check 'c1 rsync: receipt rc 0, fetched true' receipt_check "$scratch/receipts/c1.json" c1 0 true
check 'c1 rsync: <--to>/out/ holds exactly the remote files' tree_exact "$remote1/out" "$to/out"
check 'c1 rsync: rsync called once' test "$(count_in "$logs/order" rsync)" -eq 1
check 'c1 rsync: options -rLt --delete -z' rsync_args "$logs/rsync.1" options "$remote1" "$BOXRUN_MIRROR_ROOT/m5-11111111-aaaa/out/" "$key" "$ip"
check 'c1 rsync: -e ssh command with key, ConnectTimeout, ServerAliveInterval, BatchMode' \
    rsync_args "$logs/rsync.1" ssh "$remote1" "$BOXRUN_MIRROR_ROOT/m5-11111111-aaaa/out/" "$key" "$ip"
check 'c1 rsync: last two arguments are the remote out/ and the mirror out/' \
    rsync_args "$logs/rsync.1" ends "$remote1" "$BOXRUN_MIRROR_ROOT/m5-11111111-aaaa/out/" "$key" "$ip"
check 'c1 rsync: scp not used for out/' test "$(count_in "$logs/order" scp-out)" -eq 0
check 'c1 rsync: operation log arrives in <--to>/' test "$(cat "$to/c1.log" 2>/dev/null)" = log-marker
check 'c1 rsync: mirror holds the remote files' tree_exact "$remote1/out" "$BOXRUN_MIRROR_ROOT/m5-11111111-aaaa/out"
check 'c1 rsync: default mirror root unused when BOXRUN_MIRROR_ROOT is set' \
    test ! -e "$HOME/.cache/metis-serve/fetch-mirror"
check 'c1 rsync: remote command ran once' test "$(count_in "$remote1/runs" run)" -eq 1
show_output_if_failed "$before" c1

# 2. Second command against the same remote directory after changes; local out/ cleared first.
before=$failures
to=$scratch/case2
mkdir -p "$to"
run_box c2a "$remote1" "$to"
check 'c2 first: exit 0' test "$status" -eq 0
check 'c2 first: <--to>/out/ holds exactly the remote files' tree_exact "$remote1/out" "$to/out"
show_output_if_failed "$before" c2a
before=$failures
printf 'alpha changed, longer\n' > "$remote1/out/a.txt"
# Delete the only file in other/ together with its folder: whether an empty remote folder
# must appear locally is not specified, so the remote keeps none.
rm -rf -- "$remote1/out/other"
mkdir -p "$remote1/out/added"
printf 'new file\n' > "$remote1/out/added/d.txt"
rm -rf -- "$to/out"          # the pipeline clears local fetched folders before each command
run_box c2b "$remote1" "$to"
check 'c2 second: exit 0' test "$status" -eq 0
check 'c2 second: receipt fetched true' receipt_check "$scratch/receipts/c2b.json" c2b 0 true
check 'c2 second: <--to>/out/ holds exactly the second remote state' tree_exact "$remote1/out" "$to/out"
check 'c2 second: deleted file absent' test ! -e "$to/out/other/c.txt"
check 'c2 second: changed file has its new bytes' \
    test "$(cat "$to/out/a.txt" 2>/dev/null)" = 'alpha changed, longer'
check 'c2 second: mirror is the same directory both times' \
    rsync_args "$(last_rsync_call "$scratch/logs/c2b")" ends "$remote1" "$BOXRUN_MIRROR_ROOT/m5-11111111-aaaa/out/" "$key" "$ip"
check 'c2 second: first command used that mirror too' \
    rsync_args "$(last_rsync_call "$scratch/logs/c2a")" ends "$remote1" "$BOXRUN_MIRROR_ROOT/m5-11111111-aaaa/out/" "$key" "$ip"
check 'c2 second: operation log arrives' test "$(cat "$to/c2b.log" 2>/dev/null)" = log-marker
show_output_if_failed "$before" c2b

# 3. A different remote directory uses a different mirror.
before=$failures
remote2=$BOX_ROOT/m5-22222222-bbbb
mkdir -p "$remote2/out/sub"
printf 'second run only\n' > "$remote2/out/sub/z.txt"
printf 'zeta\n' > "$remote2/out/z.txt"
to=$scratch/case3
run_box c3 "$remote2" "$to"
check 'c3 other dir: exit 0' test "$status" -eq 0
check 'c3 other dir: uses its own mirror directory' \
    rsync_args "$(last_rsync_call "$scratch/logs/c3")" ends "$remote2" "$BOXRUN_MIRROR_ROOT/m5-22222222-bbbb/out/" "$key" "$ip"
check 'c3 other dir: result holds exactly its own files (none of the first)' tree_exact "$remote2/out" "$to/out"
check 'c3 other dir: first mirror still present (never deleted)' test -d "$BOXRUN_MIRROR_ROOT/m5-11111111-aaaa/out"
show_output_if_failed "$before" c3

# 4a. rsync fails every attempt: the same attempt falls back to scp.
before=$failures
remote3=$BOX_ROOT/m5-33333333-cccc
mkdir -p "$remote3"; make_tree "$remote3"
to=$scratch/case4a
run_box c4a "$remote3" "$to" RSYNC_FAIL=1
logs=$scratch/logs/c4a
check 'c4a rsync fails: exit 0' test "$status" -eq 0
check 'c4a rsync fails: receipt fetched true' receipt_check "$scratch/receipts/c4a.json" c4a 0 true
check 'c4a rsync fails: same attempt falls back to scp (got order: '"$(out_order "$logs/order")"')' \
    test "$(out_order "$logs/order")" = 'rsync scp-out'
check 'c4a rsync fails: result holds exactly the remote files' tree_exact "$remote3/out" "$to/out"
check 'c4a rsync fails: operation log arrives' test "$(cat "$to/c4a.log" 2>/dev/null)" = log-marker
check 'c4a rsync fails: remote command ran once' test "$(count_in "$remote3/runs" run)" -eq 1
show_output_if_failed "$before" c4a

# 4b. rsync and scp both fail every attempt: five attempts, fetched false, exit 2.
before=$failures
remote4=$BOX_ROOT/m5-44444444-dddd
mkdir -p "$remote4"; make_tree "$remote4"
to=$scratch/case4b
run_box c4b "$remote4" "$to" RSYNC_FAIL=1 SCP_OUT_FAIL=1
logs=$scratch/logs/c4b
check 'c4b both fail: exit 2' test "$status" -eq 2
check 'c4b both fail: receipt rc 0, fetched false' receipt_check "$scratch/receipts/c4b.json" c4b 0 false
check 'c4b both fail: five attempts, each rsync then scp (got order: '"$(out_order "$logs/order")"')' \
    test "$(out_order "$logs/order")" = 'rsync scp-out rsync scp-out rsync scp-out rsync scp-out rsync scp-out'
check 'c4b both fail: remote command not rerun' test "$(count_in "$remote4/runs" run)" -eq 1
show_output_if_failed "$before" c4b

# 5. A remote symbolic link to a file inside out/ arrives as a regular file.
before=$failures
remote5=$BOX_ROOT/m5-55555555-eeee
mkdir -p "$remote5/out/data" "$remote5/out/links"
printf 'target bytes\n' > "$remote5/out/data/target.txt"
ln -s ../data/target.txt "$remote5/out/links/link.txt"
to=$scratch/case5
run_box c5 "$remote5" "$to"
check 'c5 symlink: exit 0' test "$status" -eq 0
check 'c5 symlink: rsync used' test "$(count_in "$scratch/logs/c5/order" rsync)" -ge 1
check 'c5 symlink: link arrives as a regular file' \
    eval '[[ -f $to/out/links/link.txt && ! -L $to/out/links/link.txt ]]'
check "c5 symlink: link has the target's bytes" \
    test "$(cat "$to/out/links/link.txt" 2>/dev/null)" = 'target bytes'
check 'c5 symlink: result holds exactly the remote files' tree_exact "$remote5/out" "$to/out"
show_output_if_failed "$before" c5

# 6. Injected FETCH: no rsync, no mirror.
before=$failures
remote6=$BOX_ROOT/m5-66666666-ffff
mkdir -p "$remote6"; make_tree "$remote6"
to=$scratch/case6
mirror_before=$(python3 -c 'import os,sys; print(sorted(os.listdir(sys.argv[1])) if os.path.isdir(sys.argv[1]) else None)' "$BOXRUN_MIRROR_ROOT")
run_box c6 "$remote6" "$to" FETCH="$scratch/bin/fetch"
check 'c6 FETCH: exit 0' test "$status" -eq 0
check 'c6 FETCH: receipt fetched true' receipt_check "$scratch/receipts/c6.json" c6 0 true
check 'c6 FETCH: rsync never called' test "$(count_in "$scratch/logs/c6/order" rsync)" -eq 0
check 'c6 FETCH: no mirror created' test ! -e "$BOXRUN_MIRROR_ROOT/m5-66666666-ffff"
check 'c6 FETCH: mirror root unchanged' test "$(python3 -c 'import os,sys; print(sorted(os.listdir(sys.argv[1])) if os.path.isdir(sys.argv[1]) else None)' "$BOXRUN_MIRROR_ROOT")" = "$mirror_before"
check 'c6 FETCH: default mirror root unused' test ! -e "$HOME/.cache/metis-serve/fetch-mirror"
check 'c6 FETCH: result holds exactly the remote files' tree_exact "$remote6/out" "$to/out"
show_output_if_failed "$before" c6

if [[ -s $SSH_LOG ]]; then
    echo "note: boxrun invoked ssh directly ($(wc -l < "$SSH_LOG") call(s)); the fake ssh failed them"
fi
if (( failures )); then
    printf '%s of %s checks failed\n' "$failures" "$total"
    exit 1
fi
printf 'all %s checks passed\n' "$total"
