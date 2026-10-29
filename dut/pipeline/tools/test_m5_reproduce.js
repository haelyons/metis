#!/usr/bin/env node
'use strict'

// Black-box contract tests. Do not inspect the pipeline, scorer, or git diff.
// Usage: node tools/test_m5_reproduce.js [--profile-only]
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawn, spawnSync } = require('node:child_process')
const ROOT = path.resolve(__dirname, '..')
const fixture = require('./m5_profile_fixture.js')
const PROBE_SENTINEL = 'PROBE_PRIVATE_SENTINEL_197352'
const SENTINEL = 'HARNESS_PRIVATE_SENTINEL_846291'
const STAGES = ['intake', 'reproduce', 'profile', 'seal', 'propose', 'implement', 'evaluate', 'takeaways']
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
function writeJSON(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value) + '\n')
}
const anchor = (id, published_value, tolerance, extra = {}) => ({ id, published_value, tolerance, quantity: 'fixture quantity', source: 'https://example.org/published', ...extra })
// SCHEMAS.md A/intake/: a reference is an "==" item (explicit or default) with null tolerance.
const reference = (id, published_value, extra = {}) => anchor(id, published_value, null, extra)
const isReference = item => (item.comparison ?? '==') === '==' && item.tolerance === null
const ANCHORS = [anchor('first', 100, { abs: 1 }), anchor('second', 0, 0)]
const TIMINGS = [{ stage: 'cpu', kind: 'other', wall_s: 3, gpu_s: null, start_s: 0 },
  { stage: 'h2d', kind: 'transfer', wall_s: 2, gpu_s: null, start_s: 3 },
  { stage: 'compute', kind: 'compute', wall_s: 4.5, gpu_s: 0, start_s: 5 }]
const GPU_UTIL = [{ t: 0, util: 0 }, { t: 1, util: 75 }, { t: 3, util: 50 },
  { t: 5, util: 25 }, { t: 6, util: 25 }]
const PREDICTIONS = {
  outputs_stochastic: false,
  predictions: [{ method: 'batching', expected_speedup_interval: { low: 1.1, high: 2 },
    outcome_vs_compute_points: [1, 2, 4].map(compute_budget => ({ compute_budget, predicted_outcome: 100, uncertainty: 'exact' })) }],
  equivalence_metrics: ['exact equality'], paired_seed_tests: [0, 1, 2, 3, 4], sample_sizes: { n: 10 },
  confidence_rule: 'paired 95% interval', hardware_cost_basis: 'same CPU', timing_scope: 'whole process',
  minimum_worthwhile_gain: 1.1, evaluation_inputs: ['fixture'], splits: { evaluation: [0, 10] },
  compute_budgets: [1, 2, 4], repetitions: 5, warmup: 'one run', scheduling_order: 'alternate', equal_outcome_target: 100,
}
function script(file, body) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, '#!/usr/bin/env bash\nset -eu\n' + body + '\n')
  fs.chmodSync(file, 0o700)
}
function emitJSON(file, value) {
  return `cat > '${file}' <<'M5_FIXTURE_JSON'\n${JSON.stringify(value)}\nM5_FIXTURE_JSON\n`
}
// `staleFreeze` leaves a reproduce-out/ in the run directory before the freeze (SCHEMAS.md reproduce bullet:
// the freeze runs `test ! -e reproduce-out` first).
function setupScript(directory, failures, staleFreeze = false) {
  script(path.join(directory, 'setup.sh'), `mkdir -p out baseline-published data${staleFreeze ? "\nmkdir -p reproduce-out\nprintf '%s\\n' stale > reproduce-out/stale-marker" : ''}
printf '%s\\n' '${SENTINEL}:setup'
n=0
[[ ! -f .setup-attempts ]] || read -r n < .setup-attempts
n=$((n + 1))
printf '%s\\n' "$n" > .setup-attempts
printf '%s\\n' '${SENTINEL}' > out/setup-private.txt
${failureLog('setup', failures)}
printf '%s\\n' pinned > baseline-published/pin
printf '%s\\n' representative > data/input`)
}
// SCHEMAS.md "A/harness/": the anchors repair may rewrite run_anchors.sh, run_command.sh, or both.
// `anchorsRepairTarget` chooses which scripts fail initially and which the fake repair rewrites.
const ANCHORS_REPAIR_SCRIPTS = { 'run_anchors.sh': ['run_anchors.sh'], 'run_command.sh': ['run_command.sh'],
  both: ['run_anchors.sh', 'run_command.sh'] }
const anchorsRepairScripts = config => ANCHORS_REPAIR_SCRIPTS[config.anchorsRepairTarget ?? 'run_anchors.sh']
// The script whose failure log reaches the anchors repair prompt (run_anchors.sh fails first when both fail).
const anchorsFailureName = config => anchorsRepairScripts(config)[0] === 'run_command.sh' ? 'command' : 'anchors'
// Files a repair may not change; written by the fake agent to prove they are never uploaded or run.
const STRAY = name => `printf '%s\\n' stray > out/stray-${name}\nexit 9`
function snapshot(directory, destination) {
  fs.mkdirSync(destination, { recursive: true })
  for (const name of fs.readdirSync(directory)) fs.copyFileSync(path.join(directory, name), path.join(destination, name))
}
function failureLog(name, failures) {
  return `if (( n <= ${failures} )); then
  for ((i=1; i<=240; i++)); do printf '%s:%s:%s\\n' '${SENTINEL}' '${name}' "$i"; done
  exit 7
fi`
}
function failureScript(name, failures) {
  return `printf '%s\\n' '${SENTINEL}:${name}'
n=0
[[ ! -f .${name}-attempts ]] || read -r n < .${name}-attempts
n=$((n + 1))
printf '%s\\n' "$n" > .${name}-attempts
${failureLog(name, failures)}\n`
}
module.exports = {
  async run({ title, prompt, name }) {
    const root = process.env.M5_REPRODUCE_ROOT
    const config = JSON.parse(process.env.M5_REPRODUCE_CONFIG)
    fs.appendFileSync(process.env.M5_REPRODUCE_CALLS, JSON.stringify({ label: title, prompt, name, probeFetched: fs.existsSync(path.join(root, 'agent', 'results', 'probe', 'probe.json')) }) + '\n')
    if (config.agentDelayMs) await new Promise(resolve => setTimeout(resolve, config.agentDelayMs))
    const agent = path.join(root, 'agent')
    let facts = { v: `${title} stub` }
    if (title === 'intake') {
      facts = { found: true, anchors_count: config.anchors.length, data: 'available', licence: 'permitted', stock_environment: true, size: 'tiny' }
      const fixtures = {
        benchmark: { identity: 'contract fixture', outcome_definition: 'fixture quantity', citations: ['https://example.org/published'] },
        data: { availability: 'available', licences: ['MIT'], required_inputs: ['fixture'] },
        anchors: config.anchors,
        baseline: { repo: 'https://example.org/fixture', pin: 'fixture-v1', build_commands: ['true'], run_commands: ['true'], published_configuration: { n: 10 } },
        EXECUTION: { representative_scale: { n: 10 }, inputs: ['fixture'], outputs: ['quantity'], timing_scope: 'whole process', timeout_s: 10 },
      }
      for (const [name, value] of Object.entries(fixtures)) writeJSON(path.join(agent, 'intake', `${name}.json`), value)
      fs.writeFileSync(path.join(agent, 'intake', 'brief.md'), 'Synthetic contract fixture.\n')
    }
    if (['harness', 'harness-repair', 'anchors-repair'].includes(title)) {
      const harness = path.join(agent, 'harness')
      // A successful repair must replace the script; rerunning the original cannot pass.
      const failuresFor = field => config[field] && (title === 'harness' || config[field] >= 2) ? 999 : 0
      const targets = anchorsRepairScripts(config)
      const writes = file => title === 'harness' || (title === 'anchors-repair' && targets.includes(file))
      const anchorsFailures = file => targets.includes(file) ? failuresFor('anchorsFailures') : 0
      // Rewritten scripts carry a marker so their remote bytes can be identified.
      const marker = title === 'anchors-repair' ? '# rewritten by anchors-repair\n' : ''
      if (title === 'harness-repair' || title === 'anchors-repair') snapshot(harness, path.join(root, `pre-${title}`))
      if (title === 'harness' || title === 'harness-repair') setupScript(harness, failuresFor('setupFailures'), config.freezeFailure === 'stale')
      if (writes('run_anchors.sh')) {
        script(path.join(harness, 'run_anchors.sh'), marker + failureScript('anchors', anchorsFailures('run_anchors.sh')) + `bash harness/run_command.sh\ntest -f baseline-published/pin\ntest -f data/input\nmkdir -p out\nprintf '%s\\n' '${SENTINEL}:anchors'\n` +
          (config.missingMeasured ? 'rm -f out/anchors_measured.json\n' : emitJSON('out/anchors_measured.json', config.measured)) +
          `printf '%s\\n' '${SENTINEL}' > out/anchors-private.txt`)
      }
      // clearMps models a harness that breaks the CUDA MPS rule (like positive-openmm run1's).
      if (writes('run_command.sh')) script(path.join(harness, 'run_command.sh'), marker +
        (config.clearMps ? 'unset CUDA_MPS_PIPE_DIRECTORY CUDA_MPS_LOG_DIRECTORY\n' : '') +
        (anchorsFailures('run_command.sh') ? failureScript('command', anchorsFailures('run_command.sh')) : '') +
        `test -f baseline-published/pin\ntest -f data/input\n! command -v fake-cuda-client > /dev/null || fake-cuda-client\nprintf '%s\\n' '${SENTINEL}:command' >> out/command-calls.log` +
        (title === 'anchors-repair' ? `\nmkdir -p out\nprintf '%s\\n' rerun > out/rewritten-command.txt` : ''))
      // An anchors repair that also edits setup.sh/run_evaluation.sh; a setup repair that also edits the anchor scripts.
      if (title === 'anchors-repair' && config.anchorsRepairStray) {
        script(path.join(harness, 'setup.sh'), STRAY('setup'))
        script(path.join(harness, 'run_evaluation.sh'), STRAY('evaluation'))
      }
      if (title === 'harness-repair' && config.setupRepairStray) {
        script(path.join(harness, 'run_anchors.sh'), STRAY('anchors'))
        script(path.join(harness, 'run_command.sh'), STRAY('command'))
      }
      // What the repair left behind, before the pipeline may revert files outside the repair's scope.
      if (title === 'harness-repair' || title === 'anchors-repair') snapshot(harness, path.join(root, `post-${title}`))
    }
    if (title === 'seal') {
      const bounds = readJSON(path.join(agent, 'bounds.json'))
      const predictions = Object.entries(bounds).filter(([, value]) => value.feasible).map(([method, value]) => ({
        ...PREDICTIONS.predictions[0], method, expected_speedup_interval: { low: 1, high: 1 + (value.bound - 1) / 2 },
      }))
      const infeasible_methods = Object.entries(bounds).filter(([, value]) => !value.feasible)
        .map(([method]) => ({ method, reason: 'Amdahl bound below 1.05' }))
      writeJSON(path.join(agent, 'PREDICTIONS.json'), { ...PREDICTIONS, predictions, infeasible_methods })
      facts = { seal_present: true, seal_verified: true, prediction_count: predictions.length }
    }
    return { text: JSON.stringify(facts), json: facts, jsonError: null, sessionID: 'stub',
      tokens: { input: 10, output: 5, reasoning: 0 }, cost: 0.001, tools: 0, ms: 5, errors: [], refusal: false }
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
  assertMpsRule,
  assertRunCommandRules,
  assertEvalShapes,
}
// SCHEMAS.md evaluation adapter environment: "`EVAL_INPUTS` is an object whose `ids` array lists the
// sealed input identities in order; each record's `input_id` is one of those strings, and every other key
// ... is never itself an input. `EVAL_SEEDS` is either `{kind:"paired_median",seeds:[integer,...]}`, whose
// seeds are the execution seeds in order, or `{kind:"deterministic",...}`, whose single execution seed is
// null ... The harness prompt ... and the method author prompt both state these two shapes."
// Checked by meaning in a window after each mention of the variable, not by exact wording.
function assertEvalShapes(prompt, label) {
  const shape = (variable, meanings) => {
    const windows = [...prompt.matchAll(new RegExp(variable, 'g'))].map(match => prompt.slice(Math.max(0, match.index - 150), match.index + 900))
    assert.ok(windows.length, `${label}: prompt never names ${variable}`)
    const missing = window => meanings.filter(([pattern]) => !pattern.test(window)).map(([, meaning]) => meaning)
    const best = windows.map(missing).sort((a, b) => a.length - b.length)[0]
    assert.deepEqual(best, [], `${label}: ${variable} shape lacks ${best.join(', ')}`)
  }
  shape('EVAL_INPUTS', [[/\bobject\b/i, 'an object'], [/\bids\b/, 'the ids key'], [/\b(array|list)/i, 'ids is an array'],
    [/\border/i, 'ids are in order'], [/\binput_id\b/, 'record input_id values'],
    [/\binput_id\b[^.\n]{0,160}\b(one of|from|in|among|is|are|equals?|match\w*)\b[^.\n]{0,80}\b(ids|those|these|the) (strings|identit|IDs?)|\binput_id\b[^.\n]{0,120}\bids\b|\bids\b[^.\n]{0,160}\binput_id\b/i,
      'input_id values are the ids strings'],
    [/\b(other|every other|all other|remaining|additional|extra|any other)\b[^.\n]{0,30}\bkeys?\b[^.\n]{0,250}\b(never|not|aren't|isn't)\b[^.\n]{0,80}\binputs?\b|\b(never|not|do not|don't)\b[^.\n]{0,40}\b(treat|iterate|use|interpret|loop)\w*\b[^.\n]{0,80}\b(other|any|every|non-ids?)\b[^.\n]{0,30}\bkeys?\b[^.\n]{0,80}\binputs?\b/i,
      'other keys are never inputs']])
  shape('EVAL_SEEDS', [[/paired_median/, 'paired_median'], [/\bseeds\b/, 'the seeds key'], [/\bintegers?\b/i, 'integer seeds'],
    [/\border/i, 'seeds are in order'], [/\bdeterministic\b/, 'deterministic'],
    [/\b(single|one|exactly one|only)\b[^.\n]{0,60}\bnull\b|\bnull\b[^.\n]{0,60}\b(single|one|only)\b|\[\s*null\s*\]/i, 'a single null seed']])
}
// SCHEMAS.md "The pipeline owns CUDA MPS": harness and repair prompts state that harness scripts
// must not set, unset or override CUDA_MPS_* variables, or start or stop an MPS daemon.
// Checked by meaning near a mention of CUDA_MPS_, not by exact wording.
function assertMpsRule(prompt, label) {
  const meanings = [[/\b(must not|must never|never|do not|don't|may not|cannot|forbidden|prohibited)\b/i, 'a prohibition'],
    [/\bset\b/i, 'set'], [/\bunset/i, 'unset'], [/\boverrid/i, 'override'],
    [/\bdaemon/i, 'MPS daemon'], [/\bstart/i, 'start'], [/\bstop/i, 'stop']]
  const windows = [...prompt.matchAll(/CUDA_MPS_/g)].map(match => prompt.slice(Math.max(0, match.index - 400), match.index + 600))
  assert.ok(windows.length, `${label}: prompt never names CUDA_MPS_* variables`)
  const missing = window => meanings.filter(([pattern]) => !pattern.test(window)).map(([, meaning]) => meaning)
  const best = windows.map(missing).sort((a, b) => a.length - b.length)[0]
  assert.deepEqual(best, [], `${label}: MPS rule lacks ${best.join(', ')}`)
}
if (require.main !== module) return

let failures = 0
let checks = 0
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_reproduce_'))
// All relative paths and module paths resolve inside this temporary checkout.
// Exclude the real ledger and use M5_RAIDS_LEDGER for every workflow.
const pipeline = path.join(scratch, 'pipeline')
for (const directory of ['m5', 'idea', 'measure']) fs.cpSync(path.join(ROOT, directory), path.join(pipeline, directory), {
  recursive: true, filter: source => !['experiments', 'raids_used.jsonl'].includes(path.basename(source)),
})
const raidsLedger = path.join(scratch, 'raids_used.jsonl')
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}
function noLeak(directory) {
  assert.ok(fs.statSync(directory).isDirectory())
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    assert.ok(!entry.name.includes(SENTINEL) && !entry.name.includes(PROBE_SENTINEL), 'sentinel in filename')
    assert.ok(!entry.isSymbolicLink(), 'operator symlink')
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) noLeak(file)
    else for (const sentinel of [SENTINEL, PROBE_SENTINEL]) assert.ok(!fs.readFileSync(file).includes(Buffer.from(sentinel)), `private content leaked: ${entry.name}`)
  }
}
async function runCase(name, overrides = {}, stoppedAt = null, errorClass = null) {
  const root = path.join(scratch, name)
  const config = { anchors: ANCHORS, measured: { first: 100.5, second: 0, ignored: 999 }, timings: TIMINGS, total: 10, gpuUtil: GPU_UTIL, setupFailures: 0, anchorsFailures: 0, profileFailures: 0, ...overrides }
  const args = path.join(root, 'control', 'args.json')
  writeJSON(args, { run_root: root, tag: 'reproduce-test', stub: { propose: 'PASS', implement: 'PASS', evaluate: 'PASS' },
    ...(config.profileBudget || config.anchorsBudget || config.setupBudget ? { stage_budgets_s: {
      ...(config.profileBudget ? { profile: config.profileBudget } : {}),
      ...(config.anchorsBudget ? { anchors: config.anchorsBudget } : {}),
      ...(config.setupBudget ? { setup: config.setupBudget } : {}) } } : {}) })
  const box = path.join(root, 'box')
  fs.mkdirSync(box, { recursive: true })
  const fakeProbe = `mkdir -p out
printf '%s\\n' '{"label":"probe"}' >> "$M5_REPRODUCE_CALLS"
${config.probeFailure === 'rc' ? 'exit 7' : config.probeFailure === 'json' ? "printf '%s\\n' 'invalid probe JSON' > out/probe.json" : emitJSON('out/probe.json', { kernel: PROBE_SENTINEL, cmake: null, nvcc: [] })}`
  const replaceProbe = path.join(root, 'replace-probe.js')
  fs.writeFileSync(replaceProbe, `
const fs = require('node:fs'), path = require('node:path')
const original = ${JSON.stringify(fs.readFileSync(path.join(ROOT, 'm5', 'box_probe.sh'), 'utf8'))}
function visit(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) visit(file)
    else if (entry.isFile() && entry.name.endsWith('.sh') && fs.readFileSync(file, 'utf8') === original) {
      fs.appendFileSync(process.env.M5_REPRODUCE_CALLS, JSON.stringify({ label: 'probe-upload' }) + '\\n')
      fs.writeFileSync(file, ${JSON.stringify('#!/usr/bin/env bash\nset -eu\n' + fakeProbe + '\n')})
    }
  }
}
visit(process.env.BOX_ROOT)
require(${JSON.stringify(path.join(ROOT, 'tools/m5_profile_fixture.js'))}).replace(process.env.BOX_ROOT, JSON.parse(process.env.M5_REPRODUCE_CONFIG))
`)
  // Map the contract's absolute remote /tmp/m5-* paths into this case's box.
  const boxBin = path.join(root, 'box-bin')
  // Keep receipt telemetry unavailable regardless of the host's GPU tools.
  script(path.join(boxBin, 'nvidia-smi'), 'exit 1')
  // Never start a host MPS daemon: the real probe sees this fake control binary. Like the real
  // daemon it writes control.log in CUDA_MPS_LOG_DIRECTORY; its control endpoint in
  // CUDA_MPS_PIPE_DIRECTORY lets fake-cuda-client connect until quit.
  script(path.join(boxBin, 'nvidia-cuda-mps-control'), `calls="$BOX_ROOT/../mps-calls.log"
if [[ $# -gt 0 ]]; then
  printf 'args %s\\n' "$*" >> "$calls"
  if [[ -n \${CUDA_MPS_PIPE_DIRECTORY-} && -n \${CUDA_MPS_LOG_DIRECTORY-} ]]; then
    mkdir -p "$CUDA_MPS_PIPE_DIRECTORY" "$CUDA_MPS_LOG_DIRECTORY"
    printf '[fixture Control 1] Starting control daemon\\n' >> "$CUDA_MPS_LOG_DIRECTORY/control.log"
    printf '%s\\n' "$CUDA_MPS_LOG_DIRECTORY" > "$CUDA_MPS_PIPE_DIRECTORY/control"
  fi
else
  input=$(cat)
  printf 'stdin %s\\n' "$input" >> "$calls"
  [[ $input != quit || -z \${CUDA_MPS_PIPE_DIRECTORY-} ]] || rm -f "$CUDA_MPS_PIPE_DIRECTORY/control"
fi`)
  // freezeFailure 'timeout': the documented freeze copy `cp -a out reproduce-out` outlasts the setup budget.
  const realCp = spawnSync('/bin/bash', ['-c', 'command -v cp'], { encoding: 'utf8' }).stdout.trim()
  script(path.join(boxBin, 'cp'), `${config.freezeFailure === 'timeout' ? '[[ $# -lt 1 || ${!#} != reproduce-out ]] || sleep 8\n' : ''}exec '${realCp}' "$@"`)
  // Fake CUDA program run by the stub harness command: connects only through the daemon's pipe directory.
  script(path.join(boxBin, 'fake-cuda-client'), `if [[ -n \${CUDA_MPS_PIPE_DIRECTORY-} && -f $CUDA_MPS_PIPE_DIRECTORY/control ]]; then
  log="$(cat "$CUDA_MPS_PIPE_DIRECTORY/control")/control.log"
  [[ ! -f $log ]] || printf '[fixture Control 1] NEW CLIENT %s from user %s: Server already exists\\n' "$$" "$(id -u)" >> "$log"
fi`)
  // The probe may be written by the same command that runs it, so substitute the fake
  // at the documented invocation `python3 -I profiler/concurrency_probe.py ...`.
  const realPython = spawnSync('/bin/bash', ['-c', 'command -v python3'], { encoding: 'utf8' }).stdout.trim()
  const fakeConcurrency = path.join(root, 'fake-concurrency-probe.py')
  if (config.concurrency && config.concurrency !== 'real') fs.writeFileSync(fakeConcurrency, fixture.concurrencyProbe(config.concurrency))
  script(path.join(boxBin, 'python3'), `[[ $# -lt 2 || $1 != -I || $2 != profiler/concurrency_probe.py ]] || : > "$BOX_ROOT/../concurrency-ran"
if [[ $# -ge 2 && $1 == -I && $2 == profiler/concurrency_probe.py && -f '${fakeConcurrency}' ]]; then
  cp -- '${fakeConcurrency}' profiler/concurrency_probe.py
fi
exec '${realPython}' "$@"`)
  // Recorded run11 (positive-openmm): after the concurrency probe exited 0, the out/ fetch stalled
  // after two files and the log fetch failed. With config.concurrencyFetchFailures = N, the first N
  // attempts of each concurrency fetch fail, the out/ attempts after copying a partial tree
  // without concurrency.json. Counters record every attempt.
  const failingFetch = config.concurrencyFetchFailures ? `if [[ -f $BOX_ROOT/../concurrency-ran ]]; then
  kind=out
  if [[ $source == *.log ]]; then kind=log; [[ $source == *-concurrency.log ]] || kind=; fi
  if [[ -n $kind ]]; then
    counter="$BOX_ROOT/../concurrency-fetch-$kind"
    count=0
    [[ ! -f $counter ]] || read -r count < "$counter"
    count=$((count + 1))
    printf '%s\\n' "$count" > "$counter"
    if (( count <= ${Number(config.concurrencyFetchFailures)} )); then
      if [[ $kind == out ]]; then
        partial=$(mktemp -d)
        name=$(basename -- "$source")
        cp -r -- "$source" "$partial/$name"
        rm -f -- "$partial/$name/concurrency/concurrency.json"
        cp -r -- "$partial/$name" "$2"
        rm -rf -- "$partial"
      fi
      echo 'simulated stalled fetch' >&2
      exit 1
    fi
  fi
fi
` : ''
  // Before the first box command after an anchors receipt, keep a copy of the anchor run's remote
  // out/ in anchor-out/<receipt-id>/ (the latest one is what the freeze must copy).
  const anchorSnapshot = `latest=
for receipt in "$BOX_ROOT"/../control/receipts/*.json; do [[ ! -e $receipt ]] || latest=$receipt; done
if [[ $latest == *-anchors.json ]]; then
  snapshot="$BOX_ROOT/../anchor-out/$(basename -- "\${latest%.json}")"
  if [[ ! -e $snapshot ]]; then
    for remote in "$BOX_ROOT"/m5-*; do
      [[ ! -d $remote/out || ! -d $remote/harness ]] || { mkdir -p "$snapshot"; cp -a "$remote/out/." "$snapshot/"; }
    done
  fi
fi
`
  script(path.join(root, 'bin', 'box'), 'command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}' + '\nexport PATH="$BOX_ROOT/../box-bin:$PATH"\ncd -- "$BOX_ROOT"\n' + anchorSnapshot + 'bash -c "$command"\n"$M5_TEST_NODE" "$M5_REPLACE_PROBE"\n# Let tiny detached fixtures finish before the runner polls.\nif [[ $command == *timeout* ]]; then\n  for ((i=0; i<1000; i++)); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi\nexit 0' )
  // freezeFailure 'fetch': every fetch of the freeze log fails, so the freeze receipt has fetched=false.
  const failingFreezeFetch = config.freezeFailure === 'fetch' ? `[[ $source != *-reproduce-freeze.log ]] || { echo 'simulated failed fetch' >&2; exit 1; }\n` : ''
  script(path.join(root, 'bin', 'fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}' + '\ncd -- "$BOX_ROOT"\n' + failingFetch + failingFreezeFetch + 'exec cp -r -- "$source" "$2"')
  const callsFile = path.join(root, 'calls.jsonl')
  const stdout = fs.openSync(path.join(root, 'stdout.log'), 'w')
  const stderrFile = path.join(root, 'stderr.log')
  const stderr = fs.openSync(stderrFile, 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(pipeline, 'idea', 'wf.js'), '--script', path.join(pipeline, 'm5', 'pipeline.js'),
        '--args', args, '--out', path.join(root, 'agent', 'wf'), '--disable-family', 'claude'], {
        cwd: pipeline, timeout: 240000, killSignal: 'SIGKILL', stdio: ['ignore', stdout, stderr], env: { ...process.env,
          M5_RAIDS_LEDGER: raidsLedger, WF_STUB: __filename, M5_REPRODUCE_ROOT: root, M5_REPRODUCE_CONFIG: JSON.stringify(config), M5_REPRODUCE_CALLS: callsFile,
          M5_CONCURRENCY_CALLS: path.join(root, 'concurrency-calls.jsonl'),
          M5_TEST_NODE: process.execPath, M5_REPLACE_PROBE: replaceProbe, BOX_ROOT: box, BOX: path.join(root, 'bin', 'box'), FETCH: path.join(root, 'bin', 'fetch'),
          // Failing fetches are retried after BOXRUN_FETCH_WAIT_S; 1 s keeps the fixture fast yet measurable.
          ...(config.concurrencyFetchFailures ? { BOXRUN_FETCH_WAIT_S: config.concurrencyFetchFailures >= 5 ? '0' : '1' } : {}),
          ...(config.freezeFailure === 'fetch' ? { BOXRUN_FETCH_WAIT_S: '0' } : {}) },
      })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  check(`${name}: workflow completes`, () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0, `exit ${child.status}, signal ${child.signal}; ${fs.readFileSync(stderrFile, 'utf8').slice(-500)}`)
  })
  const stages = rows(path.join(root, 'operator', 'signatures.jsonl')).filter(row => STAGES.includes(row.signature?.stage))
  const stage = label => { const found = stages.find(row => row.signature.stage === label); assert.ok(found, `missing ${label}`); return found }
  const calls = rows(callsFile)
  check(`${name}: ordered statuses and takeaways`, () => {
    assert.deepEqual(stages.map(row => [row.signature.stage, row.signature.status]), STAGES.map((label, i) =>
      [label, label === stoppedAt ? 'FAIL' : stoppedAt && i > STAGES.indexOf(stoppedAt) && label !== 'takeaways' ? 'SKIPPED' : 'PASS']))
    if (stoppedAt) assert.ok(!calls.some(call => ['seal', 'propose', 'implement', 'evaluate'].includes(call.label)), 'scientific call after failure')
  })
  if (stoppedAt) check(`${name}: failure signature`, () => {
    const signature = stage(stoppedAt).signature
    assert.equal(signature.error_class, errorClass)
    assert.equal(signature.exit_code, errorClass === 'anchor' ? 4 : errorClass === 'timeout' ? 3 : 2)
  })
  check(`${name}: one harness call and bounded repair`, () => {
    assert.equal(calls.filter(call => call.label === 'harness').length, config.probeFailure ? 0 : 1)
    assert.equal(calls.filter(call => call.label === 'profile-repair').length, 0)
    for (const [label, needed] of [['harness-repair', config.setupFailures],
      ['anchors-repair', config.setupFailures < 2 && config.anchorsFailures]]) {
      assert.equal(calls.filter(call => call.label === label).length, needed ? 1 : 0, label)
      for (const call of calls.filter(call => call.label === label)) {
        assert.match(call.name, /-retry1$/, label)
        const script = label === 'harness-repair' ? 'setup' : anchorsFailureName(config)
        assert.ok(call.prompt.includes(`${SENTINEL}:${script}:240`), 'last failure log line missing')
        assert.ok(!call.prompt.includes(`${SENTINEL}:${script}:1\n`), 'unbounded failure log')
      }
    }
  })
  check(`${name}: harness and repair prompts state the pipeline-owned CUDA MPS rule`, () => {
    const prompts = calls.filter(call => ['harness', 'harness-repair', 'anchors-repair'].includes(call.label))
    if (!config.probeFailure) assert.ok(prompts.length >= 1, 'no harness prompt')
    for (const call of prompts) assertMpsRule(call.prompt, call.label)
  })
  if (!config.probeFailure) check(`${name}: harness prompt asks for run_evaluation.sh and states the EVAL_INPUTS and EVAL_SEEDS shapes`, () => {
    const harness = calls.filter(call => call.label === 'harness')
    assert.ok(harness.length >= 1, 'no harness prompt')
    for (const call of harness) {
      assert.match(call.prompt, /run_evaluation\.sh/, 'harness prompt never asks for run_evaluation.sh')
      assertEvalShapes(call.prompt, call.label)
    }
  })
  if (calls.some(call => call.label === 'anchors-repair')) check(`${name}: anchors repair prompt states that a rewritten run_command.sh obeys every run_command.sh rule`, () => {
    for (const call of calls.filter(call => call.label === 'anchors-repair')) assertRunCommandRules(call.prompt, call.label)
  })
  check(`${name}: fixed profiler uses shared command without profile agent`, () => {
    assert.ok(!calls.some(call => /profile/.test(call.label)))
    if (!config.probeFailure) assert.ok(!fs.existsSync(path.join(root, 'agent/harness/profile.sh')))
    if (stoppedAt !== 'reproduce') {
      const log = fs.readFileSync(path.join(root, 'agent/results/profile/out/command-calls.log'), 'utf8')
      assert.equal(log.trim().split('\n').length, 2, 'anchors and profiler must each invoke shared command once')
    }
  })
  check(`${name}: probe precedes harness and reaches every prompt`, () => {
    const labels = calls.map(call => call.label)
    assert.equal(labels.filter(label => label === 'probe-upload').length, 1)
    assert.equal(labels.filter(label => label === 'probe').length, 1)
    assert.ok(labels.indexOf('probe-upload') < labels.indexOf('probe'))
    if (config.probeFailure) {
      assert.ok(!calls.some(call => ['harness', 'harness-repair', 'anchors-repair'].includes(call.label)))
    } else {
      assert.ok(labels.indexOf('probe') < labels.indexOf('harness'))
      const probe = readJSON(path.join(root, 'agent', 'results', 'probe', 'probe.json'))
      assert.equal(probe.kernel, PROBE_SENTINEL)
      for (const call of calls.filter(call => ['harness', 'harness-repair', 'anchors-repair'].includes(call.label))) {
        assert.equal(call.probeFetched, true, `${call.label}: probe not fetched before call`)
        assert.ok(call.prompt.includes(PROBE_SENTINEL), `${call.label}: probe content missing`)
      }
    }
  })
  check(`${name}: receipts under C/receipts`, () => {
    const directory = path.join(root, 'control', 'receipts')
    const files = fs.readdirSync(directory).sort()
    const receipts = files.map(file => {
      assert.match(file, /^\d{4}-[a-z-]+\.json$/)
      const receipt = readJSON(path.join(directory, file))
      assert.equal(receipt.name, file.slice(0, -5))
      // Only the deliberately slow concurrency probe may time out.
      if (config.concurrency === 'timeout' && file.slice(5, -5) === 'concurrency') return { operation: 'concurrency', ...receipt }
      // The deliberately slow freeze copy times out (checked in freezeChecks).
      if (config.freezeFailure === 'timeout' && file.slice(5, -5) === 'reproduce-freeze') return { operation: 'reproduce-freeze', ...receipt }
      assert.ok(Number.isInteger(receipt.rc))
      assert.equal(receipt.timed_out, false)
      // Only the concurrency fetch that fails on all five attempts, or the deliberately failed
      // freeze log fetch, leaves fetched false.
      assert.equal(receipt.fetched, !(config.concurrencyFetchFailures >= 5 && file.slice(5, -5) === 'concurrency') &&
        !(config.freezeFailure === 'fetch' && file.slice(5, -5) === 'reproduce-freeze'), file)
      assert.ok(Number.isInteger(receipt.wall_s) && receipt.wall_s >= 0)
      for (const key of ['started_utc', 'ended_utc']) assert.ok(Number.isFinite(Date.parse(receipt[key])))
      return { operation: file.slice(5, -5), ...receipt }
    })
    assert.deepEqual(files.map(file => Number(file.slice(0, 4))), files.map((_, i) => i + 1))
    const probeIndex = receipts.findIndex(receipt => receipt.operation.includes('probe') && !receipt.operation.includes('upload'))
    assert.ok(probeIndex >= 1, 'probe run receipt missing or no upload before probe')
    assert.ok(receipts.slice(0, probeIndex).every(receipt => receipt.operation.includes('upload')), 'probe upload receipt missing')
    assert.equal(receipts[probeIndex].rc, config.probeFailure === 'rc' ? 7 : 0)
    if (config.probeFailure) {
      assert.equal(receipts.length, probeIndex + 1, 'commands executed after failed probe')
      return
    }
    receipts.splice(0, probeIndex + 1)
    // SCHEMAS.md reproduce bullet: when reproduce passes (and only then, apart from a failing freeze
    // itself), exactly one `reproduce-freeze` under the setup budget follows the anchor run; profile
    // commands come after it, and nothing runs after a failed freeze.
    const freezes = receipts.filter(receipt => receipt.operation === 'reproduce-freeze')
    const froze = stoppedAt !== 'reproduce' || Boolean(config.freezeFailure)
    assert.equal(freezes.length, froze ? 1 : 0, `freeze receipts: ${receipts.map(r => r.operation).join(',')}`)
    if (froze) {
      const at = receipts.indexOf(freezes[0])
      const lastAnchors = receipts.findLastIndex(receipt => receipt.operation === 'anchors')
      assert.ok(lastAnchors >= 0 && lastAnchors < at, 'freeze before the anchor run')
      assert.ok(receipts.slice(lastAnchors + 1, at).every(receipt => receipt.operation === 'upload'), receipts.map(r => r.operation).join(','))
      assert.ok(receipts.slice(at + 1).every(receipt => ['upload', 'profile', 'concurrency'].includes(receipt.operation)),
        `reproduce command after the freeze: ${receipts.map(r => r.operation).join(',')}`)
      if (config.freezeFailure) assert.equal(at, receipts.length - 1, 'box commands after a failed freeze')
      assert.equal(freezes[0].budget_s, config.setupBudget ?? 1200, 'freeze must use the setup budget')
      if (!config.freezeFailure) assert.equal(freezes[0].rc, 0)
      receipts.splice(at, 1)
    }
    // SCHEMAS.md "Concurrency probe": after a passing gate, optional upload(s) then exactly one
    // `concurrency` command (no execution retry); nothing after a failed profile.
    const profileAt = receipts.findIndex(receipt => receipt.operation === 'profile')
    const afterProfile = profileAt < 0 ? [] : receipts.splice(profileAt + 1)
    if (stoppedAt === null) {
      assert.ok(afterProfile.length >= 1, `concurrency receipt missing: ${[...receipts, ...afterProfile].map(r => r.operation).join(',')}`)
      assert.equal(afterProfile.at(-1).operation, 'concurrency')
      assert.ok(afterProfile.slice(0, -1).every(receipt => receipt.operation === 'upload'), afterProfile.map(r => r.operation).join(','))
      assert.equal(afterProfile.at(-1).budget_s, config.profileBudget ?? 1200, 'probe must use the resolved profile budget')
    } else assert.deepEqual(afterProfile.map(receipt => receipt.operation), [], 'box commands after failed profile')
    const count = operation => receipts.filter(receipt => receipt.operation === operation).length
    const firstSetup = receipts.findIndex(receipt => receipt.operation === 'setup')
    assert.ok(firstSetup >= 1, 'no harness upload before setup')
    assert.ok(receipts.slice(0, firstSetup).every(receipt => receipt.operation === 'upload'))
    // A repair rewriting two scripts may upload them in one or more receipts; only uploads separate the attempts.
    const anchorAttempts = receipts.flatMap((receipt, i) => receipt.operation === 'anchors' ? [i] : [])
    const anchorsRepairUploads = anchorAttempts.length === 2 ? anchorAttempts[1] - anchorAttempts[0] - 1 : 0
    if (anchorAttempts.length === 2) {
      assert.ok(anchorsRepairUploads >= 1, 'no upload between the anchor run and its rerun')
      assert.ok(anchorsRepairUploads <= anchorsRepairScripts(config).length, 'more anchors-repair uploads than rewritten scripts')
      // SCHEMAS.md: "the step reruns once with its original budget".
      assert.equal(receipts[anchorAttempts[1]].budget_s, receipts[anchorAttempts[0]].budget_s, 'rerun changed the anchors budget')
    }
    for (const i of anchorAttempts) assert.equal(receipts[i].budget_s, config.anchorsBudget ?? 1200, 'anchors budget')
    assert.equal(count('upload'), firstSetup + (config.setupFailures ? 1 : 0) + anchorsRepairUploads + (stoppedAt === 'reproduce' ? 0 : 1))
    if (config.setupFailures) assert.equal(receipts[firstSetup + 1].operation, 'upload')
    assert.equal(count('setup'), config.setupFailures ? 2 : 1)
    assert.equal(count('anchors'), config.setupFailures >= 2 ? 0 : config.anchorsFailures ? 2 : 1)
    assert.equal(count('profile'), stoppedAt === 'reproduce' ? 0 : 1)
    for (const [operation, failedAttempts] of [['anchors', config.anchorsFailures], ['profile', 0]]) {
      const attempts = receipts.filter(receipt => receipt.operation === operation)
      if (attempts.length) assert.deepEqual(attempts.map(receipt => receipt.rc),
        failedAttempts >= 2 ? [7, 7] : failedAttempts ? [7, 0] : operation === 'profile' && config.profileFailures ? [2] : [0])
      for (let i = 1; i < attempts.length; i++) assert.equal(receipts[receipts.indexOf(attempts[i]) - 1].operation, 'upload')
    }
    assert.deepEqual(receipts.filter(receipt => receipt.operation === 'setup').map(receipt => receipt.rc),
      config.setupFailures >= 2 ? [7, 7] : config.setupFailures ? [7, 0] : [0])
  })
  check(`${name}: private harness output fetched; operator has no sentinel`, () => {
    if (config.probeFailure) { noLeak(path.join(root, 'operator')); return }
    const results = path.join(root, 'agent', 'results', 'reproduce')
    assert.ok(fs.readdirSync(results).filter(file => file.endsWith('.log')).some(file => fs.readFileSync(path.join(results, file), 'utf8').includes(SENTINEL)), 'sentinel absent from fetched logs')
    noLeak(path.join(root, 'operator'))
  })
  check(`${name}: per-stage elapsed time and reported usage`, () => {
    for (const row of stages) {
      assert.ok(Number.isFinite(row.signature.wall_s) && row.signature.wall_s >= 0, row.signature.stage)
      const labels = { intake: ['intake'], reproduce: ['harness', 'harness-repair', 'anchors-repair'], profile: [], seal: ['seal'] }[row.signature.stage]
      if (labels && row.signature.status !== 'SKIPPED') {
        const count = calls.filter(call => labels.includes(call.label)).length
        assert.equal(row.signature.tokens_in, count * 10, row.signature.stage)
        assert.equal(row.signature.tokens_out, count * 5, row.signature.stage)
        assert.equal(row.facts.tokens_known, count > 0, row.signature.stage)
        if (count && config.agentDelayMs) assert.ok(row.signature.wall_s >= count * config.agentDelayMs / 1000 - 0.1, row.signature.stage)
      }
      if (row.signature.status === 'SKIPPED' && config.agentDelayMs) assert.ok(row.signature.wall_s < config.agentDelayMs / 1000, 'skip reused earlier duration')
    }
  })
  if (!config.probeFailure) freezeChecks(name, root, config, stage, stoppedAt)
  if (!config.probeFailure && stoppedAt !== 'reproduce') concurrencyChecks(name, root, config, stage, stoppedAt)
  const run = { root, config, stage }
  if (!config.probeFailure && stoppedAt !== 'reproduce') repairUploadChecks(name, run)
  return run
}
// Relative path -> base64 contents for every regular file under a directory.
function contents(directory) {
  const result = {}
  const visit = (parent, prefix) => {
    for (const entry of fs.readdirSync(parent, { withFileTypes: true })) {
      const file = path.join(parent, entry.name)
      if (entry.isDirectory()) visit(file, prefix + entry.name + '/')
      else if (entry.isFile()) result[prefix + entry.name] = fs.readFileSync(file).toString('base64')
    }
  }
  visit(directory, '')
  return result
}
// SCHEMAS.md reproduce bullet: "When reproduce passes, the pipeline freezes those outputs on the box:
// through boxrun, as operation `reproduce-freeze` under the `setup` budget, it runs `test ! -e
// reproduce-out` and then `cp -a out reproduce-out` ... its fetch replaces `A/results/reproduce/out/` ...
// Later stages never write to `reproduce-out/` ... A failed `reproduce-freeze` (nonzero exit, failed fetch,
// or timeout) fails reproduce with `error_class: infra`, or `timeout` on a timeout, without repair."
function freezeChecks(name, root, config, stage, stoppedAt) {
  const local = path.join(root, 'agent', 'results', 'reproduce', 'out')
  const freezeReceipt = () => {
    const directory = path.join(root, 'control', 'receipts')
    const file = fs.readdirSync(directory).find(file => /^\d{4}-reproduce-freeze\.json$/.test(file))
    assert.ok(file, 'no reproduce-freeze receipt')
    return readJSON(path.join(directory, file))
  }
  if (stoppedAt !== 'reproduce') check(`${name}: remote reproduce-out equals the anchor run's out/ and the local reproduce out/`, () => {
    const frozenDirectory = path.join(remoteHarness(root), 'reproduce-out')
    assert.ok(fs.existsSync(frozenDirectory), 'remote reproduce-out missing')
    assert.ok(!fs.lstatSync(frozenDirectory).isSymbolicLink(), 'remote reproduce-out is a symlink')
    const frozen = contents(frozenDirectory)
    const snapshots = path.join(root, 'anchor-out')
    assert.ok(fs.existsSync(snapshots), 'fixture never saw the anchor run finish')
    assert.deepEqual(frozen, contents(path.join(snapshots, fs.readdirSync(snapshots).sort().at(-1))), 'reproduce-out differs from the anchor run out/')
    assert.ok(Object.hasOwn(frozen, 'anchors_measured.json'), 'anchor measurements missing from reproduce-out')
    assert.deepEqual(contents(local), frozen, 'local A/results/reproduce/out differs from remote reproduce-out')
    // Profiling writes to out/ only: its profile/ and concurrency/ outputs and its own run of the
    // shared command (appended to command-calls.log) never reach reproduce-out or the local copy.
    assert.ok(!Object.keys(frozen).some(file => /^(profile|concurrency)\//.test(file)), 'profiler outputs in reproduce-out')
    const profiled = path.join(root, 'agent', 'results', 'profile', 'out', 'command-calls.log')
    if (fs.existsSync(profiled)) assert.notEqual(frozen['command-calls.log'], fs.readFileSync(profiled).toString('base64'), 'reproduce-out holds the profiler run')
  })
  else if (!config.freezeFailure) check(`${name}: no freeze when reproduce fails before passing`, () => {
    assert.equal(fs.existsSync(path.join(remoteHarness(root), 'reproduce-out')), false)
  })
  if (config.freezeFailure) check(`${name}: failed freeze (${config.freezeFailure}) fails reproduce without repair`, () => {
    const timeout = config.freezeFailure === 'timeout'
    const signature = stage('reproduce').signature
    assert.equal(signature.status, 'FAIL')
    assert.equal(signature.error_class, timeout ? 'timeout' : 'infra')
    assert.equal(signature.exit_code, timeout ? 3 : 2)
    // Scoring had passed: the anchor counts and stock verification stand.
    const { timed_out, budget_s, overrun, ...facts } = stage('reproduce').facts
    assert.deepEqual(facts, { anchors_passed: 2, anchors_total: 2, stock_verified: true,
      tuned_control_valid: null, tokens_known: true, gpu_busy_known: false })
    if (timeout) assert.deepEqual({ timed_out, budget_s, overrun }, { timed_out: true, budget_s: config.setupBudget, overrun: true })
    else assert.deepEqual([timed_out, budget_s, overrun], [undefined, undefined, undefined], 'timeout fields without a timeout')
    const receipt = freezeReceipt()
    if (config.freezeFailure === 'stale') {
      assert.notEqual(receipt.rc, 0, '`test ! -e reproduce-out` must fail on an existing reproduce-out')
      // The existing directory is left as it was: the copy never runs.
      assert.deepEqual(contents(path.join(remoteHarness(root), 'reproduce-out')), { 'stale-marker': Buffer.from('stale\n').toString('base64') })
    }
    if (config.freezeFailure === 'fetch') assert.deepEqual([receipt.rc, receipt.fetched], [0, false])
    if (timeout) assert.equal(receipt.timed_out, true)
    assert.ok(!rows(path.join(root, 'calls.jsonl')).some(call => /repair/.test(call.label)), 'repair after a failed freeze')
  })
}
// SCHEMAS.md "Concurrency probe" and the profile packet `concurrency` bullet.
const VALID_PROBE_MODES = { valid: fixture.VALID_CONCURRENCY, 'valid-null': fixture.NULL_CONCURRENCY }
function concurrencyChecks(name, root, config, stage, stoppedAt) {
  const ran = stoppedAt === null
  const mode = config.concurrency ?? 'real'
  const receiptDir = path.join(root, 'control', 'receipts')
  const receipt = fs.readdirSync(receiptDir).filter(file => /^\d{4}-concurrency\.json$/.test(file))
  const packetFile = path.join(root, 'agent', 'profile-packet.json')
  const fetched = path.join(root, 'agent', 'results', 'profile', 'out', 'concurrency')
  check(`${name}: concurrency probe runs only after a passing profile gate`, () => {
    assert.equal(receipt.length, ran ? 1 : 0)
    if (fs.existsSync(packetFile)) assert.ok(Object.hasOwn(readJSON(packetFile), 'concurrency'), 'packet lacks concurrency key')
    if (!ran) {
      if (fs.existsSync(packetFile)) assert.equal(readJSON(packetFile).concurrency, null, 'stale/unrun probe reached packet')
      assert.equal(stage('profile').facts.headroom, null)
      assert.ok(Object.hasOwn(stage('profile').facts, 'headroom'), 'executed profile stage must emit headroom')
    }
  })
  if (!ran) return
  const id = receipt[0].slice(0, -5)
  const fetchFailures = config.concurrencyFetchFailures ?? 0
  // Five failed attempts exhaust the retries: nothing from this probe can be fetched.
  const lost = fetchFailures >= 5
  check(`${name}: probe log, fetched results, stage unaffected (${mode})`, () => {
    if (!lost) assert.ok(fs.statSync(path.join(root, 'agent', 'results', 'profile', `${id}.log`)).isFile(), 'probe log missing')
    assert.equal(stage('profile').signature.status, 'PASS')
    if (!lost) assert.ok(!fs.existsSync(path.join(fetched, 'stale-marker')), 'remote out/concurrency was not cleared first')
    const calls = rows(path.join(root, 'concurrency-calls.jsonl'))
    if (mode === 'real') {
      assert.equal(calls.length, 0)
    } else {
      assert.equal(calls.length, 1, 'probe must run exactly once (no retry)')
      const budget = String(config.profileBudget ?? 1200)
      assert.deepEqual(calls[0].argv, ['profiler/concurrency_probe.py', 'harness/run_command.sh', 'out/concurrency', budget])
      assert.equal(calls[0].isolated, true, 'probe must run with python3 -I')
      assert.equal(calls[0].harness, true, 'probe must run from the shared run directory')
      assert.ok(calls[0].stale === null || calls[0].stale.length === 0, `stale out/concurrency: ${calls[0].stale}`)
    }
  })
  check(`${name}: packet concurrency and headroom fact (${mode})`, () => {
    const packet = readJSON(packetFile)
    const facts = stage('profile').facts
    if (VALID_PROBE_MODES[mode] && !lost) {
      assert.deepEqual(packet.concurrency, VALID_PROBE_MODES[mode])
      assert.deepEqual(readJSON(path.join(fetched, 'concurrency.json')), VALID_PROBE_MODES[mode])
      assert.deepEqual(facts.headroom, VALID_PROBE_MODES[mode].factor)
    } else if (mode === 'real') {
      fixture.assertConcurrencyShape(packet.concurrency)
      assert.deepEqual(packet.concurrency, readJSON(path.join(fetched, 'concurrency.json')))
      // SCHEMAS.md "MPS use is verified, not assumed": mps is true only when every copy connected.
      if (config.clearMps) {
        assert.equal(packet.concurrency.mps, false, 'harness cleared CUDA_MPS_*, so MPS use cannot be verified')
        assert.equal(packet.concurrency.mps_failed, true)
      } else {
        assert.equal(packet.concurrency.mps, true, 'MPS control binary on PATH must be used')
        assert.equal(packet.concurrency.mps_failed, false)
      }
      assert.equal(facts.headroom, packet.concurrency.factor)
      const mps = fs.readFileSync(path.join(root, 'mps-calls.log'), 'utf8').split('\n').filter(Boolean)
      assert.equal(mps[0], 'args -d')
      assert.equal(mps.at(-1), 'stdin quit', 'daemon must be stopped with `echo quit | nvidia-cuda-mps-control`')
    } else {
      assert.equal(packet.concurrency, null, `probe ${mode} must give packet concurrency null`)
      assert.ok(Object.hasOwn(facts, 'headroom'))
      assert.equal(facts.headroom, null)
    }
    if (mode !== 'timeout') {
      const r = readJSON(path.join(receiptDir, receipt[0]))
      assert.equal(r.rc, mode === 'rc' ? 3 : 0)
    }
    // Whole-workload bounds consume exactly this factor.
    const bounds = readJSON(path.join(root, 'agent', 'bounds.json'))
    const factor = packet.concurrency?.factor ?? null
    if (factor !== null && factor >= 1) assert.equal(bounds.batching.k_derivation.factor, factor)
    assert.equal(bounds.batching.k, factor !== null && factor >= 1 ? Math.min(4, factor) : 1)
  })
  if (fetchFailures) check(`${name}: concurrency fetches retried, probe run once (run11 regression)`, () => {
    // SCHEMAS.md receipts: out/ then the log; each failing fetch is retried up to four more times,
    // only the fetch is repeated, and the retry waits count in wall_s.
    const attempts = kind => { const file = path.join(root, `concurrency-fetch-${kind}`); return fs.existsSync(file) ? Number(fs.readFileSync(file, 'utf8')) : 0 }
    const r = readJSON(path.join(receiptDir, receipt[0]))
    assert.equal(r.rc, 0, 'remote rc recorded')
    assert.equal(r.timed_out, false)
    assert.equal(r.fetched, !lost)
    assert.equal(attempts('out'), Math.min(fetchFailures + 1, 5), 'out/ fetch attempts')
    if (lost) assert.ok(attempts('log') <= 5, `log fetch attempts ${attempts('log')}`)
    else {
      assert.equal(attempts('log'), fetchFailures + 1, 'log fetch attempts')
      const waits = 2 * fetchFailures * 1
      assert.ok(r.wall_s >= waits, `retry waits (${waits} s at BOXRUN_FETCH_WAIT_S=1) missing from wall_s ${r.wall_s}`)
    }
    assert.equal(rows(path.join(root, 'concurrency-calls.jsonl')).length, 1, 'retry repeated the probe command')
  })
}
function reproduceFacts(name, run, passed, total, stock = true) {
  check(`${name}: reproduce facts and validity`, () => {
    const row = run.stage('reproduce')
    assert.deepEqual(row.facts, { anchors_passed: passed, anchors_total: total, stock_verified: stock,
      tuned_control_valid: null, tokens_known: true, gpu_busy_known: false })
    assert.equal(row.signature.gpu_s, 0)
    // run_valid: true/false with at least one anchor; null when there are no anchors.
    if (total === 0) assert.equal(row.signature.run_valid ?? null, null, 'run_valid must be null without anchors')
    else if (total !== null) assert.equal(row.signature.run_valid, passed === total)
  })
  check(`${name}: intake anchored fact`, () => {
    const facts = run.stage('intake').facts
    assert.ok(Object.hasOwn(facts, 'anchored'), 'executed intake stage must emit anchored')
    assert.equal(facts.anchored, run.config.anchors.some(item => !isReference(item)))
  })
}
// The single remote /tmp/m5-<uuid> directory, mapped into the case's fake box.
function remoteHarness(root) {
  const box = path.join(root, 'box')
  const directories = fs.readdirSync(box).filter(entry => entry.startsWith('m5-') && fs.existsSync(path.join(box, entry, 'harness')))
  assert.equal(directories.length, 1, `expected one remote run directory: ${directories}`)
  return path.join(box, directories[0])
}
const bytesOf = file => fs.existsSync(file) ? fs.readFileSync(file) : null
// SCHEMAS.md "A/harness/": "The setup repair may rewrite only `setup.sh`. The anchors step executes
// `run_anchors.sh` and the `run_command.sh` it invokes, so the anchors repair may rewrite either or both
// and nothing else ... Every rewritten script is recopied, then the step reruns once with its original budget."
function repairUploadChecks(name, run) {
  const { root, config } = run
  const local = path.join(root, 'agent', 'harness')
  if (config.anchorsFailures) check(`${name}: rewritten ${anchorsRepairScripts(config).join(' and ')} uploaded before the rerun`, () => {
    const remote = remoteHarness(root)
    const before = path.join(root, 'pre-anchors-repair')
    for (const file of anchorsRepairScripts(config)) {
      const rewritten = bytesOf(path.join(local, file))
      assert.ok(rewritten && rewritten.includes('# rewritten by anchors-repair'), `${file}: fake repair did not rewrite the local copy`)
      assert.deepEqual(bytesOf(path.join(remote, 'harness', file)), rewritten, `${file}: rewritten bytes not on the box`)
    }
    for (const file of ['run_anchors.sh', 'run_command.sh'].filter(file => !anchorsRepairScripts(config).includes(file)))
      assert.deepEqual(bytesOf(path.join(remote, 'harness', file)), bytesOf(path.join(before, file)), `${file}: unchanged script differs on the box`)
    // The rerun's measurements are the scored ones: the first attempt failed before writing any.
    const results = path.join(root, 'agent', 'results', 'reproduce')
    const score = readJSON(path.join(results, 'anchors_scored.json'))
    assert.deepEqual(score.anchors.map(row => row.measured_value), config.anchors.map(item => config.measured[item.id] ?? null))
    if (anchorsRepairScripts(config).includes('run_command.sh'))
      assert.ok(fs.existsSync(path.join(results, 'out', 'rewritten-command.txt')), 'fetched anchor outputs did not come from the rewritten run_command.sh')
  })
  if (config.anchorsRepairStray) check(`${name}: anchors repair never uploads or runs setup.sh or run_evaluation.sh`, () => {
    const remote = remoteHarness(root)
    const before = path.join(root, 'pre-anchors-repair')
    const after = path.join(root, 'post-anchors-repair')
    for (const file of ['setup.sh', 'run_evaluation.sh'])
      assert.ok(bytesOf(path.join(after, file))?.includes('stray'), `fixture did not edit ${file} during the anchors repair`)
    assert.deepEqual(bytesOf(path.join(remote, 'harness', 'setup.sh')), bytesOf(path.join(before, 'setup.sh')), 'setup.sh changed on the box')
    assert.deepEqual(bytesOf(path.join(remote, 'harness', 'run_evaluation.sh')), bytesOf(path.join(before, 'run_evaluation.sh')), 'run_evaluation.sh changed on the box')
    for (const file of ['stray-setup', 'stray-evaluation']) assert.ok(!fs.existsSync(path.join(remote, 'out', file)), `${file}: stray script ran`)
  })
  if (config.setupRepairStray) check(`${name}: setup repair uploads only setup.sh`, () => {
    const remote = remoteHarness(root)
    const before = path.join(root, 'pre-harness-repair')
    assert.deepEqual(bytesOf(path.join(remote, 'harness', 'setup.sh')), bytesOf(path.join(local, 'setup.sh')), 'repaired setup.sh not on the box')
    for (const file of ['run_anchors.sh', 'run_command.sh']) {
      assert.ok(bytesOf(path.join(root, 'post-harness-repair', file))?.includes('stray'), `fixture did not edit ${file} during the setup repair`)
      assert.deepEqual(bytesOf(path.join(remote, 'harness', file)), bytesOf(path.join(before, file)), `${file} changed on the box`)
    }
    for (const file of ['stray-anchors', 'stray-command']) assert.ok(!fs.existsSync(path.join(remote, 'out', file)), `${file}: stray script ran`)
  })
}
// SCHEMAS.md: "a rewritten `run_command.sh` still obeys every `run_command.sh` rule above, and the anchors
// repair prompt states this." Checked by meaning, not wording: the prompt names run_command.sh and states
// the measured-command/complete-environment rule, the relative-path rule and the CUDA MPS rule.
function assertRunCommandRules(prompt, label) {
  assert.match(prompt, /run_command\.sh/, `${label}: prompt never names run_command.sh`)
  assert.match(prompt, /run_command\.sh[^\n]*\b(rewrite|rewritten|edit|modif|change|fix)|\b(rewrite|rewritten|edit|modif|change|fix)\w*[^\n]*run_command\.sh/i,
    `${label}: prompt does not allow rewriting run_command.sh`)
  assert.match(prompt, /\b(only|exact)\b[^.\n]*\bmeasured\b[^.\n]*\bcommand\b|\bmeasured\b[^.\n]*\bcommand\b[^.\n]*\bonly\b/i,
    `${label}: prompt lacks the only-the-measured-command rule`)
  assert.match(prompt, /complete environment|environment[^.\n]*complete/i, `${label}: prompt lacks the complete-environment rule`)
  assert.match(prompt, /relative[^.\n]*path|path[^.\n]*relative/i, `${label}: prompt lacks the relative-path rule`)
  assert.match(prompt, /absolute path/i, `${label}: prompt does not forbid absolute paths`)
  assertMpsRule(prompt, label)
}
function scoredFile(name, run, expectedRows) {
  check(`${name}: anchors_scored.json rows, kinds and counts`, () => {
    const score = readJSON(path.join(run.root, 'agent', 'results', 'reproduce', 'anchors_scored.json'))
    const rows = expectedRows ?? run.config.anchors.map(item => expectedRow(item, run.config.measured))
    const anchorRows = rows.filter(row => row.kind === 'anchor')
    assert.deepEqual(score, { anchors: rows, anchors_passed: anchorRows.filter(row => row.passed).length,
      anchors_total: anchorRows.length, all_passed: anchorRows.every(row => row.passed), references_total: rows.length - anchorRows.length })
  })
}
function profileFacts(name, run, fraction) {
  check(`${name}: profile packet and facts derived from files`, () => {
    const input = path.join(run.root, 'agent', 'results', 'profile', 'out', 'profile')
    const timings = readJSON(path.join(input, 'stages.json'))
    const total = readJSON(path.join(input, 'total_wall_s.json')).total_wall_s
    const packet = readJSON(path.join(run.root, 'agent', 'profile-packet.json'))
    assert.deepEqual(Object.keys(packet).sort(), ['concurrency', 'gpu_count', 'gpu_telemetry', 'stages', 'timed_fraction', 'total_wall_s'])
    const telemetry = readJSON(path.join(input, 'gpu_util.json'))
    assert.deepEqual(packet.stages, timings.map(({ stage, wall_s, gpu_s, kind, start_s = null }) => {
      const samples = start_s === null ? [] : telemetry.filter(({ t }) => t >= start_s && t < start_s + wall_s)
      return { stage, wall_s, gpu_s, ...(kind === undefined ? {} : { kind }),
        wall_fraction: Math.min(1, wall_s / total), start_s,
        mean_gpu_util: samples.length ? samples.reduce((sum, row) => sum + row.util, 0) / samples.length / 100 : null }
    }))
    assert.equal(packet.total_wall_s, total)
    assert.equal(packet.timed_fraction, Math.min(1, timings.reduce((sum, row) => sum + row.wall_s, 0) / total))
    assert.equal(packet.timed_fraction, fraction)
    const boxFile = path.join(run.root, 'control', 'box.json')
    const box = fs.existsSync(boxFile) ? readJSON(boxFile) : {}
    const allocationCount = /^gpu_(\d+)x_/.exec(box.type || '')
    const probe = readJSON(path.join(run.root, 'agent', 'results', 'probe', 'probe.json'))
    const expectedGpuCount = Number.isInteger(box.gpu_count) && box.gpu_count >= 0 ? box.gpu_count
      : allocationCount ? Number(allocationCount[1]) : probe.nvidia?.gpus?.length ?? 1
    assert.equal(packet.gpu_count, expectedGpuCount)
    assert.equal(packet.gpu_telemetry, readJSON(path.join(input, 'gpu_util.json')).length > 0)
    // Every executed profile stage emits headroom = packet concurrency.factor or null.
    // A probe box timeout may add the optional typed timeout fields (SCHEMAS.md receipts section).
    const { timed_out, budget_s, overrun, ...facts } = run.stage('profile').facts
    if (run.config.concurrency === 'timeout' && timed_out !== undefined) {
      assert.deepEqual({ timed_out, budget_s, overrun }, { timed_out: true, budget_s: run.config.profileBudget, overrun: true })
    } else assert.deepEqual([timed_out, budget_s, overrun], [undefined, undefined, undefined], 'timeout fields without a timeout')
    assert.deepEqual(facts, { profile_complete: true, timed_fraction: fraction,
      gpu_telemetry: packet.gpu_telemetry, tokens_known: false, gpu_busy_known: false,
      headroom: packet.concurrency === null ? null : packet.concurrency.factor })
    assert.equal(run.stage('profile').signature.gpu_s, 0)
    assert.ok(fs.readFileSync(path.join(input, 'raw-telemetry.txt'), 'utf8').includes(SENTINEL))
  })
}

async function probeScriptTests() {
  const bin = path.join(scratch, 'probe-path')
  fs.mkdirSync(bin)
  // Keep required utilities, excluding optional nvcc and cmake deliberately.
  for (const command of ['mkdir', 'mktemp', 'rm', 'uname', 'nproc', 'awk', 'df', 'head', 'python3']) {
    const found = spawnSync('/bin/bash', ['-c', 'command -v "$1"', 'probe-test', command], { encoding: 'utf8' })
    assert.equal(found.status, 0, `required utility missing: ${command}`)
    fs.symlinkSync(found.stdout.trim(), path.join(bin, command))
  }
  for (const restricted of [false, true]) {
    const directory = path.join(scratch, restricted ? 'probe-restricted' : 'probe-normal')
    fs.mkdirSync(directory)
    const result = await new Promise(resolve => {
      const proc = spawn('/bin/bash', [path.join(ROOT, 'm5', 'box_probe.sh')], {
        cwd: directory, env: { ...process.env, ...(restricted ? { PATH: bin } : {}) }, timeout: 60000,
      })
      let stderr = '', error
      proc.stderr.on('data', data => { stderr += data })
      proc.stdout.resume()
      proc.on('error', value => { error = value })
      proc.on('close', status => resolve({ status, stderr, error }))
    })
    check(`probe script: ${restricted ? 'without nvcc/cmake in PATH' : 'normal PATH'}`, () => {
      assert.ifError(result.error)
      assert.equal(result.status, 0, result.stderr)
      const probe = readJSON(path.join(directory, 'out', 'probe.json'))
      assert.deepEqual(Object.keys(probe).sort(), ['os', 'kernel', 'nproc', 'memory_kb', 'disk_home_avail_bytes',
        'nvidia', 'nvcc', 'cmake', 'gcc', 'g++', 'make', 'git', 'python3', 'pip', 'apt_sources', 'sudo_nopasswd'].sort())
      const nullableString = value => assert.ok(value === null || typeof value === 'string')
      nullableString(probe.kernel)
      for (const key of ['nproc', 'memory_kb', 'disk_home_avail_bytes']) assert.ok(probe[key] === null || Number.isInteger(probe[key]), key)
      if (probe.os !== null) {
        assert.deepEqual(Object.keys(probe.os).sort(), ['id', 'version_id', 'pretty_name', 'version', 'name'].sort())
        Object.values(probe.os).forEach(nullableString)
      }
      if (probe.nvidia !== null) {
        assert.deepEqual(Object.keys(probe.nvidia).sort(), ['gpus', 'driver_version', 'cuda_version'].sort())
        assert.ok(Array.isArray(probe.nvidia.gpus))
        for (const gpu of probe.nvidia.gpus) assert.equal(typeof gpu, 'string')
        nullableString(probe.nvidia.driver_version)
        nullableString(probe.nvidia.cuda_version)
      }
      const tool = value => {
        assert.deepEqual(Object.keys(value).sort(), ['path', 'version'])
        assert.equal(typeof value.path, 'string')
        nullableString(value.version)
      }
      for (const key of ['cmake', 'gcc', 'g++', 'make', 'git', 'python3', 'pip']) if (probe[key] !== null) tool(probe[key])
      assert.ok(Array.isArray(probe.nvcc))
      probe.nvcc.forEach(tool)
      assert.equal(new Set(probe.nvcc.map(value => value.path)).size, probe.nvcc.length)
      assert.ok(Array.isArray(probe.apt_sources))
      for (const source of probe.apt_sources) {
        assert.deepEqual(Object.keys(source).sort(), ['file', 'lines'])
        assert.equal(typeof source.file, 'string')
        assert.ok(Array.isArray(source.lines))
        for (const line of source.lines) assert.equal(typeof line, 'string')
      }
      assert.equal(typeof probe.sudo_nopasswd, 'boolean')
      if (restricted) {
        assert.equal(probe.cmake, null)
        // SCHEMAS.md permits discovering nvcc outside PATH in these two locations.
        const externalNvcc = ['/usr/local', '/usr/lib'].flatMap(parent => fs.readdirSync(parent)
          .filter(name => name.startsWith('cuda')).map(name => path.join(parent, name, 'bin', 'nvcc')))
          .filter(file => { try { fs.accessSync(file, fs.constants.X_OK); return true } catch { return false } })
        assert.deepEqual(probe.nvcc.map(value => value.path).sort(), externalNvcc.sort())
      }
    })
  }
}

// Expected score row, derived from SCHEMAS.md "deterministic anchor scoring" only.
const THRESHOLDS = { '>': (a, b) => a > b, '>=': (a, b) => a >= b, '<': (a, b) => a < b, '<=': (a, b) => a <= b }
function expectedRow(entry, measured) {
  const value = measured[entry.id]
  const unmeasured = !Object.hasOwn(measured, entry.id) ? 'missing'
    : typeof value !== 'number' || !Number.isFinite(value) ? 'non_numeric' : null
  const row = { id: entry.id, kind: isReference(entry) ? 'reference' : 'anchor', published_value: entry.published_value,
    measured_value: unmeasured ? null : value, tolerance: entry.tolerance,
    ...(Object.hasOwn(entry, 'uncertainty') ? { uncertainty: entry.uncertainty } : {}) }
  if (row.kind === 'reference') {
    return { ...row, passed: null, difference: unmeasured ? null : value - entry.published_value, ...(unmeasured ? { reason: unmeasured } : {}) }
  }
  const comparison = entry.comparison ?? '=='
  if (comparison !== '==' && !THRESHOLDS[comparison]) return { ...row, passed: false, reason: 'unknown_comparison' }
  if (unmeasured) return { ...row, passed: false, reason: unmeasured }
  if (comparison !== '==') {
    const passed = THRESHOLDS[comparison](value, entry.published_value)
    return { ...row, passed, ...(passed ? {} : { reason: 'threshold_not_met' }) }
  }
  const tolerance = typeof entry.tolerance === 'number' ? entry.tolerance
    : entry.tolerance.abs ?? entry.tolerance.rel * Math.abs(entry.published_value)
  const passed = Math.abs(value - entry.published_value) <= tolerance
  return { ...row, passed, ...(passed ? {} : { reason: 'out_of_tolerance' }) }
}

async function cliTests() {
  const directory = path.join(scratch, 'cli')
  fs.mkdirSync(directory)
  let sequence = 0
  async function score(label, anchors, measured, expectedExit, validate, options = {}) {
    checks++
    try {
      const prefix = path.join(directory, String(++sequence))
      const input = prefix + '-anchors.json', measurements = prefix + '-measured.json', output = prefix + '-score.json'
      if (!options.missingInput) {
        if (options.rawAnchors) fs.writeFileSync(input, options.rawAnchors)
        else writeJSON(input, anchors)
      }
      if (options.rawMeasured) fs.writeFileSync(measurements, options.rawMeasured)
      else writeJSON(measurements, measured)
      if (options.oldOutput) fs.writeFileSync(output, 'previous score\n')
      if (options.outputDirectory) fs.mkdirSync(output)
      const result = await new Promise(resolve => {
        const proc = spawn('python3', [path.join(ROOT, 'm5', 'score_anchors.py'), input, measurements, output], { timeout: 10000 })
        let stdout = '', stderr = '', error
        proc.stdout.on('data', data => { stdout += data })
        proc.stderr.on('data', data => { stderr += data })
        proc.on('error', value => { error = value })
        proc.on('close', status => resolve({ status, stdout, stderr, error }))
      })
      assert.ifError(result.error)
      assert.equal(result.status, expectedExit, `stdout=${result.stdout}; stderr=${result.stderr}`)
      assert.ok(!(result.stdout + result.stderr).includes(SENTINEL), 'input content in diagnostic')
      if (expectedExit === 1) {
        if (options.oldOutput) assert.equal(fs.readFileSync(output, 'utf8'), 'previous score\n')
        else if (!options.outputDirectory) assert.equal(fs.existsSync(output), false, 'invalid input created score')
      } else {
        const scored = readJSON(output)
        const expected = options.expectedAnchors ?? anchors.map(entry => expectedRow(entry, measured))
        const anchorRows = expected.filter(row => row.kind === 'anchor')
        assert.deepEqual(scored, { anchors: expected, anchors_passed: anchorRows.filter(row => row.passed).length,
          anchors_total: anchorRows.length, all_passed: anchorRows.every(row => row.passed),
          references_total: expected.length - anchorRows.length })
        assert.equal(result.status, anchorRows.every(row => row.passed) ? 0 : 4, 'exit code disagrees with anchor rows')
        if (validate) validate(scored)
      }
      console.log(`ok CLI ${label}`)
    } catch (error) { failures++; console.log(`FAIL CLI ${label}: ${error.message}`) }
  }
  await score('ordered anchors, exact keys, absolute forms, extra measurement ignored', ANCHORS, { second: 0, first: 101, extra: 123 }, 0)
  await score('mismatch writes complete score', ANCHORS, { first: 101.000001, second: 0 }, 4)
  const relative = [anchor('negative', -100, { rel: 0.01 }), anchor('zero', 0, { rel: 0.01 })]
  await score('relative equality boundary and zero reference pass', relative, { negative: -101, zero: 0 }, 0)
  await score('relative just outside boundary fails', relative, { negative: -101.000001, zero: 0 }, 4)
  await score('zero relative reference requires exact equality', relative, { negative: -100, zero: 1e-12 }, 4)
  const secret = anchor(SENTINEL, 1, 0)
  for (const [label, comparison, published, tolerance, measured, passed, reason] of [
    ['strict greater passes above threshold ignoring tolerance', '>', 100, 0, 101, true],
    ['strict greater fails at equality despite tolerance', '>', 100, 10, 100, false, 'threshold_not_met'],
    ['greater or equal passes at equality', '>=', 100, 0, 100, true],
    ['explicit equality passes at tolerance boundary', '==', 100, { abs: 1 }, 101, true],
    ['explicit equality fails outside tolerance', '==', 100, { abs: 1 }, 101.000001, false, 'out_of_tolerance'],
    ['unknown comparison fails', '!=', 100, 0, 100, false, 'unknown_comparison'],
    ['non-numeric measured value fails', '>', 100, 0, '101', false, 'non_numeric'],
  ]) {
    await score(label, [{ ...anchor(SENTINEL, published, tolerance), comparison }], { [SENTINEL]: measured }, passed ? 0 : 4, null, {
      expectedAnchors: [{ id: SENTINEL, kind: 'anchor', published_value: published, measured_value: reason === 'non_numeric' ? null : measured,
        tolerance, passed, ...(reason ? { reason } : {}) }],
    })
  }
  for (const [label, measured, reason, options] of [
    ['missing measurement', {}, 'missing'],
    ['boolean measured', { [SENTINEL]: true }, 'non_numeric'],
    ['string measured', { [SENTINEL]: '1' }, 'non_numeric'],
    ['null measured', { [SENTINEL]: null }, 'non_numeric'],
    ['nonfinite measured', {}, 'non_numeric', { rawMeasured: `{"${SENTINEL}":NaN}` }],
  ]) await score(label, [secret], measured, 4, null, {
    expectedAnchors: [{ id: SENTINEL, kind: 'anchor', published_value: 1, measured_value: null, tolerance: 0, passed: false, reason }],
    ...options,
  })
  // References: measured and reported, never passed or failed (passed null, difference).
  const refs = [reference('ref-default', 10), reference('ref-explicit', -2.5, { comparison: '==' }),
    reference('ref-zero', 0, { uncertainty: { kind: 'interval_halfwidth', value: 0 } })]
  await score('references report difference with passed null; counts exclude references', refs,
    { 'ref-default': 13, 'ref-explicit': 1e6, 'ref-zero': -0.25 }, 0)
  for (const [label, measured, reason, options] of [
    ['unmeasured reference missing', {}, 'missing'],
    ['unmeasured reference boolean', { [SENTINEL]: true }, 'non_numeric'],
    ['unmeasured reference string', { [SENTINEL]: '1' }, 'non_numeric'],
    ['unmeasured reference nonfinite', {}, 'non_numeric', { rawMeasured: `{"${SENTINEL}":Infinity}` }],
  ]) await score(`${label} has reason but never fails`, [reference(SENTINEL, 1)], measured, 0, null, {
    expectedAnchors: [{ id: SENTINEL, kind: 'reference', published_value: 1, measured_value: null, tolerance: null,
      passed: null, difference: null, reason }],
    ...options,
  })
  await score('uncertainty preserved unchanged on anchor and reference rows', [
    anchor('se', 5, { abs: 1 }, { uncertainty: { kind: 'standard_error', value: 0.5 } }),
    anchor('sd', 5, 0.5, { uncertainty: { kind: 'standard_deviation', value: 2 } }),
    anchor('none', 5, 1, { uncertainty: null }),
    reference('ref', 5, { uncertainty: { kind: 'interval_halfwidth', value: 3 } })],
  { se: 5.9, sd: 7, none: 5, ref: 100 }, 4, scored => {
    // Uncertainty never affects scoring: sd fails despite a published spread of 2.
    assert.deepEqual(scored.anchors.map(row => row.passed), [true, false, true, null])
  })
  await score('empty array is valid', [], {}, 0, scored => {
    assert.deepEqual(scored, { anchors: [], anchors_passed: 0, anchors_total: 0, all_passed: true, references_total: 0 })
  })
  await score('reference-only: all_passed true with no anchors', [reference('a', 1), reference('b', 2)], { a: 99 }, 0, scored => {
    assert.equal(scored.all_passed, true)
    assert.equal(scored.anchors_total, 0)
    assert.equal(scored.references_total, 2)
  })
  await score('mixed anchors and references, one failing anchor exits 4', [
    anchor('ok', 1, 0), reference('ref', 1), anchor('bad', 1, { abs: 0.1 }), reference('ref2', 7)],
  { ok: 1, ref: 500, bad: 2, ref2: 7 }, 4, scored => {
    assert.equal(scored.anchors_passed, 1)
    assert.equal(scored.anchors_total, 2)
    assert.equal(scored.references_total, 2)
    assert.equal(scored.all_passed, false)
  })
  await score('mixed anchors and references, every anchor passes despite far references', [
    reference('ref', 1), anchor('ok', 1, { rel: 0 })], { ref: -1e9, ok: 1 }, 0)
  for (const comparison of ['>', '>=', '<', '<=']) {
    await score(`inequality ${comparison} with null tolerance is an anchor (passing)`,
      [anchor('threshold', 10, null, { comparison })], { threshold: comparison.startsWith('>') ? 11 : 9 }, 0)
    await score(`inequality ${comparison} with null tolerance is an anchor (failing)`,
      [anchor('threshold', 10, null, { comparison })], { threshold: comparison.startsWith('>') ? 9 : 11 }, 4)
  }
  await score('inequality with null tolerance and missing measurement fails as anchor',
    [anchor('threshold', 10, null, { comparison: '>=' })], {}, 4)
  for (const [label, anchors, measured, options] of [
    ['duplicate IDs', [secret, secret], { [SENTINEL]: 1 }],
    ['duplicate reference IDs', [reference(SENTINEL, 1), reference(SENTINEL, 2)], { [SENTINEL]: 1 }],
    ['non-array anchors', { [SENTINEL]: 1 }, { [SENTINEL]: 1 }],
    ['reference with boolean published value', [reference(SENTINEL, false)], { [SENTINEL]: 1 }],
    ['reference with string published value', [reference(SENTINEL, '1')], { [SENTINEL]: 1 }],
    ...[
      ['unknown uncertainty kind', { kind: 'variance', value: 1 }],
      ['negative uncertainty', { kind: 'standard_error', value: -0.1 }],
      ['boolean uncertainty value', { kind: 'standard_deviation', value: true }],
      ['string uncertainty value', { kind: 'standard_deviation', value: '1' }],
      ['null uncertainty value', { kind: 'standard_error', value: null }],
      ['uncertainty missing value', { kind: 'standard_error' }],
      ['uncertainty missing kind', { value: 1 }],
      ['uncertainty extra key', { kind: 'standard_error', value: 1, note: SENTINEL }],
      ['numeric uncertainty', 1], ['string uncertainty', SENTINEL], ['array uncertainty', [1]],
      ['boolean uncertainty', false],
    ].flatMap(([label, uncertainty]) => [
      [`${label} on anchor`, [{ ...secret, uncertainty }], { [SENTINEL]: 1 }],
      [`${label} on reference`, [reference(SENTINEL, 1, { uncertainty })], { [SENTINEL]: 1 }],
    ]),
    ['nonfinite uncertainty', [], {}, { rawAnchors: `[{"id":"${SENTINEL}","quantity":"q","source":"s","published_value":1,"tolerance":0,"uncertainty":{"kind":"standard_error","value":Infinity}}]` }],
    ['NaN uncertainty on reference', [], {}, { rawAnchors: `[{"id":"${SENTINEL}","quantity":"q","source":"s","published_value":1,"tolerance":null,"uncertainty":{"kind":"standard_error","value":NaN}}]` }],
    ['null absolute tolerance', [{ ...secret, tolerance: { abs: null } }], { [SENTINEL]: 1 }],
    ['string relative tolerance', [{ ...secret, tolerance: { rel: '0.1' } }], { [SENTINEL]: 1 }],
    ['empty tolerance object', [{ ...secret, tolerance: {} }], { [SENTINEL]: 1 }],
    ['string tolerance', [{ ...secret, tolerance: '1' }], { [SENTINEL]: 1 }],
    ['array tolerance', [{ ...secret, tolerance: [1] }], { [SENTINEL]: 1 }],
    ['nonfinite absolute tolerance', [], {}, { rawAnchors: `[{"id":"${SENTINEL}","quantity":"q","source":"s","published_value":1,"tolerance":{"abs":Infinity}}]` }],
    ['invalid tolerance alongside valid reference', [reference('ref', 1), { ...secret, tolerance: { rel: -1 } }], { ref: 1, [SENTINEL]: 1 }],
    ['boolean reference', [{ ...secret, published_value: true }], { [SENTINEL]: 1 }],
    ['negative tolerance', [{ ...secret, tolerance: -1 }], { [SENTINEL]: 1 }],
    ['boolean tolerance', [{ ...secret, tolerance: false }], { [SENTINEL]: 1 }],
    ['negative relative tolerance', [{ ...secret, tolerance: { rel: -1 } }], { [SENTINEL]: 1 }],
    ['ambiguous tolerance', [{ ...secret, tolerance: { abs: 1, rel: 1 } }], { [SENTINEL]: 1 }],
    ['unknown tolerance', [{ ...secret, tolerance: { other: 1 } }], { [SENTINEL]: 1 }],
    ['overflow difference', [anchor(SENTINEL, 1e308, 0)], { [SENTINEL]: -1e308 }],
    ['overflow relative tolerance', [anchor(SENTINEL, 1e308, { rel: 1e308 })], { [SENTINEL]: 1e308 }],
    ['nonfinite reference', [], { [SENTINEL]: 1 }, { rawAnchors: `[{"id":"${SENTINEL}","published_value":Infinity,"tolerance":0}]` }],
    ['malformed JSON', [], {}, { rawAnchors: SENTINEL }], ['missing input', [], {}, { missingInput: true }],
  ]) await score(label, anchors, measured, 1, null, { oldOutput: true, ...options })
  await score('invalid uncertainty creates no output', [reference(SENTINEL, 1, { uncertainty: { kind: 'standard_error', value: -1 } })], { [SENTINEL]: 1 }, 1)
  await score('invalid tolerance creates no output', [{ ...secret, tolerance: { abs: 1, rel: 0 } }], { [SENTINEL]: 1 }, 1)
  await score('output write failure', ANCHORS, { first: 100, second: 0 }, 1, null, { outputDirectory: true })
  await recordedScoreRegression(directory)
}
// Public recorded run16: rescoring its recorded anchors.json against its recorded
// measurements must reproduce the recorded per-anchor outcome and counts, with the new fields.
const EXPERIMENTS = path.resolve(ROOT, '..', '..', 'experiments')
async function recordedScoreRegression(directory) {
  const label = 'recorded shakedown-m5/run16 rescoring'
  checks++
  try {
    const run = path.join(EXPERIMENTS, 'shakedown-m5', 'run16')
    const pick = relative => ['agent', 'A'].map(base => path.join(run, base, relative)).find(file => fs.existsSync(file))
    const sources = { anchors: pick('intake/anchors.json'), measured: pick('results/reproduce/out/anchors_measured.json'),
      scored: pick('results/reproduce/anchors_scored.json') }
    for (const [key, file] of Object.entries(sources)) assert.ok(file, `recorded ${key} file missing under ${run}`)
    // Copy fixtures first; nothing is written into experiments/.
    const fixtures = path.join(directory, 'run16')
    fs.mkdirSync(fixtures)
    for (const [key, file] of Object.entries(sources)) fs.copyFileSync(file, path.join(fixtures, `${key}.json`))
    const items = readJSON(path.join(fixtures, 'anchors.json'))
    const measured = readJSON(path.join(fixtures, 'measured.json'))
    const recorded = readJSON(path.join(fixtures, 'scored.json'))
    const output = path.join(fixtures, 'rescored.json')
    const result = spawnSync('python3', [path.join(ROOT, 'm5', 'score_anchors.py'), path.join(fixtures, 'anchors.json'),
      path.join(fixtures, 'measured.json'), output], { encoding: 'utf8', timeout: 10000 })
    assert.ifError(result.error)
    assert.equal(result.status, recorded.all_passed ? 0 : 4, result.stderr)
    const scored = readJSON(output)
    assert.deepEqual(Object.keys(scored).sort(), ['all_passed', 'anchors', 'anchors_passed', 'anchors_total', 'references_total'])
    const references = items.filter(isReference).length
    assert.equal(scored.references_total, references)
    for (const key of ['anchors_passed', 'anchors_total', 'all_passed']) assert.deepEqual(scored[key], recorded[key], key)
    assert.equal(scored.anchors.length, recorded.anchors.length)
    scored.anchors.forEach((row, i) => {
      const item = items[i]
      assert.deepEqual(row, { ...recorded.anchors[i], kind: isReference(item) ? 'reference' : 'anchor',
        ...(Object.hasOwn(item, 'uncertainty') ? { uncertainty: item.uncertainty } : {}) }, `row ${row.id}`)
    })
    console.log(`ok CLI ${label}`)
  } catch (error) { failures++; console.log(`FAIL CLI ${label}: ${error.message}`) }
}
function boundsCliTests() {
  const directory = path.join(scratch, 'bounds-cli')
  fs.mkdirSync(directory)
  const methods = ['data-parallel over inputs', 'batching', 'multi-GPU', 'ensembles', 'pipelining']
  // SCHEMAS.md "A/bounds.json": whole-workload k = min(cap, concurrency factor), p = 1;
  // pipelining is Amdahl over transfer time with k = 2; multi-GPU is Amdahl / k.
  const WHOLE = { 'data-parallel over inputs': 8, batching: 4, ensembles: 8 }
  const TRANSFER_TOKENS = new Set(['transfer', 'transfers', 'h2d', 'd2h', 'htod', 'dtoh', 'copy', 'memcpy', 'upload', 'download'])
  const COMPUTE_TOKENS = new Set(['compute', 'kernel', 'kernels', 'inference', 'training', 'forward', 'backward'])
  const kindOf = row => {
    if (row.kind !== undefined) return row.kind
    const tokens = row.stage.toLowerCase().split(/[^a-z0-9]+/).filter(Boolean)
    return tokens.some(t => TRANSFER_TOKENS.has(t)) ? 'transfer' : tokens.some(t => COMPUTE_TOKENS.has(t)) ? 'compute' : 'other'
  }
  const actsOn = (method, kind) => method in WHOLE || (method === 'pipelining' ? kind === 'transfer' : kind === 'compute')
  const amdahl = (p, k) => 1 / ((1 - p) + p / k)
  const near = (actual, expected, label) => assert.ok(typeof actual === 'number' && Math.abs(actual - expected) < 1e-12, `${label}: ${actual} != ${expected}`)
  const OMIT = Symbol('omit')
  const calibration = (factor, mps = false) => ({ ...fixture.VALID_CONCURRENCY, mps, factor })
  let sequence = 0
  function runBounds(packet, raw) {
    const input = path.join(directory, `${++sequence}-packet.json`)
    const output = path.join(directory, `${sequence}-bounds.json`)
    if (raw !== undefined) fs.writeFileSync(input, raw)
    else writeJSON(input, packet)
    const result = spawnSync('python3', [path.join(ROOT, 'm5', 'bounds.py'), input, output], {
      encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 10000,
      env: { ...process.env, M5_RAIDS_LEDGER: raidsLedger },
    })
    assert.ifError(result.error)
    return { result, output }
  }
  const packetOf = (stages, gpuCount, concurrency) => ({ stages, total_wall_s: 100, timed_fraction: 0.99, gpu_telemetry: true,
    ...(gpuCount === null ? {} : { gpu_count: gpuCount }), ...(concurrency === OMIT ? {} : { concurrency }) })
  function bounds(label, stages, compute, transfer, { gpuCount = 4, concurrency = calibration(3, true) } = {}) {
    check(`CLI bounds: ${label}`, () => {
      const { result, output } = runBounds(packetOf(stages, gpuCount, concurrency))
      assert.equal(result.status, 0, result.stderr)
      const actual = readJSON(output)
      assert.deepEqual(Object.keys(actual).sort(), [...methods].sort())
      const measured = concurrency !== OMIT && concurrency !== null ? concurrency.factor : null
      const usable = typeof measured === 'number' && measured >= 1
      for (const method of methods) {
        const row = actual[method]
        assert.deepEqual(Object.keys(row).sort(), ['bound', 'feasible', 'k', 'k_derivation', 'p', 'stages'])
        const derivation = row.k_derivation
        let p, k, bound
        if (method in WHOLE) {
          p = 1; k = usable ? Math.min(WHOLE[method], measured) : 1; bound = k
          if (usable) assert.deepEqual(derivation, { rule: 'min(fixed_cap, concurrency factor)', fixed_cap: WHOLE[method], factor: measured, mps: concurrency.mps }, method)
          else if (concurrency === OMIT || concurrency === null) assert.deepEqual(derivation, { rule: 'min(fixed_cap, concurrency factor)', fixed_cap: WHOLE[method], factor: null, mps: null }, method)
          else {
            assert.equal(derivation.rule, 'min(fixed_cap, concurrency factor)')
            assert.equal(derivation.fixed_cap, WHOLE[method])
          }
        } else if (method === 'pipelining') {
          p = transfer; k = 2; bound = amdahl(p, k)
          assert.deepEqual(derivation, { rule: 'fixed_cap', fixed_cap: 2 })
        } else {
          const gpus = gpuCount ?? 1
          p = compute; k = Math.max(1, gpus); bound = amdahl(p, k) / k
          assert.deepEqual(Object.keys(derivation).sort(), ['amdahl', 'cost_basis', 'gpu_count', 'rule'])
          assert.equal(derivation.rule, 'max(1, gpu_count)')
          assert.equal(derivation.gpu_count, gpus)
          assert.equal(derivation.cost_basis, 'equal_gpu_seconds')
          near(derivation.amdahl, amdahl(p, k), `${method}: amdahl`)
        }
        near(row.p, p, `${method}: p`)
        near(row.k, k, `${method}: k`)
        near(row.bound, bound, `${method}: bound`)
        assert.equal(row.feasible, bound >= 1.05, `${method}: feasible`)
        assert.equal(row.feasible, row.bound >= 1.05, `${method}: feasible exactly when bound >= 1.05`)
        const expectedRows = stages.filter(stage => actsOn(method, kindOf(stage)))
        assert.deepEqual(row.stages.map(stage => stage.stage), expectedRows.map(stage => stage.stage), `${method}: stage rows`)
        row.stages.forEach((stage, i) => {
          const source = expectedRows[i], kind = kindOf(source)
          assert.deepEqual(Object.keys(stage).sort(), ['kind', 'mean_gpu_util', 'methods', 'stage', 'wall_fraction'])
          assert.equal(stage.kind, kind)
          near(stage.wall_fraction, Math.min(1, source.wall_s / 100), `${method}/${stage.stage}: recomputed wall_fraction`)
          assert.equal(stage.mean_gpu_util, source.mean_gpu_util)
          assert.deepEqual([...stage.methods].sort(), methods.filter(m => actsOn(m, kind)).sort(), `${method}/${stage.stage}: methods`)
        })
      }
    })
  }
  function rejected(label, packet, raw) {
    check(`CLI bounds: ${label} exits 1 without output`, () => {
      const { result, output } = runBounds(packet, raw)
      assert.equal(result.status, 1, result.stderr)
      assert.ok(!fs.existsSync(output), 'output written for invalid input')
    })
  }
  const stage = (name, wall_s, kind) => ({ stage: name, wall_s, gpu_s: null, wall_fraction: 1, mean_gpu_util: 0.125,
    ...(kind === undefined ? {} : { kind }) })
  const mixed = [stage('arithmetic', 60, 'compute'), stage('movement', 20, 'transfer'), stage('wait', 10, 'other')]
  bounds('Amdahl compute 0.6, transfer 0.2, serial and unmeasured 0.2', mixed, 0.6, 0.2)
  bounds('explicit kind overrides conflicting names',
    [stage('compute', 20, 'transfer'), stage('h2d', 60, 'compute'), stage('kernel copy', 10, 'other')], 0.6, 0.2)
  for (const token of COMPUTE_TOKENS) {
    bounds(`legacy compute token ${token}`, [stage(`phase_${token.toUpperCase()}-end`, 60)], 0.6, 0)
  }
  for (const token of TRANSFER_TOKENS) {
    bounds(`legacy transfer token ${token} wins over compute`, [stage(`compute.${token.toUpperCase()}`, 60)], 0, 0.6)
  }
  bounds('substrings do not classify; other stage still lists whole-workload methods', [stage('precompute copycat', 90)], 0, 0)
  bounds('actionable fraction caps at one', [stage('compute', 120)], 1, 0)
  // Whole-workload factor comes only from the concurrency calibration.
  for (const [label, concurrency] of [['missing concurrency key', OMIT], ['null concurrency', null],
    ['null factor', calibration(null, true)], ['factor below one', calibration(0.8, true)],
    ['factor exactly one', calibration(1)], ['factor 1.04 just infeasible', calibration(1.04)],
    ['factor 1.05 exactly feasible', calibration(1.05)], ['factor 2.5 below both caps', calibration(2.5, true)],
    ['factor 6 between caps', calibration(6)], ['factor 12 capped', calibration(12, true)]]) {
    bounds(`whole workload, ${label}`, mixed, 0.6, 0.2, { concurrency })
  }
  bounds('stage utilisation never sets a factor',
    [{ ...stage('compute', 80), mean_gpu_util: 0.05 }, { ...stage('transfer', 20), mean_gpu_util: null }], 0.8, 0.2, { concurrency: OMIT })
  // Pipelining feasibility threshold: 1 / (1 - p/2) >= 1.05 iff p >= 2/21.
  bounds('pipelining p=0.1 feasible', [stage('h2d', 10), stage('wait', 90)], 0, 0.1)
  bounds('pipelining p=0.09 infeasible', [stage('h2d', 9), stage('wait', 91)], 0, 0.09)
  // Multi-GPU per GPU-second never exceeds 1.
  for (const gpus of [1, 2, 4, 8]) for (const p of [0, 0.25, 0.5, 0.9, 1]) {
    bounds(`multi-GPU infeasible at p=${p}, gpu_count=${gpus}`,
      [stage('kernels', p * 100), stage('wait', 100 - p * 100)], p, 0, { gpuCount: gpus })
  }
  bounds('zero GPUs uses k=1', [stage('compute', 90)], 0.9, 0, { gpuCount: 0 })
  bounds('legacy missing GPU count defaults to one', [stage('compute', 90)], 0.9, 0, { gpuCount: null })
  bounds('multi-GPU factor follows GPU count', [stage('compute', 90)], 0.9, 0, { gpuCount: 7 })
  for (const [label, concurrency] of [['numeric concurrency', 5], ['string concurrency', 'x'],
    ['array concurrency', []], ['boolean concurrency', true], ['string factor', calibration('2')],
    ['boolean factor', calibration(true)]]) {
    rejected(label, packetOf(mixed, 4, concurrency))
  }
  for (const constant of ['NaN', 'Infinity', '-Infinity']) {
    rejected(`nonfinite factor ${constant}`, null,
      JSON.stringify(packetOf(mixed, 4, calibration(1234.5))).replace('"factor":1234.5}', `"factor":${constant}}`))
  }
}

async function main() {
  try {
    if (!process.argv.includes('--profile-only')) {
      await probeScriptTests()
      await cliTests()
      boundsCliTests()
      await runCase('probe-nonzero', { probeFailure: 'rc' }, 'reproduce', 'infra')
      await runCase('probe-invalid-json', { probeFailure: 'json' }, 'reproduce', 'infra')
      const happy = await runCase('happy', { agentDelayMs: 1100 })
      reproduceFacts('happy', happy, 2, 2)
      profileFacts('happy', happy, 0.95)
      check('happy: scored anchor file matches measurements', () => {
        const score = readJSON(path.join(happy.root, 'agent', 'results', 'reproduce', 'anchors_scored.json'))
        assert.equal(score.all_passed, true)
        assert.equal(score.anchors_passed, 2)
        assert.equal(score.anchors_total, 2)
        assert.deepEqual(score.anchors.map(row => [row.id, row.measured_value, row.passed]), [['first', 100.5, true], ['second', 0, true]])
      })
      scoredFile('happy', happy)
      const mismatch = await runCase('anchor-mismatch', { measured: { first: 102, second: 0 } }, 'reproduce', 'anchor')
      reproduceFacts('anchor-mismatch', mismatch, 1, 2)
      // Unanchored runs: the intake gate passes and reproduce passes on stock verification.
      const empty = await runCase('no-anchors', { anchors: [], measured: {} })
      reproduceFacts('no-anchors', empty, 0, 0)
      scoredFile('no-anchors', empty)
      const refs = [reference('ref-a', 100, { uncertainty: { kind: 'standard_error', value: 2 } }), reference('ref-b', 0, { comparison: '==' })]
      const refOnly = await runCase('reference-only', { anchors: refs, measured: { 'ref-a': 250, 'ref-b': -3 } })
      reproduceFacts('reference-only', refOnly, 0, 0)
      scoredFile('reference-only', refOnly)
      const refUnmeasured = await runCase('reference-unmeasured', { anchors: refs, measured: { 'ref-b': 'n/a' } })
      reproduceFacts('reference-unmeasured', refUnmeasured, 0, 0)
      scoredFile('reference-unmeasured', refUnmeasured)
      // With anchors present, run_valid behaves as before; references never decide it.
      const mixed = [anchor('first', 100, { abs: 1 }), reference('ref', 5)]
      const mixedPass = await runCase('mixed-pass', { anchors: mixed, measured: { first: 100.5, ref: 5000 } })
      reproduceFacts('mixed-pass', mixedPass, 1, 1)
      scoredFile('mixed-pass', mixedPass)
      const mixedFail = await runCase('mixed-fail', { anchors: mixed, measured: { first: 102, ref: 5 } }, 'reproduce', 'anchor')
      reproduceFacts('mixed-fail', mixedFail, 0, 1)
      scoredFile('mixed-fail', mixedFail)
      for (const [name, value, stop] of [['relative-boundary', 101, null], ['relative-outside', 101.000001, 'reproduce']]) {
        const run = await runCase(name, { anchors: [anchor('relative', 100, { rel: 0.01 })], measured: { relative: value } }, stop, stop ? 'anchor' : null)
        reproduceFacts(name, run, stop ? 0 : 1, 1)
      }
      const repaired = await runCase('setup-repaired', { setupFailures: 1 })
      reproduceFacts('setup-repaired', repaired, 2, 2)
      const install = await runCase('setup-twice-failed', { setupFailures: 2 }, 'reproduce', 'install')
      reproduceFacts('setup-twice-failed', install, null, null, false)
      const anchorsRepaired = await runCase('anchors-repaired', { anchorsFailures: 1 })
      reproduceFacts('anchors-repaired', anchorsRepaired, 2, 2)
      const anchorsFailed = await runCase('anchors-twice-failed', { anchorsFailures: 2, agentDelayMs: 1100 }, 'reproduce', 'anchor')
      reproduceFacts('anchors-twice-failed', anchorsFailed, null, null)
      // The anchors repair may rewrite run_command.sh, run_anchors.sh or both; the rerun uses the original budget.
      for (const [label, target] of [['command', 'run_command.sh'], ['both', 'both'], ['anchors-only', 'run_anchors.sh']]) {
        const name = `anchors-repair-${label}`
        const run = await runCase(name, { anchorsFailures: 1, anchorsRepairTarget: target, anchorsBudget: 777 })
        reproduceFacts(name, run, 2, 2)
        scoredFile(name, run)
        profileFacts(name, run, 0.95)
      }
      const commandExhausted = await runCase('anchors-repair-command-twice-failed', { anchorsFailures: 2, anchorsRepairTarget: 'run_command.sh' }, 'reproduce', 'anchor')
      reproduceFacts('anchors-repair-command-twice-failed', commandExhausted, null, null)
      const anchorsStray = await runCase('anchors-repair-stray', { anchorsFailures: 1, anchorsRepairTarget: 'both', anchorsRepairStray: true })
      reproduceFacts('anchors-repair-stray', anchorsStray, 2, 2)
      const setupStray = await runCase('setup-repair-stray', { setupFailures: 1, setupRepairStray: true })
      reproduceFacts('setup-repair-stray', setupStray, 2, 2)
      const profileFailed = await runCase('profile-infra', { profileFailures: 1 }, 'profile', 'infra')
      check('profile-infra: incomplete facts without agent repair', () => {
        assert.equal(profileFailed.stage('profile').facts.profile_complete, false)
        assert.equal(profileFailed.stage('profile').facts.tokens_known, false)
      })
      const independent = await runCase('each-script-repaired', { setupFailures: 1, anchorsFailures: 1 })
      reproduceFacts('each-script-repaired', independent, 2, 2)
      profileFacts('each-script-repaired', independent, 0.95)
      const missing = await runCase('missing-measured', { missingMeasured: true }, 'reproduce', 'parse')
      reproduceFacts('missing-measured', missing, null, null)
      // A failed reproduce-freeze (existing reproduce-out, failed fetch, timeout) fails reproduce
      // after passing anchors, without repair; downstream stages are skipped.
      for (const [failure, errorClass, extra] of [['stale', 'infra'], ['fetch', 'infra'], ['timeout', 'timeout', { setupBudget: 2 }]]) {
        await runCase(`freeze-${failure}`, { freezeFailure: failure, ...extra }, 'reproduce', errorClass)
      }
    }
    const low = await runCase('low-coverage', { timings: TIMINGS.map((row, i) => ({ ...row, wall_s: [3, 2, 3.9][i] })) }, 'profile', 'numeric')
    reproduceFacts('low-coverage', low, 2, 2)
    profileFacts('low-coverage', low, 0.89)
    const two = await runCase('two-stages', { timings: [TIMINGS[0], { ...TIMINGS[2], wall_s: 6.5 }] }, 'profile', 'numeric')
    profileFacts('two-stages', two, 0.95)
    for (const wall of [9.8, 10, 10.2]) {
      const name = `duration-wrapper-${wall}`
      const wrapper = await runCase(name, { timings: [...TIMINGS, { stage: 'baseline', wall_s: wall, gpu_s: null }] }, 'profile', 'numeric')
      profileFacts(name, wrapper, 1)
    }
    const namedWrapper = await runCase('named-wrapper', { timings: [...TIMINGS, { stage: 'BASELINE_Process', wall_s: 0.1, gpu_s: null }] }, 'profile', 'numeric')
    profileFacts('named-wrapper', namedWrapper, 0.96)
    const noTelemetry = await runCase('missing-gpu-util', { gpuUtil: null }, 'profile', 'parse')
    check('missing-gpu-util: incomplete profile despite numeric GPU stage times', () => {
      assert.equal(noTelemetry.stage('profile').facts.profile_complete, false)
    })
    const emptyTelemetry = await runCase('empty-gpu-util', { gpuUtil: [] }, 'profile', 'numeric')
    profileFacts('empty-gpu-util', emptyTelemetry, 0.95)
    // Passing profile gate: the concurrency probe runs and can never fail the stage.
    // The harness command unsets CUDA_MPS_*: the real probe must not record MPS.
    const cleared = await runCase('concurrency-real-mps-cleared', { concurrency: 'real', clearMps: true })
    profileFacts('concurrency-real-mps-cleared', cleared, 0.95)
    for (const [mode, extra] of [['real'], ['valid'], ['valid-null'], ['timeout', { profileBudget: 2 }], ['rc'], ['missing'],
      ['invalid-json'], ['invalid-extra-key'], ['invalid-batch-order'], ['invalid-nonfinite'], ['invalid-singles']]) {
      const name = `concurrency-${mode}`
      const run = await runCase(name, { concurrency: mode, ...extra })
      profileFacts(name, run, 0.95)
    }
    // Recorded run11 (positive-openmm): the probe exited 0 but its out/ and log fetches failed,
    // so the packet lost a valid calibration. One failed attempt each must now be retried into the
    // validated object; fetches failing on every attempt still give null without affecting the stage.
    const run11 = await runCase('concurrency-fetch-fails-once', { concurrency: 'valid', concurrencyFetchFailures: 1 })
    profileFacts('concurrency-fetch-fails-once', run11, 0.95)
    check('concurrency-fetch-fails-once: validated concurrency and non-null headroom after the retry', () => {
      assert.deepEqual(readJSON(path.join(run11.root, 'agent', 'profile-packet.json')).concurrency, fixture.VALID_CONCURRENCY)
      assert.equal(run11.stage('profile').facts.headroom, fixture.VALID_CONCURRENCY.factor)
    })
    const lostRun = await runCase('concurrency-fetch-always-fails', { concurrency: 'valid', concurrencyFetchFailures: 99 })
    profileFacts('concurrency-fetch-always-fails', lostRun, 0.95)
    check('concurrency-fetch-always-fails: concurrency null, headroom null, profile PASS', () => {
      assert.equal(readJSON(path.join(lostRun.root, 'agent', 'profile-packet.json')).concurrency, null)
      assert.equal(lostRun.stage('profile').facts.headroom, null)
      assert.equal(lostRun.stage('profile').signature.status, 'PASS')
    })

  } catch (error) {
    failures++
    console.log(`FAIL test harness: ${error.stack}`)
  } finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
