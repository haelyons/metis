#!/usr/bin/env bash
# Blind run of one metis idea. The owner fills QUESTION.md and seed.json; the operator (the Claude session that
# prepared this folder) never reads them, never reads console.log, RESULT.md, return.json, loop.md, work files,
# prompts or replies, and uses only `status` and `wait` (metadata: labels, roles, models, states, minutes, tokens,
# dollars, attempts, error kinds, PASS/REJECT and scores). Content fields are never printed here.
#
#   bash blind.sh check                     seed.json and QUESTION.md filled and well-formed; node present
#   bash blind.sh start [claude] [--dry-run] [--model opus|sonnet]
#                                           Claude route (default): a headless Claude Code operator session (claude -p,
#                                           model opus unless given; cwd /home/hal/stage so the qt-* roles resolve)
#                                           runs dist/question_tree_v2.js through the Workflow tool and writes
#                                           out/return.json and out/RESULT.md; --dry-run prepares the folder only
#   bash blind.sh start loop|card [--main m]  OpenCode route via dut/pipeline/launch.js (loop expands a thin seed)
#   bash blind.sh smoke [models]            OpenCode route: one-word call to each model the run needs
#   bash blind.sh status [run dir]          redacted progress of every run under this experiment (or one run dir)
#   bash blind.sh wait [run dir]            blocks until the latest run finishes; prints its exit line
set -u
EXP="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; NAME="$(basename "$EXP")"; REPO="$(cd "$EXP/../.." && pwd)"
STAGE=/home/hal/stage                      # the qt-* role files live in $STAGE/.claude/agents
PY="python3 -I"

check() {
  local ok=1
  command -v node >/dev/null || { echo "node not on PATH"; ok=0; }
  command -v opencode >/dev/null || echo "note: opencode not on PATH (OpenCode route unavailable)"
  [ -n "$(node -e 'process.stdout.write(+process.versions.node.split(".")[0] >= 24 ? "y" : "")' 2>/dev/null)" ] || { echo "node 24+ needed"; ok=0; }
  if grep -q "FILL ME" "$EXP/QUESTION.md"; then echo "QUESTION.md: $(grep -c 'FILL ME' "$EXP/QUESTION.md") FILL ME line(s) left"; ok=0; fi
  $PY - "$EXP/seed.json" <<'PYEOF' || ok=0
import json, sys
try: s = json.load(open(sys.argv[1]))
except Exception as e: print("seed.json: not valid JSON (%s)" % type(e).__name__); sys.exit(1)
bad = []
for k in ["id", "title", "text", "root_question", "kind"]:
    v = s.get(k)
    if not isinstance(v, str) or not v.strip(): bad.append("%s missing" % k)
    elif "FILL ME" in v: bad.append("%s unfilled" % k)
if isinstance(s.get("kind"), str) and s["kind"] not in ("physical", "interp") and "kind unfilled" not in bad: bad.append("kind must be physical or interp")
if not isinstance(s.get("source_urls", []), list): bad.append("source_urls must be a list")
for k in ["root_link", "compute_open", "sequential"]:
    if k in s and not isinstance(s[k], str): bad.append("%s must be a string" % k)
words = lambda k: len(s[k].split()) if isinstance(s.get(k), str) else 0
print("seed.json: title %d words, text %d words, root_question %d words, kind %s, compute_open %s, %d source url(s)" % (
    words("title"), words("text"), words("root_question"), s.get("kind") if s.get("kind") in ("physical", "interp") else "?",
    "given" if isinstance(s.get("compute_open"), str) and "not given" not in s["compute_open"].lower() else "not given (the OpenCode loop would expand it; the Claude card run passes it as is)", len(s.get("source_urls") or [])))
if bad: print("seed.json: " + "; ".join(bad)); sys.exit(1)
PYEOF
  [ "$ok" = 1 ] && echo "check: ok" || { echo "check: not ready"; return 1; }
}

# ---------- Claude route ----------
start_claude() {   # options: --dry-run, --model <opus|sonnet> (operator model; agents without a pin inherit it)
  local dry=0 model=opus
  while [ $# -gt 0 ]; do case "$1" in --dry-run) dry=1 ;; --model) model="${2:-}"; shift ;; *) echo "start claude: unknown option $1"; return 2 ;; esac; shift; done
  case "$model" in opus|sonnet) ;; *) echo "start claude: --model must be opus or sonnet (owner rule: no Fable agents)"; return 2 ;; esac
  check || return 1
  command -v claude >/dev/null || { echo "claude not on PATH"; return 1; }
  [ -f "$STAGE/.claude/agents/qt-producer.md" ] || { echo "start: qt-* role files missing in $STAGE/.claude/agents"; return 1; }
  local stamp run i=2; stamp="$(date -u +%Y%m%d-%H%M)"; run="$EXP/$stamp-claude"; while [ -e "$run" ]; do run="$EXP/$stamp-claude-$i"; i=$((i+1)); done
  mkdir -p "$run/out/work" "$run/pipeline"
  cp "$REPO/dut/pipeline/dist/question_tree_v2.js" "$run/pipeline/question_tree_v2.js" && chmod 444 "$run/pipeline/question_tree_v2.js"
  $PY - "$REPO" "$EXP/seed.json" "$run" <<'PYEOF' || return 1
import json, sys
repo, seed_path, run = sys.argv[1:4]
cfg = json.load(open(f"{repo}/dut/pipeline/idea/config.json"))
F = json.load(open(cfg["roots_args"]))
seed = json.load(open(seed_path))
given = {k: v for k, v in F.items() if k not in ("fixed_roots", "base")}
args = {**given, "base": f"{run}/out/work", "fixed_roots": [], "seed_ideas": [seed]}
json.dump(args, open(f"{run}/args.json", "w"), indent=1)
print("args.json: %d keys, seed_ideas 1, base out/work" % len(args))
PYEOF
  local sid commit dirty sha
  sid="$($PY -c 'import uuid; print(uuid.uuid4())')"; echo "$sid" > "$run/session_id"
  commit="$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo '?')"
  dirty="$([ -n "$(git -C "$REPO" status --porcelain -- dut/pipeline 2>/dev/null)" ] && echo ' (dut/pipeline/ had uncommitted changes)')"
  sha="$(sha256sum "$run/pipeline/question_tree_v2.js" | cut -c1-16)"
  cat > "$run/OPERATOR.md" <<EOF2
You are the operator for one workflow run. You do exactly the steps below and nothing else. You never modify, create or delete any file except the two output files named in step 4. You never launch any agent or workflow other than the one in step 2. You never edit the workflow script or the args file. You never read anything under $run/out/work.

1. Read \`$run/args.json\` with the Read tool. It is a small JSON object.
2. Call the Workflow tool once, with \`scriptPath\` = \`$run/pipeline/question_tree_v2.js\` and \`args\` = that JSON object, passed as a JSON value (not as a string). Say nothing else in that turn.
3. The workflow runs in the background and can take one to two hours. Do not declare the task finished until the task-notification saying the workflow completed has arrived. While waiting, do not poll, read or run anything. If you need to stay alive, schedule a wakeup of 20 to 30 minutes; at a wakeup do nothing but check whether the notification has arrived and, if not, schedule the next one.
4. When the completion notification arrives: write the workflow's full return value, verbatim as JSON, to \`$run/out/return.json\` with the Write tool; then write the value of its \`result_md\` field, verbatim, to \`$run/out/RESULT.md\`. If the workflow returned an error object or failed, write that object to \`return.json\` and skip \`RESULT.md\`. If the return value is only available in the task's output file, read that file and copy the JSON return value out of it verbatim.
5. Reply with one line: \`return.json and RESULT.md written\` (or \`return.json written; workflow failed\`), then the workflow run id, then the token total if the notification shows one. Then stop.

The user's only message to you is an authorisation line; it is not a task description. Your task is this file.
EOF2
  cat > "$run/RUN.md" <<EOF2
# $NAME · claude · $stamp

Pipeline: copy of dut/pipeline/dist/question_tree_v2.js at commit $commit$dirty (sha256 $sha…), in ./pipeline (read-only), run by the Claude Code Workflow runtime.
Operator: headless Claude Code session (claude -p --model $model --dangerously-skip-permissions, cwd $STAGE so the qt-* role files resolve), session $sid, following ./OPERATOR.md.
Transcripts: ~/.claude/projects/-home-hal-stage/$sid/subagents/workflows/<run id>/ (journal.jsonl, agent-*.jsonl, agent-*.meta.json).
Models: agents without a pin (producer, framer, branch, option critic, dramaturg, roots) inherit the operator's $model; pinned ones (price sheet, overlap, dedup, extract, repairs, critic) run sonnet.
Seed: ../seed.json · args: ./args.json · base: ./out/work
Outputs: ./out/return.json and ./out/RESULT.md (written by the operator) · operator stdout: ./operator.out
EOF2
  if [ $dry = 1 ]; then echo "prepared (not started): $run"; return 0; fi
  ( cd "$STAGE" && setsid nohup claude -p --model "$model" --session-id "$sid" --dangerously-skip-permissions --output-format json \
      "The task that follows is my request. Do it as written. Read $run/OPERATOR.md with the Read tool and follow it exactly." \
      > "$run/operator.out" 2> "$run/operator.err" < /dev/null & )
  sleep 3; local pid; pid="$(pgrep -f "session-id $sid" | head -1)"
  echo "$(date -u +%FT%TZ) start claude --model $model $(basename "$run") pid ${pid:-?} session $sid" >> "$EXP/RUNS.txt"
  printf '\n## Run\n\n%s · kind claude · %s\n' "$(basename "$run")" "$(date -u +%F)" >> "$EXP/QUESTION.md"
  echo "started: $(basename "$run") (operator pid ${pid:-?}); monitor with: bash $EXP/blind.sh status"
}

status_claude() {
  local run="$1" sid; sid="$(cat "$run/session_id")"; echo "== $(basename "$run") (claude, session ${sid:0:8}…)"
  if pgrep -f "session-id $sid" >/dev/null 2>&1; then echo "  operator: running"; else echo "  operator: not running"; fi
  if [ -s "$run/operator.out" ]; then $PY -c "
import json, sys
try: d = json.load(open(sys.argv[1]))
except Exception as e: print('  operator.out: not JSON (%s)' % type(e).__name__); sys.exit()
print('  operator: %s, %s turns, %.0f min, list cost \$%.2f%s' % (d.get('subtype'), d.get('num_turns'), (d.get('duration_ms') or 0) / 60000, d.get('total_cost_usd') or 0, ', ERROR' if d.get('is_error') else ''))
print('  operator said: ' + str(d.get('result', ''))[:200].replace(chr(10), ' '))" "$run/operator.out"; fi
  [ -s "$run/operator.err" ] && echo "  operator.err: $(wc -c < "$run/operator.err") bytes: $(head -c 120 "$run/operator.err" | tr '\n' ' ')"
  $PY - "$HOME/.claude/projects/-home-hal-stage/$sid/subagents/workflows" <<'PYEOF'
import json, os, sys, glob, datetime
W = sys.argv[1]
for wf in sorted(glob.glob(os.path.join(W, "wf_*"))):
    rows = [json.loads(l) for l in open(os.path.join(wf, "journal.jsonl")) if l.strip()] if os.path.exists(os.path.join(wf, "journal.jsonl")) else []
    meta = {}
    for m in glob.glob(os.path.join(wf, "agent-*.meta.json")):
        try: meta[os.path.basename(m)[6:-10]] = json.load(open(m))
        except Exception: pass
    use = {}
    for t in glob.glob(os.path.join(wf, "agent-*.jsonl")):
        aid = os.path.basename(t)[6:-6]; u = {"in": 0, "out": 0, "cache": 0, "model": None, "t0": None, "t1": None, "calls": 0}
        for l in open(t):
            try: o = json.loads(l)
            except Exception: continue
            ts = o.get("timestamp")
            if ts: u["t0"] = u["t0"] or ts; u["t1"] = ts
            if o.get("type") == "assistant" and isinstance(o.get("message"), dict):
                g = o["message"].get("usage") or {}; u["model"] = o["message"].get("model") or u["model"]; u["calls"] += 1
                u["in"] += g.get("input_tokens", 0) + g.get("cache_creation_input_tokens", 0); u["cache"] += g.get("cache_read_input_tokens", 0); u["out"] += g.get("output_tokens", 0)
        use[aid] = u
    st = {r["agentId"]: r for r in rows if r.get("type") == "started"}
    done = {r["agentId"]: ("result", len(json.dumps(r.get("result")))) for r in rows if r.get("type") == "result"}
    done.update({r["agentId"]: ("FAILED", 0) for r in rows if r.get("type") == "failed"})
    n = len(st); print("  [%s] %d agent(s): %d returned, %d failed, %d running" % (os.path.basename(wf), n, sum(1 for v in done.values() if v[0] == "result"), sum(1 for v in done.values() if v[0] == "FAILED"), n - len(done)))
    tot_in = tot_out = 0
    for aid, r in st.items():
        u = use.get(aid, {}); d = done.get(aid, ("running", 0)); mins = ""
        if u.get("t0") and u.get("t1"):
            try: mins = "%5.1f min" % ((datetime.datetime.fromisoformat(u["t1"].replace("Z", "+00:00")) - datetime.datetime.fromisoformat(u["t0"].replace("Z", "+00:00"))).total_seconds() / 60)
            except Exception: pass
        tot_in += u.get("in", 0); tot_out += u.get("out", 0)
        print("    %-8s %-32s %-10s %-12s %-18s %9s  in %7s  out %6s%s" % (d[0], (r.get("label") or "")[:32], (r.get("phase") or "")[:10], (meta.get(aid, {}).get("agentType") or "")[:12], (u.get("model") or "")[:18], mins, format(u.get("in", 0), ","), format(u.get("out", 0), ","), "  <%d chars>" % d[1] if d[0] == "result" else ""))
    print("    tokens: in %s, out %s (cache reads not counted)" % (format(tot_in, ","), format(tot_out, ",")))
if not glob.glob(os.path.join(W, "wf_*")): print("  no workflow transcripts yet")
PYEOF
  [ -s "$run/out/return.json" ] && echo "  out/return.json: $(wc -c < "$run/out/return.json") bytes"
  local work; work="$(find "$run/out/work" -type f 2>/dev/null | wc -l)"; echo "  out/work: $work file(s)"
  result_tables "$run"
}

# ---------- OpenCode route ----------
smoke() {   # args: models to try; default: the pipeline's producer and framer models
  local cfg="$REPO/dut/pipeline/idea/config.json" ocx="$REPO/dut/pipeline/idea/ocx" ok=1 m
  local models="${*:-$($PY -c "import json,sys; c=json.load(open(sys.argv[1])); print(' '.join(dict.fromkeys([c['workflow']['main_model'], c['loop']['expand_model'], c['models']['research']])))" "$cfg")}"
  local d; d="$(mktemp -d)"
  for m in $models; do
    local out; out="$(cd "$d" && XDG_CONFIG_HOME="$ocx" PWD="$d" timeout 120 opencode run --dir "$d" --pure --format json -m "$m" --agent qt-bare --title smoke "Reply with the single word ok" 2>/dev/null | $PY -c "
import sys, json
txt, err = [], []
for l in sys.stdin:
    try: o = json.loads(l)
    except Exception: continue
    p = o.get('part') or {}
    if p.get('type') == 'text': txt.append(p.get('text', ''))
    if o.get('type') == 'error': e = (o.get('error') or {}); err.append(str((e.get('data') or {}).get('message') or e.get('name') or 'error')[:80])
print('ok' if 'ok' in ''.join(txt).lower() and not err else 'FAILED: ' + ('; '.join(err) or 'no reply within 120 s'))")"
    echo "  $m: ${out:-FAILED: no output}"; case "$out" in ok) ;; *) ok=0 ;; esac
  done
  rm -rf "$d"; [ "$ok" = 1 ] && echo "smoke: ok" || { echo "smoke: a model the run needs is not answering; wait and retry, or \`start card --main <model>\` with one that is"; return 1; }
}

start_opencode() {
  local kind="$1"; shift
  if [ "$kind" = loop ] && [ "${1:-}" = "--main" ]; then echo "start: loop ignores --main (card and frame models come from idea/config.json); use \`start card --main <model>\` to swap the producer"; return 2; fi
  check || return 1
  command -v opencode >/dev/null || { echo "opencode not on PATH"; return 1; }
  if [ "$kind" = card ] && [ "${1:-}" = "--main" ]; then smoke "$2" || return 1; else smoke || return 1; fi
  local before; before="$(ls -d "$EXP"/*-"$kind"* 2>/dev/null | sort)"
  ( cd "$REPO" && setsid nohup node dut/pipeline/launch.js "$NAME" "$kind" "$@" >/dev/null 2>&1 </dev/null & )
  local run=""; for _ in $(seq 1 30); do sleep 2; run="$(comm -13 <(echo "$before") <(ls -d "$EXP"/*-"$kind"* 2>/dev/null | sort) | tail -1)"; [ -n "$run" ] && break; done
  [ -n "$run" ] || { echo "start: no run folder appeared in 60 s"; return 1; }
  local pid; pid="$(pgrep -f "launch.js $NAME $kind" | head -1)"
  echo "$(date -u +%FT%TZ) start $kind $(basename "$run") pid ${pid:-?} args: $*" >> "$EXP/RUNS.txt"
  printf '\n## Run\n\n%s · kind %s · %s\n' "$(basename "$run")" "$kind" "$(date -u +%F)" >> "$EXP/QUESTION.md"
  echo "started: $(basename "$run") (pid ${pid:-?}); monitor with: bash $EXP/blind.sh status"
}

status_opencode() {
  local run="$1"; echo "== $(basename "$run")"
  if pgrep -f "launch.js $NAME" >/dev/null 2>&1 || pgrep -f "$run/pipeline" >/dev/null 2>&1; then echo "  process: running"; else echo "  process: none"; fi
  if [ -f "$run/console.log" ]; then
    local ex; ex="$(grep -o '^\[exit [0-9]*\]' "$run/console.log" | tail -1)"
    echo "  console.log: $(wc -c < "$run/console.log") bytes, last write $(( ($(date +%s) - $(stat -c %Y "$run/console.log")) / 60 )) min ago${ex:+, $ex}"
  fi
  $PY - "$run" <<'PYEOF'
import json, os, sys, glob
run = sys.argv[1]
cut = lambda e: (e or "").split(":")[0][:50]
for sj in sorted(glob.glob(os.path.join(run, "**", "status.json"), recursive=True)):
    s = json.load(open(sj)); rel = os.path.relpath(os.path.dirname(sj), run)
    print("  [%s] stage %s%s · $%.4f · %s tokens" % (rel, s.get("stage"), " (done)" if s.get("done") else "", s.get("cost_usd", 0), format(s.get("tokens", 0), ",")))
    for c in s.get("calls", []):
        err = "; ".join(cut(e) for e in (c.get("errors") or []))
        print("    %-8s %-42s %-28s %5.1f min  $%.4f%s%s" % (c.get("state"), c.get("id", "")[:42], c.get("model", "")[:28], (c.get("ms") or 0) / 60000, c.get("cost_usd") or 0,
              "  (%d attempts)" % c["attempts"] if (c.get("attempts") or 1) > 1 else "", "  " + err if err else ""))
    if s.get("best"): b = s["best"]; print("    frame best: fit %s change %s new %s sum %s/15" % (b.get("fit"), b.get("change"), b.get("new"), b.get("sum")))
    if s.get("error"): print("    error: " + cut(s["error"]))
for lj in sorted(glob.glob(os.path.join(run, "**", "ledger.jsonl"), recursive=True)):
    rows = [json.loads(l) for l in open(lj) if l.strip()]
    print("  [%s] %d loop call(s)" % (os.path.relpath(lj, run), len(rows)))
    for r in rows: print("    %-28s %-28s attempt %s  %5.1f min  $%.4f%s" % (r.get("name", "")[:28], r.get("model", "")[:28], r.get("attempt"), (r.get("ms") or 0) / 60000, r.get("cost_usd") or 0, "  " + "; ".join(cut(e) for e in r.get("errors") or []) if r.get("errors") else ""))
for lj in glob.glob(os.path.join(run, "out", "loop.json")):
    d = json.load(open(lj))
    if d.get("expanded"): print("  loop: expanded from a thin seed (framer %s), %d options screened" % (d["expanded"].get("verdict"), len(d["expanded"].get("screen") or [])))
    for s in d.get("screen") or []: print("  loop screen: option %s total %s reshape %s" % (s.get("id"), s.get("total"), s.get("reshape")))
    for r in d.get("rounds") or []: print("  loop %s: card %s · critic %s/25 %s · judged %s" % (r.get("tag"), r.get("verdict"), r.get("critic_sum"), json.dumps(r.get("critic")), r.get("judged")))
    print("  loop: chosen variant %s · loop calls $%.4f" % (d.get("chosen"), d.get("loop_calls_cost_usd") or 0))
PYEOF
  result_tables "$run"
}

# ---------- shared ----------
result_tables() {   # every RESULT.md under the run: header counts and the table without its title column
  $PY - "$1" <<'PYEOF'
import os, sys, glob
run = sys.argv[1]
for rm in sorted(glob.glob(os.path.join(run, "**", "RESULT.md"), recursive=True)):
    lines = open(rm).read().split("\n"); rel = os.path.relpath(rm, run)
    print("  [%s] %s" % (rel, next((l for l in lines if l.startswith("Picks ")), "")))
    for l in [l for l in lines if l.startswith("| [") or l.startswith("| Pick ")]: print("    |" + "|".join(l.split("|")[2:]))
PYEOF
}

runs() { ls -d "$EXP"/*-claude* "$EXP"/*-loop* "$EXP"/*-card* 2>/dev/null | sort; }
status_run() { if [ -f "$1/session_id" ]; then status_claude "$1"; else status_opencode "$1"; fi; }
status() {
  if [ -n "${1:-}" ]; then status_run "$1"; return; fi
  local any=0 r; for r in $(runs); do any=1; status_run "$r"; done
  [ "$any" = 1 ] || echo "no runs yet under $EXP"
}
wait_run() {
  local run="${1:-$(runs | tail -1)}"; [ -n "$run" ] || { echo "no run"; return 1; }
  if [ -f "$run/session_id" ]; then
    local sid; sid="$(cat "$run/session_id")"
    until [ -s "$run/operator.out" ] || ! pgrep -f "session-id $sid" >/dev/null 2>&1; do sleep 60; done
    [ -s "$run/operator.out" ] && echo "$(basename "$run"): operator finished" || echo "$(basename "$run"): operator gone without output"
  else
    until [ -f "$run/console.log" ] && grep -q '^\[exit [0-9]*\]' "$run/console.log"; do sleep 60; done
    echo "$(basename "$run") $(grep -o '^\[exit [0-9]*\]' "$run/console.log" | tail -1)"
  fi
}

case "${1:-}" in
  check) check ;;
  smoke) shift; smoke "$@" ;;
  start) shift; case "${1:-claude}" in claude) shift || true; start_claude "$@" ;; loop|card) start_opencode "$@" ;; --dry-run|--model) start_claude "$@" ;; *) echo "kind must be claude, loop or card"; exit 2 ;; esac ;;
  status) shift; status "$@" ;;
  wait) shift; wait_run "$@" ;;
  *) sed -n '2,16p' "$0"; exit 2 ;;
esac
