#!/usr/bin/env node
'use strict'

// Black-box tests: the pipeline is executed, never imported or inspected.
// Usage: node tools/test_m5_intake_seal.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { createHash } = require('node:crypto')
const { spawn } = require('node:child_process')

const ROOT = path.resolve(__dirname, '..')
const SENTINEL = 'SENTINEL_CONTENT_77'
const STAGES = ['intake', 'reproduce', 'profile', 'seal', 'propose', 'implement', 'evaluate', 'takeaways']
const INTAKE = { found: true, anchors_count: 2, data: 'available', licence: 'permitted', stock_environment: true, size: 'small' }
const PREDICTIONS = {
  predictions: [
    { method: 'batching', expected_speedup_interval: { low: 1.2, high: 2 },
      outcome_vs_compute_points: [1, 2, 4].map(compute_budget => ({
        compute_budget, predicted_outcome: 499500, uncertainty: 'exact integer equality',
      })), content: SENTINEL },
    { method: 'pipelining', expected_speedup_interval: { low: 1.1, high: 1.5 },
      outcome_vs_compute_points: [1, 2, 4].map(compute_budget => ({
        compute_budget, predicted_outcome: 499500, uncertainty: 'exact integer equality',
      })), content: SENTINEL },
  ],
  equivalence_metrics: ['exact integer equality'],
  paired_seed_tests: [0, 1, 2, 3, 4],
  sample_sizes: { integers: 1000 },
  confidence_rule: '95% confidence interval on paired timing differences',
  hardware_cost_basis: 'CPU seconds on the same stock machine',
  timing_scope: 'whole process',
  minimum_worthwhile_gain: 1.1,
  evaluation_inputs: ['integers 0 through 999'],
  splits: { evaluation: [0, 1000] },
  compute_budgets: [1, 2, 4],
  repetitions: 5,
  warmup: 'one untimed run',
  scheduling_order: 'alternate baseline and candidate for each seed',
  equal_outcome_target: 499500,
  content: SENTINEL,
}
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const readRows = file => fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse)
const writeJSON = (file, value) => {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n')
}

// The same module is loaded by WF_STUB. Only these two agents write content;
// neither agent computes hashes or writes control/operator state.
module.exports = {
  async run({ title, prompt }) {
    const runRoot = process.env.M5_INTAKE_SEAL_ROOT
    fs.appendFileSync(process.env.M5_INTAKE_SEAL_CALLS, JSON.stringify({ label: title, prompt }) + '\n')
    let facts = { v: `${title} stub` }
    if (title === 'intake') {
      facts = JSON.parse(process.env.M5_INTAKE_SEAL_FACTS)
      const brief = fs.readFileSync(process.env.M5_INTAKE_SEAL_BRIEF, 'utf8')
      const fixtures = {
        benchmark: {
          identity: 'synthetic contract fixture', outcome_definition: 'exact integer sum',
          citations: ['https://example.org/reference-1', 'https://example.org/reference-2'],
          licences: ['MIT'], intended_use_permissions: 'permitted',
          stock_environment: true, stock_environment_evidence: 'Python standard library only',
          data_gib: 0.001, peak_working_set_gib: 0.001,
          scoring_rules: 'exact integer equality', repeatability_rules: 'deterministic',
        },
        data: {
          required_inputs: ['integers 0 through 999'], availability: facts.data,
          access_instructions: 'Generate range(1000) locally', generated: true,
          licences: ['MIT'], pins: ['range(1000)'], splits: { evaluation: [0, 1000] }, seeds: [0],
        },
        baseline: {
          repo: 'https://example.org/fixture', commit: '0123456789012345678901234567890123456789',
          build_commands: ['python3 --version'], run_commands: ['python3 -c "print(sum(range(1000)))"'],
          published_configuration: { count: 1000 }, sources: ['https://example.org/reference-1'],
        },
        EXECUTION: {
          representative_scale: { count: 1000 }, inputs: { integers: 'range(1000)' },
          outputs: { sum: 499500 }, timing_scope: 'whole process', scoring_interface: 'exact integer equality',
        },
      }
      if (process.env.M5_INTAKE_SEAL_INCOMPLETE_BASELINE) delete fixtures.baseline.published_configuration
      for (const name of ['benchmark', 'anchors', 'data', 'baseline', 'EXECUTION']) {
        const content = name === 'anchors'
          ? Array.from({ length: facts.anchors_count }, (_, i) => ({
            id: `anchor-${i + 1}`, quantity: 'sum', published_value: 499500,
            tolerance: 0.01, source: `https://example.org/reference-${i + 1}`,
            content: SENTINEL, brief,
          }))
          : { ...fixtures[name], content: SENTINEL, brief }
        writeJSON(path.join(runRoot, 'agent', 'intake', `${name}.json`), content)
      }
      fs.writeFileSync(path.join(runRoot, 'agent', 'intake', 'brief.md'), brief)
    }
    if (title === 'seal') {
      if (!process.env.M5_INTAKE_SEAL_PRESERVE) writeJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json'), PREDICTIONS)
      // Deliberately claim verification: the deterministic step must verify it.
      facts = { seal_present: true, seal_verified: true, prediction_count: PREDICTIONS.predictions.length }
    }
    return {
      text: JSON.stringify(facts), json: facts, jsonError: null, sessionID: 'stub',
      tokens: { input: 10, output: 5, reasoning: 0 }, cost: 0.001,
      tools: 0, ms: 5, errors: [], refusal: false,
    }
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
if (require.main !== module) return

let failures = 0
let checks = 0
const parent = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_intake_seal_'))
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}

function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']'
  if (value !== null && typeof value === 'object') {
    return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}'
  }
  return JSON.stringify(value)
}
function predictionHash(runRoot) {
  return createHash('sha256').update(canonical(readJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json')))).digest('hex')
}
function noLeak(runRoot) {
  const operator = path.join(runRoot, 'operator')
  assert.ok(fs.statSync(operator).isDirectory())
  function visit(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      assert.ok(!entry.name.includes(SENTINEL), 'sentinel in operator filename')
      const file = path.join(dir, entry.name)
      assert.ok(!entry.isSymbolicLink(), 'operator symlink could expose content')
      if (entry.isDirectory()) visit(file)
      else assert.ok(!fs.readFileSync(file).includes(Buffer.from(SENTINEL)), `content leaked to ${path.relative(operator, file)}`)
    }
  }
  visit(operator)
}

async function runCase(name, facts = INTAKE, { runRoot = path.join(parent, name), preserve = false, incompleteBaseline = false } = {}) {
  const control = path.join(runRoot, 'control')
  const brief = path.join(runRoot, 'brief.md')
  fs.mkdirSync(control, { recursive: true })
  fs.writeFileSync(brief, `# Intake fixture\n${SENTINEL}\n`)
  const argsFile = path.join(control, 'args.json')
  writeJSON(argsFile, { run_root: runRoot, brief, tag: 'intake-seal-test', stub: { reproduce: 'PASS', profile: 'PASS' } })
  // Separate workflow directories prevent WF resume caches from hiding calls.
  const out = path.join(runRoot, 'agent', `wf-${name}`)
  const callsFile = path.join(runRoot, `calls-${name}.jsonl`)
  const stdoutFile = path.join(runRoot, `stdout-${name}.log`)
  const stderrFile = path.join(runRoot, `stderr-${name}.log`)
  const stdout = fs.openSync(stdoutFile, 'w')
  const stderr = fs.openSync(stderrFile, 'w')
  const signatureFile = path.join(runRoot, 'operator', 'signatures.jsonl')
  const previousRows = fs.existsSync(signatureFile) ? readRows(signatureFile) : []
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(ROOT, 'idea', 'wf.js'),
        '--script', path.join(ROOT, 'm5', 'pipeline.js'), '--args', argsFile,
        '--out', out, '--disable-family', 'claude'], {
        cwd: ROOT, timeout: 30000, stdio: ['ignore', stdout, stderr],
        env: { ...process.env, WF_STUB: __filename, M5_INTAKE_SEAL_ROOT: runRoot,
          M5_INTAKE_SEAL_FACTS: JSON.stringify(facts), M5_INTAKE_SEAL_BRIEF: brief,
          M5_INTAKE_SEAL_CALLS: callsFile, M5_INTAKE_SEAL_PRESERVE: preserve ? '1' : '',
          M5_INTAKE_SEAL_INCOMPLETE_BASELINE: incompleteBaseline ? '1' : '' },
      })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  check(`${name}: workflow exits successfully`, () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0, `exit ${child.status}, signal ${child.signal}; ${fs.readFileSync(stderrFile, 'utf8').slice(-1000)}`)
  })
  const rows = fs.existsSync(signatureFile) ? readRows(signatureFile) : []
  // Accept either a fresh per-run journal or an appended journal.
  const appended = previousRows.length && rows.length > previousRows.length &&
    previousRows.every((row, i) => JSON.stringify(row) === JSON.stringify(rows[i]))
  const current = appended ? rows.slice(previousRows.length) : rows
  const stages = current.filter(row => STAGES.includes((row.signature || row).stage))
  const stage = label => stages.find(row => (row.signature || row).stage === label)
  const signature = label => { const row = stage(label); assert.ok(row, `missing ${label} signature`); return row.signature || row }
  const calls = fs.existsSync(callsFile) ? readRows(callsFile) : []
  check(`${name}: exactly one intake call`, () => assert.equal(calls.filter(row => row.label === 'intake').length, 1))
  check(`${name}: intake facts emitted unchanged`, () => {
    for (const [key, value] of Object.entries(facts)) assert.deepEqual(stage('intake')?.facts?.[key], value, key)
  })
  check(`${name}: intake files contain stub content and supplied brief`, () => {
    for (const file of ['benchmark', 'anchors', 'data', 'baseline', 'EXECUTION']) {
      const value = readJSON(path.join(runRoot, 'agent', 'intake', `${file}.json`))
      if (file === 'baseline' && incompleteBaseline) assert.ok(!Object.hasOwn(value, 'published_configuration'))
      if (file === 'anchors') assert.equal(value.length, facts.anchors_count)
      for (const entry of file === 'anchors' ? value : [value]) {
        assert.equal(entry.content, SENTINEL)
        assert.equal(entry.brief, fs.readFileSync(brief, 'utf8'))
      }
    }
    assert.ok(calls.find(row => row.label === 'intake')?.prompt.includes(brief), 'args.brief path not passed to intake')
  })
  check(`${name}: sentinel absent throughout R/operator`, () => noLeak(runRoot))
  return { runRoot, out, stages, signature, stage, calls }
}

function checkStatuses(name, run, stoppedAt) {
  const expected = STAGES.map((stage, i) => ({ stage, status: stage === stoppedAt ? 'FAIL'
    : stoppedAt && i > STAGES.indexOf(stoppedAt) && stage !== 'takeaways' ? 'SKIPPED' : 'PASS' }))
  check(`${name}: ordered stage statuses; takeaways runs`, () => {
    assert.deepEqual(run.stages.map(row => {
      const { stage, status } = row.signature || row
      return { stage, status }
    }), expected)
  })
  check(`${name}: result records correct stop and skipped stages`, () => {
    const result = readJSON(path.join(run.out, 'result.json'))
    assert.equal(result.stopped_at, stoppedAt)
    assert.deepEqual(result.stages.map(({ stage, status }) => ({ stage, status })), expected)
  })
}

async function main() {
  try {
    const happy = await runCase('happy')
    checkStatuses('happy', happy, null)
    check('happy: exactly one seal call', () => assert.equal(happy.calls.filter(row => row.label === 'seal').length, 1))
    check('happy: seal facts', () => {
      const facts = happy.stage('seal')?.facts
      assert.equal(facts?.seal_present, true)
      assert.equal(facts?.seal_verified, true)
      assert.equal(facts?.prediction_count, 2)
    })
    const firstFile = path.join(happy.runRoot, 'control', 'seals', '0001.json')
    let firstBytes
    check('happy: 0001 contains independently recomputed canonical SHA-256', () => {
      firstBytes = fs.readFileSync(firstFile)
      assert.deepEqual(readJSON(path.join(happy.runRoot, 'agent', 'PREDICTIONS.json')), PREDICTIONS)
      assert.equal(JSON.parse(firstBytes).sha256, predictionHash(happy.runRoot))
      assert.deepEqual(fs.readdirSync(path.dirname(firstFile)).filter(name => /^\d{4}\.json$/.test(name)).sort(), ['0001.json'])
    })
    for (const [name, override, options] of [
      ['not-found', { found: false }], ['no-anchors', { anchors_count: 0 }],
      ['data-unavailable', { data: 'unavailable' }], ['licence-restricted', { licence: 'restricted' }],
      ['stock-incompatible', { stock_environment: false }],
      ['incomplete-baseline', {}, { incompleteBaseline: true }],
    ]) {
      const run = await runCase(name, { ...INTAKE, ...override }, options)
      checkStatuses(name, run, 'intake')
      check(`${name}: no downstream scientific agent calls or seal`, () => {
        assert.ok(run.calls.every(row => row.label === 'intake' || /takeaway/i.test(row.label)))
        assert.ok(!fs.existsSync(path.join(run.runRoot, 'control', 'seals', '0001.json')))
      })
    }
    const invalidRoot = path.join(parent, 'invalid-predictions')
    writeJSON(path.join(invalidRoot, 'agent', 'PREDICTIONS.json'), { ...PREDICTIONS, repetitions: 3 })
    const invalid = await runCase('invalid-predictions', INTAKE, { runRoot: invalidRoot, preserve: true })
    checkStatuses('invalid-predictions', invalid, 'seal')
    check('invalid-predictions: seal called; repetitions 3 rejected without a seal file', () => {
      assert.equal(invalid.calls.filter(row => row.label === 'seal').length, 1)
      assert.equal(readJSON(path.join(invalidRoot, 'agent', 'PREDICTIONS.json')).repetitions, 3)
      const seals = path.join(invalidRoot, 'control', 'seals')
      assert.deepEqual(fs.existsSync(seals) ? fs.readdirSync(seals) : [], [])
    })

    const second = await runCase('second', INTAKE, { runRoot: happy.runRoot })
    checkStatuses('second', second, null)
    check('second: 0002 has correct SHA-256; 0001 bytes unchanged', () => {
      assert.ok(firstBytes, 'first seal missing')
      assert.deepEqual(fs.readFileSync(firstFile), firstBytes)
      assert.equal(readJSON(path.join(happy.runRoot, 'control', 'seals', '0002.json')).sha256, predictionHash(happy.runRoot))
    })

    // A fresh seal is permitted on a rerun. Test rejection only when the rerun
    // reuses an existing seal instead of explicitly issuing a new receipt.
    const predictionsFile = path.join(happy.runRoot, 'agent', 'PREDICTIONS.json')
    writeJSON(predictionsFile, { ...PREDICTIONS, content: `${SENTINEL}:tampered` })
    const tampered = await runCase('tampered', INTAKE, { runRoot: happy.runRoot, preserve: true })
    const newReceipt = path.join(happy.runRoot, 'control', 'seals', '0003.json')
    if (fs.existsSync(newReceipt)) {
      check('tampered: fresh sealing rerun (existing-seal re-verification not exposed)', () => {
        assert.equal(readJSON(newReceipt).sha256, predictionHash(happy.runRoot))
        assert.deepEqual(fs.readFileSync(firstFile), firstBytes)
      })
    } else {
      check('tampered: reused seal detects changed PREDICTIONS.json', () => {
        assert.equal(tampered.stage('seal')?.facts?.seal_verified, false)
        assert.equal(tampered.signature('seal').status, 'FAIL')
        assert.deepEqual(fs.readFileSync(firstFile), firstBytes)
      })
      checkStatuses('tampered', tampered, 'seal')
    }
  } catch (error) {
    failures++
    console.log(`FAIL test harness: ${error.message}`)
  } finally { fs.rmSync(parent, { recursive: true, force: true }) }
  console.log(failures ? `${failures} check(s) FAILED (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
