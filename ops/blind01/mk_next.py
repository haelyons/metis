"""Derive the next calibration-assessment step brief from the previous one: sci_sPP.md -> sci_sNN.md (run R).
Usage: python3 mk_next.py <PP> <NN> <run number>"""
import os, re, shutil, sys
os.chdir(os.path.expanduser("~/.cache/blind01"))
pp, nn, run = sys.argv[1], sys.argv[2], sys.argv[3]
prev, cur = f"s{pp}", f"s{nn}"
s = open(f"sci_{prev}.md").read()
i = s.index("Operator metadata on it:"); j = s.index("\n\nAnswer in `ASSESSMENT.md`")
s = s[:i] + "Operator metadata on it: @RUN_META@" + s[j:]
s = re.sub(r"## Step s\d\d \([^)]*\)", f"## Step {cur} (after the calibration run {'run' + run}; no network)", s, count=1)
s = re.sub(r"science/s\d\d/`\. Read `science/s01/` to `science/s\d\d/` first\. The calibration run s\d\d chose is `experiments/blind-02/m5/run\d+/` \(brief `science/s\d\d/`",
           f"science/{cur}/`. Read `science/s01/` to `science/{prev}/` first. The calibration run {prev} chose is `experiments/blind-02/m5/run{run}/` (brief `science/{prev}/`", s, count=1)
s = s.replace("the earlier attempt, run3, failed at intake;", "earlier calibration runs: run3 (failed at intake), run4 (s03's) and later ones named in the earlier steps;")
for a in ("the quantity s", "with s", "the decision rule s"):
    s = re.sub(re.escape(a) + r"\d\d", a + pp, s)
s = re.sub(r"`## Calibration request \(science step s\d\d\)`", f"`## Calibration request (science step {cur})`", s)
open(f"sci_{cur}.md", "w").write(s)
shutil.copy(f"sci_{prev}.enums.json", f"sci_{cur}.enums.json")
for line in s.splitlines():
    if re.search(r"s\d\d|run\d", line):
        print(line[:170])
