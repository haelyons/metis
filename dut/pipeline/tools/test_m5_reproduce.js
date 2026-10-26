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
const PROBE_SENTINEL = 'PROBE_PRIVATE_SENTINEL_197352'
const SENTINEL = 'HARNESS_PRIVATE_SENTINEL_846291'
const STAGES = ['intake', 'reproduce', 'profile', 'seal', 'propose', 'implement', 'evaluate', 'takeaways']
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
function writeJSON(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value) + '\n')
}
const anchor = (id, published_value, tolerance) => ({ id, published_value, tolerance, quantity: 'fixture quantity', source: 'https://example.org/published' })
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
function setupScript(directory, failures) {
  script(path.join(directory, 'setup.sh'), `mkdir -p out baseline-published data
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
      if (title === 'harness' || title === 'harness-repair') setupScript(harness, failuresFor('setupFailures'))
      if (title === 'harness' || title === 'anchors-repair') {
        script(path.join(harness, 'run_anchors.sh'), failureScript('anchors', failuresFor('anchorsFailures')) + `bash harness/run_command.sh\ntest -f baseline-published/pin\ntest -f data/input\nmkdir -p out\nprintf '%s\\n' '${SENTINEL}:anchors'\n` +
          (config.missingMeasured ? 'rm -f out/anchors_measured.json\n' : emitJSON('out/anchors_measured.json', config.measured)) +
          `printf '%s\\n' '${SENTINEL}' > out/anchors-private.txt`)
      }
      if (title === 'harness') script(path.join(harness, 'run_command.sh'),
        `test -f baseline-published/pin\ntest -f data/input\nprintf '%s\\n' '${SENTINEL}:command' >> out/command-calls.log`)
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
  writeJSON(args, { run_root: root, tag: 'reproduce-test', stub: { propose: 'PASS', implement: 'PASS', evaluate: 'PASS' } })
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
  script(path.join(root, 'bin', 'box'), 'command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}' + '\nexport PATH="$BOX_ROOT/../box-bin:$PATH"\ncd -- "$BOX_ROOT"\nbash -c "$command"\n"$M5_TEST_NODE" "$M5_REPLACE_PROBE"\n# Let tiny detached fixtures finish before the runner polls.\nif [[ $command == *timeout* ]]; then\n  for ((i=0; i<1000; i++)); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi\nexit 0' )
  script(path.join(root, 'bin', 'fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}' + '\ncd -- "$BOX_ROOT"\nexec cp -r -- "$source" "$2"')
  const callsFile = path.join(root, 'calls.jsonl')
  const stdout = fs.openSync(path.join(root, 'stdout.log'), 'w')
  const stderrFile = path.join(root, 'stderr.log')
  const stderr = fs.openSync(stderrFile, 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(pipeline, 'idea', 'wf.js'), '--script', path.join(pipeline, 'm5', 'pipeline.js'),
        '--args', args, '--out', path.join(root, 'agent', 'wf'), '--disable-family', 'claude'], {
        cwd: pipeline, timeout: 240000, stdio: ['ignore', stdout, stderr], env: { ...process.env,
          M5_RAIDS_LEDGER: raidsLedger, WF_STUB: __filename, M5_REPRODUCE_ROOT: root, M5_REPRODUCE_CONFIG: JSON.stringify(config), M5_REPRODUCE_CALLS: callsFile,
          M5_TEST_NODE: process.execPath, M5_REPLACE_PROBE: replaceProbe, BOX_ROOT: box, BOX: path.join(root, 'bin', 'box'), FETCH: path.join(root, 'bin', 'fetch') },
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
    assert.equal(signature.exit_code, errorClass === 'anchor' ? 4 : 2)
  })
  check(`${name}: one harness call and bounded repair`, () => {
    assert.equal(calls.filter(call => call.label === 'harness').length, config.probeFailure ? 0 : 1)
    assert.equal(calls.filter(call => call.label === 'profile-repair').length, 0)
    for (const [label, needed] of [['harness-repair', config.setupFailures],
      ['anchors-repair', config.setupFailures < 2 && config.anchorsFailures]]) {
      assert.equal(calls.filter(call => call.label === label).length, needed ? 1 : 0, label)
      for (const call of calls.filter(call => call.label === label)) {
        assert.match(call.name, /-retry1$/, label)
        const script = label === 'harness-repair' ? 'setup' : 'anchors'
        assert.ok(call.prompt.includes(`${SENTINEL}:${script}:240`), 'last failure log line missing')
        assert.ok(!call.prompt.includes(`${SENTINEL}:${script}:1\n`), 'unbounded failure log')
      }
    }
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
      assert.ok(Number.isInteger(receipt.rc))
      assert.equal(receipt.timed_out, false)
      assert.equal(receipt.fetched, true)
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
    const count = operation => receipts.filter(receipt => receipt.operation === operation).length
    const firstSetup = receipts.findIndex(receipt => receipt.operation === 'setup')
    assert.ok(firstSetup >= 1, 'no harness upload before setup')
    assert.ok(receipts.slice(0, firstSetup).every(receipt => receipt.operation === 'upload'))
    assert.equal(count('upload'), firstSetup + (config.setupFailures ? 1 : 0) + (config.setupFailures < 2 && config.anchorsFailures ? 1 : 0) + (stoppedAt === 'reproduce' ? 0 : 1))
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
  return { root, config, stage }
}
function reproduceFacts(name, run, passed, total, stock = true) {
  check(`${name}: reproduce facts and validity`, () => {
    const row = run.stage('reproduce')
    assert.deepEqual(row.facts, { anchors_passed: passed, anchors_total: total, stock_verified: stock,
      tuned_control_valid: null, tokens_known: true, gpu_busy_known: false })
    assert.equal(row.signature.gpu_s, 0)
    if (total !== null) assert.equal(row.signature.run_valid, passed === total)
  })
}
function profileFacts(name, run, fraction) {
  check(`${name}: profile packet and facts derived from files`, () => {
    const input = path.join(run.root, 'agent', 'results', 'profile', 'out', 'profile')
    const timings = readJSON(path.join(input, 'stages.json'))
    const total = readJSON(path.join(input, 'total_wall_s.json')).total_wall_s
    const packet = readJSON(path.join(run.root, 'agent', 'profile-packet.json'))
    assert.deepEqual(Object.keys(packet).sort(), ['gpu_count', 'gpu_telemetry', 'stages', 'timed_fraction', 'total_wall_s'])
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
    assert.deepEqual(run.stage('profile').facts, { profile_complete: true, timed_fraction: fraction,
      gpu_telemetry: packet.gpu_telemetry, tokens_known: false, gpu_busy_known: false })
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
        const expected = options.expectedAnchors ?? anchors.map(entry => {
          const tolerance = typeof entry.tolerance === 'number' ? entry.tolerance : entry.tolerance.abs ?? entry.tolerance.rel * Math.abs(entry.published_value)
          const passed = Math.abs(measured[entry.id] - entry.published_value) <= tolerance
          return { id: entry.id, published_value: entry.published_value, measured_value: measured[entry.id], tolerance: entry.tolerance,
            passed, ...(!passed ? { reason: 'out_of_tolerance' } : {}) }
        })
        assert.deepEqual(scored, { anchors: expected, anchors_passed: expected.filter(row => row.passed).length, anchors_total: expected.length, all_passed: expected.every(row => row.passed) })
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
      expectedAnchors: [{ id: SENTINEL, published_value: published, measured_value: reason === 'non_numeric' ? null : measured,
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
    expectedAnchors: [{ id: SENTINEL, published_value: 1, measured_value: null, tolerance: 0, passed: false, reason }],
    ...options,
  })
  for (const [label, anchors, measured, options] of [
    ['empty anchors', [], {}], ['duplicate IDs', [secret, secret], { [SENTINEL]: 1 }],
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
  await score('invalid input creates no output', [], {}, 1)
  await score('output write failure', ANCHORS, { first: 100, second: 0 }, 1, null, { outputDirectory: true })
}
function boundsCliTests() {
  const directory = path.join(scratch, 'bounds-cli')
  fs.mkdirSync(directory)
  const methods = ['data-parallel over inputs', 'batching', 'multi-GPU', 'ensembles', 'pipelining']
  let sequence = 0
  function bounds(label, stages, compute, transfer, gpuCount = 4, meanUtil = 0.125) {
    check(`CLI bounds: ${label}`, () => {
      const input = path.join(directory, `${++sequence}-packet.json`)
      const output = path.join(directory, `${sequence}-bounds.json`)
      writeJSON(input, { stages, total_wall_s: 100, timed_fraction: 0.99, gpu_telemetry: true,
        ...(gpuCount === null ? {} : { gpu_count: gpuCount }) })
      const result = spawnSync('python3', [path.join(ROOT, 'm5', 'bounds.py'), input, output], {
        encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 10000,
        env: { ...process.env, M5_RAIDS_LEDGER: raidsLedger },
      })
      assert.ifError(result.error)
      assert.equal(result.status, 0, result.stderr)
      const actual = readJSON(output)
      assert.deepEqual(Object.keys(actual).sort(), [...methods].sort())
      for (const [i, method] of methods.entries()) {
        const p = [compute, transfer, compute, compute, transfer][i]
        const factor = meanUtil === null || compute === 0 ? 1 : 1 / Math.max(meanUtil, 0.05)
        const k = [Math.min(8, factor), Math.min(4, factor), Math.max(1, gpuCount ?? 1), Math.min(8, factor), Math.min(2, factor)][i]
        const expected = 1 / ((1 - p) + p / k)
        assert.deepEqual(Object.keys(actual[method]).sort(), ['bound', 'feasible', 'k', 'k_derivation', 'p', 'stages'])
        assert.ok(Math.abs(actual[method].p - p) < 1e-12, `${method}: p`)
        assert.equal(actual[method].k, k, `${method}: k`)
        assert.ok(Math.abs(actual[method].bound - expected) < 1e-12, `${method}: bound`)
        assert.equal(actual[method].feasible, expected >= 1.05, `${method}: feasible`)
        const derivation = actual[method].k_derivation
        if (method === 'multi-GPU') {
          assert.equal(derivation.rule, 'max(1, gpu_count)')
          assert.equal(derivation.gpu_count, gpuCount ?? 1)
        } else {
          assert.equal(derivation.mean_util, compute === 0 ? null : meanUtil)
          assert.equal(derivation.fixed_cap, [8, 4, null, 8, 2][i])
          assert.equal(derivation.missing_util_k, 1)
        }
        assert.ok(Array.isArray(actual[method].stages))
      }
    })
  }
  const stage = (name, wall_s, kind) => ({ stage: name, wall_s, gpu_s: null, wall_fraction: 1, mean_gpu_util: 0.125,
    ...(kind === undefined ? {} : { kind }) })
  bounds('Amdahl compute 0.6, transfer 0.2, serial and unmeasured 0.2',
    [stage('arithmetic', 60, 'compute'), stage('movement', 20, 'transfer'), stage('wait', 10, 'other')], 0.6, 0.2)
  bounds('explicit kind overrides conflicting names',
    [stage('compute', 20, 'transfer'), stage('h2d', 60, 'compute'), stage('kernel copy', 10, 'other')], 0.6, 0.2)
  for (const token of ['compute', 'kernel', 'kernels', 'inference', 'training', 'forward', 'backward']) {
    bounds(`legacy compute token ${token}`, [stage(`phase_${token.toUpperCase()}-end`, 60)], 0.6, 0)
  }
  for (const token of ['transfer', 'transfers', 'h2d', 'd2h', 'htod', 'dtoh', 'copy', 'memcpy', 'upload', 'download']) {
    bounds(`legacy transfer token ${token} wins over compute`, [stage(`compute.${token.toUpperCase()}`, 60)], 0, 0.6)
  }
  bounds('substrings do not classify; other remains serial', [stage('precompute copycat', 90)], 0, 0)
  bounds('small actionable fractions make every method infeasible',
    [stage('compute', 1), stage('transfer', 1), stage('wait', 98)], 0.01, 0.01)
  bounds('one GPU makes multi-GPU infeasible', [stage('compute', 90)], 0.9, 0, 1)
  bounds('zero GPUs caps multi-GPU factor at one', [stage('compute', 90)], 0.9, 0, 0)
  bounds('legacy missing GPU count defaults to one', [stage('compute', 90)], 0.9, 0, null)
  for (const [label, util] of [['100% utilisation gives same-GPU bound 1', 1],
    ['25% utilisation raises same-GPU cap', 0.25], ['missing utilisation gives conservative cap', null],
    ['zero utilisation respects fixed caps', 0]]) {
    bounds(label, [ { ...stage('compute', 80), mean_gpu_util: util }, stage('transfer', 20)], 0.8, 0.2, 4, util)
  }
  bounds('compute utilisation is an arithmetic mean',
    [{ ...stage('compute', 60), mean_gpu_util: 0.125 },
      { ...stage('kernels', 20), mean_gpu_util: 0.375 }, stage('transfer', 20)], 0.8, 0.2, 4, 0.25)
  bounds('one missing compute utilisation forces conservative cap',
    [stage('compute', 60), { ...stage('kernels', 20), mean_gpu_util: null }, stage('transfer', 20)], 0.8, 0.2, 4, null)
  bounds('multi-GPU factor follows GPU count', [stage('compute', 90)], 0.9, 0, 7)
  bounds('actionable fraction caps at one', [stage('compute', 120)], 1, 0)
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
      const mismatch = await runCase('anchor-mismatch', { measured: { first: 102, second: 0 } }, 'reproduce', 'anchor')
      reproduceFacts('anchor-mismatch', mismatch, 1, 2)
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

  } catch (error) {
    failures++
    console.log(`FAIL test harness: ${error.stack}`)
  } finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
