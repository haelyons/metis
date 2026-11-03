"""Create args.json for a new m5 run of a blind experiment (blind-01, blind-02, ...) from that experiment's
run1, changing only run_root and tag (and, with --addendum, the
brief: a reader agent's BRIEF_run5.md, in intake_check/ or, with --addendum=intake_check_codex, there;
blind-02's --addendum=b01_materials uses b01_materials/BRIEF_run1.md). Prints nothing else.

--harness-from=<folder> reuses the harness in that folder of blind-01/m5/ (args.harness_from; it must hold setup.sh,
run_anchors.sh and run_command.sh). --stop-after-profile stubs seal as SKIPPED (the pipeline's existing stub input),
so every later stage is skipped and takeaways still runs; --stop-after-reproduce stubs profile the same way. --units-check=<run> sets args.units_check (U51) with that
earlier run's recorded baseline outputs (<run>/agent/results/reproduce/out) as the reference. --units-probe=<run> sets
args.units_probe (U52, standalone unit probe) with the same reference.

A new experiment's run1 has no run1 to copy: it gets run1's keys (blind true, record_raid true) with the brief
<experiment>/m5/BRIEF.md, which must exist and differ from the template the operator wrote
(~/.cache/blind01/brief_template_<experiment>.sha256); the brief is checked by size and hash only, never read.

--brief-from=sNN takes the brief a science step wrote (<experiment>/science/sNN/, the file its NEXT.json names, action
m5); the step folder must be committed unchanged, and the other options must equal NEXT.json's new_run_flags.
Such a run is a calibration: args.run_ceiling_s 19800, to be launched with retry53.sh (6 h box, USD 20 cap). The brief is
copied into <run_root>/brief/ and that folder is passed in args.add_dirs, so a Claude understudy can read it.

Usage: python3 ~/.cache/blind01/new_run.py <run_root> [--addendum[=intake_check_codex|=intake_acquire|=intake_mirror|=b01_materials] | --brief-from=sNN]
           [--harness-from=<folder>] [--stop-after-profile | --stop-after-reproduce] [--units-check=<run> | --units-probe=<run>]
"""
import hashlib, json, os, re, subprocess, sys

root = os.path.abspath(sys.argv[1])
options = sys.argv[2:]
addenda = {"--addendum": "intake_check", "--addendum=intake_check_codex": "intake_check_codex",
           "--addendum=intake_acquire": "intake_acquire", "--addendum=intake_mirror": "intake_mirror",
           "--addendum=b01_materials": "b01_materials"}
harness = [o.split("=", 1)[1] for o in options if o.startswith("--harness-from=")]
check = [o.split("=", 1)[1] for o in options if o.startswith("--units-check=")]
probe = [o.split("=", 1)[1] for o in options if o.startswith("--units-probe=")]
stop = "--stop-after-profile" in options
stop_r = "--stop-after-reproduce" in options
science = [o.split("=", 1)[1] for o in options if o.startswith("--brief-from=")]
assert len(options) == len(set(options)) and all(o in addenda or o.startswith("--harness-from=") or o.startswith("--units-check=") or o.startswith("--units-probe=")
                                                  or o in ("--stop-after-profile", "--stop-after-reproduce") or re.fullmatch(r"--brief-from=s\d\d", o)
                                                  for o in options), "unknown option"
assert sum(o in addenda for o in options) + len(science) <= 1 and len(harness) <= 1 and len(check) + len(probe) <= 1 and not (stop and stop_r), "repeated option"
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
    args["brief"] = m.group(1) + "/" + addendum + ("/BRIEF_run1.md" if addendum == "b01_materials" else "/BRIEF_run5.md")
    assert os.path.isfile(args["brief"]), "no addendum brief"
if science:
    step = m.group(1)[:-len("/m5")] + "/science/" + science[0]
    nxt = json.load(open(step + "/NEXT.json"))
    assert nxt.get("action") == "m5" and re.fullmatch(r"[\w.-]+\.md", nxt.get("brief", "")), "step did not choose an m5 run"
    assert sorted(nxt.get("new_run_flags", [])) == sorted(o for o in options if not o.startswith("--brief-from=")), "options differ from the step's"
    rel = os.path.relpath(step, "/home/hal/dev/interp/metis")
    git = lambda *a: subprocess.run(["git", "-C", "/home/hal/dev/interp/metis", *a], capture_output=True, text=True)
    assert git("ls-files", "--error-unmatch", "--", rel + "/" + nxt["brief"]).returncode == 0 and not git("status", "--porcelain", "--", rel).stdout, "step not committed"
    # A copy inside the run root, passed in args.add_dirs: the Claude understudy reads only its --add-dir folders
    # (idea/wf.js callModel), so a brief in science/ is unreadable to it (run5 intake, 2026-11-03).
    os.makedirs(root + "/brief")
    data = open(step + "/" + nxt["brief"], "rb").read()
    open(root + "/brief/" + nxt["brief"], "wb").write(data)
    args["brief"], args["add_dirs"] = root + "/brief/" + nxt["brief"], [root + "/brief"]
    args["run_ceiling_s"] = 19800   # calibration runs (retry53.sh): box budgets end inside its 6 h lifetime
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
if stop_r:
    args["stub"] = {"profile": "SKIPPED"}
os.makedirs(root, exist_ok=bool(science))
json.dump(args, open(root + "/args.json", "w"), indent=2)
print("created", "run" + m.group(3), sorted(args), "addendum brief" if addendum else "science step brief" if science else "original brief",
      "harness reused" if harness else "fresh harness", "stops after profile" if stop else "stops after reproduce" if stop_r else "units check" if check else "units probe" if probe else "full chain")
