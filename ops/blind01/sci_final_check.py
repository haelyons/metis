"""Validate a science step's FINAL.json (requirements of the final experiments in a fixed vocabulary; no free text).
Prints the arms, comparisons, compute facts and design codes only when the file passes; otherwise the failed checks.
Usage: python3 ~/.cache/blind01/sci_final_check.py <NN> <sNN> <parts step sNN>
"""
import json, sys

S = f"/home/hal/dev/interp/metis/experiments/blind-{sys.argv[1]}/science"
f = json.load(open(f"{S}/{sys.argv[2]}/FINAL.json"))
parts = {p["id"] for p in json.load(open(f"{S}/{sys.argv[3]}/PARTS.json"))["items"]}
ARM = {"role": {"baseline", "variant"}, "axis": {"none", "configuration", "implementation", "input_case", "hardware"},
       "needs_new_code": {"yes", "no"}, "published": {"yes", "no"}}
CMP = {"metric": {"runtime", "throughput", "result_agreement", "quality", "cost", "memory"},
       "criterion": {"equivalence", "non_inferiority", "superiority", "error_vs_reference", "ratio_at_least"},
       "direction": {"higher_better", "lower_better", "two_sided"}, "margin_form": {"abs", "rel", "none"},
       "margin_source": {"question", "published", "design_choice", "unknown"}, "stochastic": {"yes", "no"},
       "replicates": {"one", "two_to_five", "six_to_ten", "over_ten"}}
FACTS = {"per_arm_wall", "per_arm_gpu_s", "gpu_memory", "cpu_utilisation", "energy", "hardware_identity", "usd"}
DES = {"same_box": {"yes", "no"}, "inputs": {"one", "two_to_five", "six_or_more"}, "order": {"interleaved", "blocked", "any"},
       "who_seals": {"science_step", "m5_seal_agent", "either"}, "margin_owner_input": {"yes", "no"},
       "arms_need_implement": {"none", "some", "all"}}
why = []
if not isinstance(f, dict) or set(f) != {"arms", "comparisons", "compute_facts", "design"}:
    print("FINAL INVALID ['keys']"); print("FINAL_NOT_VALID"); sys.exit()
arms, cmps, facts, des = f["arms"], f["comparisons"], f["compute_facts"], f["design"]
if not (isinstance(arms, list) and 2 <= len(arms) <= 5):
    why.append("arms count"); arms = []
for n, a in enumerate(arms):
    if not (isinstance(a, dict) and set(a) == {"id"} | set(ARM) and a["id"] == f"A{n}" and all(a[k] in v for k, v in ARM.items())
            and (a["role"] == "baseline") == (n == 0) and (a["axis"] == "none") == (n == 0)):
        why.append(f"A{n}")
ids = {a.get("id") for a in arms if isinstance(a, dict)}
if not (isinstance(cmps, list) and 1 <= len(cmps) <= 8):
    why.append("comparisons count"); cmps = []
for n, c in enumerate(cmps, 1):
    ok = (isinstance(c, dict) and set(c) == {"id", "arm", "against", "parts"} | set(CMP) and c["id"] == f"K{n}"
          and all(c[k] in v for k, v in CMP.items()) and c["arm"] in ids - {"A0"} and c["against"] in (ids | {"reference"}) - {c["arm"]}
          and isinstance(c["parts"], list) and c["parts"] and len(set(map(str, c["parts"]))) == len(c["parts"]) and set(c["parts"]) <= parts)
    if not ok:
        why.append(f"K{n}")
if not (isinstance(facts, list) and len(set(map(str, facts))) == len(facts) and set(facts) <= FACTS):
    why.append("compute_facts")
if not (isinstance(des, dict) and set(des) == set(DES) and all(des[k] in v for k, v in DES.items())):
    why.append("design")
if why:
    print("FINAL INVALID", why)
else:
    for a in arms:
        print(f"{a['id']} {a['role']} axis {a['axis']} new_code {a['needs_new_code']} published {a['published']}")
    for c in cmps:
        print(f"{c['id']} {c['arm']} vs {c['against']}: {c['metric']} {c['criterion']} {c['direction']} margin {c['margin_form']}/{c['margin_source']} "
              f"stochastic {c['stochastic']} replicates {c['replicates']} parts {','.join(c['parts'])}")
    print("compute_facts", "+".join(facts) or "none")
    print("design", " ".join(f"{k} {v}" for k, v in des.items()))
print("FINAL_NOT_VALID" if why else "FINAL_VALID")
