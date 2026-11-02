set -u; B=~/.cache/blind01; P=/home/hal/dev/interp/metis-wt/dut/pipeline
# U52 follow-up: Claude (opus) adds the four U52 null facts to the exact reproduce-fact checks of two pre-U52 suites; U52 committed locally (no push) only when all suites pass.
DENY="Read(./m5/pipeline.js) Read(./m5/score_anchors.py) Read(./m5/eval_validity.py) Read(./m5/eval_common.py) Read(./m5/signatures.py) Read(./m5/operator_takeaway.py) Read(./m5/seal_protocol.js) Read(./m5/implement.js) Read(./idea/isolated_runner.js) Read(./idea/codex_cli.js) Read(./idea/runner.js) Read(./m5/eval_equivalence.py) Read(./m5/eval_performance.py) Read(./m5/boxrun.sh) Read(./m5/adapter_smoke.py) Read(./m5/box_probe.sh) Read(./m5/profile_summarise.py) Read(./m5/profile_nsys.sh) Read(./m5/concurrency_probe.py) Read(./m5/bounds.py)"
ct(){ cd $P; timeout 5400 claude -p --model opus --output-format json --no-session-persistence --restricted --strict-mcp-config --permission-mode dontAsk --tools "Read,Write,Edit,Glob,Grep,Bash" --allowedTools "Read,Write,Edit,Glob,Grep,Bash(node tools/*),Bash(python3 tools/*),Bash(python3 -I tools/*),Bash(bash tools/*)" --disallowedTools $DENY --name "x-m5$1" < $B/$1.md > $B/$1_last.json 2> $B/$1.log; echo "$1 exit $?"; }
suites(){ cd $P; f=0; for t in tools/test_*.js tools/e2e_wf.js; do o=$(timeout 900 node $t 2>&1); r=$(printf '%s\n' "$o" | tail -1); echo "$t: $r"; echo "$r" | grep -qE 'all ([0-9]+ )?checks passed|^ok upstream| 0 failures' || { f=$((f+1)); printf '%s\n' "$o" > ~/.cache/blind01/suitefail_$(basename $t).$(date +%s).log; }; done; for t in tools/test_*.py; do r=$(python3 $t 2>&1 | tail -1); echo "$t: $r"; echo "$r" | grep -q 'all checks passed' || f=$((f+1)); done;  for t in tools/test_*.sh; do r=$(timeout 900 bash $t 2>&1 | tail -1); echo "$t: $r"; echo "$r" | grep -q "all checks passed" || f=$((f+1)); done; rm -f ./--version; echo "FAILING=$f"; return $f; }
lc(){ cd /home/hal/dev/interp/metis-wt && git add dut/pipeline/m5 $(git ls-files -m -o --exclude-standard dut/pipeline/tools | grep -v run_failures_only.js) >/dev/null 2>&1 && git commit -q -F - >/dev/null 2>&1 <<MSG && echo "COMMITTED $(git rev-parse --short HEAD)" || echo COMMIT_FAILED
$1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01R9EPikyZNGLiuyGF2iw3X3
MSG
}
ct u52_t2; echo "== suites after u52_t2"; suites && lc "m5 U52: standalone unit probe (separate tests)"
cd /home/hal/dev/interp/metis-wt && git status --short | grep -v "^?? experiments/"
echo CHAIN_DONE
