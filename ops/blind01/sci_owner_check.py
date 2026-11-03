"""Validate a science step's OWNER.json (decisions the owner must make, fixed vocabulary, no free text) and print them.
Usage: python3 ~/.cache/blind01/sci_owner_check.py <NN> <sNN>
"""
import json, sys

D = f"/home/hal/dev/interp/metis/experiments/blind-{sys.argv[1]}/science/{sys.argv[2]}"
CODES = {"margins", "thresholds_or_references", "evaluator_private_data", "arm_selection", "replicates_or_budget", "split_runs",
         "spend_above_20", "other"}
o = json.load(open(f"{D}/OWNER.json"))
d = o.get("decisions") if isinstance(o, dict) and set(o) == {"decisions"} else None
ok = isinstance(d, list) and len(set(map(str, d))) == len(d) and set(d) <= CODES
print(f"owner decisions: {'+'.join(d) or 'none'}" if ok else "OWNER INVALID")
print("OWNER_VALID" if ok else "OWNER_NOT_VALID")
