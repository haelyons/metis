set -u; B=~/.cache/blind01; P=/home/hal/dev/interp/metis/dut/pipeline; M=/home/hal/dev/interp/metis
# Blind variant of retry7.sh: same box up, pipeline, box down (always), commit, verified push.
# retry48: retry38 with run9's box type (gpu_1x_h100_pcie) first, for the unit equivalence check.
# retry38: retry36 with the 12 h ceiling. Since U47 (pipeline run_ceiling_s 43200 drives box budgets): pipeline
# timeout 46800 s (ceiling + 1 h for fetch, records, takeaways) and box --max-hours 14.
# retry36: the launch is tried up to 3 times; without a box the pipeline does not start and nothing is committed.
# Prints status lines only: git output that could name run files goes to /dev/null, and files over 95 MB
# are left uncommitted on disk (GitHub's 100 MB limit) with only their count printed.
# Usage: retry32.sh <run_root> <commit message>. The run root holds args.json. No step reads run content.
R=$1; MSG=$2; mkdir -p "$R"
pushed(){ cd $M; git fetch -q origin 2>/dev/null && [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ]; }
commit(){ cd $M; git add "$R" dut/pipeline/m5/raids_used.jsonl >/dev/null 2>&1
  n=$(find "$R" -type f -size +95M | wc -l); find "$R" -type f -size +95M -print0 | xargs -0 -r git rm --cached -q --ignore-unmatch -- >/dev/null 2>&1
  echo "large files left uncommitted: $n"
  git commit -q -m "$1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01R9EPikyZNGLiuyGF2iw3X3" >/dev/null 2>&1 || { echo COMMIT_FAILED; return 1; }
  git push -q origin main >/dev/null 2>&1; if pushed; then echo "PUSH_OK $(git rev-parse --short HEAD)"; else echo "PUSH_FAILED"; return 1; fi; }
down(){ cd $P; timeout 900 bash serve/lambda_serve.sh down 2>&1 | tail -1; }
trap down EXIT
cd $P
up=1; for i in 1 2 3; do
  timeout 7200 bash serve/lambda_serve.sh up --dev --types "gpu_1x_h100_pcie gpu_1x_h100_sxm5 gpu_1x_a100_sxm4 gpu_1x_a100 gpu_1x_a10" --max-hours 14 --wait-capacity 180 >> $R/devbox_up.log 2>&1; up=$?
  echo "devbox up attempt $i exit $up"; [ $up = 0 ] && break; down; done
[ $up = 0 ] || { echo BOX_UP_FAILED; echo CHAIN_DONE; exit 1; }
timeout 46800 node idea/wf.js --config m5/wf_config.json --script m5/pipeline.js --args $R/args.json --out $R/agent/wf --profile latent_skeptic --family codex > $R/pipeline.log 2>&1; echo "pipeline exit $?"
down; trap - EXIT
commit "$MSG"
bash $P/serve/lambda_serve.sh status 2>&1 | head -1
echo CHAIN_DONE
