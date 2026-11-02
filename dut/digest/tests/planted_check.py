#!/usr/bin/env python3
"""The planted expectations for the run a finished digest came from. Standard library only.

Usage: python3 -I planted_check.py <digest dir> [planted.json]
The run is named by MANIFEST.json's run_name. Each expectation: digest.json values ("enums"), and for each "qa" rule
one QA.md paragraph that holds any of its "terms" (case-insensitive) and any of its "figures". Exit 0 all held,
1 a miss, 2 no expectations for this run.
"""
import json, os, sys

if len(sys.argv) not in (2, 3):
    sys.exit(__doc__)
d = sys.argv[1]
planted = json.load(open(sys.argv[2] if len(sys.argv) == 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "planted.json")))
run = json.load(open(os.path.join(d, "MANIFEST.json")))["run_name"]
if run not in planted:
    print(f"no planted expectations for {run}")
    sys.exit(2)
spec, misses = planted[run], []
enums = json.load(open(os.path.join(d, "digest.json")))
for k, want in spec.get("enums", {}).items():
    print(f"{'ok  ' if enums.get(k) == want else 'MISS'} {k}: want {want}, got {enums.get(k)}")
    misses += [k] if enums.get(k) != want else []
paras = [p.replace("\n", " ") for p in open(os.path.join(d, "QA.md"), encoding="utf-8").read().split("\n\n")]
for i, rule in enumerate(spec.get("qa", [])):
    hit = next((p for p in paras if any(t.lower() in p.lower() for t in rule["terms"]) and any(f in p for f in rule["figures"])), None)
    print(f"{'ok  ' if hit else 'MISS'} qa[{i}]: a paragraph naming one of {rule['terms']} with one of {rule['figures']}" + (f": {hit[:100]}" if hit else ""))
    misses += [f"qa[{i}]"] if not hit else []
print(f"{run}: " + ("all planted expectations held" if not misses else "missed " + ", ".join(misses)))
sys.exit(1 if misses else 0)
