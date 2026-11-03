"""Release a drafted contract to the blind operator only after an independent audit found no seed content (owner approval
2026-11-03, option 1). Checks: the audit step's AUDIT.json validates with seed_content "none"; the draft and audit steps are
committed and clean; the draft's bytes now equal its bytes in the commit that added it, and that commit precedes the
audit commit (the auditor read those bytes). Then copies DRAFT.md to ~/.cache/blind01/released/<draft step>_DRAFT.md with its
SHA-256, and prints the path. Prints nothing of the draft itself.
Usage: python3 ~/.cache/blind01/sci_draft_release.py <NN> <draft step sNN> <audit step sNN>
"""
import hashlib, json, os, subprocess, sys

M = "/home/hal/dev/interp/metis"
NN, DS, AS = sys.argv[1:4]
rel = lambda s: f"experiments/blind-{NN}/science/{s}"
git = lambda *a: subprocess.run(["git", "-C", M, *a], capture_output=True, text=True)
a = json.load(open(f"{M}/{rel(AS)}/AUDIT.json"))
assert a.get("seed_content") == "none" and a.get("codes") == [], "audit found seed content"
for s in (DS, AS):
    assert not git("status", "--porcelain", "--", rel(s)).stdout, f"{s} not committed"
draft = f"{rel(DS)}/DRAFT.md"
added = git("log", "--format=%H", "--diff-filter=A", "--", draft).stdout.split()
assert len(added) == 1, "draft added more than once"
changes = git("log", "--format=%H", "--", draft).stdout.split()
assert changes == added, "draft changed after it was added"
audit = git("log", "--format=%H", "--diff-filter=A", "--", f"{rel(AS)}/AUDIT.json").stdout.split()
assert len(audit) == 1 and git("merge-base", "--is-ancestor", added[0], audit[0]).returncode == 0, "audit does not follow the draft"
data = open(f"{M}/{draft}", "rb").read()
assert data == subprocess.run(["git", "-C", M, "show", f"{added[0]}:{draft}"], capture_output=True).stdout, "draft bytes differ from its commit"
out = os.path.expanduser(f"~/.cache/blind01/released/{DS}_DRAFT.md")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "wb").write(data)
print(f"RELEASED {out} sha256 {hashlib.sha256(data).hexdigest()} draft commit {added[0][:8]} audit commit {audit[0][:8]}")
