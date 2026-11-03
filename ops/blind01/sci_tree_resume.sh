set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis
# Rebuild an earlier tree run's records with the current pipeline by --resume (U55): every agent call from the cache, no model
# call, the same cards; the records gain name, unit, band and judged. Prints only tree_resume_check.py's lines and the commit.
# Usage: bash ~/.cache/blind01/sci_tree_resume.sh <NN> <old stamp>-tree <science step sNN whose tree_args.json the old run used>
NN=$1; OLD=$2; S=$3
[[ $NN =~ ^[0-9][0-9]$ && $OLD =~ ^[0-9]{8}-[0-9]{4}-tree$ && $S =~ ^s[0-9][0-9]$ ]] || { echo USAGE; exit 2; }
X=$M/experiments/blind-$NN; A=$X/science/$S/tree_args.json
grep -q "judged" $M/dut/pipeline/src/main.js || { echo "U55_NOT_IN_MAIN"; exit 2; }
[ -f "$A" ] && [ -f "$X/$OLD/out/journal.jsonl" ] || { echo "MISSING_INPUT"; exit 2; }
cd $M && timeout 7200 node dut/pipeline/launch.js blind-$NN tree --seed "$A" --family codex --mode fallback --on-refusal halt --resume "$X/$OLD/out" > $B/tree_resume_$NN.log 2>&1
echo "launch exit $?"
RUN=$(grep -m1 -o "run folder: .*" $B/tree_resume_$NN.log | sed 's/^run folder: //')
NEW=$(basename "$RUN")
[[ $NEW =~ ^[0-9]{8}-[0-9]{4}-tree$ ]] || { echo "NO_RUN_FOLDER"; exit 1; }
python3 $B/tree_resume_check.py $NN $OLD $NEW
flock $B/.post.lock python3 $B/blind_commit.py $NN $NEW "tree records rebuilt by resume from $OLD (U55)"
echo "NEW_TREE $NEW"
