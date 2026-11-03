"""Validate a science step's CHECK.json for the final-experiment contract (G1, G3, G6) against FINAL.json's ids; fixed
vocabulary, no free text. Prints the verdict and codes only when the file passes; otherwise the failed checks.
Usage: python3 ~/.cache/blind01/sci_check_final.py <NN> <sNN> <FINAL step sNN>
"""
import json, sys

S = f"/home/hal/dev/interp/metis/experiments/blind-{sys.argv[1]}/science"
f = json.load(open(f"{S}/{sys.argv[3]}/FINAL.json"))
ids = {a["id"] for a in f["arms"]} | {c["id"] for c in f["comparisons"]} | {"compute_facts"}
PROBLEMS = {"arm_not_runnable", "metric_not_capturable", "criterion_unfit", "statistic_unfit", "margin_rule_unfit", "reference_unfit",
            "order_unfit", "inputs_unfit", "budget_unfit", "compute_unfit", "leaks_or_biases", "sealing_unfit", "other"}
c = json.load(open(f"{S}/{sys.argv[2]}/CHECK.json"))
uniq = lambda v: isinstance(v, list) and len(set(map(str, v))) == len(v)
why = [k for k, bad in (("keys", not isinstance(c, dict) or set(c) != {"gaps", "verdict", "missing", "problems"}),
                        ("gaps", c.get("gaps") != "G1+G3+G6"),
                        ("verdict", c.get("verdict") not in ("sufficient", "partial", "insufficient")),
                        ("missing", not (uniq(c.get("missing")) and set(c["missing"]) <= ids)),
                        ("problems", not (uniq(c.get("problems")) and set(c["problems"]) <= PROBLEMS))) if bad]
if why:
    print("CHECK INVALID", why)
else:
    print(f"{c['gaps']} verdict {c['verdict']} | missing {'+'.join(c['missing']) or 'none'} | problems {'+'.join(c['problems']) or 'none'}")
print("CHECK_NOT_VALID" if why else "CHECK_VALID")
