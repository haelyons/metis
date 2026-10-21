#!/usr/bin/env python3
"""Pre-build test of a gate's proposed pins (addendum 9 pattern): the runner's current PIP_PINS with the addendum's
`name==version` lines applied as substitutions or additions (never the union, which conflicts by construction), written
as a requirements file for pip_resolve-style dry runs. Prints counts only.
usage: python3 pip_overlay_resolve.py <run_<tag>.py> <addendum text file> <out requirements file>"""
import ast, re, sys
runner, text, out = sys.argv[1:4]
norm = lambda n: re.sub(r"[-_.]+", "-", n.split("[")[0]).lower()
cur = {}
for node in ast.walk(ast.parse(open(runner).read())):
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id.lower() == "pip_pins" for t in node.targets):
        v = ast.literal_eval(node.value)
        for r in ([f"{k}=={x}" for k, x in v.items()] if isinstance(v, dict) else [str(x) for x in v]):
            m = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*(?:\[[^\]]*\])?)==(.+)$", r)
            if m: cur[norm(m.group(1))] = r.strip()
cand = sorted(set(re.findall(r"\b([A-Za-z0-9][A-Za-z0-9_.-]*(?:\[[A-Za-z0-9_,.-]+\])?==[0-9][A-Za-z0-9.+!-]*)", open(text).read())))
new = {}
for l in cand:
    key = norm(l.split("==")[0])
    if key in cur and cur[key].lower() == l.lower(): continue
    new[key] = l
over = dict(cur); over.update(new)
open(out, "w").write("\n".join(over.values()) + "\n")
print(f"overlay: {len(over)} pins ({len(over) - len(new)} current kept, {len(new)} replaced or added from {len(cand)} candidate lines)")
