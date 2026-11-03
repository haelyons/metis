"""Validate a science step's PARTS.json and REQS.json against the gap register of a given step (fixed vocabulary, no
free text). Prints the part states and the requirement register only when every item passes; a failing item prints
its id and the failed check, never its values.
Usage: python3 ~/.cache/blind01/sci_reqs_check.py <NN> <sNN> <gaps step sNN>
"""
import json, sys

M = "/home/hal/dev/interp/metis"
S = f"{M}/experiments/blind-{sys.argv[1]}/science"
D, G = f"{S}/{sys.argv[2]}", f"{S}/{sys.argv[3]}"
FIELDS = {"name", "unit", "basis", "value", "differs_in", "measured_by", "phase", "line", "k_budget",
          "cum_spend_through_measured_by", "anchor", "predictions", "measured_value"}
BETWEEN = {"arm_vs_baseline", "arm_vs_arm", "arm_vs_published", "mixed"}
REQ = {"comparison_arms": {"arms": {"two", "three_to_four", "five_or_more"},
                           "arm_axis": {"configuration", "implementation", "input_case", "hardware", "mixed"},
                           "outcome": {"runtime", "throughput", "result_agreement", "quality", "cost", "mixed"},
                           "arms_from_menu": {"all", "some", "none"}, "sealable": {"yes", "no"}},
       "record_carryover": {"fields": None, "direction": {"card_to_run", "run_to_card", "both"}},
       "tolerance_equivalence": {"criterion": {"equivalence_margin", "non_inferiority", "absolute_error", "relative_error",
                                               "distribution", "mixed"}, "between": BETWEEN,
                                 "margin_source": {"question", "published", "design_choice", "unknown"},
                                 "replicates": {"one", "two_to_five", "six_or_more"}},
       "route_execution": {"needed": {"yes", "no"}},
       "agent_access": {"missing": {"brief", "data", "prior_run_outputs", "network", "mixed"},
                        "roles": {"intake", "harness", "authoring_roles", "all_claude_roles"},
                        "wrapper_fix": {"sufficient", "partial", "insufficient"}},
       "other": {"fact": {"per_arm_wall", "per_arm_gpu_s", "gpu_memory", "cpu_utilisation", "energy",
                          "hardware_identity", "mixed"}, "per": {"run", "stage", "arm"}},
       "quality_metric": {"metric": {"scalar_score", "error_vs_reference", "pass_rate", "mixed"}, "between": BETWEEN}}
STATUS = {"measured", "negative", "narrowed", "open_calibration", "open_final", "open_no_mechanism"}

gaps = json.load(open(f"{G}/GAPS.json"))["items"]
kind = {g["id"]: g["kind"] for g in gaps}
ok, out = True, []

def bad(i, why):
    global ok
    ok = False
    print(f"{i} INVALID", why)

parts = json.load(open(f"{D}/PARTS.json"))["items"]
if not isinstance(parts, list) or not 1 <= len(parts) <= 12:
    bad("PARTS", "count")
    parts = []
for n, p in enumerate(parts, 1):
    why = [k for k, c in (("keys", set(p) != {"id", "status", "gaps"}), ("id", p.get("id") != f"P{n}"),
                          ("status", p.get("status") not in STATUS),
                          ("gaps", not (isinstance(p.get("gaps"), list) and len(set(map(str, p["gaps"]))) == len(p["gaps"])
                                        and set(p["gaps"]) <= set(kind)))) if c]
    if why:
        bad(f"P{n}", why)
    else:
        out.append(f"P{n} {p['status']} gaps {','.join(p['gaps']) or 'none'}")

reqs = json.load(open(f"{D}/REQS.json"))["items"]
if not isinstance(reqs, list) or [r.get("id") for r in reqs] != [g["id"] for g in gaps]:
    bad("REQS", "ids")
    reqs = []
orders = [r.get("order") for r in reqs]
if reqs and sorted(o for o in orders if type(o) is int) != list(range(1, len(gaps) + 1)):
    bad("REQS", "order")
for r in reqs:
    spec, q = REQ.get(kind[r["id"]], {}), r.get("req")
    why = []
    if set(r) != {"id", "order", "defer", "req"}:
        why.append("keys")
    if type(r.get("defer")) is not bool:
        why.append("defer")
    if not isinstance(q, dict) or set(q) != set(spec):
        why.append("req keys")
    else:
        for k, allowed in spec.items():
            v = q[k]
            if allowed is None:
                if not (isinstance(v, list) and v and len(set(map(str, v))) == len(v) and set(v) <= FIELDS):
                    why.append(k)
            elif v not in allowed:
                why.append(k)
    if why:
        bad(r["id"], why)
    else:
        vals = ", ".join(f"{k} {'+'.join(v) if isinstance(v, list) else v}" for k, v in q.items())
        out.append(f"{r['id']} order {r['order']} defer {str(r['defer']).lower()} | {kind[r['id']]}: {vals}")
if ok:
    print("\n".join(out))
print("REQS_VALID" if ok else "REQS_NOT_VALID")
