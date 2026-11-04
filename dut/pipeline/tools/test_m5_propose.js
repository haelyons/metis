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
// Recorded public runs used read-only as regression fixtures; files are copied into scratch.
const RUNS = path.resolve(ROOT, '..', '..', 'experiments', 'shakedown-m5')
const OPENMM_RUN1 = path.resolve(ROOT, '..', '..', 'experiments', 'positive-openmm', 'run1')
const runDir = run => path.isAbsolute(run) ? run : path.join(RUNS, run)
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
const INFINITE_PLACEHOLDER = 424242.5
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
const recordedBallots = run => [1, 2, 3, 4, 5].map(i => readJSON(path.join(RUNS, run, 'agent', 'votes', `${i}.json`)))
const recordedProposal = run => readJSON(path.join(RUNS, run, 'agent', 'proposal.json'))
const recordedBox = run => readJSON(path.join(runDir(run), 'control', 'box.json'))
// Replays propose on a recorded run's inputs under a fresh seal of the recorded prediction bytes.
// `concurrency`, when given, replaces only the copied profile packet's concurrency record.
function replayFixture(root, run, concurrency) {
  const from = runDir(run)
  const copy = relative => {
    fs.mkdirSync(path.dirname(path.join(root, relative)), { recursive: true })
    fs.copyFileSync(path.join(from, relative), path.join(root, relative))
  }
  for (const relative of ['agent/PREDICTIONS.json', 'agent/bounds.json', 'control/box.json', 'agent/results/probe/probe.json']) copy(relative)
  if (fs.existsSync(path.join(from, 'agent', 'profile-packet.json'))) copy('agent/profile-packet.json')
  else {
    // Rebuild a profile packet carrying the recorded stage mapping (wall fractions, utilisation, kinds).
    const recorded = readJSON(path.join(from, 'agent', 'propose-packet.json'))
    const stages = recorded.stage_to_method.map(row => ({ stage: row.stage,
      kind: row.methods.includes('pipelining') ? 'transfer' : row.methods.includes('multi-GPU') ? 'compute' : 'other',
      wall_s: row.wall_fraction * 100, gpu_s: null, wall_fraction: row.wall_fraction, start_s: null, mean_gpu_util: row.mean_gpu_util }))
    writeJSON(path.join(root, 'agent', 'profile-packet.json'), { stages, total_wall_s: 100,
      timed_fraction: Math.min(1, stages.reduce((sum, row) => sum + row.wall_fraction, 0)), gpu_telemetry: true, concurrency: null })
  }
  if (concurrency) {
    const file = path.join(root, 'agent', 'profile-packet.json')
    writeJSON(file, { ...readJSON(file), concurrency })
  }
  const live = path.join(root, 'agent', 'PREDICTIONS.json')
  const bytes = fs.readFileSync(live)
  const frozen = path.join(root, 'control', 'seals', 'predictions-frozen.json')
  fs.mkdirSync(path.dirname(frozen), { recursive: true })
  fs.writeFileSync(frozen, bytes)
  writeJSON(path.join(root, 'control', 'seals', '0001.json'), { sha256: createHash('sha256').update(bytes).digest('hex'),
    path: frozen, utc: new Date().toISOString() })
  return { predictions: readJSON(live), bounds: readJSON(path.join(root, 'agent', 'bounds.json')),
    profile: readJSON(path.join(root, 'agent', 'profile-packet.json')) }
}
function fixture(root, config) {
  if (config.replay) return replayFixture(root, config.replay, config.replayConcurrency)
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
    baseline_invocation_s: { seconds: 0.01, source: 'fixture: one baseline equivalence invocation, 0.01 s' },
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
  // JSON cannot spell a non-finite number; 1e999 parses as Infinity.
  if (config.infiniteFactor) fs.writeFileSync(path.join(root, 'agent', 'profile-packet.json'),
    fs.readFileSync(path.join(root, 'agent', 'profile-packet.json'), 'utf8').split(`"factor": ${INFINITE_PLACEHOLDER}`).join('"factor": 1e999'))
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
        ...(config.m5Policy ? ['--profile', 'latent_skeptic', '--family', 'codex'] : ['--disable-family', 'claude'])], { cwd: ROOT, timeout: 600000,
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
const FACT_KEYS = ['method', 'expected_speedup', 'votes_approve', 'votes_total', 'vote_share', 'gate_pass',
  'votes_reject', 'votes_abstain', 'outcome', 'tokens_known', 'gpu_busy_known']
// Ballot counts are { approve, reject, abstain }; null ballots are the remainder of five.
// Outcome once counted: approved exactly when the gate passes; rejected with two or more rejections/nulls;
// otherwise conditions_unmet (SCHEMAS.md, propose facts).
function facts(name, run, counts, pass, selected = MENU[0]) {
  const { approve = 0, reject = 0, abstain = 0 } = counts
  const nulls = 5 - approve - reject - abstain
  const outcome = pass ? 'approved' : reject + nulls >= 2 ? 'rejected' : 'conditions_unmet'
  check(`${name}: exact facts (outcome ${outcome}) and persisted gate`, () => {
    const actual = run.record?.facts
    assert.deepEqual(Object.keys(actual).sort(), [...FACT_KEYS].sort())
    const { tokens_known, gpu_busy_known, expected_speedup, ...scientific } = actual
    const interval = run.evidence.predictions.predictions.find(row => row.method === selected)?.expected_speedup_interval
    if (interval) assert.ok(Math.abs(expected_speedup - (interval.low / 2 + interval.high / 2)) <= 1e-12, `expected_speedup ${expected_speedup}`)
    else assert.equal(expected_speedup, null)
    scientific.expected_speedup = expected_speedup
    assert.deepEqual(scientific, { method: selected, expected_speedup,
      votes_approve: approve, votes_total: 5, vote_share: approve / 5, gate_pass: pass,
      votes_reject: reject, votes_abstain: abstain, outcome })
    assert.equal(typeof tokens_known, 'boolean')
    assert.equal(typeof gpu_busy_known, 'boolean')
    const gate = readJSON(path.join(run.root, 'agent', 'GATE.json'))
    for (const [key, value] of Object.entries(scientific)) assert.deepEqual(gate[key], value, key)
  })
  check(`${name}: null ballots = 5 - approve - reject - abstain = ${nulls}`, () => {
    const ballots = [1, 2, 3, 4, 5].map(i => readJSON(path.join(run.root, 'agent', 'votes', `${i}.json`)))
    assert.equal(ballots.filter(value => value === null).length, nulls)
    const f = run.record.facts
    assert.equal(5 - f.votes_approve - f.votes_reject - f.votes_abstain, nulls)
    for (const [vote, count] of [['approve', approve], ['reject', reject], ['abstain', abstain]])
      assert.equal(ballots.filter(value => value?.vote === vote).length, count, vote)
  })
}
// Stages that stop before ballots are counted emit the new facts at their initial values, outcome null.
function uncounted(name, run) {
  check(`${name}: stopped before counting; votes 0/0/0 and outcome null`, () => {
    const actual = run.record?.facts
    for (const key of FACT_KEYS) assert.ok(Object.hasOwn(actual, key), `missing ${key}`)
    for (const [key, value] of Object.entries({ votes_approve: 0, votes_total: 5, vote_share: 0, gate_pass: false,
      votes_reject: 0, votes_abstain: 0, outcome: null })) assert.deepEqual(actual[key], value, key)
  })
}
// SCHEMAS.md propose: "When no feasible resource-safe method remains ... propose makes no model calls, writes
// `A/propose-packet.json` and `A/GATE.json` as usual, and keeps `method="none"`, `expected_speedup=null` and
// `gate_pass=false`."
const FINDING = 'Finding: negative. No menu method has measured headroom of at least 1.05 on this hardware.'
const findingLines = root => fs.readFileSync(path.join(root, 'operator', 'OPERATOR_TAKEAWAY.md'), 'utf8')
  .split('\n').filter(line => line.trim() === FINDING).length
function noFinding(name, run) {
  check(`${name}: OPERATOR_TAKEAWAY.md has no Finding line`, () => assert.equal(findingLines(run.root), 0))
}
// Whole-workload bounds with a measured factor of 1.02 (k = min(cap, 1.02) < 1.05); every other menu method
// except `keep` infeasible. Predictions keep only `keep`; every other method is listed as infeasible.
function absence(keep = [], factor = 1.02) {
  return ({ predictions, bounds, profile }) => {
    profile.concurrency.factor = factor
    profile.concurrency.batches = profile.concurrency.batches.map(row => ({ ...row, factor: Number.isFinite(factor) ? Math.min(factor, row.factor) : factor }))
    for (const method of MENU) {
      if (keep.includes(method)) continue
      const row = bounds[method]
      // k_derivation.factor is null when the factor is unavailable (null or the non-finite placeholder).
      if (row.k_derivation.rule.startsWith('min(')) {
        row.k = 1.02; row.bound = 1.02
        row.k_derivation.factor = factor === null || factor === INFINITE_PLACEHOLDER ? null : factor
      }
      else if (method === 'pipelining') { row.p = 0.04; row.bound = 1 / (0.96 + 0.02) }
      else { row.k = 1; row.bound = 0.6 }
      row.feasible = false
    }
    predictions.predictions = predictions.predictions.filter(row => keep.includes(row.method))
    predictions.infeasible_methods = MENU.filter(method => !keep.includes(method))
      .map(method => ({ method, reason: 'Bound is below 1.05.' }))
  }
}
function absenceArtifacts(name, run) {
  check(`${name}: propose-packet.json written with no ranked methods; GATE.json written`, () => {
    const packet = readJSON(path.join(run.root, 'agent', 'propose-packet.json'))
    assert.deepEqual(Object.keys(packet).sort(), ['ranked_methods', 'stage_to_method', 'bounds', 'sealed_equivalence_rule'].sort())
    assert.deepEqual(packet.ranked_methods, [])
    assert.deepEqual(packet.bounds, run.evidence.bounds)
    const gate = readJSON(path.join(run.root, 'agent', 'GATE.json'))
    for (const key of ['method', 'expected_speedup', 'gate_pass', 'outcome'])
      assert.deepEqual(gate[key], run.record.facts[key], key)
  })
  check(`${name}: no proposer or skeptic calls`, () => assert.equal(run.calls.length, 0))
}
// Measured negative finding: PASS, outcome no_feasible_method, implement/evaluate SKIPPED with null facts,
// takeaways runs, stop point propose, fixed Finding line in OPERATOR_TAKEAWAY.md.
function negativeFinding(name, run) {
  check(`${name}: measured absence PASSes with outcome no_feasible_method and all ballot counts 0`, () => {
    assert.equal(run.signature?.status, 'PASS')
    const { tokens_known, gpu_busy_known, ...scientific } = run.record.facts
    assert.deepEqual(Object.keys(run.record.facts).sort(), [...FACT_KEYS].sort())
    assert.deepEqual(scientific, { method: 'none', expected_speedup: null, votes_approve: 0, votes_total: 5,
      vote_share: 0, gate_pass: false, votes_reject: 0, votes_abstain: 0, outcome: 'no_feasible_method' })
  })
  absenceArtifacts(name, run)
  check(`${name}: implement and evaluate SKIPPED with null facts; takeaways runs; stopped at propose`, () => {
    const result = readJSON(path.join(run.out, 'result.json'))
    assert.equal(result.stopped_at, 'propose')
    const statuses = Object.fromEntries(result.stages.map(row => [row.stage, row.status]))
    assert.deepEqual([statuses.propose, statuses.implement, statuses.evaluate, statuses.takeaways], ['PASS', 'SKIPPED', 'SKIPPED', 'PASS'])
    const records = rows(path.join(run.root, 'operator', 'signatures.jsonl'))
    for (const stage of ['implement', 'evaluate']) {
      const record = records.filter(row => (row.signature || row).stage === stage).at(-1)
      assert.equal((record.signature || record).status, 'SKIPPED', stage)
      assert.ok(record.facts && Object.keys(record.facts).length, `${stage}: no facts`)
      for (const [key, value] of Object.entries(record.facts)) assert.equal(value, null, `${stage}.${key}`)
    }
    const takeaways = records.filter(row => (row.signature || row).stage === 'takeaways').at(-1)
    assert.equal((takeaways.signature || takeaways).status, 'PASS')
  })
  check(`${name}: OPERATOR_TAKEAWAY.md has the fixed Finding line exactly once`, () => assert.equal(findingLines(run.root), 1))
}
// Unmeasured absence: FAIL numeric (exit 2), outcome null, no model calls, downstream skipped as for any failure.
function unmeasured(name, run) {
  status(name, run, 'numeric')
  uncounted(name, run)
  check(`${name}: method none, expected_speedup null`, () => {
    assert.equal(run.record.facts.method, 'none')
    assert.equal(run.record.facts.expected_speedup, null)
  })
  absenceArtifacts(name, run)
  noFinding(name, run)
}
// Phrases the skeptic prompt must carry (SCHEMAS.md "Ballot meanings"), matched by meaning, not wording.
function ballotMeanings(prompt) {
  const near = (a, b, span = 240) => new RegExp(`(?:${a})[\\s\\S]{0,${span}}(?:${b})|(?:${b})[\\s\\S]{0,${span}}(?:${a})`, 'i').test(prompt)
  assert.ok(near('\\breject', 'defect|fail'), 'reject not described as naming a defect that makes the method fail')
  assert.ok(near('\\babstain', 'insufficient|not enough|cannot (?:be )?judged?|unable to judge|too little'),
    'abstain not described as insufficient evidence to judge')
  assert.ok(near('\\bapprove', 'no defect|adequate|sufficient'), 'approve not described as no defect with adequate evidence')
  assert.ok(near('(?:missing|weak)[\\s\\S]{0,40}evidence', '\\babstain'), 'missing or weak evidence not tied to abstain')
  assert.ok(/abstain[\s\S]{0,80}(?:not|never|rather than|instead of)\s+(?:to\s+|a\s+)?reject|(?:not|never|do not|don't)\s+reject[\s\S]{0,160}(?:missing|weak)[\s\S]{0,40}evidence/i.test(prompt),
    'prompt does not say missing or weak evidence warrants abstain, not reject')
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
    facts('four-approvals', happy, { approve: 4, reject: 1 }, true)
    noFinding('four-approvals', happy)
    check('every skeptic prompt states the three ballot meanings; missing or weak evidence warrants abstain, not reject', () => {
      const skeptics = happy.calls.filter(isSkeptic)
      assert.equal(skeptics.length, 5)
      for (const call of skeptics) ballotMeanings(call.prompt)
    })
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
    uncounted('no-revote', rerun)
    check('existing gate prohibits proposer and ballots; preserves gate and votes', () => {
      assert.equal(rerun.calls.length, 0)
      assert.deepEqual(fs.readFileSync(path.join(happy.root, 'agent', 'GATE.json')), gateBytes)
      for (let i = 1; i <= 5; i++) assert.deepEqual(fs.readFileSync(path.join(happy.root, 'agent', 'votes', `${i}.json`)), voteBytes[i - 1])
    })
    // Gate ballot condition: at most one ballot that is a rejection or null; abstentions never count
    // against it, no minimum number of approvals, and reason codes never reclassify a ballot.
    const A = ballot(), R = ballot('reject', ['exceeds_bound']), AB = ballot('abstain', ['weak_profile_evidence'])
    const weakReject = ballot('reject', ['weak_profile_evidence'])
    const allFamilies = kind => ({ codex: kind, opencode: kind, claude: kind, cursor: kind })
    for (const [name, votes, counts, pass, extra = {}] of [
      ['three-approvals-reject-abstain', [A, A, A, ballot('reject'), ballot('abstain')], { approve: 3, reject: 1, abstain: 1 }, true],
      ['five-abstentions', [AB, AB, AB, AB, ballot('abstain')], { abstain: 5 }, true],
      ['one-reject-four-abstain', [R, AB, AB, AB, AB], { reject: 1, abstain: 4 }, true],
      ['one-missing-four-abstain', [null, AB, AB, AB, AB], { abstain: 4 }, true],
      ['one-missing', [A, A, A, A, null], { approve: 4 }, true],
      ['two-rejections', [A, A, A, R, ballot('reject', [])], { approve: 3, reject: 2 }, false],
      ['reject-and-missing', [A, A, AB, R, null], { approve: 2, reject: 1, abstain: 1 }, false],
      ['missing-and-invalid', [A, A, A, null, ballot('approve', ['invented_code'])], { approve: 3 }, false],
      ['weak-evidence-rejections', [A, A, AB, weakReject, weakReject], { approve: 2, reject: 2, abstain: 1 }, false],
      ['codes-do-not-reclassify', [ballot('abstain', ['exceeds_bound', 'changes_method']), ballot('abstain', ['equivalence_risk']),
        ballot('approve', ['weak_profile_evidence']), A, weakReject], { approve: 2, reject: 1, abstain: 2 }, true],
      ['invalid-enum', [A, A, A, A, ballot('yes')], { approve: 4 }, true],
      ['invalid-extra-key', [A, A, A, A, { ...A, extra: true }], { approve: 4 }, true],
      ['invalid-reasons', [A, A, A, A, { vote: 'approve', reason_codes: 'other' }], { approve: 4 }, true],
      ['one-failed-four-abstain', [A, AB, AB, AB, AB], { abstain: 4 }, true, { failures: { 'skeptic-1': allFamilies('transport') } }],
      ['two-failed', [A, A, A, A, A], { approve: 3 }, false,
        { failures: { 'skeptic-1': allFamilies('transport'), 'skeptic-2': allFamilies('transport') } }],
      ['failed-and-invalid', [A, AB, AB, ballot('abstain', ['invented_code']), A], { approve: 1, abstain: 2 }, false,
        { failures: { 'skeptic-1': allFamilies('transport') } }],
    ]) {
      const run = await execute(name, { votes, ...extra })
      status(name, run, pass ? undefined : 'numeric')
      facts(name, run, counts, pass)
      if (name === 'two-rejections') {
        noFinding(name, run)
        const repeated = await execute('no-revote-after-failure', {}, run)
        status('no-revote-after-failure', repeated, 'other')
        uncounted('no-revote-after-failure', repeated)
        check('failed gate cannot request replacement votes', () => assert.equal(repeated.calls.length, 0))
      }
      check(`${name}: one proposer, five ballots without repairs or replacements, failed/invalid votes null`, () => {
        assert.equal(run.calls.filter(call => call.title === 'propose').length, 1)
        // Transport failures may hand over along the family chain; the ballot set is still exactly five labels.
        assert.deepEqual([...new Set(run.calls.filter(isSkeptic).map(call => call.title))].sort(), [1, 2, 3, 4, 5].map(i => `skeptic-${i}`))
        if (!extra.failures) assert.equal(run.calls.length, 6)
        for (let i = 0; i < 5; i++) {
          const value = votes[i]
          const failed = Object.hasOwn(extra.failures || {}, `skeptic-${i + 1}`)
          const valid = !failed && value && Object.keys(value).length === 2 && ['approve', 'reject', 'abstain'].includes(value.vote)
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
      uncounted(`seal-${tamper}`, run)
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
    facts('four-gpu-feasible', multi, { approve: 4, reject: 1 }, true, 'multi-GPU')
    check('multi-GPU ranks first with bound factor matching four required GPUs', () => {
      const row = readJSON(path.join(multi.root, 'agent', 'propose-packet.json')).ranked_methods[0]
      assert.equal(row.method, 'multi-GPU')
      assert.equal(row.bounds.k, 4)
      assert.equal(row.bounds.k_derivation.gpu_count, 4)
    })
    // SCHEMAS.md propose: "The absence is a negative finding exactly when it rests on measurements: the profile
    // packet's `concurrency.factor` is a finite number; its MPS state is verified, meaning `concurrency.mps` is
    // true, or `concurrency.mps` and `concurrency.mps_failed` are both false (MPS absent from the box); and both
    // GPU inventories used by the resource guards (box and probe) are available with at least one GPU each. Then
    // the stage PASSes with `outcome="no_feasible_method"`; implement and evaluate are SKIPPED with null facts,
    // takeaways runs, and the run's stop point is propose."
    // The base fixture records MPS absent (mps=false, mps_failed=false), one box GPU and one probe GPU.
    const mpsState = (mps, mps_failed) => ({ profile }) => { profile.concurrency.mps = mps; profile.concurrency.mps_failed = mps_failed }
    const compose = (...steps) => evidence => steps.forEach(step => step(evidence))
    const measured = [
      ['measured-mps-verified', { mutate: compose(absence(), mpsState(true, false)) }],
      ['measured-mps-absent', { mutate: compose(absence(), mpsState(false, false)) }],
      ['measured-zero-predictions', { mutate: absence() }],
      ['measured-multi-gpu-only-on-one-gpu', { mutate: absence(['multi-GPU']) }],
      ['measured-mps-verified-multi-gpu-only-on-one-gpu', { mutate: compose(absence(['multi-GPU']), mpsState(true, false)) }],
      ['measured-factor-below-one', { mutate: absence([], 0.8) }],
      ['measured-zero-predictions-type-fallback', { mutate: absence(), box: { type: 'gpu_1x_a10' } }],
    ]
    let negative
    for (const [name, config] of measured) {
      const run = await execute(name, config)
      negativeFinding(name, run)
      negative = negative || run
    }
    check('measured-multi-gpu-only-on-one-gpu: the sealed multi-GPU method is feasible but fails the GPU guard', () => {
      const bounds = readJSON(path.join(scratch, 'measured-multi-gpu-only-on-one-gpu', 'agent', 'bounds.json'))
      assert.equal(bounds['multi-GPU'].feasible, true)
      assert.ok(bounds['multi-GPU'].bound >= 1.05 && bounds['multi-GPU'].k > 1)
    })
    // "Its presence prevents another proposal/vote round in the same run (fails with `other`)."
    const afterNegative = await execute('no-revote-after-negative-finding', {}, negative)
    status('no-revote-after-negative-finding', afterNegative, 'other')
    uncounted('no-revote-after-negative-finding', afterNegative)
    check('no-revote-after-negative-finding: no model calls', () => assert.equal(afterNegative.calls.length, 0))
    check('measured fixtures carry the intended MPS state, a finite factor below 1.05 and one GPU in each inventory', () => {
      for (const [name, mps] of [['measured-mps-verified', true], ['measured-mps-absent', false]]) {
        const { concurrency } = readJSON(path.join(scratch, name, 'agent', 'profile-packet.json'))
        assert.deepEqual([concurrency.mps, concurrency.mps_failed], [mps, false], name)
        assert.ok(Number.isFinite(concurrency.factor) && concurrency.factor < 1.05, name)
        assert.equal(readJSON(path.join(scratch, name, 'control', 'box.json')).gpu_count, 1, name)
        assert.equal(readJSON(path.join(scratch, name, 'agent', 'results', 'probe', 'probe.json')).nvidia.gpus.length, 1, name)
      }
    })
    // "Otherwise (concurrency missing, null or not finite; `concurrency.mps_failed` true, meaning MPS exists on
    // the box but the measurement could not use it; or either GPU inventory unavailable or reporting zero GPUs)
    // the absence reflects missing measurements: the stage FAILs with `numeric` (exit 2) as before and `outcome`
    // stays null."
    const withoutConcurrency = ({ profile }) => { delete profile.concurrency }
    const nullConcurrency = ({ profile }) => { profile.concurrency = null }
    for (const [name, config] of [
      ['unmeasured-mps-failed', { mutate: compose(absence(), mpsState(false, true)) }],
      ['unmeasured-mps-failed-multi-gpu-only', { mutate: compose(absence(['multi-GPU']), mpsState(false, true)) }],
      ['unmeasured-zero-box-gpus', { mutate: absence(), box: { type: 'gpu_1x_a10', gpu_count: 0 } }],
      ['unmeasured-zero-probe-gpus', { mutate: absence(), probeCount: 0 }],
      ['unmeasured-mps-verified-zero-box-gpus', { mutate: compose(absence(), mpsState(true, false)), box: { type: 'gpu_1x_a10', gpu_count: 0 } }],
      ['unmeasured-mps-verified-zero-probe-gpus', { mutate: compose(absence(), mpsState(true, false)), probeCount: 0 }],
      // Formerly treated as measured: every predicted method feasible, but a zero-GPU inventory fails every guard.
      ['unmeasured-zero-probe', { probeCount: 0 }],
      ['unmeasured-zero-allocation', { box: { type: 'gpu_4x_a10', gpu_count: 0 } }],
      ['unmeasured-concurrency-missing', { mutate: compose(absence([], null), withoutConcurrency) }],
      ['unmeasured-concurrency-null', { mutate: compose(absence([], null), nullConcurrency) }],
      ['unmeasured-factor-null', { mutate: absence([], null) }],
      ['unmeasured-factor-infinite', { mutate: absence([], INFINITE_PLACEHOLDER), infiniteFactor: true }],
      ['unmeasured-multi-gpu-only-concurrency-missing', { mutate: compose(absence(['multi-GPU'], null), withoutConcurrency) }],
      ['unmeasured-zero-predictions-no-allocation', { mutate: absence(), noBox: true }],
      ['unmeasured-zero-predictions-no-probe', { mutate: absence(), noProbe: true }],
      ['unmeasured-zero-predictions-untyped-allocation', { mutate: absence(), box: { type: 'cpu_only' } }],
      ['no-allocation', { noBox: true }], ['no-probe', { noProbe: true }],
    ]) {
      const run = await execute(name, config)
      unmeasured(name, run)
    }
    check('measured-factor-below-one / unmeasured-factor-infinite fixtures carry the intended factor', () => {
      const below = readJSON(path.join(scratch, 'measured-factor-below-one', 'agent', 'profile-packet.json'))
      assert.equal(below.concurrency.factor, 0.8)
      const infinite = readJSON(path.join(scratch, 'unmeasured-factor-infinite', 'agent', 'profile-packet.json'))
      assert.equal(infinite.concurrency.factor, Infinity)
      const failed = readJSON(path.join(scratch, 'unmeasured-mps-failed', 'agent', 'profile-packet.json')).concurrency
      assert.deepEqual([failed.mps, failed.mps_failed], [false, true])
      assert.ok(Number.isFinite(failed.factor) && failed.factor < 1.05)
      assert.equal(readJSON(path.join(scratch, 'unmeasured-zero-box-gpus', 'control', 'box.json')).gpu_count, 0)
      assert.equal(readJSON(path.join(scratch, 'unmeasured-zero-probe-gpus', 'agent', 'results', 'probe', 'probe.json')).nvidia.gpus.length, 0)
    })
    // Interval conditions fail the gate even when the ballot condition holds: outcome conditions_unmet.
    const worthwhile = await execute('below-worthwhile', { minimum: 1.85 })
    status('below-worthwhile', worthwhile, 'numeric')
    facts('below-worthwhile', worthwhile, { approve: 4, reject: 1 }, false)
    const abstainedBelow = await execute('below-worthwhile-all-abstain', { minimum: 1.85, votes: [AB, AB, AB, AB, AB] })
    status('below-worthwhile-all-abstain', abstainedBelow, 'numeric')
    facts('below-worthwhile-all-abstain', abstainedBelow, { abstain: 5 }, false)
    // Selected high 1.8 above a still-feasible bound of 1.5 (ranking ties keep the menu's first method first).
    const aboveBound = await execute('high-above-bound', { mutate: ({ bounds }) => { bounds[MENU[0]].bound = 1.5 } })
    status('high-above-bound', aboveBound, 'numeric')
    facts('high-above-bound', aboveBound, { approve: 4, reject: 1 }, false)
    // Both conditions failing: ballots decide the outcome label.
    const both = await execute('rejected-and-below-worthwhile', { minimum: 1.85, votes: [A, A, A, R, null] })
    status('rejected-and-below-worthwhile', both, 'numeric')
    facts('rejected-and-below-worthwhile', both, { approve: 3, reject: 1 }, false)
    for (const [name, config] of [
      ['missing-proposal', { missingProposal: true }],
      ['unsafe-selection', { method: 'multi-GPU' }],
      ['malformed-proposal', { proposal: { method: MENU[0], rationale: 'fixture', plan_steps: [], files_expected: ['x'], risks: [] } }],
    ]) {
      const run = await execute(name, config)
      status(name, run, 'parse')
      check(`${name}: one proposer, no skeptic calls`, () => assert.deepEqual(run.calls.map(call => call.title), ['propose']))
      uncounted(name, run)
    }
    for (const [name, mutate] of [
      ['duplicate-method', ({ predictions }) => predictions.predictions.push(predictions.predictions[0])],
      ['unknown-method', ({ predictions }) => { predictions.predictions[0].method = 'invented' }],
      ['invalid-interval', ({ predictions }) => { predictions.predictions[0].expected_speedup_interval.low = '1.2' }],
    ]) {
      const run = await execute(name, { mutate })
      status(name, run, 'parse')
      check(`${name}: malformed sealed input rejected before agents`, () => assert.equal(run.calls.length, 0))
      uncounted(name, run)
    }
    // SCHEMAS.md "m5 model policy": run under m5/wf_config.json with --family codex.
    const approveAll = [ballot(), ballot(), ballot(), ballot(), ballot()]
    const routed = await execute('policy-routing', { m5Policy: true, votes: approveAll })
    status('policy-routing', routed)
    facts('policy-routing', routed, { approve: 5 }, true)
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
    // One refused (null) ballot plus one rejection: two against the gate.
    facts('policy-claude-refusal', refused, { approve: 3, reject: 1 }, false)
    check('policy-claude-refusal: refused ballot written as null, counted against the gate like a rejection, not handed over', () => {
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
    facts('policy-claude-transport', handed, { approve: 5 }, true)
    check('policy-claude-transport: transport failure on a claude ballot hands over to codex', () => {
      const ballot5 = handed.calls.filter(call => call.title === 'skeptic-5').sort((a, b) => a.time - b.time)
      assert.deepEqual(ballot5.map(call => familyOf(call.model)), ['claude', 'codex'])
      assert.equal(ballot5[0].model, 'claude/sonnet')
      assert.deepEqual(ballot5.map(call => call.name), ['x-propose-test-skeptic-5', 'x-propose-test-skeptic-5-fb'])
      assert.equal(handed.calls.length, 7)
      assert.deepEqual(readJSON(path.join(handed.root, 'agent', 'votes', '5.json')), ballot('approve', ['other']))
    })
    // A single refused ballot alone is one null ballot: the gate still passes.
    const refusedOnly = await execute('policy-claude-refusal-alone', { m5Policy: true,
      votes: [AB, AB, ballot(), ballot(), ballot()], failures: { 'skeptic-5': { claude: 'refusal' } } })
    status('policy-claude-refusal-alone', refusedOnly)
    facts('policy-claude-refusal-alone', refusedOnly, { approve: 2, abstain: 2 }, true)

    // Recorded-run regressions: run16's inputs, proposal and ballots; then run16's inputs with the
    // recorded ballots of run6, run9 and run15. Fixtures are copied into scratch, never written in place.
    const fixtureDigest = () => ['run6', 'run9', 'run15', 'run16'].flatMap(run => ['agent/PREDICTIONS.json', 'agent/bounds.json',
      'agent/proposal.json', 'control/box.json', 'agent/results/probe/probe.json', ...[1, 2, 3, 4, 5].map(i => `agent/votes/${i}.json`)]
      .map(relative => path.join(RUNS, run, relative)).filter(file => fs.existsSync(file))
      .map(file => [file, createHash('sha256').update(fs.readFileSync(file)).digest('hex')]))
    const fixtureBefore = fixtureDigest()
    const proposal16 = recordedProposal('run16')
    const replays = [['run16', { approve: 2, abstain: 3 }, true]]
      .concat(['run6', 'run9', 'run15'].map(run => [run, { reject: 5 }, false]))
    for (const [ballots, counts, pass] of replays) {
      const name = `replay-run16-ballots-${ballots}`
      const votes = recordedBallots(ballots)
      check(`${name}: recorded ballots are ${JSON.stringify(counts)}`, () => {
        for (const vote of ['approve', 'reject', 'abstain'])
          assert.equal(votes.filter(value => value?.vote === vote).length, counts[vote] || 0, vote)
      })
      const run = await execute(name, { replay: 'run16', box: recordedBox('run16'), proposal: proposal16, votes })
      status(name, run, pass ? undefined : 'numeric')
      facts(name, run, counts, pass, proposal16.method)
    }
    check('recorded fixtures unchanged by the replays', () => assert.deepEqual(fixtureDigest(), fixtureBefore))

    // Recorded public regression: positive-openmm run1's inputs. As recorded (concurrency mps=true) the
    // absence is a measured negative finding; with only its concurrency record changed to mps=false,
    // mps_failed=true (what the corrected probe records when copies never reach the daemon) it is unmeasured.
    const RUN1_FILES = ['agent/profile-packet.json', 'agent/bounds.json', 'agent/PREDICTIONS.json',
      'control/box.json', 'agent/results/probe/probe.json']
    const run1Digest = () => RUN1_FILES.map(relative => createHash('sha256').update(fs.readFileSync(path.join(OPENMM_RUN1, relative))).digest('hex'))
    const run1Before = run1Digest()
    const run1Concurrency = readJSON(path.join(OPENMM_RUN1, 'agent', 'profile-packet.json')).concurrency
    check('openmm-run1: recorded inputs rest on measurements (mps true, finite factor, a GPU in each inventory)', () => {
      assert.equal(run1Concurrency?.mps, true)
      assert.equal(run1Concurrency.mps_failed, false)
      assert.ok(Number.isFinite(run1Concurrency.factor))
      const box = recordedBox(OPENMM_RUN1)
      const boxCount = Number.isInteger(box.gpu_count) && box.gpu_count >= 0 ? box.gpu_count
        : Number(/^gpu_(\d+)x_/.exec(String(box.type))?.[1])
      assert.ok(boxCount >= 1, 'box inventory')
      assert.ok(readJSON(path.join(OPENMM_RUN1, 'agent', 'results', 'probe', 'probe.json')).nvidia.gpus.length >= 1, 'probe inventory')
    })
    const run1 = await execute('replay-openmm-run1', { replay: OPENMM_RUN1, box: recordedBox(OPENMM_RUN1) })
    negativeFinding('replay-openmm-run1', run1)
    const run1Failed = { ...run1Concurrency, mps: false, mps_failed: true }
    const run1Unmeasured = await execute('replay-openmm-run1-mps-failed', { replay: OPENMM_RUN1,
      box: recordedBox(OPENMM_RUN1), replayConcurrency: run1Failed })
    unmeasured('replay-openmm-run1-mps-failed', run1Unmeasured)
    check('replay-openmm-run1-mps-failed: only the concurrency record differs from the recorded inputs', () => {
      const root = run1Unmeasured.root
      const packet = readJSON(path.join(root, 'agent', 'profile-packet.json'))
      const recorded = readJSON(path.join(OPENMM_RUN1, 'agent', 'profile-packet.json'))
      assert.deepEqual(packet.concurrency, run1Failed)
      assert.deepEqual({ ...packet, concurrency: null }, { ...recorded, concurrency: null })
      for (const relative of RUN1_FILES.slice(1))
        assert.deepEqual(fs.readFileSync(path.join(root, relative)), fs.readFileSync(path.join(OPENMM_RUN1, relative)), relative)
    })
    check('openmm-run1 fixtures unchanged by the replays', () => assert.deepEqual(run1Digest(), run1Before))
  } catch (error) {
    failures++
    console.log(`FAIL test harness: ${error.stack}`)
  } finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
