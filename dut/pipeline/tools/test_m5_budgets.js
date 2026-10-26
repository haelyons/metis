#!/usr/bin/env node
'use strict'

// Black-box budget contracts from m5/SCHEMAS.md.
// Usage: node tools/test_m5_budgets.js
// Reuse the existing hermetic evaluation author fixture; never inspect M5 source.
// Only this test file belongs in the checkout. All runtime writes use temp dirs.
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')
const { createHash } = require('node:crypto')
const fixture = require('./test_m5_evaluate.js')
const ROOT = path.resolve(__dirname, '..')
const DEFAULTS = { setup: 1200, anchors: 1200, profile: 1200, method_setup: 1200, method_run: 1200, tests: 900, evaluate: 2400 }
const SMALL = Object.fromEntries(Object.keys(DEFAULTS).map(key => [key, 3]))
const STAGES = ['intake', 'reproduce', 'profile', 'seal', 'propose', 'implement', 'evaluate', 'takeaways']
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
function json(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value) + '\n')
}
function script(file, body) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, '#!/usr/bin/env bash\nset -eu\n' + body + '\n', { mode: 0o700 })
}
const emit = (file, value) => `printf '%s\\n' '${JSON.stringify(value)}' > ${file}\n`
const TARGETS = {
  setup: ['harness-repair', 'setup', 'reproduce', 'harness/setup.sh'],
  anchors: ['anchors-repair', 'anchors', 'reproduce', 'harness/run_anchors.sh'],
  profile: ['profile-repair', 'profile', 'profile', 'harness/profile.sh'],
  method_setup: ['implement', 'setup-method', 'implement', 'method/setup_method.sh'],
  method_run: ['implement', 'run-method', 'implement', 'method/run_method.sh'],
  tests: ['implement', 'run-tests', 'implement', 'tests/run_tests.sh'],
}
module.exports = {
  async run(options) {
    const root = process.env.M5_EVALUATE_ROOT, config = JSON.parse(process.env.M5_BUDGET_CONFIG)
    const callsFile = path.join(root, 'budget-calls.jsonl')
    const prior = rows(callsFile)
    fs.appendFileSync(callsFile, JSON.stringify({ title: options.title, prompt: options.prompt, name: options.name }) + '\n')
    const view = options.isolation?.directory || options.cwd
    let result
    if (['harness-repair', 'anchors-repair', 'profile-repair'].includes(options.title)) {
      const target = Object.values(TARGETS).find(value => value[0] === options.title)[3]
      fs.copyFileSync(path.join(root, 'pristine', target), path.join(root, 'agent', target))
      result = { json: { v: 'repaired' }, tokens: { input: 0, output: 0 }, tokens_known: true }
      result = { ...result, text: JSON.stringify(result.json), jsonError: null, sessionID: options.title,
        cost: 0, tools: 0, ms: 1, errors: [], refusal: false }
    } else result = await fixture.run(options)
    if (options.title === 'harness') {
      script(path.join(root, 'agent/harness/profile.sh'), 'mkdir -p out/profile\n' +
        emit('out/profile/stages.json', [
          { stage: 'cpu', kind: 'other', wall_s: 3, gpu_s: null },
          { stage: 'h2d', kind: 'transfer', wall_s: 2, gpu_s: null },
          { stage: 'compute', kind: 'compute', wall_s: 4.5, gpu_s: 0 },
        ]) + emit('out/profile/total_wall_s.json', { total_wall_s: 10 }) +
        emit('out/profile/gpu_util.json', [{ t: 0, util: 0 }, { t: 1, util: 75 }]))
      fs.cpSync(path.join(root, 'agent/harness'), path.join(root, 'pristine/harness'), { recursive: true })
    }
    if (config.target) {
      const [repair, , , target] = TARGETS[config.target]
      const initial = target.startsWith('harness/') ? 'harness' : target.startsWith('tests/') ? 'tests' : 'implement'
      const isRepair = options.title === repair && (repair !== 'implement' || prior.some(call => call.title === 'implement'))
      if (options.title === initial || isRepair) {
        // Frozen test scripts always sleep, even after the permitted method repair.
        const file = path.join(target.startsWith('harness/') ? path.join(root, 'agent') : view, target)
        if (fs.existsSync(file) && (!config.recover || !isRepair)) {
          fs.writeFileSync(file, fs.readFileSync(file, 'utf8').replace('set -eu\n', 'set -eu\nsleep 4\n'))
        }
      }
    }
    return result
  },
  exportSession: fixture.exportSession,
}
if (require.main !== module) return

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_budgets_'))
const deadline = Date.now() + 165000
let checks = 0, failures = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical)
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]))
  return value
}
function protocol() {
  return {
    predictions: [{ method: 'batching', expected_speedup_interval: { low: 1.5, high: 2.5 },
      outcome_vs_compute_points: [2, 4, 8].map(compute_budget => ({ compute_budget, predicted_outcome: 1, uncertainty: 'fixture' })) }],
    infeasible_methods: [], evaluation_inputs: { ids: ['first', 'middle', 'tail'], pin: 'fixture-v1' },
    sample_sizes: { inputs: 3, seeds: 1 },
    equivalence_metrics: [{ name: 'accuracy', tolerance: { abs: 0.01 }, source: 'fixture' }],
    paired_seed_tests: { kind: 'deterministic', justification: 'Fixed arithmetic.' },
    confidence_rule: { equivalence: { kind: 'paired_median', confidence: 0.95 }, performance: { kind: 'paired_median', confidence: 0.95 } },
    timing_scope: { kind: 'reported_wall', gpu_synchronization: 'adapter', description: 'Complete fixture workload.' },
    hardware_cost_basis: { baseline_gpus: 1, method_gpus: 1, budget_unit: 'gpu_s' },
    warmup: 1, repetitions: 5, scheduling_order: { kind: 'randomized_pairs', seed: 42 },
    minimum_worthwhile_gain: 1.1, compute_budgets: [2, 4, 8], splits: { evaluation: ['first', 'middle', 'tail'] },
    equal_outcome_target: { not_applicable: true, reason: 'No outcome curve.' },
  }
}
function budgetKey(operation) {
  if (['upload', 'probe', 'setup'].includes(operation)) return 'setup'
  if (['anchors', 'profile'].includes(operation)) return operation
  if (operation === 'setup-method') return 'method_setup'
  if (operation === 'run-method') return 'method_run'
  if (operation === 'run-tests') return 'tests'
  if (/^implement-/.test(operation) || /^evaluate-(upload|state-)/.test(operation)) return 'method_setup'
  if (/^evaluate-(validity|equivalence|performance)$/.test(operation)) return 'evaluate'
  throw new Error(`unmapped box operation ${operation}`)
}
async function runCase(name, config) {
  assert.ok(Date.now() < deadline, 'suite exceeded 165-second limit')
  const root = path.join(scratch, name), agent = path.join(root, 'agent'), home = path.join(root, 'home'), bin = path.join(root, 'bin')
  fs.mkdirSync(root, { recursive: true })
  const p = protocol()
  for (const [key, value] of Object.entries({
    benchmark: { name: 'budget fixture' }, data: { available: true },
    anchors: [{ id: 'first', quantity: 'fixture', source: 'published', published_value: 1, tolerance: 0 },
      { id: 'zero', quantity: 'fixture', source: 'published', published_value: 0, tolerance: 0 }],
    baseline: { repo: 'fixture', pin: 'v1', build_commands: ['true'], run_commands: ['true'], published_configuration: { n: 3 } },
    EXECUTION: { representative_scale: { n: 3 }, inputs: ['data/input'], outputs: ['values.json'], timing_scope: p.timing_scope,
      timeout_s: 71, timeouts: { setup: 72, setup_method: 73, run_method: 74, run_tests: 75, evaluate: 76 },
      ...(config.execution ? { stage_budgets_s: config.execution } : {}) },
  })) json(path.join(agent, 'intake', key + '.json'), value)
  const sealed = JSON.stringify(canonical(p)), frozen = path.join(root, 'control/seals/frozen.json')
  fs.writeFileSync(path.join(agent, 'PREDICTIONS.json'), sealed)
  fs.mkdirSync(path.dirname(frozen), { recursive: true })
  fs.writeFileSync(frozen, sealed, { mode: 0o444 })
  json(path.join(root, 'control/seals/0001.json'), { sha256: createHash('sha256').update(sealed).digest('hex'), path: frozen, utc: new Date().toISOString() })
  json(path.join(agent, 'proposal.json'), { method: 'batching', rationale: 'fixture', plan_steps: ['Preserve inputs.'], files_expected: ['pin'], risks: [] })
  json(path.join(home, '.cache/metis-serve/box.json'), { type: 'gpu_8x_a100', region: 'fixture', price_usd_h: 4, started_utc: new Date().toISOString() })
  script(path.join(home, '.cache/metis-serve/box.sh'), 'exit 99')
  // Both controller and fake remote use this GPU tool, regardless of host GPUs.
  script(path.join(bin, 'nvidia-smi'), 'if [[ "$*" == *--query-gpu=name* ]]; then\n  printf "%s\\n" "Fixture GPU"\n  exit 0\nfi\nexit 1')
  // Replace only the uploaded probe with a deterministic fixture, following the
  // existing reproduce test. Actual boxrun, timeout and receipt logic stays real.
  const probe = fs.readFileSync(path.join(ROOT, 'm5/box_probe.sh'), 'utf8')
  fs.writeFileSync(path.join(root, 'probe.js'), `const fs = require('node:fs'), path = require('node:path')
function visit(dir) {
  if (!fs.existsSync(dir)) return
  for (const e of fs.readdirSync(dir, {withFileTypes:true})) {
    const file = path.join(dir,e.name)
    if(e.isDirectory()) visit(file)
    else if(e.isFile() && e.name.endsWith('.sh') && fs.readFileSync(file,'utf8') === ${JSON.stringify(probe)})
      fs.writeFileSync(file, ${JSON.stringify('#!/usr/bin/env bash\nmkdir -p out\nprintf \'{"nvidia":{"gpus":["Fixture GPU"]},"nvcc":[],"cmake":null}\\n\' > out/probe.json\n')})
  }
}
visit(process.argv[2])\n`)
  script(path.join(bin, 'box'), `command=$1
remote_directory=
if [[ $command =~ /tmp/m5-[a-z0-9-]+ ]]; then
  remote_directory=\${BASH_REMATCH[0]}
  printf '%s\\n' "$remote_directory" >> "$M5_REMOTE_ROOTS"
fi
export PATH="$M5_BUDGET_BIN:$PATH"
cd "$M5_BUDGET_ROOT"
bash -c "$command"
if [[ -n $remote_directory ]]; then "$M5_TEST_NODE" "$M5_BUDGET_ROOT/probe.js" "$remote_directory"; fi
if [[ $command == *timeout* && -n $remote_directory ]]; then
  for ((i=0; i<700; i++)); do
    pending=false
    for file in "$remote_directory"/*.sh; do
      [[ -f $file ]] || continue
      [[ -f \${file%.sh}.rc ]] || pending=true
    done
    [[ $pending == true ]] || break
    sleep 0.01
  done
fi`)
  script(path.join(bin, 'fetch'), 'exec cp -r -- "$1" "$2"')
  const args = path.join(root, 'control/args.json'), out = path.join(agent, 'wf')
  json(args, { run_root: root, tag: name, raid: name,
    stub: { intake: 'PASS', seal: 'PASS', propose: 'PASS', takeaways: 'PASS' },
    ...(config.args ? { stage_budgets_s: config.args } : {}) })
  const stdout = fs.openSync(path.join(root, 'stdout'), 'w'), stderr = fs.openSync(path.join(root, 'stderr'), 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(ROOT, 'idea/wf.js'), '--script', path.join(ROOT, 'm5/pipeline.js'),
        '--args', args, '--out', out, '--disable-family', 'claude'], {
        cwd: ROOT, timeout: Math.max(1, Math.min(45000, deadline - Date.now())), killSignal: 'SIGKILL',
        stdio: ['ignore', stdout, stderr], env: { ...process.env, HOME: home, TMPDIR: root,
          PYTHONDONTWRITEBYTECODE: '1', PATH: bin + path.delimiter + process.env.PATH,
          M5_RAIDS_LEDGER: path.join(scratch, 'ledger.jsonl'), WF_STUB: __filename,
          M5_EVALUATE_ROOT: root, M5_EVALUATE_CONFIG: '{}', M5_BUDGET_CONFIG: JSON.stringify(config),
          M5_BUDGET_ROOT: root, M5_BUDGET_BIN: bin, M5_TEST_NODE: process.execPath,
          M5_REMOTE_ROOTS: path.join(scratch, 'remote-roots'), BOX: path.join(bin, 'box'), FETCH: path.join(bin, 'fetch') },
      })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  check(`${name}: workflow finishes`, () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0, `signal=${child.signal}; ${fs.readFileSync(path.join(root, 'stderr'), 'utf8').slice(-500)}`)
    assert.ok(!read(path.join(out, 'result.json')).error, JSON.stringify(read(path.join(out, 'result.json')).error))
  })
  const records = rows(path.join(root, 'operator/signatures.jsonl'))
  const calls = rows(path.join(root, 'budget-calls.jsonl'))
  const receiptDir = path.join(root, 'control/receipts')
  const receipts = fs.existsSync(receiptDir) ? fs.readdirSync(receiptDir).sort().filter(file => file.endsWith('.json'))
    .map(file => ({ operation: file.slice(5, -5), ...read(path.join(receiptDir, file)) })) : []
  const expected = { ...DEFAULTS, ...config.args, ...config.execution }
  check(`${name}: every boxrun receipt has resolved budget_s and overrun`, () => {
    assert.ok(receipts.length > 0, 'no box receipts')
    for (const receipt of receipts) {
      assert.equal(receipt.budget_s, expected[budgetKey(receipt.operation)], receipt.name)
      assert.equal(typeof receipt.overrun, 'boolean', receipt.name)
      assert.equal(receipt.overrun, receipt.rc === 124 || receipt.timed_out || receipt.wall_s > receipt.budget_s, receipt.name)
      assert.equal(receipt.gpu_busy_known, false, receipt.name)
    }
  })
  check(`${name}: author and repair prompts forbid scale search`, () => {
    const authors = calls.filter(call => ['harness', 'tests', 'implement', 'harness-repair', 'anchors-repair', 'profile-repair'].includes(call.title))
    assert.ok(authors.length > 0, 'no author prompts')
    for (const call of authors) {
      assert.match(call.prompt, /(?:no|never|do not|without)[^.\n]*(?:scale.search|doubl)|(?:scale.search|doubl)[^.\n]*(?:forbidden|prohibited)/i, call.title)
      assert.match(call.prompt, /(?:fixed|single|one)[^.\n]*scale|scale[^.\n]*(?:fixed|EXECUTION)/i, call.title)
      assert.match(call.prompt, /budget/i, call.title)
      assert.match(call.prompt, /well within[^.\n]*budget/i, call.title)
      const scripts = call.title === 'tests' ? { 'run_tests.sh': expected.tests }
        : call.title === 'implement' ? { 'setup_method.sh': expected.method_setup, 'run_method.sh': expected.method_run }
          : { 'setup.sh': expected.setup, 'run_anchors.sh': expected.anchors, 'profile.sh': expected.profile,
            'run_evaluation.sh': expected.method_run }
      for (const [file, budget] of Object.entries(scripts)) {
        const escaped = file.replaceAll('.', '\\.')
        assert.match(call.prompt, new RegExp(escaped + '[^=:\\n]*[=:]\\s*' + budget + '(?!\\d)'), call.title + ': ' + file)
      }
    }
  })
  if (!config.target) {
    check(`${name}: all seven budgets exercised through real stages`, () => {
      assert.deepEqual(new Set(receipts.map(receipt => budgetKey(receipt.operation))), new Set(Object.keys(DEFAULTS)))
      assert.deepEqual(records.map(row => [row.signature.stage, row.signature.status]), STAGES.map(stage => [stage, 'PASS']))
      assert.ok(receipts.every(receipt => !receipt.timed_out && receipt.rc === 0), 'unexpected timeout or command failure')
    })
  } else {
    const [repair, operation, stage] = TARGETS[config.target]
    const attempts = receipts.filter(receipt => receipt.operation === operation)
    check(`${name}: exactly one repair, prompt includes budget and elapsed/overrun`, () => {
      const repairs = calls.filter(call => call.title === repair).slice(repair === 'implement' ? 1 : 0)
      assert.equal(repairs.length, 1)
      assert.match(repairs[0].prompt, /timeout/i)
      assert.match(repairs[0].prompt, /budget[^\d\n]*1(?!\d)/i)
      assert.match(repairs[0].prompt, /(?:wall|elapsed)/i)
      assert.match(repairs[0].prompt, /overrun/i)
      if (repair === 'implement') assert.equal(calls.filter(call => call.title === 'tests').length, 1)
    })
    check(`${name}: original budget retained; ${config.recover ? 'repair succeeds' : 'second timeout stops stage'}`, () => {
      assert.equal(attempts.length, 2)
      assert.deepEqual(attempts.map(receipt => receipt.rc), config.recover ? [124, 0] : [124, 124])
      assert.deepEqual(attempts.map(receipt => receipt.budget_s), [1, 1])
      assert.equal(attempts[0].timed_out, true)
      assert.equal(attempts[0].overrun, true)
      const record = records.find(row => row.signature.stage === stage)
      assert.ok(record, `missing ${stage}`)
      assert.equal(record.signature.status, config.recover ? 'PASS' : 'FAIL')
      assert.equal(record.facts.timed_out, true)
      assert.equal(record.facts.budget_s, 1)
      assert.equal(record.facts.overrun, true)
      if (!config.recover) {
        assert.equal(record.signature.error_class, 'timeout')
        assert.equal(record.signature.exit_code, 3)
        for (const later of STAGES.slice(STAGES.indexOf(stage) + 1).filter(value => value !== 'takeaways'))
          assert.equal(records.find(row => row.signature.stage === later)?.signature.status, 'SKIPPED', later)
        assert.ok(receipts.slice(receipts.indexOf(attempts[1]) + 1).every(receipt => receipt.operation === 'implement-state'),
          'scientific work after second timeout')
      }
    })
  }
}
async function main() {
  const cases = [
    ['defaults-ignore-legacy', {}],
    ['args', { args: { ...SMALL, anchors: 2, profile: 2, tests: 2 } }],
    ['execution-over-args', { args: Object.fromEntries(Object.keys(DEFAULTS).map(key => [key, 2])), execution: SMALL }],
    ['independent-fallbacks', { args: { setup: 3, anchors: 2, method_setup: 3, tests: 2 }, execution: { anchors: 1, method_run: 2, evaluate: 3 } }],
    ...Object.keys(TARGETS).map(target => [`timeout-${target}`, { args: { ...SMALL, [target]: 1 }, target }]),
    ['timeout-recovered', { args: { ...SMALL, setup: 1 }, target: 'setup', recover: true }],
  ]
  try {
    // Two independent workflows at a time keep the full suite below three minutes.
    let next = 0
    await Promise.all([0, 1].map(async () => {
      while (next < cases.length) {
        const [name, config] = cases[next++]
        try { await runCase(name, config) }
        catch (error) { check(`${name}: test harness`, () => { throw error }) }
      }
    }))
  } finally {
    function writable(directory) {
      fs.chmodSync(directory, 0o700)
      for (const entry of fs.readdirSync(directory, { withFileTypes: true }))
        if (entry.isDirectory()) writable(path.join(directory, entry.name))
    }
    const registry = path.join(scratch, 'remote-roots')
    if (fs.existsSync(registry)) for (const directory of new Set(fs.readFileSync(registry, 'utf8').trim().split('\n').filter(Boolean))) {
      assert.match(directory, /^\/tmp\/m5-[0-9a-f-]{36}$/)
      if (fs.existsSync(directory)) { writable(directory); fs.rmSync(directory, { recursive: true, force: true }) }
    }
    writable(scratch)
    fs.rmSync(scratch, { recursive: true, force: true })
  }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main().catch(error => { console.log(`FAIL test harness: ${error.message}\n1 failure(s)`); process.exitCode = 1 })
