set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis; W=$M/experiments/blind-01/m5; D=$W/run6_diag3
# Authorized reader on Codex: read-only diagnosis of the install route for run6's missing tool (package-index lookups only).
# Codex reads are not confined; the prompt's rules bind it. Network for package-index metadata only. Writes: run6_diag3/.
# Prints only what intake_check_post.py prints. Usage: bash ~/.cache/blind01/run6_diag3.sh
[ -e "$D" ] && { echo ALREADY_EXISTS; exit 1; }
mkdir -p "$D"
ISO="--disable network_proxy --disable apps --disable plugins -c skills.include_instructions=false$(grep -o '^\[mcp_servers\.[A-Za-z0-9_-]*\]' ~/.codex/config.toml | sed 's/^\[mcp_servers\.\(.*\)\]$/ -c mcp_servers.\1.enabled=false/' | tr -d '\n')"
cd "$W" && timeout 1800 codex exec $ISO --json --skip-git-repo-check -C "$W" -s workspace-write -c sandbox_workspace_write.network_access=true \
  -c model_reasoning_effort=high -o "$D/codex_last.md" - < $B/run6_diag3.md > "$D/codex.jsonl" 2> "$D/codex_stderr.log"
echo "agent exit $?"
python3 $B/intake_check_post.py --dir run6_diag3 --transcript codex.jsonl
echo CHECK_DONE
