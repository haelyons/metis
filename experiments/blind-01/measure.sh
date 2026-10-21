#!/usr/bin/env bash
# measure.sh: blind operation of one latent_skeptic measure run (blind-01, 2026-10-21).
# The operator (a Claude Code session) runs only these commands and reads only what they print: states, counts, sizes,
# hashes, exit codes, masked labels. Every role that reads the card's content is a headless sonnet session (claude -p with
# its own instruction file under sessions/) or a workflow agent pinned inside the committed scripts.
#
#   usage: bash measure.sh <command> <measure dir> [options]
#   prepare [--pin sonnet]  copy dut/latent_skeptic + latent_skeptic/frozen read-only, the triage-* roles, the keys link,
#                           the design args; --pin sonnet rewrites model: 'opus' -> 'sonnet' in the copies (recorded)
#   design [--via wf ...]   headless operator: Workflow pipeline.js mode design  -> out/design_record.json; with --via wf the
#                           stage runs on dut/pipeline wf.js (OpenCode and Claude families with understudies; flags
#                           --family, --mode, --on-refusal pass through) under out/wf-<stage>-<stamp>/
#   gate [--addendum <f>] [--via wf ...]   headless gate writer (read/write tools only): GATE_COMMIT.md + EXEC_NOTE.md; --via wf runs
#                           the same instruction file as one agent() call on wf.js (measure/prompt_stage.js, role ls-writer)
#   build [--keep]          headless operator: Workflow mode build -> run_<tag>.py onbox_<tag>.sh; then bash -n,
#                           (--keep leaves the previous build's files in place for a directive that asks for edits)
#                           py_compile, the selftest to a log, hashes
#   review [--via wf ...]   headless reviewer (read/write tools only): checklist -> out/review_build<N>.{md,json}; --via wf as for gate
#   launcher                lambda_run_<tag>.sh + remote_run_<tag>.sh from m3's per-launch copies, declared points only
#   tests [--via wf flags]  claim-blind author writes tests/tests_<tag>.py from the directive and contract (builder never sees it)
#   fix --fs <name> [--via wf flags]  bounded fixer on a held box (HOLD marker): env and glue only, git commits on the box, verifier after
#   envbuild --fs <name>    build the environment of record once on a box onto the named filesystem (measure/env_build.sh):
#                           pins and apt lists of record as data; hold-open for a fixer on failure; results_env/out/env_report.json
#   launch [--type T --region R --timeout S --budget B --price P]   preflight, capacity, then the launcher detached
#   score                   results_<tag>/out records -> out/PREDICTIONS_SCORED.md + LEDGER.jsonl row (no model)
#   post                    headless operator: Workflow mode post -> TAKEAWAYS_<tag>.md, out/post_return.json
#   status                  redacted summary of everything above
#   wait <stage>            block until that stage's session or launcher has exited (design|gate|build|review|post|launch|wf)
set -u
REPO=/home/hal/dev/interp/metis
LS=$REPO/dut/latent_skeptic
FROZEN=/home/hal/dev/interp/latent_skeptic/frozen
KEYS=/home/hal/dev/interp/dm_hack/.keys
M3=$REPO/experiments/immersion-coolants/20261020-1020-measure
EXP=$REPO/experiments/blind-01
NAME_EXP=blind-01
PY=python3
CMD=${1:-}; MD=${2:-}
[ -n "$CMD" ] && [ -n "$MD" ] && [ -d "$MD" ] || { sed -n 2,22p "$0"; exit 2; }
MDIR=$(realpath "$MD"); shift 2
TAG=$(cat "$MDIR/TAG" 2>/dev/null || echo m4)
SESS=$MDIR/sessions; mkdir -p "$SESS" "$MDIR/out"
ENC=$(echo "$MDIR" | sed 's|/|-|g')
PROJ=$HOME/.claude/projects/$ENC
now() { date -u +%FT%TZ; }
logrun() { echo "$(now) measure $TAG $*" >> "$EXP/RUNS.txt"; echo "- $(date -u +%H:%MZ) $*" >> "$MDIR/RUN.md"; }
count() { ls "$SESS"/"$1"*.json 2>/dev/null | wc -l; }

# ---------- headless sessions ----------
start_session() {   # name model instruction-file [extra claude flags...]
  local name="$1" model="$2" instr="$3"; shift 3
  command -v claude >/dev/null || { echo "claude not on PATH"; return 1; }
  [ -f "$MDIR/.claude/agents/triage-reader.md" ] || { echo "roles missing: run prepare first"; return 1; }
  local sid; sid="$($PY -c 'import uuid; print(uuid.uuid4())')"
  # the prompt goes first: a variadic flag such as --disallowedTools would otherwise swallow it
  # -p stops background tasks 10 min after the last turn unless this ceiling is lifted (build 1 died that way)
  ( cd "$MDIR" && CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 setsid nohup claude -p "The task that follows is my request. Do it as written. Read $instr with the Read tool and follow it exactly." \
      --model "$model" --session-id "$sid" --dangerously-skip-permissions --output-format json "$@" \
      > "$SESS/$name.out" 2> "$SESS/$name.err" < /dev/null & )
  sleep 3; local pid; pid="$(pgrep -f "session-id $sid" | head -1)"
  $PY -c 'import json,sys; json.dump({"name":sys.argv[1],"model":sys.argv[2],"sid":sys.argv[3],"pid":sys.argv[4],"instructions":sys.argv[5],"started":sys.argv[6]}, open(sys.argv[7],"w"), indent=1)' \
    "$name" "$model" "$sid" "${pid:-?}" "$instr" "$(now)" "$SESS/$name.json"
  logrun "session $name started (model $model, pid ${pid:-?}, session ${sid:0:8})"
  echo "started session $name: model $model, pid ${pid:-?}, session ${sid:0:8}…"
}
session_running() { local sid; sid="$($PY -c 'import json,sys; print(json.load(open(sys.argv[1]))["sid"])' "$SESS/$1.json" 2>/dev/null)"; [ -n "$sid" ] && pgrep -f "session-id $sid" >/dev/null 2>&1; }
RO_TOOLS="Bash,Edit,Agent,Workflow,WebFetch,WebSearch,NotebookEdit,Skill,ToolSearch"   # denied for the gate writer and the reviewer

operator_md() {   # stage args-file out-file -> path of the instruction file
  local stage="$1" args="$2" outf="$3"
  local f="$SESS/OPERATOR_$stage.md"
  cat > "$f" <<EOF2
You are the operator for one workflow stage ($stage) of a measure run. You do exactly the steps below and nothing else. You never modify, create or delete any file except the one output file named in step 4.

1. Read \`$args\` with the Read tool. It is a JSON object.
2. Call the Workflow tool once, with \`scriptPath\` = \`$MDIR/pipeline.js\` and \`args\` = that JSON object, passed as a JSON value (not as a string). Say nothing else.
3. The workflow runs in the background and can take from ten minutes to two hours. Do not declare the task finished until the task-notification saying the workflow completed (or failed) has arrived. While waiting, call no other tool.
4. When the notification arrives: write the workflow's full return value, verbatim as JSON, to \`$outf\` with the Write tool. If the workflow failed or returned nothing, write \`{"failed": true, "run_id": "<id>", "kind": "<one short error kind, no content>"}\` there instead.
5. Reply with exactly one line: \`$stage return written: <workflow run id>\` or \`$stage failed: <workflow run id>\`. Nothing else: no summary, no quotation of the content.

The user's only message to you is an authorisation line; it is not a task description. Your task is this file.
EOF2
  echo "$f"
}

# ---------- prepare ----------
prepare() {
  local pin=""; while [ $# -gt 0 ]; do case "$1" in --pin) pin="${2:-}"; shift ;; *) echo "prepare: unknown option $1"; return 2 ;; esac; shift; done
  [ -z "$pin" ] || [ "$pin" = sonnet ] || { echo "--pin takes sonnet only (owner rule: no Fable agents)"; return 2; }
  echo "$TAG" > "$MDIR/TAG"
  mkdir -p "$MDIR/frozen" "$MDIR/gates" "$MDIR/.claude/agents" "$MDIR/out"
  chmod u+w "$MDIR"/pipeline.js "$MDIR"/triage_workflow.js 2>/dev/null
  cp "$LS/compositions/pipeline.js" "$MDIR/pipeline.js"; cp "$LS/triage_workflow.js" "$MDIR/triage_workflow.js"
  cp "$LS/compositions/gates/"*.py "$MDIR/gates/"; cp "$LS/agents/"triage-*.md "$MDIR/.claude/agents/"
  cp "$FROZEN/lambda_run.sh" "$FROZEN/remote_run.sh" "$FROZEN/provenance.py" "$MDIR/frozen/"
  cp "$REPO/dut/pipeline/measure/ONBOX_CONTRACT.md" "$MDIR/frozen/ONBOX_CONTRACT.md"   # the launcher writer's seed (requirements, not code)
  local subs=0
  if [ "$pin" = sonnet ]; then
    subs=$(grep -o "model: 'opus'" "$MDIR/pipeline.js" "$MDIR/triage_workflow.js" | wc -l)
    sed -i "s/model: 'opus'/model: 'sonnet'/g" "$MDIR/pipeline.js" "$MDIR/triage_workflow.js"
  fi
  chmod 444 "$MDIR"/pipeline.js "$MDIR"/triage_workflow.js "$MDIR"/frozen/* "$MDIR"/gates/*
  ln -sfn "$KEYS" "$MDIR/.keys"; git -C "$REPO" check-ignore -q "$MDIR/.keys" || { echo "FATAL: .keys link not ignored by git"; return 1; }
  ( cd "$MDIR" && sha256sum pipeline.js triage_workflow.js gates/*.py frozen/* .claude/agents/*.md > out/PIPELINE_HASHES.txt )
  local same; same=$(cd "$LS" && sha256sum compositions/pipeline.js triage_workflow.js | awk '{print $1}' | sort | tr '\n' ' ')
  local mine; mine=$(cd "$MDIR" && sha256sum pipeline.js triage_workflow.js | awk '{print $1}' | sort | tr '\n' ' ')
  local ident="identical to dut/latent_skeptic $(git -C "$REPO" rev-parse --short HEAD)"; [ "$same" = "$mine" ] || ident="DIFFER from dut/latent_skeptic ($subs opus->sonnet substitutions)"
  # design args: the compiled question is the seed; the substrate note carries the owner's rules
  $PY - "$MDIR" "$TAG" <<'PYEOF'
import json, sys
m, tag = sys.argv[1:3]
seed = open(f"{m}/QUESTION.md").read()
note = ("One rented Lambda GPU box: gpu_1x_a100_sxm4 (A100 SXM4 40 GB, 30 vCPU, USD 1.99/h) in us-east-1 if it has capacity, else the cheapest single GPU with capacity (recorded). "
        "Image: Ubuntu 22.04, CUDA 12.8, driver 570, python 3.10 with torch 2.7 preinstalled; anything else is installed by the on-box script inside the time cap. "
        "Hard cost cap USD 10 for the whole run, at most two launches, REMOTE_TIMEOUT at most 7,200 s per launch. "
        "Measure the inputs on the card's own protocol; no production phase; anchor first. State every hardware and cost assumption as GUESS.")
json.dump({"mode": "design", "seed": seed, "triage_path": f"{m}/triage_workflow.js", "substrate_note": note, "cap_usd": 10}, open(f"{m}/out/design_args.json", "w"), indent=1)
print("out/design_args.json: seed %d chars, cap_usd 10" % len(seed))
PYEOF
  grep -q "^## Blind operation" "$MDIR/RUN.md" || cat >> "$MDIR/RUN.md" <<EOF2

## Blind operation (measure.sh, tag $TAG)

Operator: the Claude Code session that runs \`experiments/blind-01/measure.sh\` and reads only its redacted output. Content-bearing roles: stage operators, the gate writer and the launch reviewer are headless sonnet sessions (\`sessions/\`); workflow agents keep the pins in the committed scripts. The human gate is delegated to the gate writer under the owner's standing rules (in \`sessions/GATE_*.md\`); the build's gatecheck verifies its coverage.
Pipeline copies: pipeline.js, triage_workflow.js, gates/, frozen/ (latent_skeptic/frozen), .claude/agents/triage-*.md; hashes in out/PIPELINE_HASHES.txt; $ident.
Transcripts: $PROJ/<session>/subagents/workflows/<run>/.

### Log
EOF2
  logrun "prepare: pipeline copies $ident; roles 3; keys linked; design args written"
  echo "prepared $MDIR: tag $TAG; pipeline copies $ident; roles $(ls "$MDIR/.claude/agents" | wc -l); gates $(ls "$MDIR/gates" | wc -l); frozen $(ls "$MDIR/frozen" | wc -l)"
}

# ---------- a stage on wf.js (both model families, understudies; dut/pipeline/launch.js stage) ----------
# measure.sh <design|build|post> <dir> --via wf [--family opencode|claude] [--mode fallback|shadow|swap|primary-only] [--on-refusal halt|understudy]
via_wf() {   # stage [flags...]
  local stage="$1"; shift
  local n; n=$(ls "$MDIR/out"/wf-"$stage"-* -d 2>/dev/null | wc -l); n=$((n+1))
  local ref=""; for a in "$@"; do [ "$a" = understudy ] && ref=" (refusals handed to the understudy: owner's explicit choice)"; done
  ( cd "$REPO" && setsid nohup node dut/pipeline/launch.js "$NAME_EXP" stage --measure "$MDIR" --stage "$stage" "$@" > "$SESS/wf-$stage$n.out" 2>&1 < /dev/null & )
  sleep 4; local pid; pid="$(pgrep -f "wf.js --script .* --args $MDIR/out/wf-" | head -1)"
  logrun "stage $stage on wf.js run $n: flags [$*]$ref, pid ${pid:-?}"
  echo "started $stage on wf.js (run $n, pid ${pid:-?}); flags: $*"
}
wf_running() { pgrep -f "wf.js --script .* --args $MDIR/out/wf-" >/dev/null 2>&1; }   # pipeline.js or prompt_stage.js: match on the run folder
pop_via() {   # splits "--via wf <flags>" out of "$@": sets VIA and REST
  VIA=""; REST=(); REST_WF=()
  while [ $# -gt 0 ]; do case "$1" in --via) VIA="$2"; shift ;; *) REST+=("$1") ;; esac; shift; done
}

# ---------- design ----------
design() {
  [ -f "$MDIR/out/design_args.json" ] || { echo "run prepare first"; return 1; }
  pop_via "$@"; if [ "$VIA" = wf ]; then via_wf design "${REST[@]}"; return; fi
  local n; n=$(count design); n=$((n+1)); local name="design$n"
  local f; f=$(operator_md "design" "$MDIR/out/design_args.json" "$MDIR/out/design_record.json")
  start_session "$name" sonnet "$f"
}

# ---------- gate ----------
gate() {
  pop_via "$@"; set -- "${REST[@]}"
  local add=""; while [ $# -gt 0 ]; do case "$1" in --addendum) add="$(realpath "${2:-}")"; shift ;; --family|--mode|--on-refusal) REST_WF+=("$1" "$2"); shift ;; *) echo "gate: unknown option $1"; return 2 ;; esac; shift; done
  REST=("${REST_WF[@]}")
  [ -s "$MDIR/out/design_record.json" ] || { echo "no out/design_record.json yet"; return 1; }
  local n; n=$(( $(count gate) + $(ls "$MDIR/out"/gate*_args.json 2>/dev/null | wc -l) + 1 )); local name="gate$n" f="$SESS/GATE_$n.md"
  local mode="first"; [ -n "$add" ] && mode="addendum"
  cat > "$f" <<EOF2
You are the gate for one measure run (tag $TAG) of the metis pipeline, standing in for the owner, who delegated this human role to you under the standing rules below. You write exactly two files in \`$MDIR\`: \`GATE_COMMIT.md\` and \`EXEC_NOTE.md\`. You write nothing else, edit nothing else, and run nothing.

## What this run is

Read, in this order, with the Read tool:
1. \`$MDIR/QUESTION.md\`: the measurement question compiled from a card: which of the card's load-bearing inputs are unmeasured, on what protocol, with what gate, anchor and bands.
2. \`$MDIR/CARD.json\`: the card's calibration record (inputs, measuring phase, anchor, predictions, plan cost).
3. \`$MDIR/out/design_record.json\`: the design workflow's return value. \`design\` is the typed design the build will implement as its spec; \`diff.departures\` are the questions the diff agent raised; \`triage\` holds the reader's grounding verdicts, the skeptics' cruxes and the run, author, instrument and shared queues; \`gate\` is the gate text. If it carries \`halt\` or \`error\` instead, write both files as a halt record (decision section first) and stop.
4. Shape examples from an earlier, unrelated run (another experiment: use only their structure, never their content): \`$M3/GATE_COMMIT.md\` and \`$M3/EXEC_NOTE.md\`.
$([ -n "$add" ] && echo "5. The report this addendum rules on: \`$add\`. Also read the current \`$MDIR/GATE_COMMIT.md\` and \`$MDIR/EXEC_NOTE.md\`, which you will extend, not rewrite.")

## Standing rules (owner, 2026-10-20 and 21; binding)

1. Budget: hard cap USD 10 of box time for the whole run (the owner's calibration rule; the operator records the spend of every launch and launches until the cap is reached, no fixed count); \`BUDGET_LEFT_USD\` per launch = the lesser of 5 and what remains of the cap; \`gpu_1x_a100_sxm4\` (A100 SXM4 40 GB, USD 1.99/h) in us-east-1 if it has capacity, else the cheapest single GPU with capacity (the operator records which). If the design's budget exceeds the cap, shorten the protocol to fit as a ruling of record (fewer steps, fewer repeats, one cell), never drop an input silently; if it cannot fit, decide HALT and say what it would cost.
2. Time: set \`REMOTE_TIMEOUT\` (at most 7,200 s per launch). \`onbox_$TAG.sh\` reads \`PRICE_USD_PER_HOUR\`, \`BUDGET_LEFT_USD\` and \`REMOTE_TIMEOUT\` from its environment and stops cleanly, writing a void record, before exceeding them.
3. Scope: measure the inputs on the card's own protocol; no production phase; anchor first, and a missed anchor voids the inputs (run_valid=false propagates to every later record).
4. Box: Ubuntu 22.04, CUDA 12.8, driver 570, python 3.10, torch 2.7 preinstalled; anything else is installed by \`onbox_$TAG.sh\` inside the time cap. Broken infrastructure: exit non-zero with a void record; never patch around.
5. Files: the build writes exactly \`run_$TAG.py\` and \`onbox_$TAG.sh\` in \`$MDIR\` (absolute path) and reads the design record and \`frozen/\` (provenance.py is the record writer; lambda_run.sh and remote_run.sh show what the box does; \`frozen/ONBOX_CONTRACT.md\` is the binding execution contract: its stage order, guards, record fields, selftest contract and failure checks are directive items unless you tighten them). Payload shipped to the box: \`run_$TAG.py onbox_$TAG.sh remote_run_$TAG.sh frozen/provenance.py\` and \`data/\` recursively if it exists, all under \`~/${TAG}_run/\`; results under \`~/${TAG}_run/results_$TAG/out/\`, which the launcher fetches. Nothing else is on the box.
6. Records, so a script can score them without a model: for each input C1..Cn of QUESTION.md one provenance.py record \`results_$TAG/out/endpoint-C<i>_tag-$TAG.json\` whose \`values\` carries \`measured\` (a number in the card's unit), \`unit\`, \`card_value\` and \`band\` ([lo, hi] from QUESTION.md), and whose \`decision\` is PASS, FAIL or VOID against that band; \`run_valid\` in every record; an anchor record \`endpoint-anchor_tag-$TAG.json\` (values: measured, published, tolerance); \`RUN_VALID.json\`; \`${TAG}_summary.json\`; raw rows as JSON lines.
7. Selftest: \`python3 run_$TAG.py --selftest\`, stdlib only, no GPU, no network, under 300 s; prints \`selftest: N of M checks passed\` then exactly \`selftest: PASS\` or \`selftest: FAIL\` as its last line; non-zero exit on FAIL. Planted cases for every parser and for the gate-failure (void) path.
8. Secrets: nothing reads \`.keys\`; nothing prints its environment; \`HF_TOKEN\` is used by downloads only.
9. Labels: every measured record carries instance type, GPU name and driver, engine version and build flags, wall-clock.
10. Nothing interactive; \`sudo\` only for declared apt packages; downloads only from sources the design names, URL and hash recorded; the on-box command the build returns is one line the operator runs verbatim through \`remote_run_$TAG.sh\`.

## Directive form (owner ruling 2026-10-21)

EXEC_NOTE.md is the current truth, not a changelog: in addendum mode REGENERATE it as one bounded directive of at most 40 numbered items, required-for-launch items first (each marked REQUIRED FOR LAUNCH or REPORTING ONLY), with every superseded or satisfied item removed; the history of rulings stays in GATE_COMMIT.md. Three standing changes of record: (i) the Python environment is an artifact, built once from the pins of record by the operator's env_build on a Lambda filesystem and recorded by its lock file hash in out/env_report.json; the on-box script activates that environment and verifies the lock hash instead of installing; pins live in the environment record, not in the runner; (ii) implementer selftests are not required and not credited: tests of the measurement logic are written by a separate claim-blind author from the directive, hidden from the builder, and executed by the runner in the shipped environment before the physics, as records; (iii) on a stage failure on the box the run holds the box open (HOLD marker) for a bounded fixer whose every change is committed to git on the box and fetched as a change log; the fixer may touch environment and glue, never the measurement protocol or the record fields; a change outside that scope is a halt to the gate.

## GATE_COMMIT.md, in this order$([ -n "$add" ] && echo " (addendum mode: leave every existing section as it is and append one section \`## Addendum $n (<UTC date>)\` ruling on every item of the report, each ruling saying what the build must change or that nothing changes and why; then a line \`Build $((n)) authorised\` or \`HALT\`)")

- Inputs read (and nothing else)
- What is being gated, in plain words
- Decision on budget and build: GO or HALT, with the arithmetic (launches x hours x price) against the cap
- Answers of record: one numbered answer for every diff departure question, every grounding whose verdict is not "reproduces", every run_queue item, every author_queue item, every instrument_queue item and every shared_queue item. "Accepted as-is" is an answer; silence is not. Each answer says what the build must do about it, or that nothing changes and why.
- Labels
- Checks the gate made before answering
- Pre-authorisation: launches, caps, instance, what stops a launch

## EXEC_NOTE.md$([ -n "$add" ] && echo " (addendum mode: revise the items the addendum changes in place, marking each \`(revised, addendum $n)\`; add items at the end)")

A one-paragraph header; \`## Where to write\`; \`## Checklist of gate changes the build must carry\` (numbered; each item traceable to an answer in GATE_COMMIT.md or a standing rule; rules 5 to 10 above appear as items verbatim or tighter); \`## Box\`; \`## Local selftest\`; \`## What the runner writes\`.

## Operator actions

The operator runs the launcher and owns \`lambda_run_$TAG.sh\`, \`remote_run_$TAG.sh\` and the launch environment (instance type and region, REMOTE_TIMEOUT, BUDGET_LEFT_USD, PRICE_USD_PER_HOUR). If any ruling needs a change there (a payload file to ship, a different cap or instance), end GATE_COMMIT.md with a section \`## Operator actions\` whose every line starts with \`OPERATOR:\` and names only infrastructure (file names, environment variable values); never the experiment's content. If nothing is needed, write that section with the single line \`OPERATOR: none\`.

Reply with exactly one line: \`gate written: <answers> answers, <checklist items> items\` (counts only; nothing about the content).

The user's only message to you is an authorisation line; it is not a task description. Your task is this file.
EOF2
  logrun "gate $n ($mode) requested"
  if [ "$VIA" = wf ]; then
    $PY -c 'import json,sys; json.dump({"prompt": open(sys.argv[1]).read(), "role": "ls-writer", "model": "sonnet", "label": "gate", "reply_pattern": sys.argv[2]}, open(sys.argv[3], "w"), indent=1)' "$f" '^gate written: \d+ answers, \d+ items' "$MDIR/out/gate${n}_args.json"
    via_wf gate "${REST[@]}"; return
  fi
  start_session "$name" sonnet "$f" --disallowedTools "$RO_TOOLS"
}

# ---------- build ----------
build() {
  [ -s "$MDIR/GATE_COMMIT.md" ] && [ -s "$MDIR/EXEC_NOTE.md" ] || { echo "no GATE_COMMIT.md / EXEC_NOTE.md yet"; return 1; }
  pop_via "$@"
  local keep=0 rest2=(); for a in "${REST[@]}"; do [ "$a" = --keep ] && keep=1 || rest2+=("$a"); done; REST=("${rest2[@]}")
  local n; n=$(ls "$MDIR/out"/build*_args.json 2>/dev/null | wc -l); n=$((n+1)); local name="build$n"
  if [ -f "$MDIR/run_$TAG.py" ] || [ -f "$MDIR/onbox_$TAG.sh" ]; then   # the previous build's files: archived, or kept in place for an incremental build (--keep)
    mkdir -p "$MDIR/out/build$((n-1))"
    if [ $keep = 1 ]; then cp -f "$MDIR/run_$TAG.py" "$MDIR/onbox_$TAG.sh" "$MDIR/out/build$((n-1))/" 2>/dev/null; echo "previous build files copied to out/build$((n-1))/ and KEPT in place (--keep)"
    else mv -f "$MDIR/run_$TAG.py" "$MDIR/onbox_$TAG.sh" "$MDIR/out/build$((n-1))/" 2>/dev/null; echo "previous build files archived under out/build$((n-1))/"; fi
  fi
  $PY - "$MDIR" "$TAG" "$n" "$keep" <<'PYEOF'
import json, sys
m, tag, n, keep = sys.argv[1:5]
note = open(f"{m}/EXEC_NOTE.md").read()
if keep == "1":   # the build contract's "two new files, edit nothing existing" is satisfied by overwriting these two paths in place
    note = (f"OPERATOR NOTE OF RECORD (in-place build): run_{tag}.py and onbox_{tag}.sh already exist in this directory from the previous build. "
            f"This build EDITS THEM IN PLACE as the directive's closing section instructs; the build contract's sentence about writing two new files and editing nothing existing is satisfied by overwriting exactly these two paths. Do not stop on that sentence.\n\n") + note
args = {"mode": "build", "design_record": f"{m}/out/design_record.json", "gate_commit": f"{m}/GATE_COMMIT.md", "tag": tag,
        "conventions": f"{m}/frozen", "exec_note": note}
json.dump(args, open(f"{m}/out/build{n}_args.json", "w"), indent=1)
print("out/build%s_args.json: exec_note %d chars" % (n, len(args["exec_note"])))
PYEOF
  if [ "$VIA" = wf ]; then via_wf build "${REST[@]}"; return; fi
  local f; f=$(operator_md "build" "$MDIR/out/build${n}_args.json" "$MDIR/out/build${n}_return.json")
  start_session "$name" sonnet "$f"
}
build_checks() {   # mechanical, after the build session or wf run exits
  local n; n=$(ls "$MDIR/out"/build*_args.json 2>/dev/null | wc -l); local log="$MDIR/out/selftest_build$n.log"
  cd "$MDIR" || return 1
  [ -f "run_$TAG.py" ] && [ -f "onbox_$TAG.sh" ] || { echo "build $n: files missing ($(ls run_$TAG.py onbox_$TAG.sh 2>&1 | grep -c 'No such') of 2)"; return 1; }
  sha256sum "run_$TAG.py" "onbox_$TAG.sh" > "out/BUILT_HASHES_build$n.txt"
  echo "build $n files: run_$TAG.py $(wc -l < run_$TAG.py) lines ($(cut -c1-12 < <(sha256sum run_$TAG.py))…), onbox_$TAG.sh $(wc -l < onbox_$TAG.sh) lines ($(cut -c1-12 < <(sha256sum onbox_$TAG.sh))…)"
  local others; others=$(git -C "$REPO" status --porcelain -- "$MDIR" | grep -vE "run_$TAG.py|onbox_$TAG.sh|/out/|/sessions/|RUN.md|GATE_COMMIT.md|EXEC_NOTE.md|TAG$|\.claude/|frozen/|gates/|pipeline.js|triage_workflow.js|\.last_lambda" | wc -l)
  echo "other files touched in the run dir: $others"
  bash -n "onbox_$TAG.sh" && echo "bash -n onbox: ok" || echo "bash -n onbox: SYNTAX ERROR"
  $PY -m py_compile "run_$TAG.py" && echo "py_compile run: ok" || echo "py_compile run: ERROR"; rm -rf __pycache__
  local rc=0
  if grep -q -- '--selftest' "run_$TAG.py"; then timeout 300 $PY "run_$TAG.py" --selftest > "$log" 2>&1; rc=$?; echo "selftest: exit $rc, $(wc -l < "$log") lines; $(grep -E '^selftest: ' "$log" | tr '\n' ';')"
  else echo "selftest: none (implementer selftests dropped by ruling); author's tests: $([ -f "tests/tests_$TAG.py" ] && { $PY -m py_compile "tests/tests_$TAG.py" && echo "tests/tests_$TAG.py compiles ($(wc -l < tests/tests_$TAG.py) lines)" || echo "tests/tests_$TAG.py DOES NOT COMPILE"; rm -rf tests/__pycache__; } || echo "no tests file")"; fi
  grep -nE "\.keys([^(]|$)|LAMBDA_KEY|HF_KEY" "run_$TAG.py" "onbox_$TAG.sh" | wc -l | sed 's/^/mentions of key files or names in the built files (dict .keys() calls excluded): /'
  $PY - "$MDIR" "$TAG" <<'PYEOF'
import re, sys
m, tag = sys.argv[1:3]
onbox = open(f"{m}/onbox_{tag}.sh").read(); run = open(f"{m}/run_{tag}.py").read()
used = set(re.findall(r"\$\{?([A-Z][A-Z0-9_]{2,})", onbox)) | set(re.findall(r"environ(?:\.get)?\s*[\[(]\s*['\"]([A-Z][A-Z0-9_]{2,})", run)) | set(re.findall(r"getenv\s*\(\s*['\"]([A-Z][A-Z0-9_]{2,})", run))
std = {"HOME", "PATH", "PWD", "USER", "SHELL", "TMPDIR", "PYTHONPATH", "LD_LIBRARY_PATH", "CUDA_VISIBLE_DEVICES", "OMP_NUM_THREADS", "HF_HOME", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "PYTORCH_CUDA_ALLOC_CONF", "LAMBDA_INSTANCE_ID", "GIT_COMMIT", "CUDA_HOME", "NVIDIA_VISIBLE_DEVICES", "LANG", "LC_ALL", "TERM", "HOSTNAME", "RUN_DONE", "SECONDS", "RANDOM", "LINENO", "BASH_SOURCE", "EUID", "UID", "PPID", "OLDPWD", "IFS", "OPTARG", "OPTIND", "PIPESTATUS", "FUNCNAME", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "TOKENIZERS_PARALLELISM", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "CUDA_LAUNCH_BLOCKING", "HF_HUB_ENABLE_HF_TRANSFER", "TORCH_HOME", "XDG_CACHE_HOME"}
try: launcher = open(f"{m}/lambda_run_{tag}.sh").read()
except FileNotFoundError: launcher = ""
fwd = set(re.findall(r"([A-Z][A-Z0-9_]{2,})=\\\"", launcher))
local_defined = set(re.findall(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]{2,})=", onbox, re.M)) | set(re.findall(r"^\s*(?:local\s+)?([A-Z][A-Z0-9_]{2,})=", onbox, re.M))
missing = sorted(v for v in used - std - fwd - local_defined if not v.startswith(("BASH", "SHLVL")))
print("env read on-box: %d names; forwarded by the launcher: %s; read on-box but neither forwarded nor set there: %s" % (len(used), ",".join(sorted(fwd - {"HF_TOKEN", "LAMBDA_INSTANCE_ID", "GIT_COMMIT"})) or "-", ",".join(missing) or "none"))
PYEOF
  $PY - "$MDIR/out/build${n}_return.json" <<'PYEOF'
import json, sys
try: d = json.load(open(sys.argv[1]))
except Exception as e: print("build return: unreadable (%s)" % type(e).__name__); sys.exit()
if d.get("failed"): print("build return: FAILED kind=%s" % d.get("kind")); sys.exit()
if d.get("halt"): print("build return: HALT %s, unanswered %d" % (d["halt"], len(d.get("unanswered") or []))); sys.exit()
gc = d.get("gatecheck") or {}; b = d.get("built") or {}
print("build return: gatecheck answered %s, unanswered %d; built keys %s; onbox_command %d chars; expected %d chars" % (gc.get("answered"), len(gc.get("unanswered") or []), sorted(b.keys()), len(b.get("onbox_command") or ""), len(b.get("expected") or "")))
PYEOF
  logrun "build $n checks: selftest exit $rc"
}

# ---------- review ----------
review() {
  pop_via "$@"
  local n; n=$(ls "$MDIR/out"/build*_args.json 2>/dev/null | wc -l); [ "$n" -ge 1 ] && [ -f "$MDIR/run_$TAG.py" ] || { echo "nothing built"; return 1; }
  local r; r=$(( $(count review) + $(ls "$MDIR/out"/review*_args.json 2>/dev/null | wc -l) + 1 )); local name="review$r" f="$SESS/REVIEW_$r.md"
  [ -f "$MDIR/lambda_run_$TAG.sh" ] || { echo "run launcher first (the reviewer checks the launcher copy)"; return 1; }
  cat > "$f" <<EOF2
You review the execution layer of one measure run (tag $TAG) before it spends money. You run nothing and edit nothing. You write exactly two files: \`$MDIR/out/review_build$n.md\` (findings, numbered; each names the file and line, the EXEC_NOTE item or standing rule it concerns, and BLOCKING or ADVISORY) and \`$MDIR/out/review_build$n.json\` (\`{"verdict": "PASS" or "FAIL", "blocking": n, "advisory": n}\`; FAIL if any finding is blocking).

Read with the Read tool: \`$MDIR/out/operator_findings_build$n.txt\` if it exists (the operator's mechanical findings: environment names read on-box that nothing forwards or sets, files touched; verify each); \`$MDIR/EXEC_NOTE.md\`; \`$MDIR/GATE_COMMIT.md\` (the Pre-authorisation section and the latest addendum); \`$MDIR/run_$TAG.py\`; \`$MDIR/onbox_$TAG.sh\`; \`$MDIR/lambda_run_$TAG.sh\`; \`$MDIR/remote_run_$TAG.sh\`; \`$MDIR/frozen/lambda_run.sh\`; \`$MDIR/frozen/remote_run.sh\`; \`$MDIR/frozen/provenance.py\`; \`$MDIR/frozen/ONBOX_CONTRACT.md\` (binding through standing rule 5; a contract item the directive does not carry is ADVISORY unless it would spend money without a valid record); \`$MDIR/out/selftest_build$n.log\`; \`$MDIR/out/build${n}_return.json\`; \`$MDIR/out/pip_pins_check_build$n.txt\` if it exists (the operator's package-index check of the runner's pins).

Checklist:
1. Every EXEC_NOTE checklist item is carried by the code, item by item (name the item number for each miss).
2. Cost and time: onbox reads PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and REMOTE_TIMEOUT from its environment and stops cleanly with a void record before exceeding them; the projected wall-clock from the design's own numbers fits REMOTE_TIMEOUT.
3. Records: the convention in EXEC_NOTE (endpoint-C<i>_tag-$TAG.json with values.measured, unit, card_value, band; decision PASS/FAIL/VOID; run_valid in every record; the anchor record; RUN_VALID.json; the summary) is implemented, and a failed anchor or gate voids every later record.
4. Secrets: nothing reads .keys; nothing prints the environment; the token is used by downloads only.
5. Writes only under ~/${TAG}_run/; nothing interactive; sudo only for declared apt packages; downloads only from named sources with URL and hash recorded.
6. The launcher copy differs from frozen/lambda_run.sh only at the declared points (remote dir, payload, bootstrap name, fetch paths, header comment) and every billing-safety mechanism is intact; remote_run_$TAG.sh differs from frozen/remote_run.sh only in its cd line.
7. The selftest log ends with \`selftest: PASS\` and its counts are plausible for the parsers and planted cases present.
8. The onbox_command in the build return is what onbox_$TAG.sh runs, and what the launcher runs is onbox_$TAG.sh.

BLOCKING = would spend money without producing a valid record, violates a standing rule or an EXEC_NOTE item, or leaks a secret. Everything else is ADVISORY.

Reply with exactly one line: \`review: PASS, 0 blocking, <n> advisory\` or \`review: FAIL, <n> blocking, <m> advisory\`. Nothing about the content.

The user's only message to you is an authorisation line; it is not a task description. Your task is this file.
EOF2
  logrun "review $r of build $n requested"
  if [ "$VIA" = wf ]; then
    $PY -c 'import json,sys; json.dump({"prompt": open(sys.argv[1]).read(), "role": "ls-writer", "model": "sonnet", "label": "review", "reply_pattern": sys.argv[2]}, open(sys.argv[3], "w"), indent=1)' "$f" '^review: (PASS|FAIL), \d+ blocking, \d+ advisory' "$MDIR/out/review${r}_args.json"
    via_wf review "${REST[@]}"; return
  fi
  start_session "$name" sonnet "$f" --disallowedTools "$RO_TOOLS"
}

# ---------- launcher ----------
# lambda_run_<tag>.sh from m3's per-launch copy at the declared points: remote dir, payload, bootstrap name, fetch paths,
# forwarded env (+REMOTE_TIMEOUT), REMOTE_TIMEOUT default 7200, and (2026-10-21) the filesystem attach (file_system_names)
# and the environment variables of env_build. `launcher` writes the main copy; `launcher env` writes lambda_run_env.sh
# (payload env_build.sh pins.txt apt.txt; results_env/; runner env_build.sh).
gen_launcher() {   # out-file results-dir payload-line runner-desc [fs-name]
  $PY - "$M3" "$MDIR" "$TAG" "$1" "$2" "$3" "$4" "${5:-}" <<'PYEOF'
import re, sys, datetime
m3, m, tag, outf, rdir, payload, desc, fs = sys.argv[1:9]
today = datetime.date.today().isoformat()
s = open(f"{m3}/lambda_run_m3.sh").read()
s = s.replace("PER-LAUNCH COPY for m3 (2026-10-20)", f"PER-LAUNCH COPY for {tag} ({today})")
s = s.replace("# m3 payload: runner, on-box batch, adapted remote bootstrap, record writer (frozen/), data/ (built box, decks, builder, dataset.csv).", f"# {tag} payload: {desc}")
s = s.replace("scp -r $SSHOPT data ubuntu@$IP:m3_run/", "[ -d data ] && scp -r $SSHOPT data ubuntu@$IP:m3_run/")
assert s.count("REMOTE_TIMEOUT=${REMOTE_TIMEOUT:-5400}   # 90 min hard cap") == 1
s = s.replace("REMOTE_TIMEOUT=${REMOTE_TIMEOUT:-5400}   # 90 min hard cap", "REMOTE_TIMEOUT=${REMOTE_TIMEOUT:-7200}   # 120 min default (gate ruling; was 5400), hard cap")
s = s.replace("remote dir welfare_probe -> m3_run; scp payload -> m3 files", f"remote dir welfare_probe -> {tag}_run; scp payload -> {tag} files")
s = s.replace("data/ shipped recursively (built box, decks, builder, dataset.csv).", "data/ shipped recursively if present. REMOTE_TIMEOUT, ENV_FS, ENV_TAG, HOLD_SECONDS, ENV_DIR, ENV_LOCK_SHA256 forwarded to the box (declared point 4, additive). REMOTE_TIMEOUT default 5400 -> 7200 (gate ruling, declared point: caps). Fetch (declared point: fetch paths): results_<tag>/out/*summary*.json and results_<tag>/out/RUN_VALID.json first, then the whole results_<tag>/out/ directory (the criticals-first ordering of the original)." + (f" Filesystem {fs} attached at launch (file_system_names; declared point: launch payload)." if fs else ""))
# payload (declared point 2)
old_payload = 'scp $SSHOPT run_m3.py remote_run_m3.sh "$RUNNER" ubuntu@$IP:m3_run/'
assert old_payload in s; s = s.replace(old_payload, payload)
# forwarded env (declared point 4, additive)
assert s.count('INSTANCE_TYPE=\\"${INSTANCE_TYPE:-$TYPE}\\"') == 1
s = s.replace('INSTANCE_TYPE=\\"${INSTANCE_TYPE:-$TYPE}\\"', 'INSTANCE_TYPE=\\"${INSTANCE_TYPE:-$TYPE}\\" REMOTE_TIMEOUT=\\"$REMOTE_TIMEOUT\\" ENV_FS=\\"${ENV_FS:-}\\" ENV_TAG=\\"${ENV_TAG:-}\\" HOLD_SECONDS=\\"${HOLD_SECONDS:-0}\\" ENV_DIR=\\"${ENV_DIR:-}\\" ENV_LOCK_SHA256=\\"${ENV_LOCK_SHA256:-}\\"')
# filesystem attach (declared point: launch payload)
if fs:
    old_launch = '\\"name\\":\\"drill_$RDIR\\"}'
    assert old_launch in s, "launch payload line"
    s = s.replace(old_launch, '\\"name\\":\\"drill_$RDIR\\",\\"file_system_names\\":[\\"' + fs + '\\"]}')
for a, b in (("m3_run", f"{tag}_run"), ("results_m3", rdir), ("run_m3.py", f"run_{tag}.py"), ("remote_run_m3.sh", f"remote_run_{tag}.sh")):
    s = s.replace(a, b)
assert not re.findall(r"\bm3\b", s), "unreplaced m3 tokens"
open(f"{m}/{outf}", "w").write(s)
print(f"{outf} written from m3's per-launch copy" + (f" (filesystem {fs})" if fs else ""))
PYEOF
}
launcher() {
  cd "$MDIR" || return 1
  local fs="${ENV_FS_NAME:-}"
  gen_launcher "lambda_run_$TAG.sh" "results_$TAG" 'scp $SSHOPT run_'"$TAG"'.py remote_run_'"$TAG"'.sh "$RUNNER" ubuntu@$IP:'"$TAG"'_run/; [ -f tests/tests_'"$TAG"'.py ] && scp $SSHOPT tests/tests_'"$TAG"'.py ubuntu@$IP:'"$TAG"'_run/' "runner, on-box batch, adapted remote bootstrap, record writer (frozen/), the author's tests file, data/ if present" "$fs" || return 1
  $PY - "$M3" "$MDIR" "$TAG" <<'PYEOF'
import re, sys
m3, m, tag = sys.argv[1:4]
r = open(f"{m3}/remote_run_m3.sh").read().replace("cd ~/m3_run  # ADAPTED for m3:", f"cd ~/{tag}_run  # ADAPTED for {tag}:")
assert not re.findall(r"\bm3\b", r); open(f"{m}/remote_run_{tag}.sh", "w").write(r); print(f"remote_run_{tag}.sh written")
PYEOF
  bash -n "lambda_run_$TAG.sh" && bash -n "remote_run_$TAG.sh" && echo "bash -n: ok" || { echo "bash -n: SYNTAX ERROR"; return 1; }
  echo "lambda_run_$TAG.sh: $(wc -l < lambda_run_$TAG.sh) lines, $(diff frozen/lambda_run.sh lambda_run_$TAG.sh | grep -c '^[<>]') lines differ from frozen (m3's copy: $(diff frozen/lambda_run.sh $M3/lambda_run_m3.sh | grep -c '^[<>]'))"
  echo "remote_run_$TAG.sh: $(diff frozen/remote_run.sh remote_run_$TAG.sh | grep -c '^[<>]') lines differ from frozen"
  logrun "launcher copies written from m3's (declared points only)${fs:+; filesystem $fs attached}"
}
launcher_env() {   # the env-build launcher: payload env_build.sh pins.txt apt.txt; runner env_build.sh; results_env/
  cd "$MDIR" || return 1
  local fs="${ENV_FS_NAME:?ENV_FS_NAME (filesystem name) required}"
  gen_launcher "lambda_run_env.sh" "results_env" 'scp $SSHOPT env/env_build.sh env/pins.txt env/apt.txt remote_run_'"$TAG"'.sh ubuntu@$IP:'"$TAG"'_run/' "env_build.sh, pins.txt, apt.txt (the environment of record is built on the filesystem)" "$fs" || return 1
  bash -n lambda_run_env.sh && echo "lambda_run_env.sh: bash -n ok, $(diff frozen/lambda_run.sh lambda_run_env.sh | grep -c '^[<>]') lines differ from frozen"
}
# ---------- envbuild: the environment of record, built once on a box onto the filesystem (hold-open on failure) ----------
# measure.sh envbuild <dir> --fs <filesystem name> [--type T --region R --timeout S --hold S --price P]
envbuild() {
  local fs="" type=gpu_1x_a100_sxm4 region=us-east-1 timeout=5400 hold=2400 price=1.99
  while [ $# -gt 0 ]; do case "$1" in --fs) fs="$2"; shift ;; --type) type="$2"; shift ;; --region) region="$2"; shift ;; --timeout) timeout="$2"; shift ;; --hold) hold="$2"; shift ;; --price) price="$2"; shift ;; *) echo "envbuild: unknown option $1"; return 2 ;; esac; shift; done
  [ -n "$fs" ] || { echo "envbuild needs --fs <filesystem name>"; return 2; }
  cd "$MDIR" || return 1
  mkdir -p env; cp "$REPO/dut/pipeline/measure/env_build.sh" env/env_build.sh; cp out/pip_pins_of_record.txt env/pins.txt
  grep -vE '^[0-9.]+$' out/apt_packages_of_record.txt > env/apt.txt 2>/dev/null || : > env/apt.txt   # package names only, never bare numbers
  echo "env payload: pins $(wc -l < env/pins.txt), apt $(wc -l < env/apt.txt), env_build.sh $(wc -l < env/env_build.sh) lines (sha256 $(sha256sum env/env_build.sh | cut -c1-12)…)"
  ENV_FS_NAME="$fs" launcher_env || return 1
  [ -r .keys ] || { echo "no readable .keys"; return 1; }
  pgrep -f "lambda_run_env[.]sh" >/dev/null && { echo "an env launcher is already running"; return 1; }
  local n; n=$(ls out/envbuild*.json 2>/dev/null | wc -l); n=$((n+1))
  local spent; spent=$($PY -c 'import json,glob; print(round(sum((json.load(open(j)).get("usd_est") or 0) for j in glob.glob("out/launch*.json")+glob.glob("out/envbuild*.json")), 2))'); echo "cap: USD $spent spent so far (extended budget; recorded)"
  echo "== capacity"; rm -f out/.capacity.json.fallback
  if ! lambda_capacity "$type" "$region" 2.50; then
    # the filesystem is regional: no fallback across regions here
    echo "no capacity for $type in $region (the filesystem's region); retry later or pick another type in $region with --type"; return 1
  fi
  local log="out/launcher_env_E$n.log"
  $PY -c 'import json,sys; json.dump({"n":int(sys.argv[1]),"kind":"envbuild","type":sys.argv[2],"region":sys.argv[3],"timeout_s":int(sys.argv[4]),"hold_s":int(sys.argv[5]),"price_usd_h":float(sys.argv[6]),"fs":sys.argv[7],"started":sys.argv[8],"log":sys.argv[9]}, open(sys.argv[10],"w"), indent=1)' \
    "$n" "$type" "$region" "$timeout" "$hold" "$price" "$fs" "$(now)" "$log" "out/envbuild$n.json"
  ( REMOTE_TIMEOUT=$timeout HOLD_SECONDS=$hold ENV_FS="/lambda/nfs/$fs" ENV_TAG="$TAG" PRICE_USD_PER_HOUR=$price INSTANCE_TYPE=$type setsid nohup bash lambda_run_env.sh "$type" "$region" env_build.sh results_env > "$log" 2>&1 < /dev/null & )
  sleep 5; local pid; pid=$(pgrep -f "lambda_run_env[.]sh" | head -1)
  logrun "ENVBUILD $n: $type @ $region, filesystem $fs, REMOTE_TIMEOUT=$timeout, HOLD_SECONDS=$hold, pid ${pid:-?}, log $log"
  echo "envbuild $n started: pid ${pid:-?}, log $log"
}
env_status() {   # masked view of an env build: launcher lines, hold marker, env_report summary when fetched
  cd "$MDIR" || return 1
  for j in out/envbuild*.json; do [ -s "$j" ] || continue; local log; log=$($PY -c 'import json,sys; print(json.load(open(sys.argv[1]))["log"])' "$j")
    echo "  $j: $($PY -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["type"], "@", d["region"], "fs", d["fs"], "started", d["started"], "ended", d.get("ended") or "-")' "$j"); launcher $(pgrep -f "lambda_run_env[.]sh" >/dev/null && echo running || echo exited)"
    [ -f "$log" ] && launch_tail "$log" | tail -6 | sed 's/^/      /'
    local ip; ip=$(awk '{print $2}' .last_lambda_instance 2>/dev/null); [ -n "$ip" ] && pgrep -f "lambda_run_env[.]sh" >/dev/null && echo "      box: $(timeout 25 ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -i ~/.ssh/lambda_ed25519 ubuntu@$ip "ls ${TAG}_run/HOLD ${TAG}_run/RESUME 2>/dev/null | tr '\n' ' '; echo; tail -2 ${TAG}_run/out/run_detached.log 2>/dev/null | grep -oE '^\[env\] [0-9:]+ [a-z]+:?' " 2>/dev/null | tr '\n' ' ')"
  done
  [ -f results_env/out/env_report.json ] && $PY -c "
import json; r=json.load(open('results_env/out/env_report.json')); print('  env_report: status', r.get('status'), '| imports ok', r.get('all_imports_ok'), '| dists', len(r.get('dists') or []), '| modules failing', sum(1 for d in (r.get('dists') or []) for m in d.get('modules', []) if not m.get('ok')), '| lock', (r.get('lock_sha256') or '')[:12], '| commits', r.get('git_commits'), '| elapsed', r.get('elapsed_s'), 's')"
  return 0
}

# ---------- fix: a bounded fixer on the held-open box (measure/fixer_stage.js on wf.js, both families) ----------
# measure.sh fix <dir> --fs <filesystem name> [--family ... --mode ... --on-refusal ...]
fix() {
  local fs=""; pop_via "$@"; set -- "${REST[@]}"; local rest2=()
  while [ $# -gt 0 ]; do case "$1" in --fs) fs="$2"; shift ;; --family|--mode|--on-refusal) rest2+=("$1" "$2"); shift ;; *) echo "fix: unknown option $1"; return 2 ;; esac; shift; done
  [ -n "$fs" ] || { echo "fix needs --fs <filesystem name>"; return 2; }
  cd "$MDIR" || return 1
  local ip; ip=$(awk '{print $2}' .last_lambda_instance 2>/dev/null); [ -n "$ip" ] || { echo "no box recorded in .last_lambda_instance"; return 1; }
  timeout 25 ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -i ~/.ssh/lambda_ed25519 ubuntu@$ip "test -f ${TAG}_run/HOLD || test -f ${TAG}_run/results_${TAG}/out/HOLD" 2>/dev/null || { echo "the box is not holding (no HOLD marker); nothing to fix"; return 1; }
  mkdir -p env; cat > env/box.sh <<EOF2
#!/usr/bin/env bash
# box.sh: run one command on the held box over ssh (the fixer's only tool). usage: box.sh <command...>
exec ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -o ServerAliveInterval=30 -i \$HOME/.ssh/lambda_ed25519 ubuntu@$ip "\$*"
EOF2
  chmod +x env/box.sh
  local n; n=$(ls out/fix*_args.json 2>/dev/null | wc -l); n=$((n+1))
  $PY - "$MDIR" "$TAG" "$fs" "$n" <<'PYEOF'
import json, sys
m, tag, fs, n = sys.argv[1:5]
args = {"box_helper": f"{m}/env/box.sh", "hold_dir": f"/home/ubuntu/{tag}_run", "env_dir": f"/lambda/nfs/{fs}/{tag}", "tag": tag,
        "failure_summary": f"a stage failed on the box and wrote a HOLD marker (/home/ubuntu/{tag}_run/HOLD for the environment build; /home/ubuntu/{tag}_run/results_{tag}/out/HOLD for the main run, whose RESUME marker sits beside it). Logs: /home/ubuntu/{tag}_run/results_env/out/install_pip.log, apt.log, import_check.json (per-module import results with error kinds), env_report.json. The build retries when /home/ubuntu/{tag}_run/RESUME exists.",
        "scope": "environment and glue only: pins.txt (a version, an extra, a different distribution of the same package, a build dependency), apt.txt (system libraries and build tools), environment variables of the install, files under the environment directory. Never the measurement protocol, never record fields, never files outside the environment directory and the hold directory.",
        "max_attempts": 3, "time_budget_min": 30}
json.dump(args, open(f"{m}/out/fix{n}_args.json", "w"), indent=1); print(f"out/fix{n}_args.json written")
PYEOF
  logrun "FIX $n requested on the held box (fixer_stage.js, flags [${rest2[*]}])"
  ( cd "$REPO" && setsid nohup node dut/pipeline/launch.js "$NAME_EXP" stage --measure "$MDIR" --stage fix "${rest2[@]}" > "$SESS/wf-fix$n.out" 2>&1 < /dev/null & )
  sleep 4; echo "fixer started (run $n); watch with: measure.sh status"
}

# ---------- tests: a claim-blind author writes the acceptance tests from the directive (measure/tests_stage.js); the builder never sees them ----------
tests() {
  pop_via "$@"
  cd "$MDIR" || return 1; mkdir -p tests
  local n; n=$(ls out/tests*_args.json 2>/dev/null | wc -l); n=$((n+1))
  [ -f "tests/tests_$TAG.py" ] && { mkdir -p "out/tests$((n-1))"; cp "tests/tests_$TAG.py" "out/tests$((n-1))/"; }
  $PY - "$MDIR" "$TAG" "$n" <<'PYEOF'
import json, sys
m, tag, n = sys.argv[1:4]
json.dump({"directive": f"{m}/EXEC_NOTE.md", "contract": f"{m}/frozen/ONBOX_CONTRACT.md", "design_record": f"{m}/out/design_record.json", "question": f"{m}/QUESTION.md",
           "out_file": f"{m}/tests/tests_{tag}.py", "tag": tag, "results_dir_on_box": f"results_{tag}/out"}, open(f"{m}/out/tests{n}_args.json", "w"), indent=1)
print(f"out/tests{n}_args.json written")
PYEOF
  logrun "TESTS $n: claim-blind author on wf.js (flags [${REST[*]}])"
  ( cd "$REPO" && setsid nohup node dut/pipeline/launch.js "$NAME_EXP" stage --measure "$MDIR" --stage tests "${REST[@]}" > "$SESS/wf-tests$n.out" 2>&1 < /dev/null & )
  sleep 4; echo "tests author started (run $n)"
}

# ---------- launch ----------
lambda_capacity() {   # prints 1-GPU types with capacity (names, prices, regions only); key never printed; exit 3 = requested type has none
  # curl with a browser-like agent, as the launcher does: urllib's default agent gets 403 from the API's front door
  local key; key=$(grep '^LAMBDA_KEY_ONE=' "$MDIR/.keys" | cut -d= -f2- | tr -d '\r\n')
  curl -sS -m 30 -A 'curl/8 lambda_run' -H "Authorization: Bearer $key" https://cloud.lambda.ai/api/v1/instance-types > "$MDIR/out/.capacity.json" 2>/dev/null
  $PY - "$MDIR/out/.capacity.json" "$1" "$2" "${3:-2.50}" <<'PYEOF'
import json, sys
try: d = json.load(open(sys.argv[1]))["data"]
except Exception as e: print("capacity query failed (%s): %s" % (type(e).__name__, open(sys.argv[1]).read()[:120])); sys.exit(4)
want_t, want_r, cap = sys.argv[2], sys.argv[3], float(sys.argv[4])
ok = False; alts = []
for name, v in sorted(d.items()):
    regs = [r["name"] for r in v.get("regions_with_capacity_available", [])]
    price = v["instance_type"]["price_cents_per_hour"] / 100
    if name.startswith("gpu_1x") and regs:
        print("  %-28s USD %5.2f/h  %s" % (name, price, " ".join(regs)))
        if price <= cap and want_r in regs: alts.append((price, name, want_r))   # the filesystem is regional: fall back only inside the requested region
    if name == want_t and want_r in regs: ok = True
print("requested %s @ %s: %s" % (want_t, want_r, "capacity" if ok else "NO capacity"))
if not ok and alts:
    p, n, r = sorted(alts)[0]; print("fallback (cheapest single GPU with capacity in the same region at or under USD %.2f/h): %s @ %s USD %.2f/h" % (cap, n, r, p))
    open(sys.argv[1] + ".fallback", "w").write("%s %s %.2f\n" % (n, r, p))
sys.exit(0 if ok else 3)
PYEOF
}
launch() {
  local type=gpu_1x_a100_sxm4 region=us-east-1 timeout=7200 budget=5 price=1.99
  while [ $# -gt 0 ]; do case "$1" in --type) type="$2"; shift ;; --region) region="$2"; shift ;; --timeout) timeout="$2"; shift ;; --budget) budget="$2"; shift ;; --price) price="$2"; shift ;; *) echo "launch: unknown option $1"; return 2 ;; esac; shift; done
  cd "$MDIR" || return 1
  local n; n=$(ls out/launch*.json 2>/dev/null | wc -l); n=$((n+1))
  local spent; spent=$($PY -c 'import json,glob; print(round(sum((json.load(open(j)).get("usd_est") or 0) for j in glob.glob("out/launch*.json")+glob.glob("out/envbuild*.json")), 2))')   # launches and environment builds
  local left; left=$($PY -c "print(round(10 - $spent, 2))"); [ "$($PY -c "print(1 if $left > 0.5 else 0)")" = 1 ] || { echo "launch $n refused: USD $spent of the USD 10 calibration cap already spent (owner rule)"; return 1; }
  budget=$($PY -c "print(min(float('$budget'), $left))"); echo "calibration cap: USD $spent spent, USD $left left; this launch's BUDGET_LEFT_USD=$budget"
  [ -r .keys ] || { echo "no readable .keys"; return 1; }
  for f in "lambda_run_$TAG.sh" "remote_run_$TAG.sh" "onbox_$TAG.sh" "run_$TAG.py" frozen/provenance.py; do [ -f "$f" ] || { echo "missing $f"; return 1; }; done
  local rv; rv=$(ls out/review_build*.json 2>/dev/null | sort -V | tail -1); [ -n "$rv" ] && grep -q '"PASS"' "$rv" || { echo "latest review is not PASS ($rv)"; return 1; }
  local bh; bh=$(ls out/BUILT_HASHES_build*.txt | sort -V | tail -1); ( cd "$MDIR" && sha256sum -c --quiet "$bh" ) || { echo "built files changed since $bh"; return 1; }
  # gate ruling (addenda 5 to 7): re-run the selftest before launch and compare its printed sha256 values with the files on disk
  if grep -q -- '--selftest' "run_$TAG.py"; then
    local st; st=$(timeout 300 $PY "run_$TAG.py" --selftest 2>&1 | tee "out/selftest_prelaunch_L$n.log" | grep -E '^selftest: (PASS|FAIL|files sha256)')
    echo "$st" | grep -q '^selftest: PASS' || { echo "pre-launch selftest did not PASS"; return 1; }
    local want; want=$(echo "$st" | grep -oE '[0-9a-f]{64}' | sort); local have; have=$(sha256sum "run_$TAG.py" "onbox_$TAG.sh" | awk '{print $1}' | sort)
    [ "$want" = "$have" ] && echo "pre-launch selftest PASS; its printed hashes match the files on disk" || { echo "pre-launch selftest hashes differ from the files on disk"; return 1; }
  else
    [ -f "tests/tests_$TAG.py" ] && $PY -m py_compile "tests/tests_$TAG.py" && rm -rf tests/__pycache__ && echo "pre-launch: author's tests compile; they run on the box in the shipped environment (no implementer selftest by ruling)" || { echo "pre-launch: tests/tests_$TAG.py missing or does not compile"; return 1; }
  fi
  pgrep -f "lambda_run_${TAG}[.]sh" >/dev/null && { echo "a launcher is already running"; return 1; }
  [ "$timeout" -le 7200 ] || { echo "timeout above 7,200 s (owner rule)"; return 1; }
  echo "== capacity"; rm -f out/.capacity.json.fallback
  if ! lambda_capacity "$type" "$region" 2.50; then
    # gate ruling (addendum 7): else the cheapest single GPU with capacity at no more than USD 2.50/h, recorded
    [ -s out/.capacity.json.fallback ] || { echo "no capacity for the requested type and no fallback at or under USD 2.50/h"; return 1; }
    read -r type region price < out/.capacity.json.fallback; echo "using the fallback of record: $type @ $region at USD $price/h"
  fi
  local log="out/launcher_${TAG}_L$n.log"
  $PY -c 'import json,sys; json.dump({"n":int(sys.argv[1]),"type":sys.argv[2],"region":sys.argv[3],"timeout_s":int(sys.argv[4]),"budget_left_usd":float(sys.argv[5]),"price_usd_h":float(sys.argv[6]),"started":sys.argv[7],"log":sys.argv[8]}, open(sys.argv[9],"w"), indent=1)' \
    "$n" "$type" "$region" "$timeout" "$budget" "$price" "$(now)" "$log" "out/launch$n.json"
  # environment of record (gate addendum 15): forwarded to the box; the on-box script activates it and verifies the lock hash
  local envdir lock; envdir=$($PY -c 'import json; print(json.load(open("results_env/out/env_report.json"))["env_dir"])' 2>/dev/null); lock=$($PY -c 'import json; print(json.load(open("results_env/out/env_report.json"))["lock_sha256"])' 2>/dev/null)
  [ -n "$envdir" ] && [ -n "$lock" ] || { echo "no environment of record (results_env/out/env_report.json); run envbuild first"; return 1; }
  echo "environment of record: $envdir, lock ${lock:0:16}…, HOLD_SECONDS=${HOLD_SECONDS_LAUNCH:-1200}"
  ( REMOTE_TIMEOUT=$timeout PRICE_USD_PER_HOUR=$price BUDGET_LEFT_USD=$budget INSTANCE_TYPE=$type ENV_FS="/lambda/nfs/${ENV_FS_NAME:-metis-env-us-east-1}" ENV_TAG="$TAG" ENV_DIR="$envdir" ENV_LOCK_SHA256="$lock" HOLD_SECONDS=${HOLD_SECONDS_LAUNCH:-1200} setsid nohup bash "lambda_run_$TAG.sh" "$type" "$region" "onbox_$TAG.sh" "results_$TAG" > "$log" 2>&1 < /dev/null & )
  sleep 5; local pid; pid=$(pgrep -f "lambda_run_${TAG}[.]sh" | head -1)
  logrun "LAUNCH $n: $type @ $region, REMOTE_TIMEOUT=$timeout, BUDGET_LEFT_USD=$budget, pid ${pid:-?}, log $log"
  echo "launch $n started: pid ${pid:-?}, log $log"
}
launch_tail() {   # masked view of a launcher log: the launcher's own tagged lines; the on-box tail line is masked
  grep -E '^\[(launch|poll|ssh|scp|backstop|run|fetch|done|teardown|signal|reattach)' "$1" | sed -E 's/^(\[poll-run\] \+[0-9]+s \|).*/\1 <on-box line masked>/' | uniq -c | sed -E 's/^ *([0-9]+) (.*)/\2  (x\1)/; s/  \(x1\)$//'
}
launch_finish() {   # fills end/hours/usd into out/launch<n>.json once the launcher has exited
  $PY - "$MDIR" <<'PYEOF'
import json, sys, glob, os, datetime, re
m = sys.argv[1]
for j in sorted(glob.glob(f"{m}/out/launch*.json") + glob.glob(f"{m}/out/envbuild*.json")):
    d = json.load(open(j))
    if d.get("ended"): continue
    log = f"{m}/{d['log']}"
    if not os.path.exists(log): continue
    txt = open(log).read()
    if "[teardown] terminate accepted" not in txt and "[done]" not in txt: continue
    t0 = datetime.datetime.fromisoformat(d["started"].replace("Z", "+00:00")); t1 = datetime.datetime.fromtimestamp(os.path.getmtime(log), datetime.timezone.utc)
    h = (t1 - t0).total_seconds() / 3600
    rc = re.search(r"DONE marker rc=(\d+)", txt)
    d.update({"ended": t1.strftime("%Y-%m-%dT%H:%M:%SZ"), "hours_wall": round(h, 3), "usd_est": round(h * d["price_usd_h"], 2), "rc": rc.group(1) if rc else None,
              "instance_id": (re.search(r"\[launch\] id=(\S+)", txt) or [None, None])[1], "terminated": "[teardown] terminate accepted" in txt})
    json.dump(d, open(j, "w"), indent=1)
    print("%s %d: ended %s, %.2f h wall, USD %.2f est, rc %s, terminate %s" % (d.get("kind", "launch"), d["n"], d["ended"], h, d["usd_est"], d["rc"], "accepted" if d["terminated"] else "NOT CONFIRMED"))
PYEOF
}

# ---------- score ----------
score() {
  cd "$MDIR" || return 1
  launch_finish >/dev/null
  $PY - "$MDIR" "$TAG" "$REPO" <<'PYEOF'
import json, sys, glob, os, datetime, hashlib
m, tag, repo = sys.argv[1:4]
card = json.load(open(f"{m}/CARD.json")); rec = card["record"]
R = f"{m}/results_{tag}/out"
rv = json.load(open(f"{R}/RUN_VALID.json")) if os.path.exists(f"{R}/RUN_VALID.json") else None
band = lambda u: 2.5 if u["basis"] == "PROXY" else 3
rows, lines = [], []
for i, u in enumerate(rec["required"], 1):
    f = glob.glob(f"{R}/endpoint-C{i}_tag-{tag}.json")
    e = json.load(open(f[0])) if f else None
    v = (e or {}).get("values") or {}
    meas = v.get("measured")
    lo, hi = u["value"] / band(u), u["value"] * band(u)
    held = (meas is not None and lo <= meas <= hi)
    valid = bool(e and e.get("run_valid"))
    ratio = (meas / u["value"]) if (isinstance(meas, (int, float)) and u["value"]) else None
    state = "no record" if not e else ("void" if not valid else ("held" if held else "refuted"))
    rows.append({"id": u["id"], "basis": u["basis"], "card_value": u["value"], "band": [lo, hi], "measured": meas, "unit": v.get("unit"), "decision": (e or {}).get("decision"), "run_valid": valid, "state": state, "ratio": ratio, "record": os.path.relpath(f[0], m) if f else None})
    lines.append(f"- P{i} ({u['id']}, {u['basis']} {u['value']}): {state}; measured {meas} {v.get('unit') or ''}; band [{lo:.4g}, {hi:.4g}]; record decision {(e or {}).get('decision')}; run_valid {valid}")
    print("  C%d %-5s %-9s ratio %s run_valid %s" % (i, u["basis"], state, ("%.3g" % ratio) if ratio is not None else "-", valid))
anc = glob.glob(f"{R}/endpoint-anchor_tag-{tag}.json"); a = json.load(open(anc[0])) if anc else None
print("  anchor: %s; RUN_VALID.json: %s" % ((a or {}).get("decision") or "no record", (rv or {}).get("run_valid") if rv else "missing"))
launches = [json.load(open(j)) for j in sorted(glob.glob(f"{m}/out/launch*.json"))]
usd = round(sum(l.get("usd_est") or 0 for l in launches), 2)
seal = open(f"{m}/out/SEALS.txt").read().split()[0]
md = ["# Predictions scored (mechanical, measure.sh score; no model)", "", f"Sealed predictions sha256 {seal} (out/SEALS.txt). Rule: held if the measured value lies within the band; void if the record's run_valid is false or the record is missing.", "", *lines, "",
      f"Anchor: {(a or {}).get('decision') or 'no record'}. Launches: {len(launches)}; estimated USD {usd}. Base rate update: {sum(1 for r in rows if r['state']=='held')} held of {sum(1 for r in rows if r['state'] in ('held','refuted'))} decided."]
open(f"{m}/out/PREDICTIONS_SCORED.md", "w").write("\n".join(md) + "\n")
row = {"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "kind": "card_number_resolved",
       "card": {"run": os.path.relpath(os.path.dirname(os.path.dirname(os.path.dirname(f"{repo}/{card['source']}"))), repo), "source": card["source"], "pick": rec["key"], "title": rec["title"], "result_json_sha256": card["result_json_sha256"], "plan_usd": rec.get("plan_usd"), "expected": rec.get("predictions", {}).get("expected")},
       "numbers": rows, "anchor": {"decision": (a or {}).get("decision"), "values": (a or {}).get("values")},
       "resolved_by": {"run": os.path.relpath(m, repo), "tag": tag, "launches": [{k: l.get(k) for k in ("n", "type", "region", "hours_wall", "usd_est", "rc", "instance_id")} for l in launches], "usd": usd, "run_valid": (rv or {}).get("run_valid") if rv else None},
       "operator": "blind: measure.sh (mechanical) + headless sonnet sessions for the stage operators, the gate and the review; workflow agents pinned as committed", "sealed_predictions_sha256": seal}
open(f"{repo}/experiments/_meta/LEDGER.jsonl", "a").write(json.dumps(row) + "\n")
print("  out/PREDICTIONS_SCORED.md written; ledger row appended (kind card_number_resolved, %d numbers, USD %.2f)" % (len(rows), usd))
PYEOF
  logrun "score: ledger row appended"
}

# ---------- post ----------
post() {
  [ -d "$MDIR/results_$TAG/out" ] || { echo "no results_$TAG/out"; return 1; }
  pop_via "$@"
  local n; n=$(ls "$MDIR/out"/post*_args.json 2>/dev/null | wc -l); n=$((n+1)); local name="post$n"
  $PY - "$MDIR" "$TAG" "$n" <<'PYEOF'
import json, sys
m, tag, n = sys.argv[1:4]
args = {"mode": "post", "design_record": f"{m}/out/design_record.json", "gate_commit": f"{m}/GATE_COMMIT.md", "tag": tag, "conventions": f"{m}/frozen",
        "exec_note": open(f"{m}/EXEC_NOTE.md").read(), "results_dir": f"{m}/results_{tag}/out", "triage_path": f"{m}/triage_workflow.js", "gates_dir": f"{m}/gates", "seed_file": f"{m}/QUESTION.md"}
json.dump(args, open(f"{m}/out/post{n}_args.json", "w"), indent=1)
print("out/post%s_args.json written" % n)
PYEOF
  if [ "$VIA" = wf ]; then via_wf post "${REST[@]}"; return; fi
  local f; f=$(operator_md "post" "$MDIR/out/post${n}_args.json" "$MDIR/out/post${n}_return.json")
  start_session "$name" sonnet "$f"
}

# ---------- status ----------
status() {
  echo "== $(basename "$MDIR") (tag $TAG) $(date -u +%H:%MZ)"
  for j in $(ls -t "$SESS"/*.json 2>/dev/null | sort); do
    local name; name=$(basename "$j" .json); local st="exited"; session_running "$name" && st="running"
    local said=""; if [ -s "$SESS/$name.out" ]; then said=$($PY -c "
import json, sys, re
try: d = json.load(open(sys.argv[1]))
except Exception as e: print('out not JSON (%s)' % type(e).__name__); sys.exit()
r = str(d.get('result', '')).strip().replace(chr(10), ' ')
ok = re.match(r'^(design|build|post) (return written|failed): wf_|^gate written: \d+ answers, \d+ items|^review: (PASS|FAIL), \d+ blocking, \d+ advisory', r)
print('%s, %s turns, %.0f min, \$%.2f; said: %s' % (d.get('subtype'), d.get('num_turns'), (d.get('duration_ms') or 0) / 60000, d.get('total_cost_usd') or 0, r[:90] if ok else 'NON-CONFORMING reply (%d chars, masked)' % len(r)))" "$SESS/$name.out"); fi
    echo "  session $name: $st $([ -s "$SESS/$name.err" ] && echo "err $(wc -c < "$SESS/$name.err")B") $said"
  done
  $PY - "$PROJ" <<'PYEOF'
import json, os, sys, glob, datetime
W = sys.argv[1]
wfs = sorted(glob.glob(os.path.join(W, "*", "subagents", "workflows", "wf_*")))
for wf in wfs:
    rows = [json.loads(l) for l in open(os.path.join(wf, "journal.jsonl")) if l.strip()] if os.path.exists(os.path.join(wf, "journal.jsonl")) else []
    meta = {}
    for mf in glob.glob(os.path.join(wf, "agent-*.meta.json")):
        try: meta[os.path.basename(mf)[6:-10]] = json.load(open(mf))
        except Exception: pass
    use = {}
    for t in glob.glob(os.path.join(wf, "agent-*.jsonl")):
        aid = os.path.basename(t)[6:-6]; u = {"in": 0, "out": 0, "model": None, "t0": None, "t1": None}
        for l in open(t):
            try: o = json.loads(l)
            except Exception: continue
            ts = o.get("timestamp")
            if ts: u["t0"] = u["t0"] or ts; u["t1"] = ts
            if o.get("type") == "assistant" and isinstance(o.get("message"), dict):
                g = o["message"].get("usage") or {}; u["model"] = o["message"].get("model") or u["model"]
                u["in"] += g.get("input_tokens", 0) + g.get("cache_creation_input_tokens", 0); u["out"] += g.get("output_tokens", 0)
        use[aid] = u
    st = {r["agentId"]: r for r in rows if r.get("type") == "started"}
    done = {r["agentId"]: ("result", len(json.dumps(r.get("result")))) for r in rows if r.get("type") == "result"}
    done.update({r["agentId"]: ("FAILED", 0) for r in rows if r.get("type") == "failed"})
    n = len(st); print("  [%s] %d agent(s): %d returned, %d failed, %d running" % (os.path.basename(wf), n, sum(1 for v in done.values() if v[0] == "result"), sum(1 for v in done.values() if v[0] == "FAILED"), n - len(done)))
    for aid, r in st.items():
        u = use.get(aid, {}); d = done.get(aid, ("running", 0)); mins = ""
        if u.get("t0") and u.get("t1"):
            try: mins = "%5.1f min" % ((datetime.datetime.fromisoformat(u["t1"].replace("Z", "+00:00")) - datetime.datetime.fromisoformat(u["t0"].replace("Z", "+00:00"))).total_seconds() / 60)
            except Exception: pass
        lab = (r.get("label") or ""); lab = lab.split(":")[0] + (":…" if ":" in lab else "")   # labels can carry claim text: prefix only
        print("    %-8s %-18s %-10s %-14s %-22s %9s  in %8s  out %6s%s" % (d[0], lab[:18], (r.get("phase") or "")[:10], (meta.get(aid, {}).get("agentType") or "")[:14], (u.get("model") or "")[:22], mins, format(u.get("in", 0), ","), format(u.get("out", 0), ","), "  <%d chars>" % d[1] if d[0] == "result" else ""))
if not wfs: print("  no workflow transcripts yet")
PYEOF
  for w in "$MDIR"/out/wf-*/; do [ -d "$w" ] || continue; $PY - "$w" "$MDIR" <<'PYEOF'
import json, sys, os
w, m = sys.argv[1:3]
try: st = json.load(open(os.path.join(w, "out", "status.json")))
except Exception: print("  %s: no status yet" % os.path.relpath(w, m)); sys.exit()
calls = st.get("calls", [])
by = {}
for c in calls: by[c.get("state")] = by.get(c.get("state"), 0) + 1
fam = st.get("by_family", {})
print("  %s: stage %s, %s; %d call(s) %s; substitutions %s, refusals %s; $%.2f; families %s" % (os.path.relpath(w, m), st.get("stage"), "done" if st.get("done") else "running", len(calls), json.dumps(by), st.get("substitutions"), st.get("refusals"), st.get("cost_usd", 0), ", ".join("%s %d calls %d failed" % (f, v.get("calls", 0), v.get("failed", 0)) for f, v in fam.items()) or "-"))
for c in calls[-6:]:
    lab = c.get("id", "").split(" ", 1)[-1]; lab = lab.split(":")[0] + (":…" if ":" in lab else "")
    print("    %-10s %-16s %-26s -> %-26s %-9s %5.1f min $%.3f%s" % (c.get("state"), lab[:16], c.get("model", ""), c.get("understudy") or "-", c.get("kind") or "", c.get("ms", 0) / 60000, c.get("cost_usd", 0), " (by understudy)" if c.get("substituted") else ""))
PYEOF
  done
  wf_running && echo "  wf.js: running" || true
  cd "$MDIR" || return 1
  for f in out/design_record.json out/build*_return.json out/post*_return.json; do [ -s "$f" ] && echo "  $f: $(wc -c < "$f") B $($PY -c "
import json,sys; d=json.load(open(sys.argv[1])); print('keys', sorted(d.keys())[:8], 'halt' if d.get('halt') else '', 'error' if d.get('error') else '', 'FAILED' if d.get('failed') else '')" "$f" 2>/dev/null)"; done
  for f in GATE_COMMIT.md EXEC_NOTE.md; do [ -s "$f" ] && echo "  $f: $(wc -l < "$f") lines, $(grep -c '^#' "$f") headings, $(grep -c '^## Addendum' "$f") addenda"; done
  [ -f "run_$TAG.py" ] && echo "  built: run_$TAG.py $(wc -l < run_$TAG.py) lines, onbox_$TAG.sh $(wc -l < onbox_$TAG.sh 2>/dev/null) lines; selftest logs: $(ls out/selftest_build*.log 2>/dev/null | wc -l) ($(for l in out/selftest_build*.log; do [ -f "$l" ] && grep -E '^selftest: (PASS|FAIL)' "$l" | tail -1; done | tr '\n' ' '))"
  for r in out/review_build*.json; do [ -s "$r" ] && echo "  $r: $(cat "$r" | tr -d '\n ' | cut -c1-80)"; done
  env_status
  for j in out/launch*.json; do [ -s "$j" ] || continue; local log; log=$($PY -c 'import json,sys; print(json.load(open(sys.argv[1]))["log"])' "$j")
    echo "  $j: $($PY -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["type"], "@", d["region"], "started", d["started"], "ended", d.get("ended") or "-", "usd_est", d.get("usd_est", "-"), "rc", d.get("rc", "-"))' "$j"); launcher $(pgrep -f "lambda_run_${TAG}[.]sh" >/dev/null && echo running || echo exited)"
    [ -f "$log" ] && launch_tail "$log" | tail -8 | sed 's/^/      /'; done
  [ -d "results_$TAG/out" ] && echo "  results_$TAG/out: $(ls results_$TAG/out | wc -l) files; endpoints $(ls results_$TAG/out/endpoint-*_tag-$TAG.json 2>/dev/null | wc -l); RUN_DONE $(cat results_$TAG/RUN_DONE 2>/dev/null || echo -); RUN_VALID $($PY -c "import json; print(json.load(open('results_$TAG/out/RUN_VALID.json')).get('run_valid'))" 2>/dev/null || echo -)"
  [ -s out/PREDICTIONS_SCORED.md ] && echo "  scored: $(grep -cE '^- P[0-9]+' out/PREDICTIONS_SCORED.md) predictions; $(grep -oE 'Base rate update: .*' out/PREDICTIONS_SCORED.md)"
  [ -s "TAKEAWAYS_$TAG.md" ] && echo "  TAKEAWAYS_$TAG.md: $(wc -l < TAKEAWAYS_$TAG.md) lines"
  return 0
}

wait_stage() {
  local stage="$1" t=0 max=${2:-14400}
  while [ $t -lt $max ]; do
    case "$stage" in
      launch) if ! pgrep -f "lambda_run_${TAG}[.]sh" >/dev/null; then launch_finish; echo "launch exited after $((t/60)) min"; return 0; fi ;;
      envbuild) if ! pgrep -f "lambda_run_env[.]sh" >/dev/null; then launch_finish; echo "env build exited after $((t/60)) min"; env_status; return 0; fi ;;
      hold) local ip; ip=$(awk '{print $2}' "$MDIR/.last_lambda_instance" 2>/dev/null); if ! pgrep -f "lambda_run_env[.]sh" >/dev/null; then echo "env build exited"; return 0; fi; if [ -n "$ip" ] && timeout 25 ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -i ~/.ssh/lambda_ed25519 ubuntu@$ip "test -f ${TAG}_run/HOLD || test -f ${TAG}_run/results_${TAG}/out/HOLD" 2>/dev/null; then echo "box is HELD (a stage failed) after $((t/60)) min"; return 3; fi ;;
      wf) if ! wf_running; then echo "wf.js stage exited after $((t/60)) min"; ls "$MDIR"/out/build*_args.json >/dev/null 2>&1 && [ -f "$MDIR/run_$TAG.py" ] && [ "$(ls "$MDIR"/out/wf-build-* -d 2>/dev/null | wc -l)" -ge 1 ] && build_checks; return 0; fi ;;
      *) local last; last=$(ls "$SESS"/$stage*.json 2>/dev/null | sort | tail -1); [ -n "$last" ] || { echo "no $stage session"; return 1; }
         if ! session_running "$(basename "$last" .json)"; then echo "$stage session exited after $((t/60)) min"; [ "$stage" = build ] && build_checks; return 0; fi ;;
    esac
    sleep 60; t=$((t+60))
  done
  echo "wait $stage: timed out after $((max/60)) min"; return 1
}

ask() {   # name instruction-file: one read/write-only sonnet session following the file (classifiers, probes)
  local name="$1" instr="$2"; [ -f "$instr" ] || { echo "no instruction file $instr"; return 1; }
  start_session "$name" sonnet "$(realpath "$instr")" --disallowedTools "$RO_TOOLS"
}

case "$CMD" in
  ask) ask "$@" ;;
  prepare) prepare "$@" ;; design) design "$@" ;; gate) gate "$@" ;; build) build "$@" ;; build-checks) build_checks ;; review) review "$@" ;;
  launcher) launcher ;; launch) launch "$@" ;; envbuild) envbuild "$@" ;; fix) fix "$@" ;; tests) tests "$@" ;; score) score ;; post) post "$@" ;; status) status ;; wait) wait_stage "$@" ;;
  *) sed -n 2,22p "$0"; exit 2 ;;
esac
