#!/usr/bin/env node
'use strict'

// Black-box contract tests. Do not inspect the pipeline, scorer, or git diff.
// Usage: node tools/test_m5_reproduce.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')
const ROOT = path.resolve(__dirname, '..')
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
const TIMINGS = [{ stage: 'cpu', wall_s: 5, gpu_s: null }, { stage: 'compute', wall_s: 4.5, gpu_s: 0 }]
const PREDICTIONS = {
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
if (( n <= ${failures} )); then exit 7; fi
printf '%s\\n' pinned > baseline-published/pin
printf '%s\\n' representative > data/input`)
}
module.exports = {
  async run({ title, prompt }) {
    const root = process.env.M5_REPRODUCE_ROOT
    const config = JSON.parse(process.env.M5_REPRODUCE_CONFIG)
    fs.appendFileSync(process.env.M5_REPRODUCE_CALLS, JSON.stringify({ label: title, prompt }) + '\n')
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
    if (title === 'harness' || title === 'harness-repair') {
      const harness = path.join(agent, 'harness')
      setupScript(harness, config.setupFailures)
      if (title === 'harness') {
        script(path.join(harness, 'run_anchors.sh'), `test -f baseline-published/pin\ntest -f data/input\nmkdir -p out\nprintf '%s\\n' '${SENTINEL}:anchors'\n` +
          (config.missingMeasured ? 'rm -f out/anchors_measured.json\n' : emitJSON('out/anchors_measured.json', config.measured)) +
          `printf '%s\\n' '${SENTINEL}' > out/anchors-private.txt`)
        script(path.join(harness, 'profile.sh'), `test -f baseline-published/pin\ntest -f out/anchors_measured.json\nmkdir -p out/profile\nprintf '%s\\n' '${SENTINEL}:profile'\n` +
          emitJSON('out/profile/stages.json', config.timings.map(row => ({ ...row, private_content: SENTINEL }))) +
          emitJSON('out/profile/total_wall_s.json', { total_wall_s: config.total }) +
          `printf '%s\\n' '${SENTINEL}' > out/profile/raw-telemetry.txt`)
      }
    }
    if (title === 'seal') {
      writeJSON(path.join(agent, 'PREDICTIONS.json'), PREDICTIONS)
      facts = { seal_present: true, seal_verified: true, prediction_count: 1 }
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
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}
function noLeak(directory) {
  assert.ok(fs.statSync(directory).isDirectory())
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    assert.ok(!entry.name.includes(SENTINEL), 'sentinel in filename')
    assert.ok(!entry.isSymbolicLink(), 'operator symlink')
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) noLeak(file)
    else assert.ok(!fs.readFileSync(file).includes(Buffer.from(SENTINEL)), `private content leaked: ${entry.name}`)
  }
}
async function runCase(name, overrides = {}, stoppedAt = null, errorClass = null) {
  const root = path.join(scratch, name)
  const config = { anchors: ANCHORS, measured: { first: 100.5, second: 0, ignored: 999 }, timings: TIMINGS, total: 10, setupFailures: 0, ...overrides }
  const args = path.join(root, 'control', 'args.json')
  writeJSON(args, { run_root: root, tag: 'reproduce-test' })
  const box = path.join(root, 'box')
  fs.mkdirSync(box, { recursive: true })
  // Map the contract's absolute remote /tmp/m5-* paths into this case's box.
  script(path.join(root, 'bin', 'box'), 'command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}' + '\ncd -- "$BOX_ROOT"\nbash -c "$command"\n# Let tiny detached fixtures finish before the runner polls.\nif [[ $command == *timeout* ]]; then\n  for ((i=0; i<1000; i++)); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi\nexit 0' )
  script(path.join(root, 'bin', 'fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}' + '\ncd -- "$BOX_ROOT"\nexec cp -r -- "$source" "$2"')
  const callsFile = path.join(root, 'calls.jsonl')
  const stdout = fs.openSync(path.join(root, 'stdout.log'), 'w')
  const stderrFile = path.join(root, 'stderr.log')
  const stderr = fs.openSync(stderrFile, 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(ROOT, 'idea', 'wf.js'), '--script', path.join(ROOT, 'm5', 'pipeline.js'),
        '--args', args, '--out', path.join(root, 'agent', 'wf'), '--disable-family', 'claude'], {
        cwd: ROOT, timeout: 240000, stdio: ['ignore', stdout, stderr], env: { ...process.env,
          WF_STUB: __filename, M5_REPRODUCE_ROOT: root, M5_REPRODUCE_CONFIG: JSON.stringify(config), M5_REPRODUCE_CALLS: callsFile,
          BOX_ROOT: box, BOX: path.join(root, 'bin', 'box'), FETCH: path.join(root, 'bin', 'fetch') },
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
    assert.equal(calls.filter(call => call.label === 'harness').length, 1)
    assert.equal(calls.filter(call => call.label === 'harness-repair').length, config.setupFailures ? 1 : 0)
  })
  check(`${name}: receipts under C/receipts`, () => {
    const directory = path.join(root, 'control', 'receipts')
    const files = fs.readdirSync(directory).sort()
    const receipts = files.map(file => {
      assert.match(file, /^\d{4}-(upload|setup|anchors|profile)\.json$/)
      const receipt = readJSON(path.join(directory, file))
      assert.equal(receipt.name, file.slice(0, -5))
      assert.ok(Number.isInteger(receipt.rc))
      assert.equal(receipt.timed_out, false)
      assert.equal(receipt.fetched, true)
      assert.ok(Number.isInteger(receipt.wall_s) && receipt.wall_s >= 0)
      for (const key of ['started_utc', 'ended_utc']) assert.ok(Number.isFinite(Date.parse(receipt[key])))
      return { operation: file.match(/-(\w+)\.json$/)[1], ...receipt }
    })
    assert.deepEqual(files.map(file => Number(file.slice(0, 4))), files.map((_, i) => i + 1))
    const count = operation => receipts.filter(receipt => receipt.operation === operation).length
    const firstSetup = receipts.findIndex(receipt => receipt.operation === 'setup')
    assert.ok(firstSetup >= 1, 'no harness upload before setup')
    assert.ok(receipts.slice(0, firstSetup).every(receipt => receipt.operation === 'upload'))
    assert.equal(count('upload'), firstSetup + (config.setupFailures ? 1 : 0))
    if (config.setupFailures) assert.equal(receipts[firstSetup + 1].operation, 'upload')
    assert.equal(count('setup'), config.setupFailures ? 2 : 1)
    assert.equal(count('anchors'), config.setupFailures >= 2 ? 0 : 1)
    assert.equal(count('profile'), stoppedAt === 'reproduce' ? 0 : 1)
    assert.deepEqual(receipts.filter(receipt => receipt.operation === 'setup').map(receipt => receipt.rc),
      config.setupFailures >= 2 ? [7, 7] : config.setupFailures ? [7, 0] : [0])
  })
  check(`${name}: private harness output fetched; operator has no sentinel`, () => {
    const results = path.join(root, 'agent', 'results', 'reproduce')
    assert.ok(fs.readdirSync(results).filter(file => file.endsWith('.log')).some(file => fs.readFileSync(path.join(results, file), 'utf8').includes(SENTINEL)), 'sentinel absent from fetched logs')
    noLeak(path.join(root, 'operator'))
  })
  return { root, config, stage }
}
function reproduceFacts(name, run, passed, total, stock = true) {
  check(`${name}: reproduce facts and validity`, () => {
    const row = run.stage('reproduce')
    assert.deepEqual(row.facts, { anchors_passed: passed, anchors_total: total, stock_verified: stock,
      tuned_control_valid: null, tokens_known: false, gpu_busy_known: false })
    if (total !== null) assert.equal(row.signature.run_valid, passed === total)
  })
}
function profileFacts(name, run, fraction) {
  check(`${name}: profile packet and facts derived from files`, () => {
    const input = path.join(run.root, 'agent', 'results', 'profile', 'out', 'profile')
    const timings = readJSON(path.join(input, 'stages.json'))
    const total = readJSON(path.join(input, 'total_wall_s.json')).total_wall_s
    const packet = readJSON(path.join(run.root, 'agent', 'profile-packet.json'))
    assert.deepEqual(Object.keys(packet).sort(), ['gpu_telemetry', 'stages', 'timed_fraction', 'total_wall_s'])
    assert.deepEqual(packet.stages, timings.map(({ stage, wall_s, gpu_s }) => ({ stage, wall_s, gpu_s, wall_fraction: Math.min(1, wall_s / total) })))
    assert.equal(packet.total_wall_s, total)
    assert.equal(packet.timed_fraction, Math.min(1, timings.reduce((sum, row) => sum + row.wall_s, 0) / total))
    assert.equal(packet.timed_fraction, fraction)
    assert.equal(packet.gpu_telemetry, timings.some(row => row.gpu_s !== null))
    assert.deepEqual(run.stage('profile').facts, { profile_complete: true, timed_fraction: fraction,
      gpu_telemetry: packet.gpu_telemetry, tokens_known: false, gpu_busy_known: false })
    assert.ok(fs.readFileSync(path.join(input, 'raw-telemetry.txt'), 'utf8').includes(SENTINEL))
  })
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
async function main() {
  try {
    await cliTests()
    const happy = await runCase('happy')
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
    const missing = await runCase('missing-measured', { missingMeasured: true }, 'reproduce', 'parse')
    reproduceFacts('missing-measured', missing, null, null)
    const low = await runCase('low-coverage', { timings: [{ stage: 'cpu', wall_s: 8.9, gpu_s: null }] }, 'profile', 'parse')
    reproduceFacts('low-coverage', low, 2, 2)
    profileFacts('low-coverage', low, 0.89)
  } catch (error) {
    failures++
    console.log(`FAIL test harness: ${error.stack}`)
  } finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
