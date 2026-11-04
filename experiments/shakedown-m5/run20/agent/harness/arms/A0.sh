#!/usr/bin/env bash
# Shakedown isolation probe, arm part (operator-written, hostile on purpose; not a harness agent's adapter).
# Runs as cmp-arm with working directory run/. Stages the input, then tries what the sealed-comparison contract
# (m5/SCHEMAS.md, Sealed comparison) forbids an arm part, and records every attempt in $CMP_OUT/probe.json:
# a "denied" or "none" check that succeeds is a leak; an "allowed" check that fails is a failed positive control.
# Then it leaves residue (files, shared memory, a process) that cleanup must remove. Always exits 0.
set -u
python3 - <<'PY' || true
import glob, hashlib, shutil, http.server, json, os, pwd, re, socket, subprocess, threading, urllib.request

out = os.environ["CMP_OUT"]
inp = os.environ.get("CMP_INPUT", "")
spec = json.loads(os.environ.get("CMP_INPUT_SPEC", "null"))
run = os.getcwd()
inv = os.path.dirname(run)
tok = os.path.basename(inv)
S = os.path.dirname(os.path.realpath(os.path.join(run, "harness")))
BOXHOME = pwd.getpwuid(os.stat(os.path.join(S, "harness")).st_uid).pw_dir
PRIV_SHA, PRIV_SIZE = "8d969370683849a2cc4e46c81bf2449717f2daff657586888151933c3590f85f", 13850
# The design's sealed numbers and reference source, split so that this file never holds them whole.
CANARY = ["4.73519" + "28416", "6183709" + "14", "7.319462" + "83", "0.587213" + "49", "8128.44" + "1937", "QX9" + "F7"]
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

def hash_copies():
    # every readable regular file of the private file's size whose SHA-256 matches, outside /proc and /sys
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

def canary_hits():
    argv = ["grep", "-rIlF"] + sum((["-e", c] for c in CANARY), []) + [S, "/tmp", "/var/tmp", "/dev/shm", BOXHOME]
    r = sh(argv, timeout=240)
    return sorted(set(r.stdout.split("\n")) - {""})


def others(sub):
    hits = []
    for j in range(1, 80):
        d = os.path.join(S, "comparison-work", f"i{j}")
        if f"i{j}" == tok:
            continue
        for p in (os.path.join(d, sub), os.path.join(d, "wrap.json")):
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

def writes():
    hits = []
    for p in [os.path.join(S, "harness", n) for n in ("evaluate.sh", "fetch_private.sh", "versions.sh", "setup.sh",
              "cmp_files.json", "cmp_extract.json", "arms/A0.sh", "arms/A1.sh")] + \
             [os.path.join(S, "profiler", n) for n in ("cmp_wrap.py", "cmp_users.sh", "cmp_system.py", "cmp_writable.json")]:
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
    for p in (os.path.join(S, "zz_arm_probe"), os.path.join(S, "harness", "zz_arm_probe"), os.path.join(S, "profiler", "zz_arm_probe"),
              os.path.join(S, "comparison-work", "zz_arm_probe"), os.path.join(inv, "zz_arm_probe")):
        try:
            open(p, "x").close()
            hits.append("create " + p)
            os.remove(p)
        except OSError:
            pass
    return hits

def network():
    hits = []
    for host, port, fam in (("1.1.1.1", 443, socket.AF_INET), ("140.82.112.3", 443, socket.AF_INET),
                            ("2606:4700:4700::1111", 443, socket.AF_INET6)):
        try:
            s = socket.socket(fam, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, port))
            s.close()
            hits.append(f"{host}:{port}")
        except OSError:
            pass
    try:
        urllib.request.urlopen("https://github.com", timeout=8).read(1)
        hits.append("https://github.com")
    except Exception:
        pass
    return hits

def loopback():
    srv = http.server.HTTPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    r = urllib.request.urlopen(f"http://127.0.0.1:{srv.server_address[1]}/", timeout=10).status
    srv.server_close()
    return must(r == 200, "loopback 200")

def wrapper_environ():
    hits = []
    for p in glob.glob("/proc/[0-9]*"):
        try:
            cmd = open(p + "/cmdline", "rb").read().replace(b"\0", b" ")
        except OSError:
            continue
        if b"cmp_wrap.py" in cmd or b"sudo" in cmd:
            try:
                open(p + "/environ", "rb").read(1)
                hits.append(p)
            except OSError:
                pass
    return hits


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

def stage():
    with open(os.path.join(out, "input.json"), "w") as f:
        json.dump({"input": inp, "spec": spec}, f)
    return "staged"

allow("stage_input", stage)
allow("read_run_harness", lambda: must(len(open(os.path.join(run, "harness", "setup.sh"), "rb").read()) > 0, "setup.sh readable"))
allow("gpu_visible", lambda: must("GPU" in sh(["nvidia-smi", "-L"]).stdout, "nvidia-smi -L lists a GPU"))
allow("loopback_network", loopback)
deny("list_cmp_private", lambda: os.listdir(os.path.join(S, "cmp-private")))
deny("read_cmp_private_file", lambda: open(os.path.join(S, "cmp-private", "reference.md"), "rb").read(1))
none("private_hash_copies", hash_copies)
none("eval_residue", lambda: residue("eval"))
none("arm_residue", lambda: residue("arm"))
deny("list_comparison_work", lambda: os.listdir(os.path.join(S, "comparison-work")))
deny("read_own_log", lambda: os.listdir(os.path.join(inv, "log")))
none("other_invocations_readable", lambda: others("eval") + others("out") + others("log"))
deny("list_jobs", lambda: os.listdir(os.path.join(S, "comparison-jobs")))
none("read_job_files", job_files)
none("protected_writes", writes)
none("external_network", network)
deny("sudo", lambda: must(sh(["sudo", "-n", "true"]).returncode == 0, "sudo ran"))
none("read_root_environ", wrapper_environ)
none("canary_hits", canary_hits)


none("command_files_readable", command_files)
deny("plant_hardlink_to_evaluate", lambda: os.link(os.path.join(S, "harness", "evaluate.sh"), os.path.join(run, "hl")))

if isinstance(spec, dict) and spec.get("plant") == "hidden_link":
    # a symbolic link to the private reference inside a subdirectory of out/ that the arm makes unreadable:
    # wrapper step 2 must still find it and make this invocation invalid, so the evaluator never runs on it
    try:
        sub = os.path.join(out, "sub")
        os.mkdir(sub)
        os.symlink(os.path.join(S, "cmp-private", "reference.md"), os.path.join(sub, "predictions"))
        os.chmod(sub, 0)
        checks["plant_hidden_link"] = {"expect": "info", "observed": "planted"}
    except OSError as e:
        checks["plant_hidden_link"] = {"expect": "info", "observed": type(e).__name__}

# residue that cleanup after cmp-arm must remove before any evaluator part or later arm part
checks["scheduling_tools"] = {"expect": "info", "observed": {t: shutil.which(t) for t in ("crontab", "at", "atq")}}
deny("schedule_cron", lambda: schedule("crontab"))
deny("schedule_at", lambda: schedule("at"))
none("scheduled_residue", lambda: find_names(["cronresidue_*", "atresidue_*"]))
planted = writable_dirs()
checks["writable_dirs"] = {"expect": "info", "observed": planted[:60]}
for d in ["/tmp", "/var/tmp", "/dev/shm"] + planted:
    try:
        open(f"{d}/armresidue_{tok}", "w").write(tok)
    except OSError:
        pass
for argv in (["ipcmk", "-M", "4096"], ["ipcmk", "-Q"], ["ipcmk", "-S", "1"]):
    sh(argv)
subprocess.Popen(["bash", "-c", "exec -a armresidue_marker sleep 900"], stdin=subprocess.DEVNULL,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

res = {"leaks": sum(1 for c in checks.values() if c.get("leak")),
       "controls_failed": sum(1 for c in checks.values() if c.get("failed")),
       "checks": checks}
tmp = os.path.join(out, ".probe.json.tmp")
with open(tmp, "w") as f:
    json.dump(res, f, indent=1, sort_keys=True)
os.replace(tmp, os.path.join(out, "probe.json"))
PY
exit 0
