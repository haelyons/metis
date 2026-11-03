set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis
# Run the tree a science step chose (NEXT.json action tree), on the Codex family with the default understudy chain.
# Refuses unless the step folder and the operator's predictions for it are committed unchanged (both sealed).
# Launch output goes to the step's tree_launch.log (never printed); prints the run folder name (a timestamp), the exit
# code, the commit, and tree_read.py's metadata. Usage: bash ~/.cache/blind01/sci_tree.sh <NN> <sNN>
NN=$1; S=$2
[[ $NN =~ ^[0-9][0-9]$ && $S =~ ^s[0-9][0-9]$ ]] || { echo USAGE; exit 2; }
X=$M/experiments/blind-$NN; D=$X/science/$S; P=$X/m5/predictions/tree_$S.md
cd $M
python3 -c "import json,sys; n=json.load(open('$D/NEXT.json')); sys.exit(0 if n.get('action')=='tree' else 1)" || { echo NOT_A_TREE_STEP; exit 2; }
for f in "$D" "$P"; do
  [ -e "$f" ] && [ -z "$(git status --porcelain -- "$f")" ] && git ls-files --error-unmatch -- "$f" >/dev/null 2>&1 || { echo "NOT_SEALED $([ "$f" = "$P" ] && echo operator_predictions || echo step_folder)"; exit 2; }
done
[ -e "$D/tree_launch.log" ] && { echo ALREADY_LAUNCHED; exit 1; }
echo "sealed at $(git log -1 --format=%h -- "$D") and $(git log -1 --format=%h -- "$P")"
timeout 18000 node dut/pipeline/launch.js blind-$NN tree --seed "$D/tree_args.json" --family codex --mode fallback --on-refusal halt \
  > "$D/tree_launch.log" 2>&1
echo "tree exit $?"
RUN=$(sed -n 's#^run folder: .*/\([0-9]\{8\}-[0-9]\{4\}-tree\(-[0-9]*\)\?\)$#\1#p' "$D/tree_launch.log" | head -1)
[ -n "$RUN" ] || { echo NO_RUN_FOLDER; exit 1; }
echo "run folder $RUN"
python3 $B/blind_commit.py $NN "$RUN" "tree run chosen by science step $S"
python3 $B/blind_commit.py $NN "science/$S" "tree launch log for step $S"
python3 $B/tree_read.py $NN "$RUN"
echo TREE_DONE
