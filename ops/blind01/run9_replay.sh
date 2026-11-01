set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis; W=$M/experiments/blind-01/m5; D=$W/run9_replay
# Authorized reader on Codex: run9 replay assessment (enums only).
# Codex reads are not confined; the prompt's rules bind it. No network, no git. Writes: run9_replay/.
# Prints only what intake_check_post.py prints. Usage: bash ~/.cache/blind01/run9_replay.sh
[ -e "$D" ] && { echo ALREADY_EXISTS; exit 1; }
mkdir -p "$D"
ISO="--disable network_proxy --disable apps --disable plugins -c skills.include_instructions=false$(grep -o '^\[mcp_servers\.[A-Za-z0-9_-]*\]' ~/.codex/config.toml | sed 's/^\[mcp_servers\.\(.*\)\]$/ -c mcp_servers.\1.enabled=false/' | tr -d '\n')"
cd "$W" && timeout 1500 codex exec $ISO --json --skip-git-repo-check -C "$W" -s workspace-write \
  -c model_reasoning_effort=high -o "$D/codex_last.md" - < $B/run9_replay.md > "$D/codex.jsonl" 2> "$D/codex_stderr.log"
echo "agent exit $?"
flock $B/.post.lock python3 $B/intake_check_post.py --dir run9_replay --transcript codex.jsonl
echo CHECK_DONE
