set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis; W=$M/experiments/blind-01/m5; D=$W/intake_acquire
# Authorized reader on Codex (owner 2026-10-31: "Proceed autonomously, attempt to acquire resources regarding our
# principles"): establishes verified, box-fetchable locations for the moved materials, or reports why not.
# Codex reads are not confined; the prompt's rules bind it. Writes: intake_acquire/ and the download folder.
# Prints only what intake_check_post.py prints. Usage: bash ~/.cache/blind01/intake_acquire.sh
[ -e "$D" ] && { echo ALREADY_EXISTS; exit 1; }
mkdir -p "$D" $B/intake_check_dl
ISO="--disable network_proxy --disable apps --disable plugins -c skills.include_instructions=false$(grep -o '^\[mcp_servers\.[A-Za-z0-9_-]*\]' ~/.codex/config.toml | sed 's/^\[mcp_servers\.\(.*\)\]$/ -c mcp_servers.\1.enabled=false/' | tr -d '\n')"
cd "$W" && timeout 9000 codex exec $ISO --json --skip-git-repo-check -C "$W" -s workspace-write \
  -c sandbox_workspace_write.network_access=true -c "sandbox_workspace_write.writable_roots=[\"$HOME/.cache/blind01/intake_check_dl\"]" \
  -c model_reasoning_effort=high -o "$D/codex_last.md" - < $B/intake_acquire.md > "$D/codex.jsonl" 2> "$D/codex_stderr.log"
echo "agent exit $?"
python3 $B/intake_check_post.py --dir intake_acquire --transcript codex.jsonl
echo CHECK_DONE
