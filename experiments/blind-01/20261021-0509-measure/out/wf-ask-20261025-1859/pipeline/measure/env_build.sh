#!/usr/bin/env bash
# env_build.sh: build the Python environment of record ONCE on a Lambda box, onto the attached filesystem, and report.
# Pipeline-owned (no model writes this). Inputs are data files shipped beside it; outputs are records. On a failure the
# box is HELD OPEN for a bounded fixer: this script writes HOLD, sleeps, and re-runs when the fixer writes RESUME.
#
#   env: ENV_FS      mount of the filesystem (e.g. /lambda/nfs/metis-env-us-east-1)   required
#        ENV_TAG     environment name under the filesystem (e.g. m4)                     required
#        HOLD_SECONDS  how long to hold the box open after a failure (default 1800; 0 = no hold)
#        REMOTE_TIMEOUT  the launcher's cap, read for the record
#   files beside this script: pins.txt (pip requirements, one per line), apt.txt (apt packages, one per line, may be empty)
#   writes under ./results_env/out/: env_report.json, env.lock (pip freeze), env.lock.sha256, install_pip.log, apt.log,
#        import_check.json, nvidia_smi.txt, changes.log (git log -p of the environment directory), HOLD / RESUME markers in ./
#   exit: 0 every pinned distribution installed and every top-level module imports; 2 otherwise (after any hold)
set -uo pipefail
ENV_FS=${ENV_FS:?}; ENV_TAG=${ENV_TAG:?}; HOLD_SECONDS=${HOLD_SECONDS:-1800}
HERE=$(cd "$(dirname "$0")" && pwd); OUT=$HERE/results_env/out; mkdir -p "$OUT"
ENVDIR=$ENV_FS/$ENV_TAG; VENV=$ENVDIR/venv
export DEBIAN_FRONTEND=noninteractive PIP_DISABLE_PIP_VERSION_CHECK=1
log(){ echo "[env] $(date -u +%H:%M:%S) $*"; }
T0=$(date +%s)

# the environment directory is a git repository: every change (pins, extra packages, fixes) is a commit the launcher fetches
mkdir -p "$ENVDIR"; cd "$ENVDIR" || exit 2
[ -d .git ] || { git init -q . && git config user.email env@metis && git config user.name env_build; }
# once the environment exists, its git history is the record: the shipped pins seed a new environment only, so a fixer's commits survive a re-run
if [ -f "$ENVDIR/pins.txt" ]; then log "pins of record kept from $ENVDIR (git $(git rev-parse --short HEAD 2>/dev/null), $(git rev-list --count HEAD 2>/dev/null) commits)"
else cp "$HERE/pins.txt" "$ENVDIR/pins.txt"; cp "$HERE/apt.txt" "$ENVDIR/apt.txt" 2>/dev/null || : > "$ENVDIR/apt.txt"; fi
git add -A >/dev/null 2>&1; git commit -q -m "env_build: inputs of record (pins.txt, apt.txt)" >/dev/null 2>&1 || true

attempt() {   # one build-and-check pass; returns 0 when everything imports
  local rc=0
  log "preflight: $(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null | head -1)"
  nvidia-smi > "$OUT/nvidia_smi.txt" 2>&1 || true
  if [ -s "$ENVDIR/apt.txt" ]; then
    log "apt: $(wc -l < "$ENVDIR/apt.txt") package(s)"
    for i in 1 2 3 4 5 6; do sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || break; log "apt: lock held, waiting"; sleep 20; done
    sudo apt-get -qq update > "$OUT/apt.log" 2>&1; xargs -a "$ENVDIR/apt.txt" sudo apt-get -y -qq install >> "$OUT/apt.log" 2>&1 || { log "apt install failed (see apt.log)"; rc=2; }
  fi
  if [ ! -x "$VENV/bin/python" ]; then log "venv: creating"; python3 -m venv "$VENV" || return 2; fi
  "$VENV/bin/python" -m pip install -q --upgrade pip > "$OUT/pip_upgrade.log" 2>&1 || true
  log "pip: installing $(wc -l < "$ENVDIR/pins.txt") pin(s) ($("$VENV/bin/python" -m pip --version | cut -d' ' -f1-2))"
  "$VENV/bin/python" -m pip install --report "$OUT/pip_report.json" -r "$ENVDIR/pins.txt" > "$OUT/install_pip.log" 2>&1 || { log "pip install failed (see install_pip.log)"; rc=2; }
  "$VENV/bin/python" -m pip freeze > "$ENVDIR/env.lock" 2>/dev/null; cp "$ENVDIR/env.lock" "$OUT/env.lock"; sha256sum "$ENVDIR/env.lock" | cut -d' ' -f1 > "$OUT/env.lock.sha256"
  # import check: every top-level module of every pinned distribution, in a fresh interpreter each, with the error kind only
  "$VENV/bin/python" - "$ENVDIR/pins.txt" "$OUT/import_check.json" <<'PY'
import importlib.metadata as md, json, re, subprocess, sys
pins = [l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]
out = {"python": sys.version.split()[0], "dists": [], "all_ok": True}
for p in pins:
    name = re.split(r"[\[=<>!~ @]", p)[0]
    rec = {"requirement": p, "installed_version": None, "modules": []}
    try:
        d = md.distribution(name); rec["installed_version"] = d.version
        tops = (d.read_text("top_level.txt") or "").split()
        if not tops:
            tops = sorted({f.parts[0] for f in (d.files or []) if f.suffix == ".py" and len(f.parts) > 1} | {f.stem for f in (d.files or []) if f.suffix == ".py" and len(f.parts) == 1})
        for m in tops[:8]:
            if m.startswith("_") or m in ("tests", "test"): continue
            r = subprocess.run([sys.executable, "-c", f"import {m}"], capture_output=True, text=True, timeout=300)
            kind = "ok" if r.returncode == 0 else ("import_error" if "ImportError" in r.stderr or "ModuleNotFoundError" in r.stderr else "os_error" if "OSError" in r.stderr else "other")
            rec["modules"].append({"module": m, "ok": r.returncode == 0, "error_kind": kind, "stderr_tail": r.stderr.strip().split("\n")[-1][:200] if r.returncode else ""})
            if r.returncode: out["all_ok"] = False
    except md.PackageNotFoundError:
        rec["installed_version"] = None; rec["modules"].append({"module": None, "ok": False, "error_kind": "not_installed", "stderr_tail": ""}); out["all_ok"] = False
    out["dists"].append(rec)
json.dump(out, open(sys.argv[2], "w"), indent=1)
print("[env] import check: %d dist(s), all_ok=%s" % (len(out["dists"]), out["all_ok"]))
PY
  grep -q '"all_ok": true' "$OUT/import_check.json" 2>/dev/null || rc=2
  return $rc
}

report() {   # env_report.json: the record the main run verifies against
  "$VENV/bin/python" - "$OUT" "$ENVDIR" "$1" "$T0" <<'PY' 2>/dev/null || python3 - "$OUT" "$ENVDIR" "$1" "$T0" <<'PY2'
import json, sys, os, time, subprocess
out, envdir, status, t0 = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
ic = json.load(open(f"{out}/import_check.json")) if os.path.exists(f"{out}/import_check.json") else {}
rep = {"status": status, "env_dir": envdir, "venv": f"{envdir}/venv", "lock_sha256": open(f"{out}/env.lock.sha256").read().strip() if os.path.exists(f"{out}/env.lock.sha256") else None,
       "python": ic.get("python"), "dists": ic.get("dists", []), "all_imports_ok": ic.get("all_ok"), "elapsed_s": int(time.time()) - t0,
       "git_head": subprocess.run(["git", "-C", envdir, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
       "git_commits": subprocess.run(["git", "-C", envdir, "rev-list", "--count", "HEAD"], capture_output=True, text=True).stdout.strip(),
       "remote_timeout_s": os.environ.get("REMOTE_TIMEOUT"), "hold_seconds": os.environ.get("HOLD_SECONDS")}
json.dump(rep, open(f"{out}/env_report.json", "w"), indent=1)
PY
import json, sys; json.dump({"status": sys.argv[3], "note": "venv python unavailable; minimal report"}, open(sys.argv[1] + "/env_report.json", "w"))
PY2
  git -C "$ENVDIR" add -A >/dev/null 2>&1; git -C "$ENVDIR" commit -q -m "env_build: $1 after attempt $ATTEMPT" >/dev/null 2>&1 || true
  git -C "$ENVDIR" log -p --stat -- pins.txt apt.txt > "$OUT/changes.log" 2>/dev/null || true
  cp "$ENVDIR/pins.txt" "$ENVDIR/apt.txt" "$OUT/" 2>/dev/null || true   # the inputs of record as they now stand, fetched with the report
}

ATTEMPT=1
while :; do
  log "attempt $ATTEMPT"
  if attempt; then report ok; log "environment of record ready: $(cat "$OUT/env.lock.sha256" | cut -c1-16)…"; exit 0; fi
  report failed
  [ "$HOLD_SECONDS" -gt 0 ] || { log "failed; no hold"; exit 2; }
  rm -f "$HERE/RESUME"; echo "attempt $ATTEMPT failed at $(date -u +%FT%TZ); fixer may edit $ENVDIR (pins.txt, apt.txt, venv) and write $HERE/RESUME, or $HERE/ABANDON" > "$HERE/HOLD"
  log "HOLD: box open for a fixer for up to ${HOLD_SECONDS}s (write $HERE/RESUME to retry, $HERE/ABANDON to stop)"
  W=0; while [ $W -lt "$HOLD_SECONDS" ]; do sleep 15; W=$((W+15)); [ -f "$HERE/RESUME" ] && break; [ -f "$HERE/ABANDON" ] && { log "ABANDON by the fixer"; rm -f "$HERE/HOLD"; exit 2; }; done
  [ -f "$HERE/RESUME" ] || { log "hold expired"; rm -f "$HERE/HOLD"; exit 2; }
  rm -f "$HERE/HOLD" "$HERE/RESUME"; ATTEMPT=$((ATTEMPT+1))
done
