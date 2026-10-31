set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis; W=$M/experiments/blind-01/m5; D=$W/intake_check
# Authorized reader (owner, 2026-10-30): headless Claude Opus reads blind-01 intake records and checks the materials.
# --restricted ignores user settings, so the operator's blind guard does not apply to it; file tools stay confined to
# experiments/blind-01/m5 and the download folder. Everything it writes stays in intake_check/; this script prints only
# the validated enum status and counts (intake_check_post.py). Usage: bash ~/.cache/blind01/intake_check.sh
[ -e "$D" ] && { echo ALREADY_EXISTS; exit 1; }
mkdir -p "$D" $B/intake_check_dl
ALLOW="Read,Write,Edit,Glob,Grep,WebFetch,WebSearch,Bash(curl *),Bash(wget *),Bash(git ls-remote *),Bash(git clone *),Bash(sha256sum *),Bash(md5sum *),Bash(ls *),Bash(du *),Bash(file *),Bash(tar -t*),Bash(unzip -l *),Bash(wc *),Bash(find *),Bash(mkdir *),Bash(jq *),Bash(sleep *)"
cd "$W" && timeout 7200 claude -p --model opus --output-format stream-json --verbose --no-session-persistence --restricted \
  --strict-mcp-config --permission-mode dontAsk --tools "Read,Write,Edit,Glob,Grep,Bash,WebFetch,WebSearch" \
  --allowedTools "$ALLOW" --disallowedTools "Read(**/.keys)" --add-dir $B/intake_check_dl --name x-b01-intake-check \
  < $B/intake_check.md > "$D/transcript.jsonl" 2> "$D/stderr.log"
echo "agent exit $?"
python3 $B/intake_check_post.py
echo CHECK_DONE
