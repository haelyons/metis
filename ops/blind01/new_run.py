"""Create args.json for a new blind-01 m5 run from run1's, changing only run_root and tag (and, with --addendum, the
brief: a reader agent's BRIEF_run5.md, in intake_check/ or, with --addendum=intake_check_codex, there). Prints nothing else.

--harness-from=<folder> reuses the harness in that folder of blind-01/m5/ (args.harness_from; it must hold setup.sh,
run_anchors.sh and run_command.sh). --stop-after-profile stubs seal as SKIPPED (the pipeline's existing stub input),
so every later stage is skipped and takeaways still runs. --units-check=<run> sets args.units_check (U51) with that
earlier run's recorded baseline outputs (<run>/agent/results/reproduce/out) as the reference.

Usage: python3 ~/.cache/blind01/new_run.py <run_root> [--addendum[=intake_check_codex|=intake_acquire|=intake_mirror]]
           [--harness-from=<folder>] [--stop-after-profile] [--units-check=<run>]
"""
import json, os, re, sys

root = os.path.abspath(sys.argv[1])
options = sys.argv[2:]
addenda = {"--addendum": "intake_check", "--addendum=intake_check_codex": "intake_check_codex",
           "--addendum=intake_acquire": "intake_acquire", "--addendum=intake_mirror": "intake_mirror"}
harness = [o.split("=", 1)[1] for o in options if o.startswith("--harness-from=")]
check = [o.split("=", 1)[1] for o in options if o.startswith("--units-check=")]
stop = "--stop-after-profile" in options
assert len(options) == len(set(options)) and all(o in addenda or o.startswith("--harness-from=") or o.startswith("--units-check=") or o == "--stop-after-profile"
                                                  for o in options), "unknown option"
assert sum(o in addenda for o in options) <= 1 and len(harness) <= 1 and len(check) <= 1, "repeated option"
assert all(re.fullmatch(r"run\d+", c) for c in check), "units check reference must be a run folder name"
assert all(re.fullmatch(r"[A-Za-z0-9_]+", h) for h in harness), "harness folder must be a plain folder name"
addendum = next((addenda[o] for o in options if o in addenda), None)
m = re.fullmatch(r"(/home/hal/dev/interp/metis/experiments/blind-01/m5)/run(\d+)", root)
assert m and not os.path.exists(root), "need a new blind-01 m5 run root"
args = json.load(open(m.group(1) + "/run1/args.json"))
args["run_root"], args["tag"] = root, "b01m5r" + m.group(2)
if addendum:
    args["brief"] = m.group(1) + "/" + addendum + "/BRIEF_run5.md"
    assert os.path.isfile(args["brief"]), "no addendum brief"
if harness:
    args["harness_from"] = m.group(1) + "/" + harness[0]
    assert all(os.path.isfile(os.path.join(args["harness_from"], n)) for n in ("setup.sh", "run_anchors.sh", "run_command.sh")), \
        "harness folder lacks a required script"
if check:
    args["units_check"] = {"reference": m.group(1) + "/" + check[0] + "/agent/results/reproduce/out"}
    assert os.path.isdir(args["units_check"]["reference"]), "no recorded baseline outputs in that run"
if stop:
    args["stub"] = {"seal": "SKIPPED"}
os.makedirs(root)
json.dump(args, open(root + "/args.json", "w"), indent=2)
print("created", "run" + m.group(2), sorted(args), "addendum brief" if addendum else "original brief",
      "harness reused" if harness else "fresh harness", "stops after profile" if stop else "units check" if check else "full chain")
