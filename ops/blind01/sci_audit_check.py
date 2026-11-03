"""Validate a science step's AUDIT.json (seed-content audit and sufficiency of a drafted contract; fixed vocabulary, no free
text) against FINAL.json's ids. Prints the codes only when the file passes; DRAFT_CLEAN only when no seed content was found.
Usage: python3 ~/.cache/blind01/sci_audit_check.py <NN> <audit step sNN> <FINAL step sNN>
"""
import json, sys

S = f"/home/hal/dev/interp/metis/experiments/blind-{sys.argv[1]}/science"
f = json.load(open(f"{S}/{sys.argv[3]}/FINAL.json"))
ids = {a["id"] for a in f["arms"]} | {c["id"] for c in f["comparisons"]} | {"compute_facts"}
PROBLEMS = {"arm_not_runnable", "metric_not_capturable", "criterion_unfit", "statistic_unfit", "margin_rule_unfit", "reference_unfit",
            "order_unfit", "inputs_unfit", "budget_unfit", "compute_unfit", "leaks_or_biases", "sealing_unfit", "other"}
CODES = {"program_or_library_name", "dataset_case_or_input_name", "file_path_or_output_name", "numbers_or_values", "quoted_text",
         "inferable_question_or_finding", "other"}
a = json.load(open(f"{S}/{sys.argv[2]}/AUDIT.json"))
uniq = lambda v: isinstance(v, list) and len(set(map(str, v))) == len(v)
why = [k for k, bad in (("keys", not isinstance(a, dict) or set(a) != {"seed_content", "codes", "verdict", "missing", "problems"}),
                        ("seed_content", a.get("seed_content") not in ("none", "some")),
                        ("codes", not (uniq(a.get("codes")) and set(a["codes"]) <= CODES and (not a["codes"]) == (a.get("seed_content") == "none"))),
                        ("verdict", a.get("verdict") not in ("sufficient", "partial", "insufficient")),
                        ("missing", not (uniq(a.get("missing")) and set(a["missing"]) <= ids)),
                        ("problems", not (uniq(a.get("problems")) and set(a["problems"]) <= PROBLEMS))) if bad]
if why:
    print("AUDIT INVALID", why)
else:
    print(f"seed_content {a['seed_content']} {'+'.join(a['codes']) or ''} | verdict {a['verdict']} | missing {'+'.join(a['missing']) or 'none'} | "
          f"problems {'+'.join(a['problems']) or 'none'}")
print("AUDIT_NOT_VALID" if why else ("DRAFT_CLEAN" if a["seed_content"] == "none" else "DRAFT_HAS_SEED_CONTENT"))
