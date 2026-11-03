"""After a science step: validate status.json against the step's fixed enums, NEXT.json against the action schema,
tree_args.json against the keys the tree reads, predictions.json and outcomes.json; score the previous step's
predictions (Brier, numbers only); commit and push the step folder unread. Prints enum values, counts, numbers and
push status only; never file names inside the folder's content, agent text, questions or pick keys.
Usage: python3 ~/.cache/blind01/sci_post.py <NN> <sNN>
"""
import json, os, re, subprocess, sys

B = os.path.expanduser("~/.cache/blind01")
M = "/home/hal/dev/interp/metis"
nn, step = sys.argv[1], sys.argv[2]
assert re.fullmatch(r"\d\d", nn) and re.fullmatch(r"s\d\d", step)
X = f"{M}/experiments/blind-{nn}"
D = f"{X}/science/{step}"
spec = json.load(open(f"{B}/sci_{step}.enums.json"))
ok_all = True


def load(name):
    try:
        return json.load(open(os.path.join(D, name)))
    except Exception:
        return None


def bad(msg):
    global ok_all
    ok_all = False
    print("INVALID", msg)


s = load("status.json")
E = spec["enums"]
if isinstance(s, dict) and set(s) == set(E) and all(s[k] in E[k] for k in E):
    print("STATUS " + json.dumps(dict(sorted(s.items())), sort_keys=True))
else:
    bad("status")
    s = {}

for f in ("ASSESSMENT.md", "NARROWING.md", "PREDICTIONS.md"):
    p = os.path.join(D, f)
    print(f, "bytes", os.path.getsize(p) if os.path.isfile(p) else "MISSING")
    if not os.path.isfile(p):
        bad(f)

n = load("NEXT.json")
action = n.get("action") if isinstance(n, dict) else None
if action not in spec["actions"]:
    bad("next action")
elif s and s.get("next_action") != action:
    bad("next action differs from status")
elif action == "tree":
    if set(n) != {"action", "tree_args"} or n["tree_args"] != "tree_args.json":
        bad("next keys")
    t = load("tree_args.json")
    TK = {"seed", "fixed_roots", "seed_ideas", "picks_per_branch", "pool_k", "require_compute_lever", "deepen_on_signal",
          "budget_usd", "budget_covers_storage", "budget_covers_tax"}
    if not isinstance(t, dict) or not set(t) <= TK or not isinstance(t.get("seed"), int):
        bad("tree_args keys or seed")
    else:
        roots, ideas = t.get("fixed_roots", []), t.get("seed_ideas", [])
        okr = isinstance(roots, list) and 1 <= len(roots) <= 3 and all(isinstance(r, str) and r.strip() for r in roots)
        oki = isinstance(ideas, list) and len(ideas) <= 4 and all(isinstance(i, (str, dict)) for i in ideas)
        okp = t.get("picks_per_branch", 2) in (1, 2)
        okb = isinstance(t.get("budget_usd", 1000), (int, float)) and 0 < t.get("budget_usd", 1000) <= 1000
        if not (okr and oki and okp and okb):
            bad("tree_args values")
        print("TREE_ARGS roots", len(roots) if isinstance(roots, list) else "?", "seed_ideas", len(ideas) if isinstance(ideas, list) else "?",
              "picks_per_branch", t.get("picks_per_branch", "default"), "budget_usd", t.get("budget_usd", "default"),
              "root_words", [len(r.split()) for r in roots] if okr else "?")
elif action == "measure":
    if set(n) != {"action", "tree_run", "pick"} or not re.fullmatch(r"\d{8}-\d{4}-tree(-\d+)?", str(n.get("tree_run"))) \
            or not os.path.isfile(f"{X}/{n['tree_run']}/out/result.json") or not isinstance(n.get("pick"), str):
        bad("measure next")
    else:
        recs = json.load(open(f"{X}/{n['tree_run']}/out/result.json")).get("calibration") or []
        rec = next((r for r in recs if r.get("key") == n["pick"]), None)
        print("MEASURE tree_run", n["tree_run"], "pick found", rec is not None, "state", rec and rec.get("state"),
              "inputs", rec and len(rec.get("required") or []))
elif action == "m5":
    flags = n.get("new_run_flags", [])
    okf = isinstance(flags, list) and all(re.fullmatch(r"--(stop-after-(profile|reproduce)|units-(check|probe)=run\d+|harness-from=[A-Za-z0-9_]+)", f) for f in flags)
    if set(n) != {"action", "brief", "new_run_flags"} or not re.fullmatch(r"[\w.-]+\.md", str(n.get("brief"))) \
            or not os.path.isfile(os.path.join(D, str(n.get("brief")))) or not okf:
        bad("m5 next")
    else:
        print("M5 flags", flags)
elif action == "stop":
    if n.get("reason") not in ("no_justified_test", "needs_owner", "contract_gap", "limits") or set(n) != {"action", "reason"}:
        bad("stop reason")
    else:
        print("STOP", n["reason"])


if s and "stop_reason" in s and (s["stop_reason"] == "none") != (action != "stop"):
    bad("stop_reason inconsistent with action")
if action == "stop" and s and "stop_reason" in s and isinstance(n, dict) and n.get("reason") != s["stop_reason"]:
    bad("stop reason differs from status")


def preds(path):
    try:
        items = json.load(open(path))["items"]
        assert all(re.fullmatch(r"Q([1-9]|1\d|20)", i["id"]) and 0 <= float(i["p"]) <= 1 and set(i) == {"id", "p"} for i in items)
        assert len({i["id"] for i in items}) == len(items)
        return {i["id"]: float(i["p"]) for i in items}
    except Exception:
        return None


P = preds(os.path.join(D, "predictions.json"))
if P is None:
    bad("predictions.json")
else:
    k = len(P)
    bucket = "none" if k == 0 else "1_to_5" if k <= 5 else "6_to_10" if k <= 10 else "11_to_20"
    print("predictions", k, "p values", sorted(round(v, 2) for v in P.values()))
    if s and s.get("prediction_count") != bucket:
        bad("prediction count differs from status")

prev = f"s{int(step[1:]) - 1:02d}"
if step != "s01":
    PP = preds(f"{X}/science/{prev}/predictions.json") or {}
    try:
        O = {i["id"]: i["outcome"] for i in json.load(open(os.path.join(D, "outcomes.json")))["items"]}
        assert set(O) == set(PP) and all(v in (True, False, None) for v in O.values())
        scored = [(PP[i], O[i]) for i in PP if O[i] is not None]
        brier = sum((p - (1 if o else 0)) ** 2 for p, o in scored) / len(scored) if scored else None
        print("PREVIOUS", prev, "predictions", len(PP), "resolved", len(scored), "true", sum(1 for _, o in scored if o),
              "mean_brier", None if brier is None else round(brier, 3))
    except Exception:
        bad("outcomes.json")

print("VALID" if ok_all else "NOT_VALID")
r = subprocess.run(["python3", f"{B}/blind_commit.py", nn, f"science/{step}", f"science step {step}, scientific agent outputs"],
                   capture_output=True, text=True)
print(r.stdout.strip() or "commit: no output", ("commit stderr lines " + str(len(r.stderr.splitlines()))) if r.returncode else "")
