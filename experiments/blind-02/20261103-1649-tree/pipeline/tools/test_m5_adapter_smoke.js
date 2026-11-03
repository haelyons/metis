#!/usr/bin/env node
'use strict'

// Black-box U31/U32/U34 contracts: implement's baseline adapter smoke and its one adapter repair.
// Written from m5/SCHEMAS.md only ("Baseline adapter smoke:" in the implement section, the
// evaluation adapter interface and evaluation.json record rules). U32: the smoke receives the
// sealed paired_seed_tests unchanged and needs one record per sealed seed and input id, seeds
// first. U34: the smoke writes out/smoke.json and fails `cost` when one projected performance
// scorer exceeds 0.9 x the resolved evaluate budget. Do not inspect implementation files or git diffs.
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
const { launch, removeScratch, rows, files, sha, readJSON, RUN9, RUN9_RECORDS, RUN10, RUN12, run10Fakes, SEAL_SOURCE, INTAKE_NOTE, HARNESS_NOTE } = fixtures
const { assertEvalShapes } = require('./test_m5_reproduce.js')
const ROOT = path.resolve(__dirname, '..')
const CATEGORIES = ['exit', 'timeout', 'missing_output', 'records', 'metrics', 'cost']
const DEFAULT_EVALUATE = 2400 // SCHEMAS.md stage_budgets_s default
const FACTS = ['patch_applies', 'tests_pass', 'blind_tests', 'launch_review_pass']
const METHOD_RUN = 22 // fixture EXECUTION.stage_budgets_s.method_run

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_adapter_smoke_'))
let checks = 0, failures = 0
function check(label, fn) {
  checks++
  try { fn(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}

// SCHEMAS.md "Baseline adapter smoke": "`EVAL_SEEDS` equal to the sealed `paired_seed_tests` object
// unchanged. Evaluate never passes a subset of the sealed seeds, so the smoke does not either".
const smokeSeeds = seal => seal.paired_seed_tests
const finite = value => typeof value === 'number' && Number.isFinite(value)
// Every (seed, input id) pair: "seeds first, then input ids, in sealed order (seed null under a
// deterministic seal)".
const sealedPairs = seal => (seal.paired_seed_tests.kind === 'deterministic' ? [null] : seal.paired_seed_tests.seeds)
  .flatMap(seed => seal.evaluation_inputs.ids.map(id => [seed, id]))
// Reference pass criteria, from the same sentence: "one record per sealed seed and input id, seeds
// first, then input ids, in sealed order ...; the sealed `timing_scope`; the sealed `gpu_count`;
// finite positive `wall_s` for reported timing; and every sealed `equivalence_metrics` name in each
// record's `metrics` as a finite number". Returns null (pass) or the failure category.
function smokeFailure(seal, report) {
  if (!report || typeof report !== 'object' || Array.isArray(report)) return 'missing_output'
  const pairs = sealedPairs(seal)
  const records = report.records
  if (!Array.isArray(records) || records.length !== pairs.length) return 'records'
  if (records.some((row, i) => !row || row.seed !== pairs[i][0] || row.input_id !== pairs[i][1])) return 'records'
  if (!isDeepStrictEqual(report.timing_scope, seal.timing_scope)) return 'records'
  if (report.gpu_count !== seal.hardware_cost_basis.baseline_gpus) return 'records'
  if (seal.timing_scope.kind === 'reported_wall' && !(finite(report.wall_s) && report.wall_s > 0)) return 'records'
  for (const row of records) for (const { name } of seal.equivalence_metrics) {
    if (!row.metrics || !finite(row.metrics[name])) return 'metrics'
  }
  return null
}
// Reference cost projection, from the same bullet: "`projected_s` = (sealed `warmup` + sealed
// `repetitions`) × 2 × `process_wall_s` ... plus, unless `equal_outcome_target.not_applicable` is
// true, `b / baseline_gpus + b / method_gpus` for each sealed compute budget `b`". The smoke passes
// only when projected_s is at most 0.9 × the resolved evaluate budget.
function projectedSeconds(seal, processWall) {
  const { baseline_gpus, method_gpus } = seal.hardware_cost_basis
  const curve = seal.equal_outcome_target?.not_applicable === true ? 0
    : seal.compute_budgets.reduce((sum, b) => sum + b / baseline_gpus + b / method_gpus, 0)
  return (seal.warmup + seal.repetitions) * 2 * processWall + curve
}
const costFails = (seal, processWall, evaluateBudget) => projectedSeconds(seal, processWall) > 0.9 * evaluateBudget
// Seal fields of the fixture seal (tools/test_m5_implement.js) that the projection reads.
const FIXTURE_COST = { warmup: 1, repetitions: 5, compute_budgets: [1, 2, 4], hardware_cost_basis: { baseline_gpus: 1, method_gpus: 1, budget_unit: 'gpu_s' },
  equal_outcome_target: { not_applicable: true, reason: 'fixed-work fixture' } }
// Curve term with GPU counts other than 1: sum(b/2 + b/4) over [8, 16, 40] = 32 + 16 = 48.
const CURVE_PATCH = { warmup: 2, repetitions: 6, compute_budgets: [8, 16, 40],
  hardware_cost_basis: { baseline_gpus: 2, method_gpus: 4, budget_unit: 'gpu_s' },
  equal_outcome_target: { metric: 'value_sum', comparison: '>=', target: 0.9 } }
const NO_CURVE_PATCH = { ...CURVE_PATCH, equal_outcome_target: { not_applicable: true, reason: 'fixed-work fixture' } }
// A number stated in the prompt near its name (either side, within 120 characters). Integers may
// be spelled with a trailing `.0`.
const COST_NAMES = { process_wall_s: /process_wall_s|process wall/gi, warmup: /warmup/gi, repetitions: /repetitions/gi,
  projected_s: /projected/gi, evaluate_budget_s: /evaluate/gi }
function numberNear(text, pattern, value) {
  const literal = new RegExp(`(?<![\\d.])${String(value).replace('.', '\\.')}${Number.isInteger(value) ? '(?:\\.0+)?' : '0*'}(?!\\.?\\d)`)
  for (const match of text.matchAll(pattern)) {
    if (literal.test(text.slice(Math.max(0, match.index - 120), match.index + match[0].length + 120))) return true
  }
  return false
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
  // Fixtures that replace the fetched smoke.json are checked by injectedChecks instead.
  if (!run.config.smokeJson) smokeWallChecks(run)
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

// The fetched out/smoke.json of each smoke attempt (A/results/implement/adapter/<attempt>/).
function smokeJsonOf(run, smoke) {
  const adapter = path.join(run.root, 'agent', 'results', 'implement', 'adapter')
  const log = files(adapter).find(file => path.basename(file) === smoke.name + '.log')
  assert.ok(log, `missing ${smoke.name}.log`)
  const found = files(path.dirname(log)).filter(file => path.basename(file) === 'smoke.json')
  assert.equal(found.length, 1, `${smoke.name}: expected one fetched smoke.json, found ${found.length}`)
  return fs.readFileSync(found[0], 'utf8')
}
// "always writes `out/smoke.json` as exactly {"process_wall_s": <finite nonnegative number>},
// including after a nonzero exit or TERM". `walls[i]` optionally bounds attempt i: [min, max].
function smokeWallChecks(run, walls = []) {
  const bounded = walls.some(Boolean) ? ` within ${JSON.stringify(walls)}` : ''
  check(`${run.name}: every smoke writes out/smoke.json as exactly {"process_wall_s": x}, x finite and nonnegative${bounded}`, () => {
    assert.ok(run.smokes.length >= 1, 'no adapter-smoke receipt')
    run.smokes.forEach((smoke, i) => {
      const value = JSON.parse(smokeJsonOf(run, smoke)) // JSON.parse rejects NaN/Infinity spellings
      assert.ok(value && typeof value === 'object' && !Array.isArray(value), `${smoke.name}: not an object`)
      assert.deepEqual(Object.keys(value), ['process_wall_s'], `${smoke.name}: keys`)
      const wall = value.process_wall_s
      assert.ok(finite(wall) && wall >= 0, `${smoke.name}: process_wall_s=${wall}`)
      if (walls[i]) {
        const [min, max] = walls[i]
        assert.ok(wall >= min && wall <= max, `${smoke.name} (rc ${smoke.value.rc}, timed_out ${smoke.value.timed_out}): process_wall_s=${wall} outside [${min}, ${max}]`)
      }
    })
  })
}
// The fixture replaced (or removed) a fetched smoke.json for every injected adapter label that ran,
// so the scenario really exercised the injected value.
function injectedChecks(run) {
  check(`${run.name}: the fixture replaced the fetched smoke.json of every injected smoke ${JSON.stringify(run.config.smokeJson)}`, () => {
    const injected = rows(path.join(run.root, 'smoke-inject.jsonl'))
    const ran = new Set(run.observations.map(row => row.label))
    for (const label of Object.keys(run.config.smokeJson).filter(label => ran.has(label))) {
      const row = injected.find(entry => entry.label === label)
      assert.ok(row, `no fetched smoke.json from the ${label} smoke to replace`)
      const measured = JSON.parse(row.measured)
      assert.deepEqual(Object.keys(measured), ['process_wall_s'], `${label}: measured keys`)
      assert.ok(finite(measured.process_wall_s) && measured.process_wall_s >= 0, `${label}: measured ${row.measured}`)
    }
  })
}
// SCHEMAS.md: "for `cost` it also receives `process_wall_s`, the sealed warmup and repetitions,
// `projected_s` and the evaluate budget seconds, as numbers".
function costPromptChecks(run, expected) {
  check(`${run.name}: cost repair prompt states ${JSON.stringify(expected)} as numbers`, () => {
    const prompt = run.repairs[0]?.prompt || ''
    assert.ok(prompt, 'no adapter-repair prompt')
    const missing = Object.entries(expected).filter(([key, value]) => !numberNear(prompt, COST_NAMES[key], value)).map(([key, value]) => `${key}=${value}`)
    assert.deepEqual(missing, [], 'prompt omits ' + missing.join(', '))
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
  const atFirst = report => ({ ...report, records: report.records.filter(row => row.seed === 1000) })
  check('run9 recorded: sealed metric names and the full sealed seeds', () => {
    assert.deepEqual(seal.equivalence_metrics.map(metric => metric.name), ['mean_potential_kj_mol', 'final_potential_kj_mol'])
    assert.deepEqual(seal.paired_seed_tests.seeds, [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007])
    assert.deepEqual(smokeSeeds(seal), seal.paired_seed_tests)
  })
  check('run9 recorded: baseline records for every sealed seed fail the smoke on metrics', () => {
    assert.deepEqual(baseline.records.map(row => [row.seed, row.input_id]), sealedPairs(seal))
    assert.equal(smokeFailure(seal, baseline), 'metrics')
    // A single-seed subset is no longer the smoke shape.
    assert.equal(smokeFailure(seal, atFirst(baseline)), 'records')
  })
  check('run9 recorded: method records for every sealed seed satisfy the smoke criteria', () => {
    assert.deepEqual(method.records.map(row => [row.seed, row.input_id]), sealedPairs(seal))
    assert.equal(smokeFailure(seal, method), null)
    assert.equal(smokeFailure(seal, atFirst(method)), 'records')
  })
}

// Reference criteria on synthetic reports with two or more seeds and two or more inputs: only
// every (seed, input id) in seeds-first order passes.
function recordOrderChecks() {
  const seal = { evaluation_inputs: { ids: ['input-b', 'input-a'] }, paired_seed_tests: { kind: 'paired_median', seeds: [7, 3, 5] },
    equivalence_metrics: [{ name: 'value_sum' }], timing_scope: { kind: 'reported_wall' }, hardware_cost_basis: { baseline_gpus: 1 } }
  const report = pairs => ({ records: pairs.map(([seed, input_id]) => ({ input_id, seed, metrics: { value_sum: 1 } })),
    timing_scope: seal.timing_scope, gpu_count: 1, wall_s: 1 })
  const seedsFirst = [7, 3, 5].flatMap(seed => ['input-b', 'input-a'].map(id => [seed, id]))
  const inputsFirst = ['input-b', 'input-a'].flatMap(id => [7, 3, 5].map(seed => [seed, id]))
  check('reference criteria: seeds-first records for every sealed seed and input pass; deterministic seals use seed null', () => {
    assert.deepEqual(sealedPairs(seal), seedsFirst)
    assert.equal(smokeFailure(seal, report(seedsFirst)), null)
    const deterministic = { ...seal, paired_seed_tests: { kind: 'deterministic', justification: 'fixture' } }
    assert.equal(smokeFailure(deterministic, report([[null, 'input-b'], [null, 'input-a']])), null)
    assert.equal(smokeFailure(deterministic, report([[7, 'input-b'], [7, 'input-a']])), 'records')
  })
  for (const [label, pairs] of [
    ['missing seed', seedsFirst.filter(([seed]) => seed !== 5)],
    ['extra seed', [...seedsFirst, [8, 'input-b'], [8, 'input-a']]],
    ['single-seed subset', seedsFirst.filter(([seed]) => seed === 7)],
    ['inputs-first order', inputsFirst],
    ['sorted seeds', [3, 5, 7].flatMap(seed => ['input-b', 'input-a'].map(id => [seed, id]))],
  ]) check(`reference criteria: ${label} fails with records`, () => assert.equal(smokeFailure(seal, report(pairs)), 'records'))
}

// Reference projection on the scenario numbers below, so each pipeline scenario sits on the
// stated side of the 0.9 x evaluate boundary; and the matcher for numbers in the repair prompt.
function projectionChecks() {
  const curve = { ...FIXTURE_COST, ...CURVE_PATCH }, noCurve = { ...FIXTURE_COST, ...NO_CURVE_PATCH }
  check('reference projection: (warmup + repetitions) x 2 x process_wall_s plus the curve term at GPU counts 2 and 4', () => {
    assert.equal(projectedSeconds(curve, 53.25), 16 * 53.25 + 48)
    assert.equal(projectedSeconds(curve, 53.25), 900)
    assert.equal(projectedSeconds(curve, 53.3125), 901)
    // The curve term is omitted when not_applicable is true, and only then.
    assert.equal(projectedSeconds(noCurve, 53.3125), 853)
    assert.equal(projectedSeconds({ ...curve, equal_outcome_target: { ...curve.equal_outcome_target, not_applicable: false } }, 53.3125), 901)
  })
  check('reference projection: boundary at 0.9 x the evaluate budget (EXECUTION 1000, args 1240, default 2400)', () => {
    // EXECUTION.json evaluate=1000 wins over args 5000: 900 passes, 901 fails; args 5000 or the
    // default would pass both.
    assert.equal(costFails(curve, 53.25, 1000), false)
    assert.equal(costFails(curve, 53.3125, 1000), true)
    assert.equal(costFails(curve, 53.3125, 5000), false)
    assert.equal(costFails(curve, 53.3125, DEFAULT_EVALUATE), false)
    assert.equal(costFails(noCurve, 53.3125, 1000), false)
    // args evaluate=1240 (no EXECUTION evaluate): 12 x 93 = 1116 = 0.9 x 1240 passes; 1119 fails.
    assert.equal(projectedSeconds(FIXTURE_COST, 93), 1116)
    assert.equal(costFails(FIXTURE_COST, 93, 1240), false)
    assert.equal(costFails(FIXTURE_COST, 93.25, 1240), true)
    assert.equal(costFails(FIXTURE_COST, 93.25, DEFAULT_EVALUATE), false)
    // Category order and missing_output scenarios use these walls under the default budget.
    assert.equal(costFails(FIXTURE_COST, 100000, DEFAULT_EVALUATE), true)
    assert.equal(costFails(FIXTURE_COST, 1, DEFAULT_EVALUATE), false)
  })
  const run12 = readJSON(path.join(RUN12, 'PREDICTIONS.json'))
  check('run12 recorded: warmup 1, repetitions 8, no outcome curve, one GPU per arm; 488 s fails cost, 60 s passes', () => {
    assert.equal(run12.warmup, 1)
    assert.equal(run12.repetitions, 8)
    assert.equal(run12.equal_outcome_target.not_applicable, true)
    assert.equal(run12.hardware_cost_basis.baseline_gpus, 1)
    assert.equal(run12.hardware_cost_basis.method_gpus, 1)
    assert.equal(projectedSeconds(run12, 488), 8784)
    assert.equal(costFails(run12, 488, DEFAULT_EVALUATE), true)
    assert.equal(projectedSeconds(run12, 60), 1080)
    assert.equal(costFails(run12, 60, DEFAULT_EVALUATE), false)
    // The recorded evidence: ~488 s baseline invocations and a performance scorer timed out at 2,400 s.
    const raw = rows(path.join(RUN12, 'results', 'evaluate', 'raw.jsonl'))
      .filter(row => row.arm === 'baseline' && ['warmup', 'performance'].includes(row.phase) && finite(row.process_wall_s))
    assert.ok(raw.length && raw.every(row => Math.abs(row.process_wall_s - 488) < 5), 'run12 baseline process_wall_s')
    const receipt = readJSON(path.join(RUN12, '..', 'control', 'receipts', '0035-evaluate-performance.json'))
    assert.equal(receipt.timed_out, true)
    assert.equal(receipt.budget_s, DEFAULT_EVALUATE)
  })
  check('cost prompt matcher: a number counts only as itself, near its name', () => {
    assert.ok(numberNear('projected_s: 901.0 seconds.', COST_NAMES.projected_s, 901))
    assert.ok(numberNear('process_wall_s=53.3125', COST_NAMES.process_wall_s, 53.3125))
    assert.ok(!numberNear('projected_s: 9010', COST_NAMES.projected_s, 901))
    assert.ok(!numberNear('projected_s: 901.5', COST_NAMES.projected_s, 901))
    assert.ok(!numberNear('projected_s: 1' + ' '.repeat(200) + '901', COST_NAMES.projected_s, 901))
  })
}

// Check 1: EVAL_SEEDS in the smoke is the sealed paired_seed_tests object exactly.
function sealedSeedsCheck(run) {
  check(`${run.name}: EVAL_SEEDS in every smoke is JSON of the sealed paired_seed_tests object unchanged (${run.seal.paired_seed_tests.kind})`, () => {
    assert.ok(run.observations.length >= 1, 'no observed smoke invocation')
    for (const row of run.observations) {
      assert.equal(typeof row.env.EVAL_SEEDS, 'string', 'EVAL_SEEDS missing')
      const passed = JSON.parse(row.env.EVAL_SEEDS)
      assert.deepEqual(passed, run.seal.paired_seed_tests)
      assert.deepEqual(Object.keys(passed).sort(), Object.keys(run.seal.paired_seed_tests).sort(), 'keys differ')
      if (run.seal.paired_seed_tests.kind !== 'deterministic') assert.ok(passed.seeds.length >= 2, 'fixture seal needs several seeds')
    }
  })
}

// Check 3 (direct half): run10's recorded run_evaluation.sh against the driver stand-in, outside the
// pipeline, with the full sealed seeds and with EVAL_SEEDS cut to [1000].
function run10DirectChecks() {
  const seal = readJSON(path.join(RUN10, 'PREDICTIONS.json'))
  check('run10 recorded: seal has the eight replica seeds 1000..1007 and the two sealed metric names', () => {
    assert.deepEqual(seal.paired_seed_tests.seeds, [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007])
    assert.deepEqual(seal.equivalence_metrics.map(metric => metric.name), ['mean_potential_kj_mol', 'final_potential_kj_mol'])
  })
  const python = fs.existsSync('/usr/bin/python3')
  check('run10 script: /usr/bin/python3 present to run run10 run_evaluation.sh unchanged [requires /usr/bin/python3]', () => assert.ok(python))
  if (!python) return
  const work = fs.mkdtempSync(path.join(scratch, 'run10-direct-'))
  const capture = path.join(work, 'driver.jsonl')
  const built = spawnSync('bash', ['-euc', run10Fakes(capture)], { cwd: work, encoding: 'utf8' })
  fs.writeFileSync(path.join(work, 'PREDICTIONS.json'), JSON.stringify(seal))
  const invoke = (name, seeds) => {
    const out = path.join(work, name, 'out')
    fs.mkdirSync(out, { recursive: true })
    const result = spawnSync('bash', [path.join(RUN10, 'harness', 'run_evaluation.sh')], { cwd: path.join(work, name), encoding: 'utf8', timeout: 60000,
      env: { PATH: process.env.PATH, HOME: process.env.HOME, EVAL_OUT: out, METHOD_OUT: out, BASELINE_DIR: path.join(work, 'baseline-published'),
        METHOD_DIR: path.join(work, 'baseline-published'), BASELINE_OUT: path.join(work, 'baseline-out'), EVAL_ARM: 'baseline', EVAL_MODE: 'equivalence',
        EVAL_PROTOCOL: path.join(work, 'PREDICTIONS.json'), EVAL_INPUTS: JSON.stringify(seal.evaluation_inputs),
        EVAL_SEEDS: JSON.stringify(seeds), EVAL_COMPUTE_BUDGET: '' } })
    const file = path.join(out, 'evaluation.json')
    return { ...result, report: fs.existsSync(file) ? readJSON(file) : null }
  }
  check('run10 script: with the full sealed seeds it exits 0 and its output passes the smoke criteria', () => {
    assert.equal(built.status, 0, built.stderr)
    const full = invoke('full', seal.paired_seed_tests)
    assert.equal(full.status, 0, full.stderr)
    assert.deepEqual(full.report.records.map(row => [row.seed, row.input_id]), sealedPairs(seal))
    assert.equal(smokeFailure(seal, full.report), null)
    // The stand-in ran once per input id (the published ensemble covers every replica seed).
    assert.equal(rows(capture).length, seal.evaluation_inputs.ids.length)
  })
  check('run10 script: with EVAL_SEEDS cut to [1000] it exits nonzero on its sealed-seed check', () => {
    assert.equal(built.status, 0, built.stderr)
    const cut = invoke('cut', { ...seal.paired_seed_tests, seeds: [1000] })
    assert.notEqual(cut.status, 0)
    assert.equal(cut.report, null, 'cut run wrote evaluation.json')
    assert.match(cut.stderr, /Execution seeds must preserve the published eight replica seeds/)
  })
}

async function main() {
  try {
    run9RecordedChecks()
    recordOrderChecks()
    run10DirectChecks()
    projectionChecks()
    // 1, 2, 5: run_anchors.sh is smoked when run_evaluation.sh is absent; the smoke passes.
    const anchors = await scenario('smoke-anchors', {})
    smokeInvocationChecks(anchors, 'run_anchors')
    sealedSeedsCheck(anchors)
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
    sealedSeedsCheck(evaluation)
    passChecks(evaluation)
    check('smoke-evaluation: the passing smoke output has a record for every sealed seed and input id, seeds first', () => {
      assert.ok(evaluation.seal.paired_seed_tests.seeds.length >= 2 && evaluation.seal.evaluation_inputs.ids.length >= 2, 'fixture seal too small')
      const outputs = files(path.join(evaluation.root, 'agent', 'results', 'implement', 'adapter')).filter(file => path.basename(file) === 'evaluation.json')
      assert.equal(outputs.length, 1)
      assert.deepEqual(readJSON(outputs[0]).records.map(row => [row.seed, row.input_id]), sealedPairs(evaluation.seal))
    })
    const deterministic = await scenario('smoke-deterministic', { evaluation: true, seal: 'deterministic' })
    smokeInvocationChecks(deterministic, 'run_evaluation')
    sealedSeedsCheck(deterministic)
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
      ['first_seed', 'records'], ['missing_seed', 'records'], ['extra_seed', 'records'], ['inputs_first', 'records'], ['order', 'records'], ['missing_input', 'records'], ['wrong_seed', 'records'],
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
      // U34: smoke.json is written after TERM too, covering the adapter's run up to the 3 s budget.
      smokeWallChecks(run, [config.fault, config.repairFault].map(fault => fault === 'timeout' ? [1, 3 + 5] : null))
      repairChecks(run, category)
      voidChecks(run, errorClass)
    }

    // U34 check 1: smoke.json measures the adapter's run. The adapter sleeps 2 s, then passes, or
    // exits 3 (and the repaired adapter passes).
    const slept = await scenario('wall-sleep', { evaluation: true, fault: 'sleep' })
    smokeInvocationChecks(slept, 'run_evaluation')
    smokeWallChecks(slept, [[2, 2 + 5]])
    passChecks(slept)
    const sleptExit = await scenario('wall-sleep-exit', { evaluation: true, fault: 'sleep_exit' })
    smokeInvocationChecks(sleptExit, 'run_evaluation')
    smokeWallChecks(sleptExit, [[2, 2 + 5], [0, 5]])
    repairChecks(sleptExit, 'exit')
    continuedChecks(sleptExit)

    // U34 check 2: the projection boundary, with the curve term at GPU counts 2 and 4 and the
    // evaluate budget from EXECUTION.json (1000, over args 5000), then from args (1240).
    const execBudget = { evaluation: true, evaluateBudget: 1000, argsBudgets: { evaluate: 5000 } }
    const execAt = await scenario('cost-exec-at', { ...execBudget, sealPatch: CURVE_PATCH, smokeJson: { run_evaluation: 53.25 } })
    smokeInvocationChecks(execAt, 'run_evaluation')
    injectedChecks(execAt)
    passChecks(execAt)
    const execOver = await scenario('cost-exec-over', { ...execBudget, sealPatch: CURVE_PATCH, smokeJson: { run_evaluation: 53.3125, repaired: 53.3125 } })
    smokeInvocationChecks(execOver, 'run_evaluation')
    injectedChecks(execOver)
    repairChecks(execOver, 'cost')
    costPromptChecks(execOver, { process_wall_s: 53.3125, warmup: 2, repetitions: 6, projected_s: 901, evaluate_budget_s: 1000 })
    voidChecks(execOver, 'parse')
    // Same wall, no outcome curve: 853 <= 900 passes.
    const execNoCurve = await scenario('cost-exec-no-curve', { ...execBudget, sealPatch: NO_CURVE_PATCH, smokeJson: { run_evaluation: 53.3125 } })
    smokeInvocationChecks(execNoCurve, 'run_evaluation')
    injectedChecks(execNoCurve)
    passChecks(execNoCurve)
    const argsAt = await scenario('cost-args-at', { evaluation: true, argsBudgets: { evaluate: 1240 }, smokeJson: { run_evaluation: 93 } })
    smokeInvocationChecks(argsAt, 'run_evaluation')
    injectedChecks(argsAt)
    passChecks(argsAt)
    // U34 check 4 (repair continues): cost, then a passing second smoke.
    const argsOver = await scenario('cost-args-over', { evaluation: true, argsBudgets: { evaluate: 1240 }, smokeJson: { run_evaluation: 93.25, repaired: 10 } })
    smokeInvocationChecks(argsOver, 'run_evaluation')
    injectedChecks(argsOver)
    repairChecks(argsOver, 'cost')
    costPromptChecks(argsOver, { process_wall_s: 93.25, warmup: 1, repetitions: 5, projected_s: 1119, evaluate_budget_s: 1240 })
    continuedChecks(argsOver)

    // U34 check 3: records and metrics are decided before cost, even with a ruinous wall.
    for (const [fault, category] of [['missing_seed', 'records'], ['missing_metric', 'metrics']]) {
      const run = await scenario(`order-${category}`, { evaluation: true, fault, smokeJson: { run_evaluation: 100000, repaired: 1 } })
      smokeInvocationChecks(run, 'run_evaluation')
      injectedChecks(run)
      repairChecks(run, category)
      continuedChecks(run)
    }
    // Missing or malformed smoke.json after records and metrics pass is missing_output.
    for (const [name, first, second] of [
      ['json-extra-key', '{"process_wall_s": 1, "extra": 1}', 1],
      ['json-nan', '{"process_wall_s": NaN}', '{"process_wall_s": -1}'],
      ['json-missing', 'missing', 'not json'],
      ['json-string', '{"process_wall_s": "1"}', '{"process_wall_s": true}'],
      ['json-array', '[1]', '{"process_wall_s": Infinity}'],
    ]) {
      const run = await scenario(name, { evaluation: true, smokeJson: { run_evaluation: first, repaired: second } })
      smokeInvocationChecks(run, 'run_evaluation')
      injectedChecks(run)
      repairChecks(run, 'missing_output')
      if (finite(second)) continuedChecks(run); else voidChecks(run, 'parse')
    }
    // A stale smoke.json is never read: the first smoke fails records with a valid, passing
    // smoke.json; the second passes records but its smoke.json is missing, so it fails
    // missing_output (VOID), never passing on the first smoke's measurement.
    const stale = await scenario('stale-smoke-json', { evaluation: true, fault: 'missing_seed', smokeJson: { repaired: 'missing' } })
    smokeInvocationChecks(stale, 'run_evaluation')
    injectedChecks(stale)
    check('stale-smoke-json: the first smoke left a valid passing smoke.json behind', () => {
      const first = JSON.parse(smokeJsonOf(stale, stale.smokes[0]))
      assert.ok(finite(first.process_wall_s) && !costFails(stale.seal, first.process_wall_s, DEFAULT_EVALUATE), JSON.stringify(first))
    })
    repairChecks(stale, 'records')
    voidChecks(stale, 'parse')

    // U34 check 5 (and 4): run12's seal with its measured 488 s baseline invocation fails cost; 60 s
    // passes; a 60 s repair continues; a second 488 s smoke stops implement.
    const run12Pass = await scenario('run12-60s', { evaluation: true, run12: true, smokeJson: { run_evaluation: 60 } })
    smokeInvocationChecks(run12Pass, 'run_evaluation')
    injectedChecks(run12Pass)
    passChecks(run12Pass)
    const run12Repaired = await scenario('run12-488s-then-60s', { evaluation: true, run12: true, smokeJson: { run_evaluation: 488, repaired: 60 } })
    smokeInvocationChecks(run12Repaired, 'run_evaluation')
    injectedChecks(run12Repaired)
    repairChecks(run12Repaired, 'cost')
    costPromptChecks(run12Repaired, { process_wall_s: 488, warmup: 1, repetitions: 8, projected_s: 8784, evaluate_budget_s: DEFAULT_EVALUATE })
    continuedChecks(run12Repaired)
    const run12Twice = await scenario('run12-488s-twice', { evaluation: true, run12: true, smokeJson: { run_evaluation: 488, repaired: 488 } })
    smokeInvocationChecks(run12Twice, 'run_evaluation')
    injectedChecks(run12Twice)
    repairChecks(run12Twice, 'cost')
    costPromptChecks(run12Twice, { process_wall_s: 488, warmup: 1, repetitions: 8, projected_s: 8784, evaluate_budget_s: DEFAULT_EVALUATE })
    voidChecks(run12Twice, 'parse')

    // 6: run9 regression through the real implement stage.
    const python = fs.existsSync('/usr/bin/python3')
    check('run9 script: /usr/bin/python3 present to run run9 run_evaluation.sh unchanged [requires /usr/bin/python3]', () => assert.ok(python))
    if (python) {
      const script = await scenario('run9-script', { run9Script: true, repairFault: 'run9-method' })
      check('run9-script: run9 run_evaluation.sh is the first smoked script; its records for every sealed seed lack the sealed names', () => {
        assert.ok(script.smokes.length >= 1)
        // The fixture adapters log every invocation; run9's script does not.
        assert.equal(script.sequence.filter(line => line.startsWith('smoke ')).length, script.smokes.length - 1)
        const outputs = files(path.join(script.root, 'agent', 'results', 'implement', 'adapter')).filter(file => path.basename(file) === 'evaluation.json')
        const run9Output = outputs.map(readJSON).find(report => report.records?.[0]?.metrics && 'replica_0_wall_s' in report.records[0].metrics)
        assert.ok(run9Output, 'no fetched output from run9 run_evaluation.sh')
        assert.deepEqual(run9Output.records.map(row => [row.seed, row.input_id]), sealedPairs(script.seal))
        assert.deepEqual(script.seal.paired_seed_tests.seeds, [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007])
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

    // 3: run10 regression through the real implement stage. run10's repaired run_evaluation.sh
    // rejects any seed list other than the eight sealed seeds; it exited 1 under the one-seed cut and
    // implement stopped VOID. Under the full sealed seeds it passes the first smoke.
    if (python) {
      const run10 = await scenario('run10-script', { run10Script: true })
      smokeInvocationChecks(run10, 'run_evaluation', { unobserved: 1 })
      passChecks(run10)
      check('run10-script: the smoked script is run10 run_evaluation.sh, given the sealed seeds unchanged', () => {
        assert.deepEqual(run10.seal.paired_seed_tests.seeds, [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007])
        const local = path.join(run10.root, 'agent', 'harness', 'run_evaluation.sh')
        assert.equal(sha(fs.readFileSync(local)), sha(fs.readFileSync(path.join(RUN10, 'harness', 'run_evaluation.sh'))), 'A/harness/run_evaluation.sh changed')
        const driver = rows(path.join(run10.root, 'run10-driver.jsonl'))
        assert.equal(driver.length, run10.seal.evaluation_inputs.ids.length, 'driver stand-in invocations')
        for (const row of driver) {
          assert.ok(row.cwd.includes(path.join('evaluation-work', 'smoke', '0', 'baseline')), `driver ran outside the smoke directory: ${row.cwd}`)
          assert.deepEqual(JSON.parse(row.EVAL_SEEDS), run10.seal.paired_seed_tests, 'EVAL_SEEDS')
          assert.deepEqual(JSON.parse(row.EVAL_INPUTS), run10.seal.evaluation_inputs, 'EVAL_INPUTS')
        }
        const outputs = files(path.join(run10.root, 'agent', 'results', 'implement', 'adapter')).filter(file => path.basename(file) === 'evaluation.json')
        assert.deepEqual(readJSON(outputs[0]).records.map(row => [row.seed, row.input_id]), sealedPairs(run10.seal))
      })
    }
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally { removeScratch(scratch) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : `all checks passed (${checks} checks)`)
  process.exitCode = failures ? 1 : 0
}
main()
