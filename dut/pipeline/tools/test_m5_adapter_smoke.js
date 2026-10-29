#!/usr/bin/env node
'use strict'

// Black-box U31 contracts: implement's baseline adapter smoke and its one adapter repair.
// Written from m5/SCHEMAS.md only ("Baseline adapter smoke:" in the implement section, the
// evaluation adapter interface and evaluation.json record rules). Do not inspect
// implementation files or git diffs.
// Usage: node tools/test_m5_adapter_smoke.js
// Reuses tools/test_m5_implement.js's fake box, fixture and WF_STUB (its probes require
// working unprivileged bubblewrap, as there).
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawnSync } = require('node:child_process')
const { isDeepStrictEqual } = require('node:util')
const { fixtures } = require('./test_m5_implement.js')
const { launch, removeScratch, rows, files, sha, readJSON, RUN9, RUN9_RECORDS, SEAL_SOURCE, INTAKE_NOTE, HARNESS_NOTE } = fixtures
const { assertEvalShapes } = require('./test_m5_reproduce.js')
const ROOT = path.resolve(__dirname, '..')
const CATEGORIES = ['exit', 'timeout', 'missing_output', 'records', 'metrics']
const FACTS = ['patch_applies', 'tests_pass', 'blind_tests', 'launch_review_pass']
const METHOD_RUN = 22 // fixture EXECUTION.stage_budgets_s.method_run

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_adapter_smoke_'))
let checks = 0, failures = 0
function check(label, fn) {
  checks++
  try { fn(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}

// SCHEMAS.md "Baseline adapter smoke": EVAL_SEEDS is "the sealed object with `seeds` cut to its
// first seed (a deterministic object is passed unchanged)".
const smokeSeeds = seal => seal.paired_seed_tests.kind === 'deterministic' ? seal.paired_seed_tests
  : { ...seal.paired_seed_tests, seeds: seal.paired_seed_tests.seeds.slice(0, 1) }
const finite = value => typeof value === 'number' && Number.isFinite(value)
// Reference pass criteria, from the same sentence: "one record per sealed input id, in order, at
// that seed; the sealed `timing_scope`; the sealed `gpu_count`; finite positive `wall_s` for
// reported timing; and every sealed `equivalence_metrics` name in each record's `metrics` as a
// finite number". Returns null (pass) or the failure category.
function smokeFailure(seal, report) {
  if (!report || typeof report !== 'object' || Array.isArray(report)) return 'missing_output'
  const ids = seal.evaluation_inputs.ids, spec = smokeSeeds(seal)
  const seed = spec.kind === 'deterministic' ? null : spec.seeds[0]
  const records = report.records
  if (!Array.isArray(records) || records.length !== ids.length) return 'records'
  if (records.some((row, i) => !row || row.input_id !== ids[i] || row.seed !== seed)) return 'records'
  if (!isDeepStrictEqual(report.timing_scope, seal.timing_scope)) return 'records'
  if (report.gpu_count !== seal.hardware_cost_basis.baseline_gpus) return 'records'
  if (seal.timing_scope.kind === 'reported_wall' && !(finite(report.wall_s) && report.wall_s > 0)) return 'records'
  for (const row of records) for (const { name } of seal.equivalence_metrics) {
    if (!row.metrics || !finite(row.metrics[name])) return 'metrics'
  }
  return null
}
const receiptsOf = root => files(path.join(root, 'control', 'receipts')).filter(file => file.endsWith('.json'))
  .map(file => ({ file, name: path.basename(file, '.json'), number: Number(path.basename(file).slice(0, 4)),
    operation: path.basename(file, '.json').slice(5), value: readJSON(file) })).sort((a, b) => a.number - b.number)
function remoteRun(root) {
  const box = path.join(root, 'box')
  const found = fs.readdirSync(box).map(name => path.join(box, name))
    .filter(dir => path.basename(dir).startsWith('m5-') && fs.statSync(dir).isDirectory() && fs.existsSync(path.join(dir, 'harness')))
  assert.equal(found.length, 1, 'expected one remote run directory')
  return fs.realpathSync(found[0])
}
// The failure category stated to the repair agent: a category token close after a mention of
// "category", ignoring windows that enumerate several categories (documentation of the enum).
function statedCategories(prompt) {
  const stated = new Set()
  for (const match of prompt.matchAll(/categor(?:y|ies)/gi)) {
    const window = prompt.slice(match.index, match.index + 80)
    const tokens = CATEGORIES.filter(token => new RegExp(`\\b${token}\\b`).test(window))
    if (tokens.length === 1) stated.add(tokens[0])
  }
  return [...stated]
}
// Meaning, not wording: each rule must appear within two adjacent sentences.
function assertMethodRecordRules(prompt) {
  const sentences = prompt.split(/(?<=[.!?;])\s+|\n+/).filter(Boolean)
  const windows = sentences.map((sentence, i) => sentence + ' ' + (sentences[i + 1] || ''))
  const rules = [
    ['record metrics hold every sealed equivalence metric name', [/\bmetrics\b/, /\b(every|each|all)\b/i, /equivalence_metrics|sealed (equivalence )?metric/i, /\bnames?\b/i]],
    ['keyed by exactly that name', [/\bmetrics\b/, /\bkey(ed|s)?\b/i, /\b(exact(ly)?|verbatim|identical|same)\b/i, /\bnames?\b/i]],
    ['method records mean the same as the baseline adapter records', [/\bmethod\b/i, /\bbaseline\b/i, /\brecords?\b/i, /\b(same|identical)\b/i]],
    ['same workload execution per input and seed', [/\bbaseline\b/i, /\b(same|identical)\b/i, /\b(execution|workload)\b/i, /\binputs?\b/i, /\bseeds?\b/i]],
    ['same metric definitions', [/\bbaseline\b/i, /\b(same|identical)\b/i, /\bmetric\b/i, /\bdefin(ition|itions|ed)\b/i]],
  ]
  const missing = rules.filter(([, patterns]) => !windows.some(text => patterns.every(pattern => pattern.test(text)))).map(([label]) => label)
  assert.deepEqual(missing, [], 'method author prompt omits: ' + missing.join('; '))
}
function validateSignature(record) {
  const program = `import json, sys
sys.path.insert(0, ${JSON.stringify(ROOT)})
from measure.signature import validate
print(json.dumps(validate(json.loads(sys.stdin.read()))))`
  const result = spawnSync('python3', ['-I', '-c', program], { input: JSON.stringify(record.signature), encoding: 'utf8' })
  assert.equal(result.status, 0, result.stderr)
  const problems = JSON.parse(result.stdout)
  assert.ok(!problems || (Array.isArray(problems) && !problems.length) || (typeof problems === 'object' && !Object.keys(problems).length),
    'invalid v1 signature: ' + result.stdout.trim())
}

async function scenario(name, config) {
  const run = await launch(scratch, name, config)
  run.name = name
  run.observations = rows(path.join(run.root, 'smoke.jsonl'))
  run.sequence = fs.existsSync(path.join(run.root, 'sequence.log')) ? fs.readFileSync(path.join(run.root, 'sequence.log'), 'utf8').split('\n').filter(Boolean) : []
  run.repairs = run.allCalls.filter(call => call.title === 'adapter-repair')
  run.harnessCall = run.allCalls.find(call => call.title === 'harness')
  run.receipts = receiptsOf(run.root)
  run.smokes = run.receipts.filter(row => row.operation === 'adapter-smoke')
  run.seal = readJSON(path.join(run.root, 'agent', 'PREDICTIONS.json'))
  run.budget = config.methodRun || METHOD_RUN
  check(`${name}: workflow completes with an implement signature`, () => {
    assert.ifError(run.child.error)
    assert.equal(run.child.status, 0, `status=${run.child.status} signal=${run.child.signal}`)
    const result = readJSON(path.join(run.output, 'result.json'))
    assert.ok(!result.error, JSON.stringify(result.error))
    assert.equal(run.records.find(row => row.signature?.stage === 'reproduce')?.signature.status, 'PASS', 'upstream fixture failed')
    assert.ok(run.record, 'no implement signature')
  })
  return run
}

// Order, operation, budget and the documented invocation for one smoke.
// `unobserved`: leading smokes of scripts that do not log (run9's own run_evaluation.sh).
function smokeInvocationChecks(run, expectedScript, { unobserved = 0 } = {}) {
  const { name, root, seal } = run
  check(`${name}: smoke runs after the baseline snapshot and before the test author, as adapter-smoke under method_run`, () => {
    assert.ok(run.smokes.length >= 1, 'no adapter-smoke receipt')
    const baseline = run.receipts.filter(row => row.operation === 'implement-baseline')
    assert.ok(baseline.length, 'no implement-baseline receipt')
    for (const smoke of run.smokes) {
      assert.ok(smoke.number > Math.max(...baseline.map(row => row.number)), `${smoke.name} precedes the baseline snapshot`)
      assert.equal(smoke.value.budget_s, run.budget, `${smoke.name} budget`)
      assert.equal(smoke.value.name, smoke.name)
    }
    const smokeLines = run.sequence.map((line, i) => [line, i]).filter(([line]) => line.startsWith('smoke '))
    assert.equal(smokeLines.length + unobserved, run.smokes.length, 'adapter invocations differ from adapter-smoke receipts')
    const firstAuthor = run.sequence.findIndex(line => ['agent tests', 'agent implement'].includes(line))
    if (firstAuthor !== -1) assert.ok(smokeLines.every(([, i]) => i < firstAuthor), 'an adapter smoke ran after an author call')
  })
  if (!run.observations.length) return
  check(`${name}: smoke runs ${expectedScript} in a fresh evaluation-work/smoke/0/baseline/ with the documented environment`, () => {
    const remote = remoteRun(root)
    const first = run.observations[0]
    assert.equal(first.label, expectedScript)
    // The smoke directory may be removed after the stage; getcwd() already resolved links.
    for (const row of run.observations) {
      assert.equal(row.cwd, path.join(remote, 'evaluation-work', 'smoke', '0', 'baseline'))
      const env = row.env
      assert.equal(env.EVAL_ARM, 'baseline')
      assert.equal(env.EVAL_MODE, 'equivalence')
      assert.ok(env.EVAL_PROTOCOL && path.isAbsolute(env.EVAL_PROTOCOL), 'EVAL_PROTOCOL is not an absolute path')
      assert.deepEqual(row.protocol, seal, 'EVAL_PROTOCOL is not the sealed predictions')
      assert.deepEqual(JSON.parse(env.EVAL_INPUTS), seal.evaluation_inputs, 'EVAL_INPUTS')
      assert.deepEqual(JSON.parse(env.EVAL_SEEDS), smokeSeeds(seal), 'EVAL_SEEDS')
      // "empty EVAL_COMPUTE_BUDGET": unset and the empty string are both empty in the shell.
      assert.ok(env.EVAL_COMPUTE_BUDGET === '' || env.EVAL_COMPUTE_BUDGET === null, `EVAL_COMPUTE_BUDGET=${env.EVAL_COMPUTE_BUDGET}`)
      for (const key of ['BASELINE_DIR', 'METHOD_DIR', 'BASELINE_OUT', 'METHOD_OUT', 'EVAL_OUT']) assert.ok(env[key] && path.isAbsolute(env[key]), `${key} not absolute`)
      assert.equal(env.METHOD_OUT, env.EVAL_OUT)
      assert.equal(path.resolve(row.cwd, env.EVAL_OUT), path.join(row.cwd, 'out'))
      assert.deepEqual(row.out, [], 'EVAL_OUT not empty at start')
      assert.equal(row.entries.out, 'dir')
      for (const tree of ['baseline-published', 'data', 'harness', 'baseline-out']) assert.equal(row.entries[tree], 'link', `${tree} is not linked`)
      // Fresh: nothing from an earlier smoke survives (each adapter writes stale-marker).
      assert.equal(row.entries['stale-marker'], undefined, 'work directory reused')
    }
  })
  check(`${name}: smoke logs and outputs are kept under A/results/implement/adapter/<attempt>/`, () => {
    const adapter = path.join(root, 'agent', 'results', 'implement', 'adapter')
    const logs = files(adapter).filter(file => file.endsWith('.log'))
    for (const smoke of run.smokes) {
      const log = logs.find(file => path.basename(file) === smoke.name + '.log')
      assert.ok(log, `missing ${smoke.name}.log`)
      assert.equal(path.dirname(path.dirname(log)), adapter, 'log not in an attempt directory')
    }
    const attempts = new Set(run.smokes.map(smoke => path.dirname(logs.find(file => path.basename(file) === smoke.name + '.log'))))
    assert.equal(attempts.size, run.smokes.length, 'smoke attempts share a directory')
  })
}

function passChecks(run) {
  check(`${run.name}: one passing smoke, no adapter repair, implement PASS`, () => {
    assert.equal(run.smokes.length, 1)
    assert.equal(run.smokes[0].value.rc, 0)
    assert.equal(run.repairs.length, 0)
    assert.equal(run.record?.signature.status, 'PASS', `implement ${run.record?.signature.status} ${run.record?.signature.error_class}`)
    assert.equal(run.calls.filter(call => call.title === 'tests').length, 1)
  })
  check(`${run.name}: fetched smoke output meets the reference criteria`, () => {
    const outputs = files(path.join(run.root, 'agent', 'results', 'implement', 'adapter')).filter(file => path.basename(file) === 'evaluation.json')
    assert.equal(outputs.length, 1, 'expected one fetched evaluation.json')
    assert.equal(smokeFailure(run.seal, readJSON(outputs[0])), null)
  })
}

function repairChecks(run, category, { logLines = true } = {}) {
  const { name, root } = run
  check(`${name}: exactly one adapter-repair call with the harness role and model, retry 1, fresh`, () => {
    assert.equal(run.repairs.length, 1)
    const [repair] = run.repairs
    assert.ok(run.harnessCall, 'no harness call to compare')
    assert.ok(run.harnessCall.role, 'harness call has no role to compare')
    assert.equal(repair.role, run.harnessCall.role, 'role')
    assert.equal(repair.model, run.harnessCall.model, 'model')
    // Agent option `retry: 1` reaches runners only as the `retry1` name descriptor (SCHEMAS.md naming).
    assert.match(repair.name || '', /-adapter-repair-retry1$/)
    for (const key of ['session', 'sessionID', 'resume', 'resumeSession']) assert.ok(!repair[key], `resumed via ${key}`)
    const at = run.sequence.indexOf('agent adapter-repair')
    if (!run.config.run9Script) assert.ok(at > run.sequence.findIndex(line => line.startsWith('smoke ')), 'repair before the first smoke')
    assert.ok(run.sequence.slice(0, at).every(line => !['agent tests', 'agent implement'].includes(line)), 'repair after an author call')
  })
  check(`${name}: repair receives the seal, intake, harness, category ${category} and the adapter interface`, () => {
    const [repair] = run.repairs
    const prompt = repair?.prompt || ''
    const seal = run.seal
    // "It receives the sealed predictions, intake files, current harness scripts": embedded in the
    // prompt or supplied as files in its view.
    const viewJSON = repair?.repairViewJSON || {}, view = repair?.repairView || {}
    const inView = (suffix, value) => Object.entries(viewJSON).some(([file, parsed]) => (file === suffix || file.endsWith('/' + suffix)) && isDeepStrictEqual(parsed, value))
    assert.ok(prompt.includes(seal.equivalence_metrics[0].source) || inView('PREDICTIONS.json', seal), `sealed predictions missing; view: ${Object.keys(view)}`)
    const intake = path.join(root, 'agent', 'intake')
    for (const file of fs.readdirSync(intake).filter(file => file.endsWith('.json'))) {
      const value = readJSON(path.join(intake, file))
      assert.ok(inView('intake/' + file, value) || (file === 'data.json' && prompt.includes(INTAKE_NOTE)), `intake ${file} missing`)
    }
    for (const [file, hash] of Object.entries(repair.harnessBefore)) {
      assert.ok(view['harness/' + file] === hash || (file === 'run_anchors.sh' && prompt.includes(HARNESS_NOTE)), `current harness/${file} missing`)
    }
    const stated = statedCategories(prompt)
    assert.deepEqual(stated, [category], `stated categories ${JSON.stringify(stated)}; context: ` +
      JSON.stringify([...prompt.matchAll(/categor(?:y|ies)/gi)].map(m => prompt.slice(m.index, m.index + 80))))
    for (const word of ['run_evaluation.sh', 'EVAL_OUT', 'evaluation.json', 'EVAL_ARM', 'EVAL_MODE', 'EVAL_PROTOCOL', 'EVAL_INPUTS', 'EVAL_SEEDS',
      'EVAL_COMPUTE_BUDGET', 'records', 'input_id', 'metrics', 'timing_scope', 'gpu_count', 'wall_s']) {
      assert.ok(prompt.includes(word), `interface omits ${word}`)
    }
  })
  if (logLines) check(`${name}: repair receives at most the last 200 log lines`, () => {
    const prompt = run.repairs[0]?.prompt || ''
    const lines = [...prompt.matchAll(/SMOKELOG:(\d+):end/g)].map(match => Number(match[1]))
    assert.ok(lines.length > 0 && lines.length <= 200, `${lines.length} log lines`)
    assert.ok(lines.includes(240), 'last log line missing')
    assert.ok(lines.every(n => n > 40), 'log lines older than the last 200 included')
  })
  check(`${name}: no harness script other than run_evaluation.sh changes, locally or on the box, and none runs`, () => {
    const [repair] = run.repairs
    assert.ok(repair, 'no repair call')
    const local = path.join(root, 'agent', 'harness'), remote = path.join(remoteRun(root), 'harness')
    for (const file of ['setup.sh', 'run_anchors.sh', 'run_command.sh']) {
      assert.equal(sha(fs.readFileSync(path.join(local, file))), repair.harnessBefore[file], `A/harness/${file} changed`)
      assert.equal(sha(fs.readFileSync(path.join(remote, file))), repair.harnessBefore[file], `remote ${file} changed`)
    }
    assert.ok(!files(remoteRun(root)).some(file => /stray-/.test(path.basename(file))), 'a stray rewritten script ran')
  })
  check(`${name}: rewritten run_evaluation.sh is copied to A/harness/, uploaded and smoked again`, () => {
    const [repair] = run.repairs
    assert.ok(repair, 'no repair call')
    const signature = run.record?.signature
    const state = `implement ${signature?.status} ${signature?.error_class}; smoke rc ${run.smokes.map(s => s.value.rc)}`
    const local = path.join(root, 'agent', 'harness'), remote = path.join(remoteRun(root), 'harness')
    assert.equal(run.smokes.length, 2, `expected exactly two smokes (${state})`)
    assert.equal(sha(fs.readFileSync(path.join(local, 'run_evaluation.sh'))), repair.repairedSha, 'A/harness/run_evaluation.sh')
    assert.equal(sha(fs.readFileSync(path.join(remote, 'run_evaluation.sh'))), repair.repairedSha, 'remote harness/run_evaluation.sh')
    const uploads = run.receipts.filter(row => row.operation === 'implement-upload' && row.number > run.smokes[0].number && row.number < run.smokes[1].number)
    assert.ok(uploads.length, 'no implement-upload between the smokes')
    if (run.observations.length) assert.equal(run.observations.at(-1).label, 'repaired', 'second smoke did not run the rewritten script')
  })
}

function continuedChecks(run) {
  check(`${run.name}: passing second smoke lets implement continue; authors see the repaired harness`, () => {
    assert.equal(run.smokes[1]?.value.rc, 0, `second smoke rc; implement ${run.record?.signature.status} ${run.record?.signature.error_class}, smokes ${run.smokes.length}`)
    assert.equal(run.record?.signature.status, 'PASS', `implement ${run.record?.signature.status} ${run.record?.signature.error_class}`)
    const [repair] = run.repairs
    for (const title of ['tests', 'implement']) {
      const call = run.calls.find(row => row.title === title)
      assert.ok(call, `no ${title} author call`)
      assert.equal(call.viewHarness?.['run_evaluation.sh'], repair.repairedSha, `${title} view lacks the repaired run_evaluation.sh`)
      for (const file of ['setup.sh', 'run_anchors.sh', 'run_command.sh']) assert.equal(call.viewHarness?.[file], repair.harnessBefore[file], `${title} view ${file}`)
    }
  })
}

function voidChecks(run, errorClass) {
  const exit = errorClass === 'timeout' ? 3 : 2
  check(`${run.name}: second failure stops implement VOID ${errorClass} (exit ${exit}) with null facts and no author or review`, () => {
    const signature = run.record?.signature
    assert.equal(signature?.status, 'VOID')
    assert.equal(signature.error_class, errorClass)
    assert.equal(signature.exit_code, exit)
    const facts = run.record.facts
    for (const key of FACTS) assert.equal(facts[key], null, key)
    const timeoutKeys = ['timed_out', 'budget_s', 'overrun']
    assert.deepEqual(Object.keys(facts).filter(key => !timeoutKeys.includes(key)).sort(), [...FACTS, 'tokens_known', 'gpu_busy_known'].sort())
    if ('timed_out' in facts) {
      assert.equal(typeof facts.timed_out, 'boolean'); assert.equal(typeof facts.overrun, 'boolean')
      assert.ok(Number.isInteger(facts.budget_s) && facts.budget_s >= 0)
    }
    assert.deepEqual(run.allCalls.filter(call => ['tests', 'implement', 'review'].includes(call.title)).map(call => call.title), [])
    assert.equal(fs.existsSync(path.join(run.root, 'control', 'implement', 'tests.json')), false, 'tests were frozen')
    assert.equal(run.records.find(row => row.signature?.stage === 'evaluate')?.signature.status, 'SKIPPED')
    assert.equal(run.records.find(row => row.signature?.stage === 'takeaways')?.signature.status, 'PASS')
  })
  check(`${run.name}: VOID implement signature validates`, () => {
    assert.equal(run.record?.schema_version, 2)
    validateSignature(run.record)
  })
}

function run9RecordedChecks() {
  // Regression from positive-openmm run9: evaluate was VOID because the pre-seal adapter wrote
  // records without the sealed metric names, while the method adapter keyed them by those names.
  const seal = readJSON(path.join(RUN9, 'PREDICTIONS.json'))
  const baseline = readJSON(RUN9_RECORDS.baseline), method = readJSON(RUN9_RECORDS.method)
  const first = seal.paired_seed_tests.seeds[0]
  const atFirst = report => ({ ...report, records: report.records.filter(row => row.seed === first) })
  check('run9 recorded: sealed metric names and first seed', () => {
    assert.deepEqual(seal.equivalence_metrics.map(metric => metric.name), ['mean_potential_kj_mol', 'final_potential_kj_mol'])
    assert.equal(first, 1000)
    assert.deepEqual(smokeSeeds(seal), { ...seal.paired_seed_tests, seeds: [1000] })
  })
  check('run9 recorded: baseline record for the first seed fails the smoke on metrics', () => {
    assert.equal(atFirst(baseline).records.length, 1)
    assert.equal(smokeFailure(seal, atFirst(baseline)), 'metrics')
    // The whole recorded baseline report (every sealed seed) is not the one-seed smoke shape either.
    assert.equal(smokeFailure(seal, baseline), 'records')
  })
  check('run9 recorded: method record for the first seed satisfies the smoke criteria', () => {
    assert.equal(atFirst(method).records.length, 1)
    assert.equal(smokeFailure(seal, atFirst(method)), null)
  })
}

async function main() {
  try {
    run9RecordedChecks()
    // 1, 2, 5: run_anchors.sh is smoked when run_evaluation.sh is absent; the smoke passes.
    const anchors = await scenario('smoke-anchors', {})
    smokeInvocationChecks(anchors, 'run_anchors')
    passChecks(anchors)
    check('smoke-anchors: method author prompt states the record metric names and shared meaning', () => {
      const author = anchors.calls.find(call => call.title === 'implement')
      assert.ok(author, 'missing method author call')
      assertMethodRecordRules(author.prompt)
      // Negative control: the matcher depends on the rule statements themselves.
      for (const word of [/defin/i, /\bkey/i]) {
        const stripped = author.prompt.split('\n').filter(line => !word.test(line)).join('\n')
        assert.throws(() => assertMethodRecordRules(stripped), undefined, `matcher passes without ${word}`)
      }
      assertEvalShapes(author.prompt, 'implement')
    })
    // run_evaluation.sh takes precedence (run_anchors.sh's adapter mode is broken here).
    const evaluation = await scenario('smoke-evaluation', { evaluation: true })
    smokeInvocationChecks(evaluation, 'run_evaluation')
    passChecks(evaluation)
    const deterministic = await scenario('smoke-deterministic', { evaluation: true, seal: 'deterministic' })
    smokeInvocationChecks(deterministic, 'run_evaluation')
    passChecks(deterministic)

    // 3: one repair, then implement continues.
    const repaired = await scenario('repair-exit', { evaluation: true, fault: 'exit' })
    smokeInvocationChecks(repaired, 'run_evaluation')
    repairChecks(repaired, 'exit')
    continuedChecks(repaired)
    // A repair that also rewrites setup.sh, run_anchors.sh and run_command.sh: those are not
    // accepted; its run_evaluation.sh is still the rewritten script that is copied and smoked.
    const stray = await scenario('repair-stray', { evaluation: true, fault: 'exit', stray: true })
    smokeInvocationChecks(stray, 'run_evaluation')
    repairChecks(stray, 'exit')
    continuedChecks(stray)
    // The repair creates run_evaluation.sh when only run_anchors.sh existed.
    const created = await scenario('repair-create', { anchorsFault: 'missing_output' })
    smokeInvocationChecks(created, 'run_anchors')
    repairChecks(created, 'missing_output')
    continuedChecks(created)

    // 2, 4: every failure category, repaired script failing again.
    for (const [fault, category] of [
      ['exit', 'exit'], ['missing_output', 'missing_output'],
      ['all_seeds', 'records'], ['order', 'records'], ['missing_input', 'records'], ['wrong_seed', 'records'],
      ['scope', 'records'], ['gpus', 'records'], ['wall', 'records'], ['no_wall', 'records'],
      ['missing_metric', 'metrics'], ['renamed_metric', 'metrics'], ['null_metric', 'metrics'], ['bool_metric', 'metrics'], ['string_metric', 'metrics'],
    ]) {
      const run = await scenario('void-' + fault, { evaluation: true, fault, repairFault: fault })
      smokeInvocationChecks(run, 'run_evaluation')
      check(`void-${fault}: fixture output is classified ${category} by the reference criteria`, () => {
        if (['exit', 'missing_output'].includes(fault)) return
        const outputs = files(path.join(run.root, 'agent', 'results', 'implement', 'adapter')).filter(file => path.basename(file) === 'evaluation.json')
        assert.ok(outputs.length, 'no fetched evaluation.json')
        for (const output of outputs) assert.equal(smokeFailure(run.seal, readJSON(output)), category)
      })
      repairChecks(run, category)
      voidChecks(run, 'parse')
    }
    for (const [name, config, category, errorClass] of [
      ['void-timeout', { fault: 'timeout', repairFault: 'timeout' }, 'timeout', 'timeout'],
      ['void-timeout-then-output', { fault: 'timeout', repairFault: 'missing_output' }, 'timeout', 'parse'],
      ['void-output-then-timeout', { fault: 'missing_output', repairFault: 'timeout' }, 'missing_output', 'timeout'],
    ]) {
      const run = await scenario(name, { evaluation: true, methodRun: 3, ...config })
      smokeInvocationChecks(run, 'run_evaluation')
      check(`${name}: timed-out smokes are recorded as box timeouts`, () => {
        const timedOut = run.smokes.map(smoke => smoke.value.timed_out || smoke.value.rc === 124)
        assert.deepEqual(timedOut, [config.fault === 'timeout', config.repairFault === 'timeout'])
      })
      repairChecks(run, category)
      voidChecks(run, errorClass)
    }

    // 6: run9 regression through the real implement stage.
    const python = fs.existsSync('/usr/bin/python3')
    check('run9 script: /usr/bin/python3 present to run run9 run_evaluation.sh unchanged [requires /usr/bin/python3]', () => assert.ok(python))
    if (python) {
      const script = await scenario('run9-script', { run9Script: true, repairFault: 'run9-method' })
      check('run9-script: run9 run_evaluation.sh is the first smoked script; its one-seed record lacks the sealed names', () => {
        assert.ok(script.smokes.length >= 1)
        // The fixture adapters log every invocation; run9's script does not.
        assert.equal(script.sequence.filter(line => line.startsWith('smoke ')).length, script.smokes.length - 1)
        const outputs = files(path.join(script.root, 'agent', 'results', 'implement', 'adapter')).filter(file => path.basename(file) === 'evaluation.json')
        const run9Output = outputs.map(readJSON).find(report => report.records?.[0]?.metrics && 'replica_0_wall_s' in report.records[0].metrics)
        assert.ok(run9Output, 'no fetched output from run9 run_evaluation.sh')
        assert.deepEqual(run9Output.records.map(row => row.seed), [1000])
        assert.equal(smokeFailure(script.seal, run9Output), 'metrics')
      })
      smokeInvocationChecks(script, 'repaired', { unobserved: 1 })
      repairChecks(script, 'metrics', { logLines: false })
      continuedChecks(script)
      const twice = await scenario('run9-script-twice', { run9Script: true, repairFault: 'run9-baseline' })
      smokeInvocationChecks(twice, 'repaired', { unobserved: 1 })
      repairChecks(twice, 'metrics', { logLines: false })
      voidChecks(twice, 'parse')
    }
    const recorded = await scenario('run9-recorded', { evaluation: true, run9: true, fault: 'run9-baseline', repairFault: 'run9-method' })
    smokeInvocationChecks(recorded, 'run_evaluation')
    repairChecks(recorded, 'metrics')
    continuedChecks(recorded)
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally { removeScratch(scratch) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : `all checks passed (${checks} checks)`)
  process.exitCode = failures ? 1 : 0
}
main()
