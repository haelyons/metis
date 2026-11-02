"""Create args.json for a new m5 run of a blind experiment (blind-01, blind-02, ...) from that experiment's
run1, changing only run_root and tag (and, with --addendum, the
brief: a reader agent's BRIEF_run5.md, in intake_check/ or, with --addendum=intake_check_codex, there). Prints nothing else.

--harness-from=<folder> reuses the harness in that folder of blind-01/m5/ (args.harness_from; it must hold setup.sh,
run_anchors.sh and run_command.sh). --stop-after-profile stubs seal as SKIPPED (the pipeline's existing stub input),
so every later stage is skipped and takeaways still runs. --units-check=<run> sets args.units_check (U51) with that
earlier run's recorded baseline outputs (<run>/agent/results/reproduce/out) as the reference. --units-probe=<run> sets
args.units_probe (U52, standalone unit probe) with the same reference.

A new experiment's run1 has no run1 to copy: it gets run1's keys (blind true, record_raid true) with the brief
<experiment>/m5/BRIEF.md, which must exist and differ from the template the operator wrote
(~/.cache/blind01/brief_template_<experiment>.sha256); the brief is checked by size and hash only, never read.

Usage: python3 ~/.cache/blind01/new_run.py <run_root> [--addendum[=intake_check_codex|=intake_acquire|=intake_mirror]]
           [--harness-from=<folder>] [--stop-after-profile] [--units-check=<run> | --units-probe=<run>]
"""
import hashlib, json, os, re, sys

root = os.path.abspath(sys.argv[1])
options = sys.argv[2:]
addenda = {"--addendum": "intake_check", "--addendum=intake_check_codex": "intake_check_codex",
           "--addendum=intake_acquire": "intake_acquire", "--addendum=intake_mirror": "intake_mirror"}
harness = [o.split("=", 1)[1] for o in options if o.startswith("--harness-from=")]
check = [o.split("=", 1)[1] for o in options if o.startswith("--units-check=")]
probe = [o.split("=", 1)[1] for o in options if o.startswith("--units-probe=")]
stop = "--stop-after-profile" in options
assert len(options) == len(set(options)) and all(o in addenda or o.startswith("--harness-from=") or o.startswith("--units-check=") or o.startswith("--units-probe=") or o == "--stop-after-profile"
                                                  for o in options), "unknown option"
assert sum(o in addenda for o in options) <= 1 and len(harness) <= 1 and len(check) + len(probe) <= 1, "repeated option"
assert all(re.fullmatch(r"run\d+", c) for c in check + probe), "units check reference must be a run folder name"
assert all(re.fullmatch(r"[A-Za-z0-9_]+", h) for h in harness), "harness folder must be a plain folder name"
addendum = next((addenda[o] for o in options if o in addenda), None)
m = re.fullmatch(r"(/home/hal/dev/interp/metis/experiments/blind-(\d\d)/m5)/run(\d+)", root)
assert m and not os.path.exists(root), "need a new blind m5 run root"
if os.path.exists(m.group(1) + "/run1/args.json"):
    args = json.load(open(m.group(1) + "/run1/args.json"))
else:
    assert m.group(3) == "1", "a new experiment starts at run1"
    brief = m.group(1) + "/BRIEF.md"
    template = open(os.path.expanduser("~/.cache/blind01/brief_template_blind-" + m.group(2) + ".sha256")).read().strip()
    assert os.path.isfile(brief) and os.path.getsize(brief) > 0, "no brief"
    assert hashlib.sha256(open(brief, "rb").read()).hexdigest() != template, "brief is still the template"
    args = {"run_root": None, "brief": brief, "tag": None, "blind": True, "record_raid": True}
args["run_root"], args["tag"] = root, "b" + m.group(2) + "m5r" + m.group(3)
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
if probe:
    args["units_probe"] = {"reference": m.group(1) + "/" + probe[0] + "/agent/results/reproduce/out"}
    assert os.path.isdir(args["units_probe"]["reference"]), "no recorded baseline outputs in that run"
if stop:
    args["stub"] = {"seal": "SKIPPED"}
os.makedirs(root)
json.dump(args, open(root + "/args.json", "w"), indent=2)
print("created", "run" + m.group(3), sorted(args), "addendum brief" if addendum else "original brief",
      "harness reused" if harness else "fresh harness", "stops after profile" if stop else "units check" if check else "units probe" if probe else "full chain")
