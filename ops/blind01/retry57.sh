set -u; B=~/.cache/blind01; W=/home/hal/dev/interp/metis-wt; P=$W/dut/pipeline
# Units U58, U57a, U57b (sealed comparison; gaps G1, G3, G6); worktree, after U54-U56 committed. Contract: the section a
# content-reading agent drafted seed-neutral (science s23), an independent agent audited clean and sufficient (s24), released
# by sci_draft_release.py. Owner 2026-11-03: weigh towards Claude: Claude (opus) implements, a separate Claude (opus) session
# writes the tests with the implementation Read-denied, Codex reviews afterwards. Each unit commits locally only when every suite passes.
SEC=~/.cache/blind01/u57_contract.md
DENY="Read(./m5/pipeline.js) Read(./m5/score_anchors.py) Read(./m5/eval_validity.py) Read(./m5/eval_common.py) Read(./m5/signatures.py) Read(./m5/operator_takeaway.py) Read(./m5/seal_protocol.js) Read(./m5/implement.js) Read(./idea/isolated_runner.js) Read(./idea/codex_cli.js) Read(./idea/runner.js) Read(./idea/wf.js) Read(./m5/eval_equivalence.py) Read(./m5/eval_performance.py) Read(./m5/boxrun.sh) Read(./m5/adapter_smoke.py) Read(./m5/box_probe.sh) Read(./m5/profile_summarise.py) Read(./m5/profile_nsys.sh) Read(./m5/concurrency_probe.py) Read(./m5/bounds.py) Read(./m5/score_card.py) Read(./m5/card_resolve.js) Read(./m5/score_comparison.py) Read(./m5/cmp_users.sh) Read(./m5/cmp_system.py) Read(./m5/cmp_wrap.py) Read(./src/main.js) Read(./src/schemas.js) Read(./launch.js) Read(./dist/**)"
FIXED="Edit(./tools/test_*) Write(./tools/test_*) Edit(./tools/e2e_*) Write(./tools/e2e_*) Edit(./m5/SCHEMAS.md) Write(./m5/SCHEMAS.md) Edit(./CONTRACT.md) Write(./CONTRACT.md) Read(**/.keys)"
ci(){ cd $P; timeout 7200 claude -p --model opus --output-format json --no-session-persistence --restricted --strict-mcp-config --permission-mode dontAsk --tools "Read,Write,Edit,Glob,Grep,Bash" --allowedTools "Read,Write,Edit,Glob,Grep,Bash(node *),Bash(python3 *),Bash(bash -n *)" --disallowedTools $FIXED --name "x-m5$1" < $B/$1.md > $B/$1_last.json 2> $B/$1.log; echo "$1 exit $?"; }
ct(){ cd $P; timeout 10800 claude -p --model opus --output-format json --no-session-persistence --restricted --strict-mcp-config --permission-mode dontAsk --tools "Read,Write,Edit,Glob,Grep,Bash" --allowedTools "Read,Write,Edit,Glob,Grep,Bash(node tools/*),Bash(python3 tools/*),Bash(python3 -I tools/*),Bash(bash tools/*)" --disallowedTools $DENY --name "x-m5$1" < $B/$1.md > $B/$1_last.json 2> $B/$1.log; echo "$1 exit $?"; }
suites(){ cd $P; f=0; for t in tools/test_*.js tools/e2e_wf.js; do o=$(timeout 900 node $t 2>&1); r=$(printf '%s\n' "$o" | tail -1); echo "$t: $r"; echo "$r" | grep -qE 'all ([0-9]+ )?checks passed|^ok upstream| 0 failures' || { f=$((f+1)); printf '%s\n' "$o" > ~/.cache/blind01/suitefail_$(basename $t).$(date +%s).log; }; done; for t in tools/test_*.py; do r=$(python3 $t 2>&1 | tail -1); echo "$t: $r"; echo "$r" | grep -qE 'all ([0-9]+ )?checks passed' || f=$((f+1)); done;  for t in tools/test_*.sh; do r=$(timeout 900 bash $t 2>&1 | tail -1); echo "$t: $r"; echo "$r" | grep -qE 'all ([0-9]+ )?checks passed' || f=$((f+1)); done; timeout 900 node tools/e2e_main.js > ~/.cache/blind01/e2e_main.u57.log 2>&1 && echo "tools/e2e_main.js: exit 0" || { echo "tools/e2e_main.js: FAIL"; f=$((f+1)); }; rm -f ./--version; find m5 -name __pycache__ -type d -prune -exec rm -rf {} +; echo "FAILING=$f"; return $f; }
lc(){ cd $W && git add dut/pipeline/m5 dut/pipeline/src dut/pipeline/dist dut/pipeline/launch.js dut/pipeline/idea $(git ls-files -m -o --exclude-standard dut/pipeline/tools | grep -v run_failures_only.js) >/dev/null 2>&1 && git commit -q -F - >/dev/null 2>&1 <<MSG && echo "COMMITTED $(git rev-parse --short HEAD)" || { echo COMMIT_FAILED; return 1; }
$1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01R9EPikyZNGLiuyGF2iw3X3
MSG
}
cd $W && [ -z "$(git status --porcelain -- dut/pipeline | grep -v run_failures_only.js)" ] || { echo "WORKTREE_DIRTY"; exit 1; }
python3 - "$SEC" "$P/m5/SCHEMAS.md" <<'EOF'
import sys
sec, p = open(sys.argv[1]).read().rstrip("\n") + "\n\n", sys.argv[2]
s = open(p).read(); h = "## A/results/profile/ and A/profile-packet.json"
assert s.count(h) == 1 and "## Sealed comparison (U57, U58)" not in s and "## Card write-back and re-judging (U56)" in s
open(p, "w").write(s.replace(h, sec + h))
EOF
cd $W && git add dut/pipeline/m5/SCHEMAS.md && git commit -q -m "m5 SCHEMAS: U57-U58 sealed comparison contract (gaps G1, G3, G6; drafted seed-neutral by science s23, audited clean and sufficient by s24)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01R9EPikyZNGLiuyGF2iw3X3" && echo "CONTRACT $(git rev-parse --short HEAD)" || { echo CONTRACT_FAILED; exit 1; }
ci u58; ct u58_t; echo "== suites after u58"; suites && lc "m5 U58: sealed comparison scorer (Opus understudy, separate tests)" || { echo STOP_AT_U58; exit 1; }
ci u57a; ct u57a_t; echo "== suites after u57a"; suites && lc "m5 U57a: sealed comparison design, seals, agent isolation and harness files (Opus understudy, separate tests)" || { echo STOP_AT_U57A; exit 1; }
ci u57b; ct u57b_t; echo "== suites after u57b"; suites && lc "m5 U57b: sealed comparison on the box: separated users, wrapper, compute (Opus understudy, separate tests)" || { echo STOP_AT_U57B; exit 1; }
cd $W && git status --short | grep -v "^?? experiments/"
echo CHAIN_DONE
