"""Create args.json for a new blind-01 m5 run from run1's, changing only run_root and tag (and, with --addendum, the
brief: a reader agent's BRIEF_run5.md, in intake_check/ or, with --addendum=intake_check_codex, there). Prints nothing else.

Usage: python3 ~/.cache/blind01/new_run.py <run_root> [--addendum[=intake_check_codex]]
"""
import json, os, re, sys

root = os.path.abspath(sys.argv[1])
assert sys.argv[2:] in ([], ["--addendum"], ["--addendum=intake_check_codex"], ["--addendum=intake_acquire"]), "unknown option"
addendum = {"--addendum": "intake_check", "--addendum=intake_check_codex": "intake_check_codex",
            "--addendum=intake_acquire": "intake_acquire"}.get((sys.argv[2:] or [""])[0])
m = re.fullmatch(r"(/home/hal/dev/interp/metis/experiments/blind-01/m5)/run(\d+)", root)
assert m and not os.path.exists(root), "need a new blind-01 m5 run root"
args = json.load(open(m.group(1) + "/run1/args.json"))
args["run_root"], args["tag"] = root, "b01m5r" + m.group(2)
if addendum:
    args["brief"] = m.group(1) + "/" + addendum + "/BRIEF_run5.md"
    assert os.path.isfile(args["brief"]), "no addendum brief"
os.makedirs(root)
json.dump(args, open(root + "/args.json", "w"), indent=2)
print("created", "run" + m.group(2), sorted(args), "addendum brief" if addendum else "original brief")
