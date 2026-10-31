set -u; M=/home/hal/dev/interp/metis
# Snapshot commit of a run folder, as the chain's commit step: status lines only, git output to /dev/null,
# files over 95 MB left uncommitted (count printed). Usage: commit_run.sh <run_root> <commit message>
R=$1; MSG=$2; cd $M
pushed(){ git fetch -q origin 2>/dev/null && [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ]; }
git add "$R" dut/pipeline/m5/raids_used.jsonl >/dev/null 2>&1
n=$(find "$R" -type f -size +95M | wc -l); find "$R" -type f -size +95M -print0 | xargs -0 -r git rm --cached -q --ignore-unmatch -- >/dev/null 2>&1
echo "large files left uncommitted: $n"
git commit -q -m "$MSG

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01R9EPikyZNGLiuyGF2iw3X3" >/dev/null 2>&1 || { echo COMMIT_FAILED_OR_NOTHING; exit 1; }
git push -q origin main >/dev/null 2>&1; if pushed; then echo "PUSH_OK $(git rev-parse --short HEAD)"; else echo PUSH_FAILED; exit 1; fi
