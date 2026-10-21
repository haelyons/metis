#!/usr/bin/env python3
"""Checks the runner's pinned requirements against the package index without showing the operator any name.
usage: python3 pip_pins_check.py <run_<tag>.py> <out file>
Finds a list/tuple/dict literal named PIP_PINS (or pip_pins) in the runner, parses each requirement, asks the index
whether the pinned version exists and whether each named extra is declared by that release; writes the detail to the
out file (for the reviewer) and prints counts only."""
import ast, json, re, sys, urllib.request

src = open(sys.argv[1]).read()
tree = ast.parse(src)
reqs = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id.lower() == "pip_pins" for t in node.targets):
        try: val = ast.literal_eval(node.value)
        except Exception: continue
        if isinstance(val, dict): reqs += [f"{k}=={v}" if not re.search(r"[<>=!~]", str(v)) else f"{k}{v}" for k, v in val.items()]
        elif isinstance(val, (list, tuple)): reqs += [str(x) for x in val]
        elif isinstance(val, str): reqs += val.split()
out, found, missing, extras_ok, extras_bad, unpinned = [], 0, 0, 0, 0, 0
for r in reqs:
    m = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[([^\]]*)\])?\s*(==|===)?\s*([A-Za-z0-9.*+!-]*)", r)
    if not m: out.append(f"UNPARSED {r}"); missing += 1; continue
    name, extras, op, ver = m.group(1), [e.strip() for e in (m.group(3) or "").split(",") if e.strip()], m.group(4), m.group(5)
    if not op or not ver: unpinned += 1; out.append(f"UNPINNED {r}"); continue
    try:
        d = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{ver}/json", timeout=30))
        found += 1
        declared = set(d["info"].get("provides_extra") or [])
        for e in extras:
            if e in declared: extras_ok += 1; out.append(f"OK {r}: extra {e} declared")
            else: extras_bad += 1; out.append(f"EXTRA-NOT-DECLARED {r}: extra {e} not in {sorted(declared)}")
        if not extras: out.append(f"OK {r}: release exists, {len(d.get('urls') or [])} file(s)")
    except Exception as e:
        missing += 1; out.append(f"MISSING {r}: {type(e).__name__} {str(e)[:80]}")
open(sys.argv[2], "w").write("\n".join(out) + "\n")
print(f"pins {len(reqs)}: found {found}, missing {missing}, unpinned {unpinned}; extras declared {extras_ok}, not declared {extras_bad}; detail in {sys.argv[2]}")
