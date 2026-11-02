set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis; W=$M/experiments/blind-02/m5; D=$W/b01_materials
# Authorized reader on Codex for blind-02 (owner 2026-11-02: "Codex addendum", "Yes, same mirror"): copies the case
# identities, prepared inputs, reference locations, mirror locations and hashes, and software pins the seed refers to
# from blind-01 records into the run1 brief addendum; reachability checks only, no full downloads. Codex reads are not
# confined; the prompt's rules bind it. Writes: blind-02 m5/b01_materials/. Prints only what intake_check_post.py prints.
# Usage: bash ~/.cache/blind01/b02_materials.sh
[ -e "$D" ] && { echo ALREADY_EXISTS; exit 1; }
mkdir -p "$D"
ISO="--disable network_proxy --disable apps --disable plugins -c skills.include_instructions=false$(grep -o '^\[mcp_servers\.[A-Za-z0-9_-]*\]' ~/.codex/config.toml | sed 's/^\[mcp_servers\.\(.*\)\]$/ -c mcp_servers.\1.enabled=false/' | tr -d '\n')"
cd "$W" && timeout 3000 codex exec $ISO --json --skip-git-repo-check -C "$W" -s workspace-write \
  -c sandbox_workspace_write.network_access=true \
  -c model_reasoning_effort=high -o "$D/codex_last.md" - < $B/b02_materials.md > "$D/codex.jsonl" 2> "$D/codex_stderr.log"
echo "agent exit $?"
flock $B/.post.lock python3 $B/intake_check_post.py --exp blind-02 --dir b01_materials --transcript codex.jsonl
echo CHECK_DONE
