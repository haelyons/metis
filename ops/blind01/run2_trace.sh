set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis; W=$M/experiments/blind-02/m5; D=$W/run2_trace
# Authorized reader on Codex (owner 2026-11-03: trace the seed's comparisons through the finished run2 and say what
# stopped it). Read-only on the run; writes run2_trace/ only. Codex reads are not confined; the prompt's rules bind it.
# Falls back to Claude Opus in restricted mode when Codex writes no status (usage limit). Prints only what
# run2_trace_post.py prints. Usage: bash ~/.cache/blind01/run2_trace.sh
[ -e "$D" ] && { echo ALREADY_EXISTS; exit 1; }
mkdir -p "$D"
ISO="--disable network_proxy --disable apps --disable plugins -c skills.include_instructions=false$(grep -o '^\[mcp_servers\.[A-Za-z0-9_-]*\]' ~/.codex/config.toml | sed 's/^\[mcp_servers\.\(.*\)\]$/ -c mcp_servers.\1.enabled=false/' | tr -d '\n')"
cd "$W" && timeout 2400 codex exec $ISO --json --skip-git-repo-check -C "$W" -s workspace-write \
  -c model_reasoning_effort=high -o "$D/codex_last.md" - < $B/run2_trace.md > "$D/codex.jsonl" 2> "$D/codex_stderr.log"
echo "codex exit $?"
if [ ! -s "$D/status.json" ]; then
  echo "codex wrote no status; opus fallback"
  ALLOW="Read,Write,Glob,Grep,Bash(ls *),Bash(du *),Bash(wc *),Bash(find *),Bash(stat *),Bash(head *),Bash(tail *),Bash(grep *),Bash(jq *)"
  cd "$W" && timeout 2400 claude -p --model opus --output-format stream-json --verbose --no-session-persistence --restricted \
    --strict-mcp-config --permission-mode dontAsk --tools "Read,Write,Glob,Grep,Bash" \
    --allowedTools "$ALLOW" --disallowedTools "Read(**/.keys)" --add-dir $M/dut/pipeline/m5 --name x-b02-run2-trace \
    < $B/run2_trace.md > "$D/transcript.jsonl" 2> "$D/stderr.log"
  echo "opus exit $?"
fi
python3 $B/run2_trace_post.py
echo TRACE_DONE
