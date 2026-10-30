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
  // Small enough that the protocol fits any evaluate budget used here with a wide margin.
  baseline_invocation_s: { seconds: 0.01, source: 'fixture: one baseline equivalence invocation, 0.01 s' },
  content: SENTINEL,
}
const SEAL_REASON_CODES = [
  'bounds_generation_failed', 'agent_failed', 'predictions_read_failed',
  'predictions_invalid', 'protocol_incomplete', 'compute_points_incomplete',
  'stochastic_equivalence_invalid', 'protocol_cost', 'bounds_coverage_invalid', 'interval_bounds_invalid',
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
      if (process.env.M5_INTAKE_SEAL_INCOMPLETE_BASELINE) delete fixtures.baseline[process.env.M5_INTAKE_SEAL_INCOMPLETE_BASELINE]
      if (process.env.M5_INTAKE_SEAL_BUILD) fixtures.baseline.build_commands = JSON.parse(process.env.M5_INTAKE_SEAL_BUILD)
      if (process.env.M5_INTAKE_SEAL_BASELINE_PATCH) {
        const { set = {}, drop = [] } = JSON.parse(process.env.M5_INTAKE_SEAL_BASELINE_PATCH)
        Object.assign(fixtures.baseline, set)
        for (const key of drop) delete fixtures.baseline[key]
      }
      if (process.env.M5_INTAKE_SEAL_EXEC_BUDGETS) fixtures.EXECUTION.stage_budgets_s = JSON.parse(process.env.M5_INTAKE_SEAL_EXEC_BUDGETS)
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

async function runCase(name, facts = INTAKE, { runRoot = path.join(parent, name), preserve = false, incompleteBaseline = false, profile = PROFILE, sealFault = '', repairPredictions, anchors, recorded, noBrief = false, buildCommands, baselinePatch, argsBudgets, executionBudgets } = {}) {
  // `incompleteBaseline`: true drops published_configuration; a string drops that baseline.json key.
  const droppedKey = incompleteBaseline === true ? 'published_configuration' : incompleteBaseline || ''
  const control = path.join(runRoot, 'control')
  const brief = path.join(runRoot, 'brief.md')
  fs.mkdirSync(control, { recursive: true })
  fs.writeFileSync(brief, `# Intake fixture\n${SENTINEL}\n`)
  const argsFile = path.join(control, 'args.json')
  writeJSON(argsFile, { run_root: runRoot, ...(noBrief ? {} : { brief }), tag: 'intake-seal-test', stub: { reproduce: 'PASS', profile: 'PASS', propose: 'PASS', implement: 'PASS', evaluate: 'PASS' },
    ...(argsBudgets ? { stage_budgets_s: argsBudgets } : {}) })
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
          M5_INTAKE_SEAL_INCOMPLETE_BASELINE: droppedKey,
          M5_INTAKE_SEAL_BUILD: buildCommands ? JSON.stringify(buildCommands) : '',
          M5_INTAKE_SEAL_BASELINE_PATCH: baselinePatch ? JSON.stringify(baselinePatch) : '',
          M5_INTAKE_SEAL_EXEC_BUDGETS: executionBudgets ? JSON.stringify(executionBudgets) : '',
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
      if (file === 'baseline' && droppedKey) assert.ok(!Object.hasOwn(value, droppedKey))
      if (file === 'anchors') assert.equal(value.length, anchors ? anchors.length : facts.anchors_count)
      for (const entry of file === 'anchors' ? value : [value]) {
        assert.equal(entry.content, SENTINEL)
        assert.equal(entry.brief, fs.readFileSync(brief, 'utf8'))
      }
    }
    if (!noBrief) assert.ok(calls.find(row => row.label === 'intake')?.prompt.includes(brief), 'args.brief path not passed to intake')
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
  blockerChecks(name, run, ['licence', 'data_unavailable'])
}

// SCHEMAS.md A/intake/ baseline.json: "`build_commands` lists every command that builds or installs the
// baseline, including package-manager installs of released binaries, and is never empty. The intake
// prompt states both." Both statements must sit near a mention of build_commands.
function buildCommandsPromptChecks(name, run) {
  check(`${name}: intake prompt states build_commands includes package-manager installs of released binaries and is never empty`, () => {
    const prompt = run.calls.find(row => row.label === 'intake')?.prompt
    assert.ok(prompt, 'no intake prompt recorded')
    const windows = [...prompt.matchAll(/build_commands/g)].map(match => prompt.slice(Math.max(0, match.index - 400), match.index + 600))
    assert.ok(windows.length, 'prompt never mentions build_commands')
    const installs = text => /package[- ]manager/i.test(text) && /released\s+binar/i.test(text)
    const nonEmpty = text => /never\s+(?:be\s+)?empty|non-?empty|must\s+not\s+be\s+empty|cannot\s+be\s+empty|may\s+not\s+be\s+empty|at\s+least\s+one/i.test(text)
    assert.ok(windows.some(installs), 'prompt does not state that build_commands includes package-manager installs of released binaries')
    assert.ok(windows.some(nonEmpty), 'prompt does not state that build_commands is never empty')
  })
}

// SCHEMAS.md A/intake/ baseline.json (U39): "The intake prompt names every key the completeness check reads exactly
// as the check reads it, as a JSON key: in baseline.json `repo`, `build_commands`, `run_commands`,
// `published_configuration`, and `commit` or `pin` ...; in EXECUTION.json `representative_scale`, `inputs`, `outputs`
// and `timing_scope`. It states that the check reads only these key names, so an equivalent value under another key
// does not count."
const COMPLETENESS_KEYS = ['repo', 'build_commands', 'run_commands', 'published_configuration', 'commit', 'pin',
  'representative_scale', 'inputs', 'outputs', 'timing_scope']
// A JSON key token: the bare name delimited by matching quotes or backticks, e.g. "pin" or `pin`
// (so "immutable pin" or `immutable_pin` do not count).
const keyToken = key => new RegExp(`(["'\`])${key}\\1`)
function completenessKeyPromptChecks(name, run) {
  const prompt = () => {
    const value = run.calls.find(row => row.label === 'intake')?.prompt
    assert.ok(value, 'no intake prompt recorded')
    return value
  }
  check(`${name}: intake prompt names each completeness key as a JSON key token`, () => {
    const text = prompt()
    const missing = COMPLETENESS_KEYS.filter(key => !keyToken(key).test(text))
    assert.deepEqual(missing, [], `key names not given as JSON keys: ${missing.join(', ')}`)
  })
  check(`${name}: intake prompt states that only these key names count, not an equivalent value under another key`, () => {
    const other = /\b(?:another|other|different|alternative|renamed|equivalent)\b[^.\n]{0,60}\bkeys?\b|\bonly\b[^.\n]{0,40}\bkey\s*names?\b/i
    const negation = /\b(?:does\s+not|do\s+not|doesn't|don't|never|not|no)\b[^.\n]{0,40}\b(?:count|satisf|qualif|accept|recogni|read)|\bignored\b|\bonly\b/i
    const text = prompt()
    const windows = windowsAround(text, other, 300, 300)
    const keyLines = text.split('\n').filter(line => /\bkey/i.test(line)).map(line => line.slice(0, 400))
    assert.ok(windows.length, `prompt never refers to other key names; lines mentioning "key": ${JSON.stringify(keyLines)}`)
    // The statement must be about these keys: it names them or the two files they belong to.
    const aboutKeys = window => /baseline\.json|EXECUTION\.json/.test(window) || COMPLETENESS_KEYS.some(key => keyToken(key).test(window))
    assert.ok(windows.some(window => negation.test(window) && aboutKeys(window)),
      `no statement, about these keys, that only these key names count; lines mentioning "key": ${JSON.stringify(keyLines)}`)
  })
}

// The completeness check is unchanged: `commit` or `pin` (non-empty); the identifier under another key does not count.
async function commitOrPinChecks() {
  const PIN = 'v8.1.1 release tarball sha256:00ff'
  for (const [name, baselinePatch, passes] of [
    ['completeness-commit-null-pin', { set: { commit: null, pin: PIN } }, true],
    ['completeness-commit-no-pin', { drop: ['pin'] }, true],
    ['completeness-commit-null-immutable-pin', { set: { commit: null, immutable_pin: PIN }, drop: ['pin'] }, false],
  ]) {
    const run = await runCase(name, INTAKE, { baselinePatch })
    check(`${name}: fixture baseline.json has the intended commit/pin keys`, () => {
      const baseline = readJSON(path.join(run.runRoot, 'agent', 'intake', 'baseline.json'))
      for (const [key, value] of Object.entries(baselinePatch.set || {})) assert.deepEqual(baseline[key], value, key)
      for (const key of baselinePatch.drop || []) assert.ok(!Object.hasOwn(baseline, key), key)
    })
    checkStatuses(name, run, passes ? null : 'intake')
    check(`${name}: intake ${passes ? 'PASS' : 'FAIL'}`, () => {
      assert.equal(run.signature('intake').status, passes ? 'PASS' : 'FAIL')
    })
    if (!passes) blockerChecks(name, run, ['none'])
  }
}

// Public recorded run blind-openmm run2: its baseline.json holds `commit: null` and the identifier under
// `immutable_pin`. Replayed with the run's reply facts, intake FAILs with blockers ["none"] and anchored false;
// with only `immutable_pin` renamed to `pin`, intake PASSes. Files are copied; experiments/ is read only.
const RUN2_FACTS = { found: true, anchors_count: 3, data: 'available', licence: 'permitted', stock_environment: null, size: 'unknown' }
async function blindOpenmmRun2Regression() {
  const label = 'recorded-blind-openmm-run2'
  const source = recordedRun(path.join('blind-openmm', 'run2'))
  const asRecorded = path.join(parent, `${label}-as-recorded-fixture`)
  const renamed = path.join(parent, `${label}-pin-fixture`)
  let ready = false
  check(`${label}: recorded intake files available; commit null, identifier under immutable_pin, no pin`, () => {
    assert.ok(source.intake, `no recorded intake directory under ${source.run}`)
    for (const file of ['benchmark', 'anchors', 'data', 'baseline', 'EXECUTION']) {
      assert.ok(fs.existsSync(path.join(source.intake, `${file}.json`)), `missing ${file}.json`)
    }
    fs.cpSync(source.intake, asRecorded, { recursive: true })
    fs.cpSync(source.intake, renamed, { recursive: true })
    const baseline = readJSON(path.join(asRecorded, 'baseline.json'))
    assert.equal(baseline.commit, null)
    assert.ok(!Object.hasOwn(baseline, 'pin'))
    assert.ok(baseline.immutable_pin, 'recorded immutable_pin missing')
    assert.equal(readJSON(path.join(asRecorded, 'anchors.json')).length, RUN2_FACTS.anchors_count)
    // Rename only the key, keeping its value and position.
    const text = fs.readFileSync(path.join(renamed, 'baseline.json'), 'utf8')
    assert.equal(text.split('"immutable_pin":').length, 2, 'expected exactly one immutable_pin key')
    fs.writeFileSync(path.join(renamed, 'baseline.json'), text.replace('"immutable_pin":', '"pin":'))
    const { immutable_pin, ...rest } = baseline
    const { pin, ...renamedRest } = readJSON(path.join(renamed, 'baseline.json'))
    assert.deepEqual(pin, immutable_pin)
    assert.deepEqual(renamedRest, rest)
    ready = true
  })
  check(`${label}: recorded intake reply facts match the regression facts`, () => {
    assert.ok(source.signatures, `no recorded signatures under ${source.run}`)
    const facts = readRows(source.signatures).filter(row => (row.signature || row).stage === 'intake' && row.facts).at(-1)?.facts
    assert.ok(facts, 'no recorded intake facts')
    for (const [key, value] of Object.entries(RUN2_FACTS)) assert.deepEqual(facts[key], value, key)
  })
  if (!ready) return
  {
    const name = `${label}-as-recorded`
    const run = await runCase(name, RUN2_FACTS, { recorded: asRecorded })
    checkStatuses(name, run, 'intake')
    check(`${name}: intake FAILs`, () => assert.equal(run.signature('intake').status, 'FAIL'))
    blockerChecks(name, run, ['none'])
    anchoredChecks(name, run, false)
  }
  {
    const name = `${label}-pin`
    const run = await runCase(name, RUN2_FACTS, { recorded: renamed })
    check(`${name}: intake PASSes with immutable_pin renamed to pin`, () => {
      const stderr = fs.readFileSync(path.join(run.runRoot, `stderr-${name}.log`), 'utf8')
      assert.equal(run.signature('intake').status, 'PASS', `${JSON.stringify(run.signature('intake'))}; stderr: ${stderr.slice(-1500)}`)
    })
    check(`${name}: run does not stop at intake`, () => {
      assert.notEqual(readJSON(path.join(run.out, 'result.json')).stopped_at, 'intake')
    })
    blockerChecks(name, run, ['none'])
    anchoredChecks(name, run, false)
  }
}

// Public recorded runs positive-openmm run1 and run2, gated on their intake files alone. The agent facts
// are set to gate-passing values (anchors_count from the recorded anchors.json), so the verdict rests on
// file completeness. Files are copied to a temporary directory; experiments/ is read only.
async function positiveOpenmmRegression(runName, expectPass) {
  const name = `recorded-positive-openmm-${runName}`
  const source = recordedRun(path.join('positive-openmm', runName))
  let recorded, facts
  check(`${name}: recorded intake files available and copied`, () => {
    assert.ok(source.intake, `no recorded intake directory under ${source.run}`)
    recorded = path.join(parent, `${name}-fixture`)
    fs.cpSync(source.intake, recorded, { recursive: true })
    const anchors = readJSON(path.join(recorded, 'anchors.json'))
    assert.ok(Array.isArray(anchors), 'anchors.json is not an array')
    // Every DESIGN.md intake fact (found, anchors_count, data, licence, stock_environment, size).
    facts = { ...INTAKE, anchors_count: anchors.length }
  })
  if (!recorded || !facts) return
  check(`${name}: fixture build_commands is ${expectPass ? 'a non-empty list' : 'empty, with an install command under another key'}`, () => {
    const baseline = readJSON(path.join(recorded, 'baseline.json'))
    assert.ok(Array.isArray(baseline.build_commands), 'build_commands is not a list')
    if (expectPass) assert.ok(baseline.build_commands.length > 0)
    else {
      assert.deepEqual(baseline.build_commands, [])
      const elsewhere = Object.entries(baseline).filter(([key]) => key !== 'build_commands')
      assert.ok(/\binstall\b/i.test(JSON.stringify(elsewhere)), 'no install command under another key')
    }
  })
  const run = await runCase(name, facts, { recorded })
  if (expectPass) {
    check(`${name}: intake gate PASSes`, () => {
      const stderr = fs.readFileSync(path.join(run.runRoot, `stderr-${name}.log`), 'utf8')
      assert.equal(run.signature('intake').status, 'PASS',
        `${JSON.stringify(run.signature('intake'))}; stderr: ${stderr.slice(-1500)}`)
    })
    check(`${name}: run does not stop at intake`, () => {
      assert.notEqual(readJSON(path.join(run.out, 'result.json')).stopped_at, 'intake')
    })
  } else {
    checkStatuses(name, run, 'intake')
    check(`${name}: no downstream scientific agent calls or seal`, () => {
      assert.ok(run.calls.every(row => row.label === 'intake' || /takeaway/i.test(row.label)))
      assert.ok(!fs.existsSync(path.join(run.runRoot, 'control', 'seals', '0001.json')))
    })
  }
}

// SCHEMAS.md A/PREDICTIONS.json: "The seal agent reads `A/intake/`, `A/profile-packet.json`, `A/bounds.json`
// and the baseline's measured outputs under `A/results/reproduce/` ... A margin derived from baseline variability
// names, in its `source`, the measured file and the statistic used ... When neither a scientific requirement nor
// measured baseline variability supports a positive margin, the seal agent never invents one ... The seal prompt
// states all three."
const windowsAround = (text, pattern, before = 500, after = 500) =>
  [...text.matchAll(new RegExp(pattern.source, pattern.flags.includes('g') ? pattern.flags : pattern.flags + 'g'))]
    .map(match => text.slice(Math.max(0, match.index - before), match.index + match[0].length + after))
function sealReadableInputChecks(name, run) {
  const prompt = () => {
    const value = run.calls.find(row => row.label === 'seal')?.prompt
    assert.ok(value, 'no seal prompt recorded')
    return value
  }
  check(`${name}: seal prompt names A/results/reproduce/ among the readable inputs`, () => {
    const text = prompt()
    const reproduce = /(?:\bA|agent)\/results\/reproduce\b/
    assert.match(text, reproduce, 'seal prompt does not name the A/results/reproduce/ path')
    // Listed together with the other readable inputs.
    assert.ok(windowsAround(text, reproduce, 600, 600).some(window =>
      /intake/.test(window) && /profile-packet\.json/.test(window) && /bounds\.json/.test(window)),
    'A/results/reproduce/ is not listed alongside intake/, profile-packet.json and bounds.json')
  })
  check(`${name}: seal prompt states a variability-derived margin cites the measured file and statistic in its source`, () => {
    const windows = windowsAround(prompt(), /variabilit/i, 400, 400)
    assert.ok(windows.length, 'seal prompt never mentions baseline variability')
    assert.ok(windows.some(window => /\bsource\b/.test(window) && /\bfile\b/i.test(window) && /statistic/i.test(window)),
      'no statement that the margin source names the measured file and the statistic')
  })
  check(`${name}: seal prompt states no margin is invented without a requirement or measured variability`, () => {
    const windows = windowsAround(prompt(), /invent/i, 400, 400)
    assert.ok(windows.some(window => /margin/i.test(window) && /requirement/i.test(window) && /variabilit/i.test(window)),
      'no statement that a margin is never invented without a scientific requirement or measured variability')
  })
}

// SCHEMAS.md repair bullet: "The agent may read and rewrite only `A/PREDICTIONS.json`". The new readable
// inputs of the initial seal call do not extend to repair.
function repairScopeChecks(name, run) {
  check(`${name}: repair prompt allows reading and rewriting only A/PREDICTIONS.json`, () => {
    const prompt = run.calls.find(row => row.label === 'seal-repair')?.prompt
    assert.ok(prompt, 'no repair prompt recorded')
    assert.ok(windowsAround(prompt, /PREDICTIONS\.json/, 300, 300).some(window => /\bonly\b/i.test(window)),
      'repair prompt does not restrict the agent to PREDICTIONS.json')
    // Any mention of another seal input must be a prohibition, never a grant.
    for (const other of [/results\/reproduce/, /profile-packet\.json/, /bounds\.json/, /\bintake\//]) {
      for (const window of windowsAround(prompt, other, 120, 40)) {
        assert.match(window, /\b(?:not|never|no|nothing)\b/i, `repair prompt offers ${other.source} as readable`)
      }
    }
  })
}

// Public recorded run positive-openmm run3: its PREDICTIONS.json is stochastic with null margins. Replayed
// through seal it must fail (numeric, no verified seal) before and after a repair that leaves it unchanged.
// A copy that changes only each metric's tolerance to {"abs": 100}, keeping the recorded free text
// (including "exact two-sided binomial" in `comparison`), must PASS with a verified seal: SCHEMAS.md
// "The check reads executable fields only ... Free-text metric fields (`comparison`, `kind`, `rule` and any
// others) are never scanned for words". Fixtures are copied to temporary directories; experiments/ is read only.
async function recordedSealRegression() {
  const label = 'recorded-positive-openmm-run3-seal'
  const source = path.join(EXPERIMENTS, 'positive-openmm', 'run3', 'agent')
  let recorded, profile, facts
  check(`${label}: recorded fixture available; predictions stochastic with null margins`, () => {
    for (const file of ['PREDICTIONS.json', 'profile-packet.json', 'intake', path.join('results', 'reproduce', 'anchors_scored.json')]) {
      assert.ok(fs.existsSync(path.join(source, file)), `missing ${file} under ${source}`)
    }
    const fixture = path.join(parent, `${label}-fixture`)
    for (const item of ['PREDICTIONS.json', 'profile-packet.json', 'intake', path.join('results', 'reproduce')]) {
      fs.cpSync(path.join(source, item), path.join(fixture, item), { recursive: true })
    }
    recorded = readJSON(path.join(fixture, 'PREDICTIONS.json'))
    profile = readJSON(path.join(fixture, 'profile-packet.json'))
    assert.equal(recorded.outputs_stochastic, true)
    assert.ok(Array.isArray(recorded.equivalence_metrics) && recorded.equivalence_metrics.length)
    for (const metric of recorded.equivalence_metrics) {
      const abs = metric?.tolerance && typeof metric.tolerance === 'object' ? metric.tolerance.abs : metric?.tolerance
      assert.ok(abs === null || abs === undefined, `recorded margin is not null: ${JSON.stringify(metric?.tolerance)}`)
    }
    facts = { ...INTAKE, anchors_count: readJSON(path.join(fixture, 'intake', 'anchors.json')).length }
    // Run3 predates the required `baseline_invocation_s`; supply one small enough that the cost check never decides.
    recorded.baseline_invocation_s = { seconds: 0.01, source: 'fixture: one baseline equivalence invocation, 0.01 s' }
  })
  if (!recorded || !profile || !facts) return
  const fixture = path.join(parent, `${label}-fixture`)
  const prepare = (name, predictions) => {
    const runRoot = path.join(parent, name)
    const intake = path.join(parent, `${name}-intake`)
    fs.cpSync(path.join(fixture, 'intake'), intake, { recursive: true })
    fs.cpSync(path.join(fixture, 'results', 'reproduce'), path.join(runRoot, 'agent', 'results', 'reproduce'), { recursive: true })
    writeJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json'), predictions)
    return { runRoot, intake }
  }

  // Recorded predictions, unchanged; the repair stub rewrites nothing.
  {
    const name = `${label}-null-margins`
    const { runRoot, intake } = prepare(name, recorded)
    const predictionsFile = path.join(runRoot, 'agent', 'PREDICTIONS.json')
    const before = fs.readFileSync(predictionsFile)
    const run = await runCase(name, facts, { runRoot, preserve: true, recorded: intake, profile })
    checkStatuses(name, run, 'seal')
    check(`${name}: first attempt fails stochastic_equivalence_invalid and triggers one repair`, () => {
      assert.deepEqual(run.calls.filter(row => ['seal', 'seal-repair'].includes(row.label)).map(row => row.label), ['seal', 'seal-repair'])
      assert.ok(run.calls.find(row => row.label === 'seal-repair').prompt.includes('stochastic_equivalence_invalid'))
    })
    check(`${name}: after an unchanged repair, numeric FAIL with no verified seal`, () => {
      assert.deepEqual(fs.readFileSync(predictionsFile), before)
      const signature = run.signature('seal')
      assert.equal(signature.status, 'FAIL')
      assert.equal(signature.error_class, 'numeric')
      assert.equal(signature.exit_code, 2)
      assert.equal(run.stage('seal').facts.seal_verified, false)
      assert.equal(run.stage('seal').facts.prediction_count, recorded.predictions.length)
      assert.deepEqual(readJSON(path.join(runRoot, 'control', 'stages', 'seal.json')).reason_codes, ['stochastic_equivalence_invalid'])
      const seals = path.join(runRoot, 'control', 'seals')
      assert.deepEqual(fs.existsSync(seals) ? fs.readdirSync(seals) : [], [])
    })
    sealReadableInputChecks(name, run)
    repairScopeChecks(name, run)
  }

  // The recorded predictions with only each metric's tolerance changed to {"abs": 100}; every other field,
  // including the recorded comparison text, stays exactly as recorded.
  {
    const name = `${label}-abs-100`
    const value = JSON.parse(JSON.stringify(recorded))
    for (const metric of value.equivalence_metrics) metric.tolerance = { abs: 100 }
    check(`${name}: copy differs from the recorded file only in equivalence_metrics tolerances`, () => {
      const strip = predictions => ({ ...predictions, equivalence_metrics: predictions.equivalence_metrics.map(metric => {
        const { tolerance, ...rest } = metric
        return rest
      }) })
      assert.deepEqual(strip(value), strip(recorded))
      assert.ok(recorded.equivalence_metrics.some(metric => /exact two-sided binomial/.test(JSON.stringify(metric?.comparison))),
        'recorded comparison text with "exact two-sided binomial" not found; fixture changed')
    })
    const { runRoot, intake } = prepare(name, value)
    const run = await runCase(name, facts, { runRoot, preserve: true, recorded: intake, profile })
    const diagnose = () => {
      const receipt = readJSON(path.join(runRoot, 'control', 'stages', 'seal.json'))
      const repair = run.calls.find(row => row.label === 'seal-repair')
      // Script-owned field paths from the repair feedback make a rejection diagnosable.
      const paths = repair ? [...new Set(repair.prompt.match(/\b(?:equivalence_metrics|paired_seed_tests|confidence_rule|sample_sizes|outputs_stochastic|predictions|infeasible_methods)[\w.\[\]]*/g) || [])] : []
      return { receipt, repair, detail: `reason_codes ${JSON.stringify(receipt.reason_codes)}; repair feedback field paths ${JSON.stringify(paths)}` }
    }
    check(`${name}: not rejected for stochastic_equivalence_invalid (free text is never scanned)`, () => {
      const { receipt, repair, detail } = diagnose()
      assert.ok(Array.isArray(receipt.reason_codes), 'seal receipt lacks reason_codes')
      assert.ok(!receipt.reason_codes.includes('stochastic_equivalence_invalid'), detail)
      assert.ok(!repair || !repair.prompt.includes('stochastic_equivalence_invalid'), `first attempt rejected for stochastic_equivalence_invalid; ${detail}`)
    })
    check(`${name}: seal PASSes with a verified seal on the first attempt`, () => {
      const { receipt, detail } = diagnose()
      const signature = run.signature('seal')
      assert.equal(signature.status, 'PASS', detail)
      assert.equal(signature.exit_code, 0)
      assert.equal(run.stage('seal').facts.seal_present, true)
      assert.equal(run.stage('seal').facts.seal_verified, true)
      assert.equal(run.stage('seal').facts.prediction_count, recorded.predictions.length)
      assert.deepEqual(receipt.reason_codes, [])
      assert.deepEqual(run.calls.filter(row => ['seal', 'seal-repair'].includes(row.label)).map(row => row.label), ['seal'])
      assert.deepEqual(readJSON(path.join(runRoot, 'agent', 'PREDICTIONS.json')), value)
      assert.equal(readJSON(path.join(runRoot, 'control', 'seals', '0001.json')).sha256, predictionHash(runRoot))
    })
  }
}

// SCHEMAS.md A/PREDICTIONS.json: "Stochastic seals require statistical `equivalence_metrics` with positive
// absolute margins ... The check reads executable fields only: evaluation applies each metric's `name` and
// numeric `tolerance`, so an exact or bitwise rule is a zero or missing absolute margin. Free-text metric fields
// (`comparison`, `kind`, `rule` and any others) are never scanned for words; statistical terms such as
// "exact binomial bound" are allowed."
function stochasticValid() {
  const value = JSON.parse(JSON.stringify(PREDICTIONS))
  value.outputs_stochastic = true
  value.paired_seed_tests = { kind: 'paired_median', seeds: [0, 1, 2, 3, 4, 5] }
  value.sample_sizes = { inputs: 1, seeds: 6 }
  value.confidence_rule = {
    performance: { kind: 'paired_median', confidence: 0.95 },
    equivalence: { kind: 'paired_median', confidence: 0.95 },
  }
  value.equivalence_metrics = [{ name: 'sum', source: 'baseline per-seed standard deviation of sum', tolerance: { abs: 0.1 } }]
  return value
}
async function stochasticCase(name, mutate, { raw } = {}) {
  const runRoot = path.join(parent, name)
  const value = stochasticValid()
  mutate(value)
  const predictionsFile = path.join(runRoot, 'agent', 'PREDICTIONS.json')
  writeJSON(predictionsFile, value)
  if (raw) fs.writeFileSync(predictionsFile, raw(value))
  const run = await runCase(name, INTAKE, { runRoot, preserve: true })
  const receipt = () => readJSON(path.join(runRoot, 'control', 'stages', 'seal.json'))
  return { run, runRoot, value, receipt }
}
async function stochasticFreeTextChecks() {
  const texts = ['exact binomial', 'exact', 'bitwise']
  const cases = []
  for (const field of ['comparison', 'kind', 'rule']) {
    for (const text of texts) cases.push([`${field}-${text.replace(/\W+/g, '-')}`, { [field]: text }])
  }
  cases.push(['all-fields', { comparison: 'exact two-sided binomial bound', kind: 'exact', rule: 'bitwise identical outputs' }])
  cases.push(['other-field', { notes: 'Bitwise EXACT agreement expected; exact binomial bound on sign test' }])
  for (const [label, extra] of cases) {
    const name = `stochastic-free-text-${label}`
    const { run, runRoot, receipt } = await stochasticCase(name, value => {
      Object.assign(value.equivalence_metrics[0], extra)
    })
    check(`${name}: positive absolute margin with free text ${JSON.stringify(extra)} not rejected for stochastic_equivalence_invalid`, () => {
      assert.ok(!receipt().reason_codes.includes('stochastic_equivalence_invalid'), JSON.stringify(receipt().reason_codes))
      const repair = run.calls.find(row => row.label === 'seal-repair')
      assert.ok(!repair || !repair.prompt.includes('stochastic_equivalence_invalid'), 'first attempt rejected for stochastic_equivalence_invalid')
    })
    // The base protocol is otherwise valid (it seals without the free text), so the seal must PASS.
    checkStatuses(name, run, null)
    check(`${name}: verified seal with no reason codes`, () => {
      assert.equal(run.stage('seal').facts.seal_verified, true)
      assert.deepEqual(receipt().reason_codes, [])
      assert.equal(readJSON(path.join(runRoot, 'control', 'seals', '0001.json')).sha256, predictionHash(runRoot))
    })
  }
}
async function stochasticRejectionChecks() {
  const metric = tolerance => value => {
    if (tolerance === undefined) delete value.equivalence_metrics[0].tolerance
    else value.equivalence_metrics[0].tolerance = tolerance
  }
  // JSON cannot spell non-finite numbers; 1e999 parses to Infinity.
  const nonFinite = form => value => JSON.stringify(value, null, 2).replace('"tolerance": "__INF__"', `"tolerance": ${form}`)
  const cases = [
    // Margins: zero, missing, null, negative, non-finite, relative.
    ['tolerance-zero', metric(0)],
    ['tolerance-abs-zero', metric({ abs: 0 })],
    ['tolerance-missing', metric(undefined)],
    ['tolerance-null', metric(null)],
    ['tolerance-abs-null', metric({ abs: null })],
    ['tolerance-negative', metric(-0.1)],
    ['tolerance-abs-negative', metric({ abs: -0.1 })],
    ['tolerance-infinite', metric('__INF__'), nonFinite('1e999')],
    ['tolerance-abs-infinite', metric('__INF__'), nonFinite('{"abs": 1e999}')],
    ['tolerance-rel', metric({ rel: 0.1 })],
    ['tolerance-rel-zero', metric({ rel: 0 })],
    // An exact rule is a zero absolute margin, whatever the free text says.
    ['tolerance-abs-zero-statistical-text', value => {
      Object.assign(value.equivalence_metrics[0], { tolerance: { abs: 0 }, comparison: 'paired-median confidence interval within margin' })
    }],
    // Prose-only rules and missing names/sources.
    ['metric-prose-only', value => { value.equivalence_metrics = ['paired difference within Monte Carlo error'] }],
    ['metric-empty-name', value => { value.equivalence_metrics[0].name = '' }],
    ['metric-empty-source', value => { value.equivalence_metrics[0].source = ' ' }],
    // Seeds.
    ['seeds-deterministic', value => {
      value.paired_seed_tests = { kind: 'deterministic', justification: 'fixed seed reproduces outputs' }
    }],
    ['seeds-wrong-kind', value => { value.paired_seed_tests.kind = 'paired_mean' }],
    ['seeds-duplicate', value => { value.paired_seed_tests.seeds = [0, 1, 2, 3, 4, 4] }],
    ['seeds-non-integer', value => { value.paired_seed_tests.seeds = [0, 1, 2, 3, 4, 5.5] }],
    ['seeds-prose', value => { value.paired_seed_tests = 'paired medians over six seeds' }],
    // Confidence rule.
    ['confidence-one', value => { value.confidence_rule.equivalence.confidence = 1 }],
    ['confidence-below-half', value => { value.confidence_rule.equivalence.confidence = 0.4 }],
    ['confidence-missing', value => { delete value.confidence_rule.equivalence.confidence }],
    ['confidence-wrong-kind', value => { value.confidence_rule.equivalence.kind = 'exact' }],
    ['confidence-prose', value => { value.confidence_rule = '95% paired confidence interval' }],
  ]
  for (const [label, mutate, raw] of cases) {
    const name = `stochastic-reject-${label}`
    const { run, receipt } = await stochasticCase(name, mutate, { raw })
    checkStatuses(name, run, 'seal')
    check(`${name}: rejected for stochastic_equivalence_invalid; numeric, no seal`, () => {
      assert.deepEqual(receipt().reason_codes, ['stochastic_equivalence_invalid'])
      assert.equal(run.signature('seal').error_class, 'numeric')
      assert.equal(run.signature('seal').exit_code, 2)
      assert.equal(run.stage('seal').facts.seal_verified, false)
      const seals = path.join(parent, name, 'control', 'seals')
      assert.deepEqual(fs.existsSync(seals) ? fs.readdirSync(seals) : [], [])
    })
  }
}

// SCHEMAS.md A/PREDICTIONS.json: "`baseline_invocation_s` is `{seconds, source}`. `seconds` is a finite positive
// number ... `source` is a non-empty string ... Any other shape is `protocol_incomplete`. The seal check projects one
// complete performance scorer at that estimate, with the adapter smoke's rule: `projected_s` = (`warmup` +
// `repetitions`) × 2 × `seconds`, plus, unless `equal_outcome_target.not_applicable` is true, `b / baseline_gpus +
// b / method_gpus` for each compute budget `b` ... When at least one method is feasible and `projected_s` exceeds
// 0.9 × the resolved `evaluate` budget, the seal fails `protocol_cost`; a seal with no feasible method skips this check."
// Resolution (EXECUTION.json bullet): EXECUTION.json.stage_budgets_s, then args.stage_budgets_s, then evaluate=2400.
const DEFAULT_EVALUATE = 2400
const COST_SOURCE = 'PRIVATE_COST_SOURCE_36: reproduce ensemble wall times two blocks plus start-up'
const COST_FIELD_PATHS = ['warmup', 'repetitions', 'paired_seed_tests.seeds', 'evaluation_inputs.ids', 'compute_budgets', 'baseline_invocation_s']
function projectedSeconds(seal) {
  const curve = seal.equal_outcome_target?.not_applicable === true ? 0
    : seal.compute_budgets.reduce((sum, b) => sum + b / seal.hardware_cost_basis.baseline_gpus + b / seal.hardware_cost_basis.method_gpus, 0)
  return (seal.warmup + seal.repetitions) * 2 * seal.baseline_invocation_s.seconds + curve
}
// An executable cost protocol on the base fixture: integer warmup, GPU counts per arm, no outcome curve.
function costValid(seconds = 1, extra = {}) {
  const value = JSON.parse(JSON.stringify(PREDICTIONS))
  Object.assign(value, { warmup: 1, repetitions: 5,
    hardware_cost_basis: { baseline_gpus: 1, method_gpus: 1, budget_unit: 'gpu_s' },
    equal_outcome_target: { not_applicable: true, reason: 'fixed-work fixture; no outcome curve' },
    baseline_invocation_s: { seconds, source: COST_SOURCE } }, extra)
  return value
}
// The outcome curve applies: budgets 8, 16, 40 at 2 baseline and 4 method GPUs add 0.75 × 64 = 48 s.
function withCurve(value, applies) {
  value.compute_budgets = [8, 16, 40]
  value.hardware_cost_basis = { baseline_gpus: 2, method_gpus: 4, budget_unit: 'gpu_s' }
  value.equal_outcome_target = applies ? { metric: 'sum', comparison: '>=', target: 499500 }
    : { not_applicable: true, reason: 'fixed-work fixture; no outcome curve' }
  for (const row of value.predictions) {
    row.outcome_vs_compute_points = value.compute_budgets.map(compute_budget => ({
      compute_budget, predicted_outcome: 499500, uncertainty: 'exact integer equality' }))
  }
  return value
}
// Profile with no calibration and no transfer time: no method is feasible.
function noFeasibleProfile() {
  const value = JSON.parse(JSON.stringify(PROFILE))
  delete value.concurrency
  value.gpu_count = 1
  value.stages[1].wall_s = 0
  value.stages[2].wall_s = 4
  return value
}
async function sealCase(name, value, options = {}, raw) {
  const runRoot = path.join(parent, name)
  const predictionsFile = path.join(runRoot, 'agent', 'PREDICTIONS.json')
  writeJSON(predictionsFile, value)
  if (raw) fs.writeFileSync(predictionsFile, raw)
  const run = await runCase(name, INTAKE, { ...options, runRoot, preserve: true })
  const receipt = () => readJSON(path.join(runRoot, 'control', 'stages', 'seal.json'))
  const seals = () => {
    const dir = path.join(runRoot, 'control', 'seals')
    return fs.existsSync(dir) ? fs.readdirSync(dir).filter(file => /^\d{4}\.json$/.test(file)) : []
  }
  const sealCalls = () => run.calls.filter(row => ['seal', 'seal-repair'].includes(row.label)).map(row => row.label)
  return { run, runRoot, value, receipt, seals, sealCalls }
}
function expectSealPass(name, result, detail = '') {
  checkStatuses(name, result.run, null)
  check(`${name}: verified seal 0001, no reason codes, no repair`, () => {
    assert.deepEqual(result.receipt().reason_codes, [], detail)
    assert.equal(result.run.stage('seal').facts.seal_verified, true)
    assert.deepEqual(result.seals(), ['0001.json'])
    assert.equal(readJSON(path.join(result.runRoot, 'control', 'seals', '0001.json')).sha256, predictionHash(result.runRoot))
    assert.deepEqual(result.sealCalls(), ['seal'])
  })
}
function expectSealFail(name, result, code, detail = '') {
  checkStatuses(name, result.run, 'seal')
  check(`${name}: FAIL numeric with reason code ${code}; no seal number allocated`, () => {
    assert.deepEqual(result.receipt().reason_codes, [code], detail)
    assert.equal(result.run.signature('seal').error_class, 'numeric')
    assert.equal(result.run.signature('seal').exit_code, 2)
    assert.equal(result.run.stage('seal').facts.seal_verified, false)
    assert.deepEqual(result.seals(), [])
  })
}
const sealPrompt = run => {
  const value = run.calls.find(row => row.label === 'seal')?.prompt
  assert.ok(value, 'no seal prompt recorded')
  return value
}
// The budget in seconds, next to a mention of evaluate.
function statesBudget(text, budget) {
  return windowsAround(text, new RegExp(`(?<![\\d.])${budget}(?![\\d.])`), 300, 300)
    .some(window => /evaluate/.test(window) && /second|\d\s*s\b/i.test(window))
}
// The projection rule: warmup + repetitions, × 2, the invocation estimate and the 0.9 factor of the evaluate budget.
function statesProjection(text) {
  return windowsAround(text, /0\.9(?!\d)/, 600, 600).some(window => /warmup/.test(window) && /repetitions/.test(window) &&
    /(?:×|\*|\bx)\s*2\b|\b2\s*(?:×|\*|x\b)|twice/.test(window) && /baseline_invocation_s|seconds/.test(window) && /evaluate/.test(window))
}

async function costChecks() {
  // 1. Shape. JSON cannot spell non-finite numbers; 1e999 parses to Infinity.
  const shape = [
    ['missing', value => { delete value.baseline_invocation_s }],
    ['null', value => { value.baseline_invocation_s = null }],
    ['number', value => { value.baseline_invocation_s = 10 }],
    ['string', value => { value.baseline_invocation_s = '10 seconds' }],
    ['array', value => { value.baseline_invocation_s = [10, COST_SOURCE] }],
    ['seconds-missing', value => { delete value.baseline_invocation_s.seconds }],
    ['seconds-null', value => { value.baseline_invocation_s.seconds = null }],
    ['seconds-zero', value => { value.baseline_invocation_s.seconds = 0 }],
    ['seconds-negative', value => { value.baseline_invocation_s.seconds = -1 }],
    ['seconds-string', value => { value.baseline_invocation_s.seconds = '1' }],
    ['seconds-boolean', value => { value.baseline_invocation_s.seconds = true }],
    ['seconds-infinite', value => { value.baseline_invocation_s.seconds = '__INF__' },
      value => JSON.stringify(value, null, 2).replace('"seconds": "__INF__"', '"seconds": 1e999')],
    ['source-missing', value => { delete value.baseline_invocation_s.source }],
    ['source-empty', value => { value.baseline_invocation_s.source = '' }],
    ['source-null', value => { value.baseline_invocation_s.source = null }],
    ['source-number', value => { value.baseline_invocation_s.source = 118.6 }],
    ['source-object', value => { value.baseline_invocation_s.source = { file: 'smoke.json' } }],
  ]
  for (const [label, mutate, raw] of shape) {
    const name = `invocation-shape-${label}`
    const value = costValid(0.01)
    mutate(value)
    const result = await sealCase(name, value, {}, raw ? raw(value) : undefined)
    expectSealFail(name, result, 'protocol_incomplete')
  }
  // The key is required whatever the menu: a zero-prediction seal without it is incomplete too.
  {
    const name = 'invocation-shape-missing-no-feasible'
    const value = costValid(0.01)
    delete value.baseline_invocation_s
    value.predictions = []
    value.infeasible_methods = ['data-parallel over inputs', 'batching', 'multi-GPU', 'ensembles', 'pipelining']
      .map(method => ({ method, reason: 'Bound is below 1.05.' }))
    expectSealFail(name, await sealCase(name, value, { profile: noFeasibleProfile() }), 'protocol_incomplete')
  }

  // 2. Projection at the default evaluate budget: 0.9 × 2400 = 2160 s; warmup 1 + repetitions 5 gives 12 × seconds.
  const limit = 0.9 * DEFAULT_EVALUATE
  const cases = [
    ['default-at-limit', costValid(180), true],
    ['default-over-limit', costValid(180.0625), false],
    // Curve applies: 12 × 176 + 48 = 2160 passes; 12 × 177 + 48 = 2172 fails, though 12 × 177 = 2124 alone fits.
    ['curve-at-limit', withCurve(costValid(176), true), true],
    ['curve-over-limit', withCurve(costValid(177), true), false],
    ['curve-not-applicable', withCurve(costValid(177), false), true],
  ]
  check('reference projections straddle 0.9 × the default evaluate budget', () => {
    assert.deepEqual(cases.map(([, value]) => projectedSeconds(value)), [2160, 2160.75, 2160, 2172, 2124])
    for (const [, value, fits] of cases) assert.equal(projectedSeconds(value) <= limit, fits)
  })
  const results = {}
  for (const [label, value, fits] of cases) {
    const name = `cost-${label}`
    const result = await sealCase(name, value)
    results[label] = result
    const detail = `projected ${projectedSeconds(value)} s against ${limit} s`
    if (fits) expectSealPass(name, result, detail)
    else {
      expectSealFail(name, result, 'protocol_cost', detail)
      check(`${name}: exactly one seal call and one repair`, () => assert.deepEqual(result.sealCalls(), ['seal', 'seal-repair']))
    }
  }

  // 3. Seal prompt: resolved budget, projection, 0.9 factor, measured seconds never lowered; skeletons.
  const promptRun = results['default-at-limit'].run
  check('cost prompt: seal prompt states the default evaluate budget, 2400 seconds', () => {
    assert.ok(statesBudget(sealPrompt(promptRun), DEFAULT_EVALUATE), 'resolved evaluate budget 2400 s not stated')
  })
  check('cost prompt: seal prompt states the projection (warmup + repetitions) × 2 × seconds and the 0.9 factor', () => {
    assert.ok(statesProjection(sealPrompt(promptRun)), 'projection with the 0.9 factor not stated')
  })
  check('cost prompt: seal prompt states the outcome-curve term with GPU counts unless not_applicable', () => {
    assert.ok(windowsAround(sealPrompt(promptRun), /0\.9(?!\d)/, 900, 900).some(window =>
      /not_applicable/.test(window) && /baseline_gpus/.test(window) && /method_gpus/.test(window)), 'curve term not stated')
  })
  check('cost prompt: seal prompt says seconds comes from the measurements and is never lowered to fit', () => {
    assert.ok(windowsAround(sealPrompt(promptRun), /\blower/i, 400, 400).some(window =>
      /\b(?:never|not|no)\b/i.test(window) && /measure/i.test(window) && /seconds|baseline_invocation_s/.test(window)),
    'no statement that seconds is measured and never lowered')
  })
  check('cost prompt: both skeletons include baseline_invocation_s {seconds: number, source: string}', () => {
    const prompt = sealPrompt(promptRun)
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
      const invocation = example.baseline_invocation_s
      assert.ok(invocation && typeof invocation === 'object' && !Array.isArray(invocation), 'skeleton lacks baseline_invocation_s object')
      assert.deepEqual(Object.keys(invocation).sort(), ['seconds', 'source'])
      assert.equal(typeof invocation.seconds, 'number')
      assert.equal(typeof invocation.source, 'string')
    }
  })

  // Evaluate budget from args.stage_budgets_s (1000 → 900 s) and from EXECUTION.json, which takes precedence.
  for (const [label, options, seconds, fits, budget] of [
    // 12 × 75 = 900 fits; 12 × 75.0625 = 900.75 does not, though it fits the 2160 s default.
    ['args-at-limit', { argsBudgets: { evaluate: 1000 } }, 75, true, 1000],
    ['args-over-limit', { argsBudgets: { evaluate: 1000 } }, 75.0625, false, 1000],
    ['execution-at-limit', { executionBudgets: { evaluate: 1000 } }, 75, true, 1000],
    ['execution-over-limit', { executionBudgets: { evaluate: 1000 } }, 75.0625, false, 1000],
    // EXECUTION.json 1000 wins over args 5000 (limit 4500); EXECUTION.json 5000 wins over args 1000.
    ['execution-over-args', { executionBudgets: { evaluate: 1000 }, argsBudgets: { evaluate: 5000 } }, 75.0625, false, 1000],
    ['execution-over-args-fits', { executionBudgets: { evaluate: 5000 }, argsBudgets: { evaluate: 1000 } }, 100, true, 5000],
  ]) {
    const name = `cost-${label}`
    const value = costValid(seconds)
    const result = await sealCase(name, value, options)
    const detail = `projected ${projectedSeconds(value)} s against ${0.9 * budget} s`
    if (fits) expectSealPass(name, result, detail)
    else expectSealFail(name, result, 'protocol_cost', detail)
    check(`${name}: seal prompt states the resolved evaluate budget, ${budget} seconds`, () => {
      assert.ok(statesBudget(sealPrompt(result.run), budget), `resolved evaluate budget ${budget} s not stated`)
    })
  }

  // No feasible method: the check is skipped; a verified negative result passes even at an absurd estimate.
  for (const [label, applies] of [['no-curve', false], ['curve', true]]) {
    const name = `cost-skipped-no-feasible-${label}`
    const value = withCurve(costValid(1e6), applies)
    value.predictions = []
    value.infeasible_methods = ['data-parallel over inputs', 'batching', 'multi-GPU', 'ensembles', 'pipelining']
      .map(method => ({ method, reason: 'Bound is below 1.05.' }))
    const result = await sealCase(name, value, { profile: noFeasibleProfile() })
    expectSealPass(name, result, `projected ${projectedSeconds(value)} s`)
    check(`${name}: prediction_count 0`, () => assert.equal(result.run.stage('seal').facts.prediction_count, 0))
  }

  // Order: stochastic_equivalence_invalid precedes protocol_cost, which precedes bounds_coverage_invalid.
  {
    const name = 'cost-order-stochastic-first'
    const value = costValid(1e4, { outputs_stochastic: true })
    expectSealFail(name, await sealCase(name, value), 'stochastic_equivalence_invalid')
  }
  {
    const name = 'cost-order-before-coverage'
    const value = costValid(1e4, { infeasible_methods: [] })
    expectSealFail(name, await sealCase(name, value), 'protocol_cost')
  }

  // Repair: one call; prompt carries the code, six field paths and the resolved budget, and no measured value.
  // Budget 1000 (limit 900): warmup 1 + repetitions 12 at 40.0625 s projects 1041.625 s; repetitions 8 gives
  // 721.125 s and fits; repetitions 11 gives 961.5 s and still does not.
  for (const [label, repetitions, fits] of [['fits', 8, true], ['still-over', 11, false]]) {
    const name = `cost-repair-${label}`
    const value = costValid(40.0625, { repetitions: 12 })
    const replacement = { ...JSON.parse(JSON.stringify(value)), repetitions }
    check(`${name}: reference projections`, () => {
      assert.equal(projectedSeconds(value), 1041.625)
      assert.equal(projectedSeconds(replacement), fits ? 721.125 : 961.5)
    })
    const result = await sealCase(name, value, { argsBudgets: { evaluate: 1000 }, repairPredictions: replacement })
    check(`${name}: exactly one initial seal call and one repair`, () => assert.deepEqual(result.sealCalls(), ['seal', 'seal-repair']))
    const repairPrompt = () => {
      const prompt = result.run.calls.find(row => row.label === 'seal-repair')?.prompt
      assert.ok(prompt, 'no repair prompt recorded')
      return prompt
    }
    check(`${name}: repair prompt carries protocol_cost and the six field paths`, () => {
      const prompt = repairPrompt()
      assert.ok(prompt.includes('protocol_cost'), 'missing reason code')
      for (const field of COST_FIELD_PATHS) assert.match(prompt, new RegExp(`(?<![\\w.])${field.replace('.', '\\.')}(?![\\w])`), `missing field path ${field}`)
    })
    check(`${name}: repair prompt restates the resolved evaluate budget (1000 s) and the projection rule`, () => {
      const prompt = repairPrompt()
      assert.ok(statesBudget(prompt, 1000), 'resolved evaluate budget 1000 s not restated')
      assert.ok(statesProjection(prompt), 'projection rule with the 0.9 factor not restated')
    })
    check(`${name}: repair prompt holds no value from the predictions`, () => {
      const prompt = repairPrompt()
      for (const leaked of ['40.0625', '1041.625', COST_SOURCE, 'PRIVATE_COST_SOURCE_36', SENTINEL,
        PREDICTIONS.infeasible_methods[0].reason, '499500']) {
        assert.ok(!prompt.includes(leaked), `value leaked: ${leaked}`)
      }
      assert.ok(!prompt.includes(JSON.stringify(PROFILE)), 'profile evidence leaked')
      assert.ok(!prompt.includes('k_derivation'), 'bounds leaked')
    })
    repairScopeChecks(name, result.run)
    if (fits) {
      checkStatuses(name, result.run, null)
      check(`${name}: repaired protocol seals as 0001 with no reason codes`, () => {
        assert.deepEqual(readJSON(path.join(result.runRoot, 'agent', 'PREDICTIONS.json')), replacement)
        assert.deepEqual(result.receipt().reason_codes, [])
        assert.equal(result.run.stage('seal').facts.seal_verified, true)
        assert.deepEqual(result.seals(), ['0001.json'])
        assert.equal(readJSON(path.join(result.runRoot, 'control', 'seals', '0001.json')).sha256, predictionHash(result.runRoot))
      })
    } else {
      expectSealFail(name, result, 'protocol_cost')
      check(`${name}: initial seal call saw no seal files`, () => {
        for (const call of result.run.calls.filter(row => ['seal', 'seal-repair'].includes(row.label))) assert.deepEqual(call.sealFiles, {})
      })
    }
  }
}

// Public recorded run positive-openmm run14: sealed with 16 seeds, warmup 0, repetitions 12 and no outcome curve.
// Its adapter smoke measured 118.6 s: 12 × 2 × 118.6 = 2846.4 s against 0.9 × 2400 = 2160 s. With that estimate
// sealed, the seal itself fails protocol_cost; repetitions 8 projects 1897.6 s and passes. experiments/ is read only.
async function run14CostRegression() {
  const label = 'recorded-positive-openmm-run14-cost'
  const source = path.join(EXPERIMENTS, 'positive-openmm', 'run14')
  let sealed, profile
  check(`${label}: recorded seal matches the documented protocol`, () => {
    sealed = readJSON(path.join(source, 'control', 'seals', '0001.predictions.json'))
    profile = readJSON(path.join(source, 'agent', 'profile-packet.json'))
    assert.equal(sealed.paired_seed_tests.seeds.length, 16)
    assert.equal(sealed.warmup, 0)
    assert.equal(sealed.repetitions, 12)
    assert.equal(sealed.equal_outcome_target.not_applicable, true)
    assert.deepEqual(sealed.compute_budgets, [240, 480, 960])
    const smoke = readJSON(path.join(source, 'agent', 'results', 'implement', 'adapter', '2', 'out', 'smoke.json'))
    assert.ok(Math.abs(smoke.process_wall_s - 118.6) < 0.05, `smoke measured ${smoke.process_wall_s}`)
  })
  if (!sealed || !profile) return
  const invocation = { seconds: 118.6, source: 'agent/results/implement/adapter/2/out/smoke.json process_wall_s 118.6: two sequential eight-replica blocks' }
  for (const [suffix, repetitions, fits] of [['as-sealed', 12, false], ['repetitions-8', 8, true]]) {
    const name = `${label}-${suffix}`
    const value = { ...JSON.parse(JSON.stringify(sealed)), repetitions, baseline_invocation_s: invocation }
    const projected = projectedSeconds(value)
    check(`${name}: reference projection ${fits ? 'fits' : 'exceeds'} 2160 s`, () => {
      assert.ok(Math.abs(projected - (fits ? 1897.6 : 2846.4)) < 1e-9, String(projected))
      assert.equal(projected <= 0.9 * DEFAULT_EVALUATE, fits)
    })
    const runRoot = path.join(parent, name)
    fs.cpSync(path.join(source, 'agent', 'results', 'reproduce'), path.join(runRoot, 'agent', 'results', 'reproduce'), { recursive: true })
    const result = await sealCase(name, value, { profile })
    const detail = `projected ${projected} s; reason_codes ${JSON.stringify(result.receipt().reason_codes)}`
    if (fits) {
      check(`${name}: does not fail protocol_cost`, () => {
        assert.ok(!result.receipt().reason_codes.includes('protocol_cost'), detail)
        const repair = result.run.calls.find(row => row.label === 'seal-repair')
        assert.ok(!repair || !repair.prompt.includes('protocol_cost'), 'first attempt rejected for protocol_cost')
      })
      expectSealPass(name, result, detail)
    } else expectSealFail(name, result, 'protocol_cost', detail)
  }
}

// SCHEMAS.md A/intake/: "An intake FAIL signature names the failed gate conditions in v1 `blockers`, from the
// existing blocker vocabulary and in this fixed order: `licence` ..., `data_unavailable` ..., and
// `env_irreproducible` ... Each condition is read from the facts the record carries, whatever else failed ...;
// a null or absent fact adds no blocker. When no condition applies, and for every PASS, SKIPPED and stub intake,
// `blockers` stays `["none"]`. Intake `exit_code`, `exit_kind` and `error_class` are unchanged.
// `OPERATOR_TAKEAWAY.md` lists these blockers in its Blockers section as for any stage."
const BLOCKER_VOCABULARY = ['data_unavailable', 'licence', 'env_irreproducible', 'files_local_only', 'compute_cap', 'capacity', 'none']
// Vocabulary tokens listed in the takeaway's Blockers section (heading containing "blocker" up to the next heading).
function takeawayBlockers(runRoot) {
  const lines = fs.readFileSync(path.join(runRoot, 'operator', 'OPERATOR_TAKEAWAY.md'), 'utf8').split('\n')
  const start = lines.findIndex(line => /^\s*#+\s.*blocker/i.test(line))
  assert.ok(start >= 0, 'OPERATOR_TAKEAWAY.md has no Blockers section')
  const end = lines.findIndex((line, i) => i > start && /^\s*#+\s/.test(line))
  const section = lines.slice(start + 1, end < 0 ? undefined : end).join('\n')
  return new Set(BLOCKER_VOCABULARY.filter(token => new RegExp(`(?<![A-Za-z0-9_])${token}(?![A-Za-z0-9_])`).test(section)))
}
function blockerChecks(name, run, expected) {
  check(`${name}: intake blockers are ${JSON.stringify(expected)}`, () => {
    assert.deepEqual(run.signature('intake').blockers, expected)
  })
  check(`${name}: SKIPPED stages keep blockers ["none"]`, () => {
    for (const row of run.stages) {
      const signature = row.signature || row
      if (signature.status === 'SKIPPED') assert.deepEqual(signature.blockers, ['none'], signature.stage)
    }
  })
  check(`${name}: OPERATOR_TAKEAWAY.md Blockers section lists ${expected.join(', ')}`, () => {
    const listed = takeawayBlockers(run.runRoot)
    if (expected[0] === 'none') assert.deepEqual([...listed], ['none'])
    else {
      listed.delete('none')
      assert.deepEqual([...listed].sort(), [...expected].sort())
    }
  })
}
const exitFields = signature => ({ exit_code: signature.exit_code, exit_kind: signature.exit_kind, error_class: signature.error_class })

async function intakeBlockerChecks() {
  const intakeFail = (name, run) => check(`${name}: intake FAILs`, () => assert.equal(run.signature('intake').status, 'FAIL'))
  // References that name no blocker: a fact-gate failure (found false) and an incomplete required file.
  const references = {}
  for (const [kind, override, options] of [
    ['facts', { found: false }, {}],
    ['files', {}, { incompleteBaseline: 'run_commands' }],
  ]) {
    const name = `blockers-reference-${kind}`
    const run = await runCase(name, { ...INTAKE, ...override }, options)
    checkStatuses(name, run, 'intake')
    blockerChecks(name, run, ['none'])
    references[kind] = exitFields(run.signature('intake'))
  }
  const L = 'licence', D = 'data_unavailable', E = 'env_irreproducible'
  const cases = [
    // Each condition alone, then all three in the fixed order.
    ['blockers-licence-restricted', { licence: 'restricted' }, {}, [L], 'facts'],
    ['blockers-licence-unknown', { licence: 'unknown' }, {}, [L], 'facts'],
    ['blockers-data-partial', { data: 'partial' }, {}, [D], 'facts'],
    ['blockers-data-unavailable', { data: 'unavailable' }, {}, [D], 'facts'],
    ['blockers-data-unknown', { data: 'unknown' }, {}, [D], 'facts'],
    ['blockers-stock-false', { stock_environment: false }, {}, [E], 'facts'],
    ['blockers-all-three', { licence: 'restricted', data: 'partial', stock_environment: false }, {}, [L, D, E], 'facts'],
    // Conditions are named whatever else failed.
    ['blockers-not-found-licence', { found: false, licence: 'unknown' }, {}, [L], 'facts'],
    ['blockers-not-found-all-three', { found: false, licence: 'unknown', data: 'unavailable', stock_environment: false }, {}, [L, D, E], 'facts'],
    ['blockers-incomplete-licence-data', { licence: 'restricted', data: 'unknown' }, { incompleteBaseline: 'run_commands' }, [L, D], 'files'],
    ['blockers-incomplete-stock-false', { stock_environment: false }, { incompleteBaseline: 'run_commands' }, [E], 'files'],
    // A null fact adds nothing.
    ['blockers-not-found-stock-null', { found: false, stock_environment: null }, {}, ['none'], 'facts'],
    // Regression: public blind-openmm run1 intake facts, with otherwise complete valid files.
    ['blockers-blind-openmm-run1', { found: false, anchors_count: 0, data: 'partial', licence: 'unknown', stock_environment: null, size: 'unknown' },
      { anchors: [] }, [L, D], 'facts'],
    // Regression: a private blind run (facts supplied by the operator; three valid anchors).
    ['blockers-private-blind', { found: true, anchors_count: 3, data: 'available', licence: 'unknown', stock_environment: null, size: 'unknown' },
      {}, [L], 'facts'],
  ]
  for (const [name, override, options, expected, reference] of cases) {
    const run = await runCase(name, { ...INTAKE, ...override }, options)
    checkStatuses(name, run, 'intake')
    intakeFail(name, run)
    blockerChecks(name, run, expected)
    check(`${name}: exit_code, exit_kind and error_class unchanged from the no-blocker ${reference} reference`, () => {
      assert.deepEqual(exitFields(run.signature('intake')), references[reference])
    })
    if (name === 'blockers-private-blind') anchoredChecks(name, run, true)
    if (name === 'blockers-blind-openmm-run1') anchoredChecks(name, run, false)
  }
  // PASS intakes keep ["none"], including with stock_environment null.
  for (const [name, override] of [['blockers-pass', {}], ['blockers-pass-stock-null', { stock_environment: null }]]) {
    const run = await runCase(name, { ...INTAKE, ...override })
    checkStatuses(name, run, null)
    blockerChecks(name, run, ['none'])
  }
  // The public run's recorded intake facts are the ones replayed above.
  check('blockers-blind-openmm-run1: recorded intake facts match the regression facts', () => {
    const source = recordedRun(path.join('blind-openmm', 'run1'))
    assert.ok(source.signatures, `no recorded signatures under ${source.run}`)
    const facts = readRows(source.signatures).filter(row => (row.signature || row).stage === 'intake' && row.facts).at(-1)?.facts
    assert.ok(facts, 'no recorded intake facts')
    for (const [key, value] of Object.entries({ found: false, anchors_count: 0, data: 'partial', licence: 'unknown', stock_environment: null, size: 'unknown' })) {
      assert.deepEqual(facts[key], value, key)
    }
  })
}

async function main() {
  try {
    await intakeBlockerChecks()
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
    sealReadableInputChecks('happy', happy)
    buildCommandsPromptChecks('happy (brief)', happy)
    // No brief: the intake agent runs the bounded public benchmark search (DESIGN.md stage 1 "In").
    const search = await runCase('search-no-brief', INTAKE, { noBrief: true })
    check('search-no-brief: args carry no brief', () => {
      assert.ok(!Object.hasOwn(readJSON(path.join(search.runRoot, 'control', 'args.json')), 'brief'))
    })
    buildCommandsPromptChecks('search-no-brief', search)
    completenessKeyPromptChecks('happy (brief)', happy)
    completenessKeyPromptChecks('search-no-brief', search)
    await commitOrPinChecks()
    await blindOpenmmRun2Regression()
    // Gate: build_commands must be non-empty; a single package-manager install suffices.
    const emptyBuild = await runCase('empty-build-commands', INTAKE, { buildCommands: [] })
    checkStatuses('empty-build-commands', emptyBuild, 'intake')
    check('empty-build-commands: no downstream scientific agent calls or seal', () => {
      assert.ok(emptyBuild.calls.every(row => row.label === 'intake' || /takeaway/i.test(row.label)))
      assert.ok(!fs.existsSync(path.join(emptyBuild.runRoot, 'control', 'seals', '0001.json')))
    })
    const pipBuild = await runCase('pip-install-build-commands', INTAKE, { buildCommands: ['python3 -m pip install openmm==8.1.1'] })
    checkStatuses('pip-install-build-commands', pipBuild, null)
    await positiveOpenmmRegression('run1', true)
    await positiveOpenmmRegression('run2', false)
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

    // An exact rule for stochastic outputs is a zero absolute margin; a positive one is statistical.
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
      repairScopeChecks(name, run)
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
    await recordedSealRegression()
    await stochasticFreeTextChecks()
    await stochasticRejectionChecks()
    await costChecks()
    await run14CostRegression()

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
      ['protocol_cost', value => { Object.assign(value, costValid(1e4)) }],
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
