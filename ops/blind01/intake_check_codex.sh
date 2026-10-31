set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis; W=$M/experiments/blind-01/m5; D=$W/intake_check_codex
# Authorized reader on Codex (owner 2026-10-31: cross-check the Opus reader, then retry with available alternatives).
# Phase A is independent of intake_check/ (the Opus reader's folder); phase B reads it and tries alternative sources.
# Codex reads are not confined; the prompt's rules bind it. Writes: intake_check_codex/ and the download folder.
# Prints only what intake_check_post.py prints. Usage: bash ~/.cache/blind01/intake_check_codex.sh
[ -e "$D" ] && { echo ALREADY_EXISTS; exit 1; }
mkdir -p "$D" $B/intake_check_dl
ISO="--disable network_proxy --disable apps --disable plugins -c skills.include_instructions=false$(grep -o '^\[mcp_servers\.[A-Za-z0-9_-]*\]' ~/.codex/config.toml | sed 's/^\[mcp_servers\.\(.*\)\]$/ -c mcp_servers.\1.enabled=false/' | tr -d '\n')"
cd "$W" && timeout 7800 codex exec $ISO --json --skip-git-repo-check -C "$W" -s workspace-write \
  -c sandbox_workspace_write.network_access=true -c "sandbox_workspace_write.writable_roots=[\"$HOME/.cache/blind01/intake_check_dl\"]" \
  -c model_reasoning_effort=high -o "$D/codex_last.md" - < $B/intake_check_codex.md > "$D/codex.jsonl" 2> "$D/codex_stderr.log"
echo "agent exit $?"
python3 $B/intake_check_post.py --dir intake_check_codex --transcript codex.jsonl
echo CHECK_DONE
