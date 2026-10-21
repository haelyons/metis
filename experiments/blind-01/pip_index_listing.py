#!/usr/bin/env python3
"""Offline package-index listing for the build (gate addendum 7): for the pinned requirement whose extra the index check
found undeclared, list every distribution on the index whose name starts with that requirement's name (with its available
versions) and the extras the pinned release declares. Writes the listing file; prints counts only.
usage: python3 pip_index_listing.py <run_<tag>.py> <pip_pins_check file> <out listing file>"""
import ast, json, re, sys, urllib.request, html
runner, check, out = sys.argv[1:4]
# the requirement with the undeclared extra (first EXTRA-NOT-DECLARED line of the check), else the first pin
bad = [l for l in open(check) if l.startswith("EXTRA-NOT-DECLARED")]
req = bad[0].split(" ", 1)[1].split(":")[0].strip() if bad else None
pins = []
for node in ast.walk(ast.parse(open(runner).read())):
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id.lower() == "pip_pins" for t in node.targets):
        try: v = ast.literal_eval(node.value)
        except Exception: continue
        pins += [f"{k}=={x}" for k, x in v.items()] if isinstance(v, dict) else [str(x) for x in v]
if not req and pins: req = pins[0]
m = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*==\s*([A-Za-z0-9.*+!-]+)", req or "")
if not m: print("no requirement to list"); sys.exit(2)
name, ver = m.group(1), m.group(3)
norm = lambda s: re.sub(r"[-_.]+", "-", s).lower()
simple = urllib.request.urlopen("https://pypi.org/simple/", timeout=120).read().decode("utf-8", "replace")
names = sorted({html.unescape(n) for n in re.findall(r">([^<]+)</a>", simple) if norm(n).startswith(norm(name))})
L = [f"# Package-index listing written by the operator's script before build 10 (no network for the build)", f"# requirement under question: {req}", f"# distributions whose normalised name starts with '{norm(name)}': {len(names)}", ""]
nver = 0
for n in names:
    try:
        d = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{n}/json", timeout=60))
        vs = sorted(d.get("releases", {}).keys(), key=lambda s: [int(x) if x.isdigit() else x for x in re.split(r"[.-]", s)])
        nver += len(vs); L.append(f"{n}: {len(vs)} version(s): {', '.join(vs[-12:])}{' (older omitted)' if len(vs) > 12 else ''}")
    except Exception as e: L.append(f"{n}: index query failed ({type(e).__name__})")
try:
    d = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{ver}/json", timeout=60))
    ex = d["info"].get("provides_extra") or []; rd = d["info"].get("requires_dist") or []
    L += ["", f"# pinned release {name}=={ver}: extras declared: {ex or 'none'}; requires_dist entries: {len(rd)}", *[f"  requires: {r}" for r in rd]]
    L += ["", f"# files of {name}=={ver}: " + ", ".join(sorted({u['filename'] for u in d.get('urls', [])}))]
except Exception as e: L += ["", f"# pinned release {name}=={ver}: index query failed ({type(e).__name__})"]
open(out, "w").write("\n".join(L) + "\n")
print(f"listing written: {len(names)} distribution(s) with the prefix, {nver} versions in all, pinned release extras declared: {len(ex) if 'ex' in dir() else '?'}; file {out}")
