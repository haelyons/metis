"""Metadata of one tree run for the blind operator: run totals, call states and stage names, and the calibration
records' enums and numbers. Never titles, questions, card text, table rows, quantity ids, errors or log text.
Usage: python3 ~/.cache/blind01/tree_read.py <NN> <stamp>-tree   (experiments/blind-NN/<stamp>-tree)
       python3 ~/.cache/blind01/tree_read.py --path <run out dir>  (a public run, for testing)
"""
import json, os, re, sys
from collections import Counter

if sys.argv[1] == "--path":
    O = sys.argv[2]
else:
    assert re.fullmatch(r"\d\d", sys.argv[1]) and re.fullmatch(r"\d{8}-\d{4}-tree(-\d+)?", sys.argv[2])
    O = f"/home/hal/dev/interp/metis/experiments/blind-{sys.argv[1]}/{sys.argv[2]}/out"


def load(name):
    try:
        return json.load(open(os.path.join(O, name)))
    except Exception:
        return None


num = lambda v: round(v, 3) if isinstance(v, (int, float)) and not isinstance(v, bool) else None
r = load("run.json") or {}
t = r.get("totals") or {}
print("== run", "started", r.get("started"), "finished", r.get("finished"))
print("totals", {k: num(t.get(k)) for k in ("cost_usd", "tokens", "calls")})
for k in ("by_family", "by_model"):
    if isinstance(t.get(k), dict):
        print(k, {m: {f: num(v.get(f)) for f in ("calls", "cost_usd", "tokens")} for m, v in t[k].items() if re.fullmatch(r"[\w./@-]{1,60}", m)})
for k in ("substitutions", "refusals"):
    if k in t:
        print(k, len(t[k]) if isinstance(t[k], list) else num(t[k]))
s = load("status.json") or {}
calls = s.get("calls") or []
print("== status", "stage", s.get("stage") if re.fullmatch(r"[\w -]{1,30}", str(s.get("stage"))) else "?", "done", s.get("done"),
      "error", bool(s.get("error")))
print("call states", dict(Counter(c.get("state") for c in calls)))
stage = lambda c: re.sub(r"-resample$", "", str(c.get("id", "")).split(":")[-1])
print("calls by role", dict(Counter(stage(c) for c in calls if re.fullmatch(r"[a-z0-9-]{1,30}", stage(c)))))
print("calls with errors", sum(1 for c in calls if c.get("errors")), "attempts>1", sum(1 for c in calls if (c.get("attempts") or 0) > 1))
res = load("result.json")
if not isinstance(res, dict):
    print("== result: none" if res is None else "== result: not an object")
    sys.exit(0)
print("== result keys", sorted(k for k in res if re.fullmatch(r"[a-z_]{1,20}", k)), "cards", len(res.get("cards") or []),
      "log lines", len(res.get("log") or []))
cal = res.get("calibration")
if cal is None:
    print("calibration: absent")
    sys.exit(0)
print("calibration states", dict(Counter(c.get("state") for c in cal)))
for i, c in enumerate(cal, 1):
    req = c.get("required") or []
    p = c.get("predictions") or {}
    print(f"record {i}: state {c.get('state')}, plan_usd {num(c.get('plan_usd'))}, inputs {len(req)}, "
          f"anchor {'yes' if c.get('anchor') else 'no'}, expected {p.get('expected') if p.get('expected') in ('if_lever', 'if_not', 'unsure') else None}")
    for j, u in enumerate(req, 1):
        line = u.get("line") or {}
        print(f"  input {i}.{j}: basis {u.get('basis') if u.get('basis') in ('GUESS', 'PROXY', 'MEASURED', 'CITED', 'DERIVED', 'DESIGN') else '?'}, "
              f"k_budget {num(u.get('k_budget'))}, spend_through_phase_usd {num(u.get('cum_spend_through_measured_by'))}, "
              f"line_hours {num(line.get('hours'))}, line_usd {num(line.get('usd'))}, measured_by_named {bool(u.get('measured_by'))}, "
              f"gate {'yes' if (u.get('phase') or {}).get('gate') else 'no'}")
