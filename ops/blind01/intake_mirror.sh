set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis; W=$M/experiments/blind-01/m5; D=$W/intake_mirror
# Authorized reader on Codex (owner 2026-10-31: "I approve option 2: proceed with the unverified mirror for this local
# experiment"): records the mirror candidate's URLs and hashes, re-fetches to check them, keeps its unverified provenance,
# and writes the run5 brief addendum. No new search. Codex reads are not confined; the prompt's rules bind it.
# Writes: intake_mirror/. Prints only what intake_check_post.py prints. Usage: bash ~/.cache/blind01/intake_mirror.sh
[ -e "$D" ] && { echo ALREADY_EXISTS; exit 1; }
mkdir -p "$D"
ISO="--disable network_proxy --disable apps --disable plugins -c skills.include_instructions=false$(grep -o '^\[mcp_servers\.[A-Za-z0-9_-]*\]' ~/.codex/config.toml | sed 's/^\[mcp_servers\.\(.*\)\]$/ -c mcp_servers.\1.enabled=false/' | tr -d '\n')"
cd "$W" && timeout 3600 codex exec $ISO --json --skip-git-repo-check -C "$W" -s workspace-write \
  -c sandbox_workspace_write.network_access=true \
  -c model_reasoning_effort=high -o "$D/codex_last.md" - < $B/intake_mirror.md > "$D/codex.jsonl" 2> "$D/codex_stderr.log"
echo "agent exit $?"
python3 $B/intake_check_post.py --dir intake_mirror --transcript codex.jsonl
echo CHECK_DONE
