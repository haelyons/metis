set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis; W=$M/experiments/blind-02/m5; D=$W/run2_progress
# Authorized reader on Codex: read-only progress check of blind-02 run2 while it runs (no network, no git, no box).
# Codex reads are not confined; the prompt's rules bind it. Writes run2_progress/. Prints only what intake_check_post.py
# prints. Usage: bash ~/.cache/blind01/run2_progress.sh
[ -e "$D" ] && { echo ALREADY_EXISTS; exit 1; }
mkdir -p "$D"
ISO="--disable network_proxy --disable apps --disable plugins -c skills.include_instructions=false$(grep -o '^\[mcp_servers\.[A-Za-z0-9_-]*\]' ~/.codex/config.toml | sed 's/^\[mcp_servers\.\(.*\)\]$/ -c mcp_servers.\1.enabled=false/' | tr -d '\n')"
cd "$W" && timeout 1800 codex exec $ISO --json --skip-git-repo-check -C "$W" -s workspace-write \
  -c model_reasoning_effort=high -o "$D/codex_last.md" - < $B/run2_progress.md > "$D/codex.jsonl" 2> "$D/codex_stderr.log"
echo "agent exit $?"
flock $B/.post.lock python3 $B/intake_check_post.py --exp blind-02 --dir run2_progress --transcript codex.jsonl
echo CHECK_DONE
