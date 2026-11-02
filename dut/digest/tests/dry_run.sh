#!/usr/bin/env bash
# Dry run of digest with no model calls: wf.js runs pipeline.js against a real run root with every model family
# replaced by tests/stub_runner.js, which serves the hand-written replies in tests/stub/m2/ (reader, verdict, notebook).
# Evidence copying, check.py and the marimo export are real. Writes only under <out dir>; reads the run.
# Usage: bash dut/digest/tests/dry_run.sh <out dir> [run root]      (MARIMO overrides the marimo binary)
set -u
M=$(cd "$(dirname "$0")/../../.." && pwd); D=$M/dut/digest
OUT=$(mkdir -p "${1:?usage: dry_run.sh <out dir> [run root]}" && cd "$1" && pwd)
ROOT=${2:-$M/experiments/reshape-test/20261020-0855-measure}
export WF_STUB=$D/tests/stub_runner.js MARIMO=${MARIMO:-/home/hal/dev/interp/janus/.venv-gpu/bin/marimo}
fails=0
expect() { if [ "$1" = "$2" ]; then echo "  ok   $3"; else echo "  FAIL $3 (got: $1)"; fails=$((fails + 1)); fi; }
error_of() { node -e 'const r = require(process.argv[1]); console.log(r.error ? r.error : "none")' "$1/digest/wf/result.json"; }

# run <case> <stub dir> [fresh|bare|keep|force]: fresh (default) empties the case directory and puts the synthetic
# owner file in first; bare empties it with no owner file; keep and force reuse it, force with args.force true
run() {
  local c=$OUT/$1 mode=${3:-fresh}
  case $mode in fresh|bare) rm -rf "$c"; mkdir -p "$c/digest";; esac
  [ "$mode" = fresh ] && cp "$D/tests/stub/m2/owner_questions.md" "$c/digest/questions.md"
  printf '{"run_root": "%s", "out": "%s", "force": %s}\n' "$ROOT" "$c/digest" "$([ "$mode" = force ] && echo true || echo false)" > "$c/args.json"
  (cd "$M" && DIGEST_STUB_DIR=$2 DIGEST_STUB_LOG=$c/stub_calls.jsonl node dut/pipeline/idea/wf.js --config dut/digest/wf_config.json \
    --script dut/digest/pipeline.js --args "$c/args.json" --out "$c/digest/wf" --mode fallback --on-refusal halt > "$c/console.log" 2>&1)
}
# variant <case> <node expression on r> [on v]: a stub dir whose reader.json (r) and verdict.json (v) are edited copies
variant() {
  local s=$OUT/stubs/$1; rm -rf "$s"; mkdir -p "$s"; cp "$D/tests/stub/m2/notebook.py" "$s/"
  node -e 'const fs = require("fs"), j = f => JSON.parse(fs.readFileSync(f, "utf8")); const r = j(process.argv[1]), v = j(process.argv[2]); '"$2; ${3:-}"'
    fs.writeFileSync(process.argv[3], JSON.stringify(r, null, 1)); fs.writeFileSync(process.argv[4], JSON.stringify(v, null, 1))' \
    "$D/tests/stub/m2/reader.json" "$D/tests/stub/m2/verdict.json" "$s/reader.json" "$s/verdict.json"
  echo "$s"
}

echo "== good: the hand-written m2 replies"
run good "$D/tests/stub/m2"
G=$OUT/good/digest
expect "$(error_of "$OUT/good")" none "pipeline returned without error"
python3 -I "$D/check.py" "$G" > "$OUT/good/check.txt"; expect $? 0 "check.py passes on the written digest"
sed 's/^/       /' "$OUT/good/check.txt"
python3 -I "$D/tests/planted_check.py" "$G" > "$OUT/good/planted.txt"; expect $? 0 "planted expectations for m2 hold on the stub digest (harness check only)"
printf '{"%s": {"enums": {"prediction_hit": "yes"}}}\n' "$(basename "$ROOT")" > "$OUT/planted_wrong.json"
python3 -I "$D/tests/planted_check.py" "$G" "$OUT/planted_wrong.json" > /dev/null; expect $? 1 "planted_check misses a wrong expectation"
expect "$(cd "$G" && ls evidence/_source)" RESULT.md "one-hop source card copied to evidence/_source/"
expect "$(grep -c '(\.\./\|(results_m2\|(RUN\.md)' "$G/DIGEST.md" "$G/QA.md" | awk -F: '{s += $2} END {print s}')" 0 "no citation left pointing outside evidence/"
expect "$(node -e 'const fs = require("fs"); const l = fs.readFileSync(process.argv[1], "utf8").trim().split("\n").map(JSON.parse); console.log(l.map(x => `${x.label}:${x.model}:${x.tools}:${x.cwd === process.argv[2] ? "run" : x.cwd === process.argv[3] ? "digest" : "own"}`).join(" "))' "$OUT/good/stub_calls.jsonl" "$ROOT" "$G")" \
  "reader:codex/default@high:Read,Glob,Grep:run verdict:codex/default@high::own notebook:codex/default@medium:Read,Glob,Grep:digest" "three calls, Codex primary, read-only tool lists, reader in the run root"
P=$G/wf/agents/0002-verdict/prompt.md
expect "$(awk '/^## The reader.s observations/{o=NR} /^## The owner.s beliefs/{b=NR} END {print (o && b && o < b) ? "before" : "not"}' "$P")" before "verdict prompt: observations before beliefs"
expect "$(grep -c 'parallel solver beats the CPU library' "$G/wf/agents/0001-reader/prompt.md")" 0 "reader prompt carries no owner belief"

echo "== refuse: the same command again, without force"
before=$(sha256sum "$G/DIGEST.md")
run good "$D/tests/stub/m2" keep
case "$(error_of "$OUT/good")" in *"already holds a digest"*) echo "  ok   refused: $(error_of "$OUT/good" | cut -c1-140)";; *) echo "  FAIL not refused"; fails=$((fails + 1));; esac
expect "$(sha256sum "$G/DIGEST.md")" "$before" "DIGEST.md untouched by the refused run"

echo "== force: the same command with force true"
run good "$D/tests/stub/m2" force
expect "$(error_of "$OUT/good")" none "forced run returned without error"
expect "$(ls -d "$G"/wf/prev-* 2>/dev/null | wc -l)" 1 "the earlier journal and agents kept under wf/prev-*"

echo "== no owner file: the verdict runs on the standing questions alone"
run noowner "$(variant noowner '' 'v.beliefs = {}; v.answers = {}')" bare
expect "$(error_of "$OUT/noowner")" none "pipeline returned without error"
expect "$(grep -c '^## Owner' "$OUT/noowner/digest/QA.md")" 0 "QA.md has standing questions only"
expect "$(grep -A2 "^## The owner's \(beliefs\|questions\)" "$OUT/noowner/digest/wf/agents/0002-verdict/prompt.md" | grep -c '^None\.$')" 2 "verdict prompt says None for beliefs and questions"

echo "== bad: a verdict that skips the owner's beliefs (the keyed schema demands one entry per belief)"
run skipped "$OUT/stubs/noowner"
case "$(error_of "$OUT/skipped")" in *"verdict call returned nothing"*) echo "  ok   run failed: $(error_of "$OUT/skipped")";; *) echo "  FAIL: $(error_of "$OUT/skipped")"; fails=$((fails + 1));; esac
expect "$(grep -o 'missing \\"B1\\"' "$OUT/skipped/digest/wf/journal.jsonl" | head -1)" 'missing \"B1\"' "journal names the missing belief"

echo "== a parenthesis that is not a path, such as (N/2), is left as prose"
run paren "$(variant paren 'r.analysis += " Each round of the parallel solver halves the system (N/2), as the source card says (../20261019-2344-tree/out/RESULT.md)."')"
expect "$(error_of "$OUT/paren")" none "pipeline returned without error"
expect "$(grep -c '(N/2)' "$OUT/paren/digest/DIGEST.md")" 1 "(N/2) kept in DIGEST.md"

echo "== bad: a supported verdict with no quote"
run noquote "$(variant noquote '' 'v.beliefs.B1.quote = ""')"
case "$(error_of "$OUT/noquote")" in *"supported with no quote"*) echo "  ok   run failed: $(error_of "$OUT/noquote")";; *) echo "  FAIL: $(error_of "$OUT/noquote")"; fails=$((fails + 1));; esac

echo "== bad: a citation to a file that does not exist"
run missing "$(variant missing 'r.citations.push({path: "results_m2/out/records/no-such-record.json", supports: "x"})')"
case "$(error_of "$OUT/missing")" in *"no such file"*) echo "  ok   run failed: $(error_of "$OUT/missing")";; *) echo "  FAIL"; fails=$((fails + 1));; esac
expect "$(ls "$OUT/missing/digest" | tr '\n' ' ')" "RUN.md questions.md wf " "nothing but RUN.md written; no evidence copied"

echo "== bad: a file outside the run that RUN.md does not name"
run hop "$(variant hop 'r.citations.push({path: "../20261019-2344-tree/out/run.json", supports: "x"})')"
case "$(error_of "$OUT/hop")" in *"one hop only"*) echo "  ok   run failed: $(error_of "$OUT/hop")";; *) echo "  FAIL"; fails=$((fails + 1));; esac

echo "== bad: a hidden file inside the run"
run hidden "$(variant hidden 'r.citations.push({path: ".last_lambda_instance", supports: "x"})')"
case "$(error_of "$OUT/hidden")" in *"hidden or credential"*) echo "  ok   run failed: $(error_of "$OUT/hidden")";; *) echo "  FAIL"; fails=$((fails + 1));; esac

echo "== bad: prose with an uncited number"
run uncited "$(variant uncited 'r.method += " The anchor used 2 sizes and 5 seeds."')"
case "$(error_of "$OUT/uncited")" in *"checks failed: numbers_cited"*) echo "  ok   run reports: $(error_of "$OUT/uncited")";; *) echo "  FAIL: $(error_of "$OUT/uncited")"; fails=$((fails + 1));; esac
expect "$(cd "$OUT/uncited/digest" && ls DIGEST.md QA.md digest.json digest.py MANIFEST.json CHECK.json RUN.md 2>/dev/null | wc -l)" 7 "files left in place with CHECK.json"

echo "dry run: $([ $fails = 0 ] && echo 'all expectations met' || echo "$fails failure(s)") · $OUT"
exit $([ $fails = 0 ] && echo 0 || echo 1)
