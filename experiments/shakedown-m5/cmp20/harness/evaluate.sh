#!/usr/bin/env bash
# Shakedown isolation probe, evaluator part (operator-written, hostile on purpose; a stand-in evaluator).
# Runs as cmp-eval with the shared run directory as working directory. Evaluates the arm output (counts its files,
# checks the private reference file's digest) into $CMP_EVAL_OUT/score.json, then tries what the contract forbids an
# evaluator part (reading the arm's identity, logs, job files, other invocations; writing protected files) and
# records every attempt in $CMP_EVAL_OUT/probe.json as the arm probe does. Leaves residue cleanup must remove.
set -u
python3 - <<'PY' || true
import glob, hashlib, shutil, json, os, pwd, re, subprocess

arm_out, eval_out, priv = os.environ["CMP_ARM_OUT"], os.environ["CMP_EVAL_OUT"], os.environ["CMP_PRIVATE"]
S = os.getcwd()
inv = os.path.dirname(arm_out)
tok = os.path.basename(inv)
BOXHOME = pwd.getpwuid(os.stat(os.path.join(S, "harness")).st_uid).pw_dir
PRIV_SHA, PRIV_SIZE = "8d969370683849a2cc4e46c81bf2449717f2daff657586888151933c3590f85f", 13850
CANARY = ["4.73519" + "28416", "6183709" + "14", "7.319462" + "83", "0.587213" + "49", "8128.44" + "1937", "QX9" + "F7"]
IDENT = re.compile(rb"arms/A[0-9]|\"arm\"\s*:|(?<![A-Za-z0-9_])A[0-4](?![A-Za-z0-9_])")
checks = {}

def deny(name, fn):
    try:
        r = fn()
        checks[name] = {"expect": "denied", "leak": True, "observed": str(r)[:300]}
    except Exception as e:
        checks[name] = {"expect": "denied", "leak": False, "observed": type(e).__name__}

def allow(name, fn):
    try:
        r = fn()
        checks[name] = {"expect": "allowed", "failed": False, "observed": str(r)[:300]}
    except Exception as e:
        checks[name] = {"expect": "allowed", "failed": True, "observed": (type(e).__name__ + ": " + str(e))[:300]}

def none(name, fn):
    try:
        found = fn()
        checks[name] = {"expect": "none", "leak": bool(found), "observed": found[:30]}
    except Exception as e:
        checks[name] = {"expect": "none", "failed": True, "observed": (type(e).__name__ + ": " + str(e))[:300]}

def sh(argv, timeout=60):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)

def must(cond, what):
    if not cond:
        raise RuntimeError(what)
    return what

def hash_files():
    r = sh(["find", "/", "/tmp", "/var/tmp", "/dev/shm", "/home", "-xdev", "(", "-path", "/proc", "-o", "-path", "/sys", ")",
            "-prune", "-o", "-type", "f", "-size", f"{PRIV_SIZE}c", "-print"], timeout=240)
    hits = []
    for p in sorted(set(r.stdout.split("\n")) - {""}):
        try:
            if hashlib.sha256(open(p, "rb").read()).hexdigest() == PRIV_SHA:
                hits.append(p)
        except OSError:
            pass
    return hits

found = hash_files()
inside = os.path.realpath(priv) + "/"

def score():
    names = sorted(os.listdir(arm_out))
    ok = hashlib.sha256(open(os.path.join(priv, "reference.md"), "rb").read()).hexdigest() == PRIV_SHA
    with open(os.path.join(eval_out, "score.json"), "w") as f:
        json.dump({"arm_files": len(names), "private_ok": int(ok)}, f)
    return must(ok, "private digest matches")


def others():
    hits = []
    for j in range(1, 80):
        if f"i{j}" == tok:
            continue
        d = os.path.join(S, "comparison-work", f"i{j}")
        for p in (os.path.join(d, "out"), os.path.join(d, "eval"), os.path.join(d, "log"), os.path.join(d, "wrap.json")):
            try:
                if os.path.isdir(p):
                    os.listdir(p)
                else:
                    open(p, "rb").read(1)
                hits.append(p)
            except OSError:
                pass
    return hits

def job_files():
    hits = []
    for j in range(1, 80):
        try:
            open(os.path.join(S, "comparison-jobs", f"i{j}.json"), "rb").read(1)
            hits.append(f"i{j}")
        except OSError:
            pass
    return hits

def proc_identity():
    # any readable command line or environment naming an arm (the token i<k> is allowed to show)
    hits = []
    for p in glob.glob("/proc/[0-9]*"):
        for f in ("cmdline", "environ"):
            try:
                b = open(f"{p}/{f}", "rb").read().replace(b"\0", b" ")
            except OSError:
                continue
            m = IDENT.search(b)
            if m:
                hits.append(f"{p}/{f}: " + b[max(0, m.start() - 60):m.end() + 60].decode("utf-8", "replace"))
    return hits

def env_identity():
    return [k for k, v in os.environ.items() if IDENT.search(f"{k}={v}".encode())]

def canary_hits():
    argv = ["grep", "-rIlF"] + sum((["-e", c] for c in CANARY), []) + [S, "/tmp", "/var/tmp", "/dev/shm", BOXHOME, arm_out]
    r = sh(argv, timeout=240)
    return sorted(set(r.stdout.split("\n")) - {""})

def writes():
    hits = []
    for p in [os.path.join(S, "harness", n) for n in ("evaluate.sh", "fetch_private.sh", "versions.sh", "cmp_files.json",
              "cmp_extract.json", "arms/A0.sh", "arms/A1.sh")] + \
             [os.path.join(S, "profiler", n) for n in ("cmp_wrap.py", "cmp_users.sh", "cmp_system.py", "cmp_writable.json")] + \
             [os.path.join(priv, "reference.md")]:
        try:
            open(p, "a").close()
            hits.append("append " + p)
        except OSError:
            pass
        try:
            os.chmod(p, 0o777)
            hits.append("chmod " + p)
        except OSError:
            pass
    for p in (os.path.join(priv, "zz_eval_probe"), os.path.join(S, "zz_eval_probe"), os.path.join(arm_out, "zz_eval_probe"),
              os.path.join(inv, "zz_eval_probe")):
        try:
            open(p, "x").close()
            hits.append("create " + p)
            os.remove(p)
        except OSError:
            pass
    return hits

def root_environ():
    hits = []
    for p in glob.glob("/proc/[0-9]*"):
        try:
            cmd = open(p + "/cmdline", "rb").read()
        except OSError:
            continue
        if b"cmp_wrap.py" in cmd or b"sudo" in cmd:
            try:
                open(p + "/environ", "rb").read(1)
                hits.append(p)
            except OSError:
                pass
    return hits


def arm_links():
    return [os.path.join(d, n) for d, ds, fs in os.walk(arm_out, onerror=lambda e: None) for n in ds + fs
            if os.path.islink(os.path.join(d, n))]

def find_names(patterns):
    # every path the part can see, anywhere on the box's local file systems, whose name matches a pattern
    expr = sum((["-o", "-name", p] for p in patterns), [])[1:]
    r = sh(["find", "/", "/tmp", "/var/tmp", "/dev/shm", "/dev/mqueue", "/run", "-xdev", "(", "-path", "/proc", "-o", "-path", "/sys", ")",
            "-prune", "-o", "(", *expr, ")", "-print"], timeout=240)
    return sorted(set(r.stdout.split("\n")) - {""})

def residue(kind):
    files = find_names([f"{kind}residue_*"])
    procs = [l for l in sh(["pgrep", "-af", f"{kind}residue_marker"]).stdout.split("\n") if l.strip()]
    user = "cmp-" + kind
    ipc = [l for l in sh(["ipcs", "-c"]).stdout.split("\n") if re.search(rf"\s{re.escape(user)}\s", l)]
    return files + procs + ipc

def writable_dirs():
    # directories outside the shared run directory and this invocation that this part user can write
    r = sh(["find", "/", "/tmp", "/var/tmp", "/dev/shm", "/dev/mqueue", "/run", "-xdev", "(", "-path", "/proc", "-o", "-path", "/sys", "-o",
            "-path", S, ")", "-prune", "-o", "-type", "d", "-writable", "-print"], timeout=240)
    return [d for d in sorted(set(r.stdout.split("\n")) - {""}) if d != inv and not d.startswith(inv + "/")]

def schedule(tool):
    # a part user must not be able to schedule a job (cron.deny, at.deny)
    if tool == "crontab":
        r = subprocess.run(["crontab", "-"], input=f"* * * * * touch /tmp/cronresidue_{tok}\n", capture_output=True, text=True, timeout=30)
    else:
        r = subprocess.run(["at", "now + 1 minute"], input=f"touch /tmp/atresidue_{tok}\n", capture_output=True, text=True, timeout=30)
    return must(r.returncode == 0, f"{tool} scheduled")

def command_files():
    # the evaluate stage's own box command files (every NNNN-<name>.sh|log|gpu|rc after reproduce-freeze) must be private
    names = [n for n in os.listdir(S) if re.fullmatch(r"[0-9]{4}-.+\.(sh|log|gpu|rc)", n)]
    freeze = [int(n[:4]) for n in names if n[5:].startswith("reproduce-freeze.")]
    must(freeze, "a reproduce-freeze command file in the shared run directory")
    hits = []
    for n in sorted(names):
        if int(n[:4]) > max(freeze) and os.path.isfile(os.path.join(S, n)):
            try:
                open(os.path.join(S, n), "rb").read(1)
                hits.append(n)
            except OSError:
                pass
    return hits

allow("score_and_read_private", score)
none("command_files_readable", command_files)
none("arm_out_symlinks", arm_links)
none("arm_out_unreadable_dirs", lambda: [os.path.join(d, x) for d, ds, fs in os.walk(arm_out, onerror=lambda e: None) for x in ds
                                         if not os.access(os.path.join(d, x), os.R_OK | os.X_OK)])
allow("read_arm_probe", lambda: sorted(json.load(open(os.path.join(arm_out, "probe.json"))))[:5])
allow("gpu_visible", lambda: must("GPU" in sh(["nvidia-smi", "-L"]).stdout, "nvidia-smi -L lists a GPU"))
allow("hash_search_finds_private", lambda: must(any(p.startswith(inside) for p in found), "found under cmp-private"))
none("private_copies_elsewhere", lambda: [p for p in found if not p.startswith(inside)])
deny("read_log", lambda: os.listdir(os.path.join(inv, "log")))
deny("read_run", lambda: os.listdir(os.path.join(inv, "run")))
deny("list_comparison_work", lambda: os.listdir(os.path.join(S, "comparison-work")))
none("other_invocations_readable", others)
deny("list_jobs", lambda: os.listdir(os.path.join(S, "comparison-jobs")))
none("read_job_files", job_files)
none("proc_arm_identity", proc_identity)
none("env_arm_identity", env_identity)
none("arm_out_names_arm", lambda: [n for n in os.listdir(arm_out) if IDENT.search(n.encode())])
none("canary_hits", canary_hits)
none("protected_writes", writes)
none("arm_residue", lambda: residue("arm"))
none("eval_residue", lambda: residue("eval"))
none("read_root_environ", root_environ)
deny("sudo", lambda: must(sh(["sudo", "-n", "true"]).returncode == 0, "sudo ran"))

checks["scheduling_tools"] = {"expect": "info", "observed": {t: shutil.which(t) for t in ("crontab", "at", "atq")}}
deny("schedule_cron", lambda: schedule("crontab"))
deny("schedule_at", lambda: schedule("at"))
none("scheduled_residue", lambda: find_names(["cronresidue_*", "atresidue_*"]))
planted = writable_dirs()
checks["writable_dirs"] = {"expect": "info", "observed": planted[:60]}
for d in ["/tmp", "/var/tmp", "/dev/shm"] + planted:
    try:
        open(f"{d}/evalresidue_{tok}", "w").write(tok)
    except OSError:
        pass
for argv in (["ipcmk", "-M", "4096"], ["ipcmk", "-Q"], ["ipcmk", "-S", "1"]):
    sh(argv)
subprocess.Popen(["bash", "-c", "exec -a evalresidue_marker sleep 900"], stdin=subprocess.DEVNULL,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

res = {"leaks": sum(1 for c in checks.values() if c.get("leak")),
       "controls_failed": sum(1 for c in checks.values() if c.get("failed")),
       "checks": checks}
tmp = os.path.join(eval_out, ".probe.json.tmp")
with open(tmp, "w") as f:
    json.dump(res, f, indent=1, sort_keys=True)
os.replace(tmp, os.path.join(eval_out, "probe.json"))
PY
exit 0
