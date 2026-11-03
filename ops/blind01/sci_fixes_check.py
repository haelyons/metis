"""Validate a science step's FIXES.json (fixes chosen from a fixed list for one contract check; no free text). Prints the
chosen codes only when the file passes; otherwise the failed item and check, never its values.
Usage: python3 ~/.cache/blind01/sci_fixes_check.py <NN> <sNN>
"""
import json, sys

D = f"/home/hal/dev/interp/metis/experiments/blind-{sys.argv[1]}/science/{sys.argv[2]}"
SPEC = [("predictions", {"seal_record_before_box", "return_in_scored", "judge_decision_rule", "hide_from_agents", "other"}),
        ("band_rule_unfit", {"sign_aware", "absolute_band_field", "bounded_range", "gate_decides", "noise_band", "other"}),
        ("write_back_unfit", {"as_plan_numbers", "rejudge_card", "all_runs_not_latest", "record_run_identity", "states_unfit", "other"}),
        ("leaks_or_biases", {"hide_value", "hide_predictions", "hide_anchor_value", "extraction_rule_before_run", "other"})]
f = json.load(open(f"{D}/FIXES.json"))
items = f.get("items") if isinstance(f, dict) and set(f) == {"items"} else None
ok = isinstance(items, list) and len(items) == len(SPEC)
if not ok:
    print("FIXES INVALID ['items']")
else:
    for (name, codes), it in zip(SPEC, items):
        fx = it.get("fix") if isinstance(it, dict) else None
        if not (isinstance(it, dict) and set(it) == {"for", "fix"} and it["for"] == name and isinstance(fx, list) and fx
                and len(set(map(str, fx))) == len(fx) and set(fx) <= codes):
            ok = False
            print(f"{name} INVALID")
    if ok:
        for name, it in zip((n for n, _ in SPEC), items):
            print(f"{name}: {'+'.join(it['fix'])}")
print("FIXES_VALID" if ok else "FIXES_NOT_VALID")
