"""Validate a science step's GAPS.json: each file exists under dut/, each section occurs verbatim in it, the enums are
fixed values. Prints the register (repository paths, headings found in repository files, enums) only when every item
passes; a failing item prints its id and the failed check, never its text.
Usage: python3 ~/.cache/blind01/sci_gaps_check.py <NN> <sNN>
"""
import json, os, re, sys

M = "/home/hal/dev/interp/metis"
D = f"{M}/experiments/blind-{sys.argv[1]}/science/{sys.argv[2]}"
E = {"kind": {"comparison_arms", "quality_metric", "tolerance_equivalence", "route_execution", "record_carryover", "agent_access", "other"},
     "blocks": {"calibration", "final_experiment", "both"}, "parts_blocked": {"one", "two", "three_or_more"},
     "change_size": {"small", "medium", "large"}, "existing_workaround": {"none", "partial", "full"}}
items = json.load(open(f"{D}/GAPS.json"))["items"]
assert isinstance(items, list) and 1 <= len(items) <= 8
ok, rows = True, []
for n, g in enumerate(items, 1):
    why = []
    if set(g) != {"id", "file", "section"} | set(E):
        why.append("keys")
    if g.get("id") != f"G{n}":
        why.append("id")
    f = str(g.get("file", ""))
    p = os.path.normpath(os.path.join(M, f))
    if not (re.fullmatch(r"dut/[\w./-]+", f) and p.startswith(M + "/dut/") and os.path.isfile(p)):
        why.append("file")
    else:
        lines = [l.strip() for l in open(p, errors="replace")]
        sec = str(g.get("section", "")).strip()
        bare = [re.sub(r"^(#+|//+|#|\*|--)\s*", "", l) for l in lines]
        if not sec or len(sec) > 160 or sec not in bare:
            why.append("section")
    why += [k for k in E if g.get(k) not in E[k]]
    if why:
        ok = False
        print(f"G{n} INVALID", why)
    else:
        rows.append(g)
if ok:
    for g in rows:
        print(f"{g['id']} {g['file']} :: {g['section']} | kind {g['kind']}, blocks {g['blocks']}, parts {g['parts_blocked']}, "
              f"change {g['change_size']}, workaround {g['existing_workaround']}")
print("GAPS_VALID" if ok else "GAPS_NOT_VALID")
