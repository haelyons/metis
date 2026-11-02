#!/usr/bin/env bash
# Dry run of digest with no model calls: wf.js runs pipeline.js against a real run root with every model family
# replaced by tests/stub_runner.js, which serves the hand-written replies in tests/stub/m2/ (reader, verify, writer,
# notebook, repair). Evidence copying, check.py and the sandboxed marimo export are real. Writes only under <out dir>.
# Usage: bash dut/digest/tests/dry_run.sh <out dir> [run root]      (MARIMO overrides the marimo binary)
set -u
M=$(cd "$(dirname "$0")/../../.." && pwd); D=$M/dut/digest; STUB=$D/tests/stub/m2
OUT=$(mkdir -p "${1:?usage: dry_run.sh <out dir> [run root]}" && cd "$1" && pwd)
ROOT=${2:-$M/experiments/reshape-test/20261020-0855-measure}
export WF_STUB=$D/tests/stub_runner.js MARIMO=${MARIMO:-/home/hal/dev/interp/janus/.venv-gpu/bin/marimo}
fails=0
expect() { if [ "$1" = "$2" ]; then echo "  ok   $3"; else echo "  FAIL $3 (got: $1)"; fails=$((fails + 1)); fi; }
error_of() { node -e 'const r = require(process.argv[1]); console.log(r.error ? r.error : "none")' "$1/digest/wf/result.json"; }
has() { case "$(error_of "$OUT/$1")" in *"$2"*) echo "  ok   $3: $(error_of "$OUT/$1" | cut -c1-150)";; *) echo "  FAIL $3 (got: $(error_of "$OUT/$1"))"; fails=$((fails + 1));; esac; }

# run <case> <stub dir> [fresh|keep|force]: fresh (default) empties the case directory; keep and force reuse it,
# force with args.force true
run() {
  local c=$OUT/$1 mode=${3:-fresh}
  [ "$mode" = fresh ] && { rm -rf "$c"; mkdir -p "$c/digest"; }
  printf '{"run_root": "%s", "out": "%s", "force": %s}\n' "$ROOT" "$c/digest" "$([ "$mode" = force ] && echo true || echo false)" > "$c/args.json"
  (cd "$M" && DIGEST_STUB_DIR=$2 DIGEST_STUB_LOG=$c/stub_calls.jsonl node dut/pipeline/idea/wf.js --config dut/digest/wf_config.json \
    --script dut/digest/pipeline.js --args "$c/args.json" --out "$c/digest/wf" --mode fallback --on-refusal halt > "$c/console.log" 2>&1)
}
# variant <case> <node statements on r (reader), v (verify), w (writer), n (notebook source)>: an edited copy of the stubs
variant() {
  local s=$OUT/stubs/$1; rm -rf "$s"; mkdir -p "$s"
  node -e 'const fs = require("fs"), [src, dst] = process.argv.slice(1), j = f => JSON.parse(fs.readFileSync(`${src}/${f}`, "utf8"))
    const r = j("reader.json"), v = j("verify.json"), w = j("writer.json"); let n = fs.readFileSync(`${src}/notebook.py`, "utf8"); '"$2"'
    for (const [f, x] of [["reader.json", r], ["verify.json", v], ["writer.json", w]]) fs.writeFileSync(`${dst}/${f}`, JSON.stringify(x, null, 1))
    fs.writeFileSync(`${dst}/notebook.py`, n)' "$STUB" "$s"
  echo "$s"
}

echo "== good: the hand-written m2 replies"
run good "$STUB"
G=$OUT/good/digest
expect "$(error_of "$OUT/good")" none "pipeline returned without error"
python3 -I "$D/check.py" "$G" > "$OUT/good/check.txt"; expect $? 0 "check.py passes on the written digest"
sed 's/^/       /' "$OUT/good/check.txt"
echo "  resolved calls (wf/journal.jsonl):"
node -e 'require("fs").readFileSync(process.argv[1], "utf8").trim().split("\n").map(JSON.parse).filter(r => r.type === "started")
  .forEach(r => console.log(`       ${r.label.padEnd(16)} ${r.role.padEnd(11)} tier ${r.tier.padEnd(7)} ${[r.model, ...r.chain].join(" -> ")}`))' "$G/wf/journal.jsonl"
expect "$(node -e 'require("fs").readFileSync(process.argv[1], "utf8").trim().split("\n").map(JSON.parse).filter(r => r.type === "started").forEach(r => process.stdout.write(`${r.label}:${[r.model, ...r.chain].join(">")} `))' "$G/wf/journal.jsonl")" \
  "reader:codex/default@high>claude/opus>opencode-go/mimo-v2.6-pro verify:codex/default@high>claude/opus>opencode-go/mimo-v2.6-pro writer:codex/default@high>claude/opus>opencode-go/mimo-v2.6-pro notebook:codex/default@medium>claude/sonnet>opencode-go/mimo-v2.6-pro " \
  "strong calls on codex@high then claude/opus then OpenCode; the notebook on codex@medium then claude/sonnet"
expect "$(node -e 'const l = require("fs").readFileSync(process.argv[1], "utf8").trim().split("\n").map(JSON.parse); console.log(l.map(x => `${x.label}:${x.tools}:${x.cwd === process.argv[2] ? "run" : x.cwd === process.argv[3] ? "digest" : "own"}`).join(" "))' "$OUT/good/stub_calls.jsonl" "$ROOT" "$G")" \
  "reader:Read,Glob,Grep:run verify::own writer::own notebook:Read,Glob,Grep:digest" "read-only tool lists; reader in the run root, notebook in the digest"
P=$G/wf/agents/0002-verify/prompt.md
expect "$(awk '/^## The reader.s answers/{a=NR} /^## The reader.s draft enums/{e=NR} /^## The files the reader cited/{f=NR} END {print (a < e && e < f) ? "in order" : "not"}' "$P")" "in order" "verify prompt: answers, then draft enums, then the files"
expect "$(node -e 'const s = require(process.argv[1]).summary; console.log(`${s.sentences} ${s.supported} ${s.contradicted} ${s.not_addressed}`)' "$G/VERIFY.json")" "36 34 1 1" "VERIFY.json: 36 cited sentences, the planted wrong cost contradicted, the planted guess not addressed"
expect "$(grep -c '^Contradicted: The box was billed 4.80 dollars' "$G/QA.md") $(grep -c '^Not addressed: A second run on a newer GPU' "$G/QA.md") $(grep -c '^Checked: ' "$G/QA.md")" "1 1 10" "QA.md: a check line per question, flagged sentences under it"
expect "$(grep -c '4\.80' "$G/DIGEST.md")" 0 "DIGEST.md carries no number from a contradicted sentence"
expect "$(grep -c 'sandbox": "bwrap"' "$G/CHECK.json")" 1 "the export ran inside bwrap"
python3 -I "$D/tests/planted_check.py" "$G" > "$OUT/good/planted.txt"; expect $? 0 "planted expectations for m2 hold on the stub digest (harness check only)"
printf '{"%s": {"enums": {"prediction_hit": "yes"}}}\n' "$(basename "$ROOT")" > "$OUT/planted_wrong.json"
python3 -I "$D/tests/planted_check.py" "$G" "$OUT/planted_wrong.json" > /dev/null; expect $? 1 "planted_check misses a wrong expectation"
expect "$(cd "$G" && ls evidence/_source)" RESULT.md "one-hop source card copied to evidence/_source/"
expect "$(grep -c '(\.\./\|(results_m2\|(RUN\.md)' "$G/DIGEST.md" "$G/QA.md" | awk -F: '{s += $2} END {print s}')" 0 "no citation left pointing outside evidence/"

echo "== refuse: the same command again, without force"
before=$(sha256sum "$G/DIGEST.md")
run good "$STUB" keep
has good "already holds a digest" "refused"
expect "$(sha256sum "$G/DIGEST.md")" "$before" "DIGEST.md untouched by the refused run"

echo "== force: the same command with force true"
run good "$STUB" force
expect "$(error_of "$OUT/good")" none "forced run returned without error"
expect "$(ls -d "$G"/wf/prev-* 2>/dev/null | wc -l)" 1 "the earlier journal and agents kept under wf/prev-*"

echo "== notebook export fails once: one repair call fixes it"
run repair "$(variant repair 'n = n.replace("    return E1, E3, E7", "    raise RuntimeError(\"planted export failure\")\n    return E1, E3, E7")')"
expect "$(error_of "$OUT/repair")" none "pipeline returned without error"
expect "$(ls "$OUT/repair/digest/wf/agents" | tr '\n' ' ')" "0001-reader 0002-verify 0003-writer 0004-notebook 0005-notebook-repair " "a repair call ran after the failed export"
expect "$(grep -c 'planted export failure' "$OUT/repair/digest/digest.py")" 0 "digest.py is the repaired source"

echo "== bad: notebook export fails twice"
s=$(variant repair2 'n = n.replace("    return E1, E3, E7", "    raise RuntimeError(\"planted export failure\")\n    return E1, E3, E7")'); touch "$s/repair_fails"
run repair2 "$s"
has repair2 "checks failed: notebook_export" "check fails, files left in place"

echo "== bad: the writer uses a number from a contradicted sentence"
run wnum "$(variant wnum 'w.analysis += " The box was billed 4.80 dollars for the launch (RUN.md)."')"
has wnum "checks failed: digest_numbers_verified" "check fails"

echo "== bad: a supported verdict with no quote"
run noquote "$(variant noquote 'v.overrides.push({match: "Both passed", verdict: "supported", quote: "", path: "RUN.md", reason: "x"})')"
has noquote "checks failed: quotes_verbatim" "check fails"

echo "== bad: a verify reply that skips a sentence (the keyed schema demands one entry per sentence)"
run skip "$(variant skip 'v.drop = ["S3"]')"
has skip "verify call returned nothing" "run failed"
expect "$(grep -o 'missing \\"S3\\"' "$OUT/skip/digest/wf/journal.jsonl" | head -1)" 'missing \"S3\"' "journal names the missing sentence"

echo "== a parenthesis that is not a path, such as (N/2), is left as prose"
run paren "$(variant paren 'r.answers.Q2.answer += " Each round of the parallel solver halves the system (N/2), as the source card says (../20261019-2344-tree/out/RESULT.md)."')"
expect "$(error_of "$OUT/paren")" none "pipeline returned without error"
expect "$(grep -c '(N/2)' "$OUT/paren/digest/QA.md")" 1 "(N/2) kept in QA.md"

echo "== bad: a citation to a file that does not exist"
run missing "$(variant missing 'r.citations.push({path: "results_m2/out/records/no-such-record.json", supports: "x"})')"
has missing "no such file" "run failed"
expect "$(ls "$OUT/missing/digest" | tr '\n' ' ')" "RUN.md wf " "nothing but RUN.md written; no evidence copied"

echo "== bad: a file outside the run that RUN.md does not name"
run hop "$(variant hop 'r.citations.push({path: "../20261019-2344-tree/out/run.json", supports: "x"})')"
has hop "one hop only" "run failed"

echo "== bad: a hidden file inside the run"
run hidden "$(variant hidden 'r.citations.push({path: ".last_lambda_instance", supports: "x"})')"
has hidden "hidden or credential" "run failed"

echo "== bad: an answer with an uncited number"
run uncited "$(variant uncited 'r.answers.Q7.answer += " The anchor used 2 sizes and 5 seeds."')"
has uncited "checks failed: numbers_cited" "check fails"
expect "$(cd "$OUT/uncited/digest" && ls DIGEST.md QA.md VERIFY.json digest.json digest.py MANIFEST.json CHECK.json RUN.md 2>/dev/null | wc -l)" 8 "files left in place with CHECK.json"

echo "dry run: $([ $fails = 0 ] && echo 'all expectations met' || echo "$fails failure(s)") · $OUT"
exit $([ $fails = 0 ] && echo 0 || echo 1)
