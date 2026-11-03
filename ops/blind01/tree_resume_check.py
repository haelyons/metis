"""Check a tree rerun with --resume against the earlier run (U55, 2026-11-03): every agent call answered from the cache,
and the same table, cards, inventory, frontier and calibration states, keys and required inputs; the records gain only
`name`, `unit`, `band` and `judged`. Prints counts and booleans only, never content.
Usage: python3 ~/.cache/blind01/tree_resume_check.py <NN> <old stamp>-tree <new stamp>-tree
"""
import collections, json, sys

X = f"/home/hal/dev/interp/metis/experiments/blind-{sys.argv[1]}"
old, new = (f"{X}/{s}/out" for s in sys.argv[2:4])
ev = collections.Counter(json.loads(l).get("type") for l in open(f"{new}/journal.jsonl") if l.strip())
a, b = (json.load(open(f"{d}/result.json")) for d in (old, new))
same = {k: a.get(k) == b.get(k) for k in ("table", "cards", "inventory", "frontier")}
core = lambda r: {"key": r.get("key"), "state": r.get("state"), "plan_usd": r.get("plan_usd"), "anchor": r.get("anchor"), "predictions": r.get("predictions"),
                  "required": [{k: v for k, v in u.items() if k not in ("name", "unit", "band")} for u in r.get("required", [])]}
ca, cb = a.get("calibration", []), b.get("calibration", [])
same["calibration_core"] = [core(r) for r in ca] == [core(r) for r in cb]
added = all(set(r) - set(o) == {"judged"} for r, o in zip(cb, ca)) and len(ca) == len(cb)
fields = all({"name", "unit", "band"} <= set(u) for r in cb for u in r.get("required", []))
judged = sum(r.get("judged") is not None for r in cb)
print(f"events started {ev['started']} cached {ev['cached']} result {ev['result']} failed {ev['failed']} understudy {ev['understudy']}")
print("same", " ".join(f"{k} {v}" for k, v in same.items()), f"| records {len(cb)} judged {judged} | only judged added {added} | name/unit/band on every input {fields}")
ok = ev["result"] == 0 and ev["failed"] == 0 and ev["started"] == ev["cached"] > 0 and all(same.values()) and added and fields
print("RESUME_IDENTICAL" if ok else "RESUME_DIFFERS")
