set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis
# One step of the blind science route (owner 2026-11-03: a content-reading scientific agent prepares the tree/measure
# inputs and, after each result, assesses it and chooses the next test; the operator stays metadata-only).
# Claude Opus restricted first (Codex first for network steps); the other family when the first writes no status.
# The prompt is sci_protocol.md + sci_<step>.md, kept in the step folder. Prints only what sci_post.py prints.
# Usage: bash ~/.cache/blind01/sci.sh <NN> <sNN> [net|codex]   (codex: Codex first, no network; for cross-family checks)
NN=$1; S=$2; NET=${3:-}
[[ $NN =~ ^[0-9][0-9]$ && $S =~ ^s[0-9][0-9]$ && ( -z $NET || $NET == net || $NET == codex ) ]] || { echo USAGE; exit 2; }
X=$M/experiments/blind-$NN; D=$X/science/$S
[ -f $B/sci_$S.md ] && [ -f $B/sci_$S.enums.json ] || { echo NO_STEP_BRIEF; exit 2; }
[ -e "$D" ] && { echo ALREADY_EXISTS; exit 1; }
mkdir -p "$D"
cat $B/sci_protocol.md $B/sci_$S.md > "$D/PROMPT.md"
ISO="--disable network_proxy --disable apps --disable plugins -c skills.include_instructions=false$(grep -o '^\[mcp_servers\.[A-Za-z0-9_-]*\]' ~/.codex/config.toml | sed 's/^\[mcp_servers\.\(.*\)\]$/ -c mcp_servers.\1.enabled=false/' | tr -d '\n')"
NETC=""; [ "$NET" = net ] && NETC="-c sandbox_workspace_write.network_access=true"
cx(){ cd "$D" && timeout 3600 codex exec $ISO --json --skip-git-repo-check -C "$D" -s workspace-write $NETC \
  -c model_reasoning_effort=high -o "$D/codex_last.md" - < "$D/PROMPT.md" > "$D/codex.jsonl" 2> "$D/codex_stderr.log"; echo "codex exit $?"; }
ALLOW="Read,Write,Glob,Grep,Bash(ls *),Bash(du *),Bash(wc *),Bash(find *),Bash(stat *),Bash(head *),Bash(tail *),Bash(grep *),Bash(jq *),Bash(python3 -c *)"
op(){ cd "$D" && timeout 3600 claude -p --model opus --output-format stream-json --verbose --no-session-persistence --restricted \
    --strict-mcp-config --permission-mode dontAsk --tools "Read,Write,Glob,Grep,Bash" \
    --allowedTools "$ALLOW" --disallowedTools "Read(**/.keys)" --add-dir $M/experiments/blind-$NN --add-dir $M/experiments/blind-01/m5 \
    --add-dir $M/dut --name x-b$NN-sci-$S < "$D/PROMPT.md" > "$D/transcript.jsonl" 2> "$D/stderr.log"; echo "opus exit $?"; }
# Owner 2026-11-03: weigh towards Claude (more usage). Opus first; Codex when Opus writes no status, and first for network steps.
if [ "$NET" = net ] || [ "$NET" = codex ]; then cx; [ -s "$D/status.json" ] || { echo "codex wrote no status; opus fallback"; op; }
else op; [ -s "$D/status.json" ] || { echo "opus wrote no status; codex fallback"; cx; }; fi
flock $B/.post.lock python3 $B/sci_post.py $NN $S
echo STEP_DONE
