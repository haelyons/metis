"""Commit one folder of a blind experiment without the operator reading it. Prints counts, sizes and push status only.

Usage: python3 ~/.cache/blind01/blind_commit.py <NN> <folder under experiments/blind-NN/> <message tail>
  <NN> is the experiment's two digits (02 for blind-02); the folder is relative to the experiment, e.g. m5/run2_trace or
  science/s01. Each file is scanned for the known keys and common token formats; a file with a hit, or over 95 MB, is
  left out (counted, not named). Ignored files are force-added except virtualenvs, node_modules and caches.
"""
import os, re, subprocess, sys

M = "/home/hal/dev/interp/metis"
nn, sub, tail = sys.argv[1], sys.argv[2], " ".join(sys.argv[3:])
assert re.fullmatch(r"\d\d", nn) and re.fullmatch(r"[\w.-]+(/[\w.-]+)*", sub) and ".." not in sub.split("/")
assert re.fullmatch(r"[\w .,;:()=+-]{3,200}", tail), "message tail: plain words only"
REL = f"experiments/blind-{nn}/{sub}"
assert os.path.isdir(os.path.join(M, REL)), "no such folder"
SKIP = {"node_modules", ".venv", "venv", "__pycache__", ".cache", "pip-cache", ".git"}


def git(*args):
    return subprocess.run(["git", "-C", M, *args], capture_output=True, text=True)


keys = []
for line in open("/home/hal/dev/interp/dm_hack/.keys"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        value = line.split("=", 1)[1].strip().strip("'\"")
        if len(value) >= 12:
            keys.append(value.encode())
TOKEN = re.compile(rb"(sk-[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
                   rb"|secret_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY)")

keep, secret, large, size, total = [], 0, 0, 0, 0
for root, dirs, names in os.walk(os.path.join(M, REL)):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for n in names:
        p = os.path.join(root, n)
        if os.path.islink(p) or not os.path.isfile(p):
            continue
        total += 1
        b = os.path.getsize(p)
        if b > 95 * 1024 * 1024:
            large += 1
            continue
        data = open(p, "rb").read()
        if any(k in data for k in keys) or TOKEN.search(data):
            secret += 1
            continue
        keep.append(os.path.relpath(p, M))
        size += b
print(f"files {total}, to commit {len(keep)} ({size / 1e6:.1f} MB), left out: secret-pattern {secret}, over 95 MB {large}")
if not keep:
    sys.exit(0)
for i in range(0, len(keep), 200):
    assert git("add", "-f", "--", *keep[i:i + 200]).returncode == 0, "git add failed"
if git("diff", "--cached", "--quiet", "--", REL).returncode == 0:
    print("NOTHING_NEW")
    sys.exit(0)
r = git("commit", "-q", "-m", f"blind-{nn} {sub}: {tail} (committed unread by the operator)\n\n"
        "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
        "Claude-Session: https://claude.ai/code/session_01R9EPikyZNGLiuyGF2iw3X3", "--", REL)
assert r.returncode == 0, "commit failed"
git("push", "-q", "origin", "main")
git("fetch", "-q", "origin")
head, remote = git("rev-parse", "--short", "HEAD").stdout.strip(), git("rev-parse", "--short", "origin/main").stdout.strip()
print("PUSH_OK" if head == remote else "PUSH_FAILED", head)
