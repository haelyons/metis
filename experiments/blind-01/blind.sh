#!/usr/bin/env bash
# Blind run of one metis idea. The owner fills QUESTION.md and seed.json; the operator never reads them, never reads
# console.log, RESULT.md, loop.md, prompts or replies, and uses only `status` (metadata: call ids, models, states,
# minutes, dollars, attempts, error kinds, PASS/REJECT and scores). Content fields are never printed here.
#
#   bash blind.sh check              seed.json and QUESTION.md are filled and well-formed; node and opencode present
#   bash blind.sh smoke              one-word call to each model the run needs (producer, framer); ok or the error kind
#   bash blind.sh start [loop|card] [--main provider/model]
#                                    launches detached: loop (default; a seed with compute_open "not given" is expanded
#                                    by the pipeline's framer and widener, then card, frame check, variants) or card
#   bash blind.sh status [run dir]    redacted progress of every run under this experiment (or one run dir)
#   bash blind.sh wait [run dir]      blocks until the latest run's console.log has its [exit N] line; prints the code
set -u
EXP="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; NAME="$(basename "$EXP")"; REPO="$(cd "$EXP/../.." && pwd)"
PY="python3 -I"

check() {
  local ok=1
  command -v node >/dev/null || { echo "node not on PATH"; ok=0; }
  command -v opencode >/dev/null || { echo "opencode not on PATH"; ok=0; }
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
    "given" if isinstance(s.get("compute_open"), str) and "not given" not in s["compute_open"].lower() else "not given (loop will expand it)", len(s.get("source_urls") or [])))
if bad: print("seed.json: " + "; ".join(bad)); sys.exit(1)
PYEOF
  [ "$ok" = 1 ] && echo "check: ok" || { echo "check: not ready"; return 1; }
}

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

start() {
  local kind="${1:-loop}"; shift || true
  case "$kind" in loop|card) ;; --main) set -- "$kind" "$@"; kind=loop ;; *) echo "kind must be loop or card"; return 2 ;; esac
  if [ "$kind" = loop ] && [ "${1:-}" = "--main" ]; then echo "start: loop ignores --main (card and frame models come from idea/config.json); use \`start card --main <model>\` to swap the producer"; return 2; fi
  check || return 1
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

status_run() {
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
for rm in sorted(glob.glob(os.path.join(run, "**", "RESULT.md"), recursive=True)):
    lines = open(rm).read().split("\n"); rel = os.path.relpath(rm, run)
    head = next((l for l in lines if l.startswith("Picks ")), "")
    print("  [%s] %s" % (rel, head))
    rows = [l for l in lines if l.startswith("| [") or l.startswith("| Pick ")]
    for l in rows: print("    |" + "|".join(l.split("|")[2:]))   # drop the title column
for lj in glob.glob(os.path.join(run, "out", "loop.json")):
    d = json.load(open(lj))
    if d.get("expanded"): print("  loop: expanded from a thin seed (framer %s), %d options screened" % (d["expanded"].get("verdict"), len(d["expanded"].get("screen") or [])))
    for s in d.get("screen") or []: print("  loop screen: option %s total %s reshape %s" % (s.get("id"), s.get("total"), s.get("reshape")))
    for r in d.get("rounds") or []: print("  loop %s: card %s · critic %s/25 %s · judged %s" % (r.get("tag"), r.get("verdict"), r.get("critic_sum"), json.dumps(r.get("critic")), r.get("judged")))
    print("  loop: chosen variant %s · loop calls $%.4f" % (d.get("chosen"), d.get("loop_calls_cost_usd") or 0))
PYEOF
}

status() {
  if [ -n "${1:-}" ]; then status_run "$1"; return; fi
  local any=0; for r in "$EXP"/*-loop* "$EXP"/*-card*; do [ -d "$r" ] || continue; any=1; status_run "$r"; done
  [ "$any" = 1 ] || echo "no runs yet under $EXP"
}

wait_run() {
  local run="${1:-$(ls -d "$EXP"/*-loop* "$EXP"/*-card* 2>/dev/null | sort | tail -1)}"
  [ -n "$run" ] || { echo "no run"; return 1; }
  until [ -f "$run/console.log" ] && grep -q '^\[exit [0-9]*\]' "$run/console.log"; do sleep 60; done
  echo "$(basename "$run") $(grep -o '^\[exit [0-9]*\]' "$run/console.log" | tail -1)"
}

case "${1:-}" in
  check) check ;; smoke) shift; smoke "$@" ;; start) shift; start "$@" ;; status) shift; status "$@" ;; wait) shift; wait_run "$@" ;;
  *) sed -n '2,12p' "$0"; exit 2 ;;
esac
