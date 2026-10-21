#!/usr/bin/env python3
"""Per-version file listing from the package index for the pinned requirements that have no box-compatible wheel
(gate addendum 8), so the build can choose a version or a source route without network access. For each such
requirement: every version on the index with its files (wheels with python and platform tags, sdists), and whether a
file fits the box (CPython 3.10, Linux x86_64, or a pure wheel). Writes the listing; prints counts only.
usage: python3 pip_release_files.py <run_<tag>.py> <pip_pins_check platform file> <out listing file> [--all]"""
import ast, json, re, sys, urllib.request
runner, check, out = sys.argv[1:4]
want_all = "--all" in sys.argv
flagged = []
for l in open(check):
    if "box-compatible wheel NO" in l or want_all:
        m = re.search(r"^(?:OK|\s+)\s*([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==([A-Za-z0-9.*+!-]+)", l)
        if m: flagged.append((m.group(1), m.group(2)))
if not flagged:
    for node in ast.walk(ast.parse(open(runner).read())):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id.lower() == "pip_pins" for t in node.targets):
            try: v = ast.literal_eval(node.value)
            except Exception: continue
            items = [f"{k}=={x}" for k, x in v.items()] if isinstance(v, dict) else [str(x) for x in v]
            for r in items:
                m = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==([A-Za-z0-9.*+!-]+)", r)
                if m: flagged.append((m.group(1), m.group(2)))
fits = lambda f: f.endswith(".whl") and re.search(r"-(cp310|py3|py2\.py3)-", f) and re.search(r"(manylinux|linux_x86_64|none-any)", f)
L = ["# Per-version file listing from the package index, written by the operator's script before build 11 (the build uses no network).",
     "# Box: CPython 3.10, Linux x86_64, CUDA 12.8. 'fits' = a wheel with a cp310 or pure-python tag and a manylinux, linux_x86_64 or none-any platform tag.", ""]
nv = nf = 0
def vkey(s): return [(0, int(x)) if x.isdigit() else (1, x) for x in re.split(r"[.-]", s)]   # ints before strings, comparable
for name, pinned in flagged:
    try: d = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json", timeout=60))
    except Exception as e: L.append(f"## {name} (pinned {pinned}): index query failed ({type(e).__name__})"); continue
    rel = d.get("releases", {}); L.append(f"## {name} (pinned {pinned}): {len(rel)} version(s) on the index; requires_python of the latest: {d['info'].get('requires_python')}")
    try:
        dp = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{pinned}/json", timeout=60))
        L.append(f"### pinned release {name}=={pinned}: requires_python {dp['info'].get('requires_python')}; requires_dist ({len(dp['info'].get('requires_dist') or [])} line(s)):")
        L += [f"    {r}" for r in (dp['info'].get('requires_dist') or [])] or ["    (none declared)"]
        L.append(f"### files of the pinned release ({len(dp.get('urls') or [])}):")
        L += [f"    {u.get('filename')} [{'fits' if fits(u.get('filename', '')) else 'does not fit'}]{' YANKED' if u.get('yanked') else ''}" for u in (dp.get('urls') or [])]
    except Exception as e: L.append(f"### pinned release {name}=={pinned}: index query failed ({type(e).__name__})")
    for v in sorted(rel, key=vkey):
        files = rel[v]; nv += 1; nf += len(files)
        tags = []
        for f in files:
            fn = f.get("filename", ""); yanked = " YANKED" if f.get("yanked") else ""
            kind = "wheel" if fn.endswith(".whl") else "sdist" if fn.endswith((".tar.gz", ".zip")) else "other"
            tags.append(f"{fn}{yanked} [{kind}{', fits' if fits(fn) else ''}]")
        mark = " <- pinned" if v == pinned else ""
        L.append(f"- {v}{mark}: {len(files)} file(s), fits {sum(1 for f in files if fits(f.get('filename', '')))}: " + "; ".join(tags))
    L.append("")
open(out, "w").write("\n".join(L) + "\n")
print(f"listing written for {len(flagged)} requirement(s): {nv} version(s), {nf} file(s); file {out}")
