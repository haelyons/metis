"""Structure of a science step's calibration brief, as booleans and counts: starts with the seed's exact bytes,
carries the materials addendum section unchanged, has the calibration heading. Never prints brief text."""
import json, sys
X = f"/home/hal/dev/interp/metis/experiments/blind-{sys.argv[1]}"
step = f"{X}/science/{sys.argv[2]}"
nxt = json.load(open(f"{step}/NEXT.json"))
brief = open(f"{step}/{nxt['brief']}", "rb").read()
seed = open(f"{X}/m5/BRIEF.md", "rb").read()
add = open(f"{X}/m5/b01_materials/BRIEF_run1.md", "rb").read()
section = add[len(seed):] if add.startswith(seed) else None
head = f"## Calibration request (science step {sys.argv[2]})".encode()
print("starts_with_seed", brief.startswith(seed), "addendum_prefix_is_seed", section is not None,
      "addendum_section_verbatim", bool(section) and section.strip() in brief,
      "calibration_heading", brief.count(head), "brief_bytes", len(brief), "extra_after_seed_and_addendum_bytes",
      len(brief) - len(seed) - (len(section) if section else 0))
