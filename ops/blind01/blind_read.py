"""Blind-safe metadata reader for one blind-01 run. Prints only allowlisted fields.

Usage: python3 ~/.cache/blind01/blind_read.py <run_root>
Prints: signature rows (numbers, booleans, pipeline enums), OPERATOR_TAKEAWAY.md,
receipts (rc, timed_out, wall_s, budget_s, overrun, fetched), box.json (type, price,
region, start), the raid name and the tail of the launcher log. Nothing else.
"""
import json, os, re, sys

ROOT = os.path.abspath(sys.argv[1])
assert re.search(r"/experiments/blind-01/m5/run\d+$", ROOT), "not a blind-01 run root"
SIG_KEYS = ("stage", "n", "status", "exit_code", "exit_kind", "error_class", "depth", "wall_s",
            "gpu_s", "usd", "tokens_in", "tokens_out", "model_family", "blockers", "run_valid",
            "calibration_valid")
ENUM_FACTS = {"data": {"available", "partial", "unavailable", "unknown"},
              "licence": {"permitted", "restricted", "unknown"},
              "licence_basis": {"unreachable", "none", "owner", "distribution", "explicit"},
              "size": {"tiny", "small", "medium", "large", "unknown"},
              "outcome": {"approved", "no_feasible_method", "rejected"}}
BLOCKERS = {"data_unavailable", "licence", "env_irreproducible", "files_local_only", "compute_cap",
            "capacity", "none"}


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def safe(value):
    return value is None or isinstance(value, (bool, int, float))


print("== signatures")
try:
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "operator", "signatures.jsonl")) if l.strip()]
except FileNotFoundError:
    rows = []
for r in rows:
    s = r.get("signature", {})
    out = {}
    for k in SIG_KEYS:
        v = s.get(k)
        if k == "blockers":
            v = [b if b in BLOCKERS else "<other>" for b in (v or [])]
        elif k in ("stage", "status", "exit_kind", "error_class", "model_family"):
            v = v if isinstance(v, str) and re.fullmatch(r"[a-z_A-Z]{1,24}", v) else "<other>"
        elif not safe(v):
            v = "<other>"
        out[k] = v
    facts = {}
    for k, v in (r.get("facts") or {}).items():
        if not re.fullmatch(r"[a-z_]{1,32}", k):
            continue
        if safe(v):
            facts[k] = v
        elif k in ENUM_FACTS:
            facts[k] = v if v in ENUM_FACTS[k] else "<other>"
    print(out)
    print("  facts", facts)

print("== takeaway")
try:
    print(open(os.path.join(ROOT, "operator", "OPERATOR_TAKEAWAY.md")).read().rstrip())
except FileNotFoundError:
    print("(none)")

print("== receipts")
rdir = os.path.join(ROOT, "control", "receipts")
for name in sorted(os.listdir(rdir)) if os.path.isdir(rdir) else []:
    op = name[:-5] if name.endswith(".json") else name
    label = op if re.fullmatch(r"\d{4}-[a-z-]{1,32}", op) else "<other>"
    r = load(os.path.join(rdir, name)) or {}
    print(label, {k: r.get(k) for k in ("rc", "timed_out", "wall_s", "budget_s", "overrun", "fetched") if safe(r.get(k))})

print("== box")
b = load(os.path.join(ROOT, "control", "box.json")) or {}
print({k: b.get(k) for k in ("type", "price_usd_h", "region", "started_utc")
       if isinstance(b.get(k), (int, float)) or (isinstance(b.get(k), str) and re.fullmatch(r"[\w.:-]{1,40}", b.get(k)))})
raid = load(os.path.join(ROOT, "control", "raid.json")) or {}
print("raid", raid.get("raid") if isinstance(raid.get("raid"), str) and re.fullmatch(r"[a-z]{1,24}", raid.get("raid")) else None)

print("== launcher log (tail)")
try:
    print("".join(open(os.path.join(ROOT, "devbox_up.log")).readlines()[-4:]).rstrip())
except FileNotFoundError:
    print("(none)")
