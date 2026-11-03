"""Validate a science step's SHAPES.json (per-comparison shape and contract fixes from fixed lists; no free text) against
FINAL.json's comparison ids. Prints the codes only when the file passes; otherwise the failed checks.
Usage: python3 ~/.cache/blind01/sci_shapes_check.py <NN> <sNN> <FINAL step sNN>
"""
import json, sys

S = f"/home/hal/dev/interp/metis/experiments/blind-{sys.argv[1]}/science"
ids = [c["id"] for c in json.load(open(f"{S}/{sys.argv[3]}/FINAL.json"))["comparisons"]]
SH = {"metric_origin": {"adapter_scalar", "sealed_extraction", "cross_arm_outputs", "trusted_wall", "derived", "other"},
      "comparator": {"none", "exact", "elementwise_abs", "elementwise_rel", "elementwise_abs_plus_rel", "set_or_ranking", "other"},
      "decision_unit": {"pooled_mean", "per_input_all", "per_input_each", "worst_input", "other"},
      "pairing": {"paired_replicate", "unpaired", "deterministic", "other"},
      "interval": {"all_pairs", "sign_test", "t_interval", "bootstrap", "none", "other"},
      "margin_form": {"abs", "rel", "abs_plus_rel", "none"}, "rel_base": {"none", "against_value", "reference", "per_element", "other"},
      "reference_origin": {"none", "design_constant", "published", "previous_run", "baseline_arm", "other"},
      "ratio_form": {"none", "median_of_ratios", "ratio_of_medians", "ratio_of_means", "other"}}
FX = {"inputs": {"as_drafted", "one_input_per_invocation", "inputs_differ_by_arm", "other"},
      "budget": {"as_drafted", "design_sets_budget", "split_into_runs", "other"},
      "compute": {"as_drafted", "per_invocation_rows", "exclude_overhead", "software_versions", "cpu_identity", "other"},
      "leaks": {"as_drafted", "adapter_no_metrics", "separate_adapter_authors", "view_text_screened", "other"}}
f = json.load(open(f"{S}/{sys.argv[2]}/SHAPES.json"))
why = []
if not isinstance(f, dict) or set(f) != {"comparisons", "fixes"}:
    print("SHAPES INVALID ['keys']"); print("SHAPES_NOT_VALID"); sys.exit()
cs, fx = f["comparisons"], f["fixes"]
if not isinstance(cs, list) or [c.get("id") if isinstance(c, dict) else None for c in cs] != ids:
    why.append("ids"); cs = []
for c in cs:
    if set(c) != {"id"} | set(SH) or any(c[k] not in v for k, v in SH.items()) or ((c["comparator"] == "none") != (c["metric_origin"] != "cross_arm_outputs")):
        why.append(c["id"])
if not (isinstance(fx, dict) and set(fx) == set(FX) and all(isinstance(fx[k], list) and fx[k] and len(set(map(str, fx[k]))) == len(fx[k])
                                                          and set(fx[k]) <= FX[k] for k in FX)):
    why.append("fixes")
if why:
    print("SHAPES INVALID", why)
else:
    for c in cs:
        print(c["id"], " ".join(f"{k} {c[k]}" for k in SH))
    for k in FX:
        print(f"fix {k}: {'+'.join(fx[k])}")
print("SHAPES_NOT_VALID" if why else "SHAPES_VALID")
