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
// Evidence from the stubbed profile stage: compute 60%, transfer 30%, serial 10%,
// and a same-GPU concurrency calibration with factor 6 (T1 = 1; factor_n = n * T1 / wall_n).
const PROFILE = {
  stages: [
    { stage: 'kernels', kind: 'compute', wall_s: 6, gpu_s: 6, wall_fraction: 0.6, start_s: 0, mean_gpu_util: 0.125 },
    { stage: 'h2d', kind: 'transfer', wall_s: 3, gpu_s: 1, wall_fraction: 0.3 },
    { stage: 'postprocessing', kind: 'other', wall_s: 1, gpu_s: null, wall_fraction: 0.1 },
  ],
  total_wall_s: 10, timed_fraction: 1, gpu_telemetry: true, gpu_count: 1,
  concurrency: { mps: true, mps_failed: false, single_wall_s: [1, 1, 1],
    batches: [{ n: 2, wall_s: 0.5, all_ok: true, skipped: false, factor: 4 },
      { n: 4, wall_s: 4 / 6, all_ok: true, skipped: false, factor: 6 }], factor: 6 },
}
const PREDICTIONS = {
  outputs_stochastic: false,
  predictions: [
    ['data-parallel over inputs', 1.2, 1.8], ['batching', 1.05, 1.2],
    ['ensembles', 1.1, 1.7], ['pipelining', 1.01, 1.15],
  ].map(([method, low, high]) => ({
    method, expected_speedup_interval: { low, high },
    outcome_vs_compute_points: [1, 2, 4].map(compute_budget => ({
      compute_budget, predicted_outcome: 499500, uncertainty: 'exact integer equality',
    })), content: SENTINEL,
  })),
  infeasible_methods: [{ method: 'multi-GPU', reason: 'Only one GPU; bound is 1, below 1.05.' }],
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
const SEAL_REASON_CODES = [
  'bounds_generation_failed', 'agent_failed', 'predictions_read_failed',
  'predictions_invalid', 'protocol_incomplete', 'compute_points_incomplete',
  'stochastic_equivalence_invalid', 'bounds_coverage_invalid', 'interval_bounds_invalid',
  'intervals_identical', 'seal_write_failed', 'seal_verification_failed',
]
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const readRows = file => fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse)
const writeJSON = (file, value) => {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n')
}

// Install before the workflow imports filesystem functions.
if (process.env.M5_INTAKE_SEAL_FAULT === 'verification') {
  const runRoot = process.env.M5_INTAKE_SEAL_ROOT
  let reads = 0
  const failVerificationRead = file => {
    if (String(file).startsWith(path.join(runRoot, 'control', 'seals') + path.sep) ||
        (String(file) === path.join(runRoot, 'agent', 'PREDICTIONS.json') && ++reads > 1)) {
      throw new Error('synthetic prediction verification read failure')
    }
  }
  const originalRead = fs.readFileSync
  fs.readFileSync = function (file, ...args) {
    failVerificationRead(file)
    return originalRead.call(this, file, ...args)
  }
  const originalAsyncRead = fs.promises.readFile
  fs.promises.readFile = async function (file, ...args) {
    failVerificationRead(file)
    return originalAsyncRead.call(this, file, ...args)
  }
}

// The same module is loaded by WF_STUB. Only intake and seal agents write content;
// neither agent computes hashes or writes operator state. Fault injection below
// simulates unavailable storage and failed verification without reading pipeline code.
module.exports = {
  async run({ title, prompt }) {
    const runRoot = process.env.M5_INTAKE_SEAL_ROOT
    const seals = path.join(runRoot, 'control', 'seals')
    const sealFiles = {}
    if (['seal', 'seal-repair'].includes(title) && fs.existsSync(seals) && fs.statSync(seals).isDirectory()) {
      for (const file of fs.readdirSync(seals)) sealFiles[file] = fs.readFileSync(path.join(seals, file)).toString('base64')
    }
    fs.appendFileSync(process.env.M5_INTAKE_SEAL_CALLS, JSON.stringify({ label: title, prompt, sealFiles }) + '\n')
    let facts = { v: `${title} stub` }
    if (title === 'intake' && process.env.M5_INTAKE_SEAL_RECORDED) {
      // Replay a recorded run's intake files (already copied to a temporary directory).
      facts = JSON.parse(process.env.M5_INTAKE_SEAL_FACTS)
      fs.cpSync(process.env.M5_INTAKE_SEAL_RECORDED, path.join(runRoot, 'agent', 'intake'), { recursive: true })
    } else if (title === 'intake') {
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
        const custom = process.env.M5_INTAKE_SEAL_ANCHORS
        const content = name === 'anchors' && custom
          ? JSON.parse(custom).map(item => ({ ...item, content: SENTINEL, brief }))
          : name === 'anchors'
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
      const fault = process.env.M5_INTAKE_SEAL_FAULT
      if (fault === 'agent') throw new Error('synthetic seal agent failure')
      if (fault === 'write') fs.writeFileSync(path.join(runRoot, 'control', 'seals'), 'blocked')

      if (!process.env.M5_INTAKE_SEAL_PRESERVE) writeJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json'), PREDICTIONS)
      // Deliberately claim verification: the deterministic step must verify it.
      facts = { seal_present: true, seal_verified: true, prediction_count: PREDICTIONS.predictions.length }
    }
    if (title === 'seal-repair' && process.env.M5_INTAKE_SEAL_REPAIR) {
      writeJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json'), JSON.parse(process.env.M5_INTAKE_SEAL_REPAIR))
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
      else {
        const bytes = fs.readFileSync(file)
        assert.ok(!bytes.includes(Buffer.from(SENTINEL)), `content leaked to ${path.relative(operator, file)}`)
        for (const code of SEAL_REASON_CODES) {
          assert.ok(!bytes.includes(Buffer.from(code)), `${code} leaked to ${path.relative(operator, file)}`)
        }
      }
    }
  }
  visit(operator)
}

async function runCase(name, facts = INTAKE, { runRoot = path.join(parent, name), preserve = false, incompleteBaseline = false, profile = PROFILE, sealFault = '', repairPredictions, anchors, recorded } = {}) {
  const control = path.join(runRoot, 'control')
  const brief = path.join(runRoot, 'brief.md')
  fs.mkdirSync(control, { recursive: true })
  fs.writeFileSync(brief, `# Intake fixture\n${SENTINEL}\n`)
  const argsFile = path.join(control, 'args.json')
  writeJSON(argsFile, { run_root: runRoot, brief, tag: 'intake-seal-test', stub: { reproduce: 'PASS', profile: 'PASS', propose: 'PASS', implement: 'PASS', evaluate: 'PASS' } })
  // The profile stage is stubbed, so provide its documented output directly.
  writeJSON(path.join(runRoot, 'agent', 'profile-packet.json'), profile)
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
          M5_RAIDS_LEDGER: path.join(parent, 'raids_used.jsonl'),
          M5_INTAKE_SEAL_FACTS: JSON.stringify(facts), M5_INTAKE_SEAL_BRIEF: brief,
          M5_INTAKE_SEAL_CALLS: callsFile, M5_INTAKE_SEAL_FAULT: sealFault, M5_INTAKE_SEAL_PRESERVE: preserve ? '1' : '',
          M5_INTAKE_SEAL_INCOMPLETE_BASELINE: incompleteBaseline ? '1' : '',
          M5_INTAKE_SEAL_REPAIR: repairPredictions ? JSON.stringify(repairPredictions) : '',
          M5_INTAKE_SEAL_ANCHORS: anchors ? JSON.stringify(anchors) : '', M5_INTAKE_SEAL_RECORDED: recorded || '' },
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
    // `anchored` is computed by the pipeline from anchors.json, never copied from the agent.
    for (const [key, value] of Object.entries(facts)) if (key !== 'anchored') assert.deepEqual(stage('intake')?.facts?.[key], value, key)
  })
  if (!recorded) check(`${name}: intake files contain stub content and supplied brief`, () => {
    for (const file of ['benchmark', 'anchors', 'data', 'baseline', 'EXECUTION']) {
      const value = readJSON(path.join(runRoot, 'agent', 'intake', `${file}.json`))
      if (file === 'baseline' && incompleteBaseline) assert.ok(!Object.hasOwn(value, 'published_configuration'))
      if (file === 'anchors') assert.equal(value.length, anchors ? anchors.length : facts.anchors_count)
      for (const entry of file === 'anchors' ? value : [value]) {
        assert.equal(entry.content, SENTINEL)
        assert.equal(entry.brief, fs.readFileSync(brief, 'utf8'))
      }
    }
    assert.ok(calls.find(row => row.label === 'intake')?.prompt.includes(brief), 'args.brief path not passed to intake')
  })
  check(`${name}: sentinel and seal reason codes absent throughout R/operator`, () => noLeak(runRoot))
  return { runRoot, out, stages, signature, stage, calls }
}

// SCHEMAS.md A/intake/: OPERATOR_TAKEAWAY.md shows `anchored` among the intake gate flags.
// Accept a table column named `anchored` (read from the intake row) or an inline flag.
function takeawayAnchored(runRoot) {
  const text = fs.readFileSync(path.join(runRoot, 'operator', 'OPERATOR_TAKEAWAY.md'), 'utf8')
  const cells = line => line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim().replace(/[`*]/g, ''))
  const blocks = []
  let block = []
  for (const line of text.split('\n')) {
    if (line.trim().startsWith('|')) block.push(line)
    else if (block.length) { blocks.push(block); block = [] }
  }
  if (block.length) blocks.push(block)
  for (const table of blocks) {
    const column = cells(table[0]).indexOf('anchored')
    if (column < 0) continue
    const row = table.slice(1).map(cells).find(row => row.includes('intake'))
    if (row) return row[column]
  }
  const inline = /\banchored\b\W{0,4}(true|false|null)\b/.exec(text)
  return inline ? inline[1] : undefined
}
function anchoredChecks(name, run, expected) {
  check(`${name}: intake emits anchored=${expected}`, () => {
    const facts = run.stage('intake')?.facts
    assert.ok(facts && Object.hasOwn(facts, 'anchored'), 'executed intake stage must emit anchored')
    assert.equal(facts.anchored, expected)
  })
  check(`${name}: OPERATOR_TAKEAWAY.md shows anchored among intake gate flags`, () => {
    assert.equal(takeawayAnchored(run.runRoot), String(expected))
  })
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

// Public recorded run (OpenMM). Its recorded intake must still fail the new gate, and
// it is unanchored. Files are copied to a temporary directory; experiments/ is read only.
const EXPERIMENTS = path.resolve(ROOT, '..', '..', 'experiments')
function recordedRun(relative) {
  const run = path.join(EXPERIMENTS, relative)
  const pick = candidates => candidates.map(name => path.join(run, name)).find(file => fs.existsSync(file))
  return {
    run,
    intake: pick(['agent/intake', 'A/intake']),
    signatures: pick(['operator/signatures.jsonl', 'S/signatures.jsonl']),
  }
}
async function recordedIntakeRegression() {
  const name = 'recorded-blind-openmm-run1'
  const source = recordedRun(path.join('blind-openmm', 'run1'))
  let facts, recorded
  check(`${name}: recorded intake files and intake facts available`, () => {
    assert.ok(source.intake, `no recorded intake directory under ${source.run}`)
    assert.ok(source.signatures, `no recorded signatures under ${source.run}`)
    const rows = readRows(source.signatures).filter(row => (row.signature || row).stage === 'intake' && row.facts)
    assert.ok(rows.length, 'no recorded intake facts')
    const { tokens_known, gpu_busy_known, anchored, ...agentFacts } = rows.at(-1).facts
    facts = agentFacts
    recorded = path.join(parent, `${name}-fixture`)
    fs.cpSync(source.intake, recorded, { recursive: true })
  })
  if (!facts) return
  const run = await runCase(name, facts, { recorded })
  checkStatuses(name, run, 'intake')
  anchoredChecks(name, run, false)
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
      assert.equal(facts?.prediction_count, PREDICTIONS.predictions.length)
    })
    check('happy: bounds computed from profile; feasible coverage and intervals conform', () => {
      assert.deepEqual(readJSON(path.join(happy.runRoot, 'agent', 'profile-packet.json')), PROFILE)
      const boundsFile = path.join(happy.runRoot, 'agent', 'bounds.json')
      const bounds = readJSON(boundsFile)
      // Whole-workload: p = 1, k = min(cap, factor 6); pipelining Amdahl k = 2; multi-GPU Amdahl / k.
      const expected = {
        'data-parallel over inputs': [1, 6], batching: [1, 4],
        'multi-GPU': [0.6, 1], ensembles: [1, 6], pipelining: [0.3, 2],
      }
      assert.deepEqual(Object.keys(bounds).sort(), Object.keys(expected).sort())
      for (const [method, [p, k]] of Object.entries(expected)) {
        const bound = 1 / ((1 - p) + p / k) / (method === 'multi-GPU' ? k : 1)
        assert.equal(bounds[method].p, p, method)
        assert.equal(bounds[method].k, k, method)
        assert.ok(Math.abs(bounds[method].bound - bound) < 1e-12, method)
        assert.equal(bounds[method].feasible, bound >= 1.05, method)
      }
      assert.deepEqual(PREDICTIONS.predictions.map(row => row.method).sort(),
        Object.keys(bounds).filter(method => bounds[method].feasible).sort())
      assert.deepEqual(PREDICTIONS.infeasible_methods.map(row => row.method), ['multi-GPU'])
      for (const { method, expected_speedup_interval: { low, high } } of PREDICTIONS.predictions) {
        assert.ok(low > 0 && low <= high && high <= bounds[method].bound, method)
        assert.ok(high - low <= bounds[method].bound - 1, method)
      }
      const prompt = happy.calls.find(row => row.label === 'seal')?.prompt
      assert.ok(prompt.includes(boundsFile), 'bounds path missing from seal prompt')
      assert.ok(prompt.includes('multi-GPU') && prompt.includes('feasible'), 'bounds content missing from seal prompt')
    })
    check('happy: seal prompt contains documented stochastic and deterministic skeletons', () => {
      const prompt = happy.calls.find(row => row.label === 'seal').prompt
      // Parse complete JSON objects from the public prompt, independently of the generator.
      const examples = []
      for (let start = 0; start < prompt.length; start++) {
        if (prompt[start] !== '{') continue
        for (let end = start + 1; end < prompt.length; end++) {
          if (prompt[end] !== '}') continue
          try {
            const value = JSON.parse(prompt.slice(start, end + 1))
            if (Object.hasOwn(value, 'outputs_stochastic')) examples.push(value)
            start = end
            break
          } catch {}
        }
      }
      for (const stochastic of [false, true]) {
        const example = examples.find(value => value.outputs_stochastic === stochastic)
        assert.ok(example, `missing ${stochastic ? 'stochastic' : 'deterministic'} JSON skeleton`)
        assert.deepEqual(example.evaluation_inputs, { ids: ['held-out-1'] })
        assert.deepEqual(example.sample_sizes, { inputs: 1, seeds: stochastic ? 6 : 1 })
        if (stochastic) {
          assert.deepEqual(example.paired_seed_tests, { kind: 'paired_median', seeds: [0, 1, 2, 3, 4, 5] })
        } else {
          assert.equal(example.paired_seed_tests.kind, 'deterministic')
          assert.equal(typeof example.paired_seed_tests.justification, 'string')
          assert.ok(example.paired_seed_tests.justification.trim())
        }
        for (const kind of ['performance', 'equivalence']) {
          assert.deepEqual(example.confidence_rule[kind], { kind: 'paired_median', confidence: 0.95 })
        }
        assert.ok(example.equivalence_metrics.length > 0)
        for (const metric of example.equivalence_metrics) {
          assert.equal(typeof metric.name, 'string')
          assert.ok(metric.name.trim())
          assert.equal(typeof metric.source, 'string')
          assert.ok(metric.source.trim())
          assert.deepEqual(Object.keys(metric.tolerance), ['abs'])
          assert.equal(typeof metric.tolerance.abs, 'number')
          assert.ok(Number.isFinite(metric.tolerance.abs))
          assert.ok(stochastic ? metric.tolerance.abs > 0 : metric.tolerance.abs === 0)
        }
      }
    })
    const firstFile = path.join(happy.runRoot, 'control', 'seals', '0001.json')
    let firstBytes
    check('happy: 0001 contains independently recomputed canonical SHA-256', () => {
      firstBytes = fs.readFileSync(firstFile)
      assert.deepEqual(readJSON(path.join(happy.runRoot, 'agent', 'PREDICTIONS.json')), PREDICTIONS)
      assert.equal(JSON.parse(firstBytes).sha256, predictionHash(happy.runRoot))
      assert.deepEqual(fs.readdirSync(path.dirname(firstFile)).filter(name => /^\d{4}\.json$/.test(name)).sort(), ['0001.json'])
    })
    anchoredChecks('happy', happy, true)
    // SCHEMAS.md A/intake/: "Missing executable inputs and unverified permissions block;
    // missing published tolerances do not." An empty or reference-only anchors.json passes.
    const reference = (id, extra = {}) => ({ id, quantity: 'sum', source: 'https://example.org/reference-1',
      published_value: 499500, tolerance: null, ...extra })
    const thresholdAnchor = { id: 'threshold', quantity: 'sum', source: 'https://example.org/reference-1',
      published_value: 1000, comparison: '>=', tolerance: null }
    for (const [name, anchors, expected] of [
      ['empty-anchors', [], false],
      ['reference-only', [reference('ref-default'), reference('ref-explicit', { comparison: '==',
        uncertainty: { kind: 'standard_error', value: 12.5 } }), reference('ref-null-uncertainty', { uncertainty: null })], false],
      ['inequality-null-tolerance-anchor', [thresholdAnchor, reference('ref')], true],
    ]) {
      const run = await runCase(name, { ...INTAKE, anchors_count: anchors.length }, { anchors })
      checkStatuses(name, run, null)
      anchoredChecks(name, run, expected)
    }
    // The pipeline computes `anchored`; an agent claim cannot override anchors.json.
    const claimed = await runCase('claimed-anchored', { ...INTAKE, anchors_count: 0, anchored: true }, { anchors: [] })
    checkStatuses('claimed-anchored', claimed, null)
    anchoredChecks('claimed-anchored', claimed, false)
    for (const [name, override, options, anchored] of [
      ['not-found', { found: false }, {}, true],
      ['data-unavailable', { data: 'unavailable' }, {}, true], ['licence-restricted', { licence: 'restricted' }, {}, true],
      ['stock-incompatible', { stock_environment: false }, {}, true],
      ['incomplete-baseline', {}, { incompleteBaseline: true }],
      // Unanchored intakes still fail on every other gate condition.
      ['empty-not-found', { found: false, anchors_count: 0 }, { anchors: [] }, false],
      ['empty-data-unavailable', { data: 'unavailable', anchors_count: 0 }, { anchors: [] }, false],
      ['empty-licence-unknown', { licence: 'unknown', anchors_count: 0 }, { anchors: [] }, false],
      ['empty-stock-incompatible', { stock_environment: false, anchors_count: 0 }, { anchors: [] }, false],
      ['reference-licence-restricted', { licence: 'restricted', anchors_count: 1 }, { anchors: [reference('ref')] }, false],
      // Invalid anchors.json: the files are incomplete, so the gate fails and anchored is null.
      ['anchors-count-mismatch', { anchors_count: 2 }, { anchors: [reference('ref')] }, null],
      ['invalid-uncertainty', { anchors_count: 1 }, { anchors: [reference('ref', { uncertainty: { kind: 'variance', value: 1 } })] }, null],
      ['invalid-tolerance', { anchors_count: 1 }, { anchors: [reference('ref', { tolerance: { abs: -1 } })] }, null],
    ]) {
      const run = await runCase(name, { ...INTAKE, ...override }, options)
      checkStatuses(name, run, 'intake')
      check(`${name}: no downstream scientific agent calls or seal`, () => {
        assert.ok(run.calls.every(row => row.label === 'intake' || /takeaway/i.test(row.label)))
        assert.ok(!fs.existsSync(path.join(run.runRoot, 'control', 'seals', '0001.json')))
      })
      if (anchored === null) check(`${name}: anchored is null when anchors.json is invalid`, () => {
        assert.equal(run.stage('intake')?.facts?.anchored, null)
      })
      else if (anchored !== undefined) anchoredChecks(name, run, anchored)
    }
    await recordedIntakeRegression()
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

    for (const [name, mutate] of [
      ['above-bound', value => {
        value.predictions[0].expected_speedup_interval = { low: 100, high: 100 }
      }],
      ['identical-intervals', value => {
        for (const row of value.predictions) row.expected_speedup_interval = { low: 1.01, high: 1.1 }
      }],
      ['infeasible-predicted', value => {
        value.predictions.push({ ...value.predictions[0], method: 'multi-GPU',
          expected_speedup_interval: { low: 1, high: 1 } })
        value.infeasible_methods = []
      }],
      ['infeasible-unlisted', value => { value.infeasible_methods = [] }],
    ]) {
      const runRoot = path.join(parent, name)
      const value = JSON.parse(JSON.stringify(PREDICTIONS))
      mutate(value)
      writeJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json'), value)
      const run = await runCase(name, INTAKE, { runRoot, preserve: true })
      checkStatuses(name, run, 'seal')
      check(`${name}: numeric failure; submitted count retained; no seal`, () => {
        assert.equal(run.calls.filter(row => row.label === 'seal').length, 1)
        assert.equal(run.signature('seal').error_class, 'numeric')
        assert.equal(run.signature('seal').exit_code, 2)
        assert.equal(run.stage('seal')?.facts?.seal_verified, false)
        assert.equal(run.stage('seal')?.facts?.prediction_count, value.predictions.length)
        assert.deepEqual(readJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json')), value)
        const seals = path.join(runRoot, 'control', 'seals')
        assert.deepEqual(fs.existsSync(seals) ? fs.readdirSync(seals) : [], [])
      })
    }

    for (const statistical of [false, true]) {
      const name = statistical ? 'stochastic-statistical' : 'stochastic-exact'
      const runRoot = path.join(parent, name)
      const value = JSON.parse(JSON.stringify(PREDICTIONS))
      value.outputs_stochastic = true
      // Both cases use paired seeds; only the equivalence rule differs.
      value.paired_seed_tests = { kind: 'paired_median', seeds: [0, 1, 2, 3, 4, 5] }
      value.confidence_rule = {
        equivalence: { kind: 'paired_median', confidence: 0.95 },
        performance: { kind: 'paired_median', confidence: 0.95 },
      }
      value.equivalence_metrics = [{ name: 'sum', source: 'records.metrics.sum',
        tolerance: { abs: statistical ? 0.1 : 0 } }]
      writeJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json'), value)
      const run = await runCase(name, INTAKE, { runRoot, preserve: true })
      checkStatuses(name, run, statistical ? null : 'seal')
      check(`${name}: deterministic verification enforces stochastic equivalence`, () => {
        assert.equal(run.calls.filter(row => row.label === 'seal').length, 1)
        assert.equal(run.stage('seal')?.facts?.seal_verified, statistical)
        const receipt = path.join(runRoot, 'control', 'seals', '0001.json')
        assert.equal(fs.existsSync(receipt), statistical)
        if (statistical) assert.equal(readJSON(receipt).sha256, predictionHash(runRoot))
        else {
          assert.equal(run.signature('seal').error_class, 'numeric')
          assert.equal(run.signature('seal').exit_code, 2)
        }
      })
    }

    for (const repaired of [true, false]) {
      const name = repaired ? 'repair-stochastic-valid' : 'repair-stochastic-invalid'
      const runRoot = path.join(parent, name)
      // Establish a real prior seal, then require repair without changing its files.
      const prior = await runCase(`${name}-prior`, INTAKE, { runRoot })
      checkStatuses(`${name}-prior`, prior, null)
      const seals = path.join(runRoot, 'control', 'seals')
      const snapshot = () => Object.fromEntries(fs.readdirSync(seals).sort()
        .map(file => [file, fs.readFileSync(path.join(seals, file)).toString('base64')]))
      const original = snapshot()
      const invalid = JSON.parse(JSON.stringify(PREDICTIONS))
      invalid.outputs_stochastic = true
      invalid.paired_seed_tests = { kind: 'paired_median', seeds: [0, 1, 2, 3, 4, 5] }
      invalid.evaluation_inputs = { ids: ['PRIVATE_INPUT_REPAIR_73'] }
      invalid.sample_sizes = { inputs: 1, seeds: 6 }
      invalid.confidence_rule = {
        performance: { kind: 'paired_median', confidence: 0.95 },
        equivalence: { kind: 'paired_median', confidence: 0.95 },
      }
      invalid.equivalence_metrics = [{ name: 'PRIVATE_METRIC_REPAIR_73',
        source: 'PRIVATE_SOURCE_REPAIR_73', tolerance: { abs: 0 } }]
      const replacement = JSON.parse(JSON.stringify(invalid))
      if (repaired) replacement.equivalence_metrics[0].tolerance.abs = 0.1
      else replacement.equivalence_metrics[0].tolerance = { rel: 0.1 }
      writeJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json'), invalid)
      const run = await runCase(name, INTAKE, { runRoot, preserve: true, repairPredictions: replacement })
      checkStatuses(name, run, repaired ? null : 'seal')
      check(`${name}: exactly one initial call and one repair, before seal allocation`, () => {
        const calls = run.calls.filter(row => ['seal', 'seal-repair'].includes(row.label))
        assert.deepEqual(calls.map(row => row.label), ['seal', 'seal-repair'])
        for (const call of calls) assert.deepEqual(call.sealFiles, original)
        assert.deepEqual(readJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json')), replacement)
      })
      check(`${name}: repair feedback includes reason and field path without file values`, () => {
        const prompt = run.calls.find(row => row.label === 'seal-repair').prompt
        assert.ok(prompt.includes('stochastic_equivalence_invalid'), 'missing reason code')
        assert.match(prompt, /equivalence_metrics(?:\[0\]|\.0).*tolerance/, 'missing failing field path')
        for (const value of [SENTINEL, 'PRIVATE_INPUT_REPAIR_73', 'PRIVATE_METRIC_REPAIR_73',
          'PRIVATE_SOURCE_REPAIR_73', '499500', PREDICTIONS.infeasible_methods[0].reason]) {
          assert.ok(!prompt.includes(value), `file value leaked: ${value}`)
        }
        assert.ok(!prompt.includes(JSON.stringify(PROFILE)), 'profile evidence leaked')
        assert.ok(!prompt.includes('k_derivation'), 'bounds leaked')
      })
      check(`${name}: immutable numbering; only successful repair creates 0002`, () => {
        const current = snapshot()
        for (const [file, bytes] of Object.entries(original)) assert.equal(current[file], bytes, file)
        assert.deepEqual(Object.keys(current).filter(file => /^\d{4}\.json$/.test(file)),
          repaired ? ['0001.json', '0002.json'] : ['0001.json'])
        assert.equal(run.stage('seal').facts.seal_verified, repaired)
        assert.deepEqual(readJSON(path.join(runRoot, 'control', 'stages', 'seal.json')).reason_codes,
          repaired ? [] : ['stochastic_equivalence_invalid'])
        if (repaired) assert.equal(readJSON(path.join(seals, '0002.json')).sha256, predictionHash(runRoot))
        else {
          assert.deepEqual(current, original)
          assert.equal(run.signature('seal').error_class, 'numeric')
          assert.equal(run.signature('seal').exit_code, 2)
        }
      })
    }

    // Without a concurrency calibration, whole-workload bounds are 1, and multi-GPU
    // per GPU-second never exceeds 1: only pipelining (bound 1/0.85) remains feasible.
    // Its lone interval must be exempt from identical checks.
    const singleProfile = JSON.parse(JSON.stringify(PROFILE))
    delete singleProfile.concurrency
    singleProfile.gpu_count = 2
    const singlePredictions = JSON.parse(JSON.stringify(PREDICTIONS))
    singlePredictions.predictions = [{ ...singlePredictions.predictions[0], method: 'pipelining',
      expected_speedup_interval: { low: 1.05, high: 1.15 } }]
    singlePredictions.infeasible_methods = ['data-parallel over inputs', 'batching', 'multi-GPU', 'ensembles']
      .map(method => ({ method, reason: 'Bound is at most 1.' }))
    // No calibration and no transfer time: nothing is feasible.
    const noneProfile = JSON.parse(JSON.stringify(singleProfile))
    noneProfile.gpu_count = 1
    noneProfile.stages[1].wall_s = 0
    noneProfile.stages[2].wall_s = 4
    const singleRoot = path.join(parent, 'single-feasible')
    writeJSON(path.join(singleRoot, 'agent', 'PREDICTIONS.json'), singlePredictions)
    const single = await runCase('single-feasible', INTAKE, { runRoot: singleRoot, preserve: true, profile: singleProfile })
    checkStatuses('single-feasible', single, null)
    check('single-feasible: one valid interval seals with no reason codes', () => {
      const bounds = readJSON(path.join(singleRoot, 'agent', 'bounds.json'))
      assert.deepEqual(Object.keys(bounds).filter(method => bounds[method].feasible), ['pipelining'])
      assert.equal(single.stage('seal').facts.seal_verified, true)
      assert.equal(single.stage('seal').facts.prediction_count, 1)
      assert.deepEqual(readJSON(path.join(singleRoot, 'control', 'stages', 'seal.json')).reason_codes, [])
      assert.equal(readJSON(path.join(singleRoot, 'control', 'seals', '0001.json')).sha256, predictionHash(singleRoot))
    })

    // SCHEMAS.md A/PREDICTIONS.json: "An empty feasible menu may be sealed as a negative result: a verified
    // seal with zero predictions (every menu method listed in `infeasible_methods`) PASSes the seal stage with
    // `prediction_count=0` and `reason_codes: []`." Verified negative results do not trigger repair.
    for (const [name, profile] of [['zero-predictions-uncalibrated', noneProfile],
      ['zero-predictions-calibrated', (() => {
        // Measured calibration with factor 1.02 (< 1.05): whole-workload bounds 1.02, still infeasible.
        const value = JSON.parse(JSON.stringify(noneProfile))
        value.concurrency = { mps: false, mps_failed: false, single_wall_s: [1, 1, 1],
          batches: [{ n: 2, wall_s: 2 / 1.02, all_ok: true, skipped: false, factor: 1.02 },
            { n: 4, wall_s: 4, all_ok: true, skipped: false, factor: 1 }], factor: 1.02 }
        return value
      })()]]) {
      const runRoot = path.join(parent, name)
      const value = JSON.parse(JSON.stringify(PREDICTIONS))
      value.predictions = []
      value.infeasible_methods = ['data-parallel over inputs', 'batching', 'multi-GPU', 'ensembles', 'pipelining']
        .map(method => ({ method, reason: 'Bound is below 1.05.' }))
      writeJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json'), value)
      const run = await runCase(name, INTAKE, { runRoot, preserve: true, profile })
      checkStatuses(name, run, null)
      check(`${name}: verified zero-prediction seal PASSes with prediction_count 0 and no reason codes`, () => {
        const bounds = readJSON(path.join(runRoot, 'agent', 'bounds.json'))
        assert.deepEqual(Object.keys(bounds).filter(method => bounds[method].feasible), [])
        const seal = run.signature('seal')
        assert.equal(seal.status, 'PASS')
        assert.equal(seal.exit_code, 0)
        assert.equal(run.stage('seal').facts.seal_present, true)
        assert.equal(run.stage('seal').facts.seal_verified, true)
        assert.equal(run.stage('seal').facts.prediction_count, 0)
        assert.deepEqual(readJSON(path.join(runRoot, 'control', 'stages', 'seal.json')).reason_codes, [])
        assert.equal(readJSON(path.join(runRoot, 'control', 'seals', '0001.json')).sha256, predictionHash(runRoot))
        assert.deepEqual(readJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json')), value)
      })
      check(`${name}: verified negative result triggers no repair`, () => {
        assert.deepEqual(run.calls.filter(row => ['seal', 'seal-repair'].includes(row.label)).map(row => row.label), ['seal'])
      })
    }
    check('no_feasible_methods is no longer a documented seal code', () => {
      const schema = fs.readFileSync(path.join(ROOT, 'm5', 'SCHEMAS.md'), 'utf8')
      const table = schema.slice(schema.indexOf('  | Code | Failed check or operation |'), schema.indexOf('- Seal: C/seals/'))
      assert.ok(!table.includes('no_feasible_methods'))
    })

    const reasonCases = [
      ['bounds_generation_failed', null, { profile: {} }],
      ['agent_failed', null, { sealFault: 'agent' }],
      ['predictions_read_failed', null, {}, '{invalid JSON'],
      ['predictions_invalid', value => { value.predictions = {} }],
      ['protocol_incomplete', value => { value.repetitions = 3 }],
      ['compute_points_incomplete', value => { value.predictions[0].outcome_vs_compute_points.pop() }],
      ['stochastic_equivalence_invalid', value => { value.outputs_stochastic = true }],
      ['bounds_coverage_invalid', value => { value.infeasible_methods = [] }],
      ['interval_bounds_invalid', value => {
        value.predictions[0].expected_speedup_interval = { low: 100, high: 100 }
      }],
      ['intervals_identical', value => {
        for (const row of value.predictions) row.expected_speedup_interval = { low: 1.01, high: 1.1 }
      }],
      ['seal_write_failed', null, { sealFault: 'write' }],
      ['seal_verification_failed', null, { sealFault: 'verification' }],
    ]
    check('reason cases cover every documented seal code', () => {
      const schema = fs.readFileSync(path.join(ROOT, 'm5', 'SCHEMAS.md'), 'utf8')
      const table = schema.slice(schema.indexOf('  | Code | Failed check or operation |'), schema.indexOf('- Seal: C/seals/'))
      const documented = [...table.matchAll(/\| `([^`]+)` \|/g)].map(match => match[1])
      assert.deepEqual(SEAL_REASON_CODES, documented)
      assert.deepEqual(reasonCases.map(([code]) => code), documented)
    })
    for (const [code, mutate, options = {}, raw] of reasonCases) {
      const runRoot = path.join(parent, `reason-${code}`)
      const value = JSON.parse(JSON.stringify(PREDICTIONS))
      if (mutate) mutate(value)
      const predictionsFile = path.join(runRoot, 'agent', 'PREDICTIONS.json')
      writeJSON(predictionsFile, value)
      if (raw) fs.writeFileSync(predictionsFile, raw)
      const run = await runCase(`reason-${code}`, INTAKE, { ...options, runRoot, preserve: true })
      checkStatuses(code, run, 'seal')
      check(`${code}: exact first-failure code in stage receipt`, () => {
        const receipt = readJSON(path.join(runRoot, 'control', 'stages', 'seal.json'))
        assert.deepEqual(receipt.reason_codes, [code])
        assert.equal(run.signature('seal').error_class, 'numeric')
        assert.equal(run.signature('seal').exit_code, 2)
      })
    }

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
