#!/usr/bin/env bash
# Separated users of a sealed comparison (U57), written inline by the pipeline and run from the shared run directory.
# Usage: bash profiler/cmp_users.sh SECONDS (the time left in the comparison's budget_s)
set -euo pipefail
[[ ${1:-} =~ ^[0-9]{1,9}$ ]] || { echo 'usage: cmp_users.sh SECONDS' >&2; exit 2; }
END=$((SECONDS + $1))
S=$(pwd -P)
P=$S/cmp-private
# A find -path pattern for the shared run directory: *, ?, [ and \ escaped by a backslash.
SE=$(printf '%s' "$S" | sed 's/[*?[\\]/\\&/g')
fail() { echo "comparison users: $*" >&2; exit 1; }
RULE=(OUTPUT -m owner --uid-owner cmp-arm ! -o lo -j REJECT)
# Written by the pipeline: 1 when the design has an evaluator, and each file C/arms_seal.json names with its SHA-256.
EVALUATOR=0
SEALED=()
USERS=(cmp-arm)
if ((EVALUATOR)); then USERS+=(cmp-eval); fi

# Cleanup after a part user: its processes, its entries in the directories it can write, its System V IPC objects.
cleanup() {
  local user=$1 dir uid kind
  sudo -n pkill -KILL -u "$user" || true
  while pgrep -u "$user" >/dev/null; do
    ((SECONDS + 1 <= END)) || return 1
    sleep 1
    sudo -n pkill -KILL -u "$user" || true
  done
  while IFS= read -r -d '' dir; do
    sudo -n find "$dir" -mindepth 1 -user "$user" ! -path "$SE" ! -path "$SE/*" -delete 2>/dev/null || true
  done < <(python3 -I -c '
import json, os, sys
listed = json.load(open(sys.argv[1]))[sys.argv[2]]
for item in listed:
    if not any(item != other and item.startswith(other.rstrip("/") + "/") for other in listed):
        sys.stdout.buffer.write(os.fsencode(item) + b"\0")' profiler/cmp_writable.json "$user")
  uid=$(id -u "$user")
  for kind in shm:-m msg:-q sem:-s; do
    [[ -r /proc/sysvipc/${kind%%:*} ]] || continue
    awk -v uid="$uid" 'NR == 1 { for (i = 1; i <= NF; i++) if ($i == "uid") c = i; next } c && $c == uid { print $2 }' \
      "/proc/sysvipc/${kind%%:*}" | while read -r id; do sudo -n ipcrm "${kind#*:}" "$id" || true; done
  done
}

# 1. The sealed harness files are on the box unchanged; then the part users, system users without login shell or home,
# in every group that guards a /dev/nvidia* device file.
((${#SEALED[@]})) || fail 'no sealed harness file'
for ((i = 0; i < ${#SEALED[@]}; i += 2)); do
  file=$S/harness/${SEALED[i]}
  [[ -f $file && ! -L $file && $(sha256sum < "$file") == "${SEALED[i + 1]}  -" ]] || fail "harness/${SEALED[i]} is not the sealed file"
done
for user in "${USERS[@]}"; do
  id -u "$user" >/dev/null 2>&1 || sudo -n useradd --system --user-group --no-create-home --home-dir /nonexistent \
    --shell /usr/sbin/nologin "$user" || fail "cannot create $user"
done
for device in /dev/nvidia*; do
  [[ -c $device || -b $device ]] || continue
  (( (8#$(stat -c %a "$device") & 6) == 6 )) && continue
  group=$(stat -c %G "$device")
  for user in "${USERS[@]}"; do sudo -n usermod -a -G "$group" "$user" || fail "cannot add $user to $group"; done
done

# 2. cmp-arm reaches no network but loopback.
for tool in iptables ip6tables; do
  sudo -n "$tool" -C "${RULE[@]}" 2>/dev/null || sudo -n "$tool" -I OUTPUT 1 "${RULE[@]:1}" || fail "cannot add the $tool rule"
done

# 3. Nothing in the shared run directory is writable by other users; the work, job and private directories are fresh.
sudo -n rm -rf -- "$P"
sudo -n chmod -R go-w,o+rX -- "$S" || fail 'cannot restrict the shared run directory'
sudo -n rm -rf -- "$S/comparison-work" "$S/comparison-jobs"
mkdir -m 711 -- "$S/comparison-work"
mkdir -m 700 -- "$S/comparison-jobs"
if ((EVALUATOR)); then sudo -n install -d -o cmp-eval -g cmp-eval -m 700 -- "$P" || fail 'cannot create cmp-private'; fi

# 4. The directories outside the shared run directory each user can write.
python3 -I - "$SE" "${USERS[@]}" > profiler/cmp_writable.json <<'PY' || fail 'cannot list writable directories'
import json, subprocess, sys
listed = {}
for user in sys.argv[2:]:
    found = subprocess.run(["sudo", "-n", "-u", user, "find", "/", "(", "-path", "/proc", "-o", "-path", "/sys", "-o",
                            "-path", sys.argv[1], ")", "-prune", "-o", "-type", "d", "-writable", "-print0"],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
    listed[user] = sorted({item for item in found.decode("utf-8", "surrogateescape").split("\0") if item})
json.dump(listed, sys.stdout)
PY

# Steps 5 to 7 only with an evaluator.
if ((EVALUATOR)); then
# 5. The evaluator's private data, fetched by cmp-eval only.
sudo -n -u cmp-eval mkdir -- "$P/.home" || fail 'cannot create the fetch home'
VARS=()
while IFS= read -r -d '' entry; do
  name=${entry%%=*}
  [[ $name == CMP_* || $name == SUDO_* || $name == HOME || $name == TMPDIR ]] || VARS+=("$entry")
done < <(env -0)
LEFT=$((END - SECONDS))
rc=0
if ((LEFT >= 1)); then
  # Its output may hold private data: it is not kept.
  timeout -k 5 "$LEFT" sudo -n -u cmp-eval -- env -i -C "$P" "${VARS[@]}" HOME="$P/.home" TMPDIR="$P/.home" \
    bash "$S/harness/fetch_private.sh" </dev/null >/dev/null 2>&1 || rc=$?
else
  rc=124
fi
cleanup cmp-eval || fail 'cmp-eval processes left after fetch_private.sh'
sudo -n rm -rf -- "$P/.home"
((rc == 0)) || fail "fetch_private.sh exited $rc"

# 6. Only regular files and directories, readable by the evaluator and never changed by it.
[[ -z $(sudo -n find "$P" ! -type f ! -type d -print -quit) ]] || fail 'cmp-private holds other than regular files and directories'
sudo -n chown -R root:cmp-eval -- "$P"
sudo -n find "$P" -type d -exec chmod 750 {} +
sudo -n find "$P" -type f -exec chmod 640 {} +

# 7. No copy of a private file outside cmp-private.
sudo -n python3 -I - "$S" "$P" "$HOME" profiler/cmp_writable.json <<'PY' || fail 'a copy of private data lies outside cmp-private'
import hashlib, json, os, stat, sys
shared, private, home, listing = sys.argv[1:]


def files(top):
    for root, dirs, names in os.walk(top, onerror=lambda error: None):
        dirs[:] = [name for name in dirs if os.path.join(root, name) != private]
        for name in names:
            path = os.path.join(root, name)
            try:
                info = os.lstat(path)
            except OSError:
                continue
            if stat.S_ISREG(info.st_mode):
                yield path, info.st_size


def digest(path):
    value = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


sealed = {}
for path, size in files(private):
    sealed.setdefault(size, set()).add(digest(path))
tops = sorted({shared, home, *json.load(open(listing))["cmp-arm"]})
tops = [top for top in tops if not any(top != other and top.startswith(other.rstrip("/") + "/") for other in tops)]
for top in tops:
    for path, size in files(top):
        if size in sealed:
            try:
                found = digest(path) in sealed[size]
            except OSError:
                continue
            if found:
                sys.exit(1)
PY
fi

# 8. The part users see the box user's GPUs; cmp-arm cannot read cmp-private; both network rules are present.
gpus() { "$@" nvidia-smi -L 2>/dev/null | grep -c '^GPU ' || true; }
BASE=$(gpus)
for user in "${USERS[@]}"; do
  [[ $(gpus sudo -n -u "$user") == "$BASE" ]] || fail "$user does not see the box user's GPUs"
done
if ((EVALUATOR)); then ! sudo -n -u cmp-arm test -r "$P" || fail 'cmp-arm can read cmp-private'; fi
sudo -n iptables -C "${RULE[@]}" && sudo -n ip6tables -C "${RULE[@]}" || fail 'a network rule is missing'
