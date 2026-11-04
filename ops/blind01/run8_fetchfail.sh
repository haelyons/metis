set -u; B=~/.cache/blind01; M=/home/hal/dev/interp/metis; W=$M/experiments/blind-02/m5; D=$W/run8_fetchfail
# Authorized reader (Opus, owner 2026-11-03: Claude first): why fetch_private.sh failed in the fixture rerun run8, and
# whether the comparison mechanism caused it. --restricted ignores user settings, so the operator's blind guard does
# not apply; file tools stay in the experiment folder plus the pipeline code (read only by the prompt's rules); no
# network tools. Prints only what intake_check_post.py prints. Usage: bash ~/.cache/blind01/run8_fetchfail.sh
[ -e "$D" ] && { echo ALREADY_EXISTS; exit 1; }
mkdir -p "$D"
ALLOW="Read,Write,Glob,Grep,Bash(ls *),Bash(du *),Bash(wc *),Bash(find *),Bash(stat *),Bash(head *),Bash(tail *),Bash(grep *),Bash(jq *)"
cd "$W" && timeout 1800 claude -p --model opus --output-format stream-json --verbose --no-session-persistence --restricted \
  --strict-mcp-config --permission-mode dontAsk --tools "Read,Write,Glob,Grep,Bash" \
  --allowedTools "$ALLOW" --disallowedTools "Read(**/.keys)" --add-dir $M/dut/pipeline/m5 --add-dir $W/../science --add-dir $M/experiments/shakedown-m5/cmp20 --name x-b02-run8-fetchfail \
  < $B/run8_fetchfail.md > "$D/transcript.jsonl" 2> "$D/stderr.log"
echo "agent exit $?"
flock $B/.post.lock python3 $B/intake_check_post.py --exp blind-02 --dir run8_fetchfail
echo CHECK_DONE
