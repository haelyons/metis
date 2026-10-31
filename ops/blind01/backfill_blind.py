"""Commit uncommitted blind-01 evidence without the operator reading it. Prints counts, sizes and ignore rules only.

Usage: python3 ~/.cache/blind01/backfill_blind.py brief|old [--commit]
  brief  experiments/blind-01/m5/BRIEF.md (untracked).
  old    files git ignores under experiments/blind-01 outside m5 (earlier loop and measure runs).
Each file is scanned for the known keys and common token formats; a file with a hit, or over 95 MB, is left out
(counted, not named). --commit stages the rest (force-adding ignored files), commits and pushes.
"""
import os, re, subprocess, sys
from collections import Counter

M = "/home/hal/dev/interp/metis"
BLIND = "experiments/blind-01"
mode, commit = sys.argv[1], "--commit" in sys.argv
assert mode in ("brief", "old")


def git(*args, inp=None):
    return subprocess.run(["git", "-C", M, *args], input=inp, capture_output=True, text=True)


keys = []
for line in open("/home/hal/dev/interp/dm_hack/.keys"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        value = line.split("=", 1)[1].strip().strip("'\"")
        if len(value) >= 12:
            keys.append(value.encode())
TOKEN = re.compile(rb"(sk-[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
                   rb"|secret_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY)")

if mode == "brief":
    files = [BLIND + "/m5/BRIEF.md"]
    rules = Counter({"untracked": 1})
else:
    listed = git("ls-files", "-oi", "--exclude-standard", "--", BLIND).stdout.splitlines()
    listed = [f for f in listed if not f.startswith(BLIND + "/m5/")]
    checked = git("check-ignore", "-v", "--no-index", "--stdin", inp="\n".join(listed) + "\n").stdout.splitlines()
    # Only the top-level .gitignore's wf-* rule marks agent transcripts; nested rules are named by blind files, so only
    # counted. Virtualenvs, node_modules, keys and caches are not evidence and are never added.
    rules, files = Counter(), []
    for line in checked:
        if "\t" not in line:
            continue
        source, _, pattern = line.split("\t")[0].split(":", 2)
        top = source == ".gitignore"
        rules[pattern if top else "<nested rule>"] += 1
        if top and pattern == "experiments/blind-01/*/out/wf-*/" and "/.keys" not in line:
            files.append(line.split("\t", 1)[1])

keep, secret, large, size = [], 0, 0, 0
for f in files:
    p = os.path.join(M, f)
    if not os.path.isfile(p):
        continue
    n = os.path.getsize(p)
    if n > 95 * 1024 * 1024:
        large += 1
        continue
    data = open(p, "rb").read()
    if any(k in data for k in keys) or TOKEN.search(data):
        secret += 1
        continue
    keep.append(f)
    size += n
print(f"{mode}: files {len(files)}, to commit {len(keep)} ({size / 1e6:.1f} MB), left out: secret-pattern {secret}, over 95 MB {large}")
print("ignore rules:", dict(rules))
if not commit or not keep:
    sys.exit(0)
for i in range(0, len(keep), 200):
    r = git("add", "-f", "--", *keep[i:i + 200])
    assert r.returncode == 0, "git add failed"
msg = ("blind-01 m5: owner brief, committed unread by the operator" if mode == "brief" else
       "blind-01: backfill earlier loop and measure run evidence (owner: durable agent records), committed unread")
r = git("commit", "-q", "-m", msg + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
        "Claude-Session: https://claude.ai/code/session_01R9EPikyZNGLiuyGF2iw3X3")
assert r.returncode == 0, "commit failed"
git("push", "-q", "origin", "main")
git("fetch", "-q", "origin")
head, remote = git("rev-parse", "--short", "HEAD").stdout.strip(), git("rev-parse", "--short", "origin/main").stdout.strip()
print("PUSH_OK" if head == remote else "PUSH_FAILED", head)
