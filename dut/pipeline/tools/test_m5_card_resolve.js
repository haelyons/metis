#!/usr/bin/env node
'use strict'

// Black-box contract tests for `node m5/card_resolve.js` (U56): m5/SCHEMAS.md "Card write-back and re-judging
// (U56)", with the card records of "Card calibration (U54)" and the `calibration` record of CONTRACT.md (U55).
// Never inspect m5/card_resolve.js, src/ or git history. Every run root is built by hand (control/card.json,
// card_seal.json and card_scored.json in their contract shapes); the tool is run as a program and only its exit
// status, its output file and the files around it are read. treeCases() also runs the built tree under idea/wf.js
// with the stub agents of tools/test_tree_calibration_u55.js, to obtain the tree's own gate reasons black-box.
// Usage: node tools/test_m5_card_resolve.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const crypto = require('node:crypto')
const assert = require('node:assert/strict')
const { spawnSync } = require('node:child_process')

const ROOT = path.resolve(__dirname, '..')
const TOOL = path.join(ROOT, 'm5', 'card_resolve.js')
const PLAN = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures/gates/plan.json'), 'utf8'))
const SHEET = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures/cost/price_sheet.json'), 'utf8'))
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_card_resolve_'))
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
const clone = value => JSON.parse(JSON.stringify(value))
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
let checks = 0, failures = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${String(error.message).replace(/\s*\n\s*/g, ' ').slice(0, 1500)}`) }
}
function writeJSON(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  const bytes = Buffer.from(JSON.stringify(value, null, 1) + '\n')
  fs.writeFileSync(file, bytes)
  return bytes
}
// Relative path -> base64 bytes of every regular file under a directory.
function contents(directory) {
  const result = {}
  const visit = (parent, prefix) => {
    for (const entry of fs.readdirSync(parent, { withFileTypes: true })) {
      const file = path.join(parent, entry.name)
      if (entry.isDirectory()) visit(file, prefix + entry.name + '/')
      else result[prefix + entry.name] = fs.readFileSync(file).toString('base64')
    }
  }
  if (fs.existsSync(directory)) visit(directory, '')
  return result
}
function near(actual, expected, label) {
  assert.ok(typeof actual === 'number' && Math.abs(actual - expected) <= 1e-6 * Math.max(1, Math.abs(expected)),
    `${label}: ${actual} != ${expected}`)
}

// ---- The tree result (CONTRACT.md `calibration` in the return) --------------------------------------------
// A: the fixture plan's load-bearing PROXY `steps_per_h`, with a hand-built `judged` for re-judging.
// Its cost: pilot 2 h + sweep 126000 / steps_per_h h, both at 8 x 3.99 $/h (the price sheet's 8x H100 rate).
const RATE = 8 * 3.99
const planned = stepsPerHour => RATE * 2 + RATE * 126000 / stepsPerHour
const required = (id, basis, value, extra = {}) => ({ id, name: `name of ${id}`, unit: `unit of ${id}`, band: null, basis, value,
  differs_in: basis === 'PROXY' ? ['model size'] : [], measured_by: 'P1', cum_spend_through_measured_by: 63.84, k_budget: 1.04,
  phase: { id: 'P1', what: 'pilot: throughput and reproduction' }, line: 'pilot', ...extra })
const JUDGED = {
  plan: clone(PLAN),
  pick: { key: 'R1:physical:W1', root: 'R1', branch: 'physical', kind: 'top', rank: 1, total: 24, tie_note: null, replaced: [],
    title: PLAN.option_title },
  given: { budget_usd: 1000, price_sheet: SHEET, budget_covers_storage: true, budget_covers_tax: true },
  gate_args: { budget_usd: 1000, require_compute_lever: { physical: true, interp: true }, picks_per_branch: 2, pool_k: 2 },
}
const REC_A = { key: 'R1:physical:W1', title: PLAN.option_title, state: 'calibration_required', plan_usd: planned(5000),
  required: [required('steps_per_h', 'PROXY', 5000, { phase: clone(PLAN.phases[0]) })], resolved: [],
  anchor: clone(PLAN.anchor), predictions: clone(PLAN.predictions), judged: JUDGED }
// B: two required ids, judged null (rejudged null).
const REC_B = { key: 'R2:interp:W3', title: 'bravo basalt probe', state: 'calibration_required', plan_usd: 412.5,
  required: [required('a_rate', 'PROXY', 40), required('b_lat', 'GUESS', 2.5, { measured_by: 'P2' })], resolved: [],
  anchor: { absent_reason: 'no published value' }, predictions: { if_lever: 'x 5', if_not: 'y 2' }, judged: null }
// D: a record without the `judged` key at all.
const REC_D = { key: 'R3:physical:W2', title: 'delta quartz flow', state: 'calibration_required', plan_usd: 99,
  required: [required('c_frac', 'GUESS', 0.3)], resolved: [], anchor: null, predictions: null }
// C and E: records no run names.
const REC_C = { key: 'seed:idea:seed', title: 'an idea from the human', state: 'no_unmeasured_input', plan_usd: 10, required: [],
  resolved: [], anchor: null, predictions: null, judged: null }
const REC_E = { key: 'R1:interp:W4', title: 'rejected one', state: 'rejected', plan_usd: null, required: [], resolved: [],
  anchor: null, predictions: null, judged: null }
const RESULT = { table: '| Pick | Result |', cards: ['card one', 'card two'], inventory: [], frontier: '', log: ['x'],
  result_md: '# r', price_sheet: SHEET, calibration: [REC_A, REC_B, REC_C, REC_D, REC_E] }

// ---- Hand-built run roots ---------------------------------------------------------------------------------
// A card_scored.json row exactly as U54 computes it (m5/SCHEMAS.md "Card calibration (U54)", Scoring): since the
// second review card_resolve.js rejects rows whose fields disagree with U54's rules, every fixture row is built here.
const finiteNumber = x => typeof x === 'number' && Number.isFinite(x)
function u54Row(item, rule, measured, bands = {}) {
  const value = item.value
  const own = item.band
  const ownAbs = own && typeof own === 'object' && !Array.isArray(own) && Object.keys(own).join() === 'abs' && finiteNumber(own.abs) && own.abs > 0
  let source = null, lo = null, hi = null
  if ((Object.hasOwn(bands, item.id) || ownAbs) && finiteNumber(value)) {
    const half = Object.hasOwn(bands, item.id) ? bands[item.id].abs : own.abs
    source = Object.hasOwn(bands, item.id) ? 'launch' : 'card'
    lo = value - half; hi = value + half
  } else if (finiteNumber(value) && value !== 0) {
    const k = item.basis === 'PROXY' ? 2.5 : 3
    source = 'multiplicative'
    ;[lo, hi] = value > 0 ? [value / k, value * k] : [value * k, value / k]
  }
  const verdict = measured === null ? 'not_measured' : lo === null ? 'no_band'
    : measured < lo ? 'below_band' : measured > hi ? 'above_band' : 'within_band'
  const gate = item.phase && typeof item.phase === 'object' ? item.phase.gate : null
  const gatePassed = gate && typeof gate === 'object' && gate.on === item.id && ['>=', '<='].includes(gate.op) && finiteNumber(gate.value)
    && typeof measured === 'number' ? (gate.op === '>=' ? measured >= gate.value : measured <= gate.value) : null
  const decidedBy = typeof gatePassed === 'boolean' ? 'gate' : ['within_band', 'below_band', 'above_band'].includes(verdict) ? 'band' : null
  const decision = decidedBy === 'gate' ? (gatePassed ? 'holds' : 'refuted') : decidedBy === 'band' ? (verdict === 'within_band' ? 'holds' : 'refuted')
    : measured === null ? 'not_measured' : 'undecidable'
  return { id: item.id, name: item.name ?? null, unit: item.unit ?? null, basis: item.basis, value: item.value ?? null,
    band_source: source, band_lo: lo, band_hi: hi, measured_value: measured, verdict, gate_passed: gatePassed, decided_by: decidedBy,
    decision, rule }
}
// rows: [{ id, measured, decision?, rule? }] for the record's `required` ids; `decision` is the fixture's intent,
// checked against what U54 gives (a mismatch is a fixture error).
function scoredRow(record, spec, bands = {}) {
  const item = record.required.find(entry => entry.id === spec.id) ?? { id: spec.id, name: null, unit: null, basis: 'GUESS', value: 1 }
  const row = u54Row(item, spec.rule ?? { file: `card/${spec.id}.json`, kind: 'json', expr: `/value/${spec.id}` }, spec.measured, bands)
  if (spec.decision !== undefined && row.decision !== spec.decision)
    throw new Error(`fixture: ${record.key} ${spec.id} measured ${spec.measured} gives ${row.decision}, not ${spec.decision}`)
  return row
}
const totalsOf = rows => ({ inputs_total: rows.length, measured_total: rows.filter(row => typeof row.measured_value === 'number').length,
  holds_total: rows.filter(row => row.decision === 'holds').length, refuted_total: rows.filter(row => row.decision === 'refuted').length })
// opts: { record, rows, run, commit, box: {type, started_utc} | null, result (file), bands }
function makeRun(dir, opts) {
  const control = path.join(dir, 'control')
  const resultBytes = fs.readFileSync(opts.result)
  const card = { source: opts.result, source_sha256: sha(resultBytes), record: opts.record, bands: opts.bands ?? {} }
  const cardBytes = writeJSON(path.join(control, 'card.json'), card)
  writeJSON(path.join(control, 'card_seal.json'), { card_sha256: sha(cardBytes), sealed_utc: '2026-11-03T10:00:00Z' })
  const rows = opts.rows.map(spec => scoredRow(opts.record, spec, opts.bands ?? {}))
  const box = opts.box === undefined ? { type: 'gpu_1x_a10', started_utc: '2026-11-03T09:00:00Z' } : opts.box
  writeJSON(path.join(control, 'card_scored.json'), { key: opts.record.key, run: opts.run, pipeline_commit: opts.commit ?? null,
    box_type: box?.type ?? null, box_started_utc: box?.started_utc ?? null, card_sha256: sha(cardBytes),
    extract_sha256: 'e'.repeat(64), predictions: opts.record.predictions ?? null, anchor: null, rows, ...totalsOf(rows) })
  // Box and agent files a real run also holds; the tool reads only control/.
  writeJSON(path.join(control, 'box.json'), box ?? {})
  writeJSON(path.join(dir, 'agent', 'card_inputs.json'), { inputs: [], anchor: null })
  return { dir, rows, run: opts.run, commit: opts.commit ?? null, box, record: opts.record }
}
// The entry the contract writes for one scored row of one run.
function entryFor(run, row) {
  const box = run.box
  return { run: run.run, pipeline_commit: run.commit, box_type: box?.type ?? null, box_started_utc: box?.started_utc ?? null,
    id: row.id, measured_value: row.measured_value, verdict: row.verdict, decided_by: row.decided_by, decision: row.decision,
    number: row.measured_value === null ? null : { id: row.id, name: row.name, unit: row.unit, basis: 'MEASURED',
      value: row.measured_value, differs_in: [], command: 'bash harness/run_command.sh',
      output: `${path.basename(run.dir)}/agent/results/reproduce/out/${row.rule.file}`,
      output_line: `${row.rule.kind}: ${row.rule.expr}`, machine: box?.type ?? null } }
}

// ---- Running the tool -------------------------------------------------------------------------------------
let caseNumber = 0
function setup(name, resultValue = RESULT) {
  const dir = path.join(scratch, `${String(++caseNumber).padStart(2, '0')}-${name}`)
  fs.mkdirSync(dir, { recursive: true })
  const result = path.join(dir, 'tree run', 'result.json')
  const resultBytes = writeJSON(result, resultValue)
  return { dir, result, resultBytes, resultValue, outDir: path.join(dir, 'resolved'), out: path.join(dir, 'resolved', 'calibration.json') }
}
function resolve(argv, cwd = ROOT) {
  const proc = spawnSync(process.execPath, [TOOL, ...argv], { cwd, encoding: 'utf8', timeout: 60000 })
  return { status: proc.status, stdout: proc.stdout ?? '', stderr: proc.stderr ?? '', error: proc.error }
}
const why = r => `exit ${r.status}; ${(r.stderr || '').slice(-800)}${r.error ? ` ${r.error.message}` : ''}`
// A successful run: exit 0, exact top level, result.json and every input unchanged, only the output written.
function okRun(name, c, runs, argv = null, cwd = ROOT) {
  const inputs = Object.fromEntries(runs.map(run => [run.dir, contents(run.dir)]))
  fs.mkdirSync(c.outDir, { recursive: true })
  const r = resolve(argv ?? [c.result, ...runs.map(run => run.dir), '--out', c.out], cwd)
  check(`${name}: exit 0 and the output written`, () => {
    assert.ifError(r.error)
    assert.equal(r.status, 0, why(r))
    assert.ok(fs.existsSync(c.out), 'no output file')
  })
  check(`${name}: result.json bytes and every run root unchanged; only the output file written`, () => {
    assert.ok(fs.readFileSync(c.result).equals(c.resultBytes), 'result.json changed')
    for (const run of runs) assert.deepEqual(contents(run.dir), inputs[run.dir], `${run.dir} changed`)
    assert.deepEqual(fs.readdirSync(c.outDir), ['calibration.json'], 'stray file next to the output')
  })
  const value = fs.existsSync(c.out) ? read(c.out) : null
  if (value) check(`${name}: exactly {source, source_sha256, calibration}; source absolute, SHA-256 of result.json`, () => {
    assert.deepEqual(Object.keys(value).sort(), ['calibration', 'source', 'source_sha256'])
    assert.equal(value.source, c.result, 'source is not the absolute path of result.json')
    assert.equal(value.source_sha256, sha(c.resultBytes))
    assert.ok(Array.isArray(value.calibration) && value.calibration.length === c.resultValue.calibration.length, 'calibration length')
  })
  return value
}
// Records no run names stay exactly as in result.json.
function unchangedOthers(name, value, named) {
  if (!value) return
  check(`${name}: records no run names are unchanged (${RESULT.calibration.filter(rec => !named.includes(rec.key)).map(rec => rec.key).join(', ')})`, () => {
    RESULT.calibration.forEach((record, i) => {
      if (!named.includes(record.key)) assert.deepEqual(value.calibration[i], record, record.key)
    })
  })
}
// A named record: every original field unchanged except `state` and `resolved`, plus `rejudged`.
function namedRecord(name, value, original, { entries, state, judged = true }) {
  if (!value) return null
  const record = value.calibration[RESULT.calibration.findIndex(rec => rec.key === original.key)]
  check(`${name}: ${original.key}: resolved entries (existing first, then runs in argument order)`, () => {
    assert.deepEqual(record.resolved, entries)
  })
  check(`${name}: ${original.key}: state ${state}`, () => assert.equal(record.state, state))
  check(`${name}: ${original.key}: other fields unchanged; ${judged ? 'rejudged present' : 'rejudged null'}`, () => {
    const { resolved, state: _s, rejudged, ...rest } = record
    const { resolved: _r, state: _o, ...want } = original
    assert.deepEqual(rest, want)
    assert.ok(Object.hasOwn(record, 'rejudged'), 'named record lacks rejudged')
    if (!judged) assert.equal(rejudged, null)
  })
  return record
}
// An exit-1 case: nothing written (no output, no stray file), inputs unchanged.
function refused(name, c, runs, argv, { outIsInput = null } = {}) {
  const inputs = Object.fromEntries(runs.map(run => [run.dir, contents(run.dir)]))
  fs.mkdirSync(c.outDir, { recursive: true })
  const before = contents(c.outDir)
  const r = resolve(argv)
  check(`${name}: exit 1 and nothing written`, () => {
    assert.ifError(r.error)
    assert.equal(r.status, 1, why(r))
    if (!outIsInput) assert.equal(fs.existsSync(c.out), false, 'output written')
    assert.deepEqual(contents(c.outDir), before, 'files written next to the output')
    assert.ok(fs.readFileSync(c.result).equals(c.resultBytes), 'result.json changed')
    for (const run of runs) assert.deepEqual(contents(run.dir), inputs[run.dir], `${run.dir} changed`)
  })
}

// ---- Tree runs (stub agents) ------------------------------------------------------------------------------
// The tree bundle under idea/wf.js with the stub runner of tools/test_tree_calibration_u55.js (WF_STUB), as that
// suite runs it; U55_PLAN_OVERRIDES makes the producer return a given plan for a given option title.
const WF = path.join(ROOT, 'idea', 'wf.js')
const BUNDLE = path.join(ROOT, 'dist', 'question_tree_v2.js')
const STUB = path.join(ROOT, 'tools', 'test_tree_calibration_u55.js')
const TREE_ARGS = { seed: 1, fixed_roots: ['root one', 'root two'], seed_ideas: ['an idea from the human'], budget_usd: 1000,
  require_compute_lever: { physical: true, interp: true }, pool_k: 3, picks_per_branch: 2 }
function treeRun(name, overrides = null) {
  const dir = path.join(scratch, 'tree')
  fs.mkdirSync(path.join(dir, 'home'), { recursive: true })
  fs.mkdirSync(path.join(dir, 'base'), { recursive: true })
  const args = path.join(dir, 'args.json')
  if (!fs.existsSync(args)) writeJSON(args, { ...TREE_ARGS, base: path.join(dir, 'base') })
  const out = path.join(dir, name), log = path.join(dir, `${name}.log`), prompts = path.join(dir, `${name}-prompts.jsonl`)
  const env = { ...process.env, HOME: path.join(dir, 'home'), WF_STUB: STUB, U55_CALLS: path.join(dir, `${name}-calls.jsonl`),
    U55_PROMPTS: prompts, U55_BUNDLE: BUNDLE }
  if (overrides) env.U55_PLAN_OVERRIDES = path.join(dir, `${name}-plans.json`), writeJSON(env.U55_PLAN_OVERRIDES, overrides)
  const fd = fs.openSync(log, 'w')
  let proc
  try {
    proc = spawnSync(process.execPath, [WF, '--script', BUNDLE, '--args', args, '--out', out, '--disable-family', 'claude'],
      { cwd: ROOT, env, timeout: 300000, killSignal: 'SIGKILL', stdio: ['ignore', fd, fd] })
  } finally { fs.closeSync(fd) }
  const resultFile = path.join(out, 'result.json')
  const result = fs.existsSync(resultFile) ? read(resultFile) : null
  check(`tree ${name}: the stub tree run completes (fixture)`, () => {
    assert.ifError(proc.error)
    assert.equal(proc.status, 0, `exit ${proc.status} ${proc.signal}; ${fs.readFileSync(log, 'utf8').slice(-600)}`)
    assert.ok(result && !result.error && Array.isArray(result.calibration), `result error: ${result?.error}`)
  })
  const promptRows = fs.existsSync(prompts) ? fs.readFileSync(prompts, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
  return { out, result, prompts: promptRows }
}
// The plan the contract's re-judging evaluates: each measured id's numbers entry without rests_on, source_id, quote
// and page_setting, merged with the MEASURED number of the latest measured entry, value = the median.
function rejudgedPlan(plan, measured) {
  const copy = clone(plan)
  copy.numbers = copy.numbers.map(entry => {
    if (!Object.hasOwn(measured, entry.id)) return entry
    const { rests_on, source_id, quote, page_setting, ...rest } = entry
    return { ...rest, ...measured[entry.id].number, value: measured[entry.id].median }
  })
  return copy
}

// Exact gate_reasons (second review): CONTRACT.md does not state gate_plan's reason strings, so the expected reasons
// are the tree's own. T1 runs the tree on the stub's plans; two of its calibration_required records (the random
// picks of R2) are the judged records card_resolve.js re-judges. T2 runs the tree again (same arguments, so the same
// picks, given and gate arguments) with the producer returning, for those two picks, exactly the plan re-judging must
// evaluate (rejudgedPlan); what the tree's gate says about that plan is what rejudged must say.
//   R (repair): echo basalt flow. steps_per_h measured 1900 (run-1) and 2100 (run-2): median 2000, provenance of
//     run-2; slow_f (GUESS, rests_on) measured 1 by run-2. Planned 2054.85 > 1000 >= total_stated 868.22: repair.
//     The tree's reasons are the lines of its REPAIR_EXPR prompt ("These cost expressions failed a check:").
//   H (halt): echo basalt probe, its judged plan's total_stated set to 2500. steps_per_h measured 2100 (run-1) and
//     1900 (run-2). Planned 2054.85 > 1000 and total_stated > 1000: halt. The tree's reasons are in its log.
// T3 (item 7 of the review) runs the same picks with the plan re-judging must NOT evaluate: R with rests_on,
// source_id, quote and page_setting retained, H with the provenance of the earliest measured entry (run-1).
const KEY_R = 'R2:physical:W1', KEY_H = 'R2:interp:W1'
function repairReasons(tree, label) {
  const row = tree.prompts.find(entry => entry.kind === 'REPAIR_EXPR' && String(entry.title).startsWith(label))
  const m = row && /These cost expressions failed a check:\n([\s\S]*?)\nRewrite only/.exec(row.body)
  return m ? m[1].split('\n') : null
}
// What the tree's gate said about a pick's plan: "repair" with the REPAIR_EXPR prompt's lines; "halt" with the
// halted card's text ("**Halted at G-plan.** <reasons>"; the budget halt is one condition, so one reason); else "ok".
// Plus the evaluation's planned spend (the record's plan_usd) and its uncertain ids (the record's required ids).
function treeOutcome(tree, key, label) {
  const i = tree.result?.calibration?.findIndex(record => record.key === key) ?? -1
  const record = tree.result?.calibration?.[i]
  const halted = /\*\*Halted at G-plan\.\*\* ([^\n]*)/.exec(String(tree.result?.cards?.[i] ?? ''))
  const repair = repairReasons(tree, label)
  return { action: repair ? 'repair' : halted ? 'halt' : 'ok', reasons: repair ?? (halted ? [halted[1]] : []),
    planned: record?.plan_usd ?? null, uncertain: record?.required?.map(item => item.id) ?? null }
}

function treeCases() {
  const t1 = treeRun('t1')
  const records = t1.result?.calibration ?? []
  const baseR = records.find(record => record.key === KEY_R), baseH = records.find(record => record.key === KEY_H)
  check('tree t1: the two R2 random picks are calibration_required with judged, steps_per_h, slow_f, fudge_f (fixture)', () => {
    for (const record of [baseR, baseH]) {
      assert.ok(record, 'record missing')
      assert.equal(record.state, 'calibration_required', record.key)
      assert.ok(record.judged && record.judged.plan, `${record.key} judged`)
      assert.deepEqual(record.required.map(item => item.id), ['steps_per_h', 'slow_f', 'fudge_f'], record.key)
    }
  })
  if (!baseR?.judged || !baseH?.judged) return
  const recR = clone(baseR), recH = clone(baseH)
  recH.judged.plan.cost.total_stated = 2500
  const result = { ...clone(t1.result), calibration: records.map(record => record.key === KEY_R ? recR : record.key === KEY_H ? recH : record) }

  // The card_resolve.js side: one result.json, two run roots naming both records.
  const c = setup('tree-rejudge', result)
  const fileRule = (id, i) => ({ file: `card/run${i}/${id}.json`, kind: i === 1 ? 'json' : 'regex', expr: i === 1 ? `/${id}` : `${id}=([0-9.]+)` })
  const runs = [1, 2].map(i => ({ i, dir: path.join(c.dir, `run-${i}`), box: { type: `gpu_8x_h100_v${i}`, started_utc: `2026-11-0${i}T00:00:00Z` } }))
  const rowsR = i => [{ id: 'steps_per_h', measured: i === 1 ? 1900 : 2100, rule: fileRule('steps_per_h', i) },
    { id: 'slow_f', measured: i === 1 ? null : 1, rule: fileRule('slow_f', i) }, { id: 'fudge_f', measured: null, rule: fileRule('fudge_f', i) }]
  const rowsH = i => [{ id: 'steps_per_h', measured: i === 1 ? 2100 : 1900, rule: fileRule('steps_per_h', i) },
    { id: 'slow_f', measured: null, rule: fileRule('slow_f', i) }, { id: 'fudge_f', measured: null, rule: fileRule('fudge_f', i) }]
  // Each run root names one record; run roots: R1 (R, run-1), R2 (R, run-2), H1, H2.
  const roots = []
  for (const [record, rowsOf, tag] of [[recR, rowsR, 'r'], [recH, rowsH, 'h']]) for (const run of runs)
    roots.push(makeRun(path.join(c.dir, `${tag}-run-${run.i}`), { result: c.result, record, run: `${tag}${run.i}`, commit: `k${run.i}`,
      box: run.box, rows: rowsOf(run.i) }))
  const value = okRun('tree-rejudge', c, roots)
  const out = key => value?.calibration?.find(record => record.key === key)

  // The MEASURED number the contract merges for an id: the latest (or, for T3, the earliest) measured entry's.
  const measuredOf = (rootsOfRecord, id, which) => {
    const entries = rootsOfRecord.flatMap(run => run.rows.filter(row => row.id === id && row.measured_value !== null).map(row => entryFor(run, row)))
    const values = entries.map(entry => entry.measured_value).sort((a, b) => a - b)
    const median = values.length % 2 ? values[(values.length - 1) / 2] : (values[values.length / 2 - 1] + values[values.length / 2]) / 2
    return { number: (which === 'earliest' ? entries[0] : entries[entries.length - 1]).number, median }
  }
  const rootsR = roots.slice(0, 2), rootsH = roots.slice(2)
  const cleanR = rejudgedPlan(recR.judged.plan, { steps_per_h: measuredOf(rootsR, 'steps_per_h'), slow_f: measuredOf(rootsR, 'slow_f') })
  const cleanH = rejudgedPlan(recH.judged.plan, { steps_per_h: measuredOf(rootsH, 'steps_per_h') })
  const t2 = treeRun('t2', { [recR.title]: cleanR, [recH.title]: cleanH })
  const treeR = treeOutcome(t2, KEY_R, 'R2:physical:random'), treeH = treeOutcome(t2, KEY_H, 'R2:interp:random')
  check('tree t2: the tree repairs plan R and halts plan H, each for its budget condition (fixture)', () => {
    assert.equal(treeR.action, 'repair', JSON.stringify(treeR))
    assert.equal(treeH.action, 'halt', JSON.stringify(treeH))
    for (const outcome of [treeR, treeH]) {
      assert.ok(outcome.reasons.length >= 1 && outcome.reasons.every(reason => typeof reason === 'string' && reason.length > 0), JSON.stringify(outcome))
      near(outcome.planned, RATE * (2 + 124750 / 2000), 'tree planned')
    }
  })
  const wants = [[KEY_R, recR, rootsR, treeR, ['steps_per_h', 'slow_f']], [KEY_H, recH, rootsH, treeH, ['steps_per_h']]]
  for (const [key, original, rootsOfRecord, tree, measuredIds] of wants) {
    const record = out(key)
    if (!record) continue
    check(`tree-rejudge: ${key}: resolved entries of both runs; state refuted (the gate refutes 1900 and 2100)`, () => {
      assert.deepEqual(record.resolved, rootsOfRecord.flatMap(run => run.rows.map(row => entryFor(run, row))))
      assert.equal(record.state, 'refuted')
    })
    check(`tree-rejudge: ${key}: gate_action and gate_reasons exactly the tree's own for the re-judged plan (${tree.action}: ${JSON.stringify(tree.reasons)})`, () => {
      assert.ok(record.rejudged && typeof record.rejudged === 'object', `rejudged ${JSON.stringify(record.rejudged)}`)
      assert.equal(record.rejudged.gate_action, tree.action)
      assert.deepEqual(record.rejudged.gate_reasons, tree.reasons)
    })
    check(`tree-rejudge: ${key}: rejudged measured_ids, plan_usd_before/after and uncertain_after agree with the tree's evaluation`, () => {
      assert.deepEqual(record.rejudged.measured_ids, measuredIds)
      assert.equal(record.rejudged.plan_usd_before, original.plan_usd)
      near(record.rejudged.plan_usd_after, tree.planned, 'plan_usd_after')
      assert.deepEqual(record.rejudged.uncertain_after, tree.uncertain)
    })
  }

  // Item 7 of the review: the replaced numbers drop rests_on, source_id, quote and page_setting and take the latest
  // measured entry's provenance. T3 gives the tree the plans a tool that did otherwise would evaluate. Whether any
  // of rejudged's outputs (action, reasons, planned spend, uncertain ids) can tell them apart from the contract's
  // plans is printed below. In this tree they cannot (the tool runs this tree's cost_eval_plan and gate_plan): a
  // MEASURED number's quote is not checked (only CITED and PROXY are, CONTRACT.md cost.js), and rests_on,
  // source_id, page_setting, command, output, output_line and machine reach only annotations and card text, which
  // rejudged does not carry. So no black-box output of card_resolve.js reveals these two rules; the exact checks
  // above pin everything rejudged does carry.
  const keep = (plan, record, ids) => {
    const copy = clone(plan)
    for (const id of ids) {
      const original = record.judged.plan.numbers.find(entry => entry.id === id)
      const entry = copy.numbers.find(number => number.id === id)
      for (const field of ['rests_on', 'source_id', 'quote', 'page_setting']) if (Object.hasOwn(original, field)) entry[field] = original[field]
    }
    return copy
  }
  const retained = keep(cleanR, recR, ['steps_per_h', 'slow_f'])
  const earliest = rejudgedPlan(recH.judged.plan, { steps_per_h: measuredOf(rootsH, 'steps_per_h', 'earliest') })
  check('tree t3 fixture: the T3 plans differ from the T2 plans (retained fields; earliest provenance)', () => {
    assert.notDeepEqual(retained, cleanR)
    assert.notDeepEqual(earliest, cleanH)
  })
  const t3 = treeRun('t3', { [recR.title]: retained, [recH.title]: earliest })
  const t3R = treeOutcome(t3, KEY_R, 'R2:physical:random'), t3H = treeOutcome(t3, KEY_H, 'R2:interp:random')
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b)
  console.log(`note: retained rests_on/source_id/quote/page_setting ${same(t3R, treeR) ? 'give the same' : 'change the'} action, reasons, planned spend and uncertain ids (not counted)`)
  console.log(`note: the earliest entry's provenance ${same(t3H, treeH) ? 'gives the same' : 'changes the'} action, reasons, planned spend and uncertain ids (not counted)`)
}

function main() {
  try {
    assert.ok(fs.existsSync(TOOL), 'm5/card_resolve.js missing')

    // 1. One run naming B: one entry per scored row; a measured and an unmeasured row; state unchanged.
    {
      const c = setup('one-run')
      const run = makeRun(path.join(c.dir, 'run-one'), { result: c.result, record: REC_B, run: 'blind-02-run1', commit: 'abc1234',
        rows: [{ id: 'a_rate', measured: 44.5, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: null, verdict: 'not_measured', decision: 'not_measured' }] })
      const value = okRun('one-run', c, [run])
      namedRecord('one-run', value, REC_B, { entries: run.rows.map(row => entryFor(run, row)), state: 'calibration_required', judged: false })
      unchangedOthers('one-run', value, [REC_B.key])
      if (value) check('one-run: MEASURED number fields (literal)', () => {
        const [measured, unmeasured] = value.calibration[1].resolved
        assert.deepEqual(measured.number, { id: 'a_rate', name: 'name of a_rate', unit: 'unit of a_rate', basis: 'MEASURED', value: 44.5,
          differs_in: [], command: 'bash harness/run_command.sh', output: 'run-one/agent/results/reproduce/out/card/a_rate.json',
          output_line: 'json: /value/a_rate', machine: 'gpu_1x_a10' })
        assert.equal(unmeasured.number, null)
        assert.deepEqual(Object.keys(measured).sort(), ['box_started_utc', 'box_type', 'decided_by', 'decision', 'id', 'measured_value',
          'number', 'pipeline_commit', 'run', 'verdict'])
      })
    }

    // 2. Several runs, argument order; regex rule; null box and commit; run root basename with a space.
    {
      const c = setup('several-runs')
      const second = makeRun(path.join(c.dir, 'run two'), { result: c.result, record: REC_B, run: 'r2', commit: null, box: null,
        rows: [{ id: 'a_rate', measured: 41, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: 2.75, verdict: 'within_band', decision: 'holds',
            rule: { file: 'logs/run.log', kind: 'regex', expr: 'latency=([0-9.]+)' } }] })
      const first = makeRun(path.join(c.dir, 'run-one'), { result: c.result, record: REC_B, run: 'r1', commit: 'abc',
        rows: [{ id: 'a_rate', measured: 39, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: null, verdict: 'not_measured', decision: 'not_measured' }] })
      // Argument order: the second-built run first.
      const value = okRun('several-runs', c, [second, first])
      namedRecord('several-runs', value, REC_B, {
        entries: [...second.rows.map(row => entryFor(second, row)), ...first.rows.map(row => entryFor(first, row))],
        state: 'calibrated', judged: false })
      unchangedOthers('several-runs', value, [REC_B.key])
      if (value) check('several-runs: regex output_line, null machine, basename with a space (literal)', () => {
        const number = value.calibration[1].resolved[1].number
        assert.equal(number.output_line, 'regex: latency=([0-9.]+)')
        assert.equal(number.output, 'run two/agent/results/reproduce/out/logs/run.log')
        assert.equal(number.machine, null)
        assert.equal(value.calibration[1].resolved[1].pipeline_commit, null)
      })
    }

    // 3. State rules, from every entry of every run (existing entries count; ids outside `required` do not).
    const existing = (id, decision, measured = null) => ({ run: 'earlier', pipeline_commit: null, box_type: null, box_started_utc: null,
      id, measured_value: measured, verdict: decision === 'holds' ? 'within_band' : decision === 'refuted' ? 'above_band' : 'not_measured',
      decided_by: ['holds', 'refuted'].includes(decision) ? 'band' : null, decision,
      // As card_resolve.js writes entries: a MEASURED number exactly when measured_value is a number.
      number: measured === null ? null : { id, name: `name of ${id}`, unit: `unit of ${id}`, basis: 'MEASURED', value: measured,
        differs_in: [], command: 'bash harness/run_command.sh', output: 'earlier/agent/results/reproduce/out/card/x.json',
        output_line: 'json: /x', machine: null } })
    // An `undecidable` row needs an input with no band (U54: value 0); one that also holds in another run takes a
    // launch band in that run (`bands`, per run).
    const valueZero = (...ids) => record => { for (const item of record.required) if (ids.includes(item.id)) item.value = 0 }
    const stateCases = [
      // [name, existing entries of B, runs: [[a decision, b decision], ...], expected state, record change, launch bands per run]
      ['state-any-refuted', [], [['holds', 'holds'], ['refuted', 'not_measured']], 'refuted'],
      ['state-refuted-over-all-holds', [], [['holds', 'refuted'], ['holds', 'holds']], 'refuted'],
      ['state-all-hold-across-runs', [], [['holds', 'not_measured'], ['undecidable', 'holds']], 'calibrated', valueZero('a_rate'),
        [{ a_rate: { abs: 10 } }, {}]],
      ['state-one-unheld-unchanged', [], [['holds', 'undecidable'], ['holds', 'not_measured']], 'calibration_required', valueZero('b_lat')],
      ['state-existing-refuted', [existing('b_lat', 'refuted', 9)], [['holds', 'holds']], 'refuted'],
      ['state-existing-holds', [existing('b_lat', 'holds', 2.5)], [['holds', 'not_measured']], 'calibrated'],
      ['state-existing-other-id-refuted', [existing('old_id', 'refuted', 1)], [['holds', 'holds']], 'calibrated'],
    ]
    // holds: the card's own value (inside its band); refuted: far above the band; undecidable: any number (no band).
    const measuredFor = (record, id, decision) => {
      const value = record.required.find(item => item.id === id).value
      return decision === 'not_measured' ? null : decision === 'refuted' ? value * 100 + 1000 : decision === 'undecidable' ? 1 : value
    }
    for (const [name, prior, decisions, state, change = null, bandsPerRun = []] of stateCases) {
      const result = clone(RESULT)
      result.calibration[1].resolved = prior
      if (change) change(result.calibration[1])
      const named = result.calibration[1]
      const c = setup(name, result)
      const runs = decisions.map(([a, b], i) => makeRun(path.join(c.dir, `run-${i + 1}`), { result: c.result, record: named,
        run: `run-${i + 1}`, commit: `c${i}`, bands: bandsPerRun[i] ?? {}, rows: [{ id: 'a_rate', measured: measuredFor(named, 'a_rate', a), decision: a },
          { id: 'b_lat', measured: measuredFor(named, 'b_lat', b), decision: b }] }))
      fs.mkdirSync(c.outDir, { recursive: true })
      const r = resolve([c.result, ...runs.map(run => run.dir), '--out', c.out])
      check(`${name}: exit 0`, () => assert.equal(r.status, 0, why(r)))
      if (!fs.existsSync(c.out)) continue
      const record = read(c.out).calibration[1]
      check(`${name}: state ${state}`, () => assert.equal(record.state, state))
      check(`${name}: existing entries kept first, then each run's rows`, () => assert.deepEqual(record.resolved,
        [...prior, ...runs.flatMap(run => run.rows.map(row => entryFor(run, row)))]))
    }

    // 4. Two runs naming different records in one call; D has no `judged` key: rejudged null.
    {
      const c = setup('two-records')
      const runB = makeRun(path.join(c.dir, 'run-b'), { result: c.result, record: REC_B, run: 'rb', commit: 'x',
        rows: [{ id: 'a_rate', measured: 120, verdict: 'above_band', decision: 'refuted' },
          { id: 'b_lat', measured: 2, verdict: 'within_band', decision: 'holds' }] })
      const runD = makeRun(path.join(c.dir, 'run-d'), { result: c.result, record: REC_D, run: 'rd', commit: 'y',
        rows: [{ id: 'c_frac', measured: 0.31, verdict: 'within_band', decision: 'holds' }] })
      const value = okRun('two-records', c, [runB, runD])
      namedRecord('two-records', value, REC_B, { entries: runB.rows.map(row => entryFor(runB, row)), state: 'refuted', judged: false })
      namedRecord('two-records', value, REC_D, { entries: runD.rows.map(row => entryFor(runD, row)), state: 'calibrated', judged: false })
      unchangedOthers('two-records', value, [REC_B.key, REC_D.key])
    }

    // 5. Re-judging A with its hand-built `judged`.
    // Expected gate outcomes, derived from CONTRACT.md (gates.js `gate_plan`, cost.js, §5 integration) rather than
    // from the implementation. The fixture plan passes every schema-level halt (both predictions differ, the decision
    // rule has a digit, levels 2000..32000, phases and sources present, compute_tested "yes") and has no expression
    // error, so the action is forced by the budget rule alone, with budget 1000 (judged.gate_args.budget_usd):
    //   planned <= 1000                              -> "ok", and then no reason (reasons explain a halt or a repair)
    //   planned > 1000 and total_stated (868.22) <= 1000 -> "repair"
    //   planned > 1000 and total_stated > 1000       -> "halt"
    // Reason strings are not stated in the contract, so here for "repair"/"halt" only a non-empty list of strings is
    // required; treeCases() compares them exactly with the reasons the tree itself gives for the same plan. `uncertain_after` is forced: the plan's only GUESS/PROXY input is steps_per_h (DESIGN and DERIVED
    // are never uncertain), so it is [] once steps_per_h is MEASURED and ["steps_per_h"] while it is not. A merge
    // that kept the PROXY basis would also keep the quote check ("about 5,000 ...") and fail it: "repair", not "ok".
    const gateFor = (median, totalStated = PLAN.cost.total_stated) => planned(median) <= 1000 ? 'ok'
      : totalStated <= 1000 ? 'repair' : 'halt'
    const rejudge = (name, measuredRuns, { prior = [], wantMedian, wantIds, mutate = null, wantAction = null }) => {
      const result = clone(RESULT)
      result.calibration[0].resolved = prior
      if (mutate) mutate(result.calibration[0])
      const c = setup(name, result)
      const runs = measuredRuns.map((measured, i) => makeRun(path.join(c.dir, `run-${i + 1}`), { result: c.result, record: result.calibration[0],
        run: `run-${i + 1}`, commit: `k${i}`, box: { type: `gpu_8x_h100_${i}`, started_utc: `2026-11-0${i + 1}T00:00:00Z` },
        rows: [{ id: 'steps_per_h', measured, verdict: measured === null ? 'not_measured' : 'within_band',
          decision: measured === null ? 'not_measured' : measured >= 3000 ? 'holds' : 'refuted', decided_by: measured === null ? null : 'gate' }] }))
      const value = okRun(name, c, runs)
      if (!value) return null
      const record = value.calibration[0]
      check(`${name}: rejudged has exactly {measured_ids, plan_usd_before, plan_usd_after, gate_action, gate_reasons, uncertain_after}`, () => {
        assert.ok(record.rejudged && typeof record.rejudged === 'object', `rejudged ${JSON.stringify(record.rejudged)}`)
        assert.deepEqual(Object.keys(record.rejudged).sort(), ['gate_action', 'gate_reasons', 'measured_ids', 'plan_usd_after',
          'plan_usd_before', 'uncertain_after'])
      })
      if (!record.rejudged) return record
      check(`${name}: measured_ids ${JSON.stringify(wantIds)}; plan_usd_before is the record's plan_usd`, () => {
        assert.deepEqual(record.rejudged.measured_ids, wantIds)
        assert.equal(record.rejudged.plan_usd_before, REC_A.plan_usd)
      })
      check(`${name}: plan_usd_after is the evaluation with steps_per_h = ${wantMedian}`, () => {
        near(record.rejudged.plan_usd_after, planned(wantMedian), 'plan_usd_after')
      })
      check(`${name}: gate_action and gate_reasons from gate_plan; uncertain_after a list of ids without a measured id`, () => {
        assert.ok(['halt', 'repair', 'ok'].includes(record.rejudged.gate_action), `gate_action ${record.rejudged.gate_action}`)
        assert.ok(Array.isArray(record.rejudged.gate_reasons), 'gate_reasons not an array')
        assert.ok(Array.isArray(record.rejudged.uncertain_after) && record.rejudged.uncertain_after.every(id => typeof id === 'string'),
          `uncertain_after ${JSON.stringify(record.rejudged.uncertain_after)}`)
        for (const id of wantIds) assert.ok(!record.rejudged.uncertain_after.includes(id), `${id} still uncertain after measurement`)
      })
      const action = wantAction ?? gateFor(wantMedian)
      check(`${name}: gate_action "${action}", gate_reasons and uncertain_after exactly as the contract forces them`, () => {
        assert.equal(record.rejudged.gate_action, action)
        if (action === 'ok') assert.deepEqual(record.rejudged.gate_reasons, [])
        else assert.ok(record.rejudged.gate_reasons.length > 0 && record.rejudged.gate_reasons.every(x => typeof x === 'string'),
          `gate_reasons ${JSON.stringify(record.rejudged.gate_reasons)}`)
        assert.deepEqual(record.rejudged.uncertain_after, wantIds.includes('steps_per_h') ? [] : ['steps_per_h'])
      })
      check(`${name}: entries for every run in argument order`, () => assert.deepEqual(record.resolved,
        [...prior, ...runs.flatMap(run => run.rows.map(row => entryFor(run, row)))]))
      return record
    }
    const one = rejudge('rejudge-one-run', [6300], { wantMedian: 6300, wantIds: ['steps_per_h'] })
    if (one) check('rejudge-one-run: a measured value that changes the cost changes plan_usd_after (literal 63.84 + 638.4)', () => {
      assert.notEqual(one.rejudged.plan_usd_after, one.rejudged.plan_usd_before)
      near(one.rejudged.plan_usd_after, 702.24, 'plan_usd_after (63.84 + 638.4)')
    })
    rejudge('rejudge-median-odd', [6000, 9000, 7000], { wantMedian: 7000, wantIds: ['steps_per_h'] })
    rejudge('rejudge-median-even', [6000, 7000], { wantMedian: 6500, wantIds: ['steps_per_h'] })
    rejudge('rejudge-median-with-existing-entry', [6000, 7000], { prior: [existing('steps_per_h', 'holds', 100000)], wantMedian: 7000,
      wantIds: ['steps_per_h'] })
    rejudge('rejudge-refuted-measurement', [2000], { wantMedian: 2000, wantIds: ['steps_per_h'] })
    const none = rejudge('rejudge-unmeasured', [null], { wantMedian: 5000, wantIds: [] })
    if (none) check('rejudge-unmeasured: nothing measured: the plan is evaluated unchanged', () => {
      near(none.rejudged.plan_usd_after, REC_A.plan_usd, 'plan_usd_after')
    })
    // judged.plan states a total over the budget: a measured cost over the budget halts; one within it does not.
    const statedOver = record => { record.judged.plan.cost.total_stated = 2500 }
    rejudge('rejudge-stated-over-measured-over', [2000], { wantMedian: 2000, wantIds: ['steps_per_h'], mutate: statedOver,
      wantAction: 'halt' })
    rejudge('rejudge-stated-over-measured-within', [6300], { wantMedian: 6300, wantIds: ['steps_per_h'], mutate: statedOver,
      wantAction: 'ok' })

    // 5a. The median without overflow (second review): two runs each measuring 1e308 give a MEASURED value of 1e308
    // (a sum first would be Infinity). The judged plan's sweep hours are steps_per_h / scale with scale a DESIGN
    // 1e306, so the median shows in plan_usd_after: 63.84 + 31.92 * 100 = 3255.84 for 1e308 (Infinity for an
    // overflowed median; 1596 + 63.84 for a halved one).
    {
      const result = clone(RESULT)
      const plan = result.calibration[0].judged.plan
      plan.numbers.splice(2, 0, { id: 'scale', name: 'steps per sweep hour unit', unit: 'steps', basis: 'DESIGN', value: 1e306 })
      plan.numbers.find(n => n.id === 't_main').expr = 'steps_per_h / scale'
      const c = setup('median-no-overflow', result)
      const runs = [0, 1].map(i => makeRun(path.join(c.dir, `run-${i + 1}`), { result: c.result, record: result.calibration[0],
        run: `run-${i + 1}`, commit: null, rows: [{ id: 'steps_per_h', measured: 1e308, decision: 'holds' }] }))
      const value = okRun('median-no-overflow', c, runs)
      const record = value?.calibration[0]
      if (record) {
        check('median-no-overflow: entries carry measured_value and number.value 1e308', () => assert.deepEqual(record.resolved,
          runs.flatMap(run => run.rows.map(row => entryFor(run, row)))))
        check('median-no-overflow: rejudged with steps_per_h = 1e308: plan_usd_after 3255.84 (finite), measured_ids, uncertain_after []', () => {
          assert.ok(record.rejudged && typeof record.rejudged === 'object', `rejudged ${JSON.stringify(record.rejudged)}`)
          assert.ok(Number.isFinite(record.rejudged.plan_usd_after), `plan_usd_after ${record.rejudged.plan_usd_after}`)
          near(record.rejudged.plan_usd_after, RATE * 2 + RATE * 100, 'plan_usd_after')
          assert.deepEqual(record.rejudged.measured_ids, ['steps_per_h'])
          assert.deepEqual(record.rejudged.uncertain_after, [])
          assert.ok(['halt', 'repair', 'ok'].includes(record.rejudged.gate_action), `gate_action ${record.rejudged.gate_action}`)
        })
      }
    }

    // 5b. Merging with two required ids whose `required` order (steps_per_h, eff) is not alphabetical order.
    // The judged plan's sweep hours are steps / steps_per_h / eff, so the evaluation shows which value each id took.
    // What the merged numbers look like inside the copied plan is not part of `rejudged`; the observable parts are the
    // medians (through plan_usd_after), measured_ids, and the MEASURED basis replacing PROXY/GUESS (uncertain_after,
    // and gate_action "ok": a kept PROXY basis with its quote "about 5,000 ..." would fail the quote check and repair).
    {
      const plan2 = clone(PLAN)
      plan2.numbers.splice(1, 0, { id: 'eff', name: 'step efficiency', unit: 'ratio', basis: 'GUESS', value: 2,
        rests_on: 'a guess from the pilot of a similar policy', measured_by: 'P1' })
      plan2.numbers.find(n => n.id === 't_main').expr = 'steps / steps_per_h / eff'
      const planned2 = (s, e) => RATE * 2 + RATE * 126000 / (s * e)
      const REC_F = { key: 'R4:physical:W5', title: plan2.option_title, state: 'calibration_required', plan_usd: planned2(5000, 2),
        required: [required('steps_per_h', 'PROXY', 5000, { phase: clone(PLAN.phases[0]) }),
          required('eff', 'GUESS', 2, { name: 'step efficiency', unit: 'ratio' })], resolved: [],
        anchor: clone(PLAN.anchor), predictions: clone(PLAN.predictions), judged: { ...clone(JUDGED), plan: plan2 } }
      const result = clone(RESULT)
      result.calibration[3] = REC_F   // D's slot: D is not named here
      const merge = (name, perRun, { wantIds, steps, eff, uncertain }) => {
        const c = setup(name, result)
        const runs = perRun.map(([s, e], i) => makeRun(path.join(c.dir, `run-${i + 1}`), { result: c.result, record: REC_F,
          run: `run-${i + 1}`, commit: `m${i}`, box: { type: `box_${i}`, started_utc: `2026-11-0${i + 1}T00:00:00Z` },
          rows: [{ id: 'steps_per_h', measured: s, verdict: s === null ? 'not_measured' : 'within_band', decision: s === null ? 'not_measured' : 'holds' },
            { id: 'eff', measured: e, verdict: e === null ? 'not_measured' : 'within_band', decision: e === null ? 'not_measured' : 'holds' }] }))
        fs.mkdirSync(c.outDir, { recursive: true })
        const r = resolve([c.result, ...runs.map(run => run.dir), '--out', c.out])
        check(`${name}: exit 0`, () => assert.equal(r.status, 0, why(r)))
        if (!fs.existsSync(c.out)) return
        const record = read(c.out).calibration[3]
        check(`${name}: entries for both ids of every run, in argument order`, () => assert.deepEqual(record.resolved,
          runs.flatMap(run => run.rows.map(row => entryFor(run, row)))))
        check(`${name}: rejudged present`, () => assert.ok(record.rejudged && typeof record.rejudged === 'object'))
        if (!record.rejudged) return
        check(`${name}: measured_ids ${JSON.stringify(wantIds)} in required order (not alphabetical)`, () =>
          assert.deepEqual(record.rejudged.measured_ids, wantIds))
        check(`${name}: plan_usd_before ${REC_F.plan_usd.toFixed(3)}; plan_usd_after uses the medians steps_per_h=${steps}, eff=${eff}`, () => {
          assert.equal(record.rejudged.plan_usd_before, REC_F.plan_usd)
          near(record.rejudged.plan_usd_after, planned2(steps, eff), 'plan_usd_after')
        })
        check(`${name}: gate_action "ok", no reasons, uncertain_after ${JSON.stringify(uncertain)}`, () => {
          assert.equal(record.rejudged.gate_action, 'ok')
          assert.deepEqual(record.rejudged.gate_reasons, [])
          assert.deepEqual(record.rejudged.uncertain_after, uncertain)
        })
      }
      // The latest run never holds the median: steps_per_h 9000, 7000, 6000 (median 7000, latest 6000); eff 3, 1.5, 4
      // (median 3, latest 4). planned = 63.84 + 31.92 * 126000 / 21000 = 255.36.
      merge('merge-two-ids-three-runs', [[9000, 3], [7000, 1.5], [6000, 4]], { wantIds: ['steps_per_h', 'eff'], steps: 7000, eff: 3,
        uncertain: [] })
      // Even count, with an unmeasured row in one run: steps_per_h 6000 and 8000 (median 7000), eff 2.5 alone.
      merge('merge-two-ids-even-and-unmeasured', [[6000, null], [8000, 2.5]], { wantIds: ['steps_per_h', 'eff'], steps: 7000, eff: 2.5,
        uncertain: [] })
      // Only eff measured: steps_per_h keeps its PROXY value and stays uncertain.
      merge('merge-only-second-id', [[null, 4], [null, 2]], { wantIds: ['eff'], steps: 5000, eff: 3, uncertain: ['steps_per_h'] })
      // Only steps_per_h measured: eff keeps its GUESS value and stays uncertain.
      merge('merge-only-first-id', [[6300, null]], { wantIds: ['steps_per_h'], steps: 6300, eff: 2, uncertain: ['eff'] })
    }

    treeCases()

    // 6. A relative result path from another working directory: `source` is absolute.
    {
      const c = setup('relative-result')
      const run = makeRun(path.join(c.dir, 'run-one'), { result: c.result, record: REC_B, run: 'r', commit: null,
        rows: [{ id: 'a_rate', measured: 40, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: null, verdict: 'not_measured', decision: 'not_measured' }] })
      const value = okRun('relative-result', c, [run], [path.relative(c.dir, c.result), 'run-one', '--out', path.relative(c.dir, c.out)], c.dir)
      if (value) check('relative-result: source is the absolute path of result.json', () => assert.equal(value.source, c.result))
    }

    // 7. Exit 1: nothing written.
    const base = (name, mutate = () => {}) => {
      const c = setup(name)
      const run = makeRun(path.join(c.dir, 'run-one'), { result: c.result, record: REC_B, run: 'r', commit: null,
        rows: [{ id: 'a_rate', measured: 40, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: null, verdict: 'not_measured', decision: 'not_measured' }] })
      const good = makeRun(path.join(c.dir, 'run-good'), { result: c.result, record: REC_B, run: 'g', commit: null,
        rows: [{ id: 'a_rate', measured: 41, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: 2, verdict: 'within_band', decision: 'holds' }] })
      mutate(c, run)
      return { c, run, good, runs: [good, run], argv: [c.result, good.dir, run.dir, '--out', c.out] }
    }
    const control = (run, file) => path.join(run.dir, 'control', file)
    const failing = [
      ['seal-mismatch', (c, run) => fs.appendFileSync(control(run, 'card.json'), ' ')],
      ['seal-digest-wrong', (c, run) => writeJSON(control(run, 'card_seal.json'), { card_sha256: '0'.repeat(64), sealed_utc: 'x' })],
      ['source-sha-differs', (c, run) => {
        const card = read(control(run, 'card.json'))
        card.source_sha256 = 'b'.repeat(64)
        const bytes = writeJSON(control(run, 'card.json'), card)
        writeJSON(control(run, 'card_seal.json'), { card_sha256: sha(bytes), sealed_utc: 'x' })
      }],
      ['missing-card', (c, run) => fs.rmSync(control(run, 'card.json'))],
      ['missing-seal', (c, run) => fs.rmSync(control(run, 'card_seal.json'))],
      ['missing-scored', (c, run) => fs.rmSync(control(run, 'card_scored.json'))],
      ['scored-not-json', (c, run) => fs.writeFileSync(control(run, 'card_scored.json'), '{"rows": [')],
      ['seal-not-json', (c, run) => fs.writeFileSync(control(run, 'card_seal.json'), '{')],
      ['run-root-missing', (c, run) => fs.rmSync(run.dir, { recursive: true })],
      ['key-without-record', (c, run) => {
        const card = read(control(run, 'card.json'))
        card.record = { ...card.record, key: 'R9:nowhere:W9' }
        const bytes = writeJSON(control(run, 'card.json'), card)
        writeJSON(control(run, 'card_seal.json'), { card_sha256: sha(bytes), sealed_utc: 'x' })
        const scored = read(control(run, 'card_scored.json'))
        writeJSON(control(run, 'card_scored.json'), { ...scored, key: 'R9:nowhere:W9', card_sha256: sha(bytes) })
      }],
    ]
    // card_scored.json must have exactly U54's keys and row keys, the run's record key, the run's card.json digest,
    // and rows for the record's `required` ids in order (review of U56).
    const scored = fn => (c, run) => {
      const value = read(control(run, 'card_scored.json'))
      fn(value, run)
      writeJSON(control(run, 'card_scored.json'), value)
    }
    failing.push(
      ['scored-missing-key', scored(v => { delete v.extract_sha256 })],
      ['scored-missing-predictions', scored(v => { delete v.predictions })],
      ['scored-extra-key', scored(v => { v.note = 'extra' })],
      ['scored-row-missing-key', scored(v => { delete v.rows[0].rule })],
      ['scored-row-missing-gate-passed', scored(v => { delete v.rows[1].gate_passed })],
      ['scored-row-extra-key', scored(v => { v.rows[1].note = 'extra' })],
      ['scored-other-record-key', scored(v => { v.key = REC_A.key })],
      ['scored-card-sha-other', scored(v => { v.card_sha256 = 'c'.repeat(64) })],
      ['scored-card-sha-of-seal', scored((v, run) => { v.card_sha256 = sha(fs.readFileSync(control(run, 'card_seal.json'))) })],
      ['scored-rows-reordered', scored(v => { v.rows.reverse() })],
      ['scored-rows-missing-one', scored(v => { v.rows.pop() })],
      ['scored-rows-extra-id', scored(v => { v.rows.push({ ...v.rows[0], id: 'z_extra' }) })],
      ['scored-rows-duplicate-id', scored(v => { v.rows[1] = { ...v.rows[0] } })],
      ['scored-rows-empty', scored(v => { v.rows = [] })],
    )
    // Second review of U56: exact keys and identity, but a field value U54 does not allow, or one that disagrees with
    // U54's rules for its row. Rows: [0] a_rate measured 40 (PROXY 40, band [16, 100], no gate: within_band / band /
    // holds); [1] b_lat unmeasured (not_measured). `retotal` keeps the four totals equal to the counts, so only the
    // named field is wrong.
    const retotal = v => Object.assign(v, totalsOf(v.rows))
    const row = (i, fields, keepTotals = false) => scored(v => { Object.assign(v.rows[i], fields); if (!keepTotals) retotal(v) })
    failing.push(
      ['value-unmeasured-holds', row(1, { decision: 'holds' })],
      ['value-unmeasured-holds-band-labels', row(1, { verdict: 'within_band', decided_by: 'band', decision: 'holds' })],
      ['value-unmeasured-refuted', row(1, { verdict: 'above_band', decided_by: 'band', decision: 'refuted' })],
      ['value-unmeasured-undecidable', row(1, { decision: 'undecidable' })],
      ['value-verdict-unknown', row(0, { verdict: 'inside_band' })],
      ['value-verdict-null', row(0, { verdict: null })],
      ['value-decided-by-unknown', row(0, { decided_by: 'judge' })],
      ['value-decision-unknown', row(0, { decision: 'held' })],
      ['value-decision-null', row(0, { decision: null })],
      ['value-verdict-against-band', row(0, { verdict: 'above_band', decision: 'refuted' })],
      ['value-verdict-below-against-band', row(0, { verdict: 'below_band', decision: 'refuted' })],
      ['value-verdict-not-measured-with-number', row(0, { verdict: 'not_measured', decided_by: null, decision: 'not_measured' })],
      ['value-verdict-no-band-with-band', row(0, { verdict: 'no_band', decided_by: null, decision: 'undecidable' })],
      ['value-decision-against-verdict', row(0, { decision: 'refuted' })],
      ['value-undecidable-with-band', row(0, { decided_by: null, decision: 'undecidable' })],
      ['value-decided-by-null-with-band', row(0, { decided_by: null })],
      ['value-decided-by-gate-without-gate', row(0, { decided_by: 'gate' })],
      ['value-gate-passed-without-gate', row(0, { gate_passed: true, decided_by: 'gate', decision: 'holds' })],
      ['value-gate-passed-string', row(0, { gate_passed: 'true' })],
      ['value-gate-passed-number', row(0, { gate_passed: 1 })],
      ['value-basis-not-records', row(0, { basis: 'GUESS' })],
      ['value-basis-measured', row(0, { basis: 'MEASURED' })],
      ['value-rule-kind-unknown', row(0, { rule: { file: 'card/a_rate.json', kind: 'yaml', expr: '/value/a_rate' } })],
      ['value-rule-kind-uppercase', row(0, { rule: { file: 'card/a_rate.json', kind: 'JSON', expr: '/value/a_rate' } })],
      ['total-negative', scored(v => { v.refuted_total = -1 })],
      ['total-fractional', scored(v => { v.measured_total = 1.5 })],
      ['total-boolean', scored(v => { v.holds_total = true })],
      ['total-string', scored(v => { v.inputs_total = '2' })],
      ['total-not-count-inputs', scored(v => { v.inputs_total = 3 })],
      ['total-not-count-measured', scored(v => { v.measured_total = 2 })],
      ['total-not-count-holds', scored(v => { v.holds_total = 0 })],
      ['total-not-count-refuted', scored(v => { v.refuted_total = 1 })],
    )
    for (const [name, mutate] of failing) {
      const { c, runs, argv } = base(name, mutate)
      refused(name, c, runs.filter(run => fs.existsSync(run.dir)), argv)
    }
    // Gate rows (A: steps_per_h's phase gate `>= 3000`; band [2000, 12500]). Measured 6300: gate_passed true,
    // decided_by gate, holds; measured 2500: within_band but gate_passed false, refuted.
    for (const [name, measured, fields] of [
      ['gate-passed-false-against-measurement', 6300, { gate_passed: false, decision: 'refuted' }],
      ['gate-passed-true-against-measurement', 2500, { gate_passed: true, decision: 'holds' }],
      ['gate-decision-against-gate', 6300, { decision: 'refuted' }],
      ['gate-band-decides-a-gated-row', 2500, { gate_passed: null, decided_by: 'band', decision: 'holds' }],
      ['gate-decided-by-band', 6300, { decided_by: 'band' }],
      ['gate-passed-null-with-gate', 6300, { gate_passed: null, decided_by: 'band' }],
    ]) {
      const c = setup(name)
      const good = makeRun(path.join(c.dir, 'run-good'), { result: c.result, record: REC_A, run: 'g', commit: null,
        rows: [{ id: 'steps_per_h', measured: 7000, decision: 'holds' }] })
      const run = makeRun(path.join(c.dir, 'run-one'), { result: c.result, record: REC_A, run: 'r', commit: null,
        rows: [{ id: 'steps_per_h', measured, decision: measured >= 3000 ? 'holds' : 'refuted' }] })
      scored(v => { Object.assign(v.rows[0], fields); retotal(v) })(c, run)
      refused(name, c, [good, run], [c.result, good.dir, run.dir, '--out', c.out])
    }
    // The same two run roots unmodified are accepted (the refusals above come from the changed field alone).
    {
      const c = setup('gate-rows-unmodified')
      const runs = [7000, 2500].map((measured, i) => makeRun(path.join(c.dir, `run-${i}`), { result: c.result, record: REC_A, run: `r${i}`,
        commit: null, rows: [{ id: 'steps_per_h', measured, decision: measured >= 3000 ? 'holds' : 'refuted' }] }))
      okRun('gate-rows-unmodified', c, runs)
    }
    {
      const { c, runs } = base('result-missing')
      const missing = path.join(c.dir, 'no-such-result.json')
      refused('result-missing', c, runs, [missing, ...runs.map(run => run.dir), '--out', c.out])
    }
    {
      // result.json changed after the runs: its SHA-256 no longer matches the runs' source_sha256.
      const { c, runs, argv } = base('result-changed')
      const changed = Buffer.concat([c.resultBytes, Buffer.from(' ')])
      fs.writeFileSync(c.result, changed)
      c.resultBytes = changed
      refused('result-changed', c, runs, argv)
    }
    {
      const { c, runs } = base('result-not-json')
      const bad = path.join(c.dir, 'bad.json')
      fs.writeFileSync(bad, '{"calibration": [')
      refused('result-not-json', c, runs, [bad, ...runs.map(run => run.dir), '--out', c.out])
    }
    {
      const { c } = base('no-run-root')
      refused('no-run-root', c, [], [c.result, '--out', c.out])
    }
    {
      const { c, runs } = base('missing-out')
      refused('missing-out', c, runs, [c.result, ...runs.map(run => run.dir)])
      refused('missing-out-value', c, runs, [c.result, ...runs.map(run => run.dir), '--out'])
    }
    // Refusal to write over an input: result.json, a run's card_scored.json or card.json.
    for (const [name, target] of [['out-is-result', c => c.result], ['out-is-scored', (c, run) => control(run, 'card_scored.json')],
      ['out-is-card', (c, run) => control(run, 'card.json')], ['out-is-seal', (c, run) => control(run, 'card_seal.json')]]) {
      const { c, run, runs } = base(name)
      refused(name, c, runs, [c.result, ...runs.map(r => r.dir), '--out', target(c, run)], { outIsInput: true })
    }
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : `all ${checks} checks passed`)
  process.exitCode = failures ? 1 : 0
}
main()
