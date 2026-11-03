"""Which secret pattern class matched in an uncommitted blind file. Prints class, size, and the file's path with
only structural parts (top folder under out/, agent call folder label if content-free); never matched text."""
import os, re, subprocess, sys

M = "/home/hal/dev/interp/metis"
REL = f"experiments/blind-{sys.argv[1]}/{sys.argv[2]}"
keys = {}
for line in open("/home/hal/dev/interp/dm_hack/.keys"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        name, value = line.split("=", 1)
        value = value.strip().strip("'\"")
        if len(value) >= 12:
            keys[name.strip()] = value.encode()
CLASSES = {"sk": rb"sk-[A-Za-z0-9_-]{20,}", "hf": rb"hf_[A-Za-z0-9]{20,}", "ghp": rb"ghp_[A-Za-z0-9]{20,}",
           "github_pat": rb"github_pat_[A-Za-z0-9_]{20,}", "secret_": rb"secret_[A-Za-z0-9]{20,}", "AKIA": rb"AKIA[0-9A-Z]{16}",
           "bearer": rb"Bearer [A-Za-z0-9._-]{20,}", "private_key": rb"-----BEGIN [A-Z ]*PRIVATE KEY"}
untracked = subprocess.run(["git", "-C", M, "ls-files", "-o", "--", REL], capture_output=True, text=True).stdout.split()
for f in untracked:
    data = open(os.path.join(M, f), "rb").read()
    hits = [n for n, v in keys.items() if v in data] + [c for c, rx in CLASSES.items() if re.search(rx, data)]
    if not hits:
        continue
    parts = os.path.relpath(f, REL).split("/")
    safe = [p if re.fullmatch(r"[A-Za-z0-9_.:-]{1,60}", p) and not re.search(r"[A-Z][a-z]{3,}", p) else "<name>" for p in parts]
    print("file", "/".join(safe), "bytes", len(data), "classes", hits,
          "count", {c: len(re.findall(CLASSES[c], data)) for c in hits if c in CLASSES})
