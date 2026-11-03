set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis
# Rebuild an earlier tree run's records with the current pipeline by --resume (U55): every agent call from the cache, no model
# call, the same cards; the records gain name, unit, band and judged. Prints only tree_resume_check.py's lines and the commit.
# Usage: bash ~/.cache/blind01/sci_tree_resume.sh <NN> <old stamp>-tree <science step sNN whose tree_args.json the old run used>
NN=$1; OLD=$2; S=$3
[[ $NN =~ ^[0-9][0-9]$ && $OLD =~ ^[0-9]{8}-[0-9]{4}-tree$ && $S =~ ^s[0-9][0-9]$ ]] || { echo USAGE; exit 2; }
X=$M/experiments/blind-$NN; A=$X/science/$S/tree_args.json
grep -q "judged" $M/dut/pipeline/src/main.js || { echo "U55_NOT_IN_MAIN"; exit 2; }
[ -f "$A" ] && [ -f "$X/$OLD/out/journal.jsonl" ] || { echo "MISSING_INPUT"; exit 2; }
# The tree's prompts carry the workflow's `base` (default <run folder>/work), so a resume from another run folder misses the
# cache from the first call that names it (2026-11-03: 44 of 45 calls rerun). Resume with the old run's base: the step's
# tree_args plus that base, in a private file (mode 600, removed after); a miss could then write in the old run's work
# folder, so its git state is checked and restored after the run.
mkdir -p -m 700 $B/private; RA=$B/private/resume_args_$NN.json
U0=$(cd $M && git ls-files -o -- "experiments/blind-$NN/$OLD" | wc -l)
python3 - "$A" "$X/$OLD/out/run.json" "$RA" <<'PY' || { echo "NO_BASE"; exit 2; }
import json, os, sys
a = json.load(open(sys.argv[1])); base = (json.load(open(sys.argv[2])).get("args") or {}).get("base")
assert isinstance(base, str) and base
a["base"] = base
fd = os.open(sys.argv[3], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600); os.write(fd, json.dumps(a).encode()); os.close(fd)
print("base from old run:", "under old run folder" if base.startswith(os.path.dirname(os.path.dirname(sys.argv[2]))) else "elsewhere")
PY
cd $M && timeout 7200 node dut/pipeline/launch.js blind-$NN tree --seed "$RA" --family codex --mode fallback --on-refusal halt --resume "$X/$OLD/out" > $B/tree_resume_$NN.log 2>&1
echo "launch exit $?"; rm -f "$RA"
# Tracked files changed in the old run folder are restored from git; untracked files (some were kept out of its commit
# on purpose) are never deleted, only counted before and after.
cd $M && echo "old run folder: tracked changed $(git diff --name-only -- "experiments/blind-$NN/$OLD" | wc -l), untracked before $U0 after $(git ls-files -o -- "experiments/blind-$NN/$OLD" | wc -l)"
git checkout -q -- "experiments/blind-$NN/$OLD"; echo "tracked changed after restore $(git diff --name-only -- "experiments/blind-$NN/$OLD" | wc -l)"
RUN=$(grep -m1 -o "run folder: .*" $B/tree_resume_$NN.log | sed 's/^run folder: //')
NEW=$(basename "$RUN")
[[ $NEW =~ ^[0-9]{8}-[0-9]{4}-tree$ ]] || { echo "NO_RUN_FOLDER"; exit 1; }
python3 $B/tree_resume_check.py $NN $OLD $NEW
flock $B/.post.lock python3 $B/blind_commit.py $NN $NEW "tree records rebuilt by resume from $OLD (U55)"
echo "NEW_TREE $NEW"
