"""Validate a science step's CHECK.json (content check of one operator contract against one gap; fixed vocabulary, no
free text). Prints the verdict and codes only when the file passes; otherwise the failed checks, never its values.
Usage: python3 ~/.cache/blind01/sci_check_contract.py <NN> <sNN> <gap id>
"""
import json, sys

D = f"/home/hal/dev/interp/metis/experiments/blind-{sys.argv[1]}/science/{sys.argv[2]}"
FIELDS = {"name", "unit", "basis", "value", "differs_in", "measured_by", "phase", "line", "k_budget",
          "cum_spend_through_measured_by", "anchor", "predictions", "measured_value"}
PROBLEMS = {"record_lacks_units", "band_rule_unfit", "wrong_stage", "protocol_not_runnable", "needs_several_runs",
            "anchor_rule_unfit", "write_back_unfit", "leaks_or_biases", "other"}
c = json.load(open(f"{D}/CHECK.json"))
uniq = lambda v: isinstance(v, list) and len(set(map(str, v))) == len(v)
why = [k for k, bad in (("keys", set(c) != {"gap", "verdict", "missing", "problems"}), ("gap", c.get("gap") != sys.argv[3]),
                        ("verdict", c.get("verdict") not in ("sufficient", "partial", "insufficient")),
                        ("missing", not (uniq(c.get("missing")) and set(c["missing"]) <= FIELDS)),
                        ("problems", not (uniq(c.get("problems")) and set(c["problems"]) <= PROBLEMS))) if bad]
if why:
    print("CHECK INVALID", why)
else:
    print(f"{c['gap']} verdict {c['verdict']} | missing {'+'.join(c['missing']) or 'none'} | problems {'+'.join(c['problems']) or 'none'}")
print("CHECK_NOT_VALID" if why else "CHECK_VALID")
