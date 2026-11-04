#!/usr/bin/env node
'use strict'

// Black-box compute contract tests; implementation files are executed, never read.
// Usage: node tools/test_m5_compute.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')
const ROOT = path.resolve(__dirname, '..')
const fixture = require('./m5_profile_fixture.js')
const STAGES = ['intake', 'reproduce', 'profile', 'seal', 'propose', 'implement', 'evaluate', 'takeaways']
const SENTINEL = 'PRIVATE_COMPUTE_SENTINEL_97413'
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
function writeJSON(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value) + '\n')
}
function script(file, body) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, '#!/usr/bin/env bash\nset -eu\n' + body + '\n', { mode: 0o700 })
}
const emit = (file, value) => `cat > '${file}' <<'COMPUTE_FIXTURE'\n${JSON.stringify(value)}\nCOMPUTE_FIXTURE\n`
const family = model => model.startsWith('lambda/') ? 'lambda' : model.startsWith('codex/') ? 'codex'
  : model.startsWith('cursor/') ? 'cursor' : model.startsWith('claude/') ? 'claude' : 'opencode'

// Follow the existing WF_STUB pattern. Fixture agents write only agent content.
module.exports = {
  async run(options) {
    const { title, model } = options
    const root = process.env.M5_COMPUTE_ROOT
    const config = JSON.parse(process.env.M5_COMPUTE_CONFIG)
    const failed = config.fallback && ['intake', 'harness-repair'].includes(title) && !model.startsWith('cursor/')
    fs.appendFileSync(path.join(root, 'calls.jsonl'), JSON.stringify({ title, model, failed }) + '\n')
    if (failed) return { text: '', json: null, jsonError: null, sessionID: 'stub',
      tokens: { input: 10, output: 0 }, tokens_known: true, cost: 0, tools: 0, ms: 1,
      errors: ['runner error: usage limit: synthetic fixture'], refusal: false }
    let json = { v: SENTINEL }
    if (title === 'intake') {
      json = { found: true, anchors_count: 2, data: 'available', licence: 'permitted', stock_environment: true, size: 'small' }
      const fixtures = {
        benchmark: { identity: 'compute fixture', outcome_definition: 'sum', citations: ['https://example.org/reference'] },
        data: { availability: 'available', licences: ['MIT'], required_inputs: ['integers'] },
        anchors: [1, 2].map(i => ({ id: `anchor-${i}`, quantity: 'sum', published_value: 499500,
          tolerance: 0, source: 'https://example.org/reference' })),
        baseline: { repo: 'https://example.org/fixture', pin: 'v1', build_commands: ['true'],
          run_commands: ['true'], published_configuration: { n: 1000 } },
        EXECUTION: { representative_scale: { n: 1000 }, inputs: ['integers'], outputs: ['sum'],
          timing_scope: 'whole run', timeout_s: 30 },
      }
      for (const [name, value] of Object.entries(fixtures)) writeJSON(path.join(root, 'agent', 'intake', `${name}.json`), value)
      fs.writeFileSync(path.join(root, 'agent', 'intake', 'brief.md'), SENTINEL)
    }
    if (title === 'seal') {
      const predictions = ['data-parallel over inputs', 'batching', 'ensembles', 'pipelining'].map(method => ({ method,
        expected_speedup_interval: { low: 1.05, high: method === 'batching' ? 1.3 : 1.2 },
        outcome_vs_compute_points: [1, 2, 4].map(compute_budget => ({ compute_budget,
          predicted_outcome: 499500, uncertainty: 'exact equality' })) }))
      writeJSON(path.join(root, 'agent', 'PREDICTIONS.json'), { predictions,
        infeasible_methods: [{ method: 'multi-GPU', reason: 'Only one GPU in this fixture.' }],
        outputs_stochastic: false,
        equivalence_metrics: [{ name: 'sum', tolerance: { abs: 0 }, source: 'Exact integer sum requirement.' }],
        paired_seed_tests: { kind: 'deterministic', justification: 'Integer summation has no random inputs or operations.' },
        sample_sizes: { n: 1000 },
        confidence_rule: { equivalence: { kind: 'exact' } }, hardware_cost_basis: 'same box', timing_scope: 'whole run',
        minimum_worthwhile_gain: 1.05, evaluation_inputs: ['integers'], splits: { evaluation: [0, 1000] },
        compute_budgets: [1, 2, 4], repetitions: 5, warmup: 'one run', scheduling_order: 'alternate',
        equal_outcome_target: 499500,
        baseline_invocation_s: { seconds: 0.01, source: 'fixture: one baseline equivalence invocation, 0.01 s' },
        private_content: SENTINEL })
      json = { seal_present: true, seal_verified: true, prediction_count: predictions.length }
    }
    if (title === 'harness' || title === 'harness-repair') {
      const harness = path.join(root, 'agent', 'harness')
      script(path.join(harness, 'setup.sh'), `mkdir -p out\nsleep 1\nprintf '%s\\n' '${SENTINEL}'\n` +
        (config.retry && title === 'harness' ? 'exit 7' : 'true'))
      script(path.join(harness, 'run_anchors.sh'), 'mkdir -p out\nbash harness/run_command.sh\n' +
        emit('out/anchors_measured.json', { 'anchor-1': 499500, 'anchor-2': 499500 }))
      script(path.join(harness, 'run_command.sh'), 'sleep 1')
    }
    return { text: JSON.stringify(json), json, jsonError: null, sessionID: 'stub',
      tokens: { input: 10, output: 5 }, tokens_known: true, cost: 123,
      tools: 0, ms: 1, errors: [], refusal: false }
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
if (require.main !== module) return

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_compute_'))
let failures = 0, checks = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}
function near(actual, expected, message) {
  assert.equal(typeof actual, 'number', message)
  assert.ok(Number.isFinite(actual) && Math.abs(actual - expected) <= 1e-9 * Math.max(1, Math.abs(expected)),
    `${message}: expected ${expected}, got ${actual}`)
}
async function execute(command, args, env, directory, timeout = 1800000) {
  fs.mkdirSync(directory, { recursive: true })
  const stdout = fs.openSync(path.join(directory, 'stdout.log'), 'w')
  const stderr = fs.openSync(path.join(directory, 'stderr.log'), 'w')
  try {
    return await new Promise(resolve => {
      const child = spawn(command, args, { cwd: ROOT, env, timeout, stdio: ['ignore', stdout, stderr] })
      let error
      child.on('error', value => { error = value })
      child.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
}
function cleanCell(cell) { return cell.trim().replace(/^[`*]+|[`*]+$/g, '') }
function table(text) {
  return text.split('\n').filter(line => line.trim().startsWith('|'))
    .map(line => line.trim().slice(1, -1).split('|').map(cleanCell))
}
function reportChecks(name, text, records, box) {
  check(`${name}: Compute section and per-stage compute columns`, () => {
    assert.match(text, /^#+\s+Compute\b/im)
    const cells = table(text)
    const header = cells.find(row => row.some(cell => cell.toLowerCase() === 'stage') && row.includes('model_family'))
      ?.map(cell => cell.toLowerCase())
    assert.ok(header, 'stage compute header missing')
    for (const field of ['status', 'wall_s', 'gpu_s', 'usd', 'tokens_in', 'tokens_out', 'model_family']) {
      assert.ok(header.includes(field), `missing ${field}`)
    }
    for (const { signature: sig } of records) {
      const matches = cells.filter(row => row[header.indexOf('stage')] === sig.stage)
      assert.equal(matches.length, 1, sig.stage)
      const row = matches[0]
      for (const field of ['status', 'model_family']) assert.equal(row[header.indexOf(field)], sig[field], `${sig.stage}.${field}`)
      for (const field of ['wall_s', 'gpu_s', 'usd', 'tokens_in', 'tokens_out']) {
        near(Number(row[header.indexOf(field)]), sig[field], `${sig.stage}.${field}`)
      }
    }
  })
  check(`${name}: run totals preserve stage sums and run USD override`, () => {
    const cells = table(text)
    const fields = ['wall_s', 'gpu_s', 'usd', 'tokens_in', 'tokens_out']
    const index = cells.findIndex(row => row.length === fields.length && fields.every((field, i) => row[i] === field))
    assert.ok(index >= 0, 'totals header missing')
    const values = cells[index + 2]
    const runUsd = records.find(row => row.signature.stage === 'takeaways')?.facts.run_box_usd
    fields.forEach((field, i) => near(Number(values[i]), field === 'usd' && runUsd != null ? runUsd
      : records.reduce((sum, row) => sum + row.signature[field], 0), `total ${field}`))
  })
  check(`${name}: box type and hourly price only; private content excluded`, () => {
    assert.ok(text.includes(box.type))
    assert.ok(text.includes('price_usd_h'))
    assert.ok(table(text).some(row => row.includes(String(box.price_usd_h))), 'box price missing')
    assert.ok(!text.includes(SENTINEL), 'private sentinel leaked')
    assert.ok(!text.includes(box.region), 'region leaked')
    assert.ok(!text.includes(box.started_utc), 'allocation timestamp leaked')
  })
}

async function runCase(name, config) {
  const root = path.join(scratch, name), home = path.join(root, 'home'), bin = path.join(root, 'bin')
  const remote = path.join(root, 'box')
  fs.mkdirSync(remote, { recursive: true })
  const box = { type: 'gpu_1x_a10', region: `${SENTINEL}_region`, price_usd_h: 7.25,
    started_utc: '2026-01-01T00:00:00Z', private_note: SENTINEL }
  writeJSON(path.join(home, '.cache', 'metis-serve', 'box.json'), box)
  writeJSON(path.join(root, 'control', 'box.json'), { ...box, price_usd_h: 999 })
  const argsFile = path.join(root, 'control', 'args.json')
  writeJSON(argsFile, { run_root: root, tag: 'compute-test', ...(config.noCalls ? {
    stub: Object.fromEntries(STAGES.map(stage => [stage, 'PASS'])),
  } : { stub: { propose: 'PASS', implement: 'PASS', evaluate: 'PASS' } }) })
  script(path.join(bin, 'box'), 'command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\ncd -- "$BOX_ROOT"\nbash -c "$command"\n"$M5_TEST_NODE" "$M5_PROFILE_FIXTURE" "$BOX_ROOT"\n' +
    // Let detached fixture commands finish before boxrun's first polling check.
    'if [[ $command == *timeout* ]]; then\n' +
    '  for ((end=SECONDS+1800; SECONDS<end; )); do\n    pending=false\n' +
    '    for file in "$BOX_ROOT"/m5-*/*.sh; do\n' +
    '      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n' +
    '    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi')
  script(path.join(bin, 'fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\ncd -- "$BOX_ROOT"\nexec cp -r -- "$source" "$2"')
  script(path.join(bin, 'nvidia-smi'), `if [[ "$*" == *--query-gpu=utilization.gpu* ]]; then
  printf '%s\\n' '${config.samples === false ? 'invalid' : config.util ?? 25}'
  exit 0
fi
if [[ "$*" == *--query-gpu=name* ]]; then printf '%s\\n' 'Fixture GPU'; fi`)
  // Shadow any host MPS control binary; the real concurrency probe runs on the fake box.
  script(path.join(bin, 'nvidia-cuda-mps-control'), '[[ $# -gt 0 ]] || cat > /dev/null')
  const policy = readJSON(path.join(ROOT, 'idea', 'config.json'))
  policy.workflow.label_rules = []
  policy.understudy.routes = []
  policy.understudy.primary_family = 'opencode'
  policy.understudy.disabled_families = ['claude']
  policy.understudy.chain = { opencode: ['cursor'], codex: ['cursor'], cursor: [], claude: [] }
  policy.understudy.families.opencode.models = { main: 'lambda/fixture', cheap: 'lambda/fixture', strong: 'lambda/fixture' }
  policy.understudy.families.opencode.by_role = { 'ls-writer': 'lambda/fixture', 'ls-general': 'lambda/fixture' }
  writeJSON(path.join(root, 'config.json'), policy)
  const env = { ...process.env, HOME: home, PATH: `${bin}:${process.env.PATH}`,
    M5_RAIDS_LEDGER: path.join(root, 'ledger.jsonl'), WF_STUB: __filename,
    M5_COMPUTE_ROOT: root, M5_COMPUTE_CONFIG: JSON.stringify(config),
    M5_TEST_NODE: process.execPath, M5_PROFILE_FIXTURE: path.join(ROOT, 'tools/m5_profile_fixture.js'), BOX_ROOT: remote, BOX: path.join(bin, 'box'), FETCH: path.join(bin, 'fetch') }
  const out = path.join(root, 'agent', 'wf')
  const result = await execute(process.execPath, [path.join(ROOT, 'idea', 'wf.js'), '--script', path.join(ROOT, 'm5', 'pipeline.js'),
    '--args', argsFile, '--out', out, '--config', path.join(root, 'config.json'), '--disable-family', 'claude'], env, root)
  check(`${name}: workflow completes`, () => {
    assert.ifError(result.error)
    assert.equal(result.status, 0, fs.readFileSync(path.join(root, 'stderr.log'), 'utf8').slice(-600))
    assert.ok(!readJSON(path.join(out, 'result.json')).error, 'workflow returned error')
  })
  const records = rows(path.join(root, 'operator', 'signatures.jsonl')).filter(row => STAGES.includes(row.signature?.stage))
  const journal = rows(path.join(out, 'journal.jsonl'))
  const calls = rows(path.join(root, 'calls.jsonl'))
  check(`${name}: eight ordered stage records`, () => assert.deepEqual(records.map(row => row.signature.stage), STAGES))
  check(`${name}: allocation snapshot replaces stale C/box.json`, () => assert.deepEqual(readJSON(path.join(root, 'control', 'box.json')), box))
  const answersByStage = Object.fromEntries(STAGES.map(stage => [stage, []]))
  let phase
  for (const event of journal) {
    if (event.type === 'phase') phase = event.t
    if (['result', 'cached'].includes(event.type) && answersByStage[phase]) answersByStage[phase].push(event)
  }
  for (const row of records) {
    const sig = row.signature, stage = sig.stage
    check(`${name}: ${stage} answering model family`, () => {
      const answers = answersByStage[stage]
      const expected = answers.length ? family(answers.at(-1).model) : 'none'
      assert.equal(sig.model_family, expected)
      if (stage === 'intake' && !config.noCalls) assert.equal(expected, config.fallback ? 'cursor' : 'lambda')
      if (config.noCalls) assert.equal(calls.length, 0)
    })
    check(`${name}: ${stage} control receipt matches signature; notes bounded`, () => {
      const receipt = readJSON(path.join(root, 'control', 'stages', `${stage}.json`))
      for (const key of ['stage', 'status', 'wall_s', 'gpu_s', 'usd', 'model_family']) assert.deepEqual(receipt[key], sig[key], key)
      const families = new Set(answersByStage[stage].map(event => family(event.model)))
      assert.deepEqual(receipt.notes, families.size > 1 ? ['multiple_model_families'] : [])
      assert.ok(!JSON.stringify(receipt).includes(SENTINEL))
    })
  }
  if (!config.noCalls) {
    const receiptDir = path.join(root, 'control', 'receipts')
    const receipts = fs.existsSync(receiptDir) ? fs.readdirSync(receiptDir).filter(file => file.endsWith('.json')).sort()
      .map(file => ({ operation: file.replace(/^\d+-|\.json$/g, ''), ...readJSON(path.join(receiptDir, file)) })) : []
    check(`${name}: box commands include probe, uploads, setup, anchors, profile`, () => {
      for (const op of ['probe', 'upload', 'setup', 'anchors', 'profile', 'concurrency']) assert.ok(receipts.some(row => row.operation === op), op)
      assert.equal(receipts.filter(row => row.operation === 'setup').length, config.retry ? 2 : 1)
      if (config.retry) assert.deepEqual(receipts.filter(row => row.operation === 'setup').map(row => row.rc), [7, 0])
    })
    for (const receipt of receipts) check(`${name}: ${receipt.name} sampled GPU receipt`, () => {
      assert.equal(typeof receipt.gpu_busy_known, 'boolean')
      assert.ok(Number.isFinite(receipt.gpu_busy_s) && receipt.gpu_busy_s >= 0)
      const files = []
      function visit(dir) {
        for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
          const file = path.join(dir, entry.name)
          if (entry.isDirectory()) visit(file)
          // Probe work directories symlink every top-level entry; count only real files.
          else if (entry.isFile() && entry.name === `${receipt.name}.gpu`) files.push(file)
        }
      }
      visit(remote)
      assert.equal(files.length, 1, 'remote GPU samples missing')
      const samples = fs.readFileSync(files[0], 'utf8').split(/\s+/).filter(Boolean)
        .map(Number).filter(value => Number.isFinite(value) && value >= 0 && value <= 100)
      assert.equal(receipt.gpu_busy_known, samples.length > 0)
      near(receipt.gpu_busy_s, samples.reduce((sum, value) => sum + value / 100 * 2, 0), 'sample integral')
      if (config.samples === false) { assert.equal(samples.length, 0); assert.equal(receipt.gpu_busy_s, 0) }
      else if (['setup', 'anchors', 'profile'].includes(receipt.operation)) {
        assert.ok(samples.length > 0, 'expected samples during one-second command')
        assert.ok(samples.every(value => value === (config.util ?? 25)), 'fake box PATH ignored')
      }
    })
    for (const stage of ['reproduce', 'profile']) check(`${name}: ${stage} USD and GPU sum all command receipts`, () => {
      // Profile has its own operation; all preceding uploads/probe/setup/anchors/reproduce-freeze belong to reproduce.
      // When reproduce passes, reproduce-freeze is the last reproduce command: after anchors, before profile.
      const freezes = receipts.flatMap((receipt, index) => receipt.operation === 'reproduce-freeze' ? [index] : [])
      assert.equal(freezes.length, 1, 'exactly one reproduce-freeze receipt')
      const boundary = freezes[0]
      assert.ok(boundary > receipts.findLastIndex(receipt => receipt.operation === 'anchors'), 'reproduce-freeze after last anchors')
      const firstProfile = receipts.findIndex(receipt => receipt.operation === 'profile')
      assert.ok(firstProfile >= 0 && boundary < firstProfile, 'reproduce-freeze before first profile')
      const assigned = receipts.filter((receipt, index) => (index > boundary) === (stage === 'profile'))
      assert.ok(assigned.length > 0)
      const row = records.find(row => row.signature.stage === stage)
      near(row.signature.usd, assigned.reduce((sum, receipt) => sum + receipt.wall_s, 0) / 3600 * box.price_usd_h, 'command USD')
      near(row.signature.gpu_s, assigned.reduce((sum, receipt) => sum + receipt.gpu_busy_s, 0), 'command GPU seconds')
      assert.equal(row.facts.gpu_busy_known, assigned.every(receipt => receipt.gpu_busy_known))
      assert.notEqual(row.signature.gpu_s, 999, 'profile GPU timings substituted for receipts')
    })
    check(`${name}: real concurrency probe calibrates whole-workload bounds`, () => {
      // run_command.sh sleeps 1 s, so concurrent copies overlap: factor_n = n * T1 / wall_n near n.
      const packet = readJSON(path.join(root, 'agent', 'profile-packet.json'))
      fixture.assertConcurrencyShape(packet.concurrency)
      const { single_wall_s: singles, batches, factor } = packet.concurrency
      assert.ok(singles.every(wall => wall >= 1 && wall < 3), `single walls ${singles}`)
      const t1 = [...singles].sort((a, b) => a - b)[1]
      for (const batch of batches) {
        assert.equal(batch.all_ok, true)
        assert.equal(batch.skipped, false)
        assert.ok(Math.abs(batch.factor - batch.n * t1 / batch.wall_s) < 1e-6 * batch.factor, `factor_${batch.n}`)
      }
      assert.equal(factor, Math.max(...batches.map(batch => batch.factor)))
      assert.ok(factor > 2.5, `four overlapping 1 s copies should give factor near 4, got ${factor}`)
      assert.equal(records.find(row => row.signature.stage === 'profile').facts.headroom, factor)
      const bounds = readJSON(path.join(root, 'agent', 'bounds.json'))
      for (const [method, cap] of [['data-parallel over inputs', 8], ['batching', 4], ['ensembles', 8]]) {
        near(bounds[method].k, Math.min(cap, factor), `${method} k`)
        assert.equal(bounds[method].k_derivation.factor, factor)
        assert.equal(bounds[method].k_derivation.mps, packet.concurrency.mps)
      }
    })
  }
  check(`${name}: all stage gates pass`, () => assert.ok(records.every(row => row.signature.status === 'PASS')))
  const report = path.join(root, 'operator', 'OPERATOR_TAKEAWAY.md')
  reportChecks(name, fs.existsSync(report) ? fs.readFileSync(report, 'utf8') : '', records, box)
  return { root, env, records, box }
}

async function operatorChecks(run) {
  // Exercise the public API with sentinel-bearing records and box metadata.
  const fixture = path.join(run.root, 'operator-fixture.json')
  writeJSON(fixture, { records: run.records,
    box: { ...run.box, type: SENTINEL, price_usd_h: true } })
  const program = `import json, sys\nfrom m5.operator_takeaway import takeaway\nx=json.load(open(sys.argv[1]))\nprint(takeaway(x['records'], box=x['box']))\n`
  const dir = path.join(run.root, 'operator-api')
  const result = await execute('python3', ['-c', program, fixture], { ...run.env, PYTHONDONTWRITEBYTECODE: '1' }, dir, 30000)
  check('operator API: invalid box type and boolean price sanitized', () => {
    assert.ifError(result.error)
    assert.equal(result.status, 0, fs.readFileSync(path.join(dir, 'stderr.log'), 'utf8'))
    const text = fs.readFileSync(path.join(dir, 'stdout.log'), 'utf8')
    assert.ok(!text.includes(SENTINEL))
    const cells = table(text)
    assert.ok(cells.some(row => row.includes('unknown')), 'unknown type missing')
    assert.ok(cells.some(row => row.includes('null')), 'boolean price must render null')
  })
  writeJSON(fixture, { records: run.records.map(row => ({ ...row, private_content: SENTINEL })), box: run.box })
  const rejectedDir = path.join(run.root, 'operator-rejection')
  const rejected = await execute('python3', ['-c', program, fixture], { ...run.env, PYTHONDONTWRITEBYTECODE: '1' }, rejectedDir, 30000)
  check('operator API: invalid sentinel-bearing records rejected without content leakage', () => {
    assert.ifError(rejected.error)
    assert.notEqual(rejected.status, 0, 'invalid records accepted')
    for (const file of ['stdout.log', 'stderr.log']) assert.ok(!fs.readFileSync(path.join(rejectedDir, file), 'utf8').includes(SENTINEL))
  })
}
async function main() {
  try {
    const sampled = await runCase('sampled-retry-fallback', { retry: true, fallback: true })
    await operatorChecks(sampled)
    await runCase('no-valid-samples', { samples: false })
    await runCase('zero-utilisation', { util: 0 })
    await runCase('no-agent-calls', { noCalls: true })
  } catch (error) { check('test harness', () => { throw error }) }
  finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
