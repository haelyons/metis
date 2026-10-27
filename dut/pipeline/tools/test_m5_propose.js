#!/usr/bin/env node
'use strict'

// Black-box stage-5 contracts. Execute implementation files; never inspect them.
// Usage: node tools/test_m5_propose.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { createHash, randomUUID } = require('node:crypto')
const { spawn } = require('node:child_process')
const ROOT = path.resolve(__dirname, '..')
const SENTINEL = 'PRIVATE_PROPOSAL_SENTINEL_58321'
const MENU = ['data-parallel over inputs', 'batching', 'multi-GPU', 'ensembles', 'pipelining']
const REASONS = ['exceeds_bound', 'not_parallelisable', 'changes_method', 'equivalence_risk',
  'resource_mismatch', 'weak_profile_evidence', 'other']
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
function writeJSON(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n')
}
function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']'
  if (value !== null && typeof value === 'object') return '{' + Object.keys(value).sort()
    .map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}'
  return JSON.stringify(value)
}
const ballot = (vote = 'approve', reason_codes = []) => ({ vote, reason_codes })
// Ballot i uses label skeptic-<i> (SCHEMAS.md, "Propose, independent votes, and the one-shot gate").
const ballotNumber = title => { const match = /^skeptic-([1-5])$/.exec(String(title)); return match ? Number(match[1]) : null }
const isSkeptic = call => ballotNumber(call.title) !== null
const familyOf = model => /^claude\//.test(String(model)) ? 'claude' : /^codex\//.test(String(model)) ? 'codex'
  : /^cursor\//.test(String(model)) ? 'cursor' : 'opencode'

module.exports = {
  async run(options) {
    const { title, prompt, name, model } = options
    const root = process.env.M5_PROPOSE_ROOT
    const config = JSON.parse(process.env.M5_PROPOSE_CONFIG)
    const sessionID = randomUUID()
    const capture = { ...options, event: 'start', time: Date.now(), returnedSession: sessionID }
    fs.appendFileSync(path.join(root, 'calls.jsonl'), JSON.stringify(capture) + '\n')
    // Scripted per-family failures: { "<label>": { "<family>": "refusal" | "transport" } }.
    const failure = ((config.failures || {})[title] || {})[familyOf(model)]
    if (failure) {
      await new Promise(resolve => setTimeout(resolve, 80))
      fs.appendFileSync(path.join(root, 'calls.jsonl'), JSON.stringify({ event: 'end', title, name,
        time: Date.now(), returnedSession: sessionID }) + '\n')
      return { text: failure === 'refusal' ? 'I cannot help with this request.' : '', json: null, jsonError: null, sessionID,
        tokens: { input: 10, output: 0 }, tokens_known: true, cost: 0, tools: 0, ms: 1,
        errors: [failure === 'refusal' ? 'refusal: the model declined the request' : 'exit 1: connection reset by peer'],
        refusal: failure === 'refusal' }
    }
    let json = { v: 'fixture' }, text, jsonError = null
    if (title === 'propose') {
      if (!config.missingProposal) writeJSON(path.join(root, 'agent', 'proposal.json'), config.proposal || {
        method: config.method || MENU[0], rationale: SENTINEL,
        plan_steps: ['Preserve sealed protocol; parallelise independent inputs.'],
        files_expected: ['candidate.py'], risks: ['Equivalence must be checked.'],
      })
    }
    if (ballotNumber(title) !== null) {
      const index = ballotNumber(title) - 1
      const votes = config.votes || [ballot(), ballot(), ballot(), ballot(), ballot('reject', REASONS)]
      const byFamily = ((config.familyVotes || {})[title] || {})[familyOf(model)]
      json = byFamily !== undefined ? byFamily : votes[index]
      if (json === null) { text = ''; jsonError = 'No JSON in synthetic response' }
      // Keep calls overlapping so concurrency is observable without timing thresholds.
      await new Promise(resolve => setTimeout(resolve, 80))
    }
    fs.appendFileSync(path.join(root, 'calls.jsonl'), JSON.stringify({ event: 'end', title, name,
      time: Date.now(), returnedSession: sessionID }) + '\n')
    return { text: text === undefined ? JSON.stringify(json) : text, json, jsonError, sessionID,
      tokens: { input: 10, output: 5 }, tokens_known: true, cost: 0, tools: 0, ms: 1,
      errors: [], refusal: false }
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
if (require.main !== module) return

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_propose_'))
let failures = 0, checks = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}
function fixture(root, config) {
  const profile = {
    stages: [
      { stage: 'kernels', kind: 'compute', wall_s: 6, gpu_s: 6, wall_fraction: 0.6, start_s: 0, mean_gpu_util: 0.125 },
      { stage: 'transfer', kind: 'transfer', wall_s: 3, gpu_s: 1, wall_fraction: 0.3, start_s: 6, mean_gpu_util: 0.25 },
      { stage: 'finish', kind: 'other', wall_s: 1, gpu_s: null, wall_fraction: 0.1, start_s: 9, mean_gpu_util: null },
    ], total_wall_s: 10, timed_fraction: 1, gpu_telemetry: true, gpu_count: 4, content: SENTINEL,
    concurrency: { mps: false, mps_failed: false, single_wall_s: [1, 1, 1],
      batches: [{ n: 2, wall_s: 1, all_ok: true, skipped: false, factor: 2 },
        { n: 4, wall_s: 0.5, all_ok: true, skipped: false, factor: 8 }], factor: 8 },
  }
  const intervals = [[1.2, 1.8], [1.05, 1.2], [1.4, 1.8], [1.2, 1.8], [1.01, 1.15]]
  const predictions = {
    outputs_stochastic: false, content: SENTINEL,
    predictions: MENU.map((method, i) => ({ method,
      expected_speedup_interval: { low: intervals[i][0], high: intervals[i][1] },
      outcome_vs_compute_points: [1, 2, 4].map(compute_budget => ({ compute_budget,
        predicted_outcome: 1, uncertainty: SENTINEL })) })),
    infeasible_methods: [], equivalence_metrics: ['exact equality'], paired_seed_tests: [0, 1, 2, 3, 4],
    sample_sizes: { n: 1000 }, confidence_rule: { equivalence: { kind: 'paired_median', confidence: 0.95 },
      performance: { description: SENTINEL } }, hardware_cost_basis: SENTINEL,
    timing_scope: 'whole run', minimum_worthwhile_gain: config.minimum || 1.1,
    evaluation_inputs: ['generated integers'], splits: { evaluation: [0, 1000] }, compute_budgets: [1, 2, 4],
    repetitions: 5, warmup: 'one run', scheduling_order: 'alternate', equal_outcome_target: 1,
  }
  const bounds = Object.fromEntries(MENU.map((method, i) => {
    // Whole-workload methods: p = 1, k = min(cap, concurrency factor 8). The multi-GPU row is a
    // hand-written resource-guard fixture (feasible only with superlinear evidence).
    const p = [1, 1, 0.6, 1, 0.3][i], k = [8, 4, 4, 8, 2][i]
    const kind = [0, 2, 3].includes(i) ? 'compute' : 'transfer'
    const methods = kind === 'compute' ? [MENU[0], MENU[2], MENU[3]] : [MENU[1], MENU[4]]
    const stages = profile.stages.filter(row => row.kind === kind).map(row => ({
      stage: row.stage, kind, wall_fraction: row.wall_fraction, mean_gpu_util: row.mean_gpu_util, methods,
    }))
    const k_derivation = i === 2 ? { rule: 'max(1, gpu_count)', gpu_count: 4, amdahl: 1 / ((1 - p) + p / k), cost_basis: 'equal_gpu_seconds' }
      : i === 4 ? { rule: 'fixed_cap', fixed_cap: 2 }
        : { rule: 'min(fixed_cap, concurrency factor)', fixed_cap: [8, 4, null, 8][i], factor: 8, mps: false }
    return [method, { p, k, bound: 1 / ((1 - p) + p / k), feasible: true, k_derivation, stages }]
  }))
  if (config.mutate) config.mutate({ predictions, bounds, profile })
  writeJSON(path.join(root, 'agent', 'profile-packet.json'), profile)
  writeJSON(path.join(root, 'agent', 'bounds.json'), bounds)
  if (!config.noBox) writeJSON(path.join(root, 'control', 'box.json'), config.box || { type: 'gpu_1x_a10', gpu_count: 1 })
  if (!config.noProbe) writeJSON(path.join(root, 'agent', 'results', 'probe', 'probe.json'), {
    nvidia: { gpus: Array(config.probeCount ?? 1).fill('Hermetic fixture GPU') },
  })
  const bytes = canonical(predictions)
  const frozen = path.join(root, 'control', 'seals', 'predictions-frozen.json')
  fs.mkdirSync(path.dirname(frozen), { recursive: true })
  fs.writeFileSync(frozen, bytes)
  const live = path.join(root, 'agent', 'PREDICTIONS.json')
  fs.writeFileSync(live, bytes)
  const receipt = { sha256: createHash('sha256').update(bytes).digest('hex'), path: frozen, utc: new Date().toISOString() }
  writeJSON(path.join(root, 'control', 'seals', '0001.json'), receipt)
  if (['live', 'before-profile'].includes(config.tamper)) fs.appendFileSync(live, ' ')
  if (config.tamper === 'before-profile') fs.unlinkSync(path.join(root, 'agent', 'profile-packet.json'))
  if (config.tamper === 'frozen') fs.appendFileSync(frozen, ' ')
  if (config.tamper === 'missing') fs.unlinkSync(path.join(root, 'control', 'seals', '0001.json'))
  if (config.tamper === 'latest') writeJSON(path.join(root, 'control', 'seals', '0002.json'), { ...receipt, sha256: '0'.repeat(64) })
  if (config.tamper === 'unreadable') fs.unlinkSync(frozen)
  return { profile, predictions, bounds }
}
async function execute(name, config = {}, previous) {
  const root = previous?.root || path.join(scratch, name)
  fs.mkdirSync(root, { recursive: true })
  const evidence = previous?.evidence || fixture(root, config)
  const home = path.join(root, 'fixture-home')
  fs.mkdirSync(home, { recursive: true })
  if (!config.noBox) writeJSON(path.join(home, '.cache', 'metis-serve', 'box.json'),
    config.box || { type: 'gpu_1x_a10', gpu_count: 1 })
  const args = path.join(root, 'control', 'args.json')
  const brief = path.join(root, 'brief.md')
  fs.writeFileSync(brief, 'Synthetic stage-5 contract fixture.\n')
  writeJSON(args, { run_root: root, brief, tag: 'propose-test', raid: 'propose-test',
    stub: { intake: 'PASS', reproduce: 'PASS', profile: 'PASS', seal: 'PASS', implement: 'PASS', evaluate: 'PASS', takeaways: 'PASS' } })
  // config.m5Policy: run under m5/wf_config.json with --family codex, as SCHEMAS.md "m5 model policy" prescribes.
  const policy = readJSON(path.join(ROOT, config.m5Policy ? 'm5/wf_config.json' : 'idea/config.json'))
  policy.workflow.max_concurrency = 8
  policy.workflow.runs_dir = path.join(root, 'agent', 'workflow-runs')
  const configFile = path.join(root, 'control', 'workflow-config.json')
  writeJSON(configFile, policy)
  const out = path.join(root, 'agent', `wf-${name}`)
  if (config.cacheFrom) fs.cpSync(config.cacheFrom, out, { recursive: true })
  const before = rows(path.join(root, 'calls.jsonl')).length
  const stdout = fs.openSync(path.join(root, `${name}-stdout.log`), 'w')
  const stderrFile = path.join(root, `${name}-stderr.log`)
  const stderr = fs.openSync(stderrFile, 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(ROOT, 'idea', 'wf.js'), '--script', path.join(ROOT, 'm5', 'pipeline.js'),
        '--args', args, '--out', out, '--config', configFile,
        ...(config.m5Policy ? ['--profile', 'latent_skeptic', '--family', 'codex'] : ['--disable-family', 'claude'])], { cwd: ROOT, timeout: 30000,
        stdio: ['ignore', stdout, stderr], env: { ...process.env, WF_STUB: __filename,
          HOME: home, M5_PROPOSE_ROOT: root, M5_PROPOSE_CONFIG: JSON.stringify(config), M5_RAIDS_LEDGER: path.join(scratch, 'raids.jsonl') } })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  check(`${name}: workflow completes`, () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0, fs.readFileSync(stderrFile, 'utf8').slice(-500))
    assert.ok(!readJSON(path.join(out, 'result.json')).error, JSON.stringify(readJSON(path.join(out, 'result.json')).error))
  })
  const records = rows(path.join(root, 'operator', 'signatures.jsonl'))
  const record = records.filter(row => (row.signature || row).stage === 'propose').at(-1)
  const events = rows(path.join(root, 'calls.jsonl')).slice(before)
  return { root, evidence, out, record, signature: record?.signature || record,
    calls: events.filter(row => row.event === 'start'), events }
}
function status(name, run, errorClass) {
  check(`${name}: propose ${errorClass || 'PASS'}`, () => {
    assert.equal(run.signature?.status, errorClass ? 'FAIL' : 'PASS')
    if (errorClass) { assert.equal(run.signature.error_class, errorClass); assert.equal(run.signature.exit_code, 2) }
    const result = readJSON(path.join(run.out, 'result.json'))
    assert.equal(result.stopped_at, errorClass ? 'propose' : null)
    for (const stage of ['implement', 'evaluate']) assert.equal(result.stages.find(row => row.stage === stage).status, errorClass ? 'SKIPPED' : 'PASS')
    assert.equal(result.stages.find(row => row.stage === 'takeaways').status, 'PASS')
  })
}
function facts(name, run, approvals, pass, selected = MENU[0]) {
  check(`${name}: exact facts and persisted gate`, () => {
    const actual = run.record?.facts
    assert.deepEqual(Object.keys(actual).sort(), ['method', 'expected_speedup', 'votes_approve', 'votes_total',
      'vote_share', 'gate_pass', 'tokens_known', 'gpu_busy_known'].sort())
    const { tokens_known, gpu_busy_known, ...scientific } = actual
    const interval = run.evidence.predictions.predictions.find(row => row.method === selected)?.expected_speedup_interval
    assert.deepEqual(scientific, { method: selected, expected_speedup: interval ? interval.low / 2 + interval.high / 2 : null,
      votes_approve: approvals, votes_total: 5, vote_share: approvals / 5, gate_pass: pass })
    assert.equal(typeof tokens_known, 'boolean')
    assert.equal(typeof gpu_busy_known, 'boolean')
    const gate = readJSON(path.join(run.root, 'agent', 'GATE.json'))
    for (const [key, value] of Object.entries(scientific)) assert.deepEqual(gate[key], value, key)
  })
}
function noLeak(root) {
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    assert.ok(!entry.name.includes(SENTINEL))
    const file = path.join(root, entry.name)
    assert.ok(!entry.isSymbolicLink(), 'operator symlink')
    if (entry.isDirectory()) noLeak(file)
    else assert.ok(!fs.readFileSync(file).includes(Buffer.from(SENTINEL)), `proposal leaked: ${entry.name}`)
  }
}
// Extract embedded JSON independently of whitespace and prompt prose.
function embedded(prompt, expected) {
  for (let start = prompt.indexOf('{'); start >= 0; start = prompt.indexOf('{', start + 1)) {
    let depth = 0, quoted = false, escaped = false
    for (let i = start; i < prompt.length; i++) {
      const c = prompt[i]
      if (quoted) { if (escaped) escaped = false; else if (c === '\\') escaped = true; else if (c === '"') quoted = false }
      else if (c === '"') quoted = true
      else if (c === '{') depth++
      else if (c === '}' && --depth === 0) {
        try { if (canonical(JSON.parse(prompt.slice(start, i + 1))) === canonical(expected)) return true } catch {}
        break
      }
    }
  }
  return false
}
async function main() {
  try {
    const happy = await execute('four-approvals')
    status('four-approvals', happy)
    facts('four-approvals', happy, 4, true)
    check('one proposer writes proposal; five skeptics have exact names and fresh sessions', () => {
      assert.equal(happy.calls.filter(call => call.title === 'propose').length, 1)
      const votes = happy.calls.filter(isSkeptic)
      assert.deepEqual(votes.map(call => call.title).sort(), [1, 2, 3, 4, 5].map(i => `skeptic-${i}`))
      // no sibling suffix: each ballot's own label yields its name
      for (const call of votes) assert.equal(call.name, `x-propose-test-${call.title}`)
      assert.equal(new Set(votes.map(call => call.cwd)).size, 5)
      for (const call of votes) assert.equal(call.role, 'qt-bare')
      assert.equal(happy.calls.find(call => call.title === 'propose').role, 'ls-writer')
      for (const call of happy.calls) {
        for (const key of ['session', 'sessionID', 'sessionId', 'resume', 'resumeSession']) assert.ok(!call[key], `resumed via ${key}`)
      }
      const proposal = readJSON(path.join(happy.root, 'agent', 'proposal.json'))
      assert.deepEqual(Object.keys(proposal).sort(), ['method', 'rationale', 'plan_steps', 'files_expected', 'risks'].sort())
      assert.equal(proposal.rationale, SENTINEL)
      const events = happy.events.filter(isSkeptic)
      assert.equal(events.slice(0, 5).every(row => row.event === 'start'), true, 'skeptics not concurrent')
    })
    check('ranking uses sealed midpoints, menu ties; four-GPU method excluded by one-GPU guard', () => {
      const packet = readJSON(path.join(happy.root, 'agent', 'propose-packet.json'))
      assert.deepEqual(Object.keys(packet).sort(), ['ranked_methods', 'stage_to_method', 'bounds',
        'sealed_equivalence_rule'].sort())
      assert.ok(!JSON.stringify(packet).includes(SENTINEL), 'private content leaked into packet')
      assert.deepEqual(packet.bounds, happy.evidence.bounds)
      assert.deepEqual(packet.stage_to_method, happy.evidence.profile.stages.map(row => ({
        stage: row.stage, wall_fraction: row.wall_fraction, mean_gpu_util: row.mean_gpu_util,
        methods: row.kind === 'compute' ? [MENU[0], MENU[2], MENU[3]]
          : row.kind === 'transfer' ? [MENU[1], MENU[4]] : [],
      })))
      const expected = [MENU[0], MENU[3], MENU[1], MENU[4]]
      assert.deepEqual(packet.ranked_methods.map(row => row.method), expected)
      for (const row of packet.ranked_methods) {
        assert.deepEqual(Object.keys(row).sort(), ['bounds', 'method'])
        assert.deepEqual(row.bounds, happy.evidence.bounds[row.method])
      }
      const sealed = happy.evidence.predictions
      assert.deepEqual(packet.sealed_equivalence_rule, {
        outputs_stochastic: sealed.outputs_stochastic, equivalence_metrics: sealed.equivalence_metrics,
        paired_seed_tests: sealed.paired_seed_tests, sample_sizes: sealed.sample_sizes,
        confidence_rule: sealed.confidence_rule.equivalence,
      })
    })
    check('all six calls receive same packet; skeptics receive proposal and no other ballots', () => {
      const packet = readJSON(path.join(happy.root, 'agent', 'propose-packet.json'))
      const proposal = readJSON(path.join(happy.root, 'agent', 'proposal.json'))
      for (const call of happy.calls) {
        assert.ok(embedded(call.prompt, packet), `${call.title}: packet absent or modified`)
        assert.ok(!call.prompt.includes(path.join(happy.root, 'control')), 'control path in evidence')
        assert.ok(!call.prompt.includes(path.join(happy.root, 'agent', 'intake')), 'raw intake supplied')
        if (isSkeptic(call)) {
          assert.ok(embedded(call.prompt, proposal), 'proposal absent or modified')
          assert.ok(!/"vote"\s*:\s*"(?:approve|reject|abstain)"/.test(call.prompt), 'another ballot supplied')
          const number = ballotNumber(call.title)
          assert.match(call.prompt, new RegExp(`(?:ballot|skeptic|vote)[^\\n]{0,30}\\b${number}\\b`, 'i'))
        }
      }
    })
    check('votes persist exact valid ballots and all seven fixed reason codes', () => {
      const directory = path.join(happy.root, 'agent', 'votes')
      assert.deepEqual(fs.readdirSync(directory).sort(), ['1.json', '2.json', '3.json', '4.json', '5.json'])
      for (let i = 1; i <= 5; i++) assert.deepEqual(readJSON(path.join(directory, `${i}.json`)), i === 5 ? ballot('reject', REASONS) : ballot())
    })
    check('proposal sentinel absent throughout R/operator', () => noLeak(path.join(happy.root, 'operator')))
    const fresh = await execute('fresh-with-cached-sessions', { cacheFrom: happy.out })
    status('fresh-with-cached-sessions', fresh)
    check('cached proposer and skeptic sessions never reused in new run', () => {
      assert.equal(fresh.calls.length, 6, 'fresh calls bypass completed cache entries')
      for (const call of fresh.calls) assert.ok(!call.session, 'runner received cached session')
    })
    const gateBytes = fs.readFileSync(path.join(happy.root, 'agent', 'GATE.json'))
    const voteBytes = [1, 2, 3, 4, 5].map(i => fs.readFileSync(path.join(happy.root, 'agent', 'votes', `${i}.json`)))
    const rerun = await execute('no-revote', {}, happy)
    status('no-revote', rerun, 'other')
    check('existing gate prohibits proposer and ballots; preserves gate and votes', () => {
      assert.equal(rerun.calls.length, 0)
      assert.deepEqual(fs.readFileSync(path.join(happy.root, 'agent', 'GATE.json')), gateBytes)
      for (let i = 1; i <= 5; i++) assert.deepEqual(fs.readFileSync(path.join(happy.root, 'agent', 'votes', `${i}.json`)), voteBytes[i - 1])
    })
    for (const [name, votes, approvals, pass] of [
      ['three-approvals', [ballot(), ballot(), ballot(), ballot('reject'), ballot('abstain')], 3, false],
      ['one-missing', [ballot(), ballot(), ballot(), ballot(), null], 4, true],
      ['missing-and-invalid', [ballot(), ballot(), ballot(), null, ballot('approve', ['invented_code'])], 3, false],
      ['invalid-enum', [ballot(), ballot(), ballot(), ballot(), ballot('yes')], 4, true],
      ['invalid-extra-key', [ballot(), ballot(), ballot(), ballot(), { ...ballot(), extra: true }], 4, true],
      ['invalid-reasons', [ballot(), ballot(), ballot(), ballot(), { vote: 'approve', reason_codes: 'other' }], 4, true],
    ]) {
      const run = await execute(name, { votes })
      status(name, run, pass ? undefined : 'numeric')
      facts(name, run, approvals, pass)
      if (name === 'three-approvals') {
        const repeated = await execute('no-revote-after-failure', {}, run)
        status('no-revote-after-failure', repeated, 'other')
        check('failed gate cannot request replacement votes', () => assert.equal(repeated.calls.length, 0))
      }
      check(`${name}: exactly five calls, no repairs or replacements, invalid votes null`, () => {
        assert.equal(run.calls.filter(call => call.title === 'propose').length, 1)
        assert.equal(run.calls.filter(isSkeptic).length, 5)
        assert.equal(run.calls.length, 6)
        for (let i = 0; i < 5; i++) {
          const value = votes[i]
          const valid = value && Object.keys(value).length === 2 && ['approve', 'reject', 'abstain'].includes(value.vote)
            && Array.isArray(value.reason_codes) && value.reason_codes.every(code => REASONS.includes(code))
          assert.deepEqual(readJSON(path.join(run.root, 'agent', 'votes', `${i + 1}.json`)), valid ? value : null)
        }
      })
    }
    for (const tamper of ['live', 'frozen', 'missing', 'latest', 'unreadable', 'before-profile']) {
      const run = await execute(`seal-${tamper}`, { tamper })
      status(`seal-${tamper}`, run, 'other')
      check(`seal-${tamper}: no model calls; initial facts retain denominator five`, () => {
        assert.equal(run.calls.length, 0)
        for (const [key, value] of Object.entries({ method: 'none', expected_speedup: null,
          votes_approve: 0, votes_total: 5, vote_share: 0, gate_pass: false })) assert.deepEqual(run.record?.facts?.[key], value, key)
      })
    }
    for (const [name, config] of [
      ['allocation-limits-probe', { box: { type: 'gpu_8x_a10', gpu_count: 1 }, probeCount: 4 }],
      ['probe-limits-allocation', { box: { type: 'gpu_4x_a10', gpu_count: 4 }, probeCount: 1 }],
      ['allocation-type-fallback', { box: { type: 'gpu_1x_a10' }, probeCount: 4 }],
    ]) {
      const run = await execute(name, config)
      status(name, run)
      check(`${name}: smaller inventory excludes multi-GPU`, () => {
        const packet = readJSON(path.join(run.root, 'agent', 'propose-packet.json'))
        assert.ok(!Object.hasOwn(packet, 'resource_guards'))
        assert.ok(packet.ranked_methods.every(row => row.method !== 'multi-GPU'))
      })
    }
    const multi = await execute('four-gpu-feasible', { box: { type: 'gpu_4x_a10', gpu_count: 4 }, probeCount: 4, method: 'multi-GPU' })
    status('four-gpu-feasible', multi)
    facts('four-gpu-feasible', multi, 4, true, 'multi-GPU')
    check('multi-GPU ranks first with bound factor matching four required GPUs', () => {
      const row = readJSON(path.join(multi.root, 'agent', 'propose-packet.json')).ranked_methods[0]
      assert.equal(row.method, 'multi-GPU')
      assert.equal(row.bounds.k, 4)
      assert.equal(row.bounds.k_derivation.gpu_count, 4)
    })
    for (const [name, config] of [
      ['no-allocation', { noBox: true }], ['no-probe', { noProbe: true }], ['zero-probe', { probeCount: 0 }],
      ['zero-allocation', { box: { type: 'gpu_4x_a10', gpu_count: 0 } }],
    ]) {
      const run = await execute(name, config)
      status(name, run, 'numeric')
      check(`${name}: no safe method means no model calls`, () => assert.equal(run.calls.length, 0))
    }
    const worthwhile = await execute('below-worthwhile', { minimum: 1.85 })
    status('below-worthwhile', worthwhile, 'numeric')
    facts('below-worthwhile', worthwhile, 4, false)
    for (const [name, config] of [
      ['missing-proposal', { missingProposal: true }],
      ['unsafe-selection', { method: 'multi-GPU' }],
      ['malformed-proposal', { proposal: { method: MENU[0], rationale: 'fixture', plan_steps: [], files_expected: ['x'], risks: [] } }],
    ]) {
      const run = await execute(name, config)
      status(name, run, 'parse')
      check(`${name}: one proposer, no skeptic calls`, () => assert.deepEqual(run.calls.map(call => call.title), ['propose']))
    }
    for (const [name, mutate] of [
      ['duplicate-method', ({ predictions }) => predictions.predictions.push(predictions.predictions[0])],
      ['unknown-method', ({ predictions }) => { predictions.predictions[0].method = 'invented' }],
      ['invalid-interval', ({ predictions }) => { predictions.predictions[0].expected_speedup_interval.low = '1.2' }],
    ]) {
      const run = await execute(name, { mutate })
      status(name, run, 'parse')
      check(`${name}: malformed sealed input rejected before agents`, () => assert.equal(run.calls.length, 0))
    }
    // SCHEMAS.md "m5 model policy": run under m5/wf_config.json with --family codex.
    const approveAll = [ballot(), ballot(), ballot(), ballot(), ballot()]
    const routed = await execute('policy-routing', { m5Policy: true, votes: approveAll })
    status('policy-routing', routed)
    facts('policy-routing', routed, 5, true)
    check('policy-routing: ballots 1-3 and proposer on codex, ballots 4-5 on claude/sonnet, names without suffix', () => {
      assert.equal(routed.calls.length, 6)
      const skeptics = routed.calls.filter(isSkeptic).sort((a, b) => ballotNumber(a.title) - ballotNumber(b.title))
      assert.deepEqual(skeptics.map(call => call.title), [1, 2, 3, 4, 5].map(i => `skeptic-${i}`))
      assert.deepEqual(skeptics.map(call => call.name), [1, 2, 3, 4, 5].map(i => `x-propose-test-skeptic-${i}`))
      for (const call of skeptics.slice(0, 3)) assert.equal(familyOf(call.model), 'codex', `${call.title}: ${call.model}`)
      for (const call of skeptics.slice(3)) assert.equal(call.model, 'claude/sonnet', call.title)
      const proposer = routed.calls.filter(call => call.title === 'propose')
      assert.equal(proposer.length, 1)
      assert.equal(familyOf(proposer[0].model), 'codex', proposer[0].model)
    })
    const refused = await execute('policy-claude-refusal', { m5Policy: true,
      votes: [ballot(), ballot(), ballot(), ballot(), ballot('reject')], failures: { 'skeptic-4': { claude: 'refusal' } } })
    status('policy-claude-refusal', refused, 'numeric')
    facts('policy-claude-refusal', refused, 3, false)
    check('policy-claude-refusal: refused ballot written as null, counted against approval, not handed over', () => {
      const ballot4 = refused.calls.filter(call => call.title === 'skeptic-4')
      assert.deepEqual(ballot4.map(call => call.model), ['claude/sonnet'], 'refusal handed to another family')
      assert.equal(refused.calls.length, 6)
      assert.equal(readJSON(path.join(refused.root, 'agent', 'votes', '4.json')), null)
      for (const i of [1, 2, 3]) assert.deepEqual(readJSON(path.join(refused.root, 'agent', 'votes', `${i}.json`)), ballot())
      assert.deepEqual(readJSON(path.join(refused.root, 'agent', 'votes', '5.json')), ballot('reject'))
    })
    const handed = await execute('policy-claude-transport', { m5Policy: true, votes: approveAll,
      failures: { 'skeptic-5': { claude: 'transport' } }, familyVotes: { 'skeptic-5': { codex: ballot('approve', ['other']) } } })
    status('policy-claude-transport', handed)
    facts('policy-claude-transport', handed, 5, true)
    check('policy-claude-transport: transport failure on a claude ballot hands over to codex', () => {
      const ballot5 = handed.calls.filter(call => call.title === 'skeptic-5').sort((a, b) => a.time - b.time)
      assert.deepEqual(ballot5.map(call => familyOf(call.model)), ['claude', 'codex'])
      assert.equal(ballot5[0].model, 'claude/sonnet')
      assert.deepEqual(ballot5.map(call => call.name), ['x-propose-test-skeptic-5', 'x-propose-test-skeptic-5-fb'])
      assert.equal(handed.calls.length, 7)
      assert.deepEqual(readJSON(path.join(handed.root, 'agent', 'votes', '5.json')), ballot('approve', ['other']))
    })
  } catch (error) {
    failures++
    console.log(`FAIL test harness: ${error.stack}`)
  } finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
