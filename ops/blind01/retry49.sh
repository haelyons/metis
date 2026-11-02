set -u; B=~/.cache/blind01; P=/home/hal/dev/interp/metis-wt/dut/pipeline
# Units u50b (probe script unit mode) then u52 (standalone unit probe); worktree. Codex implements, Claude (opus) writes tests from SCHEMAS.md; each unit committed locally (no push) only when all suites pass.
ISO="--disable network_proxy --disable apps --disable plugins -c skills.include_instructions=false$(grep -o '^\[mcp_servers\.[A-Za-z0-9_-]*\]' ~/.codex/config.toml | sed 's/^\[mcp_servers\.\(.*\)\]$/ -c mcp_servers.\1.enabled=false/' | tr -d '\n')"
cx(){ timeout $3 codex exec $ISO --skip-git-repo-check -C $P -s workspace-write -c model_reasoning_effort=$2 -o $B/$1_last.md - < $B/$1.md > $B/$1.log 2>&1; echo "$1 exit $?"; }
DENY="Read(./m5/pipeline.js) Read(./m5/score_anchors.py) Read(./m5/eval_validity.py) Read(./m5/eval_common.py) Read(./m5/signatures.py) Read(./m5/operator_takeaway.py) Read(./m5/seal_protocol.js) Read(./m5/implement.js) Read(./idea/isolated_runner.js) Read(./idea/codex_cli.js) Read(./idea/runner.js) Read(./m5/eval_equivalence.py) Read(./m5/eval_performance.py) Read(./m5/boxrun.sh) Read(./m5/adapter_smoke.py) Read(./m5/box_probe.sh) Read(./m5/profile_summarise.py) Read(./m5/profile_nsys.sh) Read(./m5/concurrency_probe.py) Read(./m5/bounds.py)"
ct(){ cd $P; timeout 5400 claude -p --model opus --output-format json --no-session-persistence --restricted --strict-mcp-config --permission-mode dontAsk --tools "Read,Write,Edit,Glob,Grep,Bash" --allowedTools "Read,Write,Edit,Glob,Grep,Bash(node tools/*),Bash(python3 tools/*),Bash(python3 -I tools/*),Bash(bash tools/*)" --disallowedTools $DENY --name "x-m5$1" < $B/$1.md > $B/$1_last.json 2> $B/$1.log; echo "$1 exit $?"; }
suites(){ cd $P; f=0; for t in tools/test_*.js tools/e2e_wf.js; do o=$(timeout 900 node $t 2>&1); r=$(printf '%s\n' "$o" | tail -1); echo "$t: $r"; echo "$r" | grep -qE 'all ([0-9]+ )?checks passed|^ok upstream| 0 failures' || { f=$((f+1)); printf '%s\n' "$o" > ~/.cache/blind01/suitefail_$(basename $t).$(date +%s).log; }; done; for t in tools/test_*.py; do r=$(python3 $t 2>&1 | tail -1); echo "$t: $r"; echo "$r" | grep -q 'all checks passed' || f=$((f+1)); done;  for t in tools/test_*.sh; do r=$(timeout 900 bash $t 2>&1 | tail -1); echo "$t: $r"; echo "$r" | grep -q "all checks passed" || f=$((f+1)); done; rm -f ./--version; echo "FAILING=$f"; return $f; }
lc(){ cd /home/hal/dev/interp/metis-wt && git add dut/pipeline/m5 $(git ls-files -m -o --exclude-standard dut/pipeline/tools | grep -v run_failures_only.js) >/dev/null 2>&1 && git commit -q -F - >/dev/null 2>&1 <<MSG && echo "COMMITTED $(git rev-parse --short HEAD)" || echo COMMIT_FAILED
$1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01R9EPikyZNGLiuyGF2iw3X3
MSG
}
cx u50b high 3600; ct u50b_t; echo "== suites after u50b"; suites && lc "m5 U50b: concurrency probe unit mode (separate tests)" || { echo STOP_AFTER_U50B; cd /home/hal/dev/interp/metis-wt && git status --short | grep -v "^?? experiments/"; echo CHAIN_DONE; exit 1; }
cx u52 high 5400; ct u52_t; echo "== suites after u52"; suites && lc "m5 U52: standalone unit probe (separate tests)"
cd /home/hal/dev/interp/metis-wt && git status --short | grep -v "^?? experiments/"
echo CHAIN_DONE
